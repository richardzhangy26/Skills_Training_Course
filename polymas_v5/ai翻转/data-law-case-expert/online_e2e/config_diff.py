"""线上配置的规范化、摘要和安全差异计算。"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import hashlib
import json
from types import MappingProxyType
from typing import Any

from .contracts import ConfigDiff, ConfigSnapshot, Difference, KnowledgeSnapshot


UNRESOLVED_NID_PREFIX = "PDS_NID_UNRESOLVED_"
CONTRACT_CHANGED = "CONTRACT_CHANGED"


def _jsonable(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


def _canonical_json(value: Any) -> str:
    return json.dumps(
        _jsonable(value), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(key): _freeze(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    return value


def _skill_sort_key(value: Any) -> tuple[str, str, str]:
    if isinstance(value, Mapping):
        return (
            str(value.get("nid", "")),
            str(value.get("name", "")),
            _canonical_json(value),
        )
    return ("", "", _canonical_json(value))


def normalize_online_config(value: Any, *, _field: str | None = None) -> Any:
    """将对象键排序，并将 Skill 列表按不可变 NID 排序。"""

    if isinstance(value, Mapping):
        return {
            str(key): normalize_online_config(item, _field=str(key))
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (list, tuple)):
        normalized = [normalize_online_config(item) for item in value]
        if _field == "skills":
            return sorted(normalized, key=_skill_sort_key)
        return normalized
    return value


def snapshot_config(config: Mapping[str, Any]) -> ConfigSnapshot:
    """创建深度不可变、可稳定比较的线上配置快照。"""

    normalized = normalize_online_config(config)
    canonical_json = _canonical_json(normalized)
    return ConfigSnapshot(
        normalized=_freeze(normalized),
        digest=hashlib.sha256(canonical_json.encode("utf-8")).hexdigest(),
        canonical_json=canonical_json,
    )


def _skills(config: Mapping[str, Any]) -> list[Any]:
    skills = config.get("skills", ())
    if not isinstance(skills, Sequence) or isinstance(skills, (str, bytes)):
        return []
    return list(skills)


def _valid_nid(record: Any) -> str | None:
    if not isinstance(record, Mapping):
        return None
    nid = record.get("nid")
    if not isinstance(nid, str) or not nid.strip():
        return None
    return nid


def _skill_records(config: Mapping[str, Any]) -> list[tuple[int, Any, str | None]]:
    return [(index, record, _valid_nid(record)) for index, record in enumerate(_skills(config))]


def _skill_contract_changes(
    config: Mapping[str, Any], *, expected: bool
) -> list[Difference]:
    raw_skills = config.get("skills", ())
    if not isinstance(raw_skills, (list, tuple)):
        return [
            Difference(
                "skills",
                CONTRACT_CHANGED,
                raw_skills if expected else None,
                None if expected else raw_skills,
            )
        ]
    return [
        Difference(
            f"skills[index={index}]",
            CONTRACT_CHANGED,
            record if expected else None,
            None if expected else record,
        )
        for index, record in enumerate(raw_skills)
        if not isinstance(record, Mapping)
    ]


def _field_differences(expected: Any, actual: Any, path: str = "") -> list[Difference]:
    if isinstance(expected, Mapping) and isinstance(actual, Mapping):
        items: list[Difference] = []
        for key in sorted(set(expected) | set(actual)):
            if key == "skills" and not path:
                continue
            child_path = f"{path}.{key}" if path else str(key)
            if key not in expected:
                items.append(Difference(child_path, "unexpected", None, actual[key]))
            elif key not in actual:
                items.append(Difference(child_path, "missing", expected[key], None))
            else:
                items.extend(_field_differences(expected[key], actual[key], child_path))
        return items
    if expected != actual:
        return [Difference(path, "changed", expected, actual)]
    return []


def _skill_differences(
    expected: Mapping[str, Any], actual: Mapping[str, Any]
) -> list[Difference]:
    expected_records = _skill_records(expected)
    actual_records = _skill_records(actual)
    expected_by_nid = {
        nid: record for _, record, nid in expected_records if nid is not None
    }
    actual_by_nid = {nid: record for _, record, nid in actual_records if nid is not None}
    items: list[Difference] = []

    for index, record, nid in expected_records:
        if nid is None:
            items.append(Difference(f"skills[index={index}]", "invalid_skill", record, None))
    for index, record, nid in actual_records:
        if nid is None:
            items.append(Difference(f"skills[index={index}]", "invalid_skill", None, record))

    for nid in sorted(set(expected_by_nid) | set(actual_by_nid)):
        path = f"skills[nid={nid}]"
        if nid not in expected_by_nid:
            items.append(Difference(path, "unexpected_skill", None, actual_by_nid[nid]))
        elif nid not in actual_by_nid:
            items.append(Difference(path, "missing_skill", expected_by_nid[nid], None))
        else:
            items.extend(_field_differences(expected_by_nid[nid], actual_by_nid[nid], path))
    return items


def _apply_blockers(
    expected: Mapping[str, Any],
    actual: Mapping[str, Any],
    declared_skill_nids: Mapping[str, str],
) -> list[Difference]:
    expected_records = _skill_records(expected)
    actual_records = _skill_records(actual)
    expected_nids = {nid for _, _, nid in expected_records if nid is not None}
    declared_nids = set(declared_skill_nids.values())
    blockers = _skill_contract_changes(expected, expected=True)
    blockers.extend(_skill_contract_changes(actual, expected=False))

    for index, record, nid in expected_records:
        path = f"skills[index={index}]" if nid is None else f"skills[nid={nid}]"
        if nid is None:
            blockers.append(Difference(path, "missing_skill_nid", record, None))
        elif nid.startswith(UNRESOLVED_NID_PREFIX):
            blockers.append(Difference(path, "unresolved_skill_nid", nid, None))
        elif nid not in declared_nids:
            blockers.append(Difference(path, "undeclared_skill", nid, None))

    for index, record, nid in actual_records:
        path = f"skills[index={index}]" if nid is None else f"skills[nid={nid}]"
        if nid is None:
            blockers.append(Difference(path, "missing_skill_nid", None, record))
        else:
            if nid not in declared_nids:
                blockers.append(Difference(path, "undeclared_skill", None, nid))
            if nid not in expected_nids:
                blockers.append(Difference(path, "unexpected_skill_nid", None, nid))
    return blockers


def compare_configs(
    expected: Mapping[str, Any],
    actual: Mapping[str, Any],
    *,
    declared_skill_nids: Mapping[str, str],
) -> ConfigDiff:
    """比较配置；不完整或未预览的不可变 Skill NID 一律禁止 apply。"""

    expected_snapshot = snapshot_config(expected)
    actual_snapshot = snapshot_config(actual)
    blockers = _apply_blockers(
        expected_snapshot.normalized,
        actual_snapshot.normalized,
        declared_skill_nids,
    )
    items = list(blockers)
    items.extend(
        _field_differences(expected_snapshot.normalized, actual_snapshot.normalized)
    )
    items.extend(_skill_differences(expected_snapshot.normalized, actual_snapshot.normalized))
    return ConfigDiff(
        expected=expected_snapshot,
        actual=actual_snapshot,
        items=tuple(items),
        apply_allowed=not blockers,
    )


def require_apply_allowed(report: ConfigDiff) -> None:
    """在任何线上 apply 之前执行，阻断原因会包含在稳定错误码中。"""

    if not report.apply_allowed:
        blockers = {
            CONTRACT_CHANGED,
            "missing_skill_nid",
            "undeclared_skill",
            "unexpected_skill_nid",
            "unresolved_skill_nid",
        }
        reason = next(
            (item.kind for item in report.items if item.kind in blockers),
            "apply_blocked",
        )
        raise ValueError(f"{reason}_blocks_apply")


def snapshot_knowledge(
    version: str, content: str | bytes, *, source: str | None = None
) -> KnowledgeSnapshot:
    """只保存知识产物的版本和摘要，避免在报告中复制原始知识内容。"""

    payload = content.encode("utf-8") if isinstance(content, str) else content
    return KnowledgeSnapshot(
        version=version,
        digest=hashlib.sha256(payload).hexdigest(),
        source=source,
    )


def summarize_differences(items: Sequence[Difference]) -> str:
    """为确认令牌提供顺序无关的差异摘要。"""

    summary = sorted(
        (
            {
                "actual": item.actual,
                "expected": item.expected,
                "kind": item.kind,
                "path": item.path,
            }
            for item in items
        ),
        key=_canonical_json,
    )
    return hashlib.sha256(_canonical_json(summary).encode("utf-8")).hexdigest()
