"""外层 Agent 的三轮修复协议；不自行调用模型或猜测平台写接口。"""
from datetime import datetime, timezone
import copy
import hashlib
import hmac
import json
from pathlib import Path, PurePosixPath
import secrets

from online_e2e.private_io import write_private_bytes_atomic, write_private_json_atomic
from online_e2e.run_store import DurableRunStore
from online_e2e.safety import sanitize_json
from .core import evaluate, validate_config


ACTIONS = {
    'AWAITING_TEST': '调用 run-test 使用锁定用例采集真实教师对话；自动入账后 record-review',
    'AWAITING_REVIEW': '逐条对照验收准则引用真实回答，提交 record-review',
    'NEEDS_REPAIR': '先查原子 Skill 目录与线上能力，诊断后 propose-change',
    'AWAITING_EDITS': '外层 Agent 仅编辑已批准专家文件，再 record-changes',
    'AWAITING_DEPLOYMENT': '发布专家改动并 verify-deployment；缺少可靠发布/回读能力时 block',
    'NEEDS_USER_AGREEMENT': '与用户协商助教提示词；当前权限仍不允许修改助教',
    'ITERATION_LIMIT_REACHED': '交付三轮结果与未解决问题，不继续修改',
    'PASSED': '交付验收证据、版本与修改记录',
    'BLOCKED': '交付已证实的外部阻断原因，等待条件变化',
}
CONTRACT_FILES = ('acceptance.md', 'config.json', 'criteria.json', 'scope.json', 'catalog.json')


def _now():
    return datetime.now(timezone.utc).isoformat()


def _hash(value):
    if not isinstance(value, bytes):
        value = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
    return hashlib.sha256(value).hexdigest()


def _inventory(root):
    root = Path(root).resolve()
    if not root.is_dir():
        raise ValueError('SOURCE_ROOT_REQUIRED')
    result = {}
    for p in sorted(root.rglob('*')):
        relative = p.relative_to(root)
        if any(part in ('.git', '.pytest_cache', '__pycache__') for part in relative.parts):
            continue
        if p.is_symlink():
            raise ValueError('SOURCE_SYMLINK_FORBIDDEN')
        if p.is_file():
            result[relative.as_posix()] = _hash(p.read_bytes())
    return result


def _relative(value):
    if not isinstance(value, str) or not value or '\\' in value:
        raise ValueError('INVALID_SOURCE_PATH')
    path = PurePosixPath(value)
    if path.is_absolute() or '..' in path.parts or str(path) != value:
        raise ValueError('INVALID_SOURCE_PATH')
    if any(x.startswith('.') for x in path.parts) or path.name == 'AGENTS.md':
        raise ValueError('PROTECTED_SOURCE_PATH')
    return path


def _resource(scope, path):
    p = _relative(path)
    matches = []
    for item in scope['resources']:
        allowed = _relative(item['path'])
        if p == allowed or (item['kind'] == 'expert_skill' and allowed in p.parents):
            matches.append(item)
    if len(matches) != 1:
        raise ValueError('SOURCE_SCOPE_AMBIGUOUS')
    return matches[0]


def _load(session):
    root = Path(session)
    state = json.loads((root / 'iteration.json').read_text())
    for name, digest in state['contract_hashes'].items():
        if _hash((root / name).read_bytes()) != digest:
            raise ValueError('CONTRACT_CHANGED')
    if _hash((root / 'runtime-config.json').read_bytes()) != state.get('runtime_config_hash'):
        raise ValueError('RUNTIME_CONFIG_CHANGED')
    return state


def _public(state):
    return sanitize_json({**state, 'next_action': ACTIONS[state['status']]})


def _update(session, operation):
    root = Path(session)
    store = DurableRunStore(root)
    with store.target_lock('expert-iteration'):
        state = _load(root)
        operation(state, root)
        state['updated_at'] = _now()
        write_private_json_atomic(root / 'iteration.json', sanitize_json(state))
        return _public(state)


