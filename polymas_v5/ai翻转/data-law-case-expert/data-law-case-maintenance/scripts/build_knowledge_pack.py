#!/usr/bin/env python3
"""把案例主数据生成一案例一知识块的 JSONL。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from library_core import resolve_active_root  # noqa: E402


STUDENT_VISIBLE_STATUSES = {"已发布"}


def load_library(library_root: Path) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    data_root = resolve_active_root(Path(library_root)) / "data"
    manifest = json.loads((data_root / "manifest.json").read_text(encoding="utf-8"))
    scenes = json.loads((data_root / "scenes.json").read_text(encoding="utf-8"))
    cases = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted((data_root / "cases").glob("DLCL-*.json"))
    ]
    return manifest, {scene["scene_id"]: scene for scene in scenes}, cases


def format_optional(value: str | None) -> str:
    return value.strip() if value and value.strip() else "原材料未提供"


def build_block(case: dict[str, Any], scene: dict[str, Any]) -> dict[str, Any]:
    laws = "\n".join(
        f"- {item['citation_text']}（{item['evidence_status']}）"
        for item in case.get("legal_provisions", [])
    ) or "- 原材料未提供"
    sources = "\n".join(
        f"- {item['title']}；链接：{item.get('url') or '未提供'}"
        for item in case.get("sources", [])
    ) or "- 原材料未提供"
    content = f"""# {case['title']}

案例ID：{case['case_id']}
主场景：{scene['name']}
案例类型：{case['record_type']}
主要法域：{case['jurisdiction']}
证据状态：{case['evidence_status']}

## 基本案情
{format_optional(case.get('basic_facts'))}

## 争议焦点
{format_optional(case.get('dispute_focus'))}

## 涉及法律条文
{laws}

## 裁判或处理结果
{format_optional(case.get('outcome'))}
结果类型：{case['outcome_type']}
结果证据：{case['outcome_evidence_status']}

## 法律问题分析
{format_optional(case.get('legal_analysis'))}
分析来源：{case['analysis_origin']}

## 材料来源
{sources}

边界提示：材料未记载的案号、裁判结果、事实或法律时效状态不得补造；境外案例中的中国法条仅作比较法教学映射。
"""
    return {
        "knowledge_id": f"case:{case['case_id']}:v{case['version']}",
        "title": case["title"],
        "content": content,
        "metadata": {
            "case_id": case["case_id"],
            "case_version": case["version"],
            "scene_id": case["scene_id"],
            "record_type": case["record_type"],
            "evidence_status": case["evidence_status"],
            "publication_status": case["case_status"],
        },
    }


def build_knowledge_pack(library_root: Path, output_path: Path) -> dict[str, Any]:
    manifest, scenes, cases = load_library(Path(library_root))
    blocks = [
        build_block(case, scenes[case["scene_id"]])
        for case in cases
        if case.get("case_status") in STUDENT_VISIBLE_STATUSES
    ]
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        "".join(
            json.dumps(block, ensure_ascii=False, separators=(",", ":")) + "\n"
            for block in blocks
        ),
        encoding="utf-8",
    )
    return {
        "status": "artifact_ready_knowledge_pending",
        "library_version": manifest["library_version"],
        "block_count": len(blocks),
        "output_path": str(output_path),
        "knowledge_sync_status": "not_verified",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("library_root", type=Path)
    parser.add_argument("output_path", type=Path)
    args = parser.parse_args()
    try:
        print(
            json.dumps(
                build_knowledge_pack(args.library_root, args.output_path),
                ensure_ascii=False,
            )
        )
        return 0
    except Exception as exc:  # pragma: no cover - CLI adapter
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        print(repr(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
