"""从完整线上配置构造最小、安全的专家期望配置。"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .contracts import TargetConfig


class DesiredConfigError(ValueError):
    """Skill 或完整配置无法无损、安全地转换。"""


def _clone(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _clone(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_clone(item) for item in value]
    return value


def build_desired_config(
    current_full_config: Mapping[str, Any],
    target: TargetConfig,
    agent_content: str,
) -> dict[str, Any]:
    """克隆服务器完整配置，仅替换 Expert 正文并按声明顺序重组 Skill。"""

    if not isinstance(current_full_config, Mapping) or not isinstance(agent_content, str):
        raise DesiredConfigError("config_contract_changed")
    desired = _clone(current_full_config)
    expert_md = desired.get("expertMd")
    skills = desired.get("skillInfoList")
    if not isinstance(expert_md, dict) or not isinstance(skills, list):
        raise DesiredConfigError("config_contract_changed")

    expected_names = tuple(target.expected_skill_order)
    declared = dict(target.online_skill_nids)
    if set(expected_names) != set(declared) or len(expected_names) != len(set(expected_names)):
        raise DesiredConfigError("declared_skill_contract_invalid")

    by_name: dict[str, dict[str, Any]] = {}
    seen_nids: set[str] = set()
    for item in skills:
        if not isinstance(item, dict):
            raise DesiredConfigError("skill_contract_changed")
        name = item.get("name")
        nid = item.get("skillNid")
        if not isinstance(name, str) or not isinstance(nid, str):
            raise DesiredConfigError("skill_contract_changed")
        if name not in declared or declared[name] != nid:
            raise DesiredConfigError("unknown_or_mismatched_skill")
        if item.get("bindingSource") != target.online_skill_binding_sources[name]:
            raise DesiredConfigError("binding_source_mismatch")
        if name in by_name or nid in seen_nids:
            raise DesiredConfigError("duplicate_skill")
        by_name[name] = item
        seen_nids.add(nid)

    if set(by_name) != set(expected_names):
        raise DesiredConfigError("missing_skill")

    expert_md["customContent"] = agent_content
    desired["skillInfoList"] = [by_name[name] for name in expected_names]
    return desired
