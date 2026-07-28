# 红色绵州数智研习所四路线剧本 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将红色绵州数智研习所剧本改造成一个选择节点、四条独立场馆路线和一个共享总结节点，并把过度直接的追问改成需要参观者自主组织具体问题的中等难度引导。

**Architecture:** `训练剧本配置.md` 只维护公共入口、共享总结和总拓扑；四个独立 Markdown 分别维护 `1-2-3-4`、`2-1-3-4`、`3-1-2-4`、`4-1-2-3` 四条线性路线。新增专用导入器读取五个 Markdown，装配为 18 个业务节点和 22 条真实连线；默认只做本地 dry-run，平台写入必须显式使用 `--apply --delete-existing --yes`。

**Tech Stack:** Python 3、pytest、现有 `skill_training_build/create_task_from_markdown.py` 解析/API 函数、Markdown、`training-prompt-expert` strict validator。

## Global Constraints

- 原始 DOCX `skills_training_course/绵阳职业技术学院-峥嵘绵阳/红色绵州数智研习所实训示例.docx` 只读，不得修改。
- 业务阶段必须为 18 个：1 个场馆选择、16 个路线独立场馆节点、1 个共享总结。
- 连线必须为 22 条：1 条 START 边、4 条选路边、12 条路线内部边、4 条汇总边、1 条 END 边。
- 四条路线固定为 `1→2→3→4`、`2→1→3→4`、`3→1→2→4`、`4→1→2→3`。
- 参观者未明确选择、表示随意或请小绵安排时，只有路线 1 是默认边。
- 同一场馆在不同路线中必须使用独立且全局唯一的阶段名称。
- 所有非空 `flowCondition` 必须是中文、全局唯一，并与提示词跳转分支逐字一致。
- 正常回答后不得替参观者给出下一道具体问题；“是”“想”“继续”不得触发新的知识讲解。
- 同一场馆跨路线的角色、知识库、事实边界、语气、数字人和自主提问规则必须一致。
- 四条路线中的小绵必须复用同一数字人配置；资源 ID 只能来自当前平台清单，无法核实时保守留空。
- 王右木、两弹城内容只复用现有权威材料；三线建设、震后重生不得扩写原任务文档之外的具体史实。
- 所有 Markdown 必须通过 `validate_markdown.py --strict`。
- 本轮只完成本地文件、测试和 dry-run，不调用平台写接口，不部署。
- `skills_training_course/` 被仓库 `.gitignore` 忽略；不得使用 `git add -f` 强制纳入课程资产。

---

## File Map

### Create

- `skills_training_course/绵阳职业技术学院-峥嵘绵阳/训练剧本路线1-默认-1-2-3-4.md`
  - 路线 1 的四个独立场馆阶段。
- `skills_training_course/绵阳职业技术学院-峥嵘绵阳/训练剧本路线2-2-1-3-4.md`
  - 路线 2 的四个独立场馆阶段。
- `skills_training_course/绵阳职业技术学院-峥嵘绵阳/训练剧本路线3-3-1-2-4.md`
  - 路线 3 的四个独立场馆阶段。
- `skills_training_course/绵阳职业技术学院-峥嵘绵阳/训练剧本路线4-4-1-2-3.md`
  - 路线 4 的四个独立场馆阶段。
- `skill_training_build/import_mianzhou_museum_routes.py`
  - 解析五个 Markdown、装配路由、dry-run、平台写入和只读回查。
- `tests/test_import_mianzhou_museum_routes.py`
  - 18 节点/22 边、路线顺序、默认边、唯一条件、dry-run 安全性测试。

### Modify

- `skills_training_course/绵阳职业技术学院-峥嵘绵阳/训练剧本配置.md:1-1012`
  - 改为公共入口与共享总结文件，删除共享场馆节点及其历史回忆路由。

### Reference Only

- `skills_training_course/绵阳职业技术学院-峥嵘绵阳/红色绵州数智研习所实训示例.docx`
- `skills_training_course/绵阳职业技术学院-峥嵘绵阳/王右木简介.docx`
- `skills_training_course/绵阳职业技术学院-峥嵘绵阳/两弹城博物馆简介.docx`
- `.agents/skills/training-prompt-expert/references/templates/template_moni_v2.md`
- `.agents/skills/training-prompt-expert/references/templates/template_zongjie_v2.md`
- `.agents/skills/training-prompt-expert/references/examples/ex_branch_simple.md`
- `.agents/skills/training-prompt-expert/references/examples/ex_transition.md`

---

### Task 1: 用 TDD 建立五文件路由装配核心

**Files:**

- Create: `skill_training_build/import_mianzhou_museum_routes.py`
- Create: `tests/test_import_mianzhou_museum_routes.py`

**Interfaces:**

- Consumes: `create_task_from_markdown.parse_markdown(path: Path) -> list[dict[str, Any]]`
- Produces: `RouteSpec`、`PackagePlan`、`assemble_route_package(public_steps, route_steps_by_number) -> PackagePlan`、`load_route_package(entry_path, route_paths=None) -> PackagePlan`

- [ ] **Step 1: 写出装配核心的失败测试**

在 `tests/test_import_mianzhou_museum_routes.py` 写入：

