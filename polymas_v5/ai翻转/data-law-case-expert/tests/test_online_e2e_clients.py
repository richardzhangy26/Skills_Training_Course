"""协议样本全部为 synthetic；无真实网络、凭证或身份。"""
from __future__ import annotations

import copy
import importlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from online_e2e.config_diff import snapshot_config, summarize_differences, compare_configs
from online_e2e.contracts import ConfirmationBinding
from online_e2e.safety import ConfirmationTokenManager


def module(name):
    try:
        return importlib.import_module('online_e2e.' + name)
    except ModuleNotFoundError:
        return None


def synthetic_config():
    return {
        'basicInfo': {'nid': 'synthetic-page', 'appName': '合成专家', 'appType': 'EXPERT',
                      'isPublish': 1, 'categoryNid': 'synthetic-category', 'llmModel': 'synthetic-model'},
        'expertMd': {'templateNid': 'synthetic-template', 'customContent': '原始正文'},
        'agentMd': None, 'soulMd': None, 'planMd': None, 'personaMd': None,
        'skillInfoList': [
            {'skillNid': 'z-skill', 'name': 'z', 'enabled': True, 'version': '1.0.0',
             'bindingSource': 'synthetic', 'permission': {'read': True}},
            {'skillNid': 'a-skill', 'name': 'a', 'enabled': False, 'version': '2.0.0',
             'bindingSource': 'synthetic', 'permission': {'write': False}}],
        'subAgentVOS': [], 'mcpInfoList': [], 'datasets': None, 'generalSetting': {},
        'agentLlmModelConfig': {}, 'extInfo': {},
    }


class SyntheticTransport:
    """仅模拟可注入 transport 边界，不声称源于 CDP 录制。"""
    def __init__(self):
        self.calls = []
        self.config = synthetic_config()
        self.bindings = []
        self.write_timeout = False
        self.apply_write = True
        self.response_override = None
        self.write_response_override = None

    def request(self, method, path, *, params=None, json=None, files=None):
        self.calls.append((method, path, copy.deepcopy(params), copy.deepcopy(json)))
        if self.response_override is not None:
            return self.response_override
        if path.endswith('/preview'):
            data = {'nid': 'synthetic-page', 'previewType': 'EXPERT',
                    'basicInfo': {'agentName': '合成专家'}}
        elif path.endswith('/agentFullConfig'):
            data = copy.deepcopy(self.config)
        elif path.endswith('/bind/list'):
            data = copy.deepcopy(self.bindings)
        elif path.endswith('/saveAssistant'):
            if self.apply_write:
                self.config['expertMd']['customContent'] = json['agentSettingConfig']['expertMdCustomContent']
                lookup = {s['skillNid']: s for s in self.config['skillInfoList']}
                self.config['skillInfoList'] = [lookup[s['skillNid']] for s in json['skillInfoList']]
            if self.write_timeout:
                raise TimeoutError('Authorization: synthetic-secret')
            if self.write_response_override is not None:
                return self.write_response_override
            data = True
        elif path.endswith('/unbind'):
            self.bindings = [b for b in self.bindings if b != {k: v for k, v in json.items() if k != 'agentNid'}]
            data = True
        elif path.endswith('/bind'):
            self.bindings.append({k: v for k, v in json.items() if k != 'agentNid'})
            data = True
        else:
            data = {'sessionId': 'synthetic-session', 'messageId': 'synthetic-message'}
        return {'code': 200, 'msg': 'ok', 'data': data}

    def stream(self, method, path, *, json):
        self.calls.append((method, path, None, json))
        yield b'data: {"sessionId":"synthetic-session","text":"hello"}\n\n'
        yield b'data: [DONE]\n\n'


