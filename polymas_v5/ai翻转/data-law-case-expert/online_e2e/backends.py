"""runner 与 synthetic/live 实现之间的最小稳定协议。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol

from .contracts import ConfigSnapshot, KnowledgeSnapshot, TargetConfig


@dataclass(frozen=True)
class Blocker:
    code: str
    detail: Any = None

    def as_dict(self) -> dict[str, Any]:
        value = {"code": self.code}
        if self.detail is not None:
            value["detail"] = self.detail
        return value


@dataclass(frozen=True)
class PrecheckResult:
    blockers: tuple[Blocker, ...] = ()
    relationship_version: str | None = None
    assistant_nid: str | None = None


@dataclass(frozen=True)
class RegressionSnapshot:
    config: ConfigSnapshot
    knowledge: KnowledgeSnapshot


class BackendFailure(RuntimeError):
    def __init__(self, code: str, detail: str = ""):
        self.code = code
        self.detail = detail
        super().__init__(code)


class RegressionBackend(Protocol):
    environment: str

    def precheck(self, target: TargetConfig) -> PrecheckResult: ...
    def snapshot(self, target: TargetConfig) -> RegressionSnapshot: ...
    def publish(self, target: TargetConfig, desired: Mapping[str, Any], run_id: str) -> Mapping[str, Any]: ...
    def current_config_digest(self, target: TargetConfig) -> str: ...
    def current_knowledge_snapshot(self) -> KnowledgeSnapshot: ...
    def run_student(self, scenario: Any, assistant_nid: str) -> Mapping[str, Any]: ...
    def upload_teacher_fixture(self, payload: bytes, *, scene: str, case_ids: tuple[str, ...], run_id: str) -> Mapping[str, Any]: ...
    def confirm_teacher_change(self, upload_id: str) -> Mapping[str, Any]: ...
    def sync_teacher_change(self, change_id: str) -> Mapping[str, Any]: ...
    def read_case(self, case_id: str) -> Mapping[str, Any] | None: ...
    def cleanup_teacher_cases(self, case_ids: tuple[str, ...], run_id: str) -> Mapping[str, Any]: ...
    def restore_knowledge(self, snapshot: KnowledgeSnapshot, *, owned_version: str,
                          owned_digest: str) -> Mapping[str, Any]: ...
    def verify_cases_absent(self, case_ids: tuple[str, ...]) -> bool: ...
    def restore_config(self, snapshot: ConfigSnapshot, *, owned_digest: str) -> Mapping[str, Any]: ...
