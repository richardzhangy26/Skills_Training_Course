"""真实平台的只读 precheck/snapshot 适配；写协议未补证前恒阻断。"""

from __future__ import annotations

import json

from .backends import BackendFailure, Blocker, PrecheckResult, RegressionSnapshot
from .clients import require_role, select_unique_assistant
from .config_diff import snapshot_knowledge


class LiveRegressionBackend:
    environment = "live"

    def __init__(self, pds_client, teaching_client):
        self.pds = pds_client
        self.teaching = teaching_client
        self._bindings = None

    def precheck(self, target):
        user = self.teaching.current_user()
        require_role(user, "school_teacher")
        assistants = self.teaching.assistants(
            {"userNid": user["userNid"], "terminalType": "PC", "roleTypeForPC": "PC_TEACHER"}
        )
        select_unique_assistant(assistants, target.assistant_nid, target.assistant_name)
        relationship = self.teaching.resolve_relationship(
            {"agentNid": target.assistant_nid}, expert_nid=target.expert_nid
        )
        bindings = self.pds.knowledge_bindings(target.expert_nid)
        self._bindings = bindings
        blockers = []
        if not target.live_test_enabled:
            blockers.append(Blocker("LIVE_TEST_DISABLED"))
        if (
            target.isolated_test_assistant_nid is None
            or target.isolated_test_assistant_nid == target.assistant_nid
        ):
            blockers.append(Blocker("TEST_ISOLATION_UNAVAILABLE"))
        blockers.append(Blocker("STUDENT_TRANSPORT_UNVERIFIED"))
        blockers.extend(
            Blocker(code)
            for code in (
                "SAVE_ENDPOINT_UNVERIFIED",
                "SESSION_ENDPOINT_UNVERIFIED",
                "UPLOAD_ENDPOINT_UNVERIFIED",
                "SEND_ENDPOINT_UNVERIFIED",
                "TEACHER_RESTORE_UNVERIFIED",
                "KNOWLEDGE_CONTENT_SNAPSHOT_UNVERIFIED",
            )
        )
        if target.knowledge_base_nid is None and bindings:
            candidates = []
            for item in bindings:
                if not isinstance(item, dict):
                    raise BackendFailure("CONTRACT_CHANGED", "knowledge binding")
                candidates.append(
                    {
                        "name": item.get("knowledgeBaseName"),
                        "type": item.get("knowledgeType"),
                        "resourceCount": item.get("resourceCount"),
                    }
                )
            blockers.append(Blocker("KNOWLEDGE_TARGET_AMBIGUOUS", {"candidates": candidates}))
        return PrecheckResult(
            blockers=tuple(blockers),
            relationship_version=relationship["version"],
            assistant_nid=relationship["assistant_nid"],
        )

    def snapshot(self, target):
        config = self.pds.snapshot(target.expert_nid)
        bindings = self._bindings
        if bindings is None:
            bindings = self.pds.knowledge_bindings(target.expert_nid)
        metadata = json.dumps(bindings, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return RegressionSnapshot(
            config=config,
            knowledge=snapshot_knowledge(
                "UNVERIFIED_CONTENT", metadata, source="binding-metadata-only"
            ),
        )

    def _blocked(self, operation):
        raise BackendFailure("DEPENDENCY_UNVERIFIED", operation)

    publish = current_config_digest = run_student = upload_teacher_fixture = _blocked
    confirm_teacher_change = sync_teacher_change = read_case = cleanup_teacher_cases = _blocked
    restore_knowledge = verify_cases_absent = restore_config = _blocked