```python
from __future__ import annotations

from skill_training_build import import_mianzhou_museum_routes as importer


def make_public_steps() -> list[dict]:
    return [
        {
            "stepName": "场馆集群总介绍",
            "flowCondition": "进入路线1第1站王右木真理拓源研习舱阶段",
            "transitionPrompt": "直接输出下一阶段原始开场白。",
        },
        {
            "stepName": "游览结束（总结送别）",
            "flowCondition": "训练完成",
            "transitionPrompt": "",
        },
    ]


def make_route_steps(route_number: int) -> list[dict]:
    halls = importer.ROUTE_HALL_ORDERS[route_number]
    result = []
    for position, hall_name in enumerate(halls, start=1):
        if position < 4:
            next_hall = halls[position]
            condition = f"进入路线{route_number}第{position + 1}站{next_hall}阶段"
        else:
            condition = f"进入路线{route_number}完成后的游览总结阶段"
        result.append(
            {
                "stepName": f"路线{route_number}-第{position}站-{hall_name}",
                "flowCondition": condition,
                "transitionPrompt": "直接输出下一阶段原始开场白。",
                "llmPrompt": "# Role\n【自主提问规则】",
            }
        )
    return result


def test_assemble_route_package_builds_18_nodes_and_22_flows() -> None:
    route_steps = {number: make_route_steps(number) for number in range(1, 5)}

    plan = importer.assemble_route_package(make_public_steps(), route_steps)

    assert len(plan.steps) == 18
    assert len(plan.flows) == 22
    assert plan.steps[0]["stepName"] == "场馆集群总介绍"
    assert plan.steps[-1]["stepName"] == "游览结束（总结送别）"
    assert len({step["stepName"] for step in plan.steps}) == 18


def test_assemble_route_package_keeps_exact_route_orders() -> None:
    route_steps = {number: make_route_steps(number) for number in range(1, 5)}

    plan = importer.assemble_route_package(make_public_steps(), route_steps)
    actual = {
        number: [
            step["stepName"].split("-", 3)[-1]
            for step in plan.steps
            if step["stepName"].startswith(f"路线{number}-")
        ]
        for number in range(1, 5)
    }

    assert actual == importer.ROUTE_HALL_ORDERS


def test_selector_has_one_default_route_and_conditions_are_unique() -> None:
    route_steps = {number: make_route_steps(number) for number in range(1, 5)}

    plan = importer.assemble_route_package(make_public_steps(), route_steps)
    selector_flows = [flow for flow in plan.flows if flow["sourceName"] == "场馆集群总介绍"]
    non_empty_conditions = [flow["flowCondition"] for flow in plan.flows if flow["flowCondition"]]

    assert len(selector_flows) == 4
    assert [flow["isDefault"] for flow in selector_flows] == [True, False, False, False]
    assert len(non_empty_conditions) == len(set(non_empty_conditions))


def test_wrong_route_order_is_rejected() -> None:
    route_steps = {number: make_route_steps(number) for number in range(1, 5)}
    route_steps[3][0]["stepName"] = "路线3-第1站-王右木真理拓源研习舱"

    try:
        importer.assemble_route_package(make_public_steps(), route_steps)
    except ValueError as exc:
        assert "路线3第1站应为「两弹报国铸重器研习舱」" in str(exc)
    else:
        raise AssertionError("错误路线顺序必须被拒绝")
```

- [ ] **Step 2: 运行测试并确认因模块不存在而失败**

Run:

```bash
python -m pytest tests/test_import_mianzhou_museum_routes.py -v
```

Expected: collection error，包含 `cannot import name 'import_mianzhou_museum_routes'`。

- [ ] **Step 3: 实现最小装配核心**

在 `skill_training_build/import_mianzhou_museum_routes.py` 写入：