def initialize(session, config, acceptance, criteria, scope, catalog, *, platform_snapshot=None):
    config = validate_config(config)
    if not isinstance(acceptance, str) or not acceptance.strip():
        raise ValueError('ACCEPTANCE_REQUIRED')
    if (not isinstance(criteria, list) or not criteria or any(not isinstance(c, dict)
        or not c.get('id') or not c.get('requirement') for c in criteria)
        or len({c['id'] for c in criteria}) != len(criteria)):
        raise ValueError('CRITERIA_REQUIRED')
    expert_ids = {e['nid'] for a in config['assistants'] for e in a['experts']}
    if not scope.get('resources') or not catalog.get('entries'):
        raise ValueError('SCOPE_AND_CATALOG_REQUIRED')
    for item in scope['resources']:
        _relative(item['path'])
        if item['kind'] not in ('expert_agent_md', 'expert_skill', 'assistant_prompt'):
            raise ValueError('UNKNOWN_RESOURCE_KIND')
        if item['kind'] != 'assistant_prompt' and item.get('expert_nid') not in expert_ids:
            raise ValueError('UNKNOWN_EXPERT')
    root = Path(session).resolve()
    source = Path(scope['source_root']).resolve()
    if root == source or source in root.parents:
        raise ValueError('STATE_MUST_BE_OUTSIDE_SOURCE')
    store = DurableRunStore(root)
    with store.target_lock('expert-iteration'):
        if (root / 'iteration.json').exists():
            raise ValueError('SESSION_ALREADY_EXISTS')
        originals = _inventory(source)
        write_private_bytes_atomic(root / 'acceptance.md', acceptance.encode())
        for name, value in [('config.json', config), ('criteria.json', criteria),
                            ('scope.json', scope), ('catalog.json', catalog)]:
            write_private_json_atomic(root / name, sanitize_json(value))
        write_private_json_atomic(root / 'runtime-config.json', config)
        state = {'schema_version': 1, 'status': 'AWAITING_TEST', 'iteration': 0, 'max_iterations': 3,
                 'session_id': secrets.token_hex(16),
                 'created_at': _now(), 'awaiting_test_since': _now(), 'history': [],
                 'contract_hashes': {name: _hash((root / name).read_bytes()) for name in CONTRACT_FILES},
                 'inventory': originals, 'platform_snapshot': platform_snapshot,
                 'rounds': [], 'used_report_hashes': [], 'used_evidence_ids': [],
                 'runtime_config_hash': _hash((root / 'runtime-config.json').read_bytes())}
        write_private_json_atomic(root / 'iteration.json', sanitize_json(state))
        return _public(state)


def status(session):
    return _public(_load(session))


def _receipt_binding(state, report):
    return {'session_id': state['session_id'], 'iteration': state['iteration'],
            'contract_hashes': state['contract_hashes'], 'runtime_config_hash': state['runtime_config_hash'],
            'report_hash': _hash(report)}


def _signature(root, binding):
    return hmac.new((root / 'confirmation.key').read_bytes(),
                    _hash(binding).encode(), hashlib.sha256).hexdigest()


def _trusted_capture(state, root, report):
    receipt_path = root / f"round-{state['iteration']}-receipt.json"
    if not receipt_path.exists():
        raise ValueError('TRUSTED_CAPTURE_REQUIRED')
    receipt = json.loads(receipt_path.read_text())
    binding = _receipt_binding(state, report)
    if (receipt.get('binding') != binding or not isinstance(receipt.get('signature'), str)
            or not hmac.compare_digest(receipt['signature'], _signature(root, binding))):
        raise ValueError('TRUSTED_CAPTURE_REQUIRED')


