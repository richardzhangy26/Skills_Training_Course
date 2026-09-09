from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class OnlineE2ERunnerTests(unittest.TestCase):
    def setUp(self):
        from online_e2e.contracts import load_target_config

        self.target = load_target_config("data-law-case-expert", root=ROOT)

    def _runner(self, root, backend, target=None):
        from online_e2e.reports import ReportWriter
        from online_e2e.run_store import DurableRunStore
        from online_e2e.runner import ExpertE2ERunner

        return ExpertE2ERunner(
            target or self.target,
            backend,
            DurableRunStore(Path(root) / "state"),
            ReportWriter(Path(root) / "reports"),
        )

    def test_dry_run_completes_read_only_plan_and_returns_token_only_to_stdout_payload(self):
        from online_e2e.synthetic_backend import SyntheticRegressionBackend

        with tempfile.TemporaryDirectory() as temporary:
            backend = SyntheticRegressionBackend(self.target)
            result = self._runner(temporary, backend).run("run_001", mode="dry-run")

            self.assertEqual(result["status"], "BLOCKED")
            self.assertEqual(result["code"], "AWAITING_CONFIRMATION")
            self.assertIn("confirmation_token", result)
            self.assertEqual(backend.write_count, 0)
            self.assertEqual(
                [stage["name"] for stage in result["stages"]],
                [
                    "PRECHECK",
                    "SNAPSHOT",
                    "DIFF_READY",
                    "AWAITING_CONFIRMATION",
                    "PUBLISHING",
                    "TESTING",
                    "CLEANUP",
                    "PASSED",
                ],
            )
            checkpoint = Path(result["checkpoint_path"]).read_text(encoding="utf-8")
            report = Path(result["report_json"]).read_text(encoding="utf-8")
            self.assertNotIn(result["confirmation_token"], checkpoint + report)
            self.assertNotIn("confirmation_token", checkpoint + report)

    def test_synthetic_apply_runs_full_suite_cleans_fixtures_and_keeps_published_config(self):
        from online_e2e.synthetic_backend import SyntheticRegressionBackend

        with tempfile.TemporaryDirectory() as temporary:
            backend = SyntheticRegressionBackend(self.target)
            runner = self._runner(temporary, backend)
            dry = runner.run("run_002", mode="dry-run")
            applied = runner.run(
                "run_002",
                mode="apply",
                confirmation_token=dry["confirmation_token"],
            )

            self.assertEqual(applied["status"], "PASSED")
            self.assertEqual(len(applied["assertions"]), 8)
            self.assertEqual(len(backend.student_calls), 6)
            self.assertEqual(backend.temporary_cases, set())
            self.assertEqual(backend.knowledge_version, "knowledge-v1")
            self.assertIn("本专家", backend.agent_content)
            self.assertEqual(backend.restore_config_calls, 0)
            self.assertGreaterEqual(backend.knowledge_cas_checks, 2)
            rendered = json.dumps(applied, ensure_ascii=False)
            for identifier in (
                "synthetic-isolated-assistant",
                "synthetic-conversation",
                "synthetic-message",
                "synthetic-plan",
                "synthetic-trace",
            ):
                self.assertIn(identifier, rendered)

    def test_apply_recomputes_local_digest_and_rejects_changed_assets_before_write(self):
        from online_e2e.synthetic_backend import SyntheticRegressionBackend

        with tempfile.TemporaryDirectory() as temporary:
            agent_path = Path(temporary) / "Agent.md"
            agent_path.write_text("first", encoding="utf-8")
            target = replace(self.target, agent_path=agent_path)
            backend = SyntheticRegressionBackend(target)
            runner = self._runner(temporary, backend, target)
            dry = runner.run("run_003", mode="dry-run")
            agent_path.write_text("changed", encoding="utf-8")
            applied = runner.run(
                "run_003", mode="apply", confirmation_token=dry["confirmation_token"]
            )

            self.assertEqual(applied["status"], "BLOCKED")
            self.assertEqual(applied["code"], "CONFIRMATION_INVALID")
            self.assertEqual(backend.write_count, 0)

    def test_apply_rejects_same_knowledge_version_with_changed_content_digest(self):
        from online_e2e.synthetic_backend import SyntheticRegressionBackend

        with tempfile.TemporaryDirectory() as temporary:
            backend = SyntheticRegressionBackend(self.target)
            runner = self._runner(temporary, backend)
            dry = runner.run("run_knowledge_digest", mode="dry-run")
            backend._knowledge_content = b"changed content under same knowledge version"
            result = runner.run(
                "run_knowledge_digest",
                mode="apply",
                confirmation_token=dry["confirmation_token"],
            )
            self.assertEqual(result["status"], "BLOCKED")
            self.assertEqual(result["code"], "CONFIRMATION_INVALID")
            self.assertEqual(backend.write_count, 0)

    def test_apply_rejects_changed_isolated_assistant_or_relationship_version_before_write(self):
        from online_e2e.synthetic_backend import SyntheticRegressionBackend

        for field, value in (
            ("precheck_assistant_id", "different-isolated-assistant"),
            ("relationship_version", "synthetic-v2"),
        ):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as temporary:
                backend = SyntheticRegressionBackend(self.target)
                runner = self._runner(temporary, backend)
                dry = runner.run(f"run_changed_{field}", mode="dry-run")
                setattr(backend, field, value)
                result = runner.run(
                    f"run_changed_{field}",
                    mode="apply",
                    confirmation_token=dry["confirmation_token"],
                )
                self.assertEqual(result["status"], "BLOCKED")
                self.assertEqual(result["code"], "CONFIRMATION_INVALID")
                self.assertEqual(backend.write_count, 0)

    def test_precheck_blockers_still_allow_snapshot_and_diff_but_never_issue_token_or_write(self):
        from online_e2e.backends import Blocker
        from online_e2e.synthetic_backend import SyntheticRegressionBackend

        with tempfile.TemporaryDirectory() as temporary:
            backend = SyntheticRegressionBackend(
                self.target,
                blockers=(Blocker("TEST_ISOLATION_UNAVAILABLE", "no test assistant"),),
            )
            runner = self._runner(temporary, backend)
            dry = runner.run("run_004", mode="dry-run")
            applied = runner.run("run_004", mode="apply", confirmation_token="invalid")

            self.assertEqual(dry["status"], "BLOCKED")
            self.assertNotIn("confirmation_token", dry)
            self.assertEqual(dry["stages"][1]["status"], "PASSED")
            self.assertEqual(dry["stages"][2]["status"], "PASSED")
            self.assertEqual(applied["code"], "DEPENDENCY_UNVERIFIED")
            self.assertEqual(backend.write_count, 0)

    def test_prewrite_snapshot_and_diff_errors_block_running_stage_and_add_safe_blocker(self):
        from online_e2e.desired_config import DesiredConfigError
        from online_e2e.synthetic_backend import SyntheticRegressionBackend
        from online_e2e.transport import ClientError

        class SnapshotFailure(SyntheticRegressionBackend):
            def snapshot(self, target):
                raise ClientError(
                    "SNAPSHOT_UNAVAILABLE", "snapshot", "private snapshot detail"
                )

        cases = (
            (SnapshotFailure(self.target), None, "SNAPSHOT", "SNAPSHOT_UNAVAILABLE"),
            (
                SyntheticRegressionBackend(self.target),
                DesiredConfigError("private desired diff detail"),
                "DIFF_READY",
                "CONTRACT_CHANGED",
            ),
        )
        for backend, desired_error, stage_name, expected_code in cases:
            with self.subTest(stage=stage_name), tempfile.TemporaryDirectory() as temporary:
                runner = self._runner(temporary, backend)
                if desired_error is None:
                    result = runner.run(f"run_error_{stage_name.lower()}", mode="dry-run")
                else:
                    with patch(
                        "online_e2e.runner.build_desired_config",
                        side_effect=desired_error,
                    ):
                        result = runner.run(f"run_error_{stage_name.lower()}", mode="dry-run")

                stages = {stage["name"]: stage for stage in result["stages"]}
                self.assertEqual(result["status"], "BLOCKED")
                self.assertEqual(result["code"], expected_code)
                self.assertEqual(stages[stage_name]["status"], "BLOCKED")
                self.assertEqual(stages[stage_name]["detail"], expected_code)
                self.assertNotIn("RUNNING", {stage["status"] for stage in result["stages"]})
                self.assertIn(expected_code, {item["code"] for item in result["blockers"]})
                report = Path(result["report_json"]).read_text(encoding="utf-8")
                self.assertNotIn("private", report)

    def test_dry_run_blocks_existing_exact_fixture_id_without_token_or_write(self):
        from online_e2e.fixtures import teacher_case_ids
        from online_e2e.synthetic_backend import SyntheticRegressionBackend

        with tempfile.TemporaryDirectory() as temporary:
            backend = SyntheticRegressionBackend(self.target)
            backend.temporary_cases.add(teacher_case_ids("run_collision")[0])
            result = self._runner(temporary, backend).run(
                "run_collision", mode="dry-run"
            )
            self.assertEqual(result["status"], "BLOCKED")
            self.assertEqual(result["code"], "FIXTURE_ID_COLLISION")
            self.assertNotIn("confirmation_token", result)
            self.assertIn(
                "FIXTURE_ID_COLLISION", {item["code"] for item in result["blockers"]}
            )
            self.assertEqual(backend.write_count, 0)

    def test_exact_fixture_id_appearing_between_dry_run_and_apply_blocks_zero_write(self):
        from online_e2e.fixtures import teacher_case_ids
        from online_e2e.synthetic_backend import SyntheticRegressionBackend

        with tempfile.TemporaryDirectory() as temporary:
            backend = SyntheticRegressionBackend(self.target)
            runner = self._runner(temporary, backend)
            dry = runner.run("run_late_collision", mode="dry-run")
            backend.temporary_cases.add(teacher_case_ids("run_late_collision")[1])
            result = runner.run(
                "run_late_collision", mode="apply",
                confirmation_token=dry["confirmation_token"],
            )
            self.assertEqual(result["status"], "BLOCKED")
            self.assertEqual(result["code"], "FIXTURE_ID_COLLISION")
            self.assertEqual(backend.write_count, 0)

    def test_test_failure_rolls_back_owned_config_and_knowledge(self):
        from online_e2e.synthetic_backend import SyntheticRegressionBackend

        with tempfile.TemporaryDirectory() as temporary:
            backend = SyntheticRegressionBackend(self.target, fail_at="student:follow-up-question")
            original_content = backend.agent_content
            runner = self._runner(temporary, backend)
            dry = runner.run("run_005", mode="dry-run")
            result = runner.run(
                "run_005", mode="apply", confirmation_token=dry["confirmation_token"]
            )

            self.assertEqual(result["status"], "ROLLED_BACK")
            self.assertEqual(backend.agent_content, original_content)
            self.assertEqual(backend.knowledge_version, "knowledge-v1")
            self.assertEqual(backend.temporary_cases, set())
            self.assertEqual(backend.restore_config_calls, 1)
            self.assertGreaterEqual(backend.knowledge_cas_checks, 1)

    def test_external_change_after_publish_stops_rollback_and_reports_residual_state(self):
        from online_e2e.synthetic_backend import SyntheticRegressionBackend

        with tempfile.TemporaryDirectory() as temporary:
            backend = SyntheticRegressionBackend(
                self.target,
                fail_at="student:follow-up-question",
                external_change_before_rollback=True,
            )
            runner = self._runner(temporary, backend)
            dry = runner.run("run_006", mode="dry-run")
            result = runner.run(
                "run_006", mode="apply", confirmation_token=dry["confirmation_token"]
            )

            self.assertEqual(result["status"], "ROLLBACK_FAILED")
            self.assertEqual(result["code"], "EXTERNAL_CONCURRENT_CHANGE")
            self.assertIn("config_not_restored", result["residual_state"])
            self.assertEqual(backend.restore_config_calls, 0)

    def test_teacher_natural_language_success_without_structured_receipt_rolls_back(self):
        from online_e2e.synthetic_backend import SyntheticRegressionBackend

        with tempfile.TemporaryDirectory() as temporary:
            backend = SyntheticRegressionBackend(self.target, malformed_teacher_receipt=True)
            runner = self._runner(temporary, backend)
            dry = runner.run("run_007", mode="dry-run")
            result = runner.run(
                "run_007", mode="apply", confirmation_token=dry["confirmation_token"]
            )

            self.assertEqual(result["status"], "ROLLED_BACK")
            self.assertEqual(result["code"], "STRUCTURED_RECEIPT_REQUIRED")
            self.assertEqual(backend.restore_config_calls, 1)

    def test_publish_changed_state_with_malformed_receipt_is_detected_and_rolled_back(self):
        from online_e2e.synthetic_backend import SyntheticRegressionBackend

        with tempfile.TemporaryDirectory() as temporary:
            backend = SyntheticRegressionBackend(self.target, malformed_publish_receipt=True)
            original_content = backend.agent_content
            runner = self._runner(temporary, backend)
            dry = runner.run("run_008", mode="dry-run")
            result = runner.run(
                "run_008", mode="apply", confirmation_token=dry["confirmation_token"]
            )

            self.assertEqual(result["status"], "ROLLED_BACK")
            self.assertEqual(result["code"], "STRUCTURED_RECEIPT_REQUIRED")
            self.assertEqual(backend.agent_content, original_content)
            self.assertEqual(backend.restore_config_calls, 1)

    def test_publish_that_lands_then_returns_none_is_safely_read_back_and_rolled_back(self):
        from online_e2e.synthetic_backend import SyntheticRegressionBackend

        class NonePublishBackend(SyntheticRegressionBackend):
            def publish(self, target, desired, run_id):
                super().publish(target, desired, run_id)
                return None

        with tempfile.TemporaryDirectory() as temporary:
            backend = NonePublishBackend(self.target)
            original_content = backend.agent_content
            runner = self._runner(temporary, backend)
            dry = runner.run("run_none_publish", mode="dry-run")
            result = runner.run(
                "run_none_publish", mode="apply",
                confirmation_token=dry["confirmation_token"],
            )
            self.assertEqual(result["status"], "ROLLED_BACK")
            self.assertEqual(result["code"], "STRUCTURED_RECEIPT_REQUIRED")
            self.assertEqual(backend.agent_content, original_content)

    def test_all_post_publish_backend_receipt_failures_restore_config_or_report_residual(self):
        from online_e2e.synthetic_backend import SyntheticRegressionBackend

        class FaultBackend(SyntheticRegressionBackend):
            def __init__(self, *args, stage, raises, **kwargs):
                super().__init__(*args, **kwargs)
                self.stage = stage
                self.raises = raises

            def _fault(self):
                if self.raises:
                    raise TypeError("private backend detail must not leak")
                return None

            def run_student(self, scenario, assistant_nid):
                if self.stage == "student" and scenario.scenario_id == "exact-statute":
                    return self._fault()
                return super().run_student(scenario, assistant_nid)

            def upload_teacher_fixture(self, *args, **kwargs):
                if self.stage == "upload":
                    return self._fault()
                return super().upload_teacher_fixture(*args, **kwargs)

            def sync_teacher_change(self, *args, **kwargs):
                if self.stage == "sync":
                    return self._fault()
                return super().sync_teacher_change(*args, **kwargs)

            def cleanup_teacher_cases(self, *args, **kwargs):
                if self.stage == "cleanup":
                    return self._fault()
                return super().cleanup_teacher_cases(*args, **kwargs)

        for stage, raises in (("student", False), ("upload", True),
                              ("sync", False), ("cleanup", True)):
            with self.subTest(stage=stage), tempfile.TemporaryDirectory() as temporary:
                backend = FaultBackend(self.target, stage=stage, raises=raises)
                original_content = backend.agent_content
                runner = self._runner(temporary, backend)
                dry = runner.run(f"run_fault_{stage}", mode="dry-run")
                result = runner.run(
                    f"run_fault_{stage}", mode="apply",
                    confirmation_token=dry["confirmation_token"],
                )
                self.assertIn(result["status"], ("ROLLED_BACK", "ROLLBACK_FAILED"))
                self.assertNotIn("private backend detail", json.dumps(result))
                self.assertEqual(backend.agent_content, original_content)

    def test_restore_knowledge_receipt_requires_independent_current_snapshot_readback(self):
        from online_e2e.synthetic_backend import SyntheticRegressionBackend

        class StaleRestoreBackend(SyntheticRegressionBackend):
            def restore_knowledge(self, snapshot, *, owned_version, owned_digest):
                self.write_count += 1
                return {
                    "restored": True,
                    "knowledgeVersion": snapshot.version,
                    "knowledgeDigest": snapshot.digest,
                }

        with tempfile.TemporaryDirectory() as temporary:
            backend = StaleRestoreBackend(self.target)
            runner = self._runner(temporary, backend)
            dry = runner.run("run_stale_restore", mode="dry-run")
            result = runner.run(
                "run_stale_restore", mode="apply",
                confirmation_token=dry["confirmation_token"],
            )
            self.assertEqual(result["status"], "ROLLBACK_FAILED")
            self.assertIn("knowledge_not_restored", result["residual_state"])

    def test_external_config_change_during_cleanup_cannot_report_passed_or_be_overwritten(self):
        from online_e2e.synthetic_backend import SyntheticRegressionBackend

        class ExternalConfigDuringCleanup(SyntheticRegressionBackend):
            def restore_knowledge(self, snapshot, *, owned_version, owned_digest):
                receipt = super().restore_knowledge(
                    snapshot, owned_version=owned_version, owned_digest=owned_digest
                )
                self._full_config["expertMd"]["customContent"] = "external config after cleanup"
                return receipt

        with tempfile.TemporaryDirectory() as temporary:
            backend = ExternalConfigDuringCleanup(self.target)
            runner = self._runner(temporary, backend)
            dry = runner.run("run_external_config_cleanup", mode="dry-run")
            result = runner.run(
                "run_external_config_cleanup", mode="apply",
                confirmation_token=dry["confirmation_token"],
            )
            self.assertEqual(result["status"], "ROLLBACK_FAILED")
            self.assertEqual(result["code"], "EXTERNAL_CONCURRENT_CHANGE")
            self.assertIn("config_not_restored", result["residual_state"])
            self.assertEqual(backend.agent_content, "external config after cleanup")
            self.assertEqual(backend.restore_config_calls, 0)

    def test_external_knowledge_change_stops_restore_but_config_cas_still_rolls_back(self):
        from online_e2e.synthetic_backend import SyntheticRegressionBackend

        with tempfile.TemporaryDirectory() as temporary:
            backend = SyntheticRegressionBackend(
                self.target, external_knowledge_change_before_cleanup=True
            )
            original_content = backend.agent_content
            runner = self._runner(temporary, backend)
            dry = runner.run("run_knowledge_cas", mode="dry-run")
            result = runner.run(
                "run_knowledge_cas",
                mode="apply",
                confirmation_token=dry["confirmation_token"],
            )

            self.assertEqual(result["status"], "ROLLBACK_FAILED")
            self.assertEqual(result["code"], "EXTERNAL_CONCURRENT_CHANGE")
            self.assertIn("knowledge_not_restored", result["residual_state"])
            self.assertEqual(backend.agent_content, original_content)
            self.assertEqual(backend.knowledge_version, "external-knowledge-version")
            self.assertEqual(backend.restore_config_calls, 1)

    def test_runner_evaluates_student_evidence_instead_of_trusting_passed_flag(self):
        from online_e2e.synthetic_backend import SyntheticRegressionBackend

        with tempfile.TemporaryDirectory() as temporary:
            backend = SyntheticRegressionBackend(
                self.target, corrupt_student="ambiguous-candidates"
            )
            runner = self._runner(temporary, backend)
            dry = runner.run("run_corrupt_student", mode="dry-run")
            result = runner.run(
                "run_corrupt_student",
                mode="apply",
                confirmation_token=dry["confirmation_token"],
            )

            self.assertEqual(result["status"], "ROLLED_BACK")
            self.assertEqual(result["code"], "ASSERTION_FAILED")
            self.assertEqual(backend.restore_config_calls, 1)

    def test_publication_assistant_must_equal_prechecked_isolated_assistant(self):
        from online_e2e.synthetic_backend import SyntheticRegressionBackend

        with tempfile.TemporaryDirectory() as temporary:
            backend = SyntheticRegressionBackend(
                self.target, publish_assistant_id="wrong-assistant"
            )
            runner = self._runner(temporary, backend)
            dry = runner.run("run_wrong_assistant", mode="dry-run")
            result = runner.run(
                "run_wrong_assistant",
                mode="apply",
                confirmation_token=dry["confirmation_token"],
            )

            self.assertEqual(result["status"], "ROLLED_BACK")
            self.assertEqual(result["code"], "READBACK_MISMATCH")
            self.assertEqual(backend.student_calls, [])

    def test_tampered_teacher_docx_is_rejected_and_published_config_is_rolled_back(self):
        from online_e2e.synthetic_backend import SyntheticRegressionBackend

        with tempfile.TemporaryDirectory() as temporary:
            backend = SyntheticRegressionBackend(self.target)
            runner = self._runner(temporary, backend)
            dry = runner.run("run_bad_docx", mode="dry-run")
            with patch("online_e2e.runner.build_teacher_docx", return_value=b"not-a-docx"):
                result = runner.run(
                    "run_bad_docx",
                    mode="apply",
                    confirmation_token=dry["confirmation_token"],
                )

            self.assertEqual(result["status"], "ROLLED_BACK")
            self.assertEqual(result["code"], "FIXTURE_INVALID")
            self.assertEqual(backend.restore_config_calls, 1)

    def test_fake_cleanup_receipt_is_rejected_when_cases_remain_retrievable(self):
        from online_e2e.synthetic_backend import SyntheticRegressionBackend

        with tempfile.TemporaryDirectory() as temporary:
            backend = SyntheticRegressionBackend(self.target, fake_cleanup_receipt=True)
            runner = self._runner(temporary, backend)
            dry = runner.run("run_fake_cleanup", mode="dry-run")
            result = runner.run(
                "run_fake_cleanup",
                mode="apply",
                confirmation_token=dry["confirmation_token"],
            )

            self.assertEqual(result["status"], "ROLLBACK_FAILED")
            self.assertIn("teacher_cases_not_cleaned", result["residual_state"])

    def test_partial_teacher_sync_discovers_and_cleans_exact_created_subset(self):
        from online_e2e.synthetic_backend import SyntheticRegressionBackend

        with tempfile.TemporaryDirectory() as temporary:
            backend = SyntheticRegressionBackend(self.target, partial_sync_cases=True)
            runner = self._runner(temporary, backend)
            dry = runner.run("run_partial_sync", mode="dry-run")
            result = runner.run(
                "run_partial_sync", mode="apply",
                confirmation_token=dry["confirmation_token"],
            )
            self.assertEqual(result["status"], "ROLLED_BACK")
            self.assertEqual(result["code"], "READBACK_MISMATCH")
            self.assertEqual(backend.temporary_cases, set())
            self.assertEqual(backend.last_cleanup_requested, ("AUTO-RUN_PARTIAL_SYNC-01",))

    def test_same_prefix_non_target_case_is_never_cleaned_and_successfully_survives(self):
        from online_e2e.synthetic_backend import SyntheticRegressionBackend

        with tempfile.TemporaryDirectory() as temporary:
            backend = SyntheticRegressionBackend(self.target)
            extra = "AUTO-RUN_KEEP_EXTRA-99"
            backend.temporary_cases.add(extra)
            runner = self._runner(temporary, backend)
            dry = runner.run("run_keep_extra", mode="dry-run")
            result = runner.run(
                "run_keep_extra", mode="apply",
                confirmation_token=dry["confirmation_token"],
            )
            self.assertEqual(result["status"], "PASSED")
            self.assertEqual(backend.temporary_cases, {extra})
            self.assertEqual(
                backend.last_cleanup_requested,
                ("AUTO-RUN_KEEP_EXTRA-01", "AUTO-RUN_KEEP_EXTRA-02"),
            )

    def test_cleanup_deleted_ids_must_exactly_equal_owned_set(self):
        from online_e2e.synthetic_backend import SyntheticRegressionBackend

        class WrongDeletedIds(SyntheticRegressionBackend):
            def __init__(self, *args, mode, **kwargs):
                super().__init__(*args, **kwargs)
                self.mode = mode
                self.used_wrong_receipt = False

            def cleanup_teacher_cases(self, case_ids, run_id, **kwargs):
                receipt = super().cleanup_teacher_cases(case_ids, run_id, **kwargs)
                if not self.used_wrong_receipt and case_ids:
                    self.used_wrong_receipt = True
                    if self.mode == "empty":
                        receipt["deletedIds"] = []
                    elif self.mode == "missing":
                        receipt["deletedIds"] = receipt["deletedIds"][:-1]
                    else:
                        receipt["deletedIds"] = [*receipt["deletedIds"], "AUTO-OTHER-RUN-01"]
                return receipt

        for mode in ("empty", "missing", "extra"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as temporary:
                backend = WrongDeletedIds(self.target, mode=mode)
                runner = self._runner(temporary, backend)
                dry = runner.run(f"run_deleted_{mode}", mode="dry-run")
                result = runner.run(
                    f"run_deleted_{mode}", mode="apply",
                    confirmation_token=dry["confirmation_token"],
                )
                self.assertNotEqual(result["status"], "PASSED")
                self.assertEqual(backend.temporary_cases, set())

    def test_exact_case_lookup_rejects_duplicate_or_unrequested_ids(self):
        from online_e2e.synthetic_backend import SyntheticRegressionBackend

        class InvalidExactCases(SyntheticRegressionBackend):
            def existing_case_ids(self, case_ids):
                return {"caseIds": [case_ids[0], case_ids[0], "AUTO-OTHER-RUN-01"]}

        with tempfile.TemporaryDirectory() as temporary:
            backend = InvalidExactCases(self.target)
            runner = self._runner(temporary, backend)
            result = runner.run("run_invalid_exact", mode="dry-run")
            self.assertEqual(result["status"], "BLOCKED")
            self.assertEqual(result["code"], "CONTRACT_CHANGED")
            self.assertNotIn("confirmation_token", result)

    def test_live_read_only_precheck_lists_current_known_blockers_and_safe_knowledge_candidates(self):
        from online_e2e.live_backend import LiveRegressionBackend

        class Teaching:
            def current_user(self):
                return {"userNid": "private-user", "roleList": [{"roleCode": "school_teacher"}]}

            def assistants(self, payload):
                self.payload = payload
                return [{
                    "friendNid": "FEpEJws9cS",
                    "friendNickName": "中药材",
                    "appType": "AUTO_SMART_ROBOT",
                    "appCategory": "AI_COURSE_REPRESENTATIVE",
                    "isV5": True,
                }]

            def resolve_relationship(self, payload, *, expert_nid, expected_version=None):
                return {
                    "assistant_nid": payload["agentNid"],
                    "expert_nid": expert_nid,
                    "expert_name": "数据法学案例专家",
                    "version": "6",
                }

        class Pds:
            def knowledge_bindings(self, expert_nid):
                return [
                    {
                        "knowledgeBaseNid": "private-knowledge-id",
                        "knowledgeBaseName": "数据法学（测试）",
                        "knowledgeType": "course",
                        "resourceCount": 11,
                    }
                ]

        teaching = Teaching()
        result = LiveRegressionBackend(Pds(), teaching).precheck(self.target)
        codes = {blocker.code for blocker in result.blockers}
        self.assertIn("KNOWLEDGE_TARGET_AMBIGUOUS", codes)
        self.assertIn("TEST_ISOLATION_UNAVAILABLE", codes)
        self.assertIn("STUDENT_TRANSPORT_UNVERIFIED", codes)
        self.assertIn("SAVE_ENDPOINT_UNVERIFIED", codes)
        self.assertEqual(teaching.payload["userNid"], "private-user")
        rendered = json.dumps([blocker.as_dict() for blocker in result.blockers], ensure_ascii=False)
        self.assertIn("数据法学（测试）", rendered)
        self.assertIn("course", rendered)
        self.assertIn("11", rendered)
        self.assertNotIn("private-user", rendered)
        self.assertNotIn("private-knowledge-id", rendered)
        self.assertIsNone(result.assistant_nid)

    def test_live_precheck_uses_isolated_assistant_identity_and_same_expert_version(self):
        from online_e2e.live_backend import LiveRegressionBackend

        isolated_target = replace(
            self.target,
            isolated_test_assistant_nid="isolated-assistant",
            isolated_test_assistant_name="隔离助教 AI助教",
            live_test_enabled=True,
        )

        class Teaching:
            def __init__(self):
                self.relationship_calls = []

            def current_user(self):
                return {"userNid": "private-user", "roleList": [{"roleCode": "school_teacher"}]}

            def assistants(self, payload):
                common = {
                    "appType": "AUTO_SMART_ROBOT",
                    "appCategory": "AI_COURSE_REPRESENTATIVE",
                    "isV5": True,
                }
                return [
                    {**common, "friendNid": "FEpEJws9cS", "friendNickName": "中药材"},
                    {**common, "friendNid": "isolated-assistant", "friendNickName": "隔离助教"},
                ]

            def resolve_relationship(self, payload, *, expert_nid, expected_version=None):
                self.relationship_calls.append((payload["agentNid"], expected_version))
                version = "6"
                if expected_version is not None and expected_version != version:
                    raise AssertionError("wrong expected version")
                return {
                    "assistant_nid": payload["agentNid"],
                    "expert_nid": expert_nid,
                    "expert_name": "数据法学案例专家",
                    "version": version,
                }

        class Pds:
            def knowledge_bindings(self, expert_nid):
                return []

        teaching = Teaching()
        result = LiveRegressionBackend(Pds(), teaching).precheck(isolated_target)
        self.assertEqual(result.assistant_nid, "isolated-assistant")
        self.assertEqual(result.relationship_version, "6")
        self.assertEqual(
            teaching.relationship_calls,
            [("FEpEJws9cS", None), ("isolated-assistant", "6")],
        )

    def test_student_evaluator_requires_same_conversation_and_scenario_evidence(self):
        from online_e2e.fixtures import student_scenarios
        from online_e2e.runner import evaluate_student_receipt
        from online_e2e.synthetic_backend import SyntheticRegressionBackend

        backend = SyntheticRegressionBackend(self.target)
        previous_conversation = None
        for scenario in student_scenarios():
            receipt = backend.run_student(scenario, "synthetic-isolated-assistant")
            previous_conversation = evaluate_student_receipt(
                scenario,
                receipt,
                expected_assistant_nid="synthetic-isolated-assistant",
                expected_conversation_id=previous_conversation,
            )
        self.assertEqual(previous_conversation, "synthetic-conversation")

    def test_detailed_explanation_requires_facts_dispute_or_analysis_and_reflection(self):
        from online_e2e.backends import BackendFailure
        from online_e2e.fixtures import student_scenarios
        from online_e2e.runner import evaluate_student_receipt
        from online_e2e.synthetic_backend import SyntheticRegressionBackend

        scenario = next(
            item for item in student_scenarios() if item.scenario_id == "detailed-explanation"
        )
        backend = SyntheticRegressionBackend(self.target)
        receipt = backend.run_student(scenario, "synthetic-isolated-assistant")
        receipt["evidence"] = {"caseSummary": True, "followUpQuestion": True}
        with self.assertRaises(BackendFailure) as error:
            evaluate_student_receipt(
                scenario,
                receipt,
                expected_assistant_nid="synthetic-isolated-assistant",
                expected_conversation_id=None,
            )
        self.assertEqual(error.exception.code, "ASSERTION_FAILED")


if __name__ == "__main__":
    unittest.main()
