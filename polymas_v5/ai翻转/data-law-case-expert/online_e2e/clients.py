"""PDS 配置与教学中心客户端；任何未知协议或写入结果均显式阻断。"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import hashlib
import json
from typing import Any

from .config_diff import snapshot_config
from .contracts import ConfigSnapshot, ConfirmationBinding
from .profiles import EndpointProfile, PDS_PROFILE, TEACHING_PROFILE, SaveProfile
from .safety import ConfirmationTokenManager, redact_sensitive
from .sse import parse_sse, safe_event_data
from .transport import ClientError, Transport, envelope_data


def _plain(value):
    if isinstance(value, Mapping):
        return {k: _plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(v) for v in value]
    return value


def _require_fields(value, fields, operation):
    if not isinstance(value, Mapping) or any(field not in value for field in fields):
        raise ClientError('CONTRACT_CHANGED', operation, '字段缺失或类型变化')


def _identifier(value, operation):
    if not isinstance(value, str) or not value.strip():
        raise ClientError('CONTRACT_CHANGED', operation, '标识缺失')
    return value


@dataclass(frozen=True, repr=False)
class WriteConfirmation:
    """签名令牌和不可变绑定；仅传入 True 或任意对象无法授权。"""
    token: str
    binding: ConfirmationBinding


def teaching_request_digest(operation: str, payload: Mapping, *, files=None) -> str:
    """请求语义摘要；文件用名称、MIME、内容哈希绑定，不保存文件内容。"""
    file_digests = {}
    if files is not None:
        if not isinstance(files, Mapping):
            raise ClientError('CONTRACT_CHANGED', operation, '文件参数类型无效')
        for field, item in files.items():
            if (not isinstance(item, tuple) or len(item) != 3
                    or not isinstance(item[0], str) or not isinstance(item[1], bytes)
                    or not isinstance(item[2], str)):
                raise ClientError('CONTRACT_CHANGED', operation, '文件须包含名称、字节内容与 MIME')
            file_digests[field] = {'name': item[0], 'sha256': hashlib.sha256(item[1]).hexdigest(), 'mime': item[2]}
    return snapshot_config({'operation': operation, 'payload': payload, 'files': file_digests}).digest


def require_role(user: Mapping, role_code: str) -> bool:
    _require_fields(user, ('roleList',), 'current_user')
    if not isinstance(user['roleList'], list):
        raise ClientError('CONTRACT_CHANGED', 'current_user', '角色列表类型变化')
    for role in user['roleList']:
        _require_fields(role, ('roleCode',), 'current_user')
    if role_code not in {role['roleCode'] for role in user['roleList']}:
        raise ClientError('ROLE_NOT_AUTHORIZED', 'current_user')
    return True


def select_unique_assistant(records: list, display_name: str) -> dict:
    """只允许确定的 UI 后缀归一化，不使用包含/模糊匹配。"""
    if not isinstance(records, list):
        raise ClientError('CONTRACT_CHANGED', 'assistants', '列表类型变化')
    name = display_name.removesuffix(' AI助教')
    matches = []
    for record in records:
        _require_fields(record, ('friendNid', 'friendNickName', 'appType', 'appCategory', 'isV5'), 'assistants')
        if (record['friendNickName'] == name and record['appType'] == 'AUTO_SMART_ROBOT'
                and record['appCategory'] == 'AI_COURSE_REPRESENTATIVE' and record['isV5'] is True):
            _identifier(record['friendNid'], 'assistants')
            matches.append(record)
    if len(matches) != 1:
        raise ClientError('CONTRACT_CHANGED', 'assistants', '目标不存在或不唯一')
    return matches[0]


class _Client:
    def __init__(self, transport: Transport, profile: EndpointProfile):
        self._transport = transport
        self._profile = profile

    def _call(self, operation, payload=None, *, files=None):
        endpoint = self._profile.get(operation)
        options = {'params': payload} if endpoint.method == 'GET' else {'json': payload}
        if files is not None:
            options['files'] = files
        try:
            result = self._transport.request(endpoint.method, endpoint.path, **options)
        except Exception:
            raise ClientError('TRANSPORT_ERROR', operation) from None
        return envelope_data(result, operation)


class PdsClient(_Client):
    def __init__(self, transport: Transport, *, confirmation_manager: ConfirmationTokenManager,
                 user_nid: str | None = None, target_id: str | None = None,
                 profile: EndpointProfile = PDS_PROFILE, save_profile: SaveProfile = SaveProfile()):
        super().__init__(transport, profile)
        self._confirmation_manager = confirmation_manager
        self._user_nid = user_nid
        self._target_id = target_id
        self._save_profile = save_profile

    def preview(self, page_nid: str) -> dict:
        _identifier(page_nid, 'preview')
        data = self._call('preview', {'nid': page_nid})
        _require_fields(data, ('nid', 'previewType', 'basicInfo'), 'preview')
        if data['nid'] != page_nid or data['previewType'] != 'EXPERT':
            raise ClientError('CONTRACT_CHANGED', 'preview', '专家目标不一致')
        _require_fields(data['basicInfo'], ('agentName',), 'preview')
        return data

    def full_config(self, page_nid: str) -> dict:
        _identifier(page_nid, 'full_config')
        data = self._call('full_config', {'agentNid': page_nid})
        self._validate_config(page_nid, data)
        return data

    @staticmethod
    def _validate_config(page_nid, data):
        fields = ('basicInfo', 'expertMd', 'agentMd', 'soulMd', 'planMd', 'skillInfoList',
                  'subAgentVOS', 'mcpInfoList', 'datasets', 'generalSetting',
                  'agentLlmModelConfig', 'extInfo')
        _require_fields(data, fields, 'full_config')
        _require_fields(data['basicInfo'], ('nid', 'appName', 'appType', 'isPublish'), 'full_config')
        if data['basicInfo']['nid'] != page_nid or data['basicInfo']['appType'] != 'EXPERT':
            raise ClientError('CONTRACT_CHANGED', 'full_config', '专家标识不唯一或不一致')
        if not isinstance(data['skillInfoList'], (list, tuple)):
            raise ClientError('CONTRACT_CHANGED', 'full_config', 'Skill 列表类型变化')
        nids = []
        for skill in data['skillInfoList']:
            _require_fields(skill, ('skillNid', 'name', 'enabled', 'version', 'bindingSource'), 'full_config')
            nids.append(_identifier(skill['skillNid'], 'full_config'))
            if not isinstance(skill['enabled'], bool):
                raise ClientError('CONTRACT_CHANGED', 'full_config', 'Skill 启用状态类型变化')
        if len(set(nids)) != len(nids):
            raise ClientError('CONTRACT_CHANGED', 'full_config', 'Skill 标识重复')
        for field in ('soulMd', 'agentMd', 'planMd', 'expertMd'):
            if data[field] is not None:
                _require_fields(data[field], ('templateNid', 'customContent'), 'full_config')

    def runtime_agent_nid(self, page_nid: str) -> str:
        preview = self.preview(page_nid)
        config = self.full_config(page_nid)
        identities = {preview['nid'], config['basicInfo']['nid']}
        if len(identities) != 1:
            raise ClientError('CONTRACT_CHANGED', 'runtime_agent_nid', '专家标识不唯一')
        return identities.pop()

    def knowledge_bindings(self, page_nid: str) -> list:
        _identifier(page_nid, 'knowledge_bindings')
        data = self._call('knowledge_bindings', {'agentNid': page_nid})
        if not isinstance(data, list) or any(not isinstance(item, dict) for item in data):
            raise ClientError('CONTRACT_CHANGED', 'knowledge_bindings', '绑定列表类型变化')
        return data

    def snapshot(self, page_nid: str) -> ConfigSnapshot:
        self.preview(page_nid)
        return self.snapshot_from_config(page_nid, self.full_config(page_nid),
                                         self.knowledge_bindings(page_nid))

    @classmethod
    def snapshot_from_config(cls, page_nid: str, full_config: Mapping,
                             knowledge_bindings: list) -> ConfigSnapshot:
        cls._validate_config(page_nid, full_config)
        config = _plain(full_config)
        # 不接收已混入身份/凭证的可恢复配置，不能脱敏后冒充无损快照。
        redacted = redact_sensitive(config)
        bindings = _plain(knowledge_bindings)
        if (redacted != config or redact_sensitive(bindings) != bindings
                or 'userNid' in json.dumps([config, bindings], ensure_ascii=False)):
            raise ClientError('CONTRACT_CHANGED', 'snapshot', '配置混入敏感字段')
        skills = [{'nid': skill['skillNid'], **skill} for skill in config['skillInfoList']]
        source = config['expertMd'] if config['expertMd'] is not None else config['agentMd']
        return snapshot_config({
            'page_nid': page_nid, 'runtime_agent_nid': config['basicInfo']['nid'],
            'agent_md': source['customContent'] if source else None,
            'skills': skills, 'skill_order': [s['skillNid'] for s in config['skillInfoList']],
            'knowledge_bindings': sorted(_plain(knowledge_bindings),
                key=lambda value: json.dumps(value, sort_keys=True, ensure_ascii=False)),
            'full_config': config,
        })

    def _authorize(self, page_nid, before, expected, confirmation):
        if type(confirmation) is not WriteConfirmation or type(confirmation.binding) is not ConfirmationBinding:
            raise ClientError('CONFIRMATION_INVALID', 'write', '确认上下文类型无效')
        binding = confirmation.binding
        if (binding.target_id != (self._target_id or page_nid)
                or binding.snapshot_digest != before.digest
                or binding.expected_digest != expected.digest
                or not binding.knowledge_version or not binding.diff_digest or not binding.nonce
                or not isinstance(confirmation.token, str)
                or not self._confirmation_manager.consume(confirmation.token, binding)):
            raise ClientError('CONFIRMATION_INVALID', 'write', '确认过期、已消费或绑定不一致')

    def _build_save_body(self, page_nid, config):
        profile = self._save_profile
        if (not profile.verified or profile.provenance == 'unverified'
                or profile.normalize_model is None or not profile.basic_fields):
            raise ClientError('DEPENDENCY_UNVERIFIED', 'save_and_publish', '保存模型转换尚未核验')
        if not self._user_nid:
            raise ClientError('AUTH_REQUIRED', 'save_and_publish', '缺少可信认证主体')
        basic = config['basicInfo']
        _require_fields(basic, profile.basic_fields, 'save_and_publish')
        ext = config['extInfo']
        if not isinstance(ext, dict):
            raise ClientError('CONTRACT_CHANGED', 'save_and_publish', 'extInfo 类型变化')
        questions = ext.get('recommendedQuestions', [])
        if not isinstance(questions, list) or any(not isinstance(q, str) for q in questions):
            raise ClientError('CONTRACT_CHANGED', 'save_and_publish', '推荐问题格式变化')
        body = {field: basic[field] for field in profile.basic_fields}
        body.update({field: config[field] for field in ('subAgentVOS', 'mcpInfoList', 'datasets',
                                                       'generalSetting', 'agentLlmModelConfig')})
        try:
            body['llmModel'] = profile.normalize_model(config)
        except Exception:
            raise ClientError('CONTRACT_CHANGED', 'save_and_publish', '模型转换失败') from None
        body.update({'assistantNid': page_nid, 'userNid': self._user_nid, 'isPublish': 1,
            'recommendedQuestions': questions, 'expertiseAreas': ext.get('expertiseAreas', []),
            'teamScene': ext.get('teamScene'),
            'skillInfoList': [{'skillNid': s['skillNid'], 'isEnable': 'ENABLE' if s['enabled'] else 'DISABLE',
                'rule': 1, 'version': '', 'bindingSource': s['bindingSource']} for s in config['skillInfoList']]})
        settings = {}
        for field in ('soulMd', 'agentMd', 'planMd', 'expertMd'):
            source = config[field]
            settings[field + 'Nid'] = source['templateNid'] if source else None
            settings[field + 'CustomContent'] = source['customContent'] if source else None
        body['agentSettingConfig'] = settings
        return body

    def _write_readback(self, operation, page_nid, body, expected):
        self._profile.get(operation)
        uncertain = False
        try:
            self._call(operation, body)
        except ClientError:
            uncertain = True
        try:
            actual = self.snapshot(page_nid)
        except ClientError:
            raise ClientError('WRITE_STATE_UNKNOWN', operation, '回读失败；禁止自动重试') from None
        if actual.digest != expected.digest:
            code = 'WRITE_STATE_UNKNOWN' if uncertain else 'READBACK_MISMATCH'
            raise ClientError(code, operation, '回读与确认目标不一致；禁止自动重试')
        return actual

    def save_and_publish(self, page_nid: str, desired_full_config: Mapping, *,
                         confirmation: WriteConfirmation) -> ConfigSnapshot:
        desired = _plain(desired_full_config)
        self._validate_config(page_nid, desired)
        if desired['basicInfo']['isPublish'] != 1:
            raise ClientError('CONTRACT_CHANGED', 'save_and_publish', '平台只支持保存并发布')
        body = self._build_save_body(page_nid, desired)
        self._profile.get('save_and_publish')
        before = self.snapshot(page_nid)
        expected = self.snapshot_from_config(page_nid, desired, before.normalized['knowledge_bindings'])
        self._authorize(page_nid, before, expected, confirmation)
        return self._write_readback('save_and_publish', page_nid, body, expected)

    def bind_knowledge(self, page_nid: str, knowledge_nid: str, knowledge_type: str, *,
                       bind: bool = True, confirmation: WriteConfirmation) -> ConfigSnapshot:
        _identifier(knowledge_nid, 'bind_knowledge')
        _identifier(knowledge_type, 'bind_knowledge')
        before = self.snapshot(page_nid)
        bindings = _plain(before.normalized['knowledge_bindings'])
        # 列表项的标识契约必须明确，不能靠任意对象的相等性猜绑定状态。
        for item in bindings:
            _require_fields(item, ('knowledgeBaseNid', 'knowledgeType'), 'bind_knowledge')
        key = {'knowledgeBaseNid': knowledge_nid, 'knowledgeType': knowledge_type}
        matches = [item for item in bindings if all(item[k] == v for k, v in key.items())]
        if len(matches) > 1:
            raise ClientError('CONTRACT_CHANGED', 'bind_knowledge', '绑定目标不唯一')
        if bind and not matches:
            bindings.append(key)
        elif not bind:
            bindings = [item for item in bindings if item not in matches]
        expected = self.snapshot_from_config(page_nid, before.normalized['full_config'], bindings)
        operation = 'bind_knowledge' if bind else 'unbind_knowledge'
        self._profile.get(operation)
        self._authorize(page_nid, before, expected, confirmation)
        if expected.digest == before.digest:
            return before
        return self._write_readback(operation, page_nid, {'agentNid': page_nid, **key}, expected)

    def restore(self, page_nid: str, snapshot: ConfigSnapshot, *,
                confirmation: WriteConfirmation) -> ConfigSnapshot:
        if type(snapshot) is not ConfigSnapshot or snapshot.normalized.get('page_nid') != page_nid:
            raise ClientError('CONTRACT_CHANGED', 'restore', '恢复目标不一致')
        current = self.snapshot(page_nid)
        if current.normalized['knowledge_bindings'] != snapshot.normalized['knowledge_bindings']:
            raise ClientError('DEPENDENCY_UNVERIFIED', 'restore', '知识绑定恢复需独立确认；不支持内容级恢复')
        return self.save_and_publish(page_nid, snapshot.normalized['full_config'], confirmation=confirmation)


class TeachingCenterClient(_Client):
    def __init__(self, transport: Transport, *, profile: EndpointProfile = TEACHING_PROFILE,
                 confirmation_manager: ConfirmationTokenManager | None = None,
                 target_id: str | None = None, snapshot_digest: str | None = None):
        super().__init__(transport, profile)
        self._confirmation_manager = confirmation_manager
        self._target_id = target_id
        self._snapshot_digest = snapshot_digest

    def _authorize(self, operation, payload, confirmation, *, files=None):
        if (self._confirmation_manager is None or not self._target_id or not self._snapshot_digest
                or type(confirmation) is not WriteConfirmation
                or type(confirmation.binding) is not ConfirmationBinding):
            raise ClientError('CONFIRMATION_INVALID', operation)
        binding = confirmation.binding
        if (binding.target_id != self._target_id or binding.snapshot_digest != self._snapshot_digest
                or binding.expected_digest != teaching_request_digest(operation, payload, files=files)
                or not binding.knowledge_version or not binding.diff_digest or not binding.nonce
                or not isinstance(confirmation.token, str)
                or not self._confirmation_manager.consume(confirmation.token, binding)):
            raise ClientError('CONFIRMATION_INVALID', operation, '绑定不一致或已经消费')

    def _operation(self, operation, payload, *, files=None, confirmation=None, write=False):
        endpoint = self._profile.get(operation)
        if not isinstance(payload, Mapping) or set(payload) != set(endpoint.request_fields):
            raise ClientError('CONTRACT_CHANGED', operation, '请求字段不匹配已验证契约')
        if write:
            self._authorize(operation, payload, confirmation, files=files)
        try:
            data = self._call(operation, dict(payload), files=files)
            records = data if endpoint.response_list else [data]
            if not isinstance(records, list):
                raise ClientError('CONTRACT_CHANGED', operation, '列表响应类型变化')
            for record in records:
                _require_fields(record, endpoint.response_fields, operation)
        except ClientError as error:
            if write and error.code in ('TRANSPORT_ERROR', 'CONTRACT_CHANGED'):
                raise ClientError('WRITE_STATE_UNKNOWN', operation, '禁止自动重试') from None
            raise
        result = safe_event_data(data)
        if operation == 'current_user':
            # 认证专用只读接口是唯一保留主体的通道，调用方只可在内存使用。
            result['userNid'] = _identifier(data['userNid'], operation)
        return result

    def current_user(self):
        """仅供内存身份校验；调用方不得把返回主体写入报告。"""
        return self._operation('current_user', {})

    def assistants(self, payload):
        return self._operation('assistants', payload)

    def resolve_relationship(self, payload, *, expert_nid: str, expected_version: str | None = None):
        _identifier(expert_nid, 'resolve_relationship')
        data = self._operation('resolve_relationship', payload)
        _require_fields(data['basicInfo'], ('nid', 'appName'), 'resolve_relationship')
        if data['basicInfo']['nid'] != payload['agentNid'] or not isinstance(data['subAgentVOS'], list):
            raise ClientError('CONTRACT_CHANGED', 'resolve_relationship', '助教目标不一致')
        matches = []
        for record in data['subAgentVOS']:
            _require_fields(record, ('agentNid', 'name', 'enabled', 'version'), 'resolve_relationship')
            if record['agentNid'] == expert_nid:
                matches.append(record)
        if len(matches) != 1 or matches[0]['enabled'] is not True:
            raise ClientError('CONTRACT_CHANGED', 'resolve_relationship', '专家未启用或目标不唯一')
        version = matches[0]['version']
        if expected_version is not None and version != expected_version:
            raise ClientError('BOUND_VERSION_MISMATCH', 'resolve_relationship')
        return {'assistant_nid': payload['agentNid'], 'expert_nid': expert_nid,
                'expert_name': matches[0]['name'], 'version': version}

    def create_session(self, payload, *, confirmation=None):
        return self._operation('create_session', payload, confirmation=confirmation, write=True)

    def upload_file(self, payload, *, files=None, confirmation=None):
        return self._operation('upload_file', payload, files=files, confirmation=confirmation, write=True)

    def send_message(self, payload, *, confirmation=None):
        endpoint = self._profile.get('send_message')
        if not isinstance(payload, Mapping) or set(payload) != set(endpoint.request_fields):
            raise ClientError('CONTRACT_CHANGED', 'send_message', '请求字段不匹配已验证契约')
        captured = _plain(payload)
        self._authorize('send_message', captured, confirmation)

        def events():
            try:
                yield from parse_sse(self._transport.stream(endpoint.method, endpoint.path, json=captured))
            except Exception:
                raise ClientError('WRITE_STATE_UNKNOWN', 'send_message', '对话流未完整核验；禁止自动重试') from None
        return events()

    def confirm(self, payload, *, confirmation=None):
        return self._operation('confirm', payload, confirmation=confirmation, write=True)

    def resume(self, payload, *, confirmation=None):
        return self._operation('resume', payload, confirmation=confirmation, write=True)

    def history(self, payload):
        return self._operation('history', payload)
