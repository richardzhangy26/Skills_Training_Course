"""确认门控的专家发布与固定回归状态机。"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
import re
import secrets
from typing import Any

from .backends import (
    BackendFailure,
    Blocker,
    FixtureOwnership,
    PrecheckResult,
    RegressionBackend,
)
from .clients import PdsClient
from .config_diff import compare_configs, summarize_differences
from .contracts import ConfirmationBinding, KnowledgeSnapshot, TargetConfig
from .desired_config import DesiredConfigError, build_desired_config
from .fixtures import build_teacher_docx, student_scenarios, teacher_case_ids, validate_run_id
from .json_clone import clone_json
from .transport import ClientError


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
_SAFE_ERROR_CODE = re.compile(r"^[A-Z][A-Z0-9_]{0,63}$")


def _nonempty_string(value):
    return isinstance(value, str) and bool(value.strip())


def _mapping_receipt(value, operation):
    if not isinstance(value, Mapping):
        raise BackendFailure("STRUCTURED_RECEIPT_REQUIRED", operation)
    try:
        return clone_json(value, allow_tuple=False)
    except ValueError:
        raise BackendFailure("STRUCTURED_RECEIPT_REQUIRED", operation) from None


@dataclass
class ExecutionOwnership:
    fixture: FixtureOwnership
    knowledge: KnowledgeSnapshot


def evaluate_student_receipt(
    scenario,
    receipt,
    *,
    expected_assistant_nid: str,
    expected_conversation_id: str | None,
) -> str:
    """独立验证固定学生场景，不接受 backend 自报 passed 作为证据。"""

    common = (
        "scenario_id", "assistantId", "conversationId", "messageId",
        "planId", "traceId", "outcome", "answer",
    )
    if not isinstance(receipt, dict) or any(field not in receipt for field in common):
        raise BackendFailure("ASSERTION_FAILED", scenario.scenario_id)
    if (
        receipt["scenario_id"] != scenario.scenario_id
        or receipt["assistantId"] != expected_assistant_nid
        or not all(_nonempty_string(receipt[field]) for field in
                    ("conversationId", "messageId", "planId", "traceId", "answer"))
        or (expected_conversation_id is not None
            and receipt["conversationId"] != expected_conversation_id)
    ):
        raise BackendFailure("ASSERTION_FAILED", scenario.scenario_id)

    evidence = receipt.get("evidence", {})
    valid = receipt["outcome"] == scenario.expected_outcome
    if scenario.expected_case_ids is not None:
        valid = valid and receipt.get("caseIds") == list(scenario.expected_case_ids)
    if scenario.required_evidence or scenario.any_true_evidence or scenario.needs_reflection:
        valid = valid and isinstance(evidence, dict)
    if isinstance(evidence, dict):
        for requirement in scenario.required_evidence:
            value = evidence.get(requirement.field)
            if requirement.kind == "true":
                valid = valid and value is True
            elif requirement.kind == "false":
                valid = valid and value is False
            elif requirement.kind == "equals":
                valid = valid and value == requirement.value
            elif requirement.kind == "nonempty_list":
                valid = valid and isinstance(value, list) and bool(value)
            else:
                valid = False
        for fields in scenario.any_true_evidence:
            valid = valid and any(evidence.get(field) is True for field in fields)
        if scenario.needs_reflection:
            valid = valid and evidence.get("reflectionQuestion") is True
    if scenario.min_candidates:
        candidates = receipt.get("candidates")
        candidate_ids = (
            [item.get("caseId") for item in candidates]
            if isinstance(candidates, list)
            and all(isinstance(item, dict) for item in candidates)
            else []
        )
        valid = (
            valid
            and len(candidate_ids) >= scenario.min_candidates
            and len(set(candidate_ids)) == len(candidate_ids)
            and all(_nonempty_string(item) for item in candidate_ids)
        )
    if scenario.expected_write_performed is not None:
        valid = valid and receipt.get("writePerformed") is scenario.expected_write_performed
    if scenario.reason_code is not None:
        valid = valid and receipt.get("reasonCode") == scenario.reason_code
    valid = valid and all(field not in receipt for field in scenario.forbidden_fields)
    if not valid:
        raise BackendFailure("ASSERTION_FAILED", scenario.scenario_id)
    return receipt["conversationId"]


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

    @staticmethod
    def _block_prewrite_failure(payload, error):
        candidate = getattr(error, "code", "CONTRACT_CHANGED")
        code = candidate if isinstance(candidate, str) and _SAFE_ERROR_CODE.fullmatch(candidate) else "CONTRACT_CHANGED"
        for stage in reversed(payload["stages"]):
            if stage["status"] == "RUNNING":
                stage["status"] = "BLOCKED"
                stage["detail"] = code
                break
        if code not in {item.get("code") for item in payload["blockers"] if isinstance(item, dict)}:
            payload["blockers"].append({"code": code})
        payload.update(status="BLOCKED", code=code)

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
        target_case_ids = teacher_case_ids(payload["run_id"])
        case_query_unverified = any(
            blocker.code == "CASE_EXISTENCE_ENDPOINT_UNVERIFIED"
            for blocker in precheck.blockers
        )
        baseline_exact = None
        if not case_query_unverified:
            baseline_exact = self._existing_case_ids(target_case_ids)
        fixture_ownership = FixtureOwnership(
            payload["run_id"], target_case_ids, baseline_exact
        )
        if fixture_ownership.collision:
            precheck = PrecheckResult(
                blockers=(
                    *precheck.blockers,
                    Blocker(
                        "FIXTURE_ID_COLLISION",
                        {"caseIds": list(baseline_exact or ())},
                    ),
                ),
                relationship_version=precheck.relationship_version,
                assistant_nid=precheck.assistant_nid,
            )
        payload["fixture_ownership"] = fixture_ownership.as_dict()
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
                    "isolated_assistant_nid": precheck.assistant_nid,
                    "relationship_version": precheck.relationship_version,
                    "fixture_ownership": fixture_ownership.as_dict(),
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
            knowledge_digest=before.knowledge.digest,
            diff_digest=plan_digest,
            nonce=nonce,
        )
        payload["approval"] = {
            "snapshot_digest": binding.snapshot_digest,
            "expected_digest": binding.expected_digest,
            "knowledge_version": binding.knowledge_version,
            "knowledge_digest": binding.knowledge_digest,
            "diff_digest": binding.diff_digest,
            "nonce": binding.nonce,
        }
        self._stage(payload, "DIFF_READY", "PASSED" if diff.apply_allowed else "BLOCKED")
        self._checkpoint(payload)
        return (
            precheck,
            before,
            desired,
            desired_snapshot,
            diff,
            binding,
            fixture_ownership,
        )

    @staticmethod
    def _require(receipt, fields, *, code="STRUCTURED_RECEIPT_REQUIRED"):
        if not isinstance(receipt, dict) or any(field not in receipt for field in fields):
            raise BackendFailure(code)
        return receipt

    @staticmethod
    def _call_receipt(operation, method, *args, **kwargs):
        try:
            return _mapping_receipt(method(*args, **kwargs), operation)
        except BackendFailure:
            raise
        except Exception:
            raise BackendFailure("BACKEND_ERROR", operation) from None

    def _existing_case_ids(self, target_case_ids):
        listing = self._require(
            self._call_receipt(
                "existing_case_ids", self.backend.existing_case_ids, target_case_ids
            ),
            ("caseIds",),
        )
        case_ids = listing["caseIds"]
        if (
            not isinstance(case_ids, list)
            or any(not isinstance(case_id, str) or case_id not in target_case_ids
                   for case_id in case_ids)
            or len(case_ids) != len(set(case_ids))
        ):
            raise BackendFailure("CONTRACT_CHANGED", "existing_case_ids")
        return tuple(sorted(case_ids))

    def _cleanup_teacher(
        self,
        ownership,
        knowledge_snapshot,
    ):
        fixture = ownership.fixture
        current_exact = self._existing_case_ids(fixture.target_case_ids)
        try:
            created_owned = fixture.cleanup_case_ids(current_exact)
        except ValueError:
            raise BackendFailure(
                "EXTERNAL_CONCURRENT_CHANGE", "teacher_cases_not_cleaned"
            ) from None
        cleanup = self._require(
            self._call_receipt(
                "cleanup_teacher_cases",
                self.backend.cleanup_teacher_cases,
                created_owned,
                fixture.run_id,
            ),
            ("cleaned", "deletedIds", "ownedRunId"),
        )
        if cleanup["cleaned"] is not True or cleanup["ownedRunId"] != fixture.run_id:
            raise BackendFailure("CLEANUP_VERIFICATION_FAILED")
        deleted_ids = cleanup["deletedIds"]
        if (
            not isinstance(deleted_ids, list)
            or len(deleted_ids) != len(set(deleted_ids))
            or tuple(sorted(deleted_ids)) != created_owned
            or not fixture.is_restored(
                self._existing_case_ids(fixture.target_case_ids)
            )
            or not self.backend.verify_cases_absent(created_owned)
        ):
            raise BackendFailure("CLEANUP_VERIFICATION_FAILED", "teacher_cases_not_cleaned")
        current_knowledge = self.backend.current_knowledge_snapshot()
        if (
            current_knowledge.version != ownership.knowledge.version
            or current_knowledge.digest != ownership.knowledge.digest
        ):
            raise BackendFailure("EXTERNAL_CONCURRENT_CHANGE", "knowledge_not_restored")
        restored = self._require(
            self._call_receipt(
                "restore_knowledge",
                self.backend.restore_knowledge,
                knowledge_snapshot,
                owned_version=ownership.knowledge.version,
                owned_digest=ownership.knowledge.digest,
            ),
            ("restored", "knowledgeVersion", "knowledgeDigest"),
        )
        if (
            restored["restored"] is not True
            or restored["knowledgeVersion"] != knowledge_snapshot.version
            or restored["knowledgeDigest"] != knowledge_snapshot.digest
            or not self.backend.verify_cases_absent(created_owned)
        ):
            raise BackendFailure("CLEANUP_VERIFICATION_FAILED")
        try:
            restored_current = self.backend.current_knowledge_snapshot()
        except BackendFailure:
            raise
        except Exception:
            raise BackendFailure("BACKEND_ERROR", "current_knowledge_snapshot") from None
        if (
            restored_current.version != knowledge_snapshot.version
            or restored_current.digest != knowledge_snapshot.digest
            or not fixture.is_restored(
                self._existing_case_ids(fixture.target_case_ids)
            )
            or not self.backend.verify_cases_absent(created_owned)
        ):
            detail = (
                "knowledge_not_restored"
                if (restored_current.version != knowledge_snapshot.version
                    or restored_current.digest != knowledge_snapshot.digest)
                else "teacher_cases_not_cleaned"
            )
            raise BackendFailure("CLEANUP_VERIFICATION_FAILED", detail)

    def _execute_tests(self, payload, before, assistant_nid, ownership):
        fixture = ownership.fixture
        conversations = {}
        for scenario in student_scenarios():
            receipt = self._call_receipt(
                "run_student", self.backend.run_student, scenario, assistant_nid
            )
            conversation_id = evaluate_student_receipt(
                scenario,
                receipt,
                expected_assistant_nid=assistant_nid,
                expected_conversation_id=conversations.get(scenario.continuation_group),
            )
            conversations.setdefault(scenario.continuation_group, conversation_id)
            payload["assertions"].append(receipt)

        remember = getattr(self.backend, "remember_pending_cases", None)
        if remember is not None:
            remember(fixture.target_case_ids)
        upload = self._require(
            self._call_receipt(
                "upload_teacher_fixture",
                self.backend.upload_teacher_fixture,
                build_teacher_docx(fixture.run_id),
                scene="自动化测试",
                case_ids=fixture.target_case_ids,
                run_id=fixture.run_id,
            ),
            ("accepted", "uploadId", "scene"),
        )
        if upload["accepted"] is not True or upload["scene"] != "自动化测试":
            raise BackendFailure("STRUCTURED_RECEIPT_REQUIRED")
        confirmed = self._require(
            self._call_receipt(
                "confirm_teacher_change",
                self.backend.confirm_teacher_change,
                upload["uploadId"],
            ),
            ("confirmed", "changeId"),
        )
        if confirmed["confirmed"] is not True:
            raise BackendFailure("STRUCTURED_RECEIPT_REQUIRED")
        synced = self._require(
            self._call_receipt(
                "sync_teacher_change",
                self.backend.sync_teacher_change,
                confirmed["changeId"],
            ),
            ("htmlUpdated", "knowledgeUpdated", "knowledgeVersion", "knowledgeDigest"),
        )
        if synced["htmlUpdated"] is not True or synced["knowledgeUpdated"] is not True:
            raise BackendFailure("STRUCTURED_RECEIPT_REQUIRED")
        current_knowledge = self.backend.current_knowledge_snapshot()
        if (
            current_knowledge.version != synced["knowledgeVersion"]
            or current_knowledge.digest != synced["knowledgeDigest"]
        ):
            raise BackendFailure("READBACK_MISMATCH", "knowledge")
        ownership.knowledge = current_knowledge
        current_exact = self._existing_case_ids(fixture.target_case_ids)
        try:
            created_owned = fixture.created_from(current_exact)
        except ValueError:
            raise BackendFailure("READBACK_MISMATCH", "teacher case creation") from None
        if created_owned != tuple(sorted(fixture.target_case_ids)):
            raise BackendFailure("READBACK_MISMATCH", "teacher case creation")
        for case_id in fixture.target_case_ids:
            readback = self.backend.read_case(case_id)
            if not isinstance(readback, dict) or readback.get("caseId") != case_id:
                raise BackendFailure("READBACK_MISMATCH", case_id)
            payload["assertions"].append(
                {"scenario_id": "teacher-readback", "caseId": case_id, "passed": True}
            )
        return fixture.target_case_ids

    def _rollback(
        self,
        payload,
        before,
        owned_digest,
        failure,
        ownership,
    ):
        residual = []
        self._stage(payload, "CLEANUP", "RUNNING")
        try:
            self._cleanup_teacher(
                ownership,
                before.knowledge,
            )
        except BackendFailure as cleanup_failure:
            if cleanup_failure.detail in ("knowledge_not_restored", "teacher_cases_not_cleaned"):
                residual.append(cleanup_failure.detail)
            else:
                residual.append("teacher_or_knowledge_cleanup_unverified")
        except Exception:
            residual.append("teacher_or_knowledge_cleanup_unverified")
        try:
            current_config_digest = self.backend.current_config_digest(self.target)
        except Exception:
            residual.append("config_state_unknown")
            self._stage(payload, "CLEANUP", "FAILED")
            payload.update(
                status="ROLLBACK_FAILED",
                code="WRITE_STATE_UNKNOWN",
                residual_state=residual,
            )
            return self._finish(payload)
        if current_config_digest != owned_digest:
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
                self._call_receipt(
                    "restore_config",
                    self.backend.restore_config,
                    before.config,
                    owned_digest=owned_digest,
                ),
                ("restored",),
            )
            if receipt["restored"] is not True or self.backend.current_config_digest(self.target) != before.config.digest:
                raise BackendFailure("ROLLBACK_FAILED")
        except Exception:
            residual.append("config_not_restored")
        if residual:
            self._stage(payload, "CLEANUP", "FAILED")
            code = "EXTERNAL_CONCURRENT_CHANGE" if "knowledge_not_restored" in residual else "ROLLBACK_FAILED"
            payload.update(status="ROLLBACK_FAILED", code=code, residual_state=residual)
        else:
            self._stage(payload, "CLEANUP", "PASSED")
            payload.update(status="ROLLED_BACK", code=failure.code)
        return self._finish(payload)

    def run(self, run_id: str, *, mode: str, confirmation_token: str | None = None):
        validate_run_id(run_id)
        if mode not in ("dry-run", "apply"):
            raise ValueError("invalid_mode")
        with self.store.target_lock(self.target.target_id):
            payload = self._base(run_id)
            try:
                prior = self.store.read_checkpoint(run_id) if mode == "apply" else None
                (
                    precheck,
                    before,
                    desired,
                    desired_snapshot,
                    diff,
                    binding,
                    fixture_ownership,
                ) = self._prepare(payload, prior)
            except (
                BackendFailure,
                ClientError,
                DesiredConfigError,
                OSError,
                ValueError,
            ) as error:
                self._block_prewrite_failure(payload, error)
                return self._finish(payload)

            self._stage(payload, "AWAITING_CONFIRMATION", "BLOCKED")
            if precheck.blockers:
                code = (
                    "FIXTURE_ID_COLLISION"
                    if any(blocker.code == "FIXTURE_ID_COLLISION"
                           for blocker in precheck.blockers)
                    else "DEPENDENCY_UNVERIFIED"
                )
                payload.update(status="BLOCKED", code=code)
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
                    self._call_receipt(
                        "publish", self.backend.publish, self.target, desired, run_id
                    ),
                    ("published", "owned_digest", "assistantId"),
                )
                if publication["published"] is not True or publication["owned_digest"] != desired_snapshot.digest:
                    raise BackendFailure("READBACK_MISMATCH")
                if publication["assistantId"] != precheck.assistant_nid:
                    raise BackendFailure("READBACK_MISMATCH", "assistant identity")
                owned_digest = publication["owned_digest"]
                self._stage(payload, "PUBLISHING", "PASSED")
                self._stage(payload, "TESTING", "RUNNING")
                ownership = ExecutionOwnership(fixture_ownership, before.knowledge)
                try:
                    self._execute_tests(
                        payload,
                        before,
                        publication["assistantId"],
                        ownership,
                    )
                    self._stage(payload, "TESTING", "PASSED")
                    self._stage(payload, "CLEANUP", "RUNNING")
                    self._cleanup_teacher(
                        ownership,
                        before.knowledge,
                    )
                    self._stage(payload, "CLEANUP", "PASSED")
                    try:
                        final_config_digest = self.backend.current_config_digest(self.target)
                    except BackendFailure:
                        raise
                    except Exception:
                        raise BackendFailure("BACKEND_ERROR", "current_config_digest") from None
                    if final_config_digest != owned_digest:
                        self._stage(payload, "CLEANUP", "FAILED", "EXTERNAL_CONCURRENT_CHANGE")
                        payload.update(
                            status="ROLLBACK_FAILED",
                            code="EXTERNAL_CONCURRENT_CHANGE",
                            residual_state=["config_not_restored"],
                        )
                        return self._finish(payload)
                except Exception as error:
                    failure = error if isinstance(error, BackendFailure) else BackendFailure(
                        "BACKEND_ERROR", "post_publish"
                    )
                    self._stage(payload, "TESTING", "FAILED", failure.code)
                    return self._rollback(
                        payload, before, owned_digest, failure, ownership,
                    )
            except Exception as error:
                failure = error if isinstance(error, BackendFailure) else BackendFailure(
                    "BACKEND_ERROR", "publish_or_post_publish"
                )
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
                        failure,
                        ExecutionOwnership(fixture_ownership, before.knowledge),
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
