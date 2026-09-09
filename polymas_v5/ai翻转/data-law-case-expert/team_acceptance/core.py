"""与发送协议解耦的专家团验收，所有外部 I/O 均可注入。"""
from __future__ import annotations

from datetime import datetime
import hashlib
import json
from pathlib import Path

from online_e2e.clients import TeachingCenterClient, require_role, select_unique_assistant
from online_e2e.private_io import write_private_bytes_atomic
from online_e2e.profiles import PDS_PROFILE, TEACHING_PROFILE
from online_e2e.safety import sanitize_json
from online_e2e.transport import ClientError, envelope_data


SOURCES = frozenset({'live-ui', 'live-api', 'synthetic'})
TERMINALS = frozenset({'ALL_FINISHED', 'completed', 'finished', 'success'})


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def _strings(value):
    return isinstance(value, list) and all(_text(item) for item in value)


def sanitize_identity(value, user_id):
    """普通名称也可能嵌入身份；按已认证主体补充统一 sanitizer 的键名规则。"""
    safe = sanitize_json(value)
    if not _text(user_id):
        raise ValueError('verified_identity_required')
    def replace(item):
        if isinstance(item, str):
            return item.replace(user_id, '[REDACTED]')
        if isinstance(item, dict):
            return {replace(key): replace(value) for key, value in item.items()}
        if isinstance(item, list):
            return [replace(value) for value in item]
        # 身份字段的数值由上面的统一 sanitizer 处理；普通数值不替换成字符串。
        return item
    return replace(safe)


def validate_config(value):
    """拒绝重复目标、未声明专家和缺少可执行断言的用例。"""
    if not isinstance(value, dict) or value.get('schema_version') != 1:
        raise ValueError('invalid_config_schema')
    assistants, cases = value.get('assistants'), value.get('cases')
    if not isinstance(assistants, list) or not assistants or not isinstance(cases, list) or not cases:
        raise ValueError('assistants_and_cases_required')
    targets = {}
    for assistant in assistants:
        if (not isinstance(assistant, dict) or not _text(assistant.get('nid'))
                or not _text(assistant.get('name')) or assistant['nid'] in targets):
            raise ValueError('invalid_or_duplicate_assistant')
        experts = assistant.get('experts')
        if not isinstance(experts, list) or not experts:
            raise ValueError('experts_required')
        targets[assistant['nid']] = set()
        for expert in experts:
            if (not isinstance(expert, dict) or not all(_text(expert.get(k)) for k in
                    ('nid', 'name', 'expected_version')) or expert['nid'] in targets[assistant['nid']]):
                raise ValueError('invalid_or_duplicate_expert')
            targets[assistant['nid']].add(expert['nid'])
            bindings = expert.get('knowledge_bindings', [])
            if not isinstance(bindings, list):
                raise ValueError('invalid_bindings')
            seen = set()
            for binding in bindings:
                if (not isinstance(binding, dict) or not _text(binding.get('nid'))
                        or binding['nid'] in seen):
                    raise ValueError('invalid_or_duplicate_binding')
                seen.add(binding['nid'])
    seen = set()
    for case in cases:
        if (not isinstance(case, dict) or not _text(case.get('id')) or case['id'] in seen
                or case.get('read_only') is not True or not _text(case.get('prompt'))
                or case.get('expert_nid') not in targets.get(case.get('assistant_nid'), set())):
            raise ValueError('invalid_case_or_target')
        seen.add(case['id'])
        assertions = case.get('assertions')
        if (not isinstance(assertions, dict) or not _strings(assertions.get('terminal_status'))
                or not assertions['terminal_status'] or not set(assertions['terminal_status']) <= TERMINALS):
            raise ValueError('terminal_assertion_required')
        for key in ('contains_all', 'contains_any', 'excludes', 'forbidden'):
            if not _strings(assertions.get(key, [])):
                raise ValueError('invalid_content_assertion')
        if not assertions.get('contains_all') and not assertions.get('contains_any'):
            raise ValueError('expected_content_required')
        if not _strings(case.get('required_evidence_fields', [])):
            raise ValueError('invalid_prerequisites')
    return json.loads(json.dumps(value, ensure_ascii=False, allow_nan=False))


