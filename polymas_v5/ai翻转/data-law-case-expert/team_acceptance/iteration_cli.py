"""可交接迭代入口；发现与回读走真实只读接口，发布由外层 Agent 完成。"""
import argparse
import json
from pathlib import Path
import sys

from online_e2e.clients import TeachingCenterClient, require_role, select_unique_assistant
from online_e2e.requests_transport import RequestsTransport
from online_e2e.safety import sanitize_json
from online_e2e.transport import ClientError, envelope_data
from .core import sanitize_identity
from . import iteration


def _teacher_context(transport):
    client = TeachingCenterClient(transport)
    user = client.current_user()
    require_role(user, 'school_teacher')
    records = client.assistants({'userNid': user['userNid'], 'terminalType': 'PC', 'roleTypeForPC': 'PC_TEACHER'})
    return user, records


def _full(transport, nid):
    value = envelope_data(transport.request('GET', '/llmOps/mdTemplate/v1/agentFullConfig',
                                           params={'agentNid': nid}), 'config_snapshot')
    if value.get('basicInfo', {}).get('nid') != nid:
        raise ValueError('TARGET_SNAPSHOT_MISMATCH')
    return value


def discover(assistant_id, transport):
    user, records = _teacher_context(transport)
    matches = [r for r in records if r.get('friendNid') == assistant_id]
    if len(matches) != 1:
        raise ValueError('ASSISTANT_NOT_ACCESSIBLE')
    name = matches[0]['friendNickName']
    select_unique_assistant(records, assistant_id, name)
    actual = _full(transport, assistant_id)
    experts = []
    for item in actual.get('subAgentVOS', []):
        if item.get('enabled') is True:
            if not all(item.get(k) for k in ('agentNid', 'name', 'version')):
                raise ValueError('EXPERT_IDENTITY_UNVERIFIED')
            experts.append({'nid': item['agentNid'], 'name': item['name'],
                            'expected_version': str(item['version'])})
    return sanitize_identity({'status': 'AWAITING_ACCEPTANCE_DESIGN', 'requires_test_design': True,
        'config': {'schema_version': 1, 'assistants': [{'nid': assistant_id, 'name': name, 'experts': experts}],
                   'cases': []}}, user['userNid'])


def live_snapshot(config, transport):
    user, records = _teacher_context(transport)
    prompts, experts = {}, {}
    protection = {'assistants': {}, 'experts': {}, 'previews': {}}
    for assistant in config['assistants']:
        select_unique_assistant(records, assistant['nid'], assistant['name'])
        actual = _full(transport, assistant['nid'])
        protection['assistants'][assistant['nid']] = actual
        prompts[assistant['nid']] = {key: actual.get(key) for key in ('personaMd', 'soulMd', 'agentMd', 'planMd')}
        for expected in assistant['experts']:
            if len([e for e in actual.get('subAgentVOS', [])
                    if e.get('agentNid') == expected['nid'] and e.get('enabled') is True]) != 1:
                raise ValueError('EXPERT_BINDING_UNVERIFIED')
        for relation in actual.get('subAgentVOS', []):
            nid = relation.get('agentNid')
            if not nid:
                raise ValueError('EXPERT_BINDING_UNVERIFIED')
            bound = [e for e in actual.get('subAgentVOS', []) if e.get('agentNid') == nid]
            if len(bound) != 1:
                raise ValueError('EXPERT_BINDING_UNVERIFIED')
            if nid not in experts:
                full = _full(transport, nid)
                preview = envelope_data(transport.request('GET', '/llmOps/agent/v1/preview',
                    params={'nid': nid}), 'expert_preview')
                version = preview.get('expertInfo', {}).get('sourceInfo', {}).get('version')
                md = (full.get('expertMd') or {}).get('customContent')
                if preview.get('nid') != nid or not version or not isinstance(md, str):
                    raise ValueError('EXPERT_VERSION_OR_CONTENT_UNVERIFIED')
                protection['experts'][nid] = full
                protection['previews'][nid] = preview
                experts[nid] = {'agent_md': md, 'version': str(version), 'bound_versions': {},
                    'skills': full.get('skillInfoList', [])}
            experts[nid]['bound_versions'][assistant['nid']] = str(bound[0]['version'])
    return sanitize_identity({'source': 'live-api', 'captured_at': iteration._now(),
        'assistant_prompt_digest': iteration._hash(prompts), 'experts': experts,
        'protection': protection}, user['userNid'])


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise ValueError('INVALID_ARGUMENTS')


