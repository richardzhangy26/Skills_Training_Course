#!/usr/bin/env python3
"""从“案例拆分文档”目录导入 77 份独立 Word 案例。"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any
import unicodedata


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from extract_source_docx import (  # noqa: E402
    TITLE_NUMBER_PATTERN,
    classify_record,
    infer_jurisdiction,
    normalize_text,
    read_docx_paragraphs,
)
from library_core import validate_case, write_json  # noqa: E402


CASE_FILE_PATTERN = re.compile(r"^场景(\d{2})_案例(\d{2})_.*\.docx$")
INDEX_SCENE_PATTERN = re.compile(r"^场景(\d+)[:：](.+)$")
INDEX_CASE_PATTERN = re.compile(r"^案例(\d+)[:：](.+)$")
DETAIL_LABELS = {
    "案例事实": "case_facts",
    "案例事实：": "case_facts",
    "具体案情": "case_details",
    "争议焦点": "dispute_focus",
    "涉及法律条文": "legal_provisions",
    "法院判决/处理结果": "outcome",
    "法律问题分析": "legal_analysis",
}
TOP_LEVEL_SECTIONS = (
    "一、详细案情（原始材料）",
    "二、具体案情提炼",
    "三、涉案法条/规范",
    "四、案例分析与合规启示",
)


def canonical_scene_name(value: str) -> str:
    value = normalize_text(value)
    value = value.replace("跨境HR数据", "跨境 HR 数据")
    value = value.replace("AI时代", "AI 时代")
    value = value.replace("AIGC竞争", "AIGC 竞争")
    return value


def comparable_title(value: str) -> str:
    value = unicodedata.normalize("NFKC", value)
    value = TITLE_NUMBER_PATTERN.sub("", value)
    return re.sub(r"[^0-9a-z\u3400-\u9fff]+", "", value.casefold())


def parse_index(index_path: Path) -> tuple[dict[int, str], dict[tuple[int, int], str]]:
    paragraphs = read_docx_paragraphs(index_path)
    scenes: dict[int, str] = {}
    cases: dict[tuple[int, int], str] = {}
    active_scene: int | None = None
    for paragraph in paragraphs:
        scene_match = INDEX_SCENE_PATTERN.match(paragraph)
        if scene_match:
            active_scene = int(scene_match.group(1))
            scenes[active_scene] = canonical_scene_name(scene_match.group(2))
            continue
        case_match = INDEX_CASE_PATTERN.match(paragraph)
        if case_match and active_scene is not None:
            case_number = int(case_match.group(1))
            cases[(active_scene, case_number)] = TITLE_NUMBER_PATTERN.sub(
                "", case_match.group(2)
            ).strip()
    if len(scenes) != 10 or len(cases) != 77:
        raise ValueError(
            f"invalid_split_index:scenes={len(scenes)},cases={len(cases)}"
        )
    return scenes, cases


def section_slice(paragraphs: list[str], heading: str, next_heading: str | None) -> list[str]:
    try:
        start = paragraphs.index(heading) + 1
    except ValueError as exc:
        raise ValueError(f"missing_section:{heading}") from exc
    if next_heading is None:
        end = len(paragraphs)
    else:
        try:
            end = paragraphs.index(next_heading, start)
        except ValueError as exc:
            raise ValueError(f"missing_section:{next_heading}") from exc
    return paragraphs[start:end]


def strip_footer(paragraphs: list[str]) -> list[str]:
    return [
        paragraph
        for paragraph in paragraphs
        if not re.match(r"^场景\d+\s*·\s*案例\d+\s*·", paragraph)
    ]


def parse_detail_sections(paragraphs: list[str]) -> dict[str, list[str]]:
    sections = {value: [] for value in set(DETAIL_LABELS.values())}
    sections["unstructured"] = []
    active = "unstructured"
    for paragraph in paragraphs:
        if paragraph in DETAIL_LABELS:
            active = DETAIL_LABELS[paragraph]
            continue
        sections[active].append(paragraph)
    return sections


def join_paragraphs(values: list[str]) -> str | None:
    result = "\n\n".join(value for value in values if value).strip()
    return result or None


def parse_case_document(
    path: Path,
    scene_number: int,
    case_number: int,
    sequence: int,
    scene_id: str,
    indexed_title: str,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    paragraphs = strip_footer(read_docx_paragraphs(path))
    if len(paragraphs) < 8:
        raise ValueError(f"case_document_too_short:{path.name}")
    title = TITLE_NUMBER_PATTERN.sub("", paragraphs[0]).strip()
    if comparable_title(title) != comparable_title(indexed_title):
        raise ValueError(f"index_title_mismatch:{path.name}")

    detail = section_slice(paragraphs, TOP_LEVEL_SECTIONS[0], TOP_LEVEL_SECTIONS[1])
    summary = section_slice(paragraphs, TOP_LEVEL_SECTIONS[1], TOP_LEVEL_SECTIONS[2])
    summary_laws = section_slice(paragraphs, TOP_LEVEL_SECTIONS[2], TOP_LEVEL_SECTIONS[3])
    summary_analysis = section_slice(paragraphs, TOP_LEVEL_SECTIONS[3], None)
    detail_sections = parse_detail_sections(detail)

    labeled_facts = detail_sections["case_facts"] + detail_sections["case_details"]
    basic_facts = join_paragraphs(labeled_facts or detail_sections["unstructured"] or summary)
    dispute_focus = join_paragraphs(detail_sections["dispute_focus"])
    analysis = join_paragraphs(detail_sections["legal_analysis"] or summary_analysis)
    detailed_laws = join_paragraphs(detail_sections["legal_provisions"])
    summary_law_text = join_paragraphs(summary_laws)
    provision_texts = [
        value for value in (detailed_laws, summary_law_text) if value
    ]
    provision_texts = list(dict.fromkeys(provision_texts))

    outcome_text = join_paragraphs(detail_sections["outcome"])
    review_item: dict[str, Any] | None = None
    if outcome_text and re.search(
        r"若.{0,120}(?:可能|将)|可能面临|还可能涉及|可能从|可能被要求",
        outcome_text,
    ):
        review_item = {
            "case_id": f"DLCL-{sequence:04d}",
            "title": title,
            "reason": "speculative_outcome",
            "candidate_outcome": outcome_text,
            "source_file": path.name,
            "status": "awaiting_teacher_confirmation",
        }
        outcome_text = None

    combined_laws = " ".join(provision_texts)
    combined_analysis = analysis or ""
    record = {
        "case_id": f"DLCL-{sequence:04d}",
        "title": title,
        "scene_id": scene_id,
        "record_type": classify_record(title, basic_facts or "", combined_analysis),
        "jurisdiction": infer_jurisdiction(title, basic_facts or "", combined_laws),
        "case_status": "待补证",
        "basic_facts": basic_facts,
        "dispute_focus": dispute_focus,
        "legal_provisions": [
            {
                "citation_text": value,
                "source_url": None,
                "evidence_status": "材料已核对",
            }
            for value in provision_texts
        ],
        "outcome_type": (
            "settlement"
            if outcome_text and "调解" in outcome_text
            else "judgment"
            if outcome_text
            else "unknown"
        ),
        "outcome": outcome_text,
        "outcome_evidence_status": "source_material" if outcome_text else "missing",
        "legal_analysis": analysis,
        "analysis_origin": "source_material",
        "sources": [
            {
                "title": path.name,
                "url": None,
                "published_at": None,
                "retrieved_at": None,
                "source_tier": "source_material",
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        ],
        "evidence_status": "待补证",
        "classification_review_required": True,
        "version": 1,
    }
    errors = validate_case(record)
    if errors:
        raise ValueError(f"{record['case_id']} contract errors: {errors}")
    return record, review_item


def import_split_documents(source_root: Path, output_root: Path) -> dict[str, Any]:
    source_root = Path(source_root)
    output_root = Path(output_root)
    index_path = source_root / "00_案例索引.docx"
    if not index_path.is_file():
        raise ValueError("split_index_missing")
    scene_names, indexed_cases = parse_index(index_path)

    case_files: list[tuple[int, int, Path]] = []
    for path in source_root.glob("*.docx"):
        match = CASE_FILE_PATTERN.match(path.name)
        if match:
            case_files.append((int(match.group(1)), int(match.group(2)), path))
    case_files.sort(key=lambda item: (item[0], item[1], item[2].name))
    if len(case_files) != 77:
        raise ValueError(f"expected_77_case_documents:actual={len(case_files)}")
    keys = [(scene, case) for scene, case, _ in case_files]
    if len(set(keys)) != 77 or set(keys) != set(indexed_cases):
        raise ValueError("split_document_index_mismatch")

    scenes: list[dict[str, Any]] = []
    scene_counts: list[int] = []
    for scene_number in range(1, 11):
        count = sum(scene == scene_number for scene, _, _ in case_files)
        scene_counts.append(count)
        scenes.append(
            {
                "scene_id": f"scene-{scene_number:02d}",
                "order": scene_number,
                "name": scene_names[scene_number],
                "slug": f"scene-{scene_number:02d}",
                "description": None,
                "case_count": count,
            }
        )

    cases: list[dict[str, Any]] = []
    review_queue: list[dict[str, Any]] = []
    digest = hashlib.sha256()
    digest.update(index_path.read_bytes())
    for sequence, (scene_number, case_number, path) in enumerate(case_files, start=1):
        record, review_item = parse_case_document(
            path,
            scene_number,
            case_number,
            sequence,
            f"scene-{scene_number:02d}",
            indexed_cases[(scene_number, case_number)],
        )
        cases.append(record)
        if review_item:
            review_queue.append(review_item)
        digest.update(path.name.encode("utf-8"))
        digest.update(path.read_bytes())

    data_root = output_root / "data"
    cases_root = data_root / "cases"
    cases_root.mkdir(parents=True, exist_ok=True)
    for stale in cases_root.glob("DLCL-*.json"):
        stale.unlink()
    for case in cases:
        write_json(cases_root / f"{case['case_id']}.json", case)
    write_json(data_root / "scenes.json", scenes)
    write_json(data_root / "review-queue.json", review_queue)
    write_json(
        data_root / "manifest.json",
        {
            "library_name": "数据法学案例库",
            "library_version": 1,
            "source_type": "split_docx_directory",
            "source_directory": source_root.name,
            "source_index_file": index_path.name,
            "source_document_count": len(case_files),
            "source_sha256": digest.hexdigest(),
            "scene_count": len(scenes),
            "case_count": len(cases),
            "visible_case_count": len(cases),
            "review_required_count": len(review_queue),
            "evidence_status": "待补证",
            "knowledge_sync_status": "not_started",
        },
    )
    return {
        "status": "imported_with_review_queue" if review_queue else "imported",
        "scene_count": len(scenes),
        "case_count": len(cases),
        "source_document_count": len(case_files),
        "scene_case_counts": scene_counts,
        "review_required_count": len(review_queue),
        "output_root": str(output_root),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_root", type=Path)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    try:
        print(
            json.dumps(
                import_split_documents(args.source_root, args.output_root),
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