def load_config(path):
    return validate_config(json.loads(Path(path).read_text(encoding='utf-8')))


def _check(name, status, detail=''):
    return {'name': name, 'status': status, 'detail': detail}


def _aggregate(checks):
    states = [check['status'] for check in checks]
    return 'fail' if 'fail' in states else 'unverified' if not states or 'unverified' in states else 'pass'


def _read(transport, profile, operation, payload):
    endpoint = profile.get(operation)
    options = {'params': payload} if endpoint.method == 'GET' else {'json': payload}
    try:
        return envelope_data(transport.request(endpoint.method, endpoint.path, **options), operation)
    except ClientError:
        raise
    except Exception:
        raise ClientError('TRANSPORT_ERROR', operation) from None


def preflight(config, transport):
    """只读核查：认证一次、关系一次，每个助教 full config 仅取一次。"""
    config = validate_config(config)
    report = {'mode': 'preflight', 'status': 'unverified', 'checks': [], 'snapshots': [],
              'live_dialogue_verified': False}
    checks = report['checks']
    try:
        client = TeachingCenterClient(transport)
        user = client.current_user()
        require_role(user, 'school_teacher')
        checks.append(_check('teacher_role', 'pass'))
        records = client.assistants({'userNid': user['userNid'], 'terminalType': 'PC',
                                     'roleTypeForPC': 'PC_TEACHER'})
    except ClientError as error:
        checks.append(_check('identity_and_access', 'fail', error.code))
        report['status'] = 'fail'
        return sanitize_json(report)
    binding_cache = {}
    for assistant in config['assistants']:
        nid = assistant['nid']
        try:
            select_unique_assistant(records, nid, assistant['name'])
            checks.append(_check(f'{nid}:assistant_access', 'pass'))
            snapshot = _read(transport, TEACHING_PROFILE, 'resolve_relationship', {'agentNid': nid})
            if (not isinstance(snapshot, dict) or not isinstance(snapshot.get('basicInfo'), dict)
                    or snapshot['basicInfo'].get('nid') != nid
                    or snapshot['basicInfo'].get('appName') != assistant['name'].removesuffix(' AI助教')
                    or not isinstance(snapshot.get('subAgentVOS'), list)):
                raise ClientError('CONTRACT_CHANGED', 'full_config')
            safe_snapshot = sanitize_identity(snapshot, user['userNid'])
            encoded = json.dumps(safe_snapshot, ensure_ascii=False, sort_keys=True).encode()
            report['snapshots'].append({'assistant_nid': nid, 'full_config': safe_snapshot,
                                       'sha256': hashlib.sha256(encoded).hexdigest()})
            for expert in assistant['experts']:
                expert_nid = expert['nid']
                matches = [item for item in snapshot['subAgentVOS']
                           if isinstance(item, dict) and item.get('agentNid') == expert_nid]
                valid = (len(matches) == 1 and matches[0].get('enabled') is True
                         and matches[0].get('name') == expert['name']
                         and matches[0].get('version') == expert['expected_version']
                         and sum(item.get('enabled') is True and item.get('name') == expert['name']
                                 for item in snapshot['subAgentVOS'] if isinstance(item, dict)) == 1)
                checks.append(_check(f'{nid}:{expert_nid}:relationship', 'pass' if valid else 'fail',
                                     '' if valid else '专家启用、名称、唯一性或版本不匹配'))
                if expert_nid not in binding_cache:
                    binding_cache[expert_nid] = _read(transport, PDS_PROFILE, 'knowledge_bindings',
                                                       {'agentNid': expert_nid})
                bindings = binding_cache[expert_nid]
                if not isinstance(bindings, list) or any(not isinstance(item, dict) for item in bindings):
                    raise ClientError('CONTRACT_CHANGED', 'knowledge_bindings')
                report['snapshots'][-1].setdefault('knowledge_bindings', {})[expert_nid] = bindings
                checks.append(_check(f'{nid}:{expert_nid}:bindings_read', 'pass'))
                for expected in expert.get('knowledge_bindings', []):
                    matched = [item for item in bindings if item.get('knowledgeBaseNid') == expected['nid']]
                    valid = len(matched) == 1
                    checks.append(_check(f'{nid}:{expert_nid}:binding:{expected["nid"]}',
                                         'pass' if valid else 'fail'))
        except ClientError as error:
            checks.append(_check(f'{nid}:preflight', 'fail', error.code))
    report['status'] = 'fail' if _aggregate(checks) == 'fail' else 'unverified'
    return sanitize_identity(report, user['userNid'])


