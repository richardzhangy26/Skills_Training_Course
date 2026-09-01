#!/usr/bin/env python3
"""案例库结构化数据的共享校验与序列化工具。"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


CASE_ID_PATTERN = re.compile(r"^DLCL-\d{4}$")
SENSITIVE_PATTERNS = {
    "mainland_id_number": re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)"),
    "phone_number": re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"),
    "authorization_credential": re.compile(
        r"(?i)\b(?:authorization|cookie)\s*[:=]\s*(?:bearer\s+)?[^\s,;]{8,}"
    ),
    "bearer_credential": re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._-]{12,}"),
    "jwt_credential": re.compile(
        r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"
    ),
    "private_key": re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----"),
    "email_address": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    "student_identifier": re.compile(
        r"(?i)(?:学号|学生\s*ID|student[_ -]?id)\s*(?:为|是)?\s*[:=：]?\s*[A-Za-z0-9_-]{6,32}"
    ),
    "minor_name": re.compile(
        r"(?:未成年人姓名|儿童姓名|学生姓名)\s*[:=：]?\s*[\u3400-\u9fff·]{2,12}"
    ),
}
ACTOR_REFERENCE_PATTERN = re.compile(r"^audit:[A-Za-z0-9_-]{8,64}$")
CONFIRMATION_NONCE_PATTERN = re.compile(r"^[A-Za-z0-9_-]{12,128}$")
OFFICIAL_HOST_SUFFIXES = {
    "gov.cn",
    "npc.gov.cn",
    "court.gov.cn",
    "spp.gov.cn",
    "cac.gov.cn",
    "samr.gov.cn",
    "miit.gov.cn",
    "moj.gov.cn",
    "mps.gov.cn",
    "ftc.gov",
    "justice.gov",
    "sec.gov",
    "europa.eu",
    "eur-lex.europa.eu",
    "coe.int",
    "edpb.europa.eu",
    "ico.org.uk",
    "gov.uk",
}
REQUIRED_CASE_FIELDS = (
    "case_id",
    "title",
    "scene_id",
    "record_type",
    "jurisdiction",
    "case_status",
    "basic_facts",
    "dispute_focus",
    "legal_provisions",
    "outcome_type",
    "outcome",
    "outcome_evidence_status",
    "legal_analysis",
    "analysis_origin",
    "sources",
    "evidence_status",
    "classification_review_required",
    "version",
)


def validate_case(record: dict[str, Any]) -> list[str]:
    """返回稳定错误码；空列表表示记录满足基础契约。"""

    errors = [
        f"missing_field:{field}"
        for field in REQUIRED_CASE_FIELDS
        if field not in record
    ]
    if errors:
        return errors

    if not CASE_ID_PATTERN.fullmatch(str(record["case_id"])):
        errors.append("invalid_case_id")
    if not str(record["title"]).strip():
        errors.append("empty_title")
    if not str(record["scene_id"]).startswith("scene-"):
        errors.append("invalid_scene_id")
    if not isinstance(record["legal_provisions"], list):
        errors.append("legal_provisions_must_be_list")
    if not isinstance(record["sources"], list):
        errors.append("sources_must_be_list")
    if record["outcome"] and record["outcome_evidence_status"] == "missing":
        errors.append("outcome_requires_evidence")
    if not isinstance(record["version"], int) or record["version"] < 1:
        errors.append("invalid_version")
    if record.get("analysis_origin") not in {
        "source_material",
        "teacher_confirmed",
        "ai_draft",
    }:
        errors.append("invalid_analysis_origin")
    errors.extend(evidence_validation_errors(record))
    for marker in find_sensitive_markers(record):
        errors.append(f"sensitive_content:{marker}")
    return errors


def evidence_validation_errors(record: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    sources = record.get("sources") or []
    official_sources = [
        source
        for source in sources
        if isinstance(source, dict)
        and is_official_source_url(source.get("url"))
        and source.get("source_tier") in {"official", "primary_official"}
    ]
    if record.get("evidence_status") == "官方来源已核验" and not official_sources:
        errors.append("official_evidence_requires_source")
    if record.get("outcome_evidence_status") == "verified" and not official_sources:
        errors.append("verified_outcome_requires_source")
    outcome_status = record.get("outcome_evidence_status")
    if (
        "outcome_evidence_status" in record
        and outcome_status not in {"missing", "source_material", "verified"}
    ):
        errors.append("invalid_outcome_evidence_status")
    outcome = str(record.get("outcome") or "")
    if outcome and re.search(
        r"(?:若|如|如果).{0,160}(?:可能|将|会)|可能面临|还可能涉及|可能从|可能被要求|预计将|预计会|(?:法院|平台|机构|企业|经营者).{0,60}(?:可能|预计|或将).{0,60}(?:判令|承担|面临|被要求)",
        outcome,
    ):
        errors.append("speculative_outcome_requires_review")
    valid_material_sources = [
        source
        for source in sources
        if isinstance(source, dict)
        and (str(source.get("title") or "").strip() or str(source.get("url") or "").strip())
    ]
    if outcome and outcome_status == "source_material" and not valid_material_sources:
        errors.append("source_outcome_requires_source")
    for item in record.get("legal_provisions") or []:
        if not isinstance(item, dict):
            continue
        if item.get("evidence_status") in {"官方来源已核验", "verified"} and not is_official_source_url(
            item.get("source_url")
        ):
            errors.append("verified_law_requires_source")
            break
    return errors


def validate_actor_reference(actor_reference: str | None) -> bool:
    return actor_reference is None or bool(
        ACTOR_REFERENCE_PATTERN.fullmatch(actor_reference)
    )


def validate_confirmation_nonce(confirmation_nonce: str | None) -> bool:
    return bool(
        confirmation_nonce
        and CONFIRMATION_NONCE_PATTERN.fullmatch(confirmation_nonce)
    )


def is_official_source_url(url: Any) -> bool:
    try:
        parsed = urlparse(str(url or ""))
    except ValueError:
        return False
    if parsed.scheme not in {"https", "http"} or not parsed.hostname:
        return False
    host = parsed.hostname.lower().rstrip(".")
    return any(host == suffix or host.endswith(f".{suffix}") for suffix in OFFICIAL_HOST_SUFFIXES)


def format_optional(value: str | None) -> str:
    return value.strip() if value and value.strip() else "原材料未提供"


def build_knowledge_block(
    case: dict[str, Any], scene: dict[str, Any]
) -> dict[str, Any]:
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


def find_sensitive_markers(value: Any) -> list[str]:
    """递归扫描候选结构中的常见个人标识与凭证模式。"""

    strings: list[str] = []

    def visit(item: Any) -> None:
        if isinstance(item, str):
            strings.append(item)
        elif isinstance(item, dict):
            for child in item.values():
                visit(child)
        elif isinstance(item, (list, tuple, set)):
            for child in item:
                visit(child)

    visit(value)
    markers = {
        name
        for name, pattern in SENSITIVE_PATTERNS.items()
        if any(pattern.search(text) for text in strings)
    }
    return sorted(markers)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def resolve_active_root(library_root: Path) -> Path:
    """解析原子版本指针；无指针时兼容初始根目录版本。"""

    library_root = Path(library_root)
    pointer = library_root / "current.json"
    if not pointer.exists():
        return library_root
    value = read_json(pointer)
    release = value.get("release", "")
    if not re.fullmatch(r"v\d{4}", release):
        raise ValueError("invalid_current_release")
    resolved = library_root / "releases" / release
    if not (resolved / "data" / "manifest.json").is_file():
        raise ValueError("current_release_missing")
    return resolved


def validate_release_root(
    release_root: Path, require_exports: bool = True
) -> list[str]:
    """校验一个不可变发布版本的数据与学生产物是否一致。"""

    release_root = Path(release_root)
    errors: list[str] = []
    try:
        manifest = read_json(release_root / "data" / "manifest.json")
        scenes = read_json(release_root / "data" / "scenes.json")
        cases = [
            read_json(path)
            for path in sorted((release_root / "data" / "cases").glob("DLCL-*.json"))
        ]
    except Exception as exc:
        return [f"release_data_unreadable:{type(exc).__name__}"]

    if manifest.get("scene_count") != len(scenes):
        errors.append("manifest_scene_count_mismatch")
    if manifest.get("case_count") != len(cases):
        errors.append("manifest_case_count_mismatch")
    case_ids = [case.get("case_id") for case in cases]
    if len(case_ids) != len(set(case_ids)):
        errors.append("duplicate_case_id")

    scene_ids = {scene.get("scene_id") for scene in scenes}
    visible_statuses = {"已发布"}
    visible_cases = [case for case in cases if case.get("case_status") in visible_statuses]
    visible_ids = {case.get("case_id") for case in visible_cases}
    if manifest.get("visible_case_count", len(visible_cases)) != len(visible_cases):
        errors.append("manifest_visible_case_count_mismatch")
    for case in cases:
        errors.extend(validate_case(case))
        if case.get("scene_id") not in scene_ids:
            errors.append(f"unknown_scene:{case.get('case_id')}")
    for scene in scenes:
        actual = sum(
            case.get("scene_id") == scene.get("scene_id") for case in visible_cases
        )
        if scene.get("case_count") != actual:
            errors.append(f"scene_case_count_mismatch:{scene.get('scene_id')}")

    if not require_exports:
        return sorted(set(errors))
    html_path = release_root / "exports" / "数据法学案例库.html"
    knowledge_path = release_root / "exports" / "案例专家知识包.jsonl"
    if not html_path.is_file():
        errors.append("html_missing")
    if not knowledge_path.is_file():
        errors.append("knowledge_pack_missing")
    if errors:
        return sorted(set(errors))

    try:
        html_text = html_path.read_text(encoding="utf-8")
        html_ids = set(re.findall(r'data-case-id="(DLCL-\d{4})"', html_text))
        if html_ids != visible_ids:
            errors.append("html_case_ids_mismatch")
        if "actor_reference" in html_text:
            errors.append("html_contains_private_audit_field")
        payload_match = re.search(
            r'<script id="case-data" type="application/json">(.*?)</script>',
            html_text,
            re.DOTALL,
        )
        if not payload_match:
            errors.append("html_case_payload_missing")
        else:
            payload = json.loads(payload_match.group(1))
            expected_payload = {
                "manifest": manifest,
                "scenes": scenes,
                "cases": visible_cases,
            }
            if payload != expected_payload:
                errors.append("html_case_payload_mismatch")
        knowledge_records = [
            json.loads(line)
            for line in knowledge_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        knowledge_ids = {
            item.get("metadata", {}).get("case_id") for item in knowledge_records
        }
        if knowledge_ids != visible_ids:
            errors.append("knowledge_case_ids_mismatch")
        block_ids = [item.get("knowledge_id") for item in knowledge_records]
        if len(block_ids) != len(set(block_ids)):
            errors.append("duplicate_knowledge_id")
        scenes_by_id = {scene["scene_id"]: scene for scene in scenes}
        expected_knowledge_records = [
            build_knowledge_block(case, scenes_by_id[case["scene_id"]])
            for case in visible_cases
        ]
        if knowledge_records != expected_knowledge_records:
            errors.append("knowledge_content_mismatch")
    except Exception as exc:
        errors.append(f"release_artifact_unreadable:{type(exc).__name__}")
    return sorted(set(errors))
