#!/usr/bin/env python3
"""补充连线脚本：为"三选一盲选路由版"合并任务补上分支跳转与真实结束边。

背景
----
`训练剧本配置_三选一路由版.md`（路由阶段 + 3 个病例各 8 阶段 = 25 阶段）通过标准的
`create_task_from_markdown.py` 线性流程导入后，解析器只会按 markdown 顺序把
阶段 i 连到阶段 i+1，这会产生两类错误连线：

1. 阶段1（路由阶段）默认只会连到阶段2（案例A·稳定型心绞痛 专项问诊），
   缺少 阶段1→阶段10（案例B·不稳定型心绞痛）、阶段1→阶段18（案例C·急性心肌梗死）
   两条分支边。
2. 阶段9（案例A 全流程总结评价）、阶段17（案例B 全流程总结评价）会被错误地
   线性连到下一个病例的专项问诊开场，而不是连到真正的 END 节点。
   （阶段25 是 markdown 里最后一项，解析器会正确处理为连到 END，无需修正。）

本脚本在标准导入完成、拿到 train_task_id 之后运行一次，直接调用
`create_task_from_markdown.py` 里已验证过的通用连线函数
（create_script_flow / delete_script_step_flow / query_script_step_flows /
query_script_steps），修正上述两类连线，不改动核心解析器本身。

用法
----
    python skill_training_build/wire_router_branches.py <train_task_id>            # dry-run 预览
    python skill_training_build/wire_router_branches.py <train_task_id> --apply    # 实际执行

安全性
------
默认是 dry-run：只查询、打印计划要做的连线变更，不调用任何写接口。
必须显式加 --apply 才会真正创建/删除连线。
执行前会对定位到的关键阶段做硬断言（stepName 是否包含预期关键词），
不符合就直接中止，不会盲目按位置瞎连。

⚠️ 已知未验证风险：isDefault 语义
----------------------------------
`create_script_flow`（在 create_task_from_markdown.py 里）把每条新建连线的
`isDefault` 硬编码为 1。据项目记忆，`isDefault=1` 是"兜底边"标记。本脚本执行后，
阶段1（路由阶段）会同时有 3 条 isDefault=1 的出边（→阶段2 进入心血瘀阻病例，
→阶段10 进入痰湿内阻病例，→阶段18 进入气虚血瘀病例）——在此之前，这个代码库里
从未出现过"一个节点挂多条 isDefault=1 出边"的场景，所以这个组合是否会让平台
路由出问题，目前没有直接证据，只能导入后实测确认。

**验证方法**：三选一路由版任务导入 + 本脚本 --apply 执行完后，分别用输入
"1"、"2"、"3" 各走一遍路由阶段。
- 若输入"1"正确进入张某/李某对应病例（而不是全部或部分落到王某·稳定型心绞痛案例），
  说明 isDefault 组合没有问题，无需处理。
- 若输入"2"或"3"仍然落到了王某·稳定型心绞痛案例（案例A），说明多条 isDefault=1
  边之间存在"抢兜底"的冲突，需要把 进入痰湿内阻病例 / 进入气虚血瘀病例 这两条边的
  isDefault 改成 0，只保留 进入心血瘀阻病例 一条作为兜底边。
  本脚本已内置 `--branch-is-default 0` 参数支持这个调整，无需手改代码：
  重新以 --apply --branch-is-default 0 运行前，需要先手动删除本次已创建的
  进入痰湿内阻病例 / 进入气虚血瘀病例 两条连线（可在平台界面或用
  query_script_step_flows + delete_script_step_flow 定位删除），再重新执行。
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from create_task_from_markdown import (  # noqa: E402
    load_env_config,
    query_script_steps,
    query_script_step_flows,
    get_business_script_steps,
    extract_start_end_ids,
    ability_train_url,
    get_headers,
    delete_script_step_flow,
)
from create_task_from_markdown import DEFAULT_TRANSITION_HISTORY_NUM  # noqa: E402
import requests
from nanoid import generate


def create_script_flow_with_default(train_task_id, start_id, end_id, condition_text,
                                     transition_prompt="", is_default=1):
    """create_script_flow 的本地变体：暴露 isDefault，供路由分支边按需调整。

    仅供本脚本使用，不改动 create_task_from_markdown.py 里的共享实现。
    """
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

ROUTER_TRANSITION_PROMPT = (
    "【输入参数】\n"
    "- 下一阶段原始开场白 ${next_stage_opening}\n\n"
    "【整体生成目标】\n"
    "当本阶段触发跳转关键词后，由系统进入学生盲选到的病例。请直接使用下一阶段原始开场白作为过渡，"
    "不要添加任何额外说明。严禁把中文过渡语与跳转关键词混在同一条回复中。"
)

FINAL_TRANSITION_PROMPT = (
    "【输入参数】\n"
    "- 下一阶段原始开场白 ${next_stage_opening}\n\n"
    "【整体生成目标】\n"
    "本阶段为最终阶段。当满足结束条件时仅输出 完成训练。严禁把中文点评或结束语与结束关键词混在同一条回复中。"
)

EXPECTED_STAGE_COUNT = 25
# 0-indexed position within the 25 ordered business steps
IDX_ROUTER = 0        # 阶段1：路由阶段
IDX_CASE_A_END = 8    # 阶段9：案例A 全流程总结评价
IDX_CASE_B_START = 9  # 阶段10：案例B 专项问诊
IDX_CASE_B_END = 16   # 阶段17：案例B 全流程总结评价
IDX_CASE_C_START = 17 # 阶段18：案例C 专项问诊


def position_x(item):
    """positionDTO.x 平台返回的是字符串（如 '100'/'9700'），必须转成 int 再排序，
    否则字符串按字典序比较会把 '300' 排到 '2100' 前面，导致定位完全错乱。"""
    raw = item.get("positionDTO", {}).get("x", 0)
    try:
        return int(raw)
    except (TypeError, ValueError):
        return 0


def sorted_business_steps(train_task_id):
    step_list = query_script_steps(train_task_id)
    business = get_business_script_steps(step_list)
    business.sort(key=position_x)
    return business, step_list


def find_outgoing_flow(flows, source_step_id):
    matches = [f for f in flows if f.get("scriptStepStartId") == source_step_id]
    return matches


def step_name(step):
    return step.get("stepDetailDTO", {}).get("stepName") or step.get("stepName") or ""


def main():
    parser = argparse.ArgumentParser(description="修正三选一路由版合并任务的分支连线")
    parser.add_argument("train_task_id", help="标准导入合并版 markdown 后生成的训练任务 ID")
    parser.add_argument("--apply", action="store_true", help="实际执行连线变更（默认只 dry-run 预览）")
    parser.add_argument(
        "--branch-is-default", type=int, choices=[0, 1], default=1,
        help="新增的两条路由分支边（进入痰湿内阻病例/进入气虚血瘀病例）的 isDefault 取值，默认1。"
             "若实测发现输入2/3会误落到案例A（王某），说明多条isDefault=1的边冲突，"
             "需先手动删除本次新建的这两条分支边，再用 --branch-is-default 0 重新运行。",
    )
    args = parser.parse_args()

    load_env_config()

    business_steps, full_step_list = sorted_business_steps(args.train_task_id)
    start_node_id, end_node_id = extract_start_end_ids(full_step_list)

    if len(business_steps) != EXPECTED_STAGE_COUNT:
        print(
            f"❌ 查询到的业务阶段数为 {len(business_steps)}，期望 {EXPECTED_STAGE_COUNT}。"
            "请确认 train_task_id 是否为刚导入的三选一路由版任务，脚本已中止。"
        )
        return
    if not end_node_id:
        print("❌ 未找到 END 节点，脚本已中止。")
        return

    router_step = business_steps[IDX_ROUTER]
    case_a_end_step = business_steps[IDX_CASE_A_END]
    case_b_start_step = business_steps[IDX_CASE_B_START]
    case_b_end_step = business_steps[IDX_CASE_B_END]
    case_c_start_step = business_steps[IDX_CASE_C_START]

    print("📋 已定位关键阶段（请核对 stepName 是否与预期一致）：")
    for label, step in [
        ("阶段1 路由阶段", router_step),
        ("阶段9 案例A总结评价", case_a_end_step),
        ("阶段10 案例B专项问诊", case_b_start_step),
        ("阶段17 案例B总结评价", case_b_end_step),
        ("阶段18 案例C专项问诊", case_c_start_step),
    ]:
        name = step_name(step)
        print(f"  - {label}: stepId={step.get('stepId')} stepName={name!r}")
    print(f"  - END 节点: stepId={end_node_id}")

    # 硬断言：位置排序找到的阶段必须和预期名称匹配，防止 positionDTO 缺失/顺序错乱时静默连错线
    checks = [
        (router_step, "路由", "阶段1（路由阶段）"),
        (case_a_end_step, "总结评价", "阶段9（案例A总结评价）"),
        (case_b_start_step, "张某", "阶段10（案例B专项问诊，患者张某）"),
        (case_b_end_step, "总结评价", "阶段17（案例B总结评价）"),
        (case_c_start_step, "李某", "阶段18（案例C专项问诊，患者李某）"),
    ]
    for step, expected_substr, label in checks:
        name = step_name(step)
        if expected_substr not in name:
            print(
                f"❌ 断言失败：{label} 的 stepName={name!r} 不包含预期关键词 {expected_substr!r}。"
                "positionDTO 排序可能与文档顺序不一致，脚本已中止，不会连线。"
                "请人工核对该训练任务的阶段顺序后再决定是否调整脚本的定位逻辑。"
            )
            return
    print("✅ 关键阶段名称核对通过。")

    flows = query_script_step_flows(args.train_task_id)
    case_a_end_outgoing = find_outgoing_flow(flows, case_a_end_step.get("stepId"))
    case_b_end_outgoing = find_outgoing_flow(flows, case_b_end_step.get("stepId"))

    print("\n🔍 计划变更：")
    print(f"  1. 新增连线：阶段1 --进入痰湿内阻病例--> 阶段10 (案例B专项问诊)")
    print(f"  2. 新增连线：阶段1 --进入气虚血瘀病例--> 阶段18 (案例C专项问诊)")
    if case_a_end_outgoing:
        for f in case_a_end_outgoing:
            print(
                f"  3. 删除错误连线：阶段9 --{f.get('flowCondition')!r}--> "
                f"{f.get('scriptStepEndId')} (flowId={f.get('flowId')})，"
                "然后新增 阶段9 --完成训练--> END"
            )
    else:
        print("  3. ⚠️ 未查询到阶段9的现有出边，可能已被处理过；仍将补一条 阶段9 --完成训练--> END")
    if case_b_end_outgoing:
        for f in case_b_end_outgoing:
            print(
                f"  4. 删除错误连线：阶段17 --{f.get('flowCondition')!r}--> "
                f"{f.get('scriptStepEndId')} (flowId={f.get('flowId')})，"
                "然后新增 阶段17 --完成训练--> END"
            )
    else:
        print("  4. ⚠️ 未查询到阶段17的现有出边，可能已被处理过；仍将补一条 阶段17 --完成训练--> END")

    if not args.apply:
        print("\n🧪 Dry-run 完成，未调用任何写接口。确认无误后加 --apply 参数实际执行。")
        return

    print(f"\n🚀 开始执行连线变更...（分支边 isDefault={args.branch_is_default}）")
    create_script_flow_with_default(
        args.train_task_id, router_step["stepId"], case_b_start_step["stepId"],
        "进入痰湿内阻病例", ROUTER_TRANSITION_PROMPT, is_default=args.branch_is_default,
    )
    create_script_flow_with_default(
        args.train_task_id, router_step["stepId"], case_c_start_step["stepId"],
        "进入气虚血瘀病例", ROUTER_TRANSITION_PROMPT, is_default=args.branch_is_default,
    )
    for f in case_a_end_outgoing:
        delete_script_step_flow(args.train_task_id, f["flowId"])
    create_script_flow_with_default(
        args.train_task_id, case_a_end_step["stepId"], end_node_id,
        "完成训练", FINAL_TRANSITION_PROMPT,
    )
    for f in case_b_end_outgoing:
        delete_script_step_flow(args.train_task_id, f["flowId"])
    create_script_flow_with_default(
        args.train_task_id, case_b_end_step["stepId"], end_node_id,
        "完成训练", FINAL_TRANSITION_PROMPT,
    )
    print("\n✅ 连线变更执行完毕。")
    print("⚠️ 必测项：分别用输入 1 / 2 / 3 各走一遍路由阶段——")
    print("   输入2必须进入张某·不稳定型心绞痛案例，输入3必须进入李某·急性心肌梗死案例。")
    print("   若输入2或3仍落到王某·稳定型心绞痛案例，说明多条isDefault=1出边冲突，")
    print("   参见脚本顶部文档：需先删除本次新建的两条分支边，再用 --branch-is-default 0 重跑。")


if __name__ == "__main__":
    main()
