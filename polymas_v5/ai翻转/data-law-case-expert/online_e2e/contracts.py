"""联调目标的纯数据契约与版本化配置加载。"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping


@dataclass(frozen=True)
class TargetConfig:
    """一个受版本控制的 PDS 联调目标。"""

    target_id: str
    expert_nid: str
    expert_name: str
    assistant_name: str
    agent_path: Path
    query_skill_path: Path
    maintenance_skill_path: Path
    html_path: Path
    knowledge_jsonl_path: Path
    manifest_path: Path
    online_skill_nids: Mapping[str, str]
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

    project_root = _project_root(root)
    config_path = Path(__file__).with_name("targets") / f"{target_id}.json"
    data = json.loads(config_path.read_text(encoding="utf-8"))
    if data.get("target_id") != target_id:
        raise ValueError("target_id_mismatch")

    assets = data["local_assets"]
    return TargetConfig(
        target_id=data["target_id"],
        expert_nid=data["expert_nid"],
        expert_name=data["expert_name"],
        assistant_name=data["assistant_name"],
        agent_path=project_root / assets["agent"],
        query_skill_path=project_root / assets["query_skill"],
        maintenance_skill_path=project_root / assets["maintenance_skill"],
        html_path=project_root / assets["html"],
        knowledge_jsonl_path=project_root / assets["knowledge_jsonl"],
        manifest_path=project_root / assets["manifest"],
        online_skill_nids=MappingProxyType(dict(data["online_skill_nids"])),
        runtime_agent_nid=data.get("runtime_agent_nid"),
    )