```python
#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from . import create_task_from_markdown as base
except ImportError:
    import create_task_from_markdown as base


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ENTRY_PATH = (
    ROOT
    / "skills_training_course"
    / "绵阳职业技术学院-峥嵘绵阳"
    / "训练剧本配置.md"
)
DEFAULT_ROUTE_PATHS = {
    1: DEFAULT_ENTRY_PATH.with_name("训练剧本路线1-默认-1-2-3-4.md"),
    2: DEFAULT_ENTRY_PATH.with_name("训练剧本路线2-2-1-3-4.md"),
    3: DEFAULT_ENTRY_PATH.with_name("训练剧本路线3-3-1-2-4.md"),
    4: DEFAULT_ENTRY_PATH.with_name("训练剧本路线4-4-1-2-3.md"),
}

HALL_1 = "王右木真理拓源研习舱"
HALL_2 = "三线建设耀绵州研习舱"
HALL_3 = "两弹报国铸重器研习舱"
HALL_4 = "震后重生承大爱研习舱"
ROUTE_HALL_ORDERS = {
    1: [HALL_1, HALL_2, HALL_3, HALL_4],
    2: [HALL_2, HALL_1, HALL_3, HALL_4],
    3: [HALL_3, HALL_1, HALL_2, HALL_4],
    4: [HALL_4, HALL_1, HALL_2, HALL_3],
}
SELECTOR_CONDITIONS = {
    1: "进入路线1第1站王右木真理拓源研习舱阶段",
    2: "进入路线2第1站三线建设耀绵州研习舱阶段",
    3: "进入路线3第1站两弹报国铸重器研习舱阶段",
    4: "进入路线4第1站震后重生承大爱研习舱阶段",
}
SUMMARY_CONDITIONS = {
    number: f"进入路线{number}完成后的游览总结阶段"
    for number in range(1, 5)
}


@dataclass(frozen=True)
class PackagePlan:
    steps: list[dict[str, Any]]
    flows: list[dict[str, Any]]
    positions: list[dict[str, int]]


def _validate_public_steps(public_steps: list[dict[str, Any]]) -> None:
    names = [step.get("stepName") for step in public_steps]
    expected = ["场馆集群总介绍", "游览结束（总结送别）"]
    if names != expected:
        raise ValueError(f"公共入口文件阶段必须为 {expected}，实际为 {names}")
    if public_steps[0].get("flowCondition") != SELECTOR_CONDITIONS[1]:
        raise ValueError("场馆选择阶段的默认 flowCondition 必须指向路线1")
    if public_steps[1].get("flowCondition") != "训练完成":
        raise ValueError("总结阶段 flowCondition 必须为「训练完成」")


def _validate_route_steps(route_number: int, steps: list[dict[str, Any]]) -> None:
    if len(steps) != 4:
        raise ValueError(f"路线{route_number}必须包含4个阶段，实际为{len(steps)}个")
    expected_halls = ROUTE_HALL_ORDERS[route_number]
    for position, (step, hall_name) in enumerate(zip(steps, expected_halls), start=1):
        expected_name = f"路线{route_number}-第{position}站-{hall_name}"
        if step.get("stepName") != expected_name:
            raise ValueError(
                f"路线{route_number}第{position}站应为「{hall_name}」，"
                f"实际阶段名为「{step.get('stepName')}」"
            )
        expected_condition = (
            f"进入路线{route_number}第{position + 1}站{expected_halls[position]}阶段"
            if position < 4
            else SUMMARY_CONDITIONS[route_number]
        )
        if step.get("flowCondition") != expected_condition:
            raise ValueError(
                f"路线{route_number}第{position}站 flowCondition 应为"
                f"「{expected_condition}」，实际为「{step.get('flowCondition')}」"
            )


def _build_positions() -> list[dict[str, int]]:
    positions = [{"x": 700, "y": 120}]
    for route_number in range(1, 5):
        x = 100 + (route_number - 1) * 400
        positions.extend({"x": x, "y": 380 + index * 260} for index in range(4))
    positions.append({"x": 700, "y": 1520})
    return positions


def assemble_route_package(
    public_steps: list[dict[str, Any]],
    route_steps_by_number: dict[int, list[dict[str, Any]]],
) -> PackagePlan:
    _validate_public_steps(public_steps)
    if set(route_steps_by_number) != {1, 2, 3, 4}:
        raise ValueError("必须同时提供路线1、路线2、路线3、路线4")
    for route_number in range(1, 5):
        _validate_route_steps(route_number, route_steps_by_number[route_number])

    selector = public_steps[0]
    summary = public_steps[1]
    steps = [selector]
    route_start_indexes: dict[int, int] = {}
    for route_number in range(1, 5):
        route_start_indexes[route_number] = len(steps)
        steps.extend(route_steps_by_number[route_number])
    summary_index = len(steps)
    steps.append(summary)

    flows: list[dict[str, Any]] = [
        {
            "sourceIndex": None,
            "targetIndex": 0,
            "sourceName": "START",
            "targetName": selector["stepName"],
            "flowCondition": "",
            "transitionPrompt": "",
            "isDefault": True,
        }
    ]
    for route_number in range(1, 5):
        target_index = route_start_indexes[route_number]
        flows.append(
            {
                "sourceIndex": 0,
                "targetIndex": target_index,
                "sourceName": selector["stepName"],
                "targetName": steps[target_index]["stepName"],
                "flowCondition": SELECTOR_CONDITIONS[route_number],
                "transitionPrompt": selector.get("transitionPrompt", ""),
                "isDefault": route_number == 1,
            }
        )
        for offset in range(4):
            source_index = target_index + offset
            target = source_index + 1 if offset < 3 else summary_index
            flows.append(
                {
                    "sourceIndex": source_index,
                    "targetIndex": target,
                    "sourceName": steps[source_index]["stepName"],
                    "targetName": steps[target]["stepName"],
                    "flowCondition": steps[source_index]["flowCondition"],
                    "transitionPrompt": steps[source_index].get("transitionPrompt", ""),
                    "isDefault": True,
                }
            )
    flows.append(
        {
            "sourceIndex": summary_index,
            "targetIndex": None,
            "sourceName": summary["stepName"],
            "targetName": "END",
            "flowCondition": "训练完成",
            "transitionPrompt": summary.get("transitionPrompt", ""),
            "isDefault": True,
        }
    )

    conditions = [flow["flowCondition"] for flow in flows if flow["flowCondition"]]
    if len(conditions) != len(set(conditions)):
        raise ValueError("检测到重复的非空 flowCondition")
    if len(steps) != 18 or len(flows) != 22:
        raise ValueError(f"拓扑数量错误: steps={len(steps)}, flows={len(flows)}")
    return PackagePlan(steps=steps, flows=flows, positions=_build_positions())


def load_route_package(
    entry_path: Path = DEFAULT_ENTRY_PATH,
    route_paths: dict[int, Path] | None = None,
) -> PackagePlan:
    selected_paths = route_paths or DEFAULT_ROUTE_PATHS
    missing = [str(path) for path in [entry_path, *selected_paths.values()] if not path.exists()]
    if missing:
        raise FileNotFoundError("缺少剧本文件: " + ", ".join(missing))
    public_steps = base.parse_markdown(entry_path)
    route_steps = {
        route_number: base.parse_markdown(path)
        for route_number, path in selected_paths.items()
    }
    return assemble_route_package(public_steps, route_steps)
```

- [ ] **Step 4: 运行装配核心测试**

Run:

```bash
python -m pytest tests/test_import_mianzhou_museum_routes.py -v
```

Expected: `4 passed`。

- [ ] **Step 5: 提交装配核心**

```bash
git add skill_training_build/import_mianzhou_museum_routes.py tests/test_import_mianzhou_museum_routes.py
git commit -m "feat: add Mianzhou museum route package core"
```

---

### Task 2: 重写公共入口与路线 1，确定提示词合同

**Files:**

- Modify: `skills_training_course/绵阳职业技术学院-峥嵘绵阳/训练剧本配置.md:1-1012`
- Create: `skills_training_course/绵阳职业技术学院-峥嵘绵阳/训练剧本路线1-默认-1-2-3-4.md`

**Interfaces:**

- Consumes: `training-prompt-expert` 模拟人物型、总结型模板；原文件六个阶段的知识库和素材字段。
- Produces: 两阶段公共文件；四阶段路线 1 文件；后续路线复用的场馆提示词合同。

