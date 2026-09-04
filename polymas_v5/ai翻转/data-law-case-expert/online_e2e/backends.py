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


@dataclass(frozen=True)
class FixtureOwnership:
    run_id: str
    target_case_ids: tuple[str, ...]
    baseline_case_ids: tuple[str, ...] | None

    def __post_init__(self):
        if (
            not isinstance(self.run_id, str)
            or not self.run_id
            or type(self.target_case_ids) is not tuple
            or len(self.target_case_ids) != 2
            or len(set(self.target_case_ids)) != 2
            or any(not isinstance(case_id, str) or not case_id for case_id in self.target_case_ids)
        ):
            raise ValueError("invalid_fixture_targets")
        if self.baseline_case_ids is not None:
            if (
                type(self.baseline_case_ids) is not tuple
                or len(self.baseline_case_ids) != len(set(self.baseline_case_ids))
                or not set(self.baseline_case_ids).issubset(self.target_case_ids)
            ):
                raise ValueError("invalid_fixture_baseline")

    @property
    def collision(self) -> bool:
        return bool(self.baseline_case_ids)

    def _current(self, current_case_ids) -> tuple[str, ...]:
        current = tuple(current_case_ids)
        if (
            len(current) != len(set(current))
            or not set(current).issubset(self.target_case_ids)
        ):
            raise ValueError("invalid_fixture_current")
        return tuple(sorted(current))

    def created_from(self, current_case_ids) -> tuple[str, ...]:
        if self.baseline_case_ids is None:
            raise ValueError("fixture_baseline_unverified")
        current = self._current(current_case_ids)
        if not set(self.baseline_case_ids).issubset(current):
            raise ValueError("fixture_baseline_changed")
        return tuple(sorted(set(current) - set(self.baseline_case_ids)))

    def cleanup_case_ids(self, current_case_ids) -> tuple[str, ...]:
        return self.created_from(current_case_ids)

    def is_restored(self, current_case_ids) -> bool:
        if self.baseline_case_ids is None:
            return False
        return self._current(current_case_ids) == tuple(sorted(self.baseline_case_ids))

    def as_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "target_case_ids": list(self.target_case_ids),
            "baseline_case_ids": (
                list(self.baseline_case_ids) if self.baseline_case_ids is not None else None
            ),
        }


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
    def existing_case_ids(self, case_ids: tuple[str, ...]) -> Mapping[str, Any]: ...
    def cleanup_teacher_cases(self, case_ids: tuple[str, ...], run_id: str) -> Mapping[str, Any]: ...
    def restore_knowledge(self, snapshot: KnowledgeSnapshot, *, owned_version: str,
                          owned_digest: str) -> Mapping[str, Any]: ...
    def verify_cases_absent(self, case_ids: tuple[str, ...]) -> bool: ...
    def restore_config(self, snapshot: ConfigSnapshot, *, owned_digest: str) -> Mapping[str, Any]: ...
