#!/usr/bin/env python3
"""把「生命与急救教育（三任务选练）」线性连线改成三分支路由。

线性导入后：1→2→…→11→END。
改造为：
- 阶段1 任务选择 → 阶段2 第一场中毒急救（默认边，保留）
- 阶段1 → 阶段5 第一场理化伤害（进入理化伤害急救阶段）
- 阶段1 → 阶段9 踩踏案例分析（进入踩踏预防救助阶段）
- 删除误连：任务一复盘→第一场理化伤害、任务二复盘→踩踏案例分析
- 任务一/二/三复盘 → END（训练完成）
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from create_task_from_markdown import (  # noqa: E402
    create_script_flow,
    delete_script_step_flow,
    extract_start_end_ids,
    get_business_script_steps,
    load_env_config,
    query_script_step_flows,
    query_script_steps,
)

EXPECTED_STEP_COUNT = 11
KW_HUB_T1 = "进入中毒急救阶段"
KW_HUB_T2 = "进入理化伤害急救阶段"
KW_HUB_T3 = "进入踩踏预防救助阶段"
KW_END = "训练完成"

DIRECT_OPENING_TRANSITION_PROMPT = (
    "【输入参数】\n"
    "- 下一阶段原始开场白 ${next_stage_opening}\n\n"
    "【整体生成目标】\n"
    "直接输出下一阶段原始开场白，不做额外改写。"
)

END_TRANSITION_PROMPT = (
    "【输入参数】\n"
    "- 无\n\n"
    "【整体生成目标】\n"
    "学生已完成本次选中的急救训练。输出一句简短结束语（不超过50字），"
    "肯定其完成的内容，不要提问、不要展开新训练。"
)


def step_name(step):
    return step.get("stepDetailDTO", {}).get("stepName") or step.get("stepName") or ""


def find_outgoing(flows, source_id):
    return [f for f in flows if f.get("scriptStepStartId") == source_id]


def find_flow_by_condition(flows, source_id, condition_text):
    for f in flows:
        if f.get("scriptStepStartId") == source_id and f.get("flowCondition") == condition_text:
            return f
    return None


def locate(steps, exact_name):
    matches = [s for s in steps if step_name(s) == exact_name]
    return matches[0] if matches else None


def main() -> int:
    parser = argparse.ArgumentParser(description="枣庄急救三任务路由布线")
    parser.add_argument("train_task_id")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--backup-path", type=str, default=None)
    parser.add_argument("--env-file", type=str, default="")
    args = parser.parse_args()

    if args.env_file:
        from dotenv import load_dotenv

        load_dotenv(args.env_file, override=True)
        print(f"✅ Loaded environment config: {args.env_file}")
    else:
        load_env_config()

    step_list = query_script_steps(args.train_task_id)
    flows = query_script_step_flows(args.train_task_id)
    business_steps = get_business_script_steps(step_list)

    if args.backup_path:
        Path(args.backup_path).write_text(
            json.dumps({"steps": step_list, "flows": flows}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"💾 已备份 steps/flows 到 {args.backup_path}")

    if len(business_steps) != EXPECTED_STEP_COUNT:
        print(f"❌ 业务阶段数 {len(business_steps)} != {EXPECTED_STEP_COUNT}，脚本中止。")
        for s in business_steps:
            print(f"   - {step_name(s)}")
        return 1

    start_id, end_id = extract_start_end_ids(step_list)
    if not end_id:
        print("❌ 未找到 END 节点")
        return 1

    names = {
        "中枢": "任务选择",
        "中毒入口": "第一场中毒急救",
        "理化入口": "第一场理化伤害",
        "踩踏入口": "踩踏案例分析",
        "中毒复盘": "任务一复盘",
        "理化复盘": "任务二复盘",
        "踩踏复盘": "任务三复盘",
    }
    found = {}
    problems = []
    for label, name in names.items():
        s = locate(business_steps, name)
        found[label] = s
        if s is None:
            problems.append(f"未找到阶段「{name}」")
        else:
            print(f"  - {label}: {name} stepId={s['stepId']}")
    if problems:
        print("❌ 断言失败：")
        for p in problems:
            print(f"   - {p}")
        return 1

    hub_id = found["中枢"]["stepId"]
    t2_entry = found["理化入口"]["stepId"]
    t3_entry = found["踩踏入口"]["stepId"]
    t1_end = found["中毒复盘"]["stepId"]
    t2_end = found["理化复盘"]["stepId"]
    t3_end = found["踩踏复盘"]["stepId"]

    to_delete = []
    for label, src_id, dst_id in [
        ("任务一复盘→第一场理化伤害", t1_end, t2_entry),
        ("任务二复盘→踩踏案例分析", t2_end, t3_entry),
    ]:
        for f in find_outgoing(flows, src_id):
            if f.get("scriptStepEndId") == dst_id:
                to_delete.append((label, f))

    hub_new_edges = []
    for cond, dst_id, label in [
        (KW_HUB_T2, t2_entry, "第一场理化伤害"),
        (KW_HUB_T3, t3_entry, "踩踏案例分析"),
    ]:
        if find_flow_by_condition(flows, hub_id, cond) is None:
            hub_new_edges.append((label, dst_id, cond))

    end_new_edges = []
    for label, src_id in [
        ("任务一复盘", t1_end),
        ("任务二复盘", t2_end),
        ("任务三复盘", t3_end),
    ]:
        existing = find_flow_by_condition(flows, src_id, KW_END)
        if existing is None or existing.get("scriptStepEndId") != end_id:
            end_new_edges.append((label, src_id, KW_END))

    print("\n🔍 计划变更：")
    print(f"  删除 {len(to_delete)} 条边：")
    for label, f in to_delete:
        print(f"    - {label} --{f.get('flowCondition')!r}--> flowId={f.get('flowId')}")
    print(f"  新增 {len(hub_new_edges)} 条中枢出边（isDefault=0）：")
    for label, dst_id, cond in hub_new_edges:
        print(f"    - 中枢 --{cond!r}--> {label}")
    print(f"  新增 {len(end_new_edges)} 条复盘→END边：")
    for label, src_id, cond in end_new_edges:
        print(f"    - {label} --{cond!r}--> END")

    default_ok = any(
        f.get("scriptStepEndId") == found["中毒入口"]["stepId"]
        and f.get("flowCondition") == KW_HUB_T1
        for f in find_outgoing(flows, hub_id)
    )
    print(f"  默认边 中枢 --{KW_HUB_T1}--> 第一场中毒急救: {'已存在' if default_ok else '缺失（请检查线性导入）'}")

    if not args.apply:
        print("\n🧪 Dry-run 完成，加 --apply 执行。")
        return 0 if default_ok else 1

    if not default_ok:
        print("❌ 缺少默认边，中止以免拓扑不完整。")
        return 1

    print("\n🚀 执行连线变更...")
    for label, f in to_delete:
        delete_script_step_flow(args.train_task_id, f["flowId"])
        print(f"  ✂️  {label}")
    for label, dst_id, cond in hub_new_edges:
        create_script_flow(
            args.train_task_id, hub_id, dst_id, cond,
            DIRECT_OPENING_TRANSITION_PROMPT, is_default=False,
        )
        print(f"  ➕ 中枢 --{cond}--> {label}")
    for label, src_id, cond in end_new_edges:
        create_script_flow(
            args.train_task_id, src_id, end_id, cond,
            END_TRANSITION_PROMPT, is_default=True,
        )
        print(f"  ➕ {label} --{cond}--> END")
    print("\n✅ 布线完成。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
