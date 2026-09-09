"""最终集成审查的离线回归；所有身份和事务均为合成数据。"""
from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
from types import MappingProxyType
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)) if str(ROOT) not in sys.path else None
from online_e2e.backends import BackendFailure
from online_e2e.contracts import load_target_config
from online_e2e.fixtures import teacher_case_ids
from online_e2e.reports import ReportWriter, sanitize_report
from online_e2e.run_store import DurableRunStore
from online_e2e.runner import ExpertE2ERunner
from online_e2e.synthetic_backend import SyntheticRegressionBackend


@pytest.fixture
def target():
    return load_target_config("data-law-case-expert", root=ROOT)


def runner_at(root, target, backend):
    return ExpertE2ERunner(target, backend, DurableRunStore(root / "state"), ReportWriter(root / "reports"))


def apply(runner, run_id="fix_run"):
    dry = runner.run(run_id, mode="dry-run")
    return runner.run(run_id, mode="apply", confirmation_token=dry["confirmation_token"])


def test_frozen_skill_order_diff_is_stable_json_in_all_outputs(tmp_path, target):
    backend = SyntheticRegressionBackend(target)
    backend._full_config["skillInfoList"].reverse()
    result = runner_at(tmp_path, target, backend).run("frozen", mode="dry-run")
    assert result["code"] == "AWAITING_CONFIRMATION"
    assert result["differences"]
    json.dumps(result, sort_keys=True)
    assert json.loads(Path(result["checkpoint_path"]).read_text())["differences"] == result["differences"]
    assert json.loads(Path(result["report_json"]).read_text())["differences"] == result["differences"]


def test_shared_sanitizer_preserves_business_ids_and_approval_but_removes_private_data(tmp_path):
    value = MappingProxyType({
        "run_id": "safe", "approval": MappingProxyType({"nonce": "recoverable", "diff_digest": "digest"}),
        "nested": (MappingProxyType({"Authorization": "secret-auth", "Cookie": "secret-cookie",
             "userId": "secret-user", "student_nid": "secret-student", "confirmationToken": "secret-confirm",
             "sessionId": "business-session", "assistantId": "business-assistant", "sessionCookie": "secret-session"}),),
        "text": "userId=secret-text-user student_nid:secret-text-student token=secret-text-token",
    })
    store = DurableRunStore(tmp_path / "state")
    checkpoint = json.loads(store.write_checkpoint("safe", value).read_text())
    report = json.loads(ReportWriter(tmp_path / "reports").write(value).json.read_text())
    safe = sanitize_report(value)
    assert checkpoint == report == safe
    encoded = json.dumps(safe)
    assert "secret-" not in encoded
    assert "business-session" in encoded and "business-assistant" in encoded
    assert safe["approval"] == {"nonce": "recoverable", "diff_digest": "digest"}


def test_prefixed_identity_fields_and_text_are_redacted():
    payload = {
        "fromUserNid": "private-from", "to_user_nid": "private-to",
        "ownerStudentId": "private-owner", "note": "fromUserNid=private-text toUserNid:private-text2 ownerStudentId=private-text3",
        "assistantId": "business-assistant", "conversationId": "business-conversation",
        "sessionId": "business-session", "messageId": "business-message", "traceId": "business-trace",
    }
    rendered = json.dumps(sanitize_report(payload))
    assert "private-" not in rendered
    assert all(value in rendered for key, value in payload.items() if key.endswith("Id") and key != "ownerStudentId")


def test_runner_result_and_cli_fallback_sanitize_extra_receipt_fields(tmp_path, target):
    class ExtraReceipt(SyntheticRegressionBackend):
        def run_student(self, *args):
            result = super().run_student(*args)
            result.update(userId="secret-user", Authorization="secret-auth", confirmation_token="secret-token")
            return result
    result = apply(runner_at(tmp_path, target, ExtraReceipt(target)))
    assert result["status"] == "PASSED"
    assert "secret-" not in json.dumps(result)
    from online_e2e.cli import main
    class ArbitraryRunner:
        def run(self, *args, **kwargs):
            return MappingProxyType({"status": "PASSED", "nested": (MappingProxyType({"token": "secret-token", "userId": "secret-user"}),)})
    stdout = StringIO()
    with redirect_stdout(stdout):
        assert main(["data-law-case-expert", "apply", "full", "--env-file", "/unused"], runner_factory=lambda _: ArbitraryRunner()) == 0
    assert "secret-" not in stdout.getvalue()
    json.loads(stdout.getvalue())


