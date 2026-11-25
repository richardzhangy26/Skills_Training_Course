#!/usr/bin/env python3
"""修复"讯问程序启动→讯问策略选择"连线的 transitionPrompt。

背景
----
该边原 transitionPrompt 使用 ${next_stage_opening} 模板，过渡生成模型偶发
不能原样输出完整开场白（曾只输出"3"），导致学生进入策略选择阶段时看不到
策略选项说明。修复方式：删除该边并以"开场白全文内联"的固定模板重建——
transitionPrompt 直接内置下一阶段（讯问策略选择）的开场白全文，不再依赖
${next_stage_opening} 变量。

用法
----
    python wire_fix_hub_entry_transition.py <train_task_id> <剧本md路径>            # dry-run
    python wire_fix_hub_entry_transition.py <train_task_id> <剧本md路径> --apply    # 执行

开场白从剧本 md 的阶段2"讯问策略选择"的 **开场白** 代码块自动提取，避免手抄错误。
"""

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from create_task_from_markdown import (  # noqa: E402
    load_env_config,
    query_script_steps,
    query_script_step_flows,
    get_business_script_steps,
    ability_train_url,
    get_headers,
    delete_script_step_flow,
)
from create_task_from_markdown import DEFAULT_TRANSITION_HISTORY_NUM  # noqa: E402
import requests
from nanoid import generate

ENTRY_CONDITION = "进入策略选择阶段"
RETURN_CONDITION = "返回策略选择阶段"
HUB_ENTRY_CONDITIONS = (ENTRY_CONDITION, RETURN_CONDITION)


def create_script_flow_with_default(train_task_id, start_id, end_id, condition_text,
                                     transition_prompt="", is_default=1):
    url = ability_train_url("createScriptStepFlow")
    flow_id = generate(size=21)
    payload = {
        "trainTaskId": train_task_id,
        "flowId": flow_id,
        "scriptStepStartId": start_id,
        "scriptStepStartHandle": f"{start_id}-source-bottom",
        "scriptStepEndId": end_id,
        "scriptStepEndHandle": f"{end_id}-target-top",
        "flowSettingType": "quick",
        "flowCondition": condition_text,
        "flowConfiguration": {
            "relation": "and",
            "conditions": [
                {
                    "text": "条件组1",
                    "relation": "and",
                    "conditions": [{"text": condition_text}],
                }
            ],
        },
        "transitionPrompt": transition_prompt,
        "transitionHistoryNum": DEFAULT_TRANSITION_HISTORY_NUM,
        "isDefault": is_default,
        "isError": False,
    }
    try:
        response = requests.post(url, headers=get_headers(), json=payload, timeout=20)
        res_json = response.json()
        if res_json.get("code") == 200 or res_json.get("success") is True:
            print(f"✅ Created Flow: {condition_text} (isDefault={is_default}) -> (ID: {flow_id})")
            return True
        print(f"❌ Failed to create flow {condition_text}: {res_json}")
        return False
    except Exception as e:
        print(f"❌ Error creating flow {condition_text}: {e}")
        return False


def extract_hub_opening(md_path: Path) -> str:
    """从剧本 md 中提取阶段2（讯问策略选择）的开场白代码块内容。"""
    content = md_path.read_text(encoding="utf-8")
    m = re.search(r"###\s*阶段2[::][^\n]*策略选择", content)
    if not m:
        raise ValueError("未在 md 中找到阶段2（讯问策略选择）标题")
    section = content[m.end():]
    nxt = re.search(r"^###\s*阶段3", section, re.MULTILINE)
    if nxt:
        section = section[:nxt.start()]
    om = re.search(r"\*\*开场白\*\*[::]\s*\n```\n(.*?)\n```", section, re.DOTALL)
    if not om:
        raise ValueError("未在阶段2中找到开场白代码块")
    return om.group(1).strip()


def build_transition_prompt(opening: str) -> str:
    return (
        "【输入参数】\n"
        "- 无（开场白已内置于本提示词，不使用外部变量）\n\n"
        "【输出要求】\n"
        "直接以李教官身份原样输出以下开场白，不做任何改写、扩写、续写、解释，"
        "不输出任何其他文字：\n\n"
        f"{opening}\n\n"
        "【严禁】\n"
        "- 严禁输出\"设计说明\"\"设计亮点\"\"小贴士\"等元文本\n"
        "- 严禁反问学生或追加新问题\n"
        "- 严禁以上一阶段角色（犯罪嫌疑人）口吻续讲\n"
        "- 严禁只输出数字、跳转关键词或开场白的片段，必须完整输出全部开场白内容"
    )


def step_name(step):
    return step.get("stepDetailDTO", {}).get("stepName") or step.get("stepName") or ""


def main():
    parser = argparse.ArgumentParser(description="修复程序启动→策略选择连线的过渡提示词")
    parser.add_argument("train_task_id")
    parser.add_argument("markdown_path", help="对应案例的训练剧本配置 md（用于提取阶段2开场白）")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    load_env_config()
    md_path = Path(args.markdown_path)
    if not md_path.exists():
        print(f"❌ md 文件不存在: {md_path}")
        return

    opening = extract_hub_opening(md_path)
    print(f"📄 已提取阶段2开场白（{len(opening)} 字），开头：{opening[:40]}...")

    business = get_business_script_steps(query_script_steps(args.train_task_id))
    stage1 = next((s for s in business if "程序启动" in step_name(s)), None)
    stage2 = next((s for s in business if "策略选择" in step_name(s)), None)
    if not stage1 or not stage2:
        print("❌ 未定位到 讯问程序启动 / 讯问策略选择 阶段，已中止。")
        return
    print(f"✅ 阶段1: {step_name(stage1)} ({stage1['stepId']})")
    print(f"✅ 阶段2: {step_name(stage2)} ({stage2['stepId']})")

    flows = query_script_step_flows(args.train_task_id)
    targets = [
        f for f in flows
        if f.get("scriptStepEndId") == stage2["stepId"]
        and f.get("flowCondition") in HUB_ENTRY_CONDITIONS
    ]
    if not targets:
        print("❌ 未找到进入中枢（讯问策略选择）的连线，已中止。")
        return
    for f in targets:
        print(f"✂ 计划删除旧边: {f.get('scriptStepStartId')} --{f.get('flowCondition')}--> 中枢 (flowId={f.get('flowId')}, isDefault={f.get('isDefault')})")
    print(f"＋ 计划新建 {len(targets)} 条边: transitionPrompt 内置阶段2开场白全文（保持原 isDefault 设置）")

    if not args.apply:
        print("\n🧪 Dry-run 完成，未调用写接口。确认后加 --apply 执行。")
        return

    for f in targets:
        was_default = 1 if f.get("isDefault") in (1, True) else 0
        delete_script_step_flow(args.train_task_id, f["flowId"])
        create_script_flow_with_default(
            args.train_task_id, f["scriptStepStartId"], stage2["stepId"],
            f["flowCondition"], build_transition_prompt(opening), is_default=was_default,
        )
    print("🚀 修复完成。请重新走一遍验证进入中枢时开场白完整显示。")


if __name__ == "__main__":
    main()
