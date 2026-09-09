"""教师私聊 stream→history 适配，契约于 2026-09-05 真实回读验证。"""
from datetime import datetime, timezone
from contextlib import ExitStack
import hashlib
import json
from pathlib import Path
import secrets
import string
import time

from online_e2e.safety import sanitize_json
from online_e2e.sse import parse_sse
from online_e2e.transport import envelope_data
from online_e2e.clients import TeachingCenterClient, require_role
from online_e2e.fixtures import validate_run_id
from online_e2e.private_io import write_private_json_atomic
from online_e2e.run_store import DurableRunStore
from .core import evaluate, preflight, validate_config, sanitize_identity


STREAM_PATH = '/ai-agent/assistant/v1/chat/stream'
HISTORY_PATH = '/chatim/v1/robot/chat/history'


def run_case(case, expert_name, transport, current_user_id, *, on_prepared=None):
    """仅测试对话，不发布配置。未知发送状态不重试；不会伪造独立 session。"""
    if case.get('read_only') is not True:
        raise ValueError('read_only_case_required')
    alphabet = string.ascii_letters + string.digits
    new_id = lambda: ''.join(secrets.choice(alphabet) for _ in range(10))
    input_id, answer_id = new_id(), new_id()
    trace = str(secrets.randbelow(9_000_000_000) + 1_000_000_000)
    msg_key = str(int(time.time() * 1000) * 1_000_000 + secrets.randbelow(900_000))
    body = {
        'fromNid': current_user_id, 'terminal': 'TEACHER',
        'metaData': {'traceId': trace, 'optPlatform': 'Web', 'abilityConfigs': [],
            'bizCode': 'hike_teach_center', 'msgId': str(int(msg_key) + 1),
            'sessionId': '', 'clearSession': False, 'skillName': '',
            'subAgentNIds': [case['expert_nid']], 'answerChatNid': answer_id,
            'msgKey': msg_key, 'inputChatNid': input_id},
        'userInput': case['prompt'], 'traceId': trace, 'chatMode': 'COMMON',
        'actMode': 'AUTO', 'toNid': case['assistant_nid'], 'modelName': 'Auto',
    }
    identity = {'assistant_nid': case['assistant_nid'], 'expert_nid': case['expert_nid'],
                'session_id': '', 'message_id': answer_id, 'trace_id': trace}
    captured = {'assistant_nid': case['assistant_nid'], 'expert_nid': case['expert_nid'],
                'prompt': case['prompt'], 'input_chat_nid': input_id,
                'answer_chat_nid': answer_id, 'trace_id': trace}
    record = {'case_id': case['id'], 'source': 'live-api', **identity,
        'captured_at': datetime.now(timezone.utc).isoformat(), 'prompt': case['prompt'],
        'terminal_status': None, 'response': '', 'input_persisted': False,
        'isolation': 'existing-test-assistant-conversation',
        'expert_execution_verified': False, 'observed_agent_names': [],
        'send': {'confirmed': False, 'source': 'live-api', **identity,
                 'prompt': case['prompt'], 'captured_request': captured},
        'readback': {'confirmed': False, 'source': 'live-api', 'kind': 'history',
                     **identity, 'response': '', 'terminal_status': None, 'messages': []}}
    # 调用者可在首次网络写入前持久保存安全关联键；保存失败就不发送。
    if on_prepared:
        on_prepared(sanitize_identity(record, current_user_id))
    started = time.monotonic()
    try:
        for event in parse_sse(transport.stream('POST', STREAM_PATH, json=body),
                               terminal_events=('ALL_FINISHED',), require_terminal=True):
            data = event.data
            if isinstance(data, dict):
                name = data.get('agentName')
                if name and name not in record['observed_agent_names']:
                    record['observed_agent_names'].append(name)
                if name == expert_name and data.get('agentNid') in (None, case['expert_nid']):
                    record['expert_execution_verified'] = True
                if event.event == 'ANSWER':
                    if data.get('isAdditional') is False:
                        record['response'] = ''
                    record['response'] += data.get('text') or ''
            if event.terminal:
                record['terminal_status'] = event.event
        record['send']['confirmed'] = True
    except Exception:
        record['error_code'] = 'WRITE_STATE_UNKNOWN'
    # 即使流中断，也只回读一次，绝不重复提交。
    try:
        history = envelope_data(transport.request('POST', HISTORY_PATH, json={
            'page': 1, 'pageSize': 50, 'fromUserNid': current_user_id,
            'toUserNid': case['assistant_nid']}), 'history')
        rows = history.get('list', [])
        matches = [row for row in rows if row.get('nid') == answer_id
                   and str(row.get('traceId')) == trace
                   and row.get('fromUserNid') == case['assistant_nid']
                   and row.get('toUserNid') == current_user_id
                   and row.get('msgType') == 'ROBOT_ANSWER']
        record['input_persisted'] = any(row.get('nid') == input_id
            and row.get('fromUserNid') == current_user_id
            and row.get('toUserNid') == case['assistant_nid'] for row in rows)
        if len(matches) == 1:
            row = matches[0]
            done = row.get('stepStatus') == 'DONE'
            readback = record['readback']
            readback['response'] = row.get('msgText')
            readback['terminal_status'] = 'ALL_FINISHED' if done else row.get('stepStatus')
            readback['messages'] = [{'role': 'assistant', **identity,
                'text': row.get('msgText'), 'terminal_status': readback['terminal_status'],
                'history_status': row.get('stepStatus'), 'server_message_id': row.get('msgId')}]
            readback['confirmed'] = (done and record['terminal_status'] == 'ALL_FINISHED'
                and row.get('msgText') == record['response']
                and record['expert_execution_verified'])
    except Exception:
        record['error_code'] = record.get('error_code', 'HISTORY_READBACK_FAILED')
    record['elapsed_seconds'] = round(time.monotonic() - started, 3)
    return sanitize_identity(record, current_user_id)


