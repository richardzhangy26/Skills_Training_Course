#!/usr/bin/env python3
"""补充连线脚本：把"红色绵州四大场馆导览"任务从枢纽拓扑改造成固定接力链路拓扑。

背景
----
`wire_museum_hub_routing.py` 之前把任务连成了"阶段1路由中枢，参观完每馆都返回阶段1
重新选择"的枢纽拓扑。产品需求改为：阶段1只在最开始出现一次，参观者选定优先场馆后，
其余三馆按"原始顺序（王右木→三线建设→两弹→震后重生）跳过已选场馆"的固定顺序直接
接力衔接，不再返回阶段1。四条可能的完整链路：

    王右木(默认) -> 三线建设 -> 两弹 -> 震后重生 -> 总结
    三线建设     -> 王右木   -> 两弹 -> 震后重生 -> 总结
    两弹         -> 王右木   -> 三线建设 -> 震后重生 -> 总结
    震后重生     -> 王右木   -> 三线建设 -> 两弹 -> 总结

本脚本在枢纽拓扑基础上运行一次：
1. 删除枢纽拓扑遗留的 5 条边：阶段2/3/4/5 → 阶段1（返回中枢）共4条，
   以及 阶段1 → 阶段6（原"全部完成/主动结束"直达总结）1条——固定链路设计下
   阶段1永远不会直接跳总结，该边不再有效。
2. 新增 10 条馆际直连边（含 isDefault 设置，规则：每个起点的多条出边中，
   选最常出现的"下一馆"作为默认边 isDefault=1，其余为 isDefault=0）：
   阶段2→阶段3(默认)/阶段2→阶段4
   阶段3→阶段4(默认)/阶段3→阶段2/阶段3→阶段5
   阶段4→阶段5(默认)/阶段4→阶段2/阶段4→阶段6
   阶段5→阶段6(默认)/阶段5→阶段2

保留不动：START→阶段1、阶段1→阶段2(默认)、阶段1→阶段3、阶段1→阶段4、阶段1→阶段5、
阶段6→END（训练完成）。

用法
----
    python skill_training_build/wire_museum_fixed_chain.py <train_task_id>            # dry-run 预览
    python skill_training_build/wire_museum_fixed_chain.py <train_task_id> --apply    # 实际执行

安全性
------
默认是 dry-run：只查询、打印计划要做的连线变更，不调用任何写接口。
必须显式加 --apply 才会真正创建/删除连线。
执行前会对定位到的6个阶段做硬断言（stepName 是否包含预期关键词），
不符合就直接中止。执行前会把当前完整的 steps/flows 快照写入备份文件。
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

HUB_NAME_SUBSTR = "场馆集群总介绍"
SUMMARY_NAME_SUBSTR = "总结"
V1_NAME_SUBSTR, V1_COND = "王右木", "进入王右木真理拓源研习舱阶段"
V2_NAME_SUBSTR, V2_COND = "三线建设", "进入三线建设耀绵州研习舱阶段"
V3_NAME_SUBSTR, V3_COND = "两弹", "进入两弹报国铸重器研习舱阶段"
V4_NAME_SUBSTR, V4_COND = "震后重生", "进入震后重生承大爱研习舱阶段"
SUMMARY_COND = "进入游览总结阶段"

# 枢纽拓扑遗留、需要删除的边：(source_name_substr, condition_text)
HUB_LEFTOVER_EDGES = [
    (V1_NAME_SUBSTR, "结束王右木真理拓源研习舱返回导览总台"),
    (V2_NAME_SUBSTR, "结束三线建设耀绵州研习舱返回导览总台"),
    (V3_NAME_SUBSTR, "结束两弹报国铸重器研习舱返回导览总台"),
    (V4_NAME_SUBSTR, "结束震后重生承大爱研习舱返回导览总台"),
    (HUB_NAME_SUBSTR, SUMMARY_COND),  # 阶段1 -> 阶段6 直达总结，固定链路下不再有效
]

# 新增馆际直连边：(source_name_substr, target_name_substr_or_SUMMARY, condition_text, is_default)
NEW_EDGES = [
    (V1_NAME_SUBSTR, V2_NAME_SUBSTR, V2_COND, True),
    (V1_NAME_SUBSTR, V3_NAME_SUBSTR, V3_COND, False),
    (V2_NAME_SUBSTR, V3_NAME_SUBSTR, V3_COND, True),
    (V2_NAME_SUBSTR, V1_NAME_SUBSTR, V1_COND, False),
    (V2_NAME_SUBSTR, V4_NAME_SUBSTR, V4_COND, False),
    (V3_NAME_SUBSTR, V4_NAME_SUBSTR, V4_COND, True),
    (V3_NAME_SUBSTR, V1_NAME_SUBSTR, V1_COND, False),
    (V3_NAME_SUBSTR, SUMMARY_NAME_SUBSTR, SUMMARY_COND, False),
    (V4_NAME_SUBSTR, SUMMARY_NAME_SUBSTR, SUMMARY_COND, True),
    (V4_NAME_SUBSTR, V1_NAME_SUBSTR, V1_COND, False),
]

EXPECTED_STEP_COUNT = 6


def step_name(step):
    return step.get("stepDetailDTO", {}).get("stepName") or step.get("stepName") or ""


def find_flow_by_source_and_condition(flows, source_id, condition_text):
    for f in flows:
        if f.get("scriptStepStartId") == source_id and f.get("flowCondition") == condition_text:
            return f
    return None


def find_flow_by_source_target(flows, source_id, target_id):
    for f in flows:
        if f.get("scriptStepStartId") == source_id and f.get("scriptStepEndId") == target_id:
            return f
    return None


def main():
    parser = argparse.ArgumentParser(description="把导览任务连线从枢纽拓扑改造成固定接力链路拓扑")
    parser.add_argument("train_task_id", help="已跑过 wire_museum_hub_routing.py 的训练任务 ID")
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

    def locate(name_substr):
        matches = [s for s in business_steps if name_substr in step_name(s)]
        return matches[0] if matches else None

    hub_step = locate(HUB_NAME_SUBSTR)
    summary_step = locate(SUMMARY_NAME_SUBSTR)
    v1_step, v2_step, v3_step, v4_step = (
        locate(V1_NAME_SUBSTR), locate(V2_NAME_SUBSTR), locate(V3_NAME_SUBSTR), locate(V4_NAME_SUBSTR)
    )
    name_to_step = {
        HUB_NAME_SUBSTR: hub_step, SUMMARY_NAME_SUBSTR: summary_step,
        V1_NAME_SUBSTR: v1_step, V2_NAME_SUBSTR: v2_step,
        V3_NAME_SUBSTR: v3_step, V4_NAME_SUBSTR: v4_step,
    }

    print("📋 已定位关键阶段（请核对 stepName 是否与预期一致）：")
    for label, s in name_to_step.items():
        print(f"  - [{label}]: stepId={s.get('stepId') if s else None} name={step_name(s) if s else None!r}")

    problems = [f"未找到包含「{label}」的阶段" for label, s in name_to_step.items() if s is None]
    if problems:
        print("❌ 断言失败，脚本已中止，不会连线：")
        for p in problems:
            print(f"   - {p}")
        return
    print("✅ 关键阶段名称核对通过。")

    # 计划：删除枢纽拓扑遗留边
    to_delete = []
    for source_substr, cond in HUB_LEFTOVER_EDGES:
        source_step = name_to_step[source_substr]
        f = find_flow_by_source_and_condition(flows, source_step["stepId"], cond)
        if f is not None:
            to_delete.append((source_substr, f))

    # 计划：新增馆际直连边（跳过已存在的同源同目标边，避免重复创建）
    to_create = []
    for source_substr, target_substr, cond, is_default in NEW_EDGES:
        source_step = name_to_step[source_substr]
        target_step = name_to_step[target_substr]
        existing = find_flow_by_source_target(flows, source_step["stepId"], target_step["stepId"])
        if existing is None:
            to_create.append((source_substr, target_substr, cond, is_default))

    print(f"\n🔍 计划变更：")
    print(f"  删除 {len(to_delete)} 条枢纽拓扑遗留边：")
    for source_substr, f in to_delete:
        print(f"    - {source_substr} --{f.get('flowCondition')!r}--> (flowId={f.get('flowId')})")
    print(f"  新增 {len(to_create)} 条馆际直连边：")
    for source_substr, target_substr, cond, is_default in to_create:
        print(f"    - {source_substr} --{cond!r}--> {target_substr} (isDefault={'1' if is_default else '0'})")

    if not args.apply:
        print("\n🧪 Dry-run 完成，未调用任何写接口。确认无误后加 --apply 参数实际执行。")
        return

    print("\n🚀 开始执行连线变更...")
    for source_substr, f in to_delete:
        delete_script_step_flow(args.train_task_id, f["flowId"])

    for source_substr, target_substr, cond, is_default in to_create:
        source_step = name_to_step[source_substr]
        target_step = name_to_step[target_substr]
        create_script_flow(
            args.train_task_id, source_step["stepId"], target_step["stepId"], cond,
            DIRECT_OPENING_TRANSITION_PROMPT, is_default=is_default,
        )

    print("\n✅ 连线变更执行完毕。请务必用真实对话实测以下场景：")
    print("   1. 首次进入阶段1选择'两弹' -> 应依次走 两弹->王右木->三线建设->震后重生->总结")
    print("   2. 首次进入阶段1选择'震后重生' -> 应依次走 震后重生->王右木->三线建设->两弹->总结")
    print("   3. 每个展馆说'看完了'都应直接跳到下一馆（不经过阶段1）")
    print("   4. 最后一馆说'看完了' -> 应直接跳总结送别")


if __name__ == "__main__":
    main()
