#!/usr/bin/env python3
"""补充连线脚本：把"热力学发展脉络探究（热力学名人博物馆）"任务从线性链改造成路由中枢回环拓扑。

背景
----
`训练剧本配置.md`（阶段1博物馆导览台 + 阶段2卡诺展区 + 阶段3克劳修斯展区 +
阶段4开尔文勋爵展区 + 阶段5中央大厅复盘）最初通过标准的
`create_task_from_markdown.py` 线性流程导入，解析器只会按 markdown 顺序把
阶段1→2→3→4→5 依次连接。但产品需求是把阶段1做成路由中枢：

- 阶段1需要能跳到阶段2/3/4中的**任意一个**展区（而不只是阶段2），阶段1→阶段2保留为默认边。
- 阶段2/3/4各自参观完后，若仍有其他展区未参观则**返回阶段1**，学生可以再选其余展区。
- 阶段2/3/4还各有一条直达阶段5（中央大厅复盘）的边：当该展区是第三个完成的展区
  （三馆集齐）时直接跳转复盘，不再返回导览台。
- 阶段1需要新增一条通往阶段5（中央大厅复盘）的边，供"学生未参观完毕但坚持结束"时使用。

本脚本在标准导入/更新完成、拿到 train_task_id 之后运行一次，直接调用
`create_task_from_markdown.py` 里已验证过的通用连线函数
（create_script_flow / delete_script_step_flow / query_script_step_flows /
query_script_steps），修正连线拓扑，不改动核心解析器本身、不重建节点内容。

用法
----
    python skill_training_build/wire_thermo_hub_routing.py <train_task_id>            # dry-run 预览
    python skill_training_build/wire_thermo_hub_routing.py <train_task_id> --apply    # 实际执行

安全性
------
默认是 dry-run：只查询、打印计划要做的连线变更，不调用任何写接口。
必须显式加 --apply 才会真正创建/删除连线。
执行前会对定位到的5个阶段做硬断言（stepName 是否包含预期关键词），
不符合就直接中止，不会盲目按位置瞎连。
执行前会把当前完整的 steps/flows 快照写入备份文件（若提供 --backup-path）。

isDefault 约定：同一起点的多条出边中，有且仅有一条设为默认边。
阶段1的默认边固定为→阶段2（卡诺展区），其余3条出边（→阶段3/4/5）为非默认。
阶段2-4各有两条出边：返回阶段1的边为默认边（参观状态不确定时的安全路线），
直达阶段5复盘的边为非默认。阶段5→END 由线性导入保留，为默认边。
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
        f"学生刚结束{hall_name}的参观，即将返回导览台。直接输出一句简短过渡语："
        f"\"你刚结束{hall_name}的参观。欢迎回到导览台，接下来你还想去哪个展区，"
        "还是想结束参观去做整体复盘？\"不要输出下一阶段原始开场白，"
        "不要重复三个展区的完整介绍。"
    )


# (name_substr_for_assertion, jump_in_condition, jump_out_return_condition, jump_out_summary_condition)
HALLS = [
    ("卡诺", "进入卡诺展区阶段", "结束卡诺展区返回导览台", "结束卡诺展区进入复盘"),
    ("克劳修斯", "进入克劳修斯展区阶段", "结束克劳修斯展区返回导览台", "结束克劳修斯展区进入复盘"),
    ("开尔文", "进入开尔文展区阶段", "结束开尔文展区返回导览台", "结束开尔文展区进入复盘"),
]
HUB_NAME_SUBSTR = "导览台"
SUMMARY_NAME_SUBSTR = "复盘"
SUMMARY_CONDITION = "进入脉络复盘阶段"

FULL_HALL_NAME = {
    "卡诺": "卡诺展区",
    "克劳修斯": "克劳修斯展区",
    "开尔文": "开尔文勋爵展区",
}

EXPECTED_STEP_COUNT = 5


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
    parser = argparse.ArgumentParser(description="把热力学博物馆任务连线改造成路由中枢回环拓扑")
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

    hub_step = next((s for s in business_steps if HUB_NAME_SUBSTR in step_name(s)), None)
    summary_step = next((s for s in business_steps if SUMMARY_NAME_SUBSTR in step_name(s)), None)
    hall_steps = []
    for name_substr, cond_in, cond_out, cond_summary in HALLS:
        matches = [s for s in business_steps if name_substr in step_name(s)]
        hall_steps.append((name_substr, cond_in, cond_out, cond_summary, matches[0] if matches else None))

    print("📋 已定位关键阶段（请核对 stepName 是否与预期一致）：")
    print(f"  - 路由中枢: stepId={hub_step.get('stepId') if hub_step else None} name={step_name(hub_step) if hub_step else None!r}")
    for name_substr, cond_in, cond_out, cond_summary, s in hall_steps:
        print(f"  - 展馆[{name_substr}]: stepId={s.get('stepId') if s else None} name={step_name(s) if s else None!r}")
    print(f"  - 中央大厅复盘: stepId={summary_step.get('stepId') if summary_step else None} name={step_name(summary_step) if summary_step else None!r}")

    # 硬断言
    problems = []
    if hub_step is None:
        problems.append(f"未找到包含「{HUB_NAME_SUBSTR}」的阶段")
    if summary_step is None:
        problems.append(f"未找到包含「{SUMMARY_NAME_SUBSTR}」的阶段")
    for name_substr, _, _, _, s in hall_steps:
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

    # 计划：删除阶段2→3、3→4、4→5 这条线性错误连线
    to_delete = []
    ordered_hall_ids = [s["stepId"] for _, _, _, _, s in hall_steps]
    linear_next = ordered_hall_ids[1:] + [summary_id]
    for (name_substr, cond_in, cond_out, cond_summary, s), next_id in zip(hall_steps, linear_next):
        outgoing = find_outgoing(flows, s["stepId"])
        for f in outgoing:
            if f.get("scriptStepEndId") == next_id:
                to_delete.append((name_substr, f))

    # 计划：新增 阶段1→阶段3/4（阶段1→阶段2已存在，不动）+ 阶段1→阶段5
    hub_new_edges = []
    for name_substr, cond_in, cond_out, cond_summary, s in hall_steps[1:]:  # 跳过阶段2（卡诺），已有默认边
        existing = find_flow_by_condition(flows, hub_id, cond_in)
        if existing is None:
            hub_new_edges.append((name_substr, s["stepId"], cond_in))
    if find_flow_by_condition(flows, hub_id, SUMMARY_CONDITION) is None:
        hub_new_edges.append(("中央大厅复盘", summary_id, SUMMARY_CONDITION))

    # 计划：新增 阶段2/3/4 → 阶段1 返回边
    # 注意：线性导入的边（阶段2→3等）复用了返回条件文本，必须同时校验终点确实是中枢，
    # 否则会误判"返回边已存在"而漏建。
    return_new_edges = []
    for name_substr, cond_in, cond_out, cond_summary, s in hall_steps:
        existing = find_flow_by_condition(flows, s["stepId"], cond_out)
        if existing is None or existing.get("scriptStepEndId") != hub_id:
            return_new_edges.append((name_substr, s["stepId"], cond_out))

    # 计划：新增 阶段2/3/4 → 阶段5 直达复盘边（三馆集齐时不再返回导览台）
    summary_new_edges = []
    for name_substr, cond_in, cond_out, cond_summary, s in hall_steps:
        existing = find_flow_by_condition(flows, s["stepId"], cond_summary)
        if existing is None or existing.get("scriptStepEndId") != summary_id:
            summary_new_edges.append((name_substr, s["stepId"], cond_summary))

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
    print(f"  新增 {len(summary_new_edges)} 条展区直达复盘边（isDefault=0，三馆集齐时使用）：")
    for name_substr, source_id, cond in summary_new_edges:
        print(f"    - {name_substr} --{cond!r}--> 中央大厅复盘")

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

    for name_substr, source_id, cond in summary_new_edges:
        create_script_flow(
            args.train_task_id, source_id, summary_id, cond,
            DIRECT_OPENING_TRANSITION_PROMPT,
            is_default=False,
        )

    print("\n✅ 连线变更执行完毕。请务必用真实对话实测以下场景：")
    print("   1. 首次进入导览台不给明确选择（'随便'） → 应澄清并请学生明确选择，不得默认落入卡诺展区")
    print("   2. 首次进入导览台明确选择'克劳修斯'或'开尔文' → 必须直接跳进对应展区，不能落到卡诺")
    print("   3. 完成第一个展区 → 必须返回导览台（而不是直达复盘或自动进入下一个展区）")
    print("   4. 完成第三个展区（三馆集齐） → 必须直接进入中央大厅复盘，不再返回导览台")
    print("   5. 只参观了一馆就说'结束' → 导览台应先提醒剩余展区，学生坚持后再跳转复盘")
    print("   6. 中央大厅复盘报告输出后学生说'完成' → 输出「训练完成」结束")


if __name__ == "__main__":
    main()