def main(argv=None, *, transport_factory=RequestsTransport.from_env_file):
    argv = list(sys.argv[1:] if argv is None else argv)
    if '--help' in argv or '-h' in argv:
        print(json.dumps({'status': 'HELP', 'actions': ['discover', 'init', 'status', 'run-test', 'record-test',
            'record-review', 'propose-change', 'record-changes', 'verify-deployment', 'block'],
            'guide': 'team_acceptance/ITERATION_RUNBOOK.md'}, ensure_ascii=False))
        return 0
    parser = Parser(add_help=False)
    parser.add_argument('action', choices=('discover', 'init', 'status', 'run-test', 'record-test', 'record-review',
        'propose-change', 'record-changes', 'verify-deployment', 'block'))
    parser.add_argument('--session', type=Path)
    parser.add_argument('--assistant-id')
    for name in ('config', 'acceptance', 'criteria', 'scope', 'catalog', 'report', 'review', 'plan', 'env-file'):
        parser.add_argument('--' + name, type=Path)
    parser.add_argument('--reason')
    try:
        args = parser.parse_args(argv)
        def load(name):
            p = getattr(args, name)
            if p is None:
                raise ValueError('INPUT_FILE_REQUIRED')
            return json.loads(p.read_text())
        if args.action != 'discover' and args.session is None:
            raise ValueError('SESSION_REQUIRED')
        if args.action in ('discover', 'init', 'verify-deployment', 'run-test') and args.env_file is None:
            raise ValueError('ENV_FILE_REQUIRED')
        if args.action == 'discover':
            if not args.assistant_id:
                raise ValueError('ASSISTANT_ID_REQUIRED')
            result = discover(args.assistant_id, transport_factory(args.env_file))
        elif args.action == 'init':
            config = load('config')
            if args.acceptance is None:
                raise ValueError('ACCEPTANCE_REQUIRED')
            result = iteration.initialize(args.session, config, args.acceptance.read_text(), load('criteria'),
                load('scope'), load('catalog'), platform_snapshot=live_snapshot(config, transport_factory(args.env_file)))
        elif args.action == 'status':
            result = iteration.status(args.session)
        elif args.action == 'record-test':
            result = iteration.record_test(args.session, load('report'))
        elif args.action == 'run-test':
            result = iteration.run_test(args.session, transport_factory(args.env_file))
        elif args.action == 'record-review':
            result = iteration.record_review(args.session, load('review'))
        elif args.action == 'propose-change':
            result = iteration.propose_change(args.session, load('plan'))
        elif args.action == 'record-changes':
            result = iteration.record_changes(args.session)
        elif args.action == 'verify-deployment':
            iteration.status(args.session)
            config = json.loads((args.session / 'config.json').read_text())
            result = iteration.verify_deployment(args.session, live_snapshot(config, transport_factory(args.env_file)))
        else:
            result = iteration.block(args.session, args.reason)
        code = 0
    except ClientError as error:
        result, code = {'status': 'BLOCKED', 'error': error.code}, 2
    except (ValueError, OSError, KeyError, TypeError, AttributeError) as error:
        reason = str(error) if type(error) is ValueError and str(error).replace('_', '').isupper() else 'INVALID_INPUT_OR_STATE'
        result, code = {'status': 'BLOCKED', 'error': reason}, 2
    print(json.dumps(sanitize_json(result), ensure_ascii=False, sort_keys=True))
    return code
