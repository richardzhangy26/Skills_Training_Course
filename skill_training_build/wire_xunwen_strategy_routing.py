#!/usr/bin/env python3
"""补充连线脚本：为"讯问策略和方法"四策略中枢回环路由任务修正连线。

背景
----
`案例N-xxx案-训练剧本配置.md`（8阶段：程序启动 / 策略选择中枢 / 利导·冲击·迂回·迷惑
四策略实训 / 笔录制作 / 复盘总结）通过标准 `create_task_from_markdown.py` 线性导入后，
解析器只按 markdown 顺序把阶段 i 连到阶段 i+1，产生两类错误连线：

1. 阶段2（策略选择中枢）只会线性连到阶段3（利导型），且该边条件为竖线拼接的完整
   flowCondition 字符串；缺少到阶段4/5/6（冲击/迂回/迷惑）与阶段7（笔录制作）的分支边。
2. 阶段3→4、4→5、5→6 三条线性边为错误连线（策略阶段应回到中枢或去笔录阶段）；
   阶段6→7 线性边的条件同样是竖线拼接串，需拆成两条独立边。

本脚本在标准导入完成、拿到 train_task_id 之后运行，直接调用
`create_task_from_markdown.py` 里已验证过的通用连线函数修正连线，幂等可重复运行：
对中枢与四个策略阶段的出边，按"目标条件+目标节点"核对，多余边删除、缺失边补建。

拓扑（默认边规则：每个节点只保留一条 isDefault=1 兜底边）
----------------------------------------------------------
- 阶段1 → 阶段2 `进入策略选择阶段`（线性导入已建，校验保留）
- 阶段2 → 阶段3 `进入利导型讯问阶段`（默认边）
- 阶段2 → 阶段4 `进入冲击型讯问阶段`
- 阶段2 → 阶段5 `进入迂回型讯问阶段`
- 阶段2 → 阶段6 `进入迷惑型讯问阶段`
- 阶段2 → 阶段7 `进入笔录制作阶段`（学生声明讯问完成的兜底出口）
- 阶段3-6 → 阶段2 `返回策略选择阶段`（各自默认边，轮次耗尽安全回中枢）
- 阶段3-6 → 阶段7 `进入笔录制作阶段`（供述突破后直达）
- 阶段7 → 阶段8 `进入总结阶段`（线性导入已建，校验保留）
- 阶段8 → END `训练完成`（线性导入已建，校验保留）

用法
----
    python skill_training_build/wire_xunwen_strategy_routing.py <train_task_id>            # dry-run 预览
    python skill_training_build/wire_xunwen_strategy_routing.py <train_task_id> --apply    # 实际执行

安全性
------
默认 dry-run：只查询、打印计划变更，不调用写接口；必须显式 --apply 才执行。
执行前对8个阶段做 stepName 硬断言，不符合直接中止，不会盲目连线。
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
    """create_script_flow 的本地变体：暴露 isDefault，供路由分支边按需调整。"""
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


# 全部阶段统一使用的固定 transitionPrompt（与剧本 md 中各阶段字段完全一致）
FIXED_TRANSITION_PROMPT = (
    "【输入参数】\n"
    "- 下一阶段原始开场白 ${next_stage_opening}\n\n"
    "【输出要求】\n"
    "直接以新阶段角色身份原样输出 ${next_stage_opening}，不做任何改写、扩写、续写、解释。\n\n"
    "【严禁】\n"
    "- 严禁输出\"设计说明\"\"设计亮点\"\"小贴士\"等元文本\n"
    "- 严禁反问学生或追加新问题\n"
    "- 严禁以上一阶段角色口吻续讲\n"
    "- 严禁添加括号外的旁白、台词标注或 markdown 格式说明"
)

EXPECTED_STAGE_COUNT = 8

# 阶段名断言关键词（按 positionDTO.x 排序后的 0-indexed 位置）
STAGE_CHECKS = [
    ("程序启动", "阶段1（讯问程序启动）"),
    ("策略选择", "阶段2（讯问策略选择中枢）"),
    ("利导", "阶段3（利导型讯问实训）"),
    ("冲击", "阶段4（冲击型讯问实训）"),
    ("迂回", "阶段5（迂回型讯问实训）"),
    ("迷惑", "阶段6（迷惑型讯问实训）"),
    ("笔录", "阶段7（讯问笔录制作）"),
    ("复盘", "阶段8（实训复盘总结）"),
]

C_RETURN = "返回策略选择阶段"
C_RECORD = "进入笔录制作阶段"
C_HUB_ENTRY = "进入策略选择阶段"
C_SUMMARY = "进入总结阶段"
C_DONE = "训练完成"
STRATEGY_CONDITIONS = [
    "进入利导型讯问阶段",
    "进入冲击型讯问阶段",
    "进入迂回型讯问阶段",
    "进入迷惑型讯问阶段",
]


def position_x(item):
    """positionDTO.x 平台返回的是字符串，必须转 int 再排序。"""
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


def step_name(step):
    return step.get("stepDetailDTO", {}).get("stepName") or step.get("stepName") or ""


def outgoing(flows, step_id):
    return [f for f in flows if f.get("scriptStepStartId") == step_id]


def reconcile_edges(train_task_id, flows, source_step, desired, apply_changes,
                     hub_entry_prompt=None):
    """将 source_step 的出边核对为 desired 列表：[(condition, end_id, is_default), ...]。

    已存在的 (condition, end_id) 组合保留；多余边删除；缺失边补建。幂等。
    hub_entry_prompt 非空时，指向中枢的边（进入/返回策略选择阶段）使用该
    内联开场白版过渡提示词，其余边使用 FIXED_TRANSITION_PROMPT。
    返回 (删除数, 新建数)。
    """
    sid = source_step["stepId"]
    name = step_name(source_step)
    current = outgoing(flows, sid)
    desired_set = {(c, e) for c, e, _ in desired}

    removed = created = 0
    for f in current:
        key = (f.get("flowCondition"), f.get("scriptStepEndId"))
        if key in desired_set:
            print(f"  ✔ 保留：{name} --{f.get('flowCondition')!r}--> {f.get('scriptStepEndId')}")
            continue
        print(f"  ✂ 删除：{name} --{f.get('flowCondition')!r}--> {f.get('scriptStepEndId')} (flowId={f.get('flowId')})")
        if apply_changes:
            delete_script_step_flow(train_task_id, f["flowId"])
        removed += 1

    existing = {(f.get("flowCondition"), f.get("scriptStepEndId")) for f in current}
    for condition, end_id, is_default in desired:
        if (condition, end_id) in existing:
            continue
        prompt = FIXED_TRANSITION_PROMPT
        if hub_entry_prompt and condition in (C_HUB_ENTRY, C_RETURN):
            prompt = hub_entry_prompt
        print(f"  ＋ 新建：{name} --{condition}--> {end_id} (isDefault={is_default})")
        if apply_changes:
            create_script_flow_with_default(
                train_task_id, sid, end_id, condition,
                prompt, is_default=is_default,
            )
        created += 1
    return removed, created


def main():
    parser = argparse.ArgumentParser(description="修正讯问策略和方法四策略中枢回环任务的连线")
    parser.add_argument("train_task_id", help="标准导入剧本 markdown 后生成的训练任务 ID")
    parser.add_argument("--apply", action="store_true", help="实际执行连线变更（默认只 dry-run 预览）")
    parser.add_argument(
        "--branch-is-default", type=int, choices=[0, 1], default=0,
        help="中枢到非首选策略分支边（冲击/迂回/迷惑/笔录）及策略阶段到笔录边的 isDefault 取值，默认0，"
             "保证每个节点只有一条 isDefault=1 兜底边（中枢→利导、各策略→返回中枢）。"
             "若实测发现明确选择某策略却落到别的阶段，可删除相关边后改用 1 重试。",
    )
    parser.add_argument(
        "--markdown", default="",
        help="对应剧本md路径；提供后将解析阶段2开场白，进入/返回中枢的边使用该"
             "开场白内联版过渡提示词（修复 ${next_stage_opening} 模板偶发只输出片段的缺陷）。",
    )
    args = parser.parse_args()

    load_env_config()

    hub_entry_prompt = None
    if args.markdown:
        from wire_fix_hub_entry_transition import extract_hub_opening, build_transition_prompt
        hub_entry_prompt = build_transition_prompt(extract_hub_opening(Path(args.markdown)))
        print(f"📄 已加载剧本开场白，入中枢边将使用内联版过渡提示词。")

    business_steps, full_step_list = sorted_business_steps(args.train_task_id)

    if len(business_steps) != EXPECTED_STAGE_COUNT:
        print(
            f"❌ 查询到的业务阶段数为 {len(business_steps)}，期望 {EXPECTED_STAGE_COUNT}。"
            "请确认 train_task_id 是否为刚导入的讯问策略和方法任务，脚本已中止。"
        )
        return
    if not extract_start_end_ids(full_step_list)[1]:
        print("❌ 未找到 END 节点，脚本已中止。")
        return

    print("📋 已定位阶段（按画布 x 坐标排序）：")
    for idx, step in enumerate(business_steps, start=1):
        print(f"  - 阶段{idx}: stepId={step.get('stepId')} stepName={step_name(step)!r}")

    for idx, ((expected_substr, label), step) in enumerate(zip(STAGE_CHECKS, business_steps)):
        name = step_name(step)
        if expected_substr not in name:
            print(
                f"❌ 断言失败：{label} 的 stepName={name!r} 不包含预期关键词 {expected_substr!r}。"
                "排序可能与文档顺序不一致，脚本已中止，不会连线。"
            )
            return
    print("✅ 阶段名称核对通过。")

    s1, hub, s3, s4, s5, s6, record, review = business_steps

    flows = query_script_step_flows(args.train_task_id)

    hub_desired = [
        (STRATEGY_CONDITIONS[0], s3["stepId"], 1),
        (STRATEGY_CONDITIONS[1], s4["stepId"], args.branch_is_default),
        (STRATEGY_CONDITIONS[2], s5["stepId"], args.branch_is_default),
        (STRATEGY_CONDITIONS[3], s6["stepId"], args.branch_is_default),
        (C_RECORD, record["stepId"], args.branch_is_default),
    ]
    strategy_desired = [
        (C_RETURN, hub["stepId"], 1),
        (C_RECORD, record["stepId"], args.branch_is_default),
    ]
    linear_desired = [
        (s1, [(C_HUB_ENTRY, hub["stepId"], 1)]),
        (record, [(C_SUMMARY, review["stepId"], 1)]),
    ]

    print("\n🔍 核对连线（✔保留 / ✂删除 / ＋新建）：")
    total_removed = total_created = 0
    for source, desired in (
        [(hub, hub_desired)]
        + [(s, strategy_desired) for s in (s3, s4, s5, s6)]
        + linear_desired
    ):
        removed, created = reconcile_edges(
            args.train_task_id, flows, source, desired, args.apply,
            hub_entry_prompt=hub_entry_prompt,
        )
        total_removed += removed
        total_created += created

    # 阶段8 → END 校验（线性导入建立，一般无需变更）
    end_node_id = extract_start_end_ids(full_step_list)[1]
    review_out = outgoing(flows, review["stepId"])
    done_ok = any(
        f.get("flowCondition") == C_DONE and f.get("scriptStepEndId") == end_node_id
        for f in review_out
    )
    if done_ok:
        print(f"  ✔ 保留：{step_name(review)} --{C_DONE}--> END")
    else:
        print(f"  ＋ 新建：{step_name(review)} --{C_DONE}--> END (isDefault=1)")
        if args.apply:
            create_script_flow_with_default(
                args.train_task_id, review["stepId"], end_node_id,
                C_DONE, FIXED_TRANSITION_PROMPT, is_default=1,
            )
        total_created += 1

    print(f"\n📊 汇总：删除 {total_removed} 条，新建 {total_created} 条。")
    if not args.apply:
        print("🧪 Dry-run 完成，未调用任何写接口。确认无误后加 --apply 参数实际执行。")
    else:
        print("🚀 连线变更已执行。请查询连线列表复核，并在平台上用 1/2/3/4 各走一遍路由验证。")


if __name__ == "__main__":
    main()
