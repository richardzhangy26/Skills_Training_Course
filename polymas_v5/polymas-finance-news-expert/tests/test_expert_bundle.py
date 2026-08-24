import hashlib
import importlib.util
import json
import subprocess
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).parents[1]
CONFIG = ROOT / "EXPERT_CONFIG.md"
DEPLOYMENT = ROOT / "DEPLOYMENT.md"
PACKAGER = ROOT / "scripts" / "package_skill.py"
SKILL_NAME = "finance-news-commentary"
SKILL_ROOT = ROOT / SKILL_NAME
PACKAGER_SPEC = importlib.util.spec_from_file_location("finance_skill_packager", PACKAGER)
PACKAGER_MODULE = importlib.util.module_from_spec(PACKAGER_SPEC)
PACKAGER_SPEC.loader.exec_module(PACKAGER_MODULE)
CREDENTIAL_PATTERNS = PACKAGER_MODULE.CREDENTIAL_PATTERNS


def read(path):
    return path.read_text(encoding="utf-8")


def test_expert_uses_pds_template_and_general_finance_identity():
    config = read(CONFIG)

    for token in (
        "name: ${agent_name}",
        "## 您的角色",
        "## 核心职责",
        "## 可用技能",
        "## 工作流程",
        "## 我不做什么",
        "## 工作风格",
        "## 最佳实践",
        "财经新闻推送专家",
        "财讯小信使",
        "通用财经知识分析",
    ):
        assert token in config
    assert "${agent\\_name}" not in config


def test_subscription_defaults_to_current_expert_session_without_course_access():
    config = read(CONFIG)
    deployment = read(DEPLOYMENT)
    skill = read(SKILL_ROOT / "SKILL.md")
    combined = "\n".join((config, deployment, skill))

    for forbidden in (
        "学生班课查询",
        "学生教学计划查询",
        "学生学习资源助手",
        "知识检索助手",
        "finance-news:{schoolId}:{userId}:{courseId}",
    ):
        assert forbidden not in combined

    for required in (
        "无需选择课程",
        "当前运行时的本专家个人会话",
        "finance-news:{schoolId}:{userId}:{agentId}",
        "不查询或改绑到其他会话",
    ):
        assert required in combined


def test_skill_mount_order_contains_only_domain_search_cron_and_message():
    config = read(CONFIG)
    expected = (
        "1. `finance-news-commentary`",
        "2. `平台通用工具 0.0.4`",
        "3. `cron 0.0.1`",
        "4. `channel-message 0.0.1`",
    )

    positions = [config.index(token) for token in expected]
    assert positions == sorted(positions)
    assert "四项技能" in config


def test_ask_user_question_only_collects_schedule_topics_and_confirmation():
    config = read(CONFIG)

    for token in (
        "调用 `ask_user_question` 收集频率、星期、时间、IANA 时区和财经主题",
        "展示规范化计划并取得明确订阅确认",
        "并真正等待",
        "重复订阅不创建第二个 Cron",
    ):
        assert token in config


def test_subscription_schema_has_agent_job_key_and_no_course_object():
    config = read(CONFIG)
    schema = config[config.index("每份订阅只绑定") : config.index("### 3. Cron")]

    for token in (
        '"job_key": "finance-news:{schoolId}:{userId}:{agentId}"',
        '"target_session_id": "当前专家个人会话标识"',
        '"binding_version": 1',
        '"plan_version": 1',
        '"auto_delivery_status": "enabled | disabled_atomicity"',
    ):
        assert token in schema
    assert '"course"' not in schema
    assert "courseId" not in schema


def test_first_subscription_uses_atomic_job_key_claim_before_cron_creation():
    config = read(CONFIG)

    for token in (
        "订阅持久层原子 `create-if-absent`",
        "唯一约束",
        "原子 claim 成功者",
        "竞争失败者复用既有订阅",
        "不创建 Cron",
    ):
        assert token in config


def test_cron_activation_switch_and_recovery_are_fail_closed():
    config = read(CONFIG)

    for token in (
        "pending_activation",
        "初始暂停的候选 Cron",
        "写候选 ID",
        "启用并回读",
        "最后写 `active`",
        "暂停已验证旧任务",
        "写新 ID/version",
        "旧 `cron_job_id`、旧 `plan_version`、旧计划",
        "恢复旧订阅与旧任务",
        "恢复或清理失败时新旧均暂停",
        "recovery_required=true",
        "禁止双发",
        "不得直接写 `active`",
    ):
        assert token in config


def test_delivery_revalidates_current_agent_session_and_stale_trigger():
    config = read(CONFIG)

    for token in (
        "trigger_cron_job_id",
        "trigger_job_key",
        "trigger_plan_version",
        "trigger_agent_id",
        "trigger_binding_version",
        "trigger_target_session_id",
        "target_session_id",
        "同一学生、当前专家且为个人会话",
        "skipped_stale_trigger",
        "不调用 `channel-message`",
        "不更新成功历史",
        "逐一比对 Cron ID、任务键、计划版本、agent-id、绑定版本和目标会话",
    ):
        assert token in config


