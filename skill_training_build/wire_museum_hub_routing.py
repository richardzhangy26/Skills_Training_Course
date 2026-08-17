#!/usr/bin/env python3
"""补充连线脚本：把"红色绵州四大场馆导览"任务从线性链改造成路由中枢拓扑。

背景
----
`训练剧本配置.md`（阶段1路由总介绍 + 阶段2-5四大展馆 + 阶段6总结送别）最初通过标准的
`create_task_from_markdown.py` 线性流程导入，解析器只会按 markdown 顺序把
阶段1→2→3→4→5→6 依次连接。但产品需求是把阶段1做成路由中枢：

- 阶段1需要能跳到阶段2/3/4/5中的**任意一个**（而不只是阶段2），阶段1→阶段2保留为默认边。
- 阶段2/3/4/5各自参观完后都应**返回阶段1**（而不是线性连到下一个展馆）。
- 阶段1需要新增一条通往阶段6（总结送别）的边，供"全部看完/参观者要求结束"时使用。

本脚本在标准导入/更新完成、拿到 train_task_id 之后运行一次，直接调用
`create_task_from_markdown.py` 里已验证过的通用连线函数
（create_script_flow / delete_script_step_flow / query_script_step_flows /
query_script_steps），修正连线拓扑，不改动核心解析器本身、不重建节点内容。

用法
----
    python skill_training_build/wire_museum_hub_routing.py <train_task_id>            # dry-run 预览
    python skill_training_build/wire_museum_hub_routing.py <train_task_id> --apply    # 实际执行

安全性
------
默认是 dry-run：只查询、打印计划要做的连线变更，不调用任何写接口。
必须显式加 --apply 才会真正创建/删除连线。
执行前会对定位到的6个阶段做硬断言（stepName 是否包含预期关键词），
不符合就直接中止，不会盲目按位置瞎连。
执行前会把当前完整的 steps/flows 快照写入 scratchpad 备份文件（若提供 --backup-path）。

isDefault 约定（参考 import_njtech_branching_task.py 的 compute_default_flags
与 .claude/skills/training-script-generator/reference.md 的"场景间互相跳转"章节）：
同一起点的多条出边中，有且仅有一条设为默认边。阶段1的默认边固定为→阶段2（王右木），
其余4条出边（→阶段3/4/5/6）为非默认。阶段2-5各自只有一条出边（回阶段1），天然为默认边。
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
)

DIRECT_OPENING_TRANSITION_PROMPT = (
    "【输入参数】\n"
    "- 下一阶段原始开场白 ${next_stage_opening}\n\n"
    "【整体生成目标】\n"
    "直接输出下一阶段原始开场白，不做额外改写。"
)


def welcome_back_transition_prompt(hall_name: str) -> str:
    return (
        "【输入参数】\n"
        "- 下一阶段原始开场白 ${next_stage_opening}\n\n"
        "【整体生成目标】\n"
        f"参观者刚结束{hall_name}的参观，即将返回导览总台。直接输出一句简短过渡语："
        "\"感谢您的参观，欢迎回到导览总台，接下来您还想去哪个场馆看看呢？\"不要输出下一阶段"
        "原始开场白，不要重复自我介绍或四大场馆的完整介绍。"
    )


# (name_substr_for_assertion, jump_in_condition, jump_out_condition_or_None)
HALLS = [
    ("王右木", "进入王右木真理拓源研习舱阶段", "结束王右木真理拓源研习舱返回导览总台"),
    ("三线建设", "进入三线建设耀绵州研习舱阶段", "结束三线建设耀绵州研习舱返回导览总台"),
    ("两弹", "进入两弹报国铸重器研习舱阶段", "结束两弹报国铸重器研习舱返回导览总台"),
    ("震后重生", "进入震后重生承大爱研习舱阶段", "结束震后重生承大爱研习舱返回导览总台"),
]
HUB_NAME_SUBSTR = "场馆集群总介绍"
SUMMARY_NAME_SUBSTR = "总结"
SUMMARY_CONDITION = "进入游览总结阶段"

FULL_HALL_NAME = {
    "王右木": "王右木真理拓源研习舱",
    "三线建设": "三线建设耀绵州研习舱",
    "两弹": "两弹报国铸重器研习舱",
    "震后重生": "震后重生承大爱研习舱",
}

EXPECTED_STEP_COUNT = 6


def step_name(step):
    return step.get("stepDetailDTO", {}).get("stepName") or step.get("stepName") or ""


def find_outgoing(flows, source_id):
    return [f for f in flows if f.get("scriptStepStartId") == source_id]


def find_flow_by_condition(flows, source_id, condition_text):
    for f in flows:
        if f.get("scriptStepStartId") == source_id and f.get("flowCondition") == condition_text:
            return f
    return None


def main():
    parser = argparse.ArgumentParser(description="把导览任务连线改造成路由中枢拓扑")
    parser.add_argument("train_task_id", help="已导入/更新过内容的训练任务 ID")
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

    if args.backup_path:
        Path(args.backup_path).write_text(
            json.dumps({"steps": step_list, "flows": flows}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"💾 已备份当前 steps/flows 到 {args.backup_path}")

    if len(business_steps) != EXPECTED_STEP_COUNT:
        print(
            f"❌ 查询到的业务阶段数为 {len(business_steps)}，期望 {EXPECTED_STEP_COUNT}。"
            "请确认 train_task_id 是否正确，脚本已中止。"
        )
        return

    by_name = {step_name(s): s for s in business_steps}

    hub_step = next((s for s in business_steps if HUB_NAME_SUBSTR in step_name(s)), None)
    summary_step = next((s for s in business_steps if SUMMARY_NAME_SUBSTR in step_name(s)), None)
    hall_steps = []
    for name_substr, cond_in, cond_out in HALLS:
        matches = [s for s in business_steps if name_substr in step_name(s)]
        hall_steps.append((name_substr, cond_in, cond_out, matches[0] if matches else None))

    print("📋 已定位关键阶段（请核对 stepName 是否与预期一致）：")
    print(f"  - 路由中枢: stepId={hub_step.get('stepId') if hub_step else None} name={step_name(hub_step) if hub_step else None!r}")
    for name_substr, cond_in, cond_out, s in hall_steps:
        print(f"  - 展馆[{name_substr}]: stepId={s.get('stepId') if s else None} name={step_name(s) if s else None!r}")
    print(f"  - 总结送别: stepId={summary_step.get('stepId') if summary_step else None} name={step_name(summary_step) if summary_step else None!r}")

    # 硬断言
    problems = []
    if hub_step is None:
        problems.append(f"未找到包含「{HUB_NAME_SUBSTR}」的阶段")
    if summary_step is None:
        problems.append(f"未找到包含「{SUMMARY_NAME_SUBSTR}」的阶段")
    for name_substr, _, _, s in hall_steps:
        if s is None:
            problems.append(f"未找到包含「{name_substr}」的展馆阶段")
    if problems:
        print("❌ 断言失败，脚本已中止，不会连线：")
        for p in problems:
            print(f"   - {p}")
        return
    print("✅ 关键阶段名称核对通过。")

    hub_id = hub_step["stepId"]
    summary_id = summary_step["stepId"]

    # 计划：删除阶段2→3、3→4、4→5、5→6 这条线性错误连线
    to_delete = []
    ordered_hall_ids = [s["stepId"] for _, _, _, s in hall_steps]
    linear_next = ordered_hall_ids[1:] + [summary_id]
    for (name_substr, cond_in, cond_out, s), next_id in zip(hall_steps, linear_next):
        outgoing = find_outgoing(flows, s["stepId"])
        for f in outgoing:
            if f.get("scriptStepEndId") == next_id:
                to_delete.append((name_substr, f))

    # 计划：新增 阶段1→阶段3/4/5（阶段1→阶段2已存在，不动）+ 阶段1→阶段6
    hub_new_edges = []
    for name_substr, cond_in, cond_out, s in hall_steps[1:]:  # 跳过阶段2（王右木），已有默认边
        existing = find_flow_by_condition(flows, hub_id, cond_in)
        if existing is None:
            hub_new_edges.append((name_substr, s["stepId"], cond_in))
    if find_flow_by_condition(flows, hub_id, SUMMARY_CONDITION) is None:
        hub_new_edges.append(("总结送别", summary_id, SUMMARY_CONDITION))

    # 计划：新增 阶段2/3/4/5 → 阶段1 返回边
    return_new_edges = []
    for name_substr, cond_in, cond_out, s in hall_steps:
        existing = find_flow_by_condition(flows, s["stepId"], cond_out)
        if existing is None:
            return_new_edges.append((name_substr, s["stepId"], cond_out))

    print("\n🔍 计划变更：")
    print(f"  删除 {len(to_delete)} 条线性错误连线：")
    for name_substr, f in to_delete:
        print(f"    - {name_substr} --{f.get('flowCondition')!r}--> (flowId={f.get('flowId')})")
    print(f"  新增 {len(hub_new_edges)} 条阶段1出边（isDefault=0）：")
    for name_substr, target_id, cond in hub_new_edges:
        print(f"    - 路由中枢 --{cond!r}--> {name_substr} ({target_id})")
    print(f"  新增 {len(return_new_edges)} 条返回中枢边（isDefault=1）：")
    for name_substr, source_id, cond in return_new_edges:
        print(f"    - {name_substr} --{cond!r}--> 路由中枢")

    if not args.apply:
        print("\n🧪 Dry-run 完成，未调用任何写接口。确认无误后加 --apply 参数实际执行。")
        return

    print("\n🚀 开始执行连线变更...")
    for name_substr, f in to_delete:
        delete_script_step_flow(args.train_task_id, f["flowId"])

    for name_substr, target_id, cond in hub_new_edges:
        create_script_flow(
            args.train_task_id, hub_id, target_id, cond,
            DIRECT_OPENING_TRANSITION_PROMPT, is_default=False,
        )

    for name_substr, source_id, cond in return_new_edges:
        create_script_flow(
            args.train_task_id, source_id, hub_id, cond,
            welcome_back_transition_prompt(FULL_HALL_NAME[name_substr]),
            is_default=True,
        )

    print("\n✅ 连线变更执行完毕。请务必用真实对话实测以下场景：")
    print("   1. 首次进入阶段1不给明确偏好 → 应默认进入王右木真理拓源研习舱")
    print("   2. 首次进入阶段1明确选择'两弹'或'震后重生' → 必须直接跳进对应展馆，不能落到王右木")
    print("   3. 任一展馆说'看完了/换一个' → 必须返回阶段1，而不是自动进入下一个展馆")
    print("   4. 四馆依次看完后回到阶段1 → 应自动跳转总结送别，不再询问")
    print("   5. 中途说'不想看了/结束游览' → 应直接跳转总结送别")


if __name__ == "__main__":
    main()