def test_student_failure_before_teacher_write_preserves_external_exact_case(tmp_path, target):
    class ExternalInsert(SyntheticRegressionBackend):
        def run_student(self, *args):
            self.temporary_cases.add(teacher_case_ids("fix_run")[0])
            raise BackendFailure("SYNTHETIC_STUDENT_FAILED")
    backend = ExternalInsert(target)
    original = backend.agent_content
    result = apply(runner_at(tmp_path, target, backend))
    assert backend.temporary_cases == {teacher_case_ids("fix_run")[0]}
    assert backend.last_cleanup_requested == ()
    assert result["status"] == "ROLLBACK_FAILED"
    assert result["residual_state"]
    assert backend.agent_content == original


def test_case_content_changes_synthetic_knowledge_digest(target):
    backend = SyntheticRegressionBackend(target)
    before = backend.current_knowledge_snapshot()
    backend.temporary_cases.add("AUTO-EXTERNAL-01")
    assert backend.current_knowledge_snapshot().digest != before.digest
    assert backend.snapshot(target).knowledge.digest == backend.current_knowledge_snapshot().digest


def test_cleanup_without_authoritative_ownership_keeps_cases(tmp_path, target):
    class NoOwnership(SyntheticRegressionBackend):
        def case_ownership(self, case_ids, *, run_id, change_id):
            raise BackendFailure("CASE_OWNERSHIP_UNVERIFIED")
    backend = NoOwnership(target)
    result = apply(runner_at(tmp_path, target, backend))
    assert result["status"] == "ROLLBACK_FAILED"
    assert backend.temporary_cases == set(teacher_case_ids("fix_run"))
    assert backend.last_cleanup_requested == ()


def test_knowledge_cas_prevents_case_deletion_before_external_change_is_discovered(tmp_path, target):
    backend = SyntheticRegressionBackend(target, external_knowledge_change_before_cleanup=True)
    result = apply(runner_at(tmp_path, target, backend))
    assert result["status"] == "ROLLBACK_FAILED"
    assert backend.temporary_cases == set(teacher_case_ids("fix_run"))
    assert backend.last_cleanup_requested == ()


@pytest.mark.parametrize("new_run,mode", [("crashed", "dry-run"), ("crashed", "apply"), ("other", "dry-run"), ("other", "apply")])
def test_publish_interrupt_persists_target_fence_and_original_checkpoint(tmp_path, target, new_run, mode):
    class CrashPublish(SyntheticRegressionBackend):
        def publish(self, *args):
            super().publish(*args)
            raise KeyboardInterrupt("synthetic crash")
    backend = CrashPublish(target)
    runner = runner_at(tmp_path, target, backend)
    with pytest.raises(KeyboardInterrupt):
        apply(runner, "crashed")
    writes = backend.write_count
    checkpoint = runner.store.read_checkpoint("crashed")
    fresh = runner_at(tmp_path, target, backend)
    result = fresh.run(new_run, mode=mode)
    assert backend.write_count == writes
    assert result["code"] == "RECOVERY_REQUIRED"
    assert "write_may_have_occurred" in result["residual_state"]
    assert result["recovery"]["run_id"] == "crashed"
    assert fresh.store.read_checkpoint("crashed") == checkpoint
    snapshot = tmp_path / "state" / result["recovery"]["snapshot_ref"]
    assert snapshot.is_file()
    assert json.loads(snapshot.read_text())["config"]["full_config"]["expertMd"]["customContent"] == "synthetic baseline Agent.md"


@pytest.mark.parametrize("failure", [None, "student:exact-statute"])
def test_verified_finish_clears_fence(tmp_path, target, failure):
    backend = SyntheticRegressionBackend(target, fail_at=failure)
    runner = runner_at(tmp_path, target, backend)
    assert apply(runner)["status"] in ("PASSED", "ROLLED_BACK")
    assert runner_at(tmp_path, target, backend).run("next", mode="dry-run")["code"] == "AWAITING_CONFIRMATION"
