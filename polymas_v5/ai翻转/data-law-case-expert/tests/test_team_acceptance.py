"""专家团只读验收；所有 transport/对话样本均为 synthetic。"""
import copy
import importlib
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def api():
    try:
        module = importlib.import_module('team_acceptance.core')
    except ModuleNotFoundError:
        module = None
    assert module is not None, '需要新增独立专家团验收模块'
    return module


def config():
    return {'schema_version': 1, 'assistants': [{'name': '合成助教', 'nid': 'a1',
        'experts': [{'name': '合成专家', 'nid': 'e1', 'expected_version': 'v6',
                     'knowledge_bindings': [{'nid': 'k1', 'name': '合成知识库'}]}]}],
        'cases': [{'id': 'query', 'assistant_nid': 'a1', 'expert_nid': 'e1',
                   'read_only': True, 'prompt': '查询案例的法条。',
                   'assertions': {'terminal_status': ['completed'],
                                  'contains_all': ['法条'], 'contains_any': ['案例', '依据'],
                                  'excludes': ['写入成功']}}]}


class ReadTransport:
    def __init__(self):
        self.calls = []
        self.relations = [{'agentNid': 'e1', 'name': '合成专家', 'enabled': True, 'version': 'v6'}]

    def request(self, method, path, *, params=None, json=None):
        self.calls.append((method, path, params, json))
        if path.endswith('get-current-user-detail'):
            data = {'userNid': 'private-user', 'roleList': [{'roleCode': 'school_teacher'}]}
        elif path.endswith('/agent/list'):
            assert json['userNid'] == 'private-user'
            assert json['roleTypeForPC'] == 'PC_TEACHER'
            data = [{'friendNid': 'a1', 'friendNickName': '合成助教',
                     'appType': 'AUTO_SMART_ROBOT', 'appCategory': 'AI_COURSE_REPRESENTATIVE', 'isV5': True}]
        elif path.endswith('agentFullConfig'):
            data = {'basicInfo': {'nid': 'a1', 'appName': '合成助教'},
                    'subAgentVOS': copy.deepcopy(self.relations), 'userNid': 'private-user'}
        elif path.endswith('/bind/list'):
            data = [{'knowledgeBaseNid': 'k1', 'knowledgeBaseName': '合成知识库'}]
        else:
            raise AssertionError('禁止未经核验端点或写入')
        return {'code': 200, 'data': data}


def evidence(source='live-api'):
    identity = {'assistant_nid': 'a1', 'expert_nid': 'e1', 'session_id': 's1',
                'message_id': 'm1', 'trace_id': 't1'}
    return {'schema_version': 1, 'records': [{'case_id': 'query', 'source': source,
        'expert_execution_verified': True, 'observed_agent_names': ['合成专家'],
        'captured_at': '2026-09-05T10:00:00+08:00', **identity,
        'prompt': '查询案例的法条。', 'terminal_status': 'completed', 'response': '案例法条依据',
        'send': {'confirmed': True, 'source': source, **identity, 'prompt': '查询案例的法条。'},
        'readback': {'confirmed': True, 'source': source, 'kind': 'history', **identity,
                     'terminal_status': 'completed', 'response': '案例法条依据',
                     'messages': [{'role': 'user', **identity, 'text': '查询案例的法条。'},
                                  {'role': 'assistant', **identity, 'text': '案例法条依据',
                                   'terminal_status': 'completed'}]},
        'userNid': 'private-user'}]}


def test_explicit_wrong_expert_execution_never_passes():
    e = evidence()
    e['records'][0]['expert_execution_verified'] = False
    assert api().evaluate(config(), e)['status'] != 'pass'


def test_duplicate_enabled_expert_names_block_preflight():
    t = ReadTransport()
    t.relations.append(dict(t.relations[0], agentNid='another-expert'))
    assert api().preflight(config(), t)['status'] == 'fail'


def test_authenticated_identity_is_redacted_inside_public_named_fields():
    class NamedLibraryTransport(ReadTransport):
        def request(self, method, path, **kwargs):
            result = super().request(method, path, **kwargs)
            if path.endswith('/bind/list'):
                result['data'][0]['knowledgeBaseName'] = 'self_private-user'
            return result
    report = api().preflight(config(), NamedLibraryTransport())
    assert 'private-user' not in json.dumps(report)


def test_known_identity_redaction_preserves_json_numbers_and_escaped_text():
    result = api().sanitize_identity({'count': 1234567890, 'label': 'self_1234567890'}, '1234567890')
    assert result == {'count': 1234567890, 'label': 'self_[REDACTED]'}
    assert api().sanitize_identity({'value': 'line\nend'}, 'n')['value'] == 'li[REDACTED]e\ne[REDACTED]d'


def test_config_requires_unique_declared_read_only_targets(tmp_path):
    module = api()
    path = tmp_path / 'config.json'
    path.write_text(json.dumps(config()))
    assert module.load_config(path)['assistants'][0]['nid'] == 'a1'
    for modify in ('duplicate', 'write', 'unknown'):
        value = config()
        if modify == 'duplicate': value['cases'].append(value['cases'][0])
        if modify == 'write': value['cases'][0]['read_only'] = False
        if modify == 'unknown': value['cases'][0]['expert_nid'] = 'unknown'
        with pytest.raises(ValueError): module.validate_config(value)