def _accept_test(state, root, report):
    if state['status'] != 'AWAITING_TEST':
        raise ValueError('TEST_NOT_EXPECTED')
    _trusted_capture(state, root, report)
    if report.get('evidence_origin') not in ('captured-live-api', 'captured-live-api-re-evaluated'):
        raise ValueError('LIVE_REPORT_REQUIRED')
    config = json.loads((root / 'runtime-config.json').read_text())
    records = [c['evidence'] for c in report.get('cases', []) if 'evidence' in c]
    expected_ids = {c['id'] for c in config['cases']}
    if {r.get('case_id') for r in records} != expected_ids or len(records) != len(expected_ids):
        raise ValueError('COMPLETE_REPORT_REQUIRED')
    evidence_ids = []
    for record in records:
        try:
            captured = datetime.fromisoformat(record['captured_at'])
            if captured.tzinfo is None:
                raise ValueError('INVALID_CAPTURE_TIME')
        except (ValueError, TypeError, KeyError):
            raise ValueError('INVALID_CAPTURE_TIME') from None
        if captured > datetime.now(timezone.utc):
            raise ValueError('FUTURE_TEST_REPORT')
        if captured < datetime.fromisoformat(state['awaiting_test_since']):
            raise ValueError('STALE_TEST_REPORT')
        identity = [record.get(k) for k in ('assistant_nid', 'expert_nid', 'message_id', 'trace_id')]
        if not all(isinstance(v, str) and v for v in identity):
            raise ValueError('LIVE_EVIDENCE_UNVERIFIED')
        evidence_ids.append(_hash(identity))
    if len(set(evidence_ids)) != len(evidence_ids) or set(evidence_ids) & set(state['used_evidence_ids']):
        raise ValueError('REUSED_TEST_REPORT')
    verified = evaluate(config, {'schema_version': 1, 'records': records})
    for result in verified['cases']:
        if any(c['status'] != 'pass' for c in result['checks']
               if c['name'] in ('online_send_and_history_readback', 'actual_expert_execution',
                                'assistant_nid', 'expert_nid', 'prompt', 'terminal_status')):
            raise ValueError('LIVE_EVIDENCE_UNVERIFIED')
    digest = _hash(records)
    if digest in state['used_report_hashes']:
        raise ValueError('REUSED_TEST_REPORT')
    path = f"round-{state['iteration']}-test.json"
    write_private_json_atomic(root / path, verified)
    state['used_report_hashes'].append(digest)
    state['used_evidence_ids'].extend(evidence_ids)
    state['test_report'] = path
    state['test_report_hash'] = _hash((root / path).read_bytes())
    state['status'] = 'AWAITING_REVIEW'


def record_test(session, report):
    """仅恢复当前 session/轮次 run-test 已签名采集的原报告，不信任外部来源声明。"""
    def operation(state, root):
        _accept_test(state, root, report)
    return _update(session, operation)


def run_test(session, transport, *, runner=None):
    """锁内采集、落盘并入账；注入 runner 仅是本机受信任代码测试边界。"""
    if runner is None:
        from .live_chat import run_suite
        runner = run_suite
    def operation(state, root):
        if state['status'] in ('AWAITING_REVIEW', 'BLOCKED'):
            return
        if state['status'] != 'AWAITING_TEST':
            raise ValueError('TEST_NOT_EXPECTED')
        round_id = state['iteration']
        capture = root / f'round-{round_id}-capture.json'
        receipt_path = root / f'round-{round_id}-receipt.json'
        if capture.exists():
            report = json.loads(capture.read_text())
        else:
            config = json.loads((root / 'runtime-config.json').read_text())
            try:
                report = runner(config, transport, root / 'live-tests', f'iteration-{round_id}')
            except Exception:
                report = {'status': 'unverified', 'error': 'CAPTURE_INTERRUPTED',
                          'note': '证据保留在 live-tests checkpoint；仅可只读恢复，不重发'}
            report = sanitize_json(report)
            write_private_json_atomic(capture, report)
            binding = _receipt_binding(state, report)
            write_private_json_atomic(receipt_path, {'binding': binding, 'signature': _signature(root, binding)})
        state['capture_report'] = capture.name
        try:
            _accept_test(state, root, report)
        except (ValueError, KeyError, TypeError) as error:
            state['status'] = 'BLOCKED'
            state['blocked_from'] = 'AWAITING_TEST'
            state['block_reason'] = (str(error) if type(error) is ValueError else 'LIVE_EVIDENCE_UNVERIFIED')
    return _update(session, operation)


