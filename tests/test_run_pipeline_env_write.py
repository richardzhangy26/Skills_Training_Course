"""POLYMAS_NO_ENV_WRITE=1 時，兩個回寫 TASK_ID 的函式都不得寫 .env 檔。"""
import importlib.util
import os
import sys
from pathlib import Path

import pytest

from skill_training_build import create_configuration_from_markdown as cfm


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUN_PIPELINE_PATH = (
    PROJECT_ROOT / ".claude" / "skills" / "training-deploy-and-test" / "scripts" / "run_pipeline.py"
)
ORIGINAL = 'COOKIE=xyz\nTASK_ID="old-task"\n'


@pytest.fixture(scope="module")
def run_pipeline():
    """載入 run_pipeline。它在匯入時會讀根 .env 並改 sys.path，所以載入後還原兩者。"""
    saved_env, saved_path = dict(os.environ), list(sys.path)
    spec = importlib.util.spec_from_file_location("run_pipeline_under_test", RUN_PIPELINE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    try:
        spec.loader.exec_module(module)
    finally:
        os.environ.clear()
        os.environ.update(saved_env)
        sys.path[:] = saved_path
    return module


@pytest.fixture(params=["run_pipeline", "create_configuration"])
def write_task_id(request, run_pipeline):
    if request.param == "run_pipeline":
        return run_pipeline.write_task_id_to_env
    return cfm.write_root_task_id


def test_env_file_is_untouched_when_switch_is_on(write_task_id, tmp_path, monkeypatch):
    env_path = tmp_path / ".env"
    env_path.write_text(ORIGINAL, encoding="utf-8")
    missing_path = tmp_path / "missing" / ".env"
    monkeypatch.setenv("POLYMAS_NO_ENV_WRITE", "1")
    monkeypatch.setenv("TASK_ID", "old-task")

    write_task_id("new-task", env_path=env_path)
    write_task_id("new-task", env_path=missing_path)

    assert env_path.read_text(encoding="utf-8") == ORIGINAL
    assert not missing_path.parent.exists()
    assert os.environ["TASK_ID"] == "new-task"


@pytest.mark.parametrize("switch", [None, "", "0"])
def test_env_file_is_written_when_switch_is_off(write_task_id, tmp_path, monkeypatch, switch):
    env_path = tmp_path / ".env"
    env_path.write_text(ORIGINAL, encoding="utf-8")
    if switch is None:
        monkeypatch.delenv("POLYMAS_NO_ENV_WRITE", raising=False)
    else:
        monkeypatch.setenv("POLYMAS_NO_ENV_WRITE", switch)
    monkeypatch.setenv("TASK_ID", "old-task")

    write_task_id("new-task", env_path=env_path)

    assert env_path.read_text(encoding="utf-8") == 'COOKIE=xyz\nTASK_ID="new-task"\n'
    assert os.environ["TASK_ID"] == "new-task"
