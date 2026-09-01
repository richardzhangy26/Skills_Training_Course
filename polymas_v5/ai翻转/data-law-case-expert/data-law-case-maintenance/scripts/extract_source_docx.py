#!/usr/bin/env python3
"""把案例汇总 DOCX 确定性拆分为场景和单案例 JSON。"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any
from xml.etree import ElementTree as ET
from zipfile import ZipFile


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from library_core import validate_case, write_json  # noqa: E402


WORD_NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
TITLE_NUMBER_PATTERN = re.compile(r"^\s*\d+\s*[.．、]\s*")
EXPANDED_CASE_PATTERN = re.compile(r"^案例[一二三四五六七八九十]+\s*[:：]\s*")
EXPANDED_SECTION_NAMES = {
    "案例事实": "case_facts",
    "案例事实：": "case_facts",
    "具体案情": "case_details",
    "争议焦点": "dispute_focus",
    "涉及法律条文": "legal_provisions",
    "法院判决/处理结果": "outcome",
    "法律问题分析": "legal_analysis",
}


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def read_docx_tables(path: Path) -> list[list[list[str]]]:
    """用标准库读取 Word 主文档中的表格文本。"""

    with ZipFile(path) as archive:
        root = ET.fromstring(archive.read("word/document.xml"))

    tables: list[list[list[str]]] = []
    for table in root.findall(".//w:tbl", WORD_NS):
        rows: list[list[str]] = []
        for row in table.findall("./w:tr", WORD_NS):
            cells: list[str] = []
            for cell in row.findall("./w:tc", WORD_NS):
                paragraphs: list[str] = []
                for paragraph in cell.findall("./w:p", WORD_NS):
                    text = "".join(
                        node.text or ""
                        for node in paragraph.findall(".//w:t", WORD_NS)
                    )
                    if normalize_text(text):
                        paragraphs.append(normalize_text(text))
                cells.append(normalize_text(" ".join(paragraphs)))
            rows.append(cells)
        tables.append(rows)
    return tables


def read_docx_paragraphs(path: Path) -> list[str]:
    with ZipFile(path) as archive:
        root = ET.fromstring(archive.read("word/document.xml"))
    paragraphs: list[str] = []
    for paragraph in root.findall(".//w:body/w:p", WORD_NS):
        text = "".join(
            node.text or "" for node in paragraph.findall(".//w:t", WORD_NS)
        )
        clean = normalize_text(text)
        if clean:
            paragraphs.append(clean)
    return paragraphs


def classify_record(title: str, facts: str, analysis: str) -> str:
    material = f"{title} {facts} {analysis}"
    if re.search(r"未决|争议型", material):
        return "pending_dispute"
    if re.search(r"漏洞|泄露|侵入|渗透测试|伪造视频|数据暴露", material):
        return "security_incident"
    if re.search(r"行政处罚|被罚|罚款|监管机构.*处理|FTC.*处罚", material):
        return "administrative_enforcement"
    if re.search(r"和解|监管事件|监管争议", material):
        return "regulatory_event"
    if re.search(r"法院|诉|检例|民事公益诉讼|侮辱案", material):
        return "judicial_case"
    if re.search(r"合规治理|建立本地数据中心|风险场景", material):
        return "compliance_event"
    return "research_material"


def infer_jurisdiction(title: str, facts: str, provisions: str) -> str:
    material = f"{title} {facts} {provisions}"
    if re.search(
        r"欧盟|欧洲|德国|西班牙|罗马尼亚|Romania|GDPR|Bărbulescu|Barbulescu|López|H&M",
        material,
        re.I,
    ):
        return "欧盟或欧洲国家"
    if re.search(r"美国|FTC|COPPA|Equifax|Capital One|GoodRx|PowerPlan", material, re.I):
        return "美国"
    if re.search(r"日本|丰田", material):
        return "日本"
    if re.search(r"韩国", material):
        return "韩国"
    if re.search(r"以色列", material):
        return "以色列"
    if re.search(r"黎巴嫩", material):
        return "黎巴嫩"
    if re.search(r"尼泊尔", material):
        return "尼泊尔或跨境"
    if "对应我国" not in material and re.search(
        r"《个人信息保护法》|《网络安全法》|《数据安全法》|《刑法》|《民法典》|《反垄断法》",
        provisions,
    ):
        return "中国"
    return "待确认"


def canonical_title(value: str) -> str:
    value = EXPANDED_CASE_PATTERN.sub("", value)
    value = re.sub(r"（.*$", "", value)
    value = re.sub(r"\(.*$", "", value)
    return re.sub(r"[\s·・,，。:：/（）()\-—_]", "", value).lower()


def parse_expanded_cases(path: Path) -> list[dict[str, Any]]:
    paragraphs = read_docx_paragraphs(path)
    starts = [
        index
        for index, paragraph in enumerate(paragraphs)
        if EXPANDED_CASE_PATTERN.match(paragraph)
    ]
    parsed: list[dict[str, Any]] = []
    for position, start in enumerate(starts):
        end = starts[position + 1] if position + 1 < len(starts) else len(paragraphs)
        block = paragraphs[start:end]
        record: dict[str, Any] = {
            "title": EXPANDED_CASE_PATTERN.sub("", block[0]).strip(),
            "sections": {value: [] for value in set(EXPANDED_SECTION_NAMES.values())},
        }
        active_section: str | None = None
        for paragraph in block[1:]:
            if paragraph in EXPANDED_SECTION_NAMES:
                active_section = EXPANDED_SECTION_NAMES[paragraph]
                continue
            if active_section:
                record["sections"][active_section].append(paragraph)
        parsed.append(record)
    return parsed


def build_case(
    sequence: int,
    scene_id: str,
    title: str,
    facts: str,
    provisions: str,
    analysis: str,
    source_name: str,
) -> dict[str, Any]:
    clean_title = TITLE_NUMBER_PATTERN.sub("", title).strip()
    record = {
        "case_id": f"DLCL-{sequence:04d}",
        "title": clean_title,
        "scene_id": scene_id,
        "record_type": classify_record(clean_title, facts, analysis),
        "jurisdiction": infer_jurisdiction(clean_title, facts, provisions),
        "case_status": "待补证",
        "basic_facts": facts or None,
        "dispute_focus": None,
        "legal_provisions": [
            {
                "citation_text": provisions,
                "source_url": None,
                "evidence_status": "待补证",
            }
        ]
        if provisions
        else [],
        "outcome_type": "unknown",
        "outcome": None,
        "outcome_evidence_status": "missing",
        "legal_analysis": analysis or None,
        "analysis_origin": "source_material",
        "sources": [
            {
                "title": source_name,
                "url": None,
                "published_at": None,
                "retrieved_at": None,
                "source_tier": "source_material",
            }
        ],
        "evidence_status": "待补证",
        "classification_review_required": True,
        "version": 1,
    }
    errors = validate_case(record)
    if errors:
        raise ValueError(f"{record['case_id']} contract errors: {errors}")
    return record


def extract_summary(source_docx: Path, output_root: Path) -> dict[str, Any]:
    source_docx = Path(source_docx)
    output_root = Path(output_root)
    tables = read_docx_tables(source_docx)
    if len(tables) != 11:
        raise ValueError(f"预期 11 张表，实际 {len(tables)} 张")

    overview_rows = tables[0][1:]
    if len(overview_rows) != 10:
        raise ValueError(f"预期 10 个场景，实际 {len(overview_rows)} 个")

    scenes: list[dict[str, Any]] = []
    cases: list[dict[str, Any]] = []
    scene_case_counts: list[int] = []
    sequence = 1

    for index, (overview_row, detail_table) in enumerate(
        zip(overview_rows, tables[1:]), start=1
    ):
        scene_id = f"scene-{index:02d}"
        scene_name = normalize_text(overview_row[1])
        detail_rows = [row for row in detail_table[1:] if row and any(row)]
        scene_case_counts.append(len(detail_rows))
        scenes.append(
            {
                "scene_id": scene_id,
                "order": index,
                "name": scene_name,
                "slug": f"scene-{index:02d}",
                "description": None,
                "case_count": len(detail_rows),
            }
        )
        for row in detail_rows:
            if len(row) < 4:
                raise ValueError(f"{scene_name} 中存在少于四列的案例行")
            cases.append(
                build_case(
                    sequence=sequence,
                    scene_id=scene_id,
                    title=normalize_text(row[0]),
                    facts=normalize_text(row[1]),
                    provisions=normalize_text(row[2]),
                    analysis=normalize_text(row[3]),
                    source_name=source_docx.name,
                )
            )
            sequence += 1

    data_dir = output_root / "data"
    cases_dir = data_dir / "cases"
    cases_dir.mkdir(parents=True, exist_ok=True)
    for stale in cases_dir.glob("DLCL-*.json"):
        stale.unlink()
    for case in cases:
        write_json(cases_dir / f"{case['case_id']}.json", case)

    write_json(data_dir / "scenes.json", scenes)
    manifest = {
        "library_name": "数据法学案例库",
        "library_version": 1,
        "source_file": source_docx.name,
        "source_sha256": hashlib.sha256(source_docx.read_bytes()).hexdigest(),
        "scene_count": len(scenes),
        "case_count": len(cases),
        "evidence_status": "待补证",
        "knowledge_sync_status": "not_started",
    }
    write_json(data_dir / "manifest.json", manifest)
    return {
        "status": "extracted",
        "scene_count": len(scenes),
        "case_count": len(cases),
        "scene_case_counts": scene_case_counts,
        "output_root": str(output_root),
    }


def merge_expanded_document(
    expanded_docx: Path, output_root: Path
) -> dict[str, Any]:
    expanded_docx = Path(expanded_docx)
    output_root = Path(output_root)
    case_paths = sorted((output_root / "data" / "cases").glob("DLCL-*.json"))
    cases = [json.loads(path.read_text(encoding="utf-8")) for path in case_paths]
    cases_by_title = {canonical_title(case["title"]): case for case in cases}

    matched_count = 0
    unmatched: list[dict[str, Any]] = []
    review_queue: list[dict[str, Any]] = []

    for expanded in parse_expanded_cases(expanded_docx):
        key = canonical_title(expanded["title"])
        case = cases_by_title.get(key)
        if case is None:
            candidates = [
                item
                for title, item in cases_by_title.items()
                if key in title or title in key
            ]
            case = candidates[0] if len(candidates) == 1 else None
        if case is None:
            unmatched.append({"title": expanded["title"], "reason": "no_unique_match"})
            continue

        matched_count += 1
        sections = expanded["sections"]
        fact_detail = "\n\n".join(
            sections["case_facts"] + sections["case_details"]
        ).strip()
        if fact_detail:
            case["basic_facts"] = fact_detail
        dispute_focus = "\n\n".join(sections["dispute_focus"]).strip()
        if dispute_focus:
            case["dispute_focus"] = dispute_focus
        provision_text = "\n\n".join(sections["legal_provisions"]).strip()
        if provision_text and all(
            item.get("citation_text") != provision_text
            for item in case["legal_provisions"]
        ):
            case["legal_provisions"].append(
                {
                    "citation_text": provision_text,
                    "source_url": None,
                    "evidence_status": "材料已核对",
                }
            )
        outcome_text = "\n\n".join(sections["outcome"]).strip()
        if outcome_text:
            if re.search(r"若进入司法程序|可能从|可能被要求", outcome_text):
                review_queue.append(
                    {
                        "case_id": case["case_id"],
                        "title": case["title"],
                        "reason": "speculative_outcome",
                        "candidate_outcome": outcome_text,
                        "status": "awaiting_teacher_confirmation",
                    }
                )
            else:
                case["outcome"] = outcome_text
                case["outcome_evidence_status"] = "source_material"
                case["outcome_type"] = (
                    "settlement" if "调解" in outcome_text else "judgment"
                )
        analysis_detail = "\n\n".join(sections["legal_analysis"]).strip()
        if analysis_detail:
            case["legal_analysis"] = analysis_detail
        if all(
            source.get("title") != expanded_docx.name for source in case["sources"]
        ):
            case["sources"].append(
                {
                    "title": expanded_docx.name,
                    "url": None,
                    "published_at": None,
                    "retrieved_at": None,
                    "source_tier": "source_material",
                }
            )
        write_json(
            output_root / "data" / "cases" / f"{case['case_id']}.json",
            case,
        )

    write_json(output_root / "data" / "review-queue.json", review_queue)
    manifest_path = output_root / "data" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["expanded_source_file"] = expanded_docx.name
    manifest["expanded_matches"] = matched_count
    manifest["review_required_count"] = len(review_queue)
    write_json(manifest_path, manifest)
    return {
        "status": "merged_with_review_queue"
        if review_queue
        else "merged",
        "matched_count": matched_count,
        "unmatched_count": len(unmatched),
        "unmatched": unmatched,
        "review_required_count": len(review_queue),
        "total_after_merge": len(cases),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_docx", type=Path)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--expanded-docx", type=Path)
    args = parser.parse_args()
    try:
        result = extract_summary(args.source_docx, args.output_root)
        if args.expanded_docx:
            result["expanded_merge"] = merge_expanded_document(
                args.expanded_docx, args.output_root
            )
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except Exception as exc:  # pragma: no cover - CLI error adapter
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        print(repr(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
