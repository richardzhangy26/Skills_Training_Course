import importlib
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def api():
    try:
        module = importlib.import_module('team_acceptance.live_chat')
    except ModuleNotFoundError:
        module = None
    assert module is not None, '缺少已实测 stream→history 适配'
    return module


def case():
    return {'id': 'unknown', 'assistant_nid': 'assistant-test', 'expert_nid': 'expert-test',
            'prompt': '只读查询不存在的案例。', 'read_only': True}


class ChatTransport:
    def __init__(self, *, fail=False, wrong_trace=False, wrong_agent=False):
        self.fail, self.wrong_trace, self.wrong_agent = fail, wrong_trace, wrong_agent
        self.sent = []
        self.history_reads = 0

    def stream(self, method, path, *, json):
        assert (method, path) == ('POST', '/ai-agent/assistant/v1/chat/stream')
        self.sent.append(json)
        assert json['terminal'] == 'TEACHER'
        assert json['fromNid'] == 'private-user'
        if self.fail:
            raise TimeoutError('Authorization: Bearer private-token')
        name = '错误专家' if self.wrong_agent else '合成专家'
        for event, text, additional in [('ANSWER', '过程文字', False),
                                         ('ANSWER', '查不到', False),
                                         ('ANSWER', '，未补造。', True),
                                         ('ALL_FINISHED', None, False)]:
            yield ('event:' + event + '\ndata:' + __import__('json').dumps(
                {'event': event, 'text': text, 'isAdditional': additional,
                 'agentName': name, 'agentNid': None}) + '\n\n').encode()

    def request(self, method, path, *, json):
        assert path == '/chatim/v1/robot/chat/history'
        self.history_reads += 1
        sent = self.sent[-1]
        return {'code': 200, 'data': {'list': [{
            'nid': sent['metaData']['answerChatNid'],
            'traceId': 'wrong' if self.wrong_trace else sent['traceId'],
            'fromUserNid': sent['toNid'], 'toUserNid': 'private-user',
            'msgText': '查不到，未补造。', 'msgType': 'ROBOT_ANSWER',
            'customMsgType': 'ROBOT_ANSWER', 'stepStatus': 'DONE',
            'msgId': 'server-generated', 'msgKey': 'server-generated-key'}]}}


def test_live_stream_and_exact_answer_history_without_fake_session_or_user_message():
    transport = ChatTransport()
    r = api().run_case(case(), '合成专家', transport, 'private-user')
    assert r['terminal_status'] == 'ALL_FINISHED'
    assert r['response'] == '查不到，未补造。'
    assert r['readback']['confirmed'] is True
    assert r['input_persisted'] is False
    assert r['session_id'] == ''
    assert r['expert_execution_verified'] is True
    assert r['readback']['messages'][0]['trace_id'] == r['trace_id']
    assert 'private-user' not in json.dumps(r)
    assert len(transport.sent) == 1


def test_wrong_trace_never_verifies_readback():
    r = api().run_case(case(), '合成专家', ChatTransport(wrong_trace=True), 'private-user')
    assert r['readback']['confirmed'] is False


def test_uncertain_send_never_retries_and_redacts_error():
    transport = ChatTransport(fail=True)
    r = api().run_case(case(), '合成专家', transport, 'private-user')
    assert len(transport.sent) == 1
    assert r['error_code'] == 'WRITE_STATE_UNKNOWN'
    assert r['terminal_status'] is None
    assert 'private-token' not in json.dumps(r)


def test_requested_expert_is_not_proof_of_actual_execution():
    r = api().run_case(case(), '合成专家', ChatTransport(wrong_agent=True), 'private-user')
    assert r['expert_execution_verified'] is False
    assert r['readback']['confirmed'] is False


def test_write_case_rejected_before_transport():
    c = case()
    c['read_only'] = False
    transport = ChatTransport()
    with pytest.raises(ValueError):
        api().run_case(c, '合成专家', transport, 'private-user')
    assert not transport.sent


def suite_config():
    c = case()
    c['assertions'] = {'terminal_status': ['ALL_FINISHED'], 'contains_all': ['查不到']}
    return {'schema_version': 1, 'assistants': [{'nid': 'assistant-test', 'name': '合成助教',
        'experts': [{'nid': 'expert-test', 'name': '合成专家', 'expected_version': '6'}]}],
        'cases': [c]}


