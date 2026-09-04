"""联调目标的纯数据契约与版本化配置加载。"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path
import re
from types import MappingProxyType
from typing import Any, Mapping


_TARGET_ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")


@dataclass(frozen=True)
class TargetConfig:
    """一个受版本控制的 PDS 联调目标。"""

    target_id: str
    expert_nid: str
    expert_name: str
    assistant_nid: str
    assistant_name: str
    isolated_test_assistant_nid: str | None
    isolated_test_assistant_name: str | None
    live_test_enabled: bool
    knowledge_base_nid: str | None
    agent_path: Path
    query_skill_path: Path
    maintenance_skill_path: Path
    html_path: Path
    knowledge_jsonl_path: Path
    manifest_path: Path
    online_skill_nids: Mapping[str, str]
    online_skill_binding_sources: Mapping[str, str]
    expected_skill_order: tuple[str, ...]
    runtime_agent_nid: str | None = None


@dataclass(frozen=True)
class ConfigSnapshot:
    """规范化后的线上配置及其可重复计算的摘要。"""

    normalized: Mapping[str, Any]
    digest: str
    canonical_json: str


@dataclass(frozen=True)
class Difference:
    """期望配置与线上快照间的一个可显示差异。"""

    path: str
    kind: str
    expected: Any
    actual: Any


@dataclass(frozen=True)
class ConfigDiff:
    """配置比较结果；出现未声明 Skill 时禁止写入。"""

    expected: ConfigSnapshot
    actual: ConfigSnapshot
    items: tuple[Difference, ...]
    apply_allowed: bool


@dataclass(frozen=True)
class ConfirmationBinding:
    """确认令牌必须绑定的不可变预览上下文。"""

    target_id: str
    snapshot_digest: str
    expected_digest: str
    knowledge_version: str
    knowledge_digest: str
    diff_digest: str
    nonce: str


class StageStatus(str, Enum):
    """联调阶段的稳定状态集合。"""

    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"


@dataclass(frozen=True)
class StageState:
    name: str
    status: StageStatus
    detail: str | None = None


@dataclass(frozen=True)
class KnowledgeSnapshot:
    """知识产物版本及内容摘要，不保存其原始内容。"""

    version: str
    digest: str
    source: str | None = None


@dataclass(frozen=True)
class TestAssertionResult:
    name: str
    passed: bool
    expected: Any = None
    actual: Any = None
    detail: str | None = None


@dataclass(frozen=True)
class RunRequest:
    target_id: str
    run_id: str
    apply: bool = False
    confirmation_token: str | None = None


@dataclass(frozen=True)
class RunResult:
    target_id: str
    run_id: str
    status: StageStatus
    stages: tuple[StageState, ...] = ()
    config_snapshot: ConfigSnapshot | None = None
    knowledge_snapshot: KnowledgeSnapshot | None = None
    differences: tuple[Difference, ...] = ()
    assertions: tuple[TestAssertionResult, ...] = ()
    checkpoint_path: str | None = None


def _project_root(root: Path | None) -> Path:
    return (root or Path(__file__).resolve().parents[1]).resolve()


def load_target_config(target_id: str, *, root: Path | None = None) -> TargetConfig:
    """加载一个仅含公开标识和本地路径的目标配置。"""

    if not isinstance(target_id, str) or not _TARGET_ID.fullmatch(target_id):
        raise ValueError("invalid_target_id")
    project_root = _project_root(root)
    config_path = Path(__file__).with_name("targets") / f"{target_id}.json"
    data = json.loads(config_path.read_text(encoding="utf-8"))
    if data.get("target_id") != target_id:
        raise ValueError("target_id_mismatch")

    assets = data["local_assets"]
    skill_nids = dict(data["online_skill_nids"])
    binding_sources = dict(data["online_skill_binding_sources"])
    skill_order = tuple(data["expected_skill_order"])
    if (
        set(skill_nids) != set(binding_sources)
        or set(skill_nids) != set(skill_order)
        or len(skill_order) != len(set(skill_order))
        or any(not isinstance(value, str) or not value for value in skill_nids.values())
        or any(value not in ("BUILTIN", "MARKETPLACE") for value in binding_sources.values())
    ):
        raise ValueError("skill_mapping_mismatch")
    return TargetConfig(
        target_id=data["target_id"],
        expert_nid=data["expert_nid"],
        expert_name=data["expert_name"],
        assistant_nid=data["assistant_nid"],
        assistant_name=data["assistant_name"],
        isolated_test_assistant_nid=data.get("isolated_test_assistant_nid"),
        isolated_test_assistant_name=data.get("isolated_test_assistant_name"),
        live_test_enabled=data.get("live_test_enabled") is True,
        knowledge_base_nid=data.get("knowledge_base_nid"),
        agent_path=project_root / assets["agent"],
        query_skill_path=project_root / assets["query_skill"],
        maintenance_skill_path=project_root / assets["maintenance_skill"],
        html_path=project_root / assets["html"],
        knowledge_jsonl_path=project_root / assets["knowledge_jsonl"],
        manifest_path=project_root / assets["manifest"],
        online_skill_nids=MappingProxyType(skill_nids),
        online_skill_binding_sources=MappingProxyType(binding_sources),
        expected_skill_order=skill_order,
        runtime_agent_nid=data.get("runtime_agent_nid"),
    )