def record_review(session, review):
    def operation(state, root):
        if state['status'] != 'AWAITING_REVIEW':
            raise ValueError('REVIEW_NOT_EXPECTED')
        p = root / state['test_report']
        if _hash(p.read_bytes()) != state['test_report_hash']:
            raise ValueError('TEST_REPORT_CHANGED')
        test = json.loads(p.read_text())
        criteria = json.loads((root / 'criteria.json').read_text())
        rows = review.get('criteria', [])
        if len(rows) != len(criteria) or {r.get('id') for r in rows} != {r['id'] for r in criteria}:
            raise ValueError('ALL_CRITERIA_REQUIRED')
        evidence = {r['case_id']: r['evidence'] for r in test['cases']}
        for row in rows:
            if row.get('verdict') not in ('pass', 'fail', 'unverified') or not row.get('reason') or not row.get('evidence'):
                raise ValueError('REVIEW_EVIDENCE_REQUIRED')
            for ref in row['evidence']:
                actual = evidence.get(ref.get('case_id'), {})
                if (not ref.get('quote') or ref.get('message_id') != actual.get('message_id')
                    or ref['quote'] not in actual.get('response', '')):
                    raise ValueError('REVIEW_QUOTE_NOT_FOUND')
        passed = test['status'] == 'pass' and all(r['verdict'] == 'pass' for r in rows)
        write_private_json_atomic(root / f"round-{state['iteration']}-review.json", sanitize_json(review))
        state['history'].append({'iteration': state['iteration'], 'test_status': test['status'],
                                 'review_status': 'pass' if passed else 'fail'})
        state['status'] = ('PASSED' if passed else 'ITERATION_LIMIT_REACHED'
                           if state['iteration'] >= 3 else 'NEEDS_REPAIR')
    return _update(session, operation)


def propose_change(session, plan):
    def operation(state, root):
        if state['status'] not in ('NEEDS_REPAIR', 'NEEDS_USER_AGREEMENT') or state['iteration'] >= 3:
            raise ValueError('REPAIR_NOT_ALLOWED')
        scope = json.loads((root / 'scope.json').read_text())
        files = plan.get('files', [])
        if not files or len(files) != len(set(files)) or not plan.get('reason'):
            raise ValueError('CHANGE_PLAN_REQUIRED')
        resources = [_resource(scope, path) for path in files]
        if any(item['kind'] == 'assistant_prompt' for item in resources):
            state['status'] = 'NEEDS_USER_AGREEMENT'
            state['agreement_reason'] = '涉及 AI 助教提示词，须先与用户协商；当前修改范围未扩大'
            return
        catalog = json.loads((root / 'catalog.json').read_text())
        reuse = plan.get('reuse_review', {})
        checked = reuse.get('checked_entry_ids', [])
        if not checked or not set(checked) <= {e['id'] for e in catalog['entries']} or not reuse.get('reason'):
            raise ValueError('CATALOG_REFERENCE_REQUIRED')
        if reuse.get('decision') not in ('reuse_existing', 'extend_existing', 'new_domain_skill'):
            raise ValueError('REUSE_DECISION_REQUIRED')
        if plan.get('capability_type') not in ('domain', 'retrieval', 'course'):
            raise ValueError('CAPABILITY_TYPE_REQUIRED')
        if plan['capability_type'] in ('retrieval', 'course') and reuse['decision'] == 'new_domain_skill':
            raise ValueError('REUSE_EXISTING_REQUIRED')
        if reuse['decision'] == 'new_domain_skill' and not reuse.get('uncovered_behavior'):
            raise ValueError('DOMAIN_GAP_REQUIRED')
        if _inventory(scope['source_root']) != state['inventory']:
            raise ValueError('SOURCE_CHANGED_BEFORE_PLAN')
        state['iteration'] += 1
        state['plan'] = sanitize_json(plan)
        state['rounds'].append({'iteration': state['iteration'], 'plan': sanitize_json(plan)})
        state['status'] = 'AWAITING_EDITS'
    return _update(session, operation)


def record_changes(session):
    def operation(state, root):
        if state['status'] != 'AWAITING_EDITS':
            raise ValueError('EDITS_NOT_EXPECTED')
        scope = json.loads((root / 'scope.json').read_text())
        current = _inventory(scope['source_root'])
        changed = {p for p in set(current) | set(state['inventory']) if current.get(p) != state['inventory'].get(p)}
        if not changed or not changed <= set(state['plan']['files']):
            raise ValueError('OUT_OF_SCOPE_CHANGE')
        state['changed_files'] = sorted(changed)
        state['candidate_inventory'] = current
        state['status'] = 'AWAITING_DEPLOYMENT'
    return _update(session, operation)