class SuiteTransport(ChatTransport):
    def request(self, method, path, *, json=None, params=None):
        if path == '/console/v1/get-current-user-detail':
            return {'code': 200, 'data': {'userNid': 'private-user', 'roleList': [{'roleCode': 'school_teacher'}]}}
        if path.endswith('/agent/list'):
            return {'code': 200, 'data': [{'friendNid': 'assistant-test', 'friendNickName': '合成助教',
                'appType': 'AUTO_SMART_ROBOT', 'appCategory': 'AI_COURSE_REPRESENTATIVE', 'isV5': True}]}
        if path.endswith('agentFullConfig'):
            return {'code': 200, 'data': {'basicInfo': {'nid': 'assistant-test', 'appName': '合成助教'},
                'subAgentVOS': [{'agentNid': 'expert-test', 'name': '合成专家', 'enabled': True, 'version': '6'}]}}
        if path.endswith('/bind/list'):
            return {'code': 200, 'data': []}
        return super().request(method, path, json=json)


def test_suite_same_run_does_not_send_again(tmp_path):
    transport = SuiteTransport()
    r = api().run_suite(suite_config(), transport, tmp_path, 'run-1')
    assert r['status'] == 'pass'
    assert r['evidence_origin'] == 'captured-live-api'
    replay = api().run_suite(suite_config(), transport, tmp_path, 'run-1')
    assert replay['status'] == 'pass'
    assert len(transport.sent) == 1


def test_crash_fence_stops_new_run_and_preserves_checkpoint(tmp_path):
    class CrashTransport(SuiteTransport):
        def stream(self, *args, **kwargs):
            self.sent.append(kwargs['json'])
            raise KeyboardInterrupt()
    transport = CrashTransport()
    with pytest.raises(KeyboardInterrupt):
        api().run_suite(suite_config(), transport, tmp_path, 'run-crash')
    before = (tmp_path / 'runs' / 'run-crash.json').read_bytes()
    r = api().run_suite(suite_config(), transport, tmp_path, 'run-new')
    assert r['error'] == 'RECOVERY_REQUIRED'
    assert len(transport.sent) == 1
    assert (tmp_path / 'runs' / 'run-crash.json').read_bytes() == before


def test_cli_run_produces_live_evidence_and_report(tmp_path, capsys):
    from team_acceptance.cli import main
    cpath = tmp_path / 'config.json'
    cpath.write_text(json.dumps(suite_config()))
    transport = SuiteTransport()
    code = main(['run', '--config', str(cpath), '--env-file', 'explicit.env',
                 '--run-id', 'cli-run', '--state-dir', str(tmp_path / 'state'),
                 '--report-prefix', str(tmp_path / 'report')], transport_factory=lambda p: transport)
    result = json.loads(capsys.readouterr().out)
    assert code == 0
    assert result['evidence_origin'] == 'captured-live-api'
    assert Path(result['reports']['markdown']).is_file()
    assert len(transport.sent) == 1


def test_same_run_different_targets_cannot_overwrite_checkpoint(tmp_path, monkeypatch):
    import copy
    import threading
    from concurrent.futures import ThreadPoolExecutor
    module = api()
    entered, release, second_entered = threading.Event(), threading.Event(), threading.Event()
    def preflight_hook(c, t):
        if c['assistants'][0]['nid'] == 'assistant-test':
            entered.set()
            assert release.wait(3)
        else:
            second_entered.set()
        return {'status': 'unverified', 'checks': []}
    monkeypatch.setattr(module, 'preflight', preflight_hook)

    other = copy.deepcopy(suite_config())
    other['assistants'][0]['nid'] = 'another-target'
    other['cases'][0]['assistant_nid'] = 'another-target'
    with ThreadPoolExecutor(2) as pool:
        first = pool.submit(module.run_suite, suite_config(), SuiteTransport(), tmp_path, 'same-run')
        assert entered.wait(2)
        second = pool.submit(module.run_suite, other, SuiteTransport(), tmp_path, 'same-run')
        raced = second_entered.wait(0.2)
        release.set()
        assert first.result()['status'] == 'pass'
        r = second.result()
    assert not raced
    assert r['error'] == 'RUN_CONFIG_MISMATCH'