- [ ] **Step 1: 导出并核对当前数字人资源**

先确认 `.env` 中 `AUTHORIZATION`、`COOKIE`、`COURSE_ID` 均有非空值，再运行：

```bash
python .agents/skills/training-prompt-expert/scripts/export_digital_human_catalog.py --output /tmp/polymas_digital_human_catalog.md
```

Expected: `/tmp/polymas_digital_human_catalog.md` 存在并列出当前数字人、声音和形象。

读取资源清单后：

- 若现有“小绵”数字人可复用，五个 Markdown 全部使用同一 `customNid`、`voiceNid`、`avatarNid`。
- 若没有“小绵”但 `TTS2cuBiZ` 与 `QKR4HaqByQ` 仍在清单中，保持 `数字人` 为空、`数字人名称` 为“小绵”，声音和形象使用清单中的真实 ID。
- 若资源导出失败或 ID 不再存在，五个 Markdown 的 `数字人`、`声音`、`形象` 保守留空，并在配置说明中记录“资源清单不可用，未杜撰 ID”。

- [ ] **Step 2: 将 `训练剧本配置.md` 改成公共入口文件**

使用 `apply_patch` 保留基础配置，最终只包含连续编号的两个阶段：

1. `阶段1: 场馆集群总介绍`
2. `阶段2: 游览结束（总结送别）`

场馆选择阶段必须具备以下行为：

- 开场白完整列出四个场馆和编号 1-4。
- 接受数字、完整馆名以及能唯一对应场馆的主题词。
- 未明确选择、回答“随便”“默认”“你安排”时只输出：

  `进入路线1第1站王右木真理拓源研习舱阶段`

- 选择 2、3、4 时分别只输出：

  `进入路线2第1站三线建设耀绵州研习舱阶段`

  `进入路线3第1站两弹报国铸重器研习舱阶段`

  `进入路线4第1站震后重生承大爱研习舱阶段`

- 四个跳转分支不得输出标点、说明或多个关键词。
- `flowCondition` 字段写默认路线 1 的关键词。
- 关系表列出 START、4 条选路边、4 条路线汇总边、总结到 END 的完整拓扑。

总结阶段复用原阶段 6 的四馆回顾内容，但统一满足：

- 总结未输出时强制先输出总结。
- 总结已输出且参观者明确结束时只输出 `训练完成`。
- 不评价参观者“做得好/遗漏”，只回顾四馆主题和精神内核。

- [ ] **Step 3: 创建路线 1 的四个阶段**

路线 1 阶段顺序和跳转必须为：

| 阶段 | 阶段名称 | `flowCondition` |
|---|---|---|
| 1 | `路线1-第1站-王右木真理拓源研习舱` | `进入路线1第2站三线建设耀绵州研习舱阶段` |
| 2 | `路线1-第2站-三线建设耀绵州研习舱` | `进入路线1第3站两弹报国铸重器研习舱阶段` |
| 3 | `路线1-第3站-两弹报国铸重器研习舱` | `进入路线1第4站震后重生承大爱研习舱阶段` |
| 4 | `路线1-第4站-震后重生承大爱研习舱` | `进入路线1完成后的游览总结阶段` |

四个场馆提示词统一采用以下六类意图：

1. 有效具体问询。
2. 结束本馆、进入下一站。
3. 无效续讲请求或模糊提问。
4. 超纲深挖或错误前提。
5. 背景信息询问。
6. 完全无关。

正常回答分支必须包含：

```text
先只回答参观者本轮提出的具体问题，不主动补充未问内容。回答结束后，使用“想了解”“想聊”“想问”“想知道”中的一个词，自然邀请参观者根据刚才获得的信息自主提出一个新的具体问题；不得给出下一问题的对象、谓语、答案方向或可直接照抄的问题句。
```

无效续讲请求分支必须包含：

```text
若参观者在本馆第一次只说“是”“想”“可以”“继续”“还有吗”等内容，回复：“请把你想了解的对象和角度说完整，我再为你讲解。”

若本馆此前已经出现过一次上述无效输入，本轮仍未形成具体问题，只允许提示：“你可以从人物、事件、原因、过程、影响或精神价值中选择一个角度，再组织成一个具体问题。”不得追加场馆知识点或示范问题。
```

每个场馆 Opening Line 的结尾统一采用：

```text
请从刚才的介绍中选择一条你最感兴趣的线索，并用一个完整问题开始探索。
```

每个场馆必须删除：

- `步骤0` 中的“下一场馆判断”和首选场馆查表。
- “想知道他后来……吗”“想了解……吗”“想聊聊……吗”等直接给出下一问题的句子。
- 根据历史对话推断下一站的多出口规则。

每个场馆结束分支只保留本路线固定的唯一下一站关键词。

- [ ] **Step 4: 对公共文件和路线 1 做 strict 验证**

Run:

```bash
python .agents/skills/training-prompt-expert/scripts/validate_markdown.py 'skills_training_course/绵阳职业技术学院-峥嵘绵阳/训练剧本配置.md' --strict
python .agents/skills/training-prompt-expert/scripts/validate_markdown.py 'skills_training_course/绵阳职业技术学院-峥嵘绵阳/训练剧本路线1-默认-1-2-3-4.md' --strict
```

Expected: 两次均输出 `✅ 所有检查通过`，无 `❌`。

- [ ] **Step 5: 检查入口和路线 1 的提示词语义**

Run:

```bash
rg -n '下一场馆判断|想知道[^。！？]*[吗？]|想了解[^。！？]*[吗？]|想聊聊[^。！？]*[吗？]|要不要[^。！？]*了解' \
  'skills_training_course/绵阳职业技术学院-峥嵘绵阳/训练剧本配置.md' \
  'skills_training_course/绵阳职业技术学院-峥嵘绵阳/训练剧本路线1-默认-1-2-3-4.md'
```

