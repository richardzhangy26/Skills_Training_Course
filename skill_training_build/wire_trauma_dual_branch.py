#!/usr/bin/env python3
"""补充连线脚本：把"急诊创伤处置——无菌技术实战训练"任务从线性链改造成路由双分支拓扑。

背景
----
`训练剧本配置（路由合并版）.md`（阶段1训练模式选择 + 阶段2-9助学分支 +
阶段10-14考核分支）通过标准的 `create_task_from_markdown.py` 线性流程导入后，
解析器按 markdown 顺序把 1→2→…→9→10→…→14→END 依次连接。但产品需求是：

- 阶段1（路由）双出边：学生选"助学"→阶段2（手卫生），选"考核"→阶段10（上腹部病例）。
  阶段1→阶段2 为线性导入保留的默认边；阶段1→阶段10 需要补建（非默认边）。
- 助学分支学完即结束：阶段9（助学总结）应直连 END（条件"助学训练完成"），
  线性导入误连的 阶段9→阶段10 边必须删除。
- 考核分支保持线性：阶段10→11→12→13→14→END 不动。

本脚本在标准导入完成、拿到 train_task_id 之后运行，直接调用
`create_task_from_markdown.py` 里已验证过的通用连线函数
（create_script_flow / delete_script_step_flow / query_script_step_flows /
query_script_steps / extract_start_end_ids），修正连线拓扑，不重建节点内容。

用法
----
    python skill_training_build/wire_trauma_dual_branch.py <train_task_id>            # dry-run 预览
    python skill_training_build/wire_trauma_dual_branch.py <train_task_id> --apply    # 实际执行

安全性
------
默认 dry-run：只查询、打印计划变更，不调用任何写接口；必须显式 --apply 才执行。
执行前对定位到的4个关键阶段做 stepName 硬断言，不符合即中止。
执行前可把 steps/flows 快照写入 --backup-path（强烈建议）。
幂等：find_flow_by_condition 同时校验条件文本、起点与终点，重复运行不会重复建边。

isDefault 约定：同一起点多条出边中有且仅有一条默认边。
阶段1默认边为→阶段2（助学，线性导入保留）；→阶段10（考核）为非默认。
阶段9删除误连边后只剩→END一条边，设为默认。
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from create_task_from_markdown import (  # noqa: E402
    load_env_config,
    query_script_steps,
    query_script_step_flows,
    get_business_script_steps,
    create_script_flow,
    delete_script_step_flow,
    extract_start_end_ids,
)

FIXED_TRANSITION_PROMPT = (
    "【输入参数】\n"
    "- 下一阶段原始开场白 ${next_stage_opening}\n\n"
    "【输出要求】\n"
    "直接以新阶段角色身份原样输出 ${next_stage_opening}，不做任何改写、扩写、续写、解释。\n\n"
    "【严禁】\n"
    "- 严禁输出\"设计说明\"\"设计亮点\"\"小贴士\"等元文本\n"
    "- 严禁反问学生或追加新问题\n"
    "- 严禁以上一阶段角色口吻续讲\n"
    "- 严禁添加括号外的旁白、台词标注或markdown格式说明"
)

ROUTER_NAME_SUBSTR = "模式选择"
ZHUXUE_ENTRY_NAME_SUBSTR = "手卫生"
ZHUXUE_SUMMARY_NAME_SUBSTR = "助学总结"
KAOHE_ENTRY_NAME_SUBSTR = "上腹部"

ROUTER_TO_KAOHE_CONDITION = "进入考核模式阶段"
ZHUXUE_SUMMARY_TO_END_CONDITION = "助学训练完成"

EXPECTED_STEP_COUNT = 14


def step_name(step):
    return step.get("stepDetailDTO", {}).get("stepName") or step.get("stepName") or ""


def find_flow(flows, source_id, condition_text, target_id):
    for f in flows:
        if (
            f.get("scriptStepStartId") == source_id
            and f.get("flowCondition") == condition_text
            and f.get("scriptStepEndId") == target_id
        ):
            return f
    return None


def find_outgoing(flows, source_id):
    return [f for f in flows if f.get("scriptStepStartId") == source_id]


def main():
    parser = argparse.ArgumentParser(description="把急诊创伤处置任务连线改造成路由双分支拓扑")
    parser.add_argument("train_task_id", help="已导入合并剧本内容的训练任务 ID")
    parser.add_argument("--apply", action="store_true", help="实际执行连线变更（默认只 dry-run 预览）")
    parser.add_argument(
        "--backup-path", type=str, default=None,
        help="执行前把当前 steps/flows 快照写入该 JSON 路径（强烈建议提供）",
    )
    args = parser.parse_args()

    load_env_config()

    step_list = query_script_steps(args.train_task_id)
    flows = query_script_step_flows(args.train_task_id)
    business_steps = get_business_script_steps(step_list)
    start_node_id, end_node_id = extract_start_end_ids(step_list)

    if args.backup_path:
        Path(args.backup_path).write_text(
            json.dumps({"steps": step_list, "flows": flows}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"💾 已备份当前 steps/flows 到 {args.backup_path}")

    if len(business_steps) != EXPECTED_STEP_COUNT:
        print(
            f"❌ 查询到的业务阶段数为 {len(business_steps)}，期望 {EXPECTED_STEP_COUNT}。"
            "请确认已先用 create_task_from_markdown.py 导入《训练剧本配置（路由合并版）.md》。脚本已中止。"
        )
        return
    if not start_node_id or not end_node_id:
        print("❌ 未找到 START/END 节点，脚本已中止。")
        return

    def locate(name_substr):
        matches = [s for s in business_steps if name_substr in step_name(s)]
        return matches[0] if matches else None

    router_step = locate(ROUTER_NAME_SUBSTR)
    zhuxue_entry_step = locate(ZHUXUE_ENTRY_NAME_SUBSTR)
    zhuxue_summary_step = locate(ZHUXUE_SUMMARY_NAME_SUBSTR)
    kaohe_entry_step = locate(KAOHE_ENTRY_NAME_SUBSTR)

    print("📋 已定位关键阶段（请核对 stepName 是否与预期一致）：")
    for label, s in [
        ("路由阶段", router_step),
        ("助学入口(手卫生)", zhuxue_entry_step),
        ("助学总结", zhuxue_summary_step),
        ("考核入口(上腹部)", kaohe_entry_step),
    ]:
        print(f"  - {label}: stepId={s.get('stepId') if s else None} name={step_name(s) if s else None!r}")
    print(f"  - END 节点: {end_node_id}")

    problems = []
    if router_step is None:
        problems.append(f"未找到包含「{ROUTER_NAME_SUBSTR}」的阶段")
    if zhuxue_entry_step is None:
        problems.append(f"未找到包含「{ZHUXUE_ENTRY_NAME_SUBSTR}」的阶段")
    if zhuxue_summary_step is None:
        problems.append(f"未找到包含「{ZHUXUE_SUMMARY_NAME_SUBSTR}」的阶段")
    if kaohe_entry_step is None:
        problems.append(f"未找到包含「{KAOHE_ENTRY_NAME_SUBSTR}」的阶段")
    if problems:
        print("❌ 断言失败，脚本已中止，不会连线：")
        for p in problems:
            print(f"   - {p}")
        return
    print("✅ 关键阶段名称核对通过。")

    router_id = router_step["stepId"]
    zhuxue_summary_id = zhuxue_summary_step["stepId"]
    kaohe_entry_id = kaohe_entry_step["stepId"]

    # 变更1：删除线性误连边 助学总结→考核入口（上腹部）
    to_delete = []
    for f in find_outgoing(flows, zhuxue_summary_id):
        if f.get("scriptStepEndId") == kaohe_entry_id:
            to_delete.append(f)

    # 变更2：补建 路由→考核入口 边（非默认）
    need_router_to_kaohe = find_flow(flows, router_id, ROUTER_TO_KAOHE_CONDITION, kaohe_entry_id) is None

    # 变更3：补建 助学总结→END 边（默认）
    need_summary_to_end = find_flow(flows, zhuxue_summary_id, ZHUXUE_SUMMARY_TO_END_CONDITION, end_node_id) is None

    print("\n🔍 计划变更：")
    print(f"  删除 {len(to_delete)} 条线性误连边：")
    for f in to_delete:
        print(f"    - 助学总结 --{f.get('flowCondition')!r}--> 考核入口 (flowId={f.get('flowId')})")
    print(f"  新增 路由→考核入口 边（isDefault=0）：{'需要' if need_router_to_kaohe else '已存在，跳过'}")
    print(f"  新增 助学总结→END 边（isDefault=1）：{'需要' if need_summary_to_end else '已存在，跳过'}")

    if not args.apply:
        print("\n🧪 Dry-run 完成，未调用任何写接口。确认无误后加 --apply 参数实际执行。")
        return

    print("\n🚀 开始执行连线变更...")
    for f in to_delete:
        delete_script_step_flow(args.train_task_id, f["flowId"])

    if need_router_to_kaohe:
        create_script_flow(
            args.train_task_id, router_id, kaohe_entry_id,
            ROUTER_TO_KAOHE_CONDITION, FIXED_TRANSITION_PROMPT, is_default=False,
        )

    if need_summary_to_end:
        create_script_flow(
            args.train_task_id, zhuxue_summary_id, end_node_id,
            ZHUXUE_SUMMARY_TO_END_CONDITION, FIXED_TRANSITION_PROMPT, is_default=True,
        )

    print("\n✅ 连线变更执行完毕。请务必用真实对话实测以下场景：")
    print("   1. 路由阶段明确选'助学' → 进入手卫生（助学分支）")
    print("   2. 路由阶段明确选'考核' → 直接进入上腹部病例（考核分支）")
    print("   3. 路由阶段回答'随便' → 澄清确认，不默认落入任何分支")
    print("   4. 助学分支走到助学总结，学生说'完成' → 训练结束（不得串入考核病例）")
    print("   5. 考核分支四病例走完+总结 → 训练结束")


if __name__ == "__main__":
    main()
