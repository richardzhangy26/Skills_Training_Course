#!/usr/bin/env python3
"""补充连线脚本：把"统计微观观测站——统计热力学探究实训"任务从线性链改造成路由中枢回环拓扑。

克隆自 `wire_storage_workshop_hub.py`（储能热力工坊，已双档验证），仅替换阶段名与跳转关键词。

`训练剧本配置_统计微观观测站.md`（阶段1观测站引导员 + 阶段2玻尔兹曼展区 +
阶段3吉布斯展区 + 阶段4微观-宏观复盘大厅）经标准线性流程导入后，本脚本改造为：

- 阶段1可跳到阶段2/3中的任意一个展区，阶段1→阶段2为默认边；
- 阶段2/3参观完后，若仍有其他展区未参观则返回阶段1（默认边）；
- 阶段2/3各有一条直达阶段4复盘的边（两个展区集齐时使用，非默认）；
- 阶段1另有一条通往阶段4的边，供"未参观完毕但坚持结束"使用（非默认）。

用法
----
    python skill_training_build/wire_statistical_observatory_hub.py <train_task_id>            # dry-run 预览
    python skill_training_build/wire_statistical_observatory_hub.py <train_task_id> --apply    # 实际执行

默认 dry-run，只查询并打印计划；--apply 才会写。执行前对4个阶段做 stepName 关键词硬断言。
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
        f"学生刚结束{hall_name}的参观，即将返回引导台。直接输出一句简短过渡语："
        f"\"你刚结束{hall_name}的参观。欢迎回到引导台，接下来你还想去哪个展区，"
        "还是想结束参观去做整体复盘？\"不要输出下一阶段原始开场白，"
        "不要重复两个展区的完整介绍。"
    )


# (name_substr_for_assertion, jump_in_condition, jump_out_return_condition, jump_out_summary_condition)
HALLS = [
    ("玻尔兹曼", "进入玻尔兹曼展区阶段", "结束玻尔兹曼展区返回引导台", "结束玻尔兹曼展区进入复盘"),
    ("吉布斯", "进入吉布斯展区阶段", "结束吉布斯展区返回引导台", "结束吉布斯展区进入复盘"),
]
HUB_NAME_SUBSTR = "引导员"
SUMMARY_NAME_SUBSTR = "复盘"
SUMMARY_CONDITION = "进入观测站复盘阶段"

FULL_HALL_NAME = {
    "玻尔兹曼": "玻尔兹曼展区",
    "吉布斯": "吉布斯展区",
}

EXPECTED_STEP_COUNT = 4


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
    parser = argparse.ArgumentParser(description="把统计微观观测站任务连线改造成路由中枢回环拓扑")
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
        print(f"  - 展区[{name_substr}]: stepId={s.get('stepId') if s else None} name={step_name(s) if s else None!r}")
    print(f"  - 复盘大厅: stepId={summary_step.get('stepId') if summary_step else None} name={step_name(summary_step) if summary_step else None!r}")

    # 硬断言
    problems = []
    if hub_step is None:
        problems.append(f"未找到包含「{HUB_NAME_SUBSTR}」的阶段")
    if summary_step is None:
        problems.append(f"未找到包含「{SUMMARY_NAME_SUBSTR}」的阶段")
    for name_substr, _, _, _, s in hall_steps:
        if s is None:
            problems.append(f"未找到包含「{name_substr}」的展区阶段")
    if problems:
        print("❌ 断言失败，脚本已中止，不会连线：")
        for p in problems:
            print(f"   - {p}")
        return
    print("✅ 关键阶段名称核对通过。")

    hub_id = hub_step["stepId"]
    summary_id = summary_step["stepId"]

    # 计划：删除阶段2→3、3→4 这条线性错误连线
    to_delete = []
    ordered_hall_ids = [s["stepId"] for _, _, _, _, s in hall_steps]
    linear_next = ordered_hall_ids[1:] + [summary_id]
    for (name_substr, cond_in, cond_out, cond_summary, s), next_id in zip(hall_steps, linear_next):
        outgoing = find_outgoing(flows, s["stepId"])
        for f in outgoing:
            if f.get("scriptStepEndId") == next_id:
                to_delete.append((name_substr, f))

    # 计划：新增 阶段1→阶段3（阶段1→阶段2已存在，不动）+ 阶段1→阶段4
    hub_new_edges = []
    for name_substr, cond_in, cond_out, cond_summary, s in hall_steps[1:]:  # 跳过阶段2（玻尔兹曼），已有默认边
        existing = find_flow_by_condition(flows, hub_id, cond_in)
        if existing is None:
            hub_new_edges.append((name_substr, s["stepId"], cond_in))
    if find_flow_by_condition(flows, hub_id, SUMMARY_CONDITION) is None:
        hub_new_edges.append(("微观-宏观复盘大厅", summary_id, SUMMARY_CONDITION))

    # 计划：新增 阶段2/3 → 阶段1 返回边
    # 注意：线性导入的边（阶段2→3等）复用了返回条件文本，必须同时校验终点确实是中枢，
    # 否则会误判"返回边已存在"而漏建。
    return_new_edges = []
    for name_substr, cond_in, cond_out, cond_summary, s in hall_steps:
        existing = find_flow_by_condition(flows, s["stepId"], cond_out)
        if existing is None or existing.get("scriptStepEndId") != hub_id:
            return_new_edges.append((name_substr, s["stepId"], cond_out))

    # 计划：新增 阶段2/3 → 阶段4 直达复盘边（两馆集齐时不再返回引导台）
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
    print(f"  新增 {len(summary_new_edges)} 条展区直达复盘边（isDefault=0，两馆集齐时使用）：")
    for name_substr, source_id, cond in summary_new_edges:
        print(f"    - {name_substr} --{cond!r}--> 复盘大厅")

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
    print("   1. 首次进入引导台不给明确选择（'随便'） → 应澄清并请学生明确选择，不得默认落入玻尔兹曼展区")
    print("   2. 首次进入引导台明确选择'吉布斯' → 必须直接跳进吉布斯展区，不能落到玻尔兹曼")
    print("   3. 完成第一个展区 → 必须返回引导台（而不是直达复盘或自动进入下一个展区）")
    print("   4. 完成第二个展区（两馆集齐） → 必须直接进入复盘大厅，不再返回引导台")
    print("   5. 只参观了一馆就说'结束' → 引导台应先提醒剩余展区，学生坚持后再跳转复盘")
    print("   6. 复盘大厅总结报告输出后学生说'完成' → 输出「训练完成」结束")


if __name__ == "__main__":
    main()