def _protected_snapshot(snapshot, changed_experts):
    """只屏蔽计划内专家正文与版本，保留所有挂载、权限、排序和其他字段。"""
    protected = copy.deepcopy(snapshot)
    protected.pop('captured_at', None)
    for nid in changed_experts:
        expert = protected.get('experts', {}).get(nid, {})
        for key in ('agent_md', 'version', 'bound_versions'):
            expert.pop(key, None)
        full = protected.get('protection', {}).get('experts', {}).get(nid, {})
        if isinstance(full.get('expertMd'), dict):
            full['expertMd'].pop('customContent', None)
        for key in ('version',):
            full.get('basicInfo', {}).pop(key, None)
        preview = protected.get('protection', {}).get('previews', {}).get(nid, {})
        preview.get('expertInfo', {}).get('sourceInfo', {}).pop('version', None)
    for full in protected.get('protection', {}).get('assistants', {}).values():
        for relation in full.get('subAgentVOS', []):
            if relation.get('agentNid') in changed_experts:
                relation.pop('version', None)
    return protected


def verify_deployment(session, snapshot):
    """snapshot 必须由可信的实际平台回读适配器取得；CLI 仅使用实时 API。"""
    def operation(state, root):
        if state['status'] != 'AWAITING_DEPLOYMENT':
            raise ValueError('DEPLOYMENT_NOT_EXPECTED')
        scope = json.loads((root / 'scope.json').read_text())
        if _inventory(scope['source_root']) != state['candidate_inventory']:
            raise ValueError('CANDIDATE_CHANGED')
        before = state.get('platform_snapshot')
        if not before or snapshot.get('assistant_prompt_digest') != before.get('assistant_prompt_digest'):
            state['status'] = 'NEEDS_USER_AGREEMENT'
            state['agreement_reason'] = '缺少助教提示词基线或线上提示词已变化，须先与用户核对'
            return
        config = json.loads((root / 'config.json').read_text())
        changed_experts = set()
        for path in state['changed_files']:
            item = _resource(scope, path)
            changed_experts.add(item['expert_nid'])
            expert = snapshot.get('experts', {}).get(item['expert_nid'], {})
            expected_assistants = {a['nid'] for a in config['assistants']
                                   if any(e['nid'] == item['expert_nid'] for e in a['experts'])}
            if (not expert.get('version') or not expert.get('bound_versions')
                or not expected_assistants <= set(expert['bound_versions'])
                or any(v != expert['version'] for v in expert['bound_versions'].values())):
                state['deployment_blocker'] = 'BOUND_VERSION_MISMATCH'
                return
            if item['kind'] == 'expert_skill':
                # 版本号本身不能证明具体代码已上线，等待能回读内容的适配器。
                state['deployment_blocker'] = 'SKILL_CONTENT_READBACK_UNVERIFIED'
                return
            file = Path(scope['source_root']) / path
            if not file.is_file() or expert.get('agent_md') != file.read_text():
                state['deployment_blocker'] = 'EXPERT_CONTENT_READBACK_MISMATCH'
                return
        if not before.get('protection') or not snapshot.get('protection'):
            state['deployment_blocker'] = 'PROTECTED_SNAPSHOT_REQUIRED'
            return
        if _protected_snapshot(before, changed_experts) != _protected_snapshot(snapshot, changed_experts):
            state['deployment_blocker'] = 'OUT_OF_SCOPE_DEPLOYMENT'
            return
        state.pop('deployment_blocker', None)
        state['platform_snapshot'] = snapshot
        state['inventory'] = state.pop('candidate_inventory')
        state['status'] = 'AWAITING_TEST'
        state['awaiting_test_since'] = _now()
        runtime = json.loads((root / 'config.json').read_text())
        for assistant in runtime['assistants']:
            for expert in assistant['experts']:
                observed = snapshot.get('experts', {}).get(expert['nid'], {})
                if observed.get('version'):
                    expert['expected_version'] = observed['version']
        write_private_json_atomic(root / 'runtime-config.json', runtime)
        state['runtime_config_hash'] = _hash((root / 'runtime-config.json').read_bytes())
    return _update(session, operation)


def block(session, reason):
    if not isinstance(reason, str) or not reason.strip():
        raise ValueError('BLOCK_REASON_REQUIRED')
    def operation(state, root):
        state['blocked_from'] = state['status']
        state['status'] = 'BLOCKED'
        state['block_reason'] = reason
    return _update(session, operation)