class ClientTests(unittest.TestCase):
    def setUp(self):
        self.clients = module('clients')
        self.assertIsNotNone(self.clients, '需要实现 clients 模块')
        self.transport = SyntheticTransport()
        self.manager = ConfirmationTokenManager(secret=b'synthetic-secret-manager')
        profiles = module('profiles')
        save_profile = profiles.SaveProfile(True, 'synthetic',
            lambda config: config['basicInfo']['llmModel'], ('appName', 'appType', 'categoryNid'))
        self.client = self.clients.PdsClient(self.transport, confirmation_manager=self.manager,
                                            user_nid='synthetic-memory-user', save_profile=save_profile)

    def confirmation(self, before, desired, request_digest='synthetic-diff'):
        binding = ConfirmationBinding('synthetic-page', before.digest, desired.digest,
                                      'synthetic-knowledge-v1', request_digest, 'synthetic-nonce')
        return self.clients.WriteConfirmation(self.manager.issue(binding), binding)

    def save_confirmation(self, before, desired, config=None, operation='save_and_publish'):
        config = config or desired.normalized['full_config']
        if operation == 'restore':
            digest = self.client.restore_request_digest('synthetic-page', desired)
        else:
            digest = self.client.save_and_publish_request_digest('synthetic-page', config)
        return self.confirmation(before, desired, digest)

    def test_snapshot_preserves_null_metadata_and_skill_order(self):
        snap = self.client.snapshot('synthetic-page')
        self.assertEqual(snap.normalized['runtime_agent_nid'], 'synthetic-page')
        self.assertEqual(snap.normalized['skill_order'], ('z-skill', 'a-skill'))
        self.assertEqual([s['nid'] for s in snap.normalized['skills']], ['a-skill', 'z-skill'])
        self.assertIsNone(snap.normalized['full_config']['datasets'])
        self.assertTrue(snap.normalized['full_config']['skillInfoList'][0]['permission']['read'])
        self.assertNotIn('synthetic-memory-user', snap.canonical_json)

    def test_snapshot_rejects_conflicting_upstream_nid_alias(self):
        self.transport.config['skillInfoList'][0]['nid'] = 'conflicting-nid'
        with self.assertRaises(self.clients.ClientError) as error:
            self.client.snapshot('synthetic-page')
        self.assertEqual(error.exception.code, 'CONTRACT_CHANGED')

    def test_runtime_resolution_rejects_conflicting_identity(self):
        self.transport.config['basicInfo']['nid'] = 'another-synthetic-page'
        with self.assertRaises(self.clients.ClientError) as error:
            self.client.runtime_agent_nid('synthetic-page')
        self.assertEqual(error.exception.code, 'CONTRACT_CHANGED')

    def test_envelope_and_missing_fields_fail_closed_without_secret(self):
        for envelope in ({'code': 200, 'data': {}}, {'code': 401, 'msg': 'Authorization: synthetic-secret'}):
            self.transport.response_override = envelope
            with self.assertRaises(self.clients.ClientError) as error:
                self.client.snapshot('synthetic-page')
            self.assertNotIn('synthetic-secret', str(error.exception))

    def test_envelope_accepts_numeric_string_codes(self):
        transport = module('transport')
        self.assertEqual(transport.envelope_data({'code': '200', 'data': 'ok'}, 'read'), 'ok')
        for code in ('401', '403'):
            with self.assertRaises(self.clients.ClientError) as error:
                transport.envelope_data({'code': code, 'data': None}, 'read')
            self.assertEqual(error.exception.code, 'AUTH_REQUIRED')

    def test_save_is_single_publish_and_roundtrip_verified(self):
        before = self.client.snapshot('synthetic-page')
        desired = synthetic_config()
        desired['expertMd']['customContent'] = '新正文'
        expected = self.client.snapshot_from_config('synthetic-page', desired, [])
        result = self.client.save_and_publish('synthetic-page', desired,
            confirmation=self.save_confirmation(before, expected, desired))
        self.assertEqual(result.digest, expected.digest)
        writes = [c for c in self.transport.calls if c[1].endswith('/saveAssistant')]
        self.assertEqual(len(writes), 1)
        body = writes[0][3]
        self.assertEqual(body['isPublish'], 1)
        self.assertEqual(body['assistantNid'], 'synthetic-page')
        self.assertEqual(body['userNid'], 'synthetic-memory-user')
        self.assertEqual(body['skillInfoList'][1]['isEnable'], 'DISABLE')
        self.assertEqual(body['skillInfoList'][0]['version'], '')

    def test_save_confirmation_binds_operation_and_every_request_field(self):
        before = self.client.snapshot('synthetic-page')
        desired = synthetic_config()
        desired['basicInfo']['appName'] = '变更后名称'
        expected = self.client.snapshot_from_config('synthetic-page', desired, [])
        original_body_digest = self.client.save_and_publish_request_digest('synthetic-page', synthetic_config())
        wrong = self.confirmation(before, expected, original_body_digest)
        with self.assertRaises(self.clients.ClientError) as error:
            self.client.save_and_publish('synthetic-page', desired, confirmation=wrong)
        self.assertEqual(error.exception.code, 'CONFIRMATION_INVALID')
        self.assertFalse(any(c[1].endswith('/saveAssistant') for c in self.transport.calls))

    def test_bind_and_unbind_confirmations_are_not_interchangeable(self):
        self.transport.bindings = [{'knowledgeBaseNid': 'synthetic-kb', 'knowledgeType': 'synthetic-type'}]
        before = self.client.snapshot('synthetic-page')
        expected = self.client.snapshot_from_config('synthetic-page', synthetic_config(), [])
        bind_digest = self.client.knowledge_binding_request_digest(
            'synthetic-page', 'synthetic-kb', 'synthetic-type', bind=True)
        wrong = self.confirmation(before, expected, bind_digest)
        with self.assertRaises(self.clients.ClientError) as error:
            self.client.bind_knowledge('synthetic-page', 'synthetic-kb', 'synthetic-type',
                                       bind=False, confirmation=wrong)
        self.assertEqual(error.exception.code, 'CONFIRMATION_INVALID')
        self.assertFalse(any(c[1].endswith('/unbind') for c in self.transport.calls))

    def test_all_pds_write_operation_digests_are_domain_separated(self):
        snapshot = self.client.snapshot('synthetic-page')
        digests = {
            self.client.save_and_publish_request_digest('synthetic-page', synthetic_config()),
            self.client.restore_request_digest('synthetic-page', snapshot),
            self.client.knowledge_binding_request_digest(
                'synthetic-page', 'synthetic-kb', 'synthetic-type', bind=True),
            self.client.knowledge_binding_request_digest(
                'synthetic-page', 'synthetic-kb', 'synthetic-type', bind=False),
        }
        self.assertEqual(len(digests), 4)
        self.assertNotEqual(
            self.client.save_and_publish_request_digest('synthetic-page', synthetic_config()),
            self.client.restore_request_digest('synthetic-page', snapshot),
        )

    def test_restore_requires_restore_operation_digest_not_save_digest(self):
        original = self.client.snapshot('synthetic-page')
        self.transport.config['expertMd']['customContent'] = '修改后'
        current = self.client.snapshot('synthetic-page')
        save_digest = self.client.save_and_publish_request_digest(
            'synthetic-page', original.normalized['full_config'])
        wrong = self.confirmation(current, original, save_digest)
        with self.assertRaises(self.clients.ClientError) as error:
            self.client.restore('synthetic-page', original, confirmation=wrong)
        self.assertEqual(error.exception.code, 'CONFIRMATION_INVALID')
        self.assertFalse(any(c[1].endswith('/saveAssistant') for c in self.transport.calls))

    def test_noop_save_and_bind_do_not_send_or_consume_confirmation(self):
        before = self.client.snapshot('synthetic-page')
        confirmation = self.save_confirmation(before, before)
        calls = len(self.transport.calls)
        self.assertEqual(self.client.save_and_publish('synthetic-page', synthetic_config(),
                                                      confirmation=confirmation), before)
        self.assertEqual(len(self.transport.calls), calls + 3)  # 只做发送前快照回读
        self.transport.bindings = [{'knowledgeBaseNid': 'synthetic-kb', 'knowledgeType': 'synthetic-type'}]
        bound = self.client.snapshot('synthetic-page')
        bind_confirmation = self.confirmation(bound, bound,
            self.client.knowledge_binding_request_digest('synthetic-page', 'synthetic-kb', 'synthetic-type'))
        calls = len(self.transport.calls)
        self.assertEqual(self.client.bind_knowledge('synthetic-page', 'synthetic-kb', 'synthetic-type',
                                                    confirmation=bind_confirmation), bound)
        self.assertEqual(len(self.transport.calls), calls + 3)
        # no-op 不消费令牌；状态变化后还可用于原精确请求。
        self.assertTrue(self.manager.consume(confirmation.token, confirmation.binding))

    def test_bool_or_forged_confirmation_never_writes(self):
        for invalid in (True, object(), self.clients.WriteConfirmation('forged',
                ConfirmationBinding('synthetic-page', 'a', 'b', 'c', 'd', 'e'))):
            with self.assertRaises(self.clients.ClientError):
                self.client.save_and_publish('synthetic-page', synthetic_config(), confirmation=invalid)
        self.assertFalse(any(c[1].endswith('/saveAssistant') for c in self.transport.calls))

    def test_confirmation_bound_to_fresh_snapshot_and_desired_content(self):
        before = self.client.snapshot('synthetic-page')
        desired = synthetic_config()
        confirm = self.save_confirmation(before, before)
        desired['expertMd']['customContent'] = '没有确认的内容'
        with self.assertRaises(self.clients.ClientError) as error:
            self.client.save_and_publish('synthetic-page', desired, confirmation=confirm)
        self.assertEqual(error.exception.code, 'CONFIRMATION_INVALID')

    def test_write_timeout_reads_back_and_never_retries(self):
        before = self.client.snapshot('synthetic-page')
        desired = synthetic_config()
        desired['expertMd']['customContent'] = '超时但已写入'
        expected = self.client.snapshot_from_config('synthetic-page', desired, [])
        self.transport.write_timeout = True
        result = self.client.save_and_publish('synthetic-page', desired,
            confirmation=self.save_confirmation(before, expected, desired))
        self.assertEqual(result.digest, expected.digest)
        self.assertEqual(sum(c[1].endswith('/saveAssistant') for c in self.transport.calls), 1)

    def test_unresolved_timeout_is_unknown_not_success_and_not_retried(self):
        before = self.client.snapshot('synthetic-page')
        desired = synthetic_config()
        desired['expertMd']['customContent'] = '未提交成功'
        expected = self.client.snapshot_from_config('synthetic-page', desired, [])
        self.transport.write_timeout = True
        self.transport.apply_write = False
        with self.assertRaises(self.clients.ClientError) as error:
            self.client.save_and_publish('synthetic-page', desired,
                confirmation=self.save_confirmation(before, expected, desired))
        self.assertEqual(error.exception.code, 'WRITE_STATE_UNKNOWN')
        self.assertNotIn('synthetic-secret', str(error.exception))
        self.assertEqual(sum(c[1].endswith('/saveAssistant') for c in self.transport.calls), 1)

    def test_definite_save_rejection_is_not_hidden_by_matching_readback(self):
        before = self.client.snapshot('synthetic-page')
        desired = synthetic_config()
        desired['expertMd']['customContent'] = '服务端写入但信封拒绝'
        expected = self.client.snapshot_from_config('synthetic-page', desired, [])
        self.transport.write_response_override = {'code': '401', 'msg': 'denied', 'data': None}
        calls = len(self.transport.calls)
        with self.assertRaises(self.clients.ClientError) as error:
            self.client.save_and_publish('synthetic-page', desired,
                confirmation=self.save_confirmation(before, expected, desired))
        self.assertEqual(error.exception.code, 'AUTH_REQUIRED')
        self.assertEqual(len(self.transport.calls), calls + 4)  # 三项写前快照 + 一次写入
        self.assertTrue(self.transport.calls[-1][1].endswith('/saveAssistant'))
        self.assertEqual(sum(c[1].endswith('/saveAssistant') for c in self.transport.calls), 1)

    def test_restore_and_bind_are_confirmed_and_read_back(self):
        before = self.client.snapshot('synthetic-page')
        desired = self.client.snapshot_from_config('synthetic-page', synthetic_config(),
            [{'knowledgeBaseNid': 'synthetic-kb', 'knowledgeType': 'synthetic-type'}])
        result = self.client.bind_knowledge('synthetic-page', 'synthetic-kb', 'synthetic-type',
            confirmation=self.confirmation(before, desired,
                self.client.knowledge_binding_request_digest('synthetic-page', 'synthetic-kb', 'synthetic-type')))
        self.assertEqual(result.digest, desired.digest)
        # 恢复仅配置；知识绑定差异需要独立确认，不隐式跨域恢复。
        with self.assertRaises(self.clients.ClientError) as error:
            self.client.restore('synthetic-page', before,
                confirmation=self.save_confirmation(result, before, operation='restore'))
        self.assertEqual(error.exception.code, 'DEPENDENCY_UNVERIFIED')

    def test_default_teaching_operations_are_unverified_and_do_not_send(self):
        teaching = self.clients.TeachingCenterClient(self.transport)
        for operation in ('create_session', 'upload_file', 'send_message',
                          'confirm', 'resume', 'history'):
            with self.assertRaises(self.clients.ClientError) as error:
                result = getattr(teaching, operation)({})
                if operation == 'send_message':
                    list(result)
            self.assertEqual(error.exception.code, 'DEPENDENCY_UNVERIFIED')
        self.assertEqual(self.transport.calls, [])

    def test_explicit_synthetic_teaching_profile_checks_request_and_response(self):
        profiles = module('profiles')
        endpoint = profiles.Endpoint('POST', '/synthetic/session', verified=True,
            provenance='synthetic', request_fields=('assistantNid',), response_fields=('sessionId',))
        profile = profiles.EndpointProfile({'create_session': endpoint})
        teaching = self.clients.TeachingCenterClient(self.transport, profile=profile,
            confirmation_manager=self.manager, target_id='synthetic-page', snapshot_digest='synthetic-baseline')
        payload = {'assistantNid': 'synthetic-assistant'}
        digest = self.clients.teaching_request_digest('create_session', payload)
        binding = ConfirmationBinding('synthetic-page', 'synthetic-baseline', digest, 'v1', digest, 'nonce')
        confirmation = self.clients.WriteConfirmation(self.manager.issue(binding), binding)
        self.assertEqual(teaching.create_session(payload, confirmation=confirmation)['sessionId'], 'synthetic-session')
        with self.assertRaises(self.clients.ClientError):
            teaching.create_session(payload, confirmation=confirmation)
        with self.assertRaises(self.clients.ClientError):
            teaching.create_session({'guessedField': 'no'})
        self.assertEqual(len(self.transport.calls), 1)

    def test_default_save_profile_blocks_without_writing(self):
        client = self.clients.PdsClient(self.transport, confirmation_manager=self.manager,
                                       user_nid='synthetic-memory-user')
        with self.assertRaises(self.clients.ClientError) as error:
            client.save_and_publish('synthetic-page', synthetic_config(), confirmation=True)
        self.assertEqual(error.exception.code, 'DEPENDENCY_UNVERIFIED')
        self.assertEqual(self.transport.calls, [])

    def test_draft_desired_config_never_publishes_implicitly(self):
        desired = synthetic_config()
        desired['basicInfo']['isPublish'] = 0
        with self.assertRaises(self.clients.ClientError) as error:
            self.client.save_and_publish('synthetic-page', desired, confirmation=True)
        self.assertEqual(error.exception.code, 'CONTRACT_CHANGED')
        self.assertFalse(any(c[1].endswith('/saveAssistant') for c in self.transport.calls))

    def test_teaching_stream_failure_is_unknown_and_does_not_leak(self):
        profiles = module('profiles')
        profile = profiles.EndpointProfile({'send_message': profiles.Endpoint(
            'POST', '/synthetic/send', True, 'synthetic', ('message',))})
        teaching = self.clients.TeachingCenterClient(self.transport, profile=profile,
            confirmation_manager=self.manager, target_id='synthetic-page', snapshot_digest='baseline')
        payload = {'message': '合成测试'}
        binding = ConfirmationBinding('synthetic-page', 'baseline',
            self.clients.teaching_request_digest('send_message', payload), 'v1',
            self.clients.teaching_request_digest('send_message', payload), 'nonce')
        confirmation = self.clients.WriteConfirmation(self.manager.issue(binding), binding)
        def broken_stream(*args, **kwargs):
            raise TimeoutError('Authorization: synthetic-secret')
        self.transport.stream = broken_stream
        with self.assertRaises(self.clients.ClientError) as error:
            list(teaching.send_message(payload, confirmation=confirmation))
        self.assertEqual(error.exception.code, 'WRITE_STATE_UNKNOWN')
        self.assertNotIn('synthetic-secret', str(error.exception))

    def test_snapshots_do_not_persist_binding_credentials(self):
        self.transport.bindings = [{'knowledgeBaseNid': 'synthetic-kb', 'token': 'hidden-secret'}]
        with self.assertRaises(self.clients.ClientError):
            self.client.snapshot('synthetic-page')

    def test_select_assistant_exact_match_and_ambiguity(self):
        records = [{'friendNid': 'synthetic-assistant', 'friendNickName': '中药材',
                    'appType': 'AUTO_SMART_ROBOT', 'appCategory': 'AI_COURSE_REPRESENTATIVE', 'isV5': True}]
        select = self.clients.select_unique_assistant
        self.assertEqual(select(records, 'synthetic-assistant', '中药材 AI助教')['friendNid'], 'synthetic-assistant')
        for bad in ([], records + records, [{**records[0], 'friendNickName': '中药材二班'}],
                    [{**records[0], 'friendNid': 'same-name-other-assistant'}],
                    records + [{**records[0], 'friendNickName': '伪装的重复 NID'}]):
            with self.assertRaises(self.clients.ClientError):
                select(bad, 'synthetic-assistant', '中药材 AI助教')

    def test_resolve_expert_relationship_requires_exact_identity_and_version(self):
        teaching = self.clients.TeachingCenterClient(self.transport)
        self.transport.response_override = {'code': 200, 'data': {
            'basicInfo': {'nid': 'synthetic-assistant', 'appName': '中药材'},
            'subAgentVOS': [{'agentNid': 'synthetic-page', 'name': '合成专家', 'enabled': True, 'version': '6'}]}}
        result = teaching.resolve_relationship({'agentNid': 'synthetic-assistant'},
                                               expert_nid='synthetic-page', expected_version='6')
        self.assertEqual(result['expert_nid'], 'synthetic-page')
        self.assertEqual(result['assistant_nid'], 'synthetic-assistant')
        with self.assertRaises(self.clients.ClientError) as error:
            teaching.resolve_relationship({'agentNid': 'synthetic-assistant'},
                                           expert_nid='synthetic-page', expected_version='7')
        self.assertEqual(error.exception.code, 'BOUND_VERSION_MISMATCH')

    def test_confirmation_cannot_be_reused_after_actual_write(self):
        before = self.client.snapshot('synthetic-page')
        desired = synthetic_config()
        desired['expertMd']['customContent'] = '第一次真实发送'
        expected = self.client.snapshot_from_config('synthetic-page', desired, [])
        confirmation = self.save_confirmation(before, expected, desired)
        result = self.client.save_and_publish('synthetic-page', desired, confirmation=confirmation)
        self.assertEqual(result.digest, expected.digest)
        self.transport.config = synthetic_config()
        with self.assertRaises(self.clients.ClientError):
            self.client.save_and_publish('synthetic-page', desired, confirmation=confirmation)

    def test_unverified_write_endpoint_is_blocked_not_confused_with_satisfied_state(self):
        profiles = module('profiles')
        endpoints = dict(profiles.PDS_PROFILE.endpoints)
        endpoints['save_and_publish'] = profiles.Endpoint()
        self.client._profile = profiles.EndpointProfile(endpoints)
        before = self.client.snapshot('synthetic-page')
        with self.assertRaises(self.clients.ClientError) as error:
            self.client.save_and_publish('synthetic-page', synthetic_config(),
                                         confirmation=self.save_confirmation(before, before))
        self.assertEqual(error.exception.code, 'DEPENDENCY_UNVERIFIED')

    def test_teaching_missing_response_after_write_is_unknown(self):
        profiles = module('profiles')
        profile = profiles.EndpointProfile({'create_session': profiles.Endpoint(
            'POST', '/synthetic/session', True, 'synthetic', (), ('sessionId',))})
        teaching = self.clients.TeachingCenterClient(self.transport, profile=profile,
            confirmation_manager=self.manager, target_id='synthetic-page', snapshot_digest='baseline')
        binding = ConfirmationBinding('synthetic-page', 'baseline',
            self.clients.teaching_request_digest('create_session', {}), 'v1',
            self.clients.teaching_request_digest('create_session', {}), 'nonce')
        self.transport.response_override = {'code': 200, 'data': {}}
        with self.assertRaises(self.clients.ClientError) as error:
            teaching.create_session({}, confirmation=self.clients.WriteConfirmation(self.manager.issue(binding), binding))
        self.assertEqual(error.exception.code, 'WRITE_STATE_UNKNOWN')

    def test_teaching_confirmation_requires_request_digest_in_shared_diff_binding(self):
        profiles = module('profiles')
        profile = profiles.EndpointProfile({'create_session': profiles.Endpoint(
            'POST', '/synthetic/session', True, 'synthetic', (), ('sessionId',))})
        teaching = self.clients.TeachingCenterClient(self.transport, profile=profile,
            confirmation_manager=self.manager, target_id='synthetic-page', snapshot_digest='baseline')
        digest = self.clients.teaching_request_digest('create_session', {})
        binding = ConfirmationBinding('synthetic-page', 'baseline', digest, 'v1',
                                      'digest-from-another-operation', 'nonce')
        with self.assertRaises(self.clients.ClientError) as error:
            teaching.create_session({}, confirmation=self.clients.WriteConfirmation(
                self.manager.issue(binding), binding))
        self.assertEqual(error.exception.code, 'CONFIRMATION_INVALID')
        self.assertEqual(self.transport.calls, [])

    def test_teaching_upload_digest_binds_content_and_metadata(self):
        digest = self.clients.teaching_request_digest
        first = digest('upload_file', {}, files={'file': ('synthetic.txt', b'one', 'text/plain')})
        second = digest('upload_file', {}, files={'file': ('synthetic.txt', b'two', 'text/plain')})
        self.assertNotEqual(first, second)
        with self.assertRaises(self.clients.ClientError):
            digest('upload_file', {}, files={'file': object()})

    def test_missing_teacher_role_is_not_granted_by_display_name(self):
        validate = self.clients.require_role
        self.assertTrue(validate({'roleList': [{'roleCode': 'school_teacher'}]}, 'school_teacher'))
        with self.assertRaises(self.clients.ClientError):
            validate({'roleList': [{'roleName': '教师', 'roleCode': 'school_student'}]}, 'school_teacher')

    def test_current_user_identity_is_available_only_on_explicit_memory_read(self):
        self.transport.response_override = {'code': 200, 'data': {
            'userNid': 'synthetic-private-user', 'roleList': [{'roleCode': 'school_teacher'}], 'token': 'hidden'}}
        teaching = self.clients.TeachingCenterClient(self.transport)
        result = teaching.current_user()
        self.assertEqual(result['userNid'], 'synthetic-private-user')
        self.assertNotIn('hidden', repr(result))