Expected: 无输出。

课程目录被忽略，本任务不得执行 `git add -f`。

---

### Task 3: 创建路线 2、3、4 并做跨路线一致性检查

**Files:**

- Create: `skills_training_course/绵阳职业技术学院-峥嵘绵阳/训练剧本路线2-2-1-3-4.md`
- Create: `skills_training_course/绵阳职业技术学院-峥嵘绵阳/训练剧本路线3-3-1-2-4.md`
- Create: `skills_training_course/绵阳职业技术学院-峥嵘绵阳/训练剧本路线4-4-1-2-3.md`
- Modify: `tests/test_import_mianzhou_museum_routes.py`

**Interfaces:**

- Consumes: Task 2 的路线 1 场馆提示词合同。
- Produces: 四条完整路线；`validate_repeated_hall_content(plan) -> None`。

- [ ] **Step 1: 创建路线 2**

使用 `apply_patch` 写完整 Markdown，阶段和跳转为：

| 阶段 | 阶段名称 | `flowCondition` |
|---|---|---|
| 1 | `路线2-第1站-三线建设耀绵州研习舱` | `进入路线2第2站王右木真理拓源研习舱阶段` |
| 2 | `路线2-第2站-王右木真理拓源研习舱` | `进入路线2第3站两弹报国铸重器研习舱阶段` |
| 3 | `路线2-第3站-两弹报国铸重器研习舱` | `进入路线2第4站震后重生承大爱研习舱阶段` |
| 4 | `路线2-第4站-震后重生承大爱研习舱` | `进入路线2完成后的游览总结阶段` |

- [ ] **Step 2: 创建路线 3**

使用 `apply_patch` 写完整 Markdown，阶段和跳转为：

| 阶段 | 阶段名称 | `flowCondition` |
|---|---|---|
| 1 | `路线3-第1站-两弹报国铸重器研习舱` | `进入路线3第2站王右木真理拓源研习舱阶段` |
| 2 | `路线3-第2站-王右木真理拓源研习舱` | `进入路线3第3站三线建设耀绵州研习舱阶段` |
| 3 | `路线3-第3站-三线建设耀绵州研习舱` | `进入路线3第4站震后重生承大爱研习舱阶段` |
| 4 | `路线3-第4站-震后重生承大爱研习舱` | `进入路线3完成后的游览总结阶段` |

- [ ] **Step 3: 创建路线 4**

使用 `apply_patch` 写完整 Markdown，阶段和跳转为：

| 阶段 | 阶段名称 | `flowCondition` |
|---|---|---|
| 1 | `路线4-第1站-震后重生承大爱研习舱` | `进入路线4第2站王右木真理拓源研习舱阶段` |
| 2 | `路线4-第2站-王右木真理拓源研习舱` | `进入路线4第3站三线建设耀绵州研习舱阶段` |
| 3 | `路线4-第3站-三线建设耀绵州研习舱` | `进入路线4第4站两弹报国铸重器研习舱阶段` |
| 4 | `路线4-第4站-两弹报国铸重器研习舱` | `进入路线4完成后的游览总结阶段` |

每个同名场馆从路线 1 复制完整角色、知识库、Opening Line、自主提问规则、意图类型、分支和 Response Constraints；只替换路线号、站序、阶段名称和唯一下一站关键词。

- [ ] **Step 4: 写出跨路线知识库一致性失败测试**

在 `tests/test_import_mianzhou_museum_routes.py` 追加：

```python
def test_repeated_hall_knowledge_bases_must_match() -> None:
    route_steps = {number: make_route_steps(number) for number in range(1, 5)}
    for steps in route_steps.values():
        for step in steps:
            hall_name = step["stepName"].split("-", 3)[-1]
            step["llmPrompt"] = (
                "# Role\n"
                "## [标准知识库]（你的回答必须源于此）\n"
                f"- 场馆：{hall_name}\n"
                "# Opening Line\n"
                "【自主提问规则】"
            )
    plan = importer.assemble_route_package(make_public_steps(), route_steps)
    importer.validate_repeated_hall_content(plan)

    route_three_hall = next(
        step
        for step in plan.steps
        if step["stepName"] == "路线3-第2站-王右木真理拓源研习舱"
    )
    route_three_hall["llmPrompt"] = route_three_hall["llmPrompt"].replace("场馆：", "错误改写：")

    try:
        importer.validate_repeated_hall_content(plan)
    except ValueError as exc:
        assert "同一场馆的标准知识库不一致" in str(exc)
    else:
        raise AssertionError("跨路线知识库差异必须被拒绝")
```

- [ ] **Step 5: 实现跨路线知识库一致性检查**

在 `skill_training_build/import_mianzhou_museum_routes.py` 追加：

```python
def _hall_name_from_step_name(step_name: str) -> str | None:
    if not step_name.startswith("路线"):
        return None
    return step_name.split("-", 3)[-1]


def _extract_knowledge_base(prompt: str) -> str:
    marker = "## [标准知识库]"
    start = prompt.find(marker)
    end = prompt.find("# Opening Line", start + len(marker))
    if start < 0 or end < 0:
        raise ValueError("场馆提示词缺少标准知识库或 Opening Line")
    return prompt[start:end].strip()


def validate_repeated_hall_content(plan: PackagePlan) -> None:
    knowledge_by_hall: dict[str, str] = {}
    for step in plan.steps:
        hall_name = _hall_name_from_step_name(step.get("stepName", ""))
        if hall_name is None:
            continue
        prompt = step.get("llmPrompt", "")
        if "【自主提问规则】" not in prompt:
            raise ValueError(f"{step['stepName']} 缺少【自主提问规则】")
        knowledge = _extract_knowledge_base(prompt)
        previous = knowledge_by_hall.setdefault(hall_name, knowledge)
        if previous != knowledge:
            raise ValueError(f"同一场馆的标准知识库不一致: {hall_name}")
```

