import hashlib
import subprocess
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).parents[1]
CONFIG = ROOT / "EXPERT_CONFIG.md"
DEPLOYMENT = ROOT / "DEPLOYMENT.md"
PACKAGER = ROOT / "scripts" / "package_skill.py"
SKILL_NAME = "finance-news-course-commentary"


def read(path):
    return path.read_text(encoding="utf-8")


def test_expert_config_declares_identity_complete_agent_and_exact_skill_mounts():
    config = read(CONFIG)

    for token in (
        "财经新闻推送专家",
        "财讯小信使",
        "---\nname: ${agent_name}\n---",
        "## 您的角色",
        "## 核心职责",
        "## 可用技能",
        "## 工作流程",
        "## 我不做什么",
        "## 工作风格",
        "## 最佳实践",
    ):
        assert token in config

    mounts = (
        "finance-news-course-commentary",
        "平台通用工具 0.0.4",
        "知识检索助手 1.0.1",
        "学生班课查询 1.0.1",
        "学生教学计划查询 1.0.0",
        "学生学习资源助手 1.0.0",
        "cron 0.0.1",
        "channel-message 0.0.1",
    )
    positions = [config.index(mount) for mount in mounts]
    assert positions == sorted(positions)


def test_expert_config_requires_course_plan_and_consent_before_subscription():
    config = read(CONFIG)

    for field in (
        "status",
        "course",
        "topics",
        "schedule",
        "timezone",
        "consent_at",
        "job_key",
        "plan_version",
        "cron_job_id",
        "target_session_id",
        "last_success_at",
        "next_run_at",
        "finance-news:{schoolId}:{userId}:{courseId}",
    ):
        assert field in config
    assert "ask_user_question" in config
    assert "课程候选" in config
    assert "学生自己填写计划" in config
    assert "确认" in config
    assert "不预先绑定课程" in config


def test_expert_config_covers_subscription_delivery_interaction_and_lifecycle_routes():
    config = read(CONFIG)

    for route in (
        "首次订阅",
        "定时生成/投递",
        "展开某条新闻",
        "修改课程/计划",
        "暂停",
        "恢复",
        "退订",
    ):
        assert route in config
    for context_field in ("edition_id", "item_id", "course", "target_session_id"):
        assert context_field in config


def test_expert_config_enforces_cron_swap_and_delivery_safety():
    config = read(CONFIG)

    for token in (
        "--agent-id",
        "job_key",
        "两阶段切换",
        "新任务",
        "旧任务",
        "回滚",
        "订阅状态",
        "plan_version",
        "个人会话",
        "唯一",
        "停止",
        "不得降级到班级群",
        "channel-message",
        "发送成功",
        "last_success_at",
    ):
        assert token in config


def test_deployment_document_has_safe_real_platform_checklist_and_upload_instructions():
    deployment = read(DEPLOYMENT)

    for token in (
        "finance-news-course-commentary.zip",
        "财经新闻推送专家",
        "财讯小信使",
        "挂载顺序",
        "ask_user_question",
        "Cron",
        "channel-message",
        "真实联调",
        "未验证",
        "Token",
        "Cookie",
    ):
        assert token in deployment


def test_packager_produces_deterministic_upload_root_without_sensitive_or_test_files(tmp_path):
    first = tmp_path / "first.zip"
    second = tmp_path / "second.zip"

    for output in (first, second):
        result = subprocess.run(
            [sys.executable, str(PACKAGER), "--output", str(output)],
            text=True,
            capture_output=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        assert result.stderr == ""
        assert output.exists()

    assert hashlib.sha256(first.read_bytes()).digest() == hashlib.sha256(second.read_bytes()).digest()
    with zipfile.ZipFile(first) as archive:
        names = archive.namelist()
        assert names == sorted(names)
        assert names == [
            f"{SKILL_NAME}/SKILL.md",
            f"{SKILL_NAME}/output_format/briefing.md",
            f"{SKILL_NAME}/references/data-contract.md",
            f"{SKILL_NAME}/references/source-policy.md",
            f"{SKILL_NAME}/scripts/normalize_candidates.py",
        ]
        assert all(not Path(name).name.startswith(".") for name in names)
        assert all("test" not in Path(name).parts for name in names)
        assert all("__pycache__" not in Path(name).parts for name in names)
        assert all("token" not in name.lower() and "cookie" not in name.lower() for name in names)