class SSETests(unittest.TestCase):
    def setUp(self):
        self.sse = module('sse')
        self.assertIsNotNone(self.sse, '需要实现 sse 模块')

    def test_bytewise_utf8_crlf_multiline_heartbeat_id_done_and_redaction(self):
        raw = (': heartbeat\r\nid: evt-1\r\nevent: delta\r\ndata: {"text":"你好",\r\n'
               'data: "sessionId":"synthetic-session","messageId":"synthetic-message",'
               '"planId":"synthetic-plan","traceId":"synthetic-trace","token":"hidden"}\r\n\r\n'
               'data: [DONE]\r\n\r\n').encode()
        events = list(self.sse.parse_sse(bytes([byte]) for byte in raw))
        self.assertEqual(events[0].event, 'delta')
        self.assertEqual(events[0].id, 'evt-1')
        self.assertEqual(events[0].data['text'], '你好')
        self.assertEqual(events[0].data['sessionId'], 'synthetic-session')
        self.assertEqual(events[0].data['planId'], 'synthetic-plan')
        self.assertNotIn('hidden', repr(events))
        self.assertTrue(events[-1].terminal)

    def test_json_fragment_is_preserved_and_named_end_is_terminal(self):
        events = list(self.sse.parse_sse([b'data: {"text":\n\nevent: end\ndata: {}\n\n']))
        self.assertEqual(events[0].data, '{"text":')
        self.assertTrue(events[-1].terminal)

    def test_invalid_utf8_and_unterminated_stream_are_structured_errors(self):
        clients = module('clients')
        for raw in (b'data: \xff\n\n', b'data: {"text":"no end"}\n\n'):
            with self.assertRaises(clients.ClientError) as error:
                list(self.sse.parse_sse([raw]))
            self.assertEqual(error.exception.code, 'CONTRACT_CHANGED')

    def test_event_only_end_is_terminal_and_nested_ids_survive(self):
        raw = b'data: {"nested":{"sessionId":"synthetic-session","authorization":"hidden"}}\n\nevent: end\n\n'
        events = list(self.sse.parse_sse([raw]))
        self.assertEqual(events[0].data['nested']['sessionId'], 'synthetic-session')
        self.assertNotIn('hidden', repr(events))
        self.assertTrue(events[-1].terminal)

    def test_profile_defined_terminal_status_and_size_limit(self):
        events = list(self.sse.parse_sse([b'data: {"status":"completed"}\n\n'],
            terminal_statuses=('completed',)))
        self.assertTrue(events[-1].terminal)
        clients = module('clients')
        with self.assertRaises(clients.ClientError):
            list(self.sse.parse_sse([b'data: too-long\n\n'], max_event_chars=3))

    def test_sse_does_not_retain_authenticated_person_identity(self):
        events = list(self.sse.parse_sse([
            b'data: {"userNid":"synthetic-private-user","studentId":"synthetic-private-student",'
            b'"fromUserNid":"synthetic-from","ToUserNID":"synthetic-to",'
            b'"SENDERUSERID":"synthetic-sender","receiverStudentNid":"synthetic-receiver"}\n\ndata: [DONE]\n\n']))
        self.assertNotIn('synthetic-private-user', repr(events))
        self.assertNotIn('synthetic-private-student', repr(events))
        for secret in ('synthetic-from', 'synthetic-to', 'synthetic-sender', 'synthetic-receiver'):
            self.assertNotIn(secret, repr(events))


if __name__ == '__main__':
    unittest.main()
