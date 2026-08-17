#!/usr/bin/env python3
"""一次性导入南京理工有机实验分支剧本。

现有 create_task_from_markdown.py 会按阶段顺序线性连线。本脚本专门读取
《阶段跳转关系》里的真实边表，避免把多出口 flowCondition 合并到一条线。
"""

from __future__ import annotations

import argparse
import json
import os
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from . import create_task_from_markdown as base
except ImportError:  # 允许直接 python skill_training_build/import_njtech_branching_task.py
    import create_task_from_markdown as base


DEFAULT_MARKDOWN_PATH = (
    Path(__file__).resolve().parents[1]
    / "skills_training_course"
    / "南京理工-有机化学"
    / "场景一-基础无机操作类能力训练"
    / "训练剧本配置.md"
)

RELATION_LINE_RE = re.compile(
    r"^\s*-\s+\*\*阶段(?P<source_num>\d+)\s+"
    r"(?P<source_name>.*?)\s*→\s*"
    r"(?:(?:阶段(?P<target_num>\d+)\s+(?P<target_name>.*?))|(?P<end>结束))"
    r"\*\*.*?`(?P<condition>[^`]+)`"
)


def step_display_name(step: dict[str, Any]) -> str:
    return step.get("stepName", "未命名阶段")


def build_step_indexes(steps: list[dict[str, Any]]) -> dict[str, int]:
    indexes: dict[str, int] = {}
    for idx, step in enumerate(steps):
        name = step_display_name(step)
        if name in indexes:
            raise ValueError(f"阶段名称重复，无法建立分支拓扑: {name}")
        indexes[name] = idx
    return indexes


def iter_relation_lines(markdown_path: Path):
    in_relations = False
    for raw_line in markdown_path.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        if stripped.startswith("## 阶段跳转关系"):
            in_relations = True
            continue
        if in_relations and stripped.startswith("## "):
            break
        if in_relations and stripped.startswith("- **阶段"):
            yield stripped


