"""线上配置的规范化、摘要和差异计算。"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

from .contracts import ConfigDiff, ConfigSnapshot, Difference, KnowledgeSnapshot


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


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
    """创建可稳定比较的配置快照。"""

    normalized = normalize_online_config(config)
    digest = hashlib.sha256(_canonical_json(normalized).encode("utf-8")).hexdigest()
    return ConfigSnapshot(normalized=normalized, digest=digest)


def _skill_nids(config: Mapping[str, Any]) -> set[str]:
    skills = config.get("skills", [])
    if not isinstance(skills, list):
        return set()
    return {
        str(skill["nid"])
        for skill in skills
        if isinstance(skill, Mapping) and skill.get("nid")
    }


def _field_differences(expected: Any, actual: Any, path: str = "") -> list[Difference]:
    if isinstance(expected, Mapping) and isinstance(actual, Mapping):
        items: list[Difference] = []
        keys = sorted(set(expected) | set(actual))
        for key in keys:
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


def compare_configs(
    expected: Mapping[str, Any],
    actual: Mapping[str, Any],
    *,
    declared_skill_nids: Mapping[str, str],
) -> ConfigDiff:
    """比较配置，并让线上出现的未声明 Skill 成为 apply 阻断项。"""

    expected_snapshot = snapshot_config(expected)
    actual_snapshot = snapshot_config(actual)
    declared = set(declared_skill_nids.values())
    undeclared = sorted(_skill_nids(actual_snapshot.normalized) - declared)
    items = _field_differences(expected_snapshot.normalized, actual_snapshot.normalized)
    items.extend(
        Difference("skills", "undeclared_skill", None, nid) for nid in undeclared
    )
    return ConfigDiff(
        expected=expected_snapshot,
        actual=actual_snapshot,
        items=tuple(items),
        apply_allowed=not undeclared,
    )


def require_apply_allowed(report: ConfigDiff) -> None:
    """在任何线上 apply 之前执行；未声明 Skill 永远不可被静默保留。"""

    if not report.apply_allowed:
        raise ValueError("undeclared_skill_blocks_apply")


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


def summarize_differences(items: tuple[Difference, ...]) -> str:
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
