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


if __name__ == "__main__":
    unittest.main()
