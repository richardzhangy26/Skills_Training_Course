"""可信采集边界回归；runner 是显式注入的合成测试替身，无网络。"""
import copy
from datetime import datetime, timedelta, timezone
import json

import pytest

from test_team_iteration import api, setup, fail_review, plan


def report():
    from test_team_acceptance import config, evidence
    from team_acceptance.core import evaluate
    data = evidence()
    data['records'][0]['captured_at'] = datetime.now(timezone.utc).isoformat()
    result = evaluate(config(), data)
    result['evidence_origin'] = 'captured-live-api'
    return result


def test_external_report_cannot_self_declare_trusted_live_source(tmp_path):
    session, _, _ = setup(tmp_path)
    with pytest.raises(ValueError, match='TRUSTED_CAPTURE_REQUIRED'):
        api().record_test(session, report())


def test_run_test_collects_once_and_reuses_durable_receipt(tmp_path):
    session, _, _ = setup(tmp_path)
    calls = []
    def runner(config, transport, state_dir, run_id):
        calls.append(run_id)
        return report()
    result = api().run_test(session, object(), runner=runner)
    assert result['status'] == 'AWAITING_REVIEW'
    assert api().run_test(session, object(), runner=runner)['status'] == 'AWAITING_REVIEW'
    assert len(calls) == 1


def test_trusted_capture_and_complete_grounded_review_reaches_passed(tmp_path):
    session, _, _ = setup(tmp_path)
    assert api().run_test(session, object(), runner=lambda *args: report())['status'] == 'AWAITING_REVIEW'
    result = api().record_review(session, {'criteria': [{
        'id': 'guide', 'verdict': 'pass', 'reason': '测试替身：已核对本条准则与原文引用',
        'evidence': [{'case_id': 'query', 'message_id': 'm1', 'quote': '案例法条依据'}]}]})
    assert result['status'] == 'PASSED'
    assert result['iteration'] == 0
    assert result['history'][0]['test_status'] == 'pass'


def test_restart_after_state_save_failure_reuses_capture_without_resend(tmp_path, monkeypatch):
    session, _, _ = setup(tmp_path)
    module = api()
    original_write = module.write_private_json_atomic
    calls = []
    def runner(*args):
        calls.append(1)
        return report()
    def interrupted_write(path, value):
        if path.name == 'iteration.json':
            raise OSError('synthetic process interruption')
        return original_write(path, value)
    monkeypatch.setattr(module, 'write_private_json_atomic', interrupted_write)
    with pytest.raises(OSError):
        module.run_test(session, object(), runner=runner)
    monkeypatch.setattr(module, 'write_private_json_atomic', original_write)
    assert module.run_test(session, object(), runner=runner)['status'] == 'AWAITING_REVIEW'
    assert len(calls) == 1


def test_run_test_rejects_modified_runtime_before_invoking_runner(tmp_path):
    session, _, _ = setup(tmp_path)
    runtime = json.loads((session / 'runtime-config.json').read_text())
    runtime['cases'][0]['prompt'] = '降低标准'
    (session / 'runtime-config.json').write_text(json.dumps(runtime))
    with pytest.raises(ValueError, match='RUNTIME_CONFIG_CHANGED'):
        api().run_test(session, object(), runner=lambda *args: pytest.fail('不可发送'))


@pytest.mark.parametrize('delta', [-3600, 3600])
def test_trusted_capture_still_rejects_stale_and_future_timestamps(tmp_path, delta):
    session, _, _ = setup(tmp_path)
    value = report()
    value['cases'][0]['evidence']['captured_at'] = (datetime.now(timezone.utc) + timedelta(seconds=delta)).isoformat()
    result = api().run_test(session, object(), runner=lambda *args: value)
    assert result['status'] == 'BLOCKED'
    assert result['block_reason'] in ('STALE_TEST_REPORT', 'FUTURE_TEST_REPORT')
    assert list(session.glob('round-0-capture.json'))


def test_transport_failure_persists_blocker_and_never_resends(tmp_path):
    session, _, _ = setup(tmp_path)
    calls = []
    def runner(*args):
        calls.append(1)
        raise RuntimeError('Authorization: secret-value')
    result = api().run_test(session, object(), runner=runner)
    assert result['status'] == 'BLOCKED'
    api().run_test(session, object(), runner=runner)
    assert len(calls) == 1
    assert 'secret-value' not in (session / 'round-0-capture.json').read_text()


def test_record_test_checks_signature_even_when_attacker_updates_report_digest(tmp_path):
    session, _, _ = setup(tmp_path)
    api().run_test(session, object(), runner=lambda *args: report())
    state = api().status(session)
    value = json.loads((session / 'round-0-capture.json').read_text())
    value['status'] = 'forged-pass'
    receipt = json.loads((session / 'round-0-receipt.json').read_text())
    receipt['binding']['report_hash'] = api()._hash(value)
    (session / 'round-0-receipt.json').write_text(json.dumps(receipt))
    with pytest.raises(ValueError, match='TRUSTED_CAPTURE_REQUIRED'):
        api()._trusted_capture(state, session, value)


def test_copied_receipt_cannot_cross_session_boundary(tmp_path):
    first, _, _ = setup(tmp_path / 'first')
    second, _, _ = setup(tmp_path / 'second')
    api().run_test(first, object(), runner=lambda *args: report())
    (second / 'round-0-receipt.json').write_bytes((first / 'round-0-receipt.json').read_bytes())
    value = json.loads((first / 'round-0-capture.json').read_text())
    with pytest.raises(ValueError, match='TRUSTED_CAPTURE_REQUIRED'):
        api().record_test(second, value)


def deployment_setup(tmp_path):
    session, source, _ = setup(tmp_path)
    fail_review(session)
    api().propose_change(session, plan())
    (source / 'expert/Agent.md').write_text('新版')
    api().record_changes(session)
    before = api().status(session)['platform_snapshot']
    snapshot = copy.deepcopy(before)
    snapshot['experts']['e1'].update(agent_md='新版', version='7', bound_versions={'a1': '7'})
    return session, snapshot


def test_old_message_and_trace_cannot_be_reused_after_changing_time(tmp_path):
    session, snapshot = deployment_setup(tmp_path)
    api().verify_deployment(session, snapshot)
    # fail_review baseline uses trace t10; only timestamp changes here.
    old = json.loads((session / 'round-0-capture.json').read_text())
    old['cases'][0]['evidence']['captured_at'] = datetime.now(timezone.utc).isoformat()
    result = api().run_test(session, object(), runner=lambda *args: old)
    assert result['status'] == 'BLOCKED'
    assert result['block_reason'] == 'REUSED_TEST_REPORT'


@pytest.mark.parametrize('change', ['skill', 'unplanned_expert', 'unrelated_setting', 'missing_binding'])
def test_deployment_rejects_changes_outside_exact_agent_md_plan(tmp_path, change):
    session, snapshot = deployment_setup(tmp_path)
    if change == 'skill': snapshot['experts']['e1']['skills'] = [{'nid': 'new'}]
    if change == 'unplanned_expert': snapshot['experts']['e2']['agent_md'] = '非计划改动'
    if change == 'unrelated_setting': snapshot['protection']['assistants']['a1']['generalSetting'] = {'changed': True}
    if change == 'missing_binding': snapshot['experts']['e1']['bound_versions'] = {'other': '7'}
    result = api().verify_deployment(session, snapshot)
    assert result['status'] == 'AWAITING_DEPLOYMENT'
    assert result['deployment_blocker'] in ('OUT_OF_SCOPE_DEPLOYMENT', 'BOUND_VERSION_MISMATCH')