def _live_evidence(record):
    """关联已发送请求与独立 history 回读，不把 confirmed 布尔值当作回读。"""
    if record.get('source') not in SOURCES - {'synthetic'}:
        return False
    try:
        if datetime.fromisoformat(record.get('captured_at', '').replace('Z', '+00:00')).tzinfo is None:
            return False
    except (ValueError, TypeError, AttributeError):
        return False
    keys = ('assistant_nid', 'expert_nid', 'message_id', 'trace_id')
    if any(not _text(record.get(key)) for key in keys):
        return False
    if not isinstance(record.get('session_id'), str):
        return False
    if not record['session_id'] and record.get('isolation') != 'existing-test-assistant-conversation':
        return False
    send, readback = record.get('send'), record.get('readback')
    for receipt in (send, readback):
        if (not isinstance(receipt, dict) or receipt.get('confirmed') is not True
                or receipt.get('source') not in SOURCES - {'synthetic'}
                or any(receipt.get(key) != record[key] for key in (*keys, 'session_id'))):
            return False
    if send.get('prompt') != record.get('prompt') or readback.get('kind') != 'history':
        return False
    if (readback.get('response') != record.get('response')
            or readback.get('terminal_status') != record.get('terminal_status')):
        return False
    messages = readback.get('messages')
    if not isinstance(messages, list):
        return False
    answer = [item for item in messages if isinstance(item, dict) and item.get('role') == 'assistant'
              and all(item.get(key) == record[key] for key in keys)
              and item.get('text') == record.get('response')
              and item.get('terminal_status') == record.get('terminal_status')]
    question = [item for item in messages if isinstance(item, dict) and item.get('role') == 'user'
                and item.get('session_id') == record['session_id']
                and item.get('assistant_nid') == record['assistant_nid']
                and item.get('text') == record.get('prompt')]
    request = send.get('captured_request', {})
    captured = (record.get('source') == 'live-api' and isinstance(request, dict)
                and request.get('assistant_nid') == record['assistant_nid']
                and request.get('prompt') == record.get('prompt')
                and request.get('answer_chat_nid') == record['message_id']
                and request.get('trace_id') == record['trace_id']
                and _text(request.get('input_chat_nid')))
    return len(answer) == 1 and (len(question) == 1 or captured)