def test_rebind_pauses_cron_and_cas_increments_binding_version():
    config = read(CONFIG)

    for token in (
        "暂停当前 Cron",
        "CAS",
        "binding_version",
        "递增",
        "恢复旧绑定与 Cron",
        "旧触发",
        "skipped_stale_trigger",
    ):
        assert token in config


def test_delivery_requires_atomic_key_and_records_only_confirmed_success():
    config = read(CONFIG)

    for token in (
        "delivery_key={job_key}:{plan_version}:{edition_id}",
        "create-if-absent",
        "skipped_duplicate",
        "delivery_uncertain",
        "delivery_atomicity_unavailable",
        "disabled_atomicity",
        "不自动重发",
        "不更新 `last_success_at`",
        "schedule_state_error",
    ):
        assert token in config


def test_history_is_scoped_to_student_agent_and_bound_session():
    config = read(CONFIG)

    for token in (
        "schoolId/userId/agentId/target_session_id",
        '"agent_id": "当前专家标识"',
        '"target_session_id": "已绑定的当前专家个人会话"',
        '"retrieved_at": "带时区检索时间"',
        '"theory_analysis": "通用财经知识分析"',
        '"source": "规范化来源"',
        '"url": "https://www.pbc.gov.cn/example"',
        '"published_at": "带时区发布时间"',
        '"source_level": 1',
        "不使用其他会话或未投递草稿",
    ):
        assert token in config


def test_deployment_matches_no_course_current_session_mode():
    deployment = read(DEPLOYMENT)

    for token in (
        "finance-news-commentary.zip",
        "四项能力",
        "当前运行时会话自动绑定",
        "不查询或改绑到其他会话",
        "finance-news:{schoolId}:{userId}:{agentId}",
        "不触发任何课程查询",
        "真实平台联调",
    ):
        assert token in deployment


def test_packager_produces_deterministic_upload_root_without_sensitive_files(tmp_path):
    first = tmp_path / "first.zip"
    second = tmp_path / "second.zip"

    for output in (first, second):
        result = subprocess.run(
            [sys.executable, str(PACKAGER), "--output", str(output)],
            text=True,
            capture_output=True,
            check=False,
        )
        assert result.returncode == 0, result.stdout
        assert result.stderr == ""

    assert hashlib.sha256(first.read_bytes()).digest() == hashlib.sha256(second.read_bytes()).digest()
    with zipfile.ZipFile(first) as archive:
        names = archive.namelist()
        assert names == [
            f"{SKILL_NAME}/SKILL.md",
            f"{SKILL_NAME}/output_format/briefing.md",
            f"{SKILL_NAME}/references/data-contract.md",
            f"{SKILL_NAME}/references/source-policy.md",
            f"{SKILL_NAME}/scripts/normalize_candidates.py",
        ]
        for name in names:
            body = archive.read(name)
            source = ROOT / Path(name)
            assert hashlib.sha256(body).digest() == hashlib.sha256(source.read_bytes()).digest()
            text = body.decode("utf-8")
            assert all(pattern.search(text) is None for pattern in CREDENTIAL_PATTERNS)


def test_packager_help_and_unknown_arguments_are_json_only():
    help_result = subprocess.run(
        [sys.executable, str(PACKAGER), "--help"],
        text=True,
        capture_output=True,
        check=False,
    )
    bad_result = subprocess.run(
        [sys.executable, str(PACKAGER), "--unexpected"],
        text=True,
        capture_output=True,
        check=False,
    )

    assert help_result.returncode == 0
    assert help_result.stderr == ""
    assert json.loads(help_result.stdout) == {
        "help": "生成可上传的财经新闻通用点评 Skill ZIP",
        "options": ["--help", "--output"],
    }
    assert bad_result.returncode != 0
    assert bad_result.stderr == ""
    assert json.loads(bad_result.stdout) == {"error": "invalid command-line arguments"}


def test_packager_credential_patterns_cover_common_secret_shapes():
    examples = (
        '"token": "secretvalue123"',
        "Authorization: Bearer abcdefghijklmnopqrstuvwxyz",
        'PASSWORD="!S3cret-passphrase-2026"',
        "https://example.invalid/blob?sig=abcdefghijklmnopqrstuvwxyz",
        "".join(("sk", "_live_", "abcdefghijklmnopqrstuvwxyz123456")),
        "redis://:password@example.invalid/0",
        "-----BEGIN PRIVATE KEY-----",
    )

    for example in examples:
        assert PACKAGER_MODULE.contains_potential_credential(example)
