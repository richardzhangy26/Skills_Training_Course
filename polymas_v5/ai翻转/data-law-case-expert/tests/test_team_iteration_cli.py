import importlib
import json
from pathlib import Path
import sys

import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

def api():
    try:m=importlib.import_module('team_acceptance.iteration_cli')
    except ModuleNotFoundError:m=None
    assert m is not None,'需要只读部署回读与CLI'
    return m

class SnapshotTransport:
    def __init__(self):self.calls=[]
    def request(self,method,path,*,params=None,json=None):
        self.calls.append(path)
        if path.endswith('get-current-user-detail'):d={'userNid':'private-user','roleList':[{'roleCode':'school_teacher'}]}
        elif path.endswith('/agent/list'):d=[{'friendNid':'a1','friendNickName':'合成助教','appType':'AUTO_SMART_ROBOT','appCategory':'AI_COURSE_REPRESENTATIVE','isV5':True}]
        elif path.endswith('agentFullConfig') and params['agentNid']=='a1':d={'basicInfo':{'nid':'a1'},'agentMd':{'customContent':'助教'},'subAgentVOS':[{'agentNid':'e1','enabled':True,'version':'6'}]}
        elif path.endswith('agentFullConfig'):d={'basicInfo':{'nid':'e1'},'expertMd':{'customContent':'专家'},'skillInfoList':[]}
        elif path.endswith('preview'):d={'nid':'e1','expertInfo':{'sourceInfo':{'version':'6'}}}
        else:raise AssertionError('未授权路径')
        return {'code':200,'data':d}

def test_snapshot_reads_exact_expert_and_binding_versions_without_writes():
    from test_team_acceptance import config
    t=SnapshotTransport();r=api().live_snapshot(config(),t)
    assert r['experts']['e1']['version']=='6'
    assert r['experts']['e1']['bound_versions']=={'a1':'6'}
    assert r['experts']['e1']['agent_md']=='专家'
    assert all('save' not in p and 'publish' not in p for p in t.calls)
    assert 'private-user' not in json.dumps(r)
    assert r['protection']['assistants']['a1']['agentMd']['customContent']=='助教'
    assert r['protection']['experts']['e1']['expertMd']['customContent']=='专家'


def test_live_snapshot_protects_disabled_unplanned_experts_and_complete_skill_binding():
    from test_team_acceptance import config
    class ExtendedTransport(SnapshotTransport):
        def request(self,*args,**kwargs):
            value=super().request(*args,**kwargs)
            nid=kwargs.get('params',{}).get('agentNid')
            if args[1].endswith('agentFullConfig') and nid=='a1':
                value['data']['subAgentVOS'].append({'agentNid':'e2','enabled':False,'version':'6'})
            elif args[1].endswith('agentFullConfig') and nid=='e2':
                value['data']['basicInfo']['nid']='e2'
                value['data']['skillInfoList']=[{'skillNid':'k','enabled':False,'rule':3,'permission':{'write':True}}]
            elif args[1].endswith('preview') and kwargs.get('params',{}).get('nid')=='e2':
                value['data']['nid']='e2'
            return value
    value=api().live_snapshot(config(),ExtendedTransport())
    assert value['experts']['e2']['skills'][0]['permission']=={'write':True}
    assert value['protection']['assistants']['a1']['subAgentVOS'][1]['enabled'] is False


def test_run_test_cli_requires_explicit_env_file(capsys):
    assert api().main(['run-test','--session','synthetic'])==2
    assert json.loads(capsys.readouterr().out)['error']=='ENV_FILE_REQUIRED'

def test_cli_missing_inputs_returns_one_safe_json(capsys):
    assert api().main([])==2
    r=json.loads(capsys.readouterr().out)
    assert r['status']=='BLOCKED'

def test_discover_uses_agent_id_and_never_invents_acceptance_cases():
    class DiscoveryTransport(SnapshotTransport):
        def request(self,*args,**kwargs):
            r=super().request(*args,**kwargs)
            if args[1].endswith('agentFullConfig') and kwargs.get('params',{}).get('agentNid')=='a1':
                r['data']['subAgentVOS'][0]['name']='合成专家'
            return r
    r=api().discover('a1',DiscoveryTransport())
    assert r['config']['assistants'][0]['experts'][0]['nid']=='e1'
    assert r['config']['cases']==[] and r['requires_test_design'] is True

def test_old_bound_version_does_not_unlock_retest(tmp_path):
    from test_team_iteration import setup,fail_review,plan
    from team_acceptance import iteration
    session,source,_=setup(tmp_path);fail_review(session)
    iteration.propose_change(session,plan());(source/'expert/Agent.md').write_text('新版')
    iteration.record_changes(session)
    r=iteration.verify_deployment(session,{'assistant_prompt_digest':'original','experts':{'e1':{'agent_md':'新版','version':'7','bound_versions':{'a1':'6'}}}})
    assert r['status']=='AWAITING_DEPLOYMENT'
    assert r['deployment_blocker']=='BOUND_VERSION_MISMATCH'
