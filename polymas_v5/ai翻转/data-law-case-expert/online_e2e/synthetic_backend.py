"""仅供离线状态机回归的 synthetic backend。"""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
import json
from typing import Any

from .backends import BackendFailure, Blocker, PrecheckResult, RegressionSnapshot
from .clients import PdsClient
from .config_diff import snapshot_knowledge
from .contracts import ConfigSnapshot, TargetConfig


_BINDING_SOURCES = {
    "search-router": "BUILTIN",
    "polymas-teacher-knowledge-distillation": "MARKETPLACE",
    "data-law-case-maintenance": "BUILTIN",
    "data-law-case-query": "BUILTIN",
    "polymas-resource-upload": "BUILTIN",
}


def _thaw(value):
    if isinstance(value, Mapping):
        return {str(key): _thaw(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_thaw(item) for item in value]
    return value


class SyntheticRegressionBackend:
    environment = "synthetic"

    def __init__(
        self,
        target: TargetConfig,
        *,
        blockers: tuple[Blocker, ...] = (),
        fail_at: str | None = None,
        external_change_before_rollback: bool = False,
        malformed_teacher_receipt: bool = False,
        malformed_publish_receipt: bool = False,
    ):
        self.target = target
        self.blockers = blockers
        self.fail_at = fail_at
        self.external_change_before_rollback = external_change_before_rollback
        self.malformed_teacher_receipt = malformed_teacher_receipt
        self.malformed_publish_receipt = malformed_publish_receipt
        self.write_count = 0
        self.restore_config_calls = 0
        self.student_calls: list[str] = []
        self.temporary_cases: set[str] = set()
        self.knowledge_version = "knowledge-v1"
        self._knowledge_content = b"synthetic baseline knowledge"
        self._full_config = self._make_full_config("synthetic baseline Agent.md")

    def _make_full_config(self, content: str) -> dict[str, Any]:
        return {
            "basicInfo": {
                "nid": self.target.expert_nid,
                "appName": self.target.expert_name,
                "appType": "EXPERT",
                "isPublish": 1,
            },
            "personaMd": None,
            "soulMd": None,
            "agentMd": None,
            "planMd": None,
            "expertMd": {
                "templateNid": "eu5FW3sdWS",
                "customContent": content,
                "rawContent": "synthetic raw content",
            },
            "skillInfoList": [
                {
                    "skillNid": self.target.online_skill_nids[name],
                    "name": name,
                    "enabled": True,
                    "version": "synthetic",
                    "bindingSource": _BINDING_SOURCES[name],
                    "permission": "TEACHER",
                }
                for name in self.target.expected_skill_order
            ],
            "subAgentVOS": [],
            "mcpInfoList": [],
            "datasets": None,
            "generalSetting": {},
            "agentLlmModelConfig": {},
            "extInfo": {"recommendedQuestions": [], "expertiseAreas": [], "teamScene": None},
        }

    @property
    def agent_content(self) -> str:
        return self._full_config["expertMd"]["customContent"]

    def _config_snapshot(self) -> ConfigSnapshot:
        return PdsClient.snapshot_from_config(self.target.expert_nid, self._full_config, [])

    def precheck(self, target: TargetConfig) -> PrecheckResult:
        return PrecheckResult(
            blockers=self.blockers,
            relationship_version="synthetic-v1",
            assistant_nid="synthetic-assistant",
        )

    def snapshot(self, target: TargetConfig) -> RegressionSnapshot:
        return RegressionSnapshot(
            config=self._config_snapshot(),
            knowledge=snapshot_knowledge(
                self.knowledge_version,
                self._knowledge_content,
                source="synthetic-content-snapshot",
            ),
        )

    def publish(self, target: TargetConfig, desired: Mapping[str, Any], run_id: str):
        if self.fail_at == "publish":
            raise BackendFailure("SYNTHETIC_PUBLISH_FAILED")
        self.write_count += 1
        self._full_config = deepcopy(dict(desired))
        if self.malformed_publish_receipt:
            return {"answer": "published"}
        digest = self._config_snapshot().digest
        return {"published": True, "owned_digest": digest, "assistantId": "synthetic-assistant"}

    def current_config_digest(self, target: TargetConfig) -> str:
        return self._config_snapshot().digest

    def run_student(self, scenario, assistant_nid: str):
        self.write_count += 1
        self.student_calls.append(scenario.scenario_id)
        if self.fail_at == f"student:{scenario.scenario_id}":
            if self.external_change_before_rollback:
                self._full_config["expertMd"]["customContent"] = "external concurrent content"
            raise BackendFailure("SYNTHETIC_STUDENT_FAILED", scenario.scenario_id)
        return {
            "passed": True,
            "scenario_id": scenario.scenario_id,
            "assistantId": "synthetic-assistant",
            "conversationId": f"synthetic-conversation-{scenario.scenario_id}",
            "messageId": f"synthetic-message-{scenario.scenario_id}",
            "planId": f"synthetic-plan-{scenario.scenario_id}",
            "traceId": f"synthetic-trace-{scenario.scenario_id}",
            "answer": f"synthetic content assertion: {scenario.expected_intent}",
        }

    def upload_teacher_fixture(self, payload: bytes, *, scene: str, case_ids: tuple[str, ...], run_id: str):
        self.write_count += 1
        if self.malformed_teacher_receipt:
            return {"answer": "上传成功"}
        if self.fail_at == "teacher:upload":
            raise BackendFailure("SYNTHETIC_UPLOAD_FAILED")
        return {"accepted": True, "uploadId": f"upload-{run_id}", "scene": scene}

    def confirm_teacher_change(self, upload_id: str):
        self.write_count += 1
        if self.fail_at == "teacher:confirm":
            raise BackendFailure("SYNTHETIC_CONFIRM_FAILED")
        return {"confirmed": True, "changeId": f"change-{upload_id}"}

    def sync_teacher_change(self, change_id: str):
        self.write_count += 1
        if self.fail_at == "teacher:sync":
            raise BackendFailure("SYNTHETIC_SYNC_FAILED")
        self.temporary_cases.update(
            item for item in getattr(self, "_pending_case_ids", ())
        )
        self.knowledge_version = "knowledge-temporary"
        self._knowledge_content = b"synthetic temporary knowledge"
        return {
            "htmlUpdated": True,
            "knowledgeUpdated": True,
            "version": self.knowledge_version,
        }

    def read_case(self, case_id: str):
        if case_id not in self.temporary_cases:
            return None
        return {"caseId": case_id, "scene": "自动化测试"}

    def cleanup_teacher_cases(self, case_ids: tuple[str, ...], run_id: str):
        self.write_count += 1
        if self.fail_at == "cleanup:cases":
            raise BackendFailure("SYNTHETIC_CLEANUP_FAILED")
        deleted = [case_id for case_id in case_ids if case_id in self.temporary_cases]
        self.temporary_cases.difference_update(case_ids)
        return {"cleaned": True, "deletedIds": list(case_ids), "ownedRunId": run_id}

    def restore_knowledge(self, snapshot):
        self.write_count += 1
        if self.fail_at == "cleanup:knowledge":
            raise BackendFailure("SYNTHETIC_KNOWLEDGE_RESTORE_FAILED")
        self.knowledge_version = snapshot.version
        self._knowledge_content = b"synthetic baseline knowledge"
        actual = snapshot_knowledge(self.knowledge_version, self._knowledge_content,
                                    source="synthetic-content-snapshot")
        return {"restored": actual.digest == snapshot.digest,
                "version": actual.version, "digest": actual.digest}

    def verify_cases_absent(self, case_ids: tuple[str, ...]) -> bool:
        return not self.temporary_cases.intersection(case_ids)

    def restore_config(self, snapshot: ConfigSnapshot, *, owned_digest: str):
        self.restore_config_calls += 1
        self.write_count += 1
        if self.current_config_digest(self.target) != owned_digest:
            raise BackendFailure("EXTERNAL_CONCURRENT_CHANGE")
        self._full_config = _thaw(snapshot.normalized["full_config"])
        return {"restored": self.current_config_digest(self.target) == snapshot.digest}

    def remember_pending_cases(self, case_ids: tuple[str, ...]) -> None:
        self._pending_case_ids = case_ids
