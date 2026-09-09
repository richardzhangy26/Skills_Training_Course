import importlib
import json
import os
from pathlib import Path
import subprocess
import sys

from test_team_acceptance import ROOT, config, evidence, ReadTransport


def cli():
    try:
        module = importlib.import_module('team_acceptance.cli')
    except ModuleNotFoundError:
        module = None
    assert module is not None, '需要独立 CLI'
    return module


def files(tmp_path):
    settings, records = tmp_path / 'config.json', tmp_path / 'evidence.json'
    settings.write_text(json.dumps(config()))
    records.write_text(json.dumps(evidence()))
    return settings, records


def test_cli_evaluate_offline_single_json(tmp_path, capsys):
    module = cli()
    settings, records = files(tmp_path)
    result = module.main(['evaluate', '--config', str(settings), '--evidence', str(records),
                          '--report-prefix', str(tmp_path / 'out' / 'report')])
    output = json.loads(capsys.readouterr().out)
    assert result == 0
    assert output['status'] == 'pass'
    assert Path(output['reports']['json']).is_file()


def test_cli_preflight_requires_explicit_env(tmp_path, capsys):
    module = cli()
    settings, _ = files(tmp_path)
    os.environ['AUTHORIZATION'] = 'must-not-use'
    try:
        assert module.main(['preflight', '--config', str(settings)]) == 2
    finally:
        del os.environ['AUTHORIZATION']
    output = json.loads(capsys.readouterr().out)
    assert output['error'] == 'explicit_env_file_required'


def test_preflight_transport_injection_has_no_live_dependency(tmp_path, capsys):
    module = cli()
    settings, _ = files(tmp_path)
    assert module.main(['preflight', '--config', str(settings), '--env-file', 'synthetic.env'],
                       transport_factory=lambda path: ReadTransport()) == 3
    assert json.loads(capsys.readouterr().out)['status'] == 'unverified'


def test_cli_entrypoint_invalid_arguments_single_json():
    cli()
    run = subprocess.run([sys.executable, '-m', 'team_acceptance', 'unexpected'],
                         cwd=ROOT, text=True, capture_output=True)
    assert run.returncode == 2
    assert json.loads(run.stdout)['status'] == 'fail'
    assert not run.stderr