在 `load_route_package()` 返回前调用：

```python
plan = assemble_route_package(public_steps, route_steps)
validate_repeated_hall_content(plan)
return plan
```

- [ ] **Step 6: 运行单元测试**

Run:

```bash
python -m pytest tests/test_import_mianzhou_museum_routes.py -v
```

Expected: `5 passed`。

- [ ] **Step 7: 对四条路线执行 strict 验证**

Run:

```bash
for file in \
  'skills_training_course/绵阳职业技术学院-峥嵘绵阳/训练剧本路线1-默认-1-2-3-4.md' \
  'skills_training_course/绵阳职业技术学院-峥嵘绵阳/训练剧本路线2-2-1-3-4.md' \
  'skills_training_course/绵阳职业技术学院-峥嵘绵阳/训练剧本路线3-3-1-2-4.md' \
  'skills_training_course/绵阳职业技术学院-峥嵘绵阳/训练剧本路线4-4-1-2-3.md'
do
  python .agents/skills/training-prompt-expert/scripts/validate_markdown.py "$file" --strict
done
```

Expected: 四个文件均输出 `✅ 所有检查通过`。

- [ ] **Step 8: 提交一致性检查代码**

```bash
git add skill_training_build/import_mianzhou_museum_routes.py tests/test_import_mianzhou_museum_routes.py
git commit -m "test: validate Mianzhou route content consistency"
```

课程 Markdown 不执行 `git add -f`。

---

### Task 4: 增加安全 CLI、dry-run、平台写入和只读回查

**Files:**

- Modify: `skill_training_build/import_mianzhou_museum_routes.py`
- Modify: `tests/test_import_mianzhou_museum_routes.py`

**Interfaces:**

- Consumes: `PackagePlan`、`base.query_script_steps()`、`base.query_script_step_flows()`、`base.create_script_step()`、`base.create_script_flow()`、`base.delete_existing_steps_and_flows()`
- Produces: `print_dry_run(plan)`、`verify_platform_topology(task_id, plan)`、`apply_package(task_id, plan, delete_existing, assume_yes)`、`main(argv=None) -> int`

- [ ] **Step 1: 写出默认 dry-run 不调用平台 API 的失败测试**

在 `tests/test_import_mianzhou_museum_routes.py` 追加：

```python
def test_main_defaults_to_dry_run_without_platform_calls(monkeypatch, capsys) -> None:
    route_steps = {number: make_route_steps(number) for number in range(1, 5)}
    plan = importer.assemble_route_package(make_public_steps(), route_steps)
    monkeypatch.setattr(importer, "load_route_package", lambda *args, **kwargs: plan)

    def forbidden(*args, **kwargs):
        raise AssertionError("默认 dry-run 不得调用平台 API")

    monkeypatch.setattr(importer.base, "query_script_steps", forbidden)
    monkeypatch.setattr(importer.base, "query_script_step_flows", forbidden)
    monkeypatch.setattr(importer.base, "create_script_step", forbidden)
    monkeypatch.setattr(importer.base, "create_script_flow", forbidden)

    assert importer.main([]) == 0
    output = capsys.readouterr().out
    assert "业务节点: 18" in output
    assert "真实连线: 22" in output
    assert "未调用平台 API" in output
```

- [ ] **Step 2: 实现 CLI 和 dry-run**

在导入器中增加 `argparse`、`json`、`os`、`datetime` 导入，并实现：

```python
def print_dry_run(plan: PackagePlan) -> None:
    print("🧪 红色绵州四路线剧本 dry-run")
    print(f"业务节点: {len(plan.steps)}")
    print(f"真实连线: {len(plan.flows)}")
    for index, step in enumerate(plan.steps, start=1):
        print(f"  节点[{index:02d}] {step['stepName']}")
    for index, flow in enumerate(plan.flows, start=1):
        print(
            f"  连线[{index:02d}] {flow['sourceName']} -> {flow['targetName']} | "
            f"condition={flow['flowCondition']!r} | isDefault={int(flow['isDefault'])}"
        )
    print("🧪 Dry-run 完成，未调用平台 API。")


def parse_cli_args(argv=None):
    parser = argparse.ArgumentParser(description="装配红色绵州四条独立场馆路线")
    parser.add_argument("--entry", type=Path, default=DEFAULT_ENTRY_PATH)
    parser.add_argument("--task-id")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--delete-existing", action="store_true")
    parser.add_argument("--yes", action="store_true")
    parser.add_argument("--verify-only", action="store_true")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_cli_args(argv)
    try:
        plan = load_route_package(args.entry)
        if not args.apply and not args.verify_only:
            print_dry_run(plan)
            return 0
        base.load_env_config()
        task_id = args.task_id or os.getenv("TASK_ID", "").strip()
        if not task_id:
            raise ValueError("缺少 TASK_ID，请通过 --task-id 或 .env 提供")
        if args.verify_only:
            result = verify_platform_topology(task_id, plan)
            return 0 if not result["errors"] else 1
        if not args.delete_existing or not args.yes:
            raise ValueError("平台重建必须同时使用 --apply --delete-existing --yes")
        apply_package(task_id, plan, delete_existing=True, assume_yes=True)
        result = verify_platform_topology(task_id, plan)
        return 0 if not result["errors"] else 1
    except Exception as exc:
        print(f"❌ {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 3: 实现平台写入保护**

在导入器中加入以下实现：

```python
def _ensure_start_end(task_id: str, step_list: list[dict[str, Any]]) -> tuple[str, str]:
    start_id, end_id = base.extract_start_end_ids(step_list)
    if start_id and end_id:
        return start_id, end_id
    course_id = os.getenv("COURSE_ID", "").strip()
    if not course_id:
        raise ValueError("平台缺少 START/END，且 .env 未提供 COURSE_ID")
    return base.create_start_end_nodes(task_id, course_id)


