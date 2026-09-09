"""三轮协议的合成行为测试，不代表线上发布验证。"""
import copy
import importlib
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def api():
    try:
        m = importlib.import_module('team_acceptance.iteration')
    except ModuleNotFoundError:
        m = None
    assert m is not None, '缺少三轮专家迭代协议'
    return m


def setup(tmp_path):
    from test_team_acceptance import config
    source = tmp_path / 'source'
    (source / 'expert').mkdir(parents=True)
    (source / 'expert/Agent.md').write_text('原专家提示词')
    (source / 'assistant.md').write_text('助教提示词')
    session = tmp_path / 'session'
    scope = {'source_root': str(source), 'resources': [
        {'kind': 'expert_agent_md', 'expert_nid': 'e1', 'path': 'expert/Agent.md'},
        {'kind': 'assistant_prompt', 'path': 'assistant.md'}]}
    criteria = [{'id': 'guide', 'requirement': '先引导学生回答，再反馈。'}]
    state = api().initialize(session, config(), '用户怎么问：病例。\n专家怎么做：引导。\n最后得到什么：反馈。',
                             criteria, scope, {'schema_version': 1, 'entries': [{'id': 'existing-search', 'name': '已有检索'}]},
                             platform_snapshot={'assistant_prompt_digest':'original',
                                'protection': {'assistants': {'a1': {'generalSetting': {}}}, 'experts': {}},
                                'experts':{'e1':{'agent_md':'原专家提示词','skills':[], 'version':'v6','bound_versions':{'a1':'v6'}},
                                           'e2':{'agent_md':'未计划专家','skills':[], 'version':'v1','bound_versions':{'a1':'v1'}}}})
    return session, source, state


def fail_review(session):
    from test_team_acceptance import config, evidence
    from team_acceptance.core import evaluate
    from datetime import datetime, timezone
    e = evidence()
    e['records'][0]['captured_at'] = datetime.now(timezone.utc).isoformat()
    e['records'][0]['trace_id'] += str(api().status(session)['iteration'])
    ident = e['records'][0]['trace_id']
    for receipt in ('send', 'readback'):
        e['records'][0][receipt]['trace_id'] = ident
    for row in e['records'][0]['readback']['messages']:
        row['trace_id'] = ident
    r = evaluate(config(), e)
    r['evidence_origin'] = 'captured-live-api'
    api().run_test(session, object(), runner=lambda *args: r)
    return api().record_review(session, {'criteria': [{'id': 'guide', 'verdict': 'fail',
        'reason': '回答直接给出依据，缺少引导', 'evidence': [{'case_id': 'query', 'message_id': 'm1', 'quote': '案例法条依据'}]}]})


def plan():
    return {'files': ['expert/Agent.md'], 'capability_type': 'domain',
            'reason': '补充先引导后反馈的顺序', 'reuse_review': {
                'checked_entry_ids': ['existing-search'], 'decision': 'reuse_existing',
                'reason': '继续复用已有检索，只修专家教学顺序'}}


def test_initialize_locks_acceptance_and_starts_at_baseline(tmp_path):
    session, _, state = setup(tmp_path)
    assert state['iteration'] == 0 and state['max_iterations'] == 3
    assert state['status'] == 'AWAITING_TEST'
    (session / 'acceptance.md').write_text('降低验收标准')
    with pytest.raises(ValueError, match='CONTRACT_CHANGED'):
        api().status(session)


def test_assistant_prompt_changes_pause_without_consuming_round(tmp_path):
    session, _, _ = setup(tmp_path)
    fail_review(session)
    p = plan(); p['files'] = ['assistant.md']
    r = api().propose_change(session, p)
    assert r['status'] == 'NEEDS_USER_AGREEMENT' and r['iteration'] == 0


def test_scope_escape_and_missing_reuse_are_rejected(tmp_path):
    session, _, _ = setup(tmp_path)
    fail_review(session)
    for paths in [['../outside.md'], ['expert/AGENTS.md'], ['/tmp/unsafe']]:
        p = plan(); p['files'] = paths
        with pytest.raises(ValueError): api().propose_change(session, p)
    p = plan(); p['reuse_review']['checked_entry_ids'] = ['invented']
    with pytest.raises(ValueError, match='CATALOG_REFERENCE_REQUIRED'):
        api().propose_change(session, p)


def test_review_needs_all_criteria_and_exact_dialogue_evidence(tmp_path):
    session, _, _ = setup(tmp_path)
    from test_team_acceptance import config, evidence
    from team_acceptance.core import evaluate
    from datetime import datetime, timezone
    e=evidence();e['records'][0]['captured_at']=datetime.now(timezone.utc).isoformat()
    r=evaluate(config(),e);r['evidence_origin']='captured-live-api'
    api().run_test(session, object(), runner=lambda *args: r)
    for verdict in [{'criteria': []}, {'criteria': [{'id':'guide','verdict':'pass','reason':'满足','evidence':[{'case_id':'query','message_id':'m1','quote':'不存在的引用'}]}]}]:
        with pytest.raises(ValueError):api().record_review(session,verdict)


def test_three_repairs_then_stop_and_do_not_change_criteria(tmp_path):
    session, source, _ = setup(tmp_path)
    for round_number in range(1,4):
        assert fail_review(session)['status'] == 'NEEDS_REPAIR'
        r=api().propose_change(session,plan())
        assert r['iteration']==round_number
        (source/'expert/Agent.md').write_text('修复提示词'+str(round_number))
        r=api().record_changes(session)
        assert r['status']=='AWAITING_DEPLOYMENT'
        snapshot=copy.deepcopy(api().status(session)['platform_snapshot'])
        snapshot['experts']['e1'].update(agent_md='修复提示词'+str(round_number),version='7',bound_versions={'a1':'7'})
        r=api().verify_deployment(session,snapshot)
        assert r['status']=='AWAITING_TEST'
        runtime=json.loads((session/'runtime-config.json').read_text())
        assert runtime['assistants'][0]['experts'][0]['expected_version']=='7'
        original=json.loads((session/'config.json').read_text())
        assert runtime['cases']==original['cases']
    assert fail_review(session)['status']=='ITERATION_LIMIT_REACHED'
    with pytest.raises(ValueError):api().propose_change(session,plan())


def test_changes_outside_plan_or_wrong_online_content_block(tmp_path):
    session, source, _=setup(tmp_path);fail_review(session)
    api().propose_change(session,plan())
    (source/'expert/Agent.md').write_text('新版')
    (source/'assistant.md').write_text('未协商修改')
    with pytest.raises(ValueError,match='OUT_OF_SCOPE_CHANGE'):api().record_changes(session)
    (source/'assistant.md').write_text('助教提示词')
    api().record_changes(session)
    r=api().verify_deployment(session,{'assistant_prompt_digest':'original','experts':{'e1':{'agent_md':'旧版'}}})
    assert r['status']=='AWAITING_DEPLOYMENT'
