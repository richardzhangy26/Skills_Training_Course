from __future__ import annotations

import importlib
import json
from dataclasses import replace
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def load_contracts():
    try:
        return importlib.import_module("online_e2e.contracts")
    except ModuleNotFoundError:
        return None


def load_config_diff():
    try:
        return importlib.import_module("online_e2e.config_diff")
    except ModuleNotFoundError:
        return None


def load_safety():
    try:
        return importlib.import_module("online_e2e.safety")
    except ModuleNotFoundError:
        return None


class OnlineE2ECoreTests(unittest.TestCase):
    def test_versioned_target_config_loads_fixed_data_law_identity_and_local_assets(self):
        contracts = load_contracts()
        self.assertIsNotNone(contracts)

        config = contracts.load_target_config("data-law-case-expert", root=ROOT)

        self.assertEqual(config.target_id, "data-law-case-expert")
        self.assertEqual(config.expert_nid, "x3PalTZaWr")
        self.assertEqual(config.assistant_nid, "FEpEJws9cS")
        self.assertIsNone(config.isolated_test_assistant_nid)
        self.assertIsNone(config.isolated_test_assistant_name)
        self.assertFalse(config.live_test_enabled)
        self.assertIsNone(config.knowledge_base_nid)
        self.assertTrue(hasattr(config, "runtime_agent_nid"))
        self.assertIsNone(config.runtime_agent_nid)
        self.assertEqual(config.expert_name, "数据法学案例专家")
        self.assertEqual(config.assistant_name, "中药材 AI助教")
        self.assertEqual(config.agent_path, ROOT / "Agent.md")
        self.assertEqual(config.manifest_path, ROOT / "case-library" / "data" / "manifest.json")
        self.assertEqual(
            set(config.online_skill_nids),
            {
                "search-router",
                "polymas-teacher-knowledge-distillation",
                "data-law-case-maintenance",
                "data-law-case-query",
                "polymas-resource-upload",
            },
        )
        self.assertEqual(
            config.expected_skill_order,
            (
                "search-router",
                "polymas-teacher-knowledge-distillation",
                "data-law-case-maintenance",
                "data-law-case-query",
                "polymas-resource-upload",
            ),
        )
        self.assertTrue(all(value for value in config.online_skill_nids.values()))
        self.assertEqual(set(config.online_skill_binding_sources), set(config.online_skill_nids))
        self.assertEqual(
            config.online_skill_binding_sources["polymas-teacher-knowledge-distillation"],
            "MARKETPLACE",
        )

    def test_target_skill_nid_source_and_order_keys_must_match(self):
        contracts = load_contracts()
        import unittest.mock

        invalid = {
            "target_id": "data-law-case-expert",
            "expert_nid": "x",
            "expert_name": "x",
            "assistant_nid": "a",
            "assistant_name": "a",
            "isolated_test_assistant_nid": None,
            "isolated_test_assistant_name": None,
            "live_test_enabled": False,
            "knowledge_base_nid": None,
            "local_assets": {
                "agent": "Agent.md", "query_skill": "q", "maintenance_skill": "m",
                "html": "h", "knowledge_jsonl": "k", "manifest": "x",
            },
            "online_skill_nids": {"one": "nid-1"},
            "online_skill_binding_sources": {"two": "BUILTIN"},
            "expected_skill_order": ["one"],
        }
        with unittest.mock.patch.object(Path, "read_text", return_value=json.dumps(invalid)):
            with self.assertRaisesRegex(ValueError, "skill_mapping_mismatch"):
                contracts.load_target_config("data-law-case-expert", root=ROOT)

    def test_target_alias_rejects_path_traversal_before_reading_config(self):
        contracts = load_contracts()
        for value in ("../data-law-case-expert", "two/levels", "..", "", "含中文"):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "invalid_target_id"):
                    contracts.load_target_config(value, root=ROOT)

    def test_normalized_online_config_has_stable_digest_despite_key_and_skill_order(self):
        config_diff = load_config_diff()
        self.assertIsNotNone(config_diff)

        first = {
            "display_name": "数据法学案例专家",
            "metadata": {"z": 2, "a": 1},
            "skills": [
                {"nid": "skill-b", "name": "B"},
                {"nid": "skill-a", "name": "A"},
            ],
        }
        second = {
            "skills": [
                {"name": "A", "nid": "skill-a"},
                {"name": "B", "nid": "skill-b"},
            ],
            "metadata": {"a": 1, "z": 2},
            "display_name": "数据法学案例专家",
        }

        first_snapshot = config_diff.snapshot_config(first)
        second_snapshot = config_diff.snapshot_config(second)

        self.assertEqual(first_snapshot.digest, second_snapshot.digest)
        self.assertEqual(
            [skill["nid"] for skill in first_snapshot.normalized["skills"]],
            ["skill-a", "skill-b"],
        )

    def test_undeclared_online_skill_is_reported_and_blocks_apply(self):
        config_diff = load_config_diff()
        self.assertIsNotNone(config_diff)
        compare_configs = getattr(config_diff, "compare_configs", None)
        self.assertIsNotNone(compare_configs)

        report = compare_configs(
            expected={"skills": [{"nid": "skill-a", "name": "查询"}]},
            actual={
                "skills": [
                    {"nid": "skill-a", "name": "查询"},
                    {"nid": "skill-rogue", "name": "未声明"},
                ]
            },
            declared_skill_nids={"查询": "skill-a"},
        )

        self.assertFalse(report.apply_allowed)
        self.assertEqual(report.items[0].kind, "undeclared_skill")
        self.assertEqual(report.items[0].actual, "skill-rogue")

    def test_apply_gate_rejects_missing_unexpected_and_unresolved_skill_nids(self):
        config_diff = load_config_diff()
        cases = (
            (
                "actual skill without nid",
                {"skills": [{"name": "查询"}]},
                {"skills": [{"nid": "skill-a", "name": "查询"}]},
                {"查询": "skill-a"},
                "missing_skill_nid",
            ),
            (
                "actual immutable nid is not expected",
                {"skills": [{"nid": "skill-a"}]},
                {"skills": [{"nid": "skill-b"}]},
                {"查询": "skill-a", "维护": "skill-b"},
                "unexpected_skill_nid",
            ),
            (
                "expected skill without nid",
                {"skills": [{"name": "查询"}]},
                {"skills": []},
                {},
                "missing_skill_nid",
            ),
            (
                "unresolved placeholder is dry run only",
                {"skills": [{"nid": "PDS_NID_UNRESOLVED_query"}]},
                {"skills": [{"nid": "PDS_NID_UNRESOLVED_query"}]},
                {"查询": "PDS_NID_UNRESOLVED_query"},
                "unresolved_skill_nid",
            ),
        )
        for name, expected, actual, declared, reason in cases:
            with self.subTest(name=name):
                report = config_diff.compare_configs(
                    expected, actual, declared_skill_nids=declared
                )
                self.assertFalse(report.apply_allowed)
                self.assertIn(reason, [item.kind for item in report.items])
                with self.assertRaisesRegex(ValueError, reason):
                    config_diff.require_apply_allowed(report)

    def test_root_skills_have_individual_readable_differences_and_change_digest(self):
        contracts = load_contracts()
        config_diff = load_config_diff()
        report = config_diff.compare_configs(
            expected={
                "skills": [
                    {"nid": "skill-a", "name": "旧名称"},
                    {"nid": "skill-b", "name": "待删除"},
                ]
            },
            actual={
                "skills": [
                    {"nid": "skill-a", "name": "新名称"},
                    {"nid": "skill-c", "name": "新增"},
                ]
            },
            declared_skill_nids={
                "查询": "skill-a",
                "维护": "skill-b",
                "额外": "skill-c",
            },
        )

        paths = {item.path for item in report.items}
        self.assertIn("skills[nid=skill-a].name", paths)
        self.assertIn("skills[nid=skill-b]", paths)
        self.assertIn("skills[nid=skill-c]", paths)
        self.assertNotEqual(
            config_diff.summarize_differences(report.items),
            config_diff.summarize_differences(
                (contracts.Difference("skills", "changed", None, None),)
            ),
        )

    def test_config_snapshot_is_deeply_immutable_after_digest_calculation(self):
        config_diff = load_config_diff()
        snapshot = config_diff.snapshot_config(
            {"metadata": {"nested": {"name": "初始"}}, "skills": [{"nid": "a"}]}
        )

        with self.assertRaises(TypeError):
            snapshot.normalized["metadata"]["nested"]["name"] = "篡改"
        with self.assertRaises(TypeError):
            snapshot.normalized["skills"][0] = {"nid": "b"}
        self.assertEqual(
            snapshot.digest,
            config_diff.snapshot_config(
                {"metadata": {"nested": {"name": "初始"}}, "skills": [{"nid": "a"}]}
            ).digest,
        )

    def test_apply_guard_rejects_diff_that_contains_undeclared_skill(self):
        config_diff = load_config_diff()
        require_apply_allowed = getattr(config_diff, "require_apply_allowed", None)
        self.assertIsNotNone(require_apply_allowed)
        report = config_diff.compare_configs(
            expected={"skills": []},
            actual={"skills": [{"nid": "unknown-skill"}]},
            declared_skill_nids={},
        )

        with self.assertRaisesRegex(ValueError, "undeclared_skill"):
            require_apply_allowed(report)

    def test_normal_skill_metadata_difference_remains_applyable(self):
        config_diff = load_config_diff()
        report = config_diff.compare_configs(
            expected={"skills": [{"nid": "skill-a", "name": "旧名称"}]},
            actual={"skills": [{"nid": "skill-a", "name": "新名称"}]},
            declared_skill_nids={"查询": "skill-a"},
        )

        self.assertTrue(report.apply_allowed)
        self.assertIn(
            "skills[nid=skill-a].name", {item.path for item in report.items}
        )
        config_diff.require_apply_allowed(report)

    def test_apply_guard_has_stable_fallback_for_inconsistent_blocked_report(self):
        config_diff = load_config_diff()
        report = config_diff.compare_configs(
            expected={"skills": []}, actual={"skills": []}, declared_skill_nids={}
        )

        with self.assertRaisesRegex(ValueError, "apply_blocked"):
            config_diff.require_apply_allowed(
                replace(report, apply_allowed=False, items=())
            )

    def test_expected_undeclared_skill_nid_blocks_apply_without_actual_skills(self):
        config_diff = load_config_diff()
        report = config_diff.compare_configs(
            expected={"skills": [{"nid": "rogue-skill"}]},
            actual={"skills": []},
            declared_skill_nids={},
        )

        self.assertFalse(report.apply_allowed)
        self.assertIn("undeclared_skill", [item.kind for item in report.items])
        with self.assertRaisesRegex(ValueError, "undeclared_skill"):
            config_diff.require_apply_allowed(report)

    def test_malformed_actual_skills_response_is_contract_changed_and_blocked(self):
        config_diff = load_config_diff()
        cases = (
            {"skills": {"nid": "skill-a"}},
            {"skills": ["not-a-skill-mapping"]},
        )
        for actual in cases:
            with self.subTest(actual=actual):
                report = config_diff.compare_configs(
                    expected={"skills": []},
                    actual=actual,
                    declared_skill_nids={},
                )
                self.assertFalse(report.apply_allowed)
                self.assertIn("CONTRACT_CHANGED", [item.kind for item in report.items])
                with self.assertRaisesRegex(ValueError, "CONTRACT_CHANGED"):
                    config_diff.require_apply_allowed(report)

    def test_knowledge_and_difference_summaries_have_stable_digests(self):
        contracts = load_contracts()
        config_diff = load_config_diff()
        snapshot_knowledge = getattr(config_diff, "snapshot_knowledge", None)
        summarize_differences = getattr(config_diff, "summarize_differences", None)
        self.assertIsNotNone(snapshot_knowledge)
        self.assertIsNotNone(summarize_differences)

        knowledge = snapshot_knowledge("library-v1", "one traceable knowledge block")
        self.assertEqual(knowledge.version, "library-v1")
        self.assertEqual(
            knowledge.digest,
            snapshot_knowledge("library-v1", "one traceable knowledge block").digest,
        )
        difference_a = contracts.Difference("name", "changed", "旧名", "新名")
        difference_b = contracts.Difference("skills", "undeclared_skill", None, "rogue")
        self.assertEqual(
            summarize_differences((difference_a, difference_b)),
            summarize_differences((difference_b, difference_a)),
        )

    def test_confirmation_token_is_bound_to_every_snapshot_field_and_single_use(self):
        contracts = load_contracts()
        safety = load_safety()
        self.assertIsNotNone(safety)
        manager = safety.ConfirmationTokenManager(secret=b"test-secret")
        binding = contracts.ConfirmationBinding(
            target_id="data-law-case-expert",
            snapshot_digest="snapshot-digest",
            expected_digest="expected-digest",
            knowledge_version="77-v1",
            diff_digest="diff-digest",
            nonce="session-nonce-0001",
        )

        token = manager.issue(binding)

        for field in (
            "target_id",
            "snapshot_digest",
            "expected_digest",
            "knowledge_version",
            "diff_digest",
            "nonce",
        ):
            with self.subTest(field=field):
                self.assertFalse(manager.consume(token, replace(binding, **{field: "tampered"})))
        self.assertTrue(manager.consume(token, binding))
        self.assertFalse(manager.consume(token, binding))

    def test_recursive_redaction_removes_sensitive_keys_and_credential_values(self):
        safety = load_safety()
        redact = getattr(safety, "redact_sensitive", None)
        self.assertIsNotNone(redact)
        authorization = "Bearer super-secret-token-1234567890"
        cookie = "sessionid=cookie-secret-1234567890"
        jwt = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ0ZXN0LXVzZXIifQ.signature1234567890"
        access_token = "access-secret-1234567890"

        result = redact(
            {
                "Authorization": authorization,
                "nested": {
                    "Cookie": cookie,
                    "jwt": jwt,
                    "access_token": access_token,
                    "safe": "visible",
                },
                "message": f"Authorization: {authorization}; Cookie: {cookie}; {jwt}",
            }
        )

        rendered = json.dumps(result, ensure_ascii=False)
        for secret in (authorization, cookie, jwt, access_token):
            self.assertNotIn(secret, rendered)
        self.assertIn("visible", rendered)

    def test_redaction_removes_common_bare_token_values_from_report_text(self):
        safety = load_safety()
        openai_token = "sk-proj-1234567890abcdefghijklmnopqrstuvwxyz"
        github_token = "ghp_1234567890abcdefghijklmnopqrstuvwxyz"

        rendered = safety.redact_sensitive(
            f"upstream returned {openai_token} and {github_token}"
        )

        self.assertNotIn(openai_token, rendered)
        self.assertNotIn(github_token, rendered)

    def test_redaction_removes_json_quoted_credentials_from_nested_serialized_text(self):
        safety = load_safety()
        authorization = "Bearer plain-secret-1234567890"
        cookie = "sessionid=cookie-plain-secret-1234567890"
        nested = json.dumps({"Authorization": authorization, "Cookie": cookie})
        serialized = json.dumps({"nested": nested})

        redacted = safety.redact_sensitive(serialized)

        self.assertNotIn(authorization, redacted)
        self.assertNotIn(cookie, redacted)

    def test_redaction_removes_all_values_from_plain_and_nested_cookie_headers(self):
        safety = load_safety()
        first = "sid=first-test-secret"
        second = "auth=second-test-secret"
        header = f"Cookie: {first}; {second}\nstatus=visible"
        serialized = json.dumps({"nested": json.dumps({"Cookie": f"{first}; {second}"})})

        redacted_header = safety.redact_sensitive(header)
        redacted_serialized = safety.redact_sensitive(serialized)

        for secret in (first, second):
            self.assertNotIn(secret, redacted_header)
            self.assertNotIn(secret, redacted_serialized)
        self.assertIn("status=visible", redacted_header)

    def test_checkpoint_write_is_atomic_private_and_redacted(self):
        safety = load_safety()
        write_checkpoint = getattr(safety, "write_checkpoint_atomic", None)
        self.assertIsNotNone(write_checkpoint)

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "nested" / "checkpoint.json"
            result = write_checkpoint(path, {"run": "run-001", "token": "do-not-save"})

            self.assertEqual(result, path)
            self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["run"], "run-001")
            self.assertNotIn("do-not-save", path.read_text(encoding="utf-8"))
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            self.assertEqual(list(path.parent.glob("*.tmp")), [])

    def test_public_run_contract_carries_stage_snapshot_diff_and_assertion_results(self):
        contracts = load_contracts()
        run_request_type = getattr(contracts, "RunRequest", None)
        self.assertIsNotNone(run_request_type)

        request = run_request_type(target_id="data-law-case-expert", run_id="run-001")
        stage = contracts.StageState(
            name="compare_config", status=contracts.StageStatus.PASSED
        )
        knowledge = contracts.KnowledgeSnapshot(version="v1", digest="knowledge-digest")
        assertion = contracts.TestAssertionResult(
            name="manifest_is_present", passed=True, expected=True, actual=True
        )
        result = contracts.RunResult(
            target_id=request.target_id,
            run_id=request.run_id,
            status=contracts.StageStatus.PASSED,
            stages=(stage,),
            knowledge_snapshot=knowledge,
            assertions=(assertion,),
        )

        self.assertFalse(request.apply)
        self.assertEqual(result.stages[0].status, contracts.StageStatus.PASSED)
        self.assertEqual(result.knowledge_snapshot.version, "v1")
        self.assertTrue(result.assertions[0].passed)


if __name__ == "__main__":
    unittest.main()