def _backup_platform_state(
    task_id: str,
    steps: list[dict[str, Any]],
    flows: list[dict[str, Any]],
) -> Path:
    backup_dir = ROOT / "tmp"
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = backup_dir / f"mianzhou_route_import_backup_{timestamp}.json"
    path.write_text(
        json.dumps(
            {
                "trainTaskId": task_id,
                "createdAt": datetime.now().isoformat(timespec="seconds"),
                "steps": steps,
                "flows": flows,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"🧾 已备份现有平台状态: {path}")
    return path


def _prepare_step_resources(
    plan: PackagePlan,
    entry_path: Path,
    course_id: str,
) -> None:
    base.resolve_steps_digital_humans(plan.steps, entry_path, course_id=course_id)
    for step in plan.steps:
        background = step.get("backgroundImage", "")
        if not background:
            continue
        if base.is_remote_url(background):
            step["scriptStepCover"] = base.build_script_step_cover_from_url(background)
            continue
        image_path = Path(background)
        if not image_path.is_absolute():
            image_path = (entry_path.parent / image_path).resolve()
        cover = base.upload_cover_image(image_path)
        if not cover:
            raise RuntimeError(f"背景图上传失败: {image_path}")
        step["scriptStepCover"] = cover


def apply_package(
    task_id: str,
    plan: PackagePlan,
    *,
    entry_path: Path = DEFAULT_ENTRY_PATH,
    delete_existing: bool,
    assume_yes: bool,
) -> None:
    step_list = base.query_script_steps(task_id)
    flow_list = base.query_script_step_flows(task_id)
    start_id, end_id = _ensure_start_end(task_id, step_list)
    business_steps = base.get_business_script_steps(step_list)

    if business_steps or flow_list:
        if not delete_existing or not assume_yes:
            raise RuntimeError(
                "目标任务已有业务节点或连线；重建必须显式使用 "
                "--apply --delete-existing --yes"
            )
        _backup_platform_state(task_id, step_list, flow_list)
        if not base.delete_existing_steps_and_flows(task_id, business_steps, flow_list):
            raise RuntimeError("删除现有业务节点或连线失败")
        step_list = base.query_script_steps(task_id)
        start_id, end_id = _ensure_start_end(task_id, step_list)

    course_id = os.getenv("COURSE_ID", "").strip()
    if not course_id:
        raise ValueError("平台写入需要 COURSE_ID")
    _prepare_step_resources(plan, entry_path, course_id)

    created_ids: dict[int, str] = {}
    for index, (step, position) in enumerate(zip(plan.steps, plan.positions)):
        step_id = base.create_script_step(task_id, step, position)
        if not step_id:
            raise RuntimeError(f"创建节点失败: {step['stepName']}")
        created_ids[index] = step_id

    for flow in plan.flows:
        source_id = (
            start_id
            if flow["sourceIndex"] is None
            else created_ids[flow["sourceIndex"]]
        )
        target_id = (
            end_id
            if flow["targetIndex"] is None
            else created_ids[flow["targetIndex"]]
        )
        created = base.create_script_flow(
            task_id,
            source_id,
            target_id,
            flow["flowCondition"],
            flow["transitionPrompt"],
            is_default=flow["isDefault"],
        )
        if not created:
            raise RuntimeError(
                f"创建连线失败: {flow['sourceName']} -> {flow['targetName']}"
            )
```

- [ ] **Step 4: 实现平台只读回查**

在导入器中加入：

```python
def verify_platform_topology(task_id: str, plan: PackagePlan) -> dict[str, Any]:
    step_list = base.query_script_steps(task_id)
    flow_list = base.query_script_step_flows(task_id)
    start_id, end_id = base.extract_start_end_ids(step_list)
    if not start_id or not end_id:
        return {
            "business_step_count": 0,
            "flow_count": len(flow_list),
            "errors": ["平台缺少 START 或 END 节点"],
        }

    business_steps = base.get_business_script_steps(step_list)
    actual_names = [
        item.get("stepDetailDTO", {}).get("stepName", "")
        for item in business_steps
    ]
    expected_names = [step["stepName"] for step in plan.steps]
    errors: list[str] = []
    if len(business_steps) != 18:
        errors.append(f"业务节点数量不匹配: expected=18, actual={len(business_steps)}")
    if set(actual_names) != set(expected_names):
        errors.append(
            "业务节点名称不匹配: "
            f"missing={sorted(set(expected_names) - set(actual_names))}, "
            f"extra={sorted(set(actual_names) - set(expected_names))}"
        )

    name_by_id = {start_id: "START", end_id: "END"}
    for item in business_steps:
        name_by_id[item.get("stepId")] = (
            item.get("stepDetailDTO", {}).get("stepName", "")
        )
    actual_triples = {
        (
            name_by_id.get(flow.get("scriptStepStartId"), "<UNKNOWN>"),
            name_by_id.get(flow.get("scriptStepEndId"), "<UNKNOWN>"),
            flow.get("flowCondition", ""),
        )
        for flow in flow_list
    }
    expected_triples = {
        (flow["sourceName"], flow["targetName"], flow["flowCondition"])
        for flow in plan.flows
    }
    if len(flow_list) != 22:
        errors.append(f"连线数量不匹配: expected=22, actual={len(flow_list)}")
    if actual_triples != expected_triples:
        errors.append(
            "连线集合不匹配: "
            f"missing={sorted(expected_triples - actual_triples)}, "
            f"extra={sorted(actual_triples - expected_triples)}"
        )

    actual_conditions = [
        flow.get("flowCondition", "")
        for flow in flow_list
        if flow.get("flowCondition", "")
    ]
    if len(actual_conditions) != len(set(actual_conditions)):
        errors.append("平台存在重复的非空 flowCondition")

    selector_id = next(
        (
            item.get("stepId")
            for item in business_steps
            if item.get("stepDetailDTO", {}).get("stepName") == "场馆集群总介绍"
        ),
        None,
    )
    selector_defaults = {
        flow.get("flowCondition", ""): bool(flow.get("isDefault"))
        for flow in flow_list
        if flow.get("scriptStepStartId") == selector_id
    }
    expected_defaults = {
        SELECTOR_CONDITIONS[number]: number == 1
        for number in range(1, 5)
    }
    if selector_defaults != expected_defaults:
        errors.append(
            "场馆选择默认边不匹配: "
            f"expected={expected_defaults}, actual={selector_defaults}"
        )

    return {
        "business_step_count": len(business_steps),
        "flow_count": len(flow_list),
        "errors": errors,
    }
```

在 `main()` 的 `apply_package()` 调用中传入 `entry_path=args.entry`。

- [ ] **Step 5: 运行 CLI 安全测试**

Run:

```bash
python -m pytest tests/test_import_mianzhou_museum_routes.py -v
```

Expected: `6 passed`。

- [ ] **Step 6: 运行语法检查**

Run:

```bash
python -m py_compile skill_training_build/import_mianzhou_museum_routes.py
```

Expected: 无输出，退出码 0。

- [ ] **Step 7: 提交 CLI**

```bash
git add skill_training_build/import_mianzhou_museum_routes.py tests/test_import_mianzhou_museum_routes.py
git commit -m "feat: add safe Mianzhou route importer CLI"
```

---

### Task 5: 完整格式、语义和拓扑验收

**Files:**

- Verify: `skills_training_course/绵阳职业技术学院-峥嵘绵阳/训练剧本配置.md`
- Verify: `skills_training_course/绵阳职业技术学院-峥嵘绵阳/训练剧本路线1-默认-1-2-3-4.md`
- Verify: `skills_training_course/绵阳职业技术学院-峥嵘绵阳/训练剧本路线2-2-1-3-4.md`
- Verify: `skills_training_course/绵阳职业技术学院-峥嵘绵阳/训练剧本路线3-3-1-2-4.md`
- Verify: `skills_training_course/绵阳职业技术学院-峥嵘绵阳/训练剧本路线4-4-1-2-3.md`
- Verify: `skill_training_build/import_mianzhou_museum_routes.py`
- Verify: `tests/test_import_mianzhou_museum_routes.py`

**Interfaces:**

- Consumes: 五个 Markdown 和专用导入器。
- Produces: 可验证的本地剧本包；不产生平台变更。

- [ ] **Step 1: 对五个 Markdown 执行 strict validator**

Run:

```bash
for file in \
  'skills_training_course/绵阳职业技术学院-峥嵘绵阳/训练剧本配置.md' \
  'skills_training_course/绵阳职业技术学院-峥嵘绵阳/训练剧本路线1-默认-1-2-3-4.md' \
  'skills_training_course/绵阳职业技术学院-峥嵘绵阳/训练剧本路线2-2-1-3-4.md' \
  'skills_training_course/绵阳职业技术学院-峥嵘绵阳/训练剧本路线3-3-1-2-4.md' \
  'skills_training_course/绵阳职业技术学院-峥嵘绵阳/训练剧本路线4-4-1-2-3.md'
do
  python .agents/skills/training-prompt-expert/scripts/validate_markdown.py "$file" --strict
done
```

Expected: 五个文件全部通过，无 `❌`。

- [ ] **Step 2: 扫描过度直接引导与旧历史路由**

Run:

```bash
rg -n '下一场馆判断|首选场馆|想知道[^。！？]*[吗？]|想了解[^。！？]*[吗？]|想聊聊[^。！？]*[吗？]|要不要[^。！？]*了解' \
  skills_training_course/绵阳职业技术学院-峥嵘绵阳/训练剧本*.md
```

Expected: 无输出。

- [ ] **Step 3: 检查自主提问规则覆盖 16 个场馆节点**

Run:

```bash
rg -c '【自主提问规则】' \
  skills_training_course/绵阳职业技术学院-峥嵘绵阳/训练剧本路线*.md
```

Expected: 四个路线文件分别输出计数 `4`。

- [ ] **Step 4: 运行全套目标测试**

Run:

```bash
python -m pytest \
  tests/test_import_mianzhou_museum_routes.py \
  tests/test_create_task_from_markdown_update_existing.py \
  -v
```

Expected: 全部通过。

- [ ] **Step 5: 运行专用装配 dry-run**

Run:

```bash
python skill_training_build/import_mianzhou_museum_routes.py
```

Expected:

```text
业务节点: 18
真实连线: 22
Dry-run 完成，未调用平台 API。
```

节点预览必须能人工核对出四列路线顺序，场馆选择节点的四条出边中只有路线 1 为默认。

- [ ] **Step 6: 检查跳转关键词一致性**

使用导入器输出的 21 个非空条件逐项回查：

- 场馆选择提示词的四个纯跳转分支与四条选择边一致。
- 16 个路线场馆阶段的 `flowCondition` 与各自结束分支一致。
- 四条路线末站使用四个不同的共享总结关键词。
- 共享总结结束分支与 `训练完成` 一致。

若任何一处不一致，修复 Markdown 后重新执行 Step 1 至 Step 6。

- [ ] **Step 7: 检查未发生平台写入**

本次命令记录中不得出现：

```text
--apply
--delete-existing
--yes
```

最终交付必须明确标注：

- 已完成本地内容和结构验证。
- 已完成 dry-run。
- 未部署、未覆盖平台任务。
- 课程 Markdown 位于 Git 忽略目录，已通过直接回读和验证器确认，不以 `git status` 作为存在性证据。