def test_preflight_single_snapshot_and_no_publish_gate():
    module = api()
    transport = ReadTransport()
    report = module.preflight(config(), transport)
    assert report['status'] == 'unverified'
    assert all(check['status'] == 'pass' for check in report['checks'])
    assert len([call for call in transport.calls if call[1].endswith('agentFullConfig')]) == 1
    assert 'private-user' not in json.dumps(report)
    assert report['snapshots'][0]['assistant_nid'] == 'a1'


@pytest.mark.parametrize('change', ['version', 'disabled', 'duplicate'])
def test_preflight_rejects_wrong_expert_relationship(change):
    module = api()
    transport = ReadTransport()
    if change == 'version': transport.relations[0]['version'] = 'v5'
    if change == 'disabled': transport.relations[0]['enabled'] = False
    if change == 'duplicate': transport.relations.append(copy.deepcopy(transport.relations[0]))
    assert module.preflight(config(), transport)['status'] == 'fail'


@pytest.mark.parametrize('change', ['synthetic', 'missing_send', 'wrong_readback', 'wrong_prompt', 'missing_case', 'no_history'])
def test_missing_or_unlinked_live_evidence_cannot_pass(change):
    module = api()
    value = evidence('synthetic' if change == 'synthetic' else 'live-api')
    if change == 'missing_send': del value['records'][0]['send']
    if change == 'wrong_readback': value['records'][0]['readback']['message_id'] = 'different'
    if change == 'wrong_prompt': value['records'][0]['prompt'] = '别的测试'
    if change == 'missing_case': value['records'] = []
    if change == 'no_history': del value['records'][0]['readback']['messages']
    assert module.evaluate(config(), value)['status'] != 'pass'


def test_evaluation_checks_content_terminal_expert_and_preserves_trace():
    module = api()
    report = module.evaluate(config(), evidence())
    assert report['status'] == 'pass'
    assert report['evidence_origin'] == 'imported'
    assert report['cases'][0]['evidence']['session_id'] == 's1'
    assert report['cases'][0]['evidence']['trace_id'] == 't1'
    assert 'private-user' not in json.dumps(report)
    for key, value in [('response', '写入成功'), ('terminal_status', 'running'), ('expert_nid', 'wrong')]:
        changed = evidence()
        changed['records'][0][key] = value
        assert module.evaluate(config(), changed)['status'] == 'fail'


def test_missing_declared_prerequisite_is_unverified():
    module = api()
    settings = config()
    settings['cases'][0]['required_evidence_fields'] = ['knowledge_retrieved']
    assert module.evaluate(settings, evidence())['status'] == 'unverified'


def test_live_api_captured_request_links_answer_without_inventing_input_history():
    module = api()
    value = evidence()
    record = value['records'][0]
    record['session_id'] = ''
    record['isolation'] = 'existing-test-assistant-conversation'
    for receipt in (record['send'], record['readback']):
        receipt['session_id'] = ''
    record['readback']['messages'] = [record['readback']['messages'][1]]
    record['readback']['messages'][0]['session_id'] = ''
    record['send']['captured_request'] = {
        'assistant_nid': 'a1', 'prompt': record['prompt'], 'input_chat_nid': 'input1',
        'answer_chat_nid': 'm1', 'trace_id': 't1'}
    result = module.evaluate(config(), value)
    assert result['status'] == 'pass'
    assert result['cases'][0]['input_persisted'] is False
    assert result['cases'][0]['session_isolation']['status'] == 'unverified'
    record['readback']['messages'][0]['trace_id'] = 'mismatched'
    assert module.evaluate(config(), value)['status'] != 'pass'


def test_report_uses_shared_sanitizer_and_private_atomic_files(tmp_path):
    module = api()
    report = {'status': 'unverified', 'session_id': 's1', 'userNid': 'private-user',
              'message': 'Authorization: secret', 'token': 'token-value'}
    paths = module.write_reports(tmp_path / 'report', report)
    for path in paths.values():
        path = Path(path)
        assert path.stat().st_mode & 0o777 == 0o600
        assert 'private-user' not in path.read_text()
        assert 'token-value' not in path.read_text()
        assert 's1' in path.read_text()


@pytest.mark.parametrize('readback', [None, [], {'messages': None}])
def test_malformed_readback_is_unverified_instead_of_crashing(readback):
    value = evidence()
    value['records'][0]['readback'] = readback
    assert api().evaluate(config(), value)['status'] == 'unverified'


def test_preflight_transport_failure_after_identity_is_safe_failure():
    class BrokenTransport(ReadTransport):
        def request(self, method, path, **kwargs):
            if path.endswith('agentFullConfig'):
                raise RuntimeError('Authorization: private-secret')
            return super().request(method, path, **kwargs)
    result = api().preflight(config(), BrokenTransport())
    assert result['status'] == 'fail'
    assert 'private-secret' not in json.dumps(result)
