#!/usr/bin/env python3
"""案例库结构化数据的共享校验与序列化工具。"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


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
        and str(source.get("url") or "").startswith(("https://", "http://"))
        and source.get("source_tier") in {"official", "primary_official"}
    ]
    if record.get("evidence_status") == "官方来源已核验" and not official_sources:
        errors.append("official_evidence_requires_source")
    if record.get("outcome_evidence_status") == "verified" and not official_sources:
        errors.append("verified_outcome_requires_source")
    for item in record.get("legal_provisions") or []:
        if not isinstance(item, dict):
            continue
        if item.get("evidence_status") in {"官方来源已核验", "verified"} and not str(
            item.get("source_url") or ""
        ).startswith(("https://", "http://")):
            errors.append("verified_law_requires_source")
            break
    return errors


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
    visible_statuses = {"待补证", "已发布"}
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
    except Exception as exc:
        errors.append(f"release_artifact_unreadable:{type(exc).__name__}")
    return sorted(set(errors))
