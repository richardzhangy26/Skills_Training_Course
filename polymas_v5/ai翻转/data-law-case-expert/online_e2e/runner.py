"""确认门控的专家发布与固定回归状态机。"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import secrets
from typing import Any

from .backends import BackendFailure, RegressionBackend
from .clients import PdsClient
from .config_diff import compare_configs, summarize_differences
from .contracts import ConfirmationBinding, TargetConfig
from .desired_config import DesiredConfigError, build_desired_config
from .fixtures import build_teacher_docx, student_scenarios, teacher_case_ids, validate_run_id


_STAGES = (
    "PRECHECK",
    "SNAPSHOT",
    "DIFF_READY",
    "AWAITING_CONFIRMATION",
    "PUBLISHING",
    "TESTING",
    "CLEANUP",
    "PASSED",
)


class ExpertE2ERunner:
    def __init__(self, target: TargetConfig, backend: RegressionBackend, store, report_writer):
        self.target = target
        self.backend = backend
        self.store = store
        self.report_writer = report_writer

    def _base(self, run_id: str) -> dict[str, Any]:
        return {
            "target_alias": self.target.target_id,
            "run_id": run_id,
            "environment": self.backend.environment,
            "status": "BLOCKED",
            "code": "IN_PROGRESS",
            "stages": [{"name": name, "status": "PENDING"} for name in _STAGES],
            "blockers": [],
            "assertions": [],
            "residual_state": [],
        }

    @staticmethod
    def _stage(payload, name, status, detail=None):
        for stage in payload["stages"]:
            if stage["name"] == name:
                stage["status"] = status
                if detail is not None:
                    stage["detail"] = detail
                return

    def _checkpoint(self, payload):
        path = self.store.write_checkpoint(payload["run_id"], payload)
        payload["checkpoint_path"] = str(path)

    def _finish(self, payload, *, token=None):
        for stage in payload["stages"]:
            if stage["status"] == "PENDING":
                stage["status"] = "SKIPPED"
        self._checkpoint(payload)
        paths = self.report_writer.write(payload)
        result = dict(payload)
        result["report_json"] = str(paths.json)
        result["report_markdown"] = str(paths.markdown)
        if token is not None:
            result["confirmation_token"] = token
        return result

    def _local_assets(self):
        paths = (
            self.target.agent_path,
            self.target.query_skill_path,
            self.target.maintenance_skill_path,
            self.target.html_path,
            self.target.knowledge_jsonl_path,
            self.target.manifest_path,
        )
        digest = hashlib.sha256()
        for path in paths:
            path = Path(path)
            digest.update(path.name.encode("utf-8"))
            digest.update(b"\0")
            digest.update(path.read_bytes())
            digest.update(b"\0")
        return digest.hexdigest(), Path(self.target.agent_path).read_text(encoding="utf-8")

    def _prepare(self, payload, prior):
        self._stage(payload, "PRECHECK", "RUNNING")
        precheck = self.backend.precheck(self.target)
        payload["blockers"] = [item.as_dict() for item in precheck.blockers]
        self._stage(payload, "PRECHECK", "BLOCKED" if precheck.blockers else "PASSED")
        self._checkpoint(payload)

        self._stage(payload, "SNAPSHOT", "RUNNING")
        before = self.backend.snapshot(self.target)
        local_digest, agent_content = self._local_assets()
        self._stage(payload, "SNAPSHOT", "PASSED")
        self._checkpoint(payload)

        self._stage(payload, "DIFF_READY", "RUNNING")
        full_config = before.config.normalized["full_config"]
        desired = build_desired_config(full_config, self.target, agent_content)
        desired_snapshot = PdsClient.snapshot_from_config(
            self.target.expert_nid,
            desired,
            list(before.config.normalized["knowledge_bindings"]),
        )
        diff = compare_configs(
            desired_snapshot.normalized,
            before.config.normalized,
            declared_skill_nids=self.target.online_skill_nids,
        )
        payload["differences"] = [
            {"path": item.path, "kind": item.kind, "expected": item.expected, "actual": item.actual}
            for item in diff.items
        ]
        plan_digest = hashlib.sha256(
            json.dumps(
                {
                    "local_assets": local_digest,
                    "diff": summarize_differences(diff.items),
                    "operations": ["publish", "student-suite", "teacher-suite", "cleanup"],
                    "assistant_nid": precheck.assistant_nid,
                },
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        nonce = None
        if prior:
            approval = prior.get("approval")
            if isinstance(approval, dict):
                nonce = approval.get("nonce")
        nonce = nonce if isinstance(nonce, str) and nonce else secrets.token_hex(16)
        binding = ConfirmationBinding(
            target_id=self.target.target_id,
            snapshot_digest=before.config.digest,
            expected_digest=desired_snapshot.digest,
            knowledge_version=before.knowledge.version,
            diff_digest=plan_digest,
            nonce=nonce,
        )
        payload["approval"] = {
            "snapshot_digest": binding.snapshot_digest,
            "expected_digest": binding.expected_digest,
            "knowledge_version": binding.knowledge_version,
            "diff_digest": binding.diff_digest,
            "nonce": binding.nonce,
        }
        self._stage(payload, "DIFF_READY", "PASSED" if diff.apply_allowed else "BLOCKED")
        self._checkpoint(payload)
        return precheck, before, desired, desired_snapshot, diff, binding

    @staticmethod
    def _require(receipt, fields, *, code="STRUCTURED_RECEIPT_REQUIRED"):
        if not isinstance(receipt, dict) or any(field not in receipt for field in fields):
            raise BackendFailure(code)
        return receipt

    def _cleanup_teacher(self, case_ids, run_id, knowledge_snapshot):
        cleanup = self._require(
            self.backend.cleanup_teacher_cases(case_ids, run_id),
            ("cleaned", "deletedIds", "ownedRunId"),
        )
        if cleanup["cleaned"] is not True or cleanup["ownedRunId"] != run_id:
            raise BackendFailure("CLEANUP_VERIFICATION_FAILED")
        if set(cleanup["deletedIds"]) != set(case_ids):
            raise BackendFailure("CLEANUP_VERIFICATION_FAILED")
        restored = self._require(
            self.backend.restore_knowledge(knowledge_snapshot),
            ("restored", "version", "digest"),
        )
        if (
            restored["restored"] is not True
            or restored["version"] != knowledge_snapshot.version
            or restored["digest"] != knowledge_snapshot.digest
            or not self.backend.verify_cases_absent(case_ids)
        ):
            raise BackendFailure("CLEANUP_VERIFICATION_FAILED")

    def _execute_tests(self, payload, before, run_id, assistant_nid):
        for scenario in student_scenarios():
            receipt = self._require(
                dict(self.backend.run_student(scenario, assistant_nid)),
                ("passed", "scenario_id", "assistantId", "conversationId", "messageId", "planId", "traceId"),
            )
            if receipt["passed"] is not True or receipt["scenario_id"] != scenario.scenario_id:
                raise BackendFailure("ASSERTION_FAILED", scenario.scenario_id)
            payload["assertions"].append(receipt)

        case_ids = teacher_case_ids(run_id)
        remember = getattr(self.backend, "remember_pending_cases", None)
        if remember is not None:
            remember(case_ids)
        upload = self._require(
            dict(self.backend.upload_teacher_fixture(
                build_teacher_docx(run_id), scene="自动化测试", case_ids=case_ids, run_id=run_id
            )),
            ("accepted", "uploadId", "scene"),
        )
        if upload["accepted"] is not True or upload["scene"] != "自动化测试":
            raise BackendFailure("STRUCTURED_RECEIPT_REQUIRED")
        confirmed = self._require(
            dict(self.backend.confirm_teacher_change(upload["uploadId"])),
            ("confirmed", "changeId"),
        )
        if confirmed["confirmed"] is not True:
            raise BackendFailure("STRUCTURED_RECEIPT_REQUIRED")
        synced = self._require(
            dict(self.backend.sync_teacher_change(confirmed["changeId"])),
            ("htmlUpdated", "knowledgeUpdated", "version"),
        )
        if synced["htmlUpdated"] is not True or synced["knowledgeUpdated"] is not True:
            raise BackendFailure("STRUCTURED_RECEIPT_REQUIRED")
        for case_id in case_ids:
            readback = self.backend.read_case(case_id)
            if not isinstance(readback, dict) or readback.get("caseId") != case_id:
                raise BackendFailure("READBACK_MISMATCH", case_id)
            payload["assertions"].append(
                {"scenario_id": "teacher-readback", "caseId": case_id, "passed": True}
            )
        return case_ids

    def _rollback(self, payload, before, owned_digest, case_ids, run_id, failure):
        residual = []
        self._stage(payload, "CLEANUP", "RUNNING")
        try:
            self._cleanup_teacher(case_ids, run_id, before.knowledge)
        except Exception:
            residual.append("teacher_or_knowledge_cleanup_unverified")
        if self.backend.current_config_digest(self.target) != owned_digest:
            residual.append("config_not_restored")
            self._stage(payload, "CLEANUP", "FAILED")
            payload.update(
                status="ROLLBACK_FAILED",
                code="EXTERNAL_CONCURRENT_CHANGE",
                residual_state=residual,
            )
            return self._finish(payload)
        try:
            receipt = self._require(
                dict(self.backend.restore_config(before.config, owned_digest=owned_digest)),
                ("restored",),
            )
            if receipt["restored"] is not True or self.backend.current_config_digest(self.target) != before.config.digest:
                raise BackendFailure("ROLLBACK_FAILED")
        except Exception:
            residual.append("config_not_restored")
        if residual:
            self._stage(payload, "CLEANUP", "FAILED")
            payload.update(status="ROLLBACK_FAILED", code="ROLLBACK_FAILED", residual_state=residual)
        else:
            self._stage(payload, "CLEANUP", "PASSED")
            payload.update(status="ROLLED_BACK", code=failure.code)
        return self._finish(payload)

    def run(self, run_id: str, *, mode: str, confirmation_token: str | None = None):
        validate_run_id(run_id)
        if mode not in ("dry-run", "apply"):
            raise ValueError("invalid_mode")
        with self.store.target_lock(self.target.target_id):
            prior = self.store.read_checkpoint(run_id) if mode == "apply" else None
            payload = self._base(run_id)
            try:
                precheck, before, desired, desired_snapshot, diff, binding = self._prepare(payload, prior)
            except (BackendFailure, DesiredConfigError, OSError, ValueError) as error:
                payload.update(status="BLOCKED", code=getattr(error, "code", "CONTRACT_CHANGED"))
                return self._finish(payload)

            self._stage(payload, "AWAITING_CONFIRMATION", "BLOCKED")
            if precheck.blockers:
                payload.update(status="BLOCKED", code="DEPENDENCY_UNVERIFIED")
                return self._finish(payload)
            if not diff.apply_allowed:
                payload.update(status="BLOCKED", code="CONTRACT_CHANGED")
                return self._finish(payload)
            if mode == "dry-run":
                token = self.store.confirmations.issue(binding)
                payload.update(status="BLOCKED", code="AWAITING_CONFIRMATION")
                return self._finish(payload, token=token)

            if not confirmation_token or not self.store.confirmations.consume(confirmation_token, binding):
                payload.update(status="BLOCKED", code="CONFIRMATION_INVALID")
                return self._finish(payload)
            self._stage(payload, "AWAITING_CONFIRMATION", "PASSED")
            self._stage(payload, "PUBLISHING", "RUNNING")
            try:
                publication = self._require(
                    dict(self.backend.publish(self.target, desired, run_id)),
                    ("published", "owned_digest", "assistantId"),
                )
                if publication["published"] is not True or publication["owned_digest"] != desired_snapshot.digest:
                    raise BackendFailure("READBACK_MISMATCH")
                owned_digest = publication["owned_digest"]
                self._stage(payload, "PUBLISHING", "PASSED")
                self._stage(payload, "TESTING", "RUNNING")
                case_ids = teacher_case_ids(run_id)
                try:
                    case_ids = self._execute_tests(
                        payload, before, run_id, publication["assistantId"]
                    )
                    self._stage(payload, "TESTING", "PASSED")
                    self._stage(payload, "CLEANUP", "RUNNING")
                    self._cleanup_teacher(case_ids, run_id, before.knowledge)
                    self._stage(payload, "CLEANUP", "PASSED")
                except BackendFailure as failure:
                    self._stage(payload, "TESTING", "FAILED", failure.code)
                    return self._rollback(payload, before, owned_digest, case_ids, run_id, failure)
            except BackendFailure as failure:
                self._stage(payload, "PUBLISHING", "FAILED", failure.code)
                try:
                    current_digest = self.backend.current_config_digest(self.target)
                except Exception:
                    payload.update(
                        status="ROLLBACK_FAILED",
                        code="WRITE_STATE_UNKNOWN",
                        residual_state=["config_state_unknown"],
                    )
                    return self._finish(payload)
                if current_digest == desired_snapshot.digest:
                    return self._rollback(
                        payload,
                        before,
                        desired_snapshot.digest,
                        teacher_case_ids(run_id),
                        run_id,
                        failure,
                    )
                if current_digest != before.config.digest:
                    payload.update(
                        status="ROLLBACK_FAILED",
                        code="EXTERNAL_CONCURRENT_CHANGE",
                        residual_state=["config_not_restored"],
                    )
                    return self._finish(payload)
                payload.update(status="BLOCKED", code=failure.code)
                return self._finish(payload)

            self._stage(payload, "PASSED", "PASSED")
            payload.update(status="PASSED", code="PASSED")
            return self._finish(payload)
