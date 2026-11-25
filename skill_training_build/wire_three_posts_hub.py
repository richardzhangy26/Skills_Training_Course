#!/usr/bin/env python3
"""把"物流岗位实训（三岗选考）"任务的线性连线改造成路由中枢回环拓扑。

背景
----
训练剧本配置（路由合并版）.md（17阶段：阶段1岗位选择中枢 + 分拣2-7 / 客服8-12 / 管理13-17）
经 create_configuration_from_markdown --with-steps 或 create_task_from_markdown 线性导入后，
连线为 1→2→…→17→END。本脚本将其改造为：

- 阶段1 → 阶段2（分拣入口，线性默认边，保留）/ 阶段8（客服入口）/ 阶段13（管理入口）/ END
- 阶段7 / 12 / 17 → 阶段1 返回边（各自默认边）
- 删除线性误连边：阶段7→8、阶段12→13、阶段17→END

isDefault 约定：同一起点有且仅有一条默认边。
入中枢边 transitionPrompt 用中枢开场白内联版（防 ${next_stage_opening} 偶发只输出片段）。

用法
----
    python wire_three_posts_hub.py <train_task_id> [--markdown <合并版md路径>]   # dry-run
    python wire_three_posts_hub.py <train_task_id> --apply [--backup-path xx.json]
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from create_task_from_markdown import (  # noqa: E402
    load_env_config,
    query_script_steps,
    query_script_step_flows,
    get_business_script_steps,
    extract_start_end_ids,
    create_script_flow,
    delete_script_step_flow,
)

DEFAULT_MD = (
    Path("/Users/zhangyichi/工作/能力训练/skills_training_course/"
         "四川交通职技术大学-物流专业实习四维智能体课程/训练剧本配置（路由合并版）.md")
)

KW_HUB_TO_SERVICE = "进入客户服务岗训练"
KW_HUB_TO_DATA = "进入管理岗训练"
KW_HUB_TO_END = "训练完成"
KW_SORT_END = "分拣训练完成"
KW_SERVICE_END = "客服训练完成"
KW_DATA_END = "管理训练完成"
KW_RETURN_LEGACY = "返回岗位选择"  # 旧回环拓扑遗留条件，出现即清理

HUB_SUBSTR = "岗位选择"
SORT_ENTRY_SUBSTR = "情境导入"        # 阶段2
SERVICE_ENTRY_SUBSTR = "投诉类型判断"  # 阶段8
DATA_ENTRY_SUBSTR = "库存数量分析认知"  # 阶段13
SORT_END_SUBSTR = "复盘反思"          # 阶段7
SERVICE_END_SUBSTR = "反思与总结"     # 阶段12
DATA_END_SUBSTR = "结论改进"          # 阶段17

EXPECTED_STEP_COUNT = 17

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
    "学生已明确结束本次实训。输出一句简短的结束语（不超过50字），"
    "肯定学生完成的学习内容并鼓励其将所学运用到实际岗位工作中，不要提问、不要展开新内容。"
)


def extract_hub_opening(md_path: Path) -> str:
    """从合并版 md 提取阶段1（岗位选择）开场白代码块全文。"""
    content = md_path.read_text(encoding="utf-8")
    m = re.search(r"^###\s*阶段1[::][^\n]*岗位选择", content, re.MULTILINE)
    if not m:
        raise ValueError("未在 md 中找到阶段1（岗位选择）标题")
    section = content[m.end():]
    nxt = re.search(r"^###\s*阶段2", section, re.MULTILINE)
    if nxt:
        section = section[:nxt.start()]
    om = re.search(r"\*\*开场白\*\*[::]\s*\n```\n(.*?)\n```", section, re.DOTALL)
    if not om:
        raise ValueError("未在阶段1中找到开场白代码块")
    return om.group(1).strip()


def build_hub_entry_transition(opening: str) -> str:
    return (
        "【输入参数】\n"
        "- 无（开场白已内置于本提示词，不使用外部变量）\n\n"
        "【输出要求】\n"
        "直接以实训导学助手身份原样输出以下开场白，不做任何改写、扩写、续写、解释，"
        "不输出任何其他文字：\n\n"
        f"{opening}\n\n"
        "【严禁】\n"
        "- 严禁输出\"设计说明\"\"小贴士\"等元文本\n"
        "- 严禁反问学生或追加开场白之外的新问题\n"
        "- 严禁以上一阶段带教师傅的口吻续讲\n"
        "- 严禁只输出数字、跳转关键词或开场白的片段，必须完整输出全部开场白内容"
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


def locate(steps, substr):
    matches = [s for s in steps if substr in step_name(s)]
    return matches[0] if matches else None


def main():
    parser = argparse.ArgumentParser(description="把三岗选考任务连线改造成路由中枢回环拓扑")
    parser.add_argument("train_task_id")
    parser.add_argument("--markdown", type=str, default=str(DEFAULT_MD), help="合并版剧本 md（提取中枢开场白）")
    parser.add_argument("--apply", action="store_true", help="实际执行（默认 dry-run）")
    parser.add_argument("--backup-path", type=str, default=None, help="执行前快照 steps/flows 到该 JSON")
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
        print(f"💾 已备份 steps/flows 到 {args.backup_path}")

    if len(business_steps) != EXPECTED_STEP_COUNT:
        print(f"❌ 业务阶段数 {len(business_steps)} != {EXPECTED_STEP_COUNT}，请确认任务 ID，脚本中止。")
        return 1

    start_id, end_id = extract_start_end_ids(step_list)
    if not end_id:
        print("❌ 未找到 END 节点，脚本中止。")
        return 1

    targets = {
        "中枢": HUB_SUBSTR,
        "分拣入口": SORT_ENTRY_SUBSTR,
        "客服入口": SERVICE_ENTRY_SUBSTR,
        "管理入口": DATA_ENTRY_SUBSTR,
        "分拣收尾": SORT_END_SUBSTR,
        "客服收尾": SERVICE_END_SUBSTR,
        "管理收尾": DATA_END_SUBSTR,
    }
    found = {}
    problems = []
    for label, substr in targets.items():
        s = locate(business_steps, substr)
        found[label] = s
        if s is None:
            problems.append(f"未找到包含「{substr}」的阶段（{label}）")
        else:
            print(f"  - {label}: stepId={s['stepId']} name={step_name(s)!r}")
    if problems:
        print("❌ 断言失败，脚本中止：")
        for p in problems:
            print(f"   - {p}")
        return 1

    hub_id = found["中枢"]["stepId"]
    service_entry_id = found["客服入口"]["stepId"]
    data_entry_id = found["管理入口"]["stepId"]
    sort_end_id = found["分拣收尾"]["stepId"]
    service_end_id = found["客服收尾"]["stepId"]
    data_end_id = found["管理收尾"]["stepId"]

    # 计划删除：线性误连边 + 旧回环拓扑的返回中枢边
    to_delete = []
    for label, src_id, dst_id in [
        ("分拣收尾→客服入口", sort_end_id, service_entry_id),
        ("客服收尾→管理入口", service_end_id, data_entry_id),
    ]:
        for f in find_outgoing(flows, src_id):
            if f.get("scriptStepEndId") == dst_id:
                to_delete.append((label, f))
    # 管理收尾→END 的线性误连边（条件非 管理训练完成 才算误连）
    for f in find_outgoing(flows, data_end_id):
        if f.get("scriptStepEndId") == end_id and f.get("flowCondition") != KW_DATA_END:
            to_delete.append(("管理收尾→END误连", f))
    # 旧回环拓扑遗留：收尾→中枢 的返回边
    for label, src_id in [("分拣收尾", sort_end_id), ("客服收尾", service_end_id), ("管理收尾", data_end_id)]:
        for f in find_outgoing(flows, src_id):
            if f.get("scriptStepEndId") == hub_id or f.get("flowCondition") == KW_RETURN_LEGACY:
                to_delete.append((f"{label}→中枢(旧回环)", f))

    # 计划新增：中枢出边（客服/管理/END，分拣默认边线性已建）
    hub_new_edges = []
    for cond, dst_id, label in [
        (KW_HUB_TO_SERVICE, service_entry_id, "客服入口"),
        (KW_HUB_TO_DATA, data_entry_id, "管理入口"),
        (KW_HUB_TO_END, end_id, "END"),
    ]:
        if find_flow_by_condition(flows, hub_id, cond) is None:
            hub_new_edges.append((label, dst_id, cond))

    # 计划新增：三个收尾→END 直达结束边（各自默认边；校验条件+终点双匹配保证幂等）
    end_new_edges = []
    for label, src_id, cond in [
        ("分拣收尾", sort_end_id, KW_SORT_END),
        ("客服收尾", service_end_id, KW_SERVICE_END),
        ("管理收尾", data_end_id, KW_DATA_END),
    ]:
        existing = find_flow_by_condition(flows, src_id, cond)
        if existing is None or existing.get("scriptStepEndId") != end_id:
            end_new_edges.append((label, src_id, cond))

    print("\n🔍 计划变更：")
    print(f"  删除 {len(to_delete)} 条边：")
    for label, f in to_delete:
        print(f"    - {label} --{f.get('flowCondition')!r}--> (flowId={f.get('flowId')})")
    print(f"  新增 {len(hub_new_edges)} 条中枢出边（isDefault=0）：")
    for label, dst_id, cond in hub_new_edges:
        print(f"    - 中枢 --{cond!r}--> {label}")
    print(f"  新增 {len(end_new_edges)} 条收尾→END边（isDefault=1，直达结束）：")
    for label, src_id, cond in end_new_edges:
        print(f"    - {label} --{cond!r}--> END")

    if not args.apply:
        print("\n🧪 Dry-run 完成，未调用写接口。确认无误后加 --apply 执行。")
        return 0

    print("\n🚀 执行连线变更...")
    for label, f in to_delete:
        delete_script_step_flow(args.train_task_id, f["flowId"])
        print(f"  ✂️  删除 {label}")

    for label, dst_id, cond in hub_new_edges:
        tp = END_TRANSITION_PROMPT if dst_id == end_id else DIRECT_OPENING_TRANSITION_PROMPT
        create_script_flow(args.train_task_id, hub_id, dst_id, cond, tp, is_default=False)
        print(f"  ➕ 中枢 --{cond}--> {label}")

    for label, src_id, cond in end_new_edges:
        create_script_flow(args.train_task_id, src_id, end_id, cond, END_TRANSITION_PROMPT, is_default=True)
        print(f"  ➕ {label} --{cond}--> END")

    print("\n✅ 布线完成。建议实测：")
    print("   1. 中枢明确选'客服/管理' → 必须落到对应入口，不得默认落分拣")
    print("   2. 中枢选择不明确 → 澄清而非默认进入")
    print("   3. 任一分支复盘总结完成 → 直接结束实训（不返回中枢）")
    print("   4. 中枢说'结束/不练了' → 输出 训练完成 到 END")
    return 0


if __name__ == "__main__":
    sys.exit(main())