def evaluate(config, evidence):
    """评估归一化导入证据；来源声明随报告保留，不声称独立认证证据真实性。"""
    config = validate_config(config)
    if (not isinstance(evidence, dict) or evidence.get('schema_version') != 1
            or not isinstance(evidence.get('records'), list)
            or any(not isinstance(item, dict) or item.get('source') not in SOURCES
                   for item in evidence['records'])):
        raise ValueError('invalid_evidence_schema')
    known = {case['id'] for case in config['cases']}
    if any(record.get('case_id') not in known for record in evidence['records']):
        raise ValueError('unknown_evidence_case')
    report = {'mode': 'evaluate', 'evidence_origin': 'imported', 'status': 'unverified', 'cases': []}
    for case in config['cases']:
        matches = [item for item in evidence['records'] if item.get('case_id') == case['id']]
        result = {'case_id': case['id'], 'checks': []}
        checks = result['checks']
        if len(matches) != 1:
            checks.append(_check('unique_evidence', 'unverified' if not matches else 'fail'))
        else:
            record = matches[0]
            result['evidence'] = record
            readback = record.get('readback')
            history = readback.get('messages', []) if isinstance(readback, dict) else []
            history = history if isinstance(history, list) else []
            result['input_persisted'] = any(isinstance(item, dict) and item.get('role') == 'user'
                                          and item.get('text') == record.get('prompt')
                                          for item in history)
            result['session_isolation'] = _check('session_isolation', 'unverified',
                                                 '未独立核验会话隔离；不影响已声明的回答内容断言')
            for key in ('assistant_nid', 'expert_nid', 'prompt'):
                checks.append(_check(key, 'unverified' if key not in record else
                                     'pass' if record[key] == case[key] else 'fail'))
            checks.append(_check('online_send_and_history_readback',
                                 'pass' if _live_evidence(record) else 'unverified'))
            expected_name = next(e['name'] for a in config['assistants']
                if a['nid'] == case['assistant_nid'] for e in a['experts']
                if e['nid'] == case['expert_nid'])
            execution = record.get('expert_execution_verified')
            observed = record.get('observed_agent_names')
            checks.append(_check('actual_expert_execution',
                'pass' if execution is True and isinstance(observed, list) and expected_name in observed
                else 'fail' if execution is False else 'unverified'))
            prerequisites = case.get('required_evidence_fields', [])
            prerequisite_evidence = record.get('prerequisites', {})
            available = isinstance(prerequisite_evidence, dict) and all(
                prerequisite_evidence.get(key) is True for key in prerequisites)
            if prerequisites:
                checks.append(_check('prerequisites', 'pass' if available else 'unverified'))
            assertions = case['assertions']
            terminal = record.get('terminal_status')
            checks.append(_check('terminal_status', 'unverified' if terminal is None else
                                 'pass' if terminal in assertions['terminal_status'] else 'fail'))
            response = record.get('response')
            for name in ('contains_all', 'contains_any', 'excludes', 'forbidden'):
                terms = assertions.get(name, [])
                if not terms:
                    continue
                if not isinstance(response, str) or not available:
                    state = 'unverified'
                else:
                    matched = [term in response for term in terms]
                    passed = all(matched) if name == 'contains_all' else any(matched) if name == 'contains_any' else not any(matched)
                    state = 'pass' if passed else 'fail'
                checks.append(_check(name, state))
        result['status'] = _aggregate(checks)
        report['cases'].append(result)
    report['status'] = _aggregate(report['cases'])
    report['live_dialogue_verified'] = report['status'] == 'pass'
    return sanitize_json(report)


def write_reports(prefix, report):
    """Markdown 与 JSON 共用已脱敏 payload，并使用私有原子写。"""
    prefix = Path(prefix)
    safe = sanitize_json(report)
    encoded = json.dumps(safe, ensure_ascii=False, indent=2, sort_keys=True)
    paths = {'json': str(prefix.with_suffix('.json')), 'markdown': str(prefix.with_suffix('.md'))}
    write_private_bytes_atomic(Path(paths['json']), (encoded + '\n').encode())
    labels = {'pass': '通过', 'fail': '未通过', 'unverified': '未验证'}
    lines = ['# 专家团验收报告', '', f"验收结果：**{labels.get(safe.get('status'), '未验证')}**",
             '', f"模式：{safe.get('mode', 'evaluate')}；证据：{safe.get('evidence_origin', '只读预检')}",
             '', f'完整结构化证据见 [{prefix.name}.json]({prefix.name}.json)。', '']
    for key in ('run_id', 'session_id', 'message_id', 'trace_id', 'error'):
        if key in safe:
            lines.extend([f"{key}：{safe[key]}", ''])
    for check in safe.get('checks', safe.get('preflight', {}).get('checks', [])):
        lines.append(f"- {labels.get(check['status'], '未验证')}：{check['name']} {check.get('detail', '')}")
    for result in safe.get('cases', []):
        lines.extend(['', f"## {result['case_id']}：{labels.get(result['status'], '未验证')}", ''])
        for check in result.get('checks', []):
            lines.append(f"- {labels.get(check['status'], '未验证')}：{check['name']} {check.get('detail', '')}")
        evidence = result.get('evidence', {})
        lines.extend(['', '测试问题：', ''])
        lines.extend('    ' + line for line in str(evidence.get('prompt', '')).splitlines())
        lines.extend(['', '实际回答：', ''])
        lines.extend('    ' + line for line in str(evidence.get('response', '')).splitlines())
        lines.extend(['', f"回答标识：{evidence.get('message_id', '无')}；trace：{evidence.get('trace_id', '无')}",
            '', '本轮复用测试助教现有私聊，未宣称创建独立会话。'])
    markdown = '\n'.join(lines) + '\n'
    write_private_bytes_atomic(Path(paths['markdown']), markdown.encode())
    return paths