def parse_relation_edges(markdown_path: str | Path, steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Parse explicit stage relation edges from the Markdown relation table."""
    path = Path(markdown_path)
    stage_indexes = build_step_indexes(steps)
    edges: list[dict[str, Any]] = []

    for line in iter_relation_lines(path):
        match = RELATION_LINE_RE.match(line)
        if not match:
            raise ValueError(f"无法解析阶段跳转关系行: {line}")

        source_num = int(match.group("source_num"))
        source_name = match.group("source_name").strip()
        source_idx = source_num - 1
        if source_idx < 0 or source_idx >= len(steps):
            raise ValueError(f"源阶段编号越界: 阶段{source_num} {source_name}")
        actual_source_name = step_display_name(steps[source_idx])
        if actual_source_name != source_name:
            raise ValueError(
                f"源阶段编号与名称不匹配: 阶段{source_num} 应为「{actual_source_name}」，关系表为「{source_name}」"
            )

        if match.group("end"):
            target_idx = None
            target_name = "END"
        else:
            target_num = int(match.group("target_num"))
            parsed_target_name = match.group("target_name").strip()
            target_idx = target_num - 1
            if target_idx < 0 or target_idx >= len(steps):
                raise ValueError(f"目标阶段编号越界: 阶段{target_num} {parsed_target_name}")
            actual_target_name = step_display_name(steps[target_idx])
            if actual_target_name != parsed_target_name:
                raise ValueError(
                    f"目标阶段编号与名称不匹配: 阶段{target_num} 应为「{actual_target_name}」，关系表为「{parsed_target_name}」"
                )
            if stage_indexes.get(parsed_target_name) != target_idx:
                raise ValueError(f"目标阶段名称无法唯一解析: {parsed_target_name}")
            target_name = parsed_target_name

        condition = match.group("condition").strip()
        if "/" in condition:
            raise ValueError(f"阶段关系边不能使用合并 flowCondition: {condition}")

        edges.append(
            {
                "sourceIndex": source_idx,
                "targetIndex": target_idx,
                "sourceName": source_name,
                "targetName": target_name,
                "flowCondition": condition,
                "transitionPrompt": steps[source_idx].get("transitionPrompt", ""),
            }
        )

    if not edges:
        raise ValueError("未在 Markdown 中解析到任何阶段跳转关系。")

    return edges


def build_branch_flow_specs(markdown_path: str | Path, steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build START + explicit relation edges for branching import."""
    if not steps:
        raise ValueError("No steps found in markdown.")

    specs = [
        {
            "sourceIndex": None,
            "targetIndex": 0,
            "sourceName": "START",
            "targetName": step_display_name(steps[0]),
            "flowCondition": "",
            "transitionPrompt": "",
        }
    ]
    specs.extend(parse_relation_edges(markdown_path, steps))

    seen: set[tuple[str, str, str]] = set()
    for spec in specs:
        condition = spec["flowCondition"]
        if "/" in condition:
            raise ValueError(f"检测到未拆分的多出口 flowCondition: {condition}")
        triple = (spec["sourceName"], spec["targetName"], condition)
        if triple in seen:
            raise ValueError(f"重复连线: {triple}")
        seen.add(triple)

    return specs


def print_dry_run(steps: list[dict[str, Any]], flow_specs: list[dict[str, Any]]) -> None:
    print("\n🧪 南京理工分支导入 dry-run：不会调用平台 API。")
    print(f"📋 将创建业务节点: {len(steps)}")
    print(f"🔗 将创建真实分支连线: {len(flow_specs)}")

    print("\n节点预览:")
    for idx, step in enumerate(steps, start=1):
        print(
            f"  [{idx}] {step_display_name(step)} | "
            f"训练官={step.get('trainerName', '')} | 轮次={step.get('interactiveRounds', '')}"
        )

    print("\n连线预览:")
    for idx, spec in enumerate(flow_specs, start=1):
        transition_flag = "有 transitionPrompt" if spec["transitionPrompt"] else "无 transitionPrompt"
        print(
            f"  [{idx}] {spec['sourceName']} -> {spec['targetName']} | "
            f"flowCondition={spec['flowCondition']!r} | {transition_flag}"
        )

    if any("/" in spec["flowCondition"] for spec in flow_specs):
        raise ValueError("dry-run 检测到合并 flowCondition，已停止。")

    print("\n🧪 Dry-run complete. 未调用平台 API。")


def prepare_step_covers(steps: list[dict[str, Any]], markdown_path: Path) -> None:
    """Match create_task_from_markdown.py cover behavior for created nodes."""
    global_cover = None
    for idx, step in enumerate(steps):
        background_image = step.get("backgroundImage")
        if background_image:
            if base.is_remote_url(background_image):
                cover = base.build_script_step_cover_from_url(
                    background_image,
                    existing_cover=step.get("scriptStepCover"),
                )
                step["scriptStepCover"] = cover
                if idx == 0:
                    global_cover = cover
            else:
                image_path = Path(background_image)
                if not image_path.is_absolute():
                    image_path = (markdown_path.parent / image_path).resolve()
                cover = base.upload_cover_image(image_path)
                if cover:
                    step["scriptStepCover"] = cover
                    if idx == 0:
                        global_cover = cover
                else:
                    print(f"⚠️ Failed to upload background image for step: {step_display_name(step)}")
        elif idx == 0 and step.get("scriptStepCover"):
            global_cover = step.get("scriptStepCover")
        elif idx > 0 and global_cover and not step.get("scriptStepCover"):
            step["scriptStepCover"] = global_cover


def backup_existing_state(train_task_id: str, steps: list[dict[str, Any]], flows: list[dict[str, Any]]) -> Path:
    backup_dir = Path("tmp")
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"njtech_branch_import_backup_{timestamp}.json"
    backup_payload = {
        "trainTaskId": train_task_id,
        "createdAt": datetime.now().isoformat(timespec="seconds"),
        "steps": steps,
        "flows": flows,
    }
    backup_path.write_text(json.dumps(backup_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"🧾 已备份现有平台状态: {backup_path}")
    return backup_path


def ensure_start_end(train_task_id: str, step_list: list[dict[str, Any]]) -> tuple[str, str]:
    start_node_id, end_node_id = base.extract_start_end_ids(step_list)
    if start_node_id and end_node_id:
        print(f"✅ Found Start Node: {start_node_id}, End Node: {end_node_id}")
        return start_node_id, end_node_id

    course_id = os.getenv("COURSE_ID", "").strip()
    if not course_id:
        raise ValueError("未找到 START/END 且缺少 COURSE_ID，无法自动创建起止节点。")

    print("🔧 未找到 START/END 节点，正在自动创建...")
    start_node_id, end_node_id = base.create_start_end_nodes(train_task_id, course_id)
    print(f"✅ 已创建 START 节点: {start_node_id}")
    print(f"✅ 已创建 END 节点: {end_node_id}")
    return start_node_id, end_node_id


def compute_default_flags(flow_specs: list[dict[str, Any]]) -> list[bool]:
    """当同一个来源节点有多条出边时（正常关卡 vs 危险彩蛋），只把目标是彩蛋节点的
    那条边标记为非默认（isDefault=0），正常主线出边保持默认（isDefault=1）。
    平台的默认连线用于"未匹配到任何条件时兜底走哪条边"，彩蛋分支绝不能是兜底选项。
    来源节点只有一条出边时，该边始终为默认（没有歧义）。"""
    by_source: dict[Any, list[int]] = defaultdict(list)
    for idx, spec in enumerate(flow_specs):
        by_source[spec["sourceIndex"]].append(idx)

    defaults = [True] * len(flow_specs)
    for indices in by_source.values():
        if len(indices) <= 1:
            continue
        for idx in indices:
            if "彩蛋" in flow_specs[idx]["targetName"]:
                defaults[idx] = False
    return defaults


def create_branching_task(
    markdown_path: Path,
    train_task_id: str,
    steps: list[dict[str, Any]],
    flow_specs: list[dict[str, Any]],
    *,
    delete_existing: bool,
    assume_yes: bool,
) -> None:
    print(f"\n⏳ Fetching task info for Task ID: {train_task_id}...")
    step_list = base.query_script_steps(train_task_id)
    start_node_id, end_node_id = ensure_start_end(train_task_id, step_list)
    flow_list = base.query_script_step_flows(train_task_id)

    existing_business_steps = [
        item
        for item in step_list
        if item.get("stepDetailDTO", {}).get("nodeType") not in ("SCRIPT_START", "SCRIPT_END")
    ]

    if existing_business_steps or flow_list:
        names = [
            item.get("stepDetailDTO", {}).get("stepName", "未命名步骤")
            for item in existing_business_steps
        ]
        print(f"⚠️ 检测到现有业务节点 {len(existing_business_steps)} 个、连线 {len(flow_list)} 条")
        if names:
            print("   业务节点: " + ", ".join(names))
        if not delete_existing:
            raise RuntimeError("目标任务已有节点或连线。请显式传入 --delete-existing --yes 后重建。")
        if not assume_yes:
            raise RuntimeError("删除重建需要 --yes 确认。")
        backup_existing_state(train_task_id, step_list, flow_list)
        if not base.delete_existing_steps_and_flows(train_task_id, existing_business_steps, flow_list):
            raise RuntimeError("删除现有节点/连线失败，已停止创建。")

        step_list = base.query_script_steps(train_task_id)
        start_node_id, end_node_id = ensure_start_end(train_task_id, step_list)

    prepare_step_covers(steps, markdown_path)

    print("\n🚀 Creating Nodes...")
    created_steps_map: dict[int, str] = {}
    for idx, step in enumerate(steps):
        pos = build_node_position(idx, step_display_name(step))
        new_id = base.create_script_step(train_task_id, step, pos)
        if not new_id:
            raise RuntimeError(f"创建节点失败: {step_display_name(step)}")
        created_steps_map[idx] = new_id

    print("\n🔗 Creating Branch Flows...")
    default_flags = compute_default_flags(flow_specs)
    for idx, spec in enumerate(flow_specs, start=1):
        source_id = start_node_id if spec["sourceIndex"] is None else created_steps_map[spec["sourceIndex"]]
        target_id = end_node_id if spec["targetIndex"] is None else created_steps_map[spec["targetIndex"]]
        is_default = default_flags[idx - 1]
        print(
            f"   Linking [{idx}] {spec['sourceName']} -> {spec['targetName']} "
            f"with Condition: {spec['flowCondition']!r} | isDefault={is_default}"
        )
        if not base.create_script_flow(
            train_task_id,
            source_id,
            target_id,
            spec["flowCondition"],
            spec["transitionPrompt"],
            is_default=is_default,
        ):
            raise RuntimeError(f"创建连线失败: {spec['sourceName']} -> {spec['targetName']}")


def build_node_position(index: int, step_name: str) -> dict[str, int]:
    egg_names = {
        "倒吸事故彩蛋",
        "高温固体飞溅彩蛋",
        "碱液腐蚀彩蛋",
        "溶液溢出彩蛋",
        "蒸发皿炸裂彩蛋",
    }
    x = 100 + (index * 260)
    y = 620 if step_name in egg_names else 300
    return {"x": x, "y": y}


def verify_platform_topology(
    train_task_id: str,
    steps: list[dict[str, Any]],
    expected_specs: list[dict[str, Any]],
) -> dict[str, Any]:
    step_list = base.query_script_steps(train_task_id)
    flow_list = base.query_script_step_flows(train_task_id)
    start_node_id, end_node_id = base.extract_start_end_ids(step_list)
    if not start_node_id or not end_node_id:
        raise RuntimeError("平台缺少 START 或 END 节点。")

    expected_step_names = [step_display_name(step) for step in steps]
    business_steps = [
        item
        for item in step_list
        if item.get("stepDetailDTO", {}).get("nodeType") == "SCRIPT_NODE"
    ]
    actual_step_names = [
        item.get("stepDetailDTO", {}).get("stepName", "")
        for item in business_steps
    ]

    errors: list[str] = []
    if len(business_steps) != len(expected_step_names):
        errors.append(f"业务节点数量不匹配: expected={len(expected_step_names)}, actual={len(business_steps)}")
    if set(actual_step_names) != set(expected_step_names):
        missing = sorted(set(expected_step_names) - set(actual_step_names))
        extra = sorted(set(actual_step_names) - set(expected_step_names))
        errors.append(f"业务节点名称不匹配: missing={missing}, extra={extra}")

    node_name_by_id = {start_node_id: "START", end_node_id: "END"}
    for item in business_steps:
        node_name_by_id[item.get("stepId")] = item.get("stepDetailDTO", {}).get("stepName", "")

    expected_triples = {
        (spec["sourceName"], spec["targetName"], spec["flowCondition"])
        for spec in expected_specs
    }
    actual_triples = {
        (
            node_name_by_id.get(flow.get("scriptStepStartId"), "<UNKNOWN>"),
            node_name_by_id.get(flow.get("scriptStepEndId"), "<UNKNOWN>"),
            flow.get("flowCondition", ""),
        )
        for flow in flow_list
    }

    if len(flow_list) != len(expected_specs):
        errors.append(f"连线数量不匹配: expected={len(expected_specs)}, actual={len(flow_list)}")
    missing_flows = sorted(expected_triples - actual_triples)
    extra_flows = sorted(actual_triples - expected_triples)
    if missing_flows or extra_flows:
        errors.append(f"连线集合不匹配: missing={missing_flows}, extra={extra_flows}")

    merged_conditions = [
        flow.get("flowCondition", "")
        for flow in flow_list
        if "/" in flow.get("flowCondition", "")
    ]
    if merged_conditions:
        errors.append(f"检测到未拆分的合并 flowCondition: {merged_conditions}")

    old_easter = [
        flow.get("flowCondition", "")
        for flow in flow_list
        if flow.get("flowCondition") == "NEXT_TO_EASTER_EGG"
    ]
    if old_easter:
        errors.append("检测到旧 NEXT_TO_EASTER_EGG 连线")

    wrong_default_egg_flows = [
        f"{node_name_by_id.get(flow.get('scriptStepStartId'), '<UNKNOWN>')} -> "
        f"{node_name_by_id.get(flow.get('scriptStepEndId'), '<UNKNOWN>')}"
        for flow in flow_list
        if "彩蛋" in node_name_by_id.get(flow.get("scriptStepEndId"), "")
        and flow.get("isDefault")
    ]
    if wrong_default_egg_flows:
        errors.append(f"彩蛋连线被错误标记为默认连线(isDefault=1): {wrong_default_egg_flows}")

    result = {
        "business_step_count": len(business_steps),
        "flow_count": len(flow_list),
        "expected_step_count": len(expected_step_names),
        "expected_flow_count": len(expected_specs),
        "errors": errors,
    }
    if errors:
        print("❌ 平台拓扑回查失败:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("✅ 平台拓扑回查通过:")
        print(f"  - 业务节点: {len(business_steps)}/{len(expected_step_names)}")
        print(f"  - 连线: {len(flow_list)}/{len(expected_specs)}")
        print("  - 未发现合并 flowCondition、旧 NEXT_TO_EASTER_EGG，且彩蛋连线均未被标记为默认连线")
    return result


def load_markdown_and_specs(markdown_path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    steps = base.parse_markdown(markdown_path)
    flow_specs = build_branch_flow_specs(markdown_path, steps)
    return steps, flow_specs


def parse_cli_args(argv=None):
    parser = argparse.ArgumentParser(description="导入南京理工有机实验分支剧本")
    parser.add_argument(
        "markdown_path",
        nargs="?",
        default=str(DEFAULT_MARKDOWN_PATH),
        help="训练剧本配置 Markdown 文件路径",
    )
    parser.add_argument("--task-id", help="覆盖 .env 中的 TASK_ID")
    parser.add_argument("--dry-run", action="store_true", help="只解析并打印分支拓扑，不调用 API")
    parser.add_argument("--verify-only", action="store_true", help="只查询平台并核对拓扑")
    parser.add_argument("--delete-existing", action="store_true", help="删除旧业务节点和旧连线后重建")
    parser.add_argument("--yes", action="store_true", help="确认执行删除重建")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_cli_args(argv)
    base.load_env_config()

    markdown_path = Path(args.markdown_path)
    if not markdown_path.exists():
        print(f"❌ Markdown file not found: {markdown_path}")
        return 1

    train_task_id = args.task_id or os.getenv("TASK_ID", "").strip()
    if not train_task_id and not args.dry_run:
        print("❌ 缺少 TASK_ID，请在 .env 中配置或传入 --task-id。")
        return 1

    try:
        print(f"📖 Parsing {markdown_path}...")
        steps, flow_specs = load_markdown_and_specs(markdown_path)
        if args.dry_run:
            print_dry_run(steps, flow_specs)
            return 0
        if args.verify_only:
            result = verify_platform_topology(train_task_id, steps, flow_specs)
            return 0 if not result["errors"] else 1
        create_branching_task(
            markdown_path,
            train_task_id,
            steps,
            flow_specs,
            delete_existing=args.delete_existing,
            assume_yes=args.yes,
        )
        print("\n🔎 Verifying platform topology...")
        result = verify_platform_topology(train_task_id, steps, flow_specs)
        return 0 if not result["errors"] else 1
    except Exception as exc:
        print(f"❌ {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