def run_suite(config, transport, state_dir, run_id):
    """顺序执行教师只读对话用例，未知状态留下停写记录，同 run 不重复发送。"""
    config = validate_config(config)
    validate_run_id(run_id)
    store = DurableRunStore(Path(state_dir))
    digest = hashlib.sha256(json.dumps(config, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    assistants = sorted(a['nid'] for a in config['assistants'])
    fence_paths = {nid: store.root / 'chat-fences' / (hashlib.sha256(nid.encode()).hexdigest() + '.json')
                   for nid in assistants}
    with ExitStack() as locks:
        locks.enter_context(store.target_lock('run-' + run_id))
        for nid in assistants:
            locks.enter_context(store.target_lock('chat-' + nid))
        for nid, path in fence_paths.items():
            if path.exists():
                try:
                    fence = json.loads(path.read_text())
                    if fence.get('state') == 'RESOLVED':
                        continue
                except (ValueError, OSError, AttributeError):
                    fence = {'state': 'UNREADABLE'}
                return sanitize_json({'mode': 'run', 'status': 'unverified',
                    'error': 'RECOVERY_REQUIRED', 'assistant_nid': nid, 'residual_state': fence})
        previous = store.read_checkpoint(run_id)
        if previous:
            if previous.get('config_digest') != digest:
                return {'mode': 'run', 'status': 'fail', 'error': 'RUN_CONFIG_MISMATCH'}
            if previous.get('state') == 'FINISHED':
                return previous['report']
            return {'mode': 'run', 'status': 'unverified', 'error': 'RECOVERY_REQUIRED'}
        pre = preflight(config, transport)
        if pre['status'] == 'fail':
            return {'mode': 'run', 'status': 'fail', 'preflight': pre, 'cases': []}
        user = TeachingCenterClient(transport).current_user()
        require_role(user, 'school_teacher')
        records = []
        experts = {(a['nid'], e['nid']): e['name'] for a in config['assistants'] for e in a['experts']}
        for case in config['cases']:
            nid = case['assistant_nid']

            def prepared(record):
                store.write_checkpoint(run_id, {'state': 'IN_FLIGHT', 'config_digest': digest,
                    'records': records, 'pending': record})
                write_private_json_atomic(fence_paths[nid], sanitize_json({
                    'state': 'IN_FLIGHT', 'run_id': run_id, 'case_id': case['id'],
                    'trace_id': record['trace_id'], 'message_id': record['message_id'],
                    'note': '仅允许按关联标识只读对账；不得自动重复发送'}))

            record = run_case(case, experts[(nid, case['expert_nid'])], transport,
                              user['userNid'], on_prepared=prepared)
            records.append(record)
            store.write_checkpoint(run_id, {'state': 'IN_FLIGHT', 'config_digest': digest,
                                           'records': records})
            if record.get('error_code') == 'WRITE_STATE_UNKNOWN' or not record['readback']['confirmed']:
                break
            write_private_json_atomic(fence_paths[nid], {'state': 'RESOLVED', 'run_id': run_id})
        report = evaluate(config, {'schema_version': 1, 'records': records})
        report.update({'mode': 'run', 'run_id': run_id, 'evidence_origin': 'captured-live-api',
                       'preflight': pre, 'scope': 'teacher-private-assistant-read-only-dialogue'})
        store.write_checkpoint(run_id, {'state': 'FINISHED', 'config_digest': digest, 'report': report})
        return report
