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


def test_expert_does_not_access_or_select_courses():
    combined = "\n".join((read(CONFIG), read(DEPLOYMENT), read(SKILL_ROOT / "SKILL.md")))

    for forbidden in (
        "学生班课查询",
        "学生教学计划查询",
        "学生学习资源助手",
        "知识检索助手",
        "finance-news:{schoolId}:{userId}:{courseId}",
    ):
        assert forbidden not in combined
    assert "无需选择课程" in combined


def test_only_domain_skills_are_mounted_and_runtime_capabilities_are_builtin():
    config = read(CONFIG)
    deployment = read(DEPLOYMENT)
    skill_section = config.split("## 可用技能", 1)[1].split("## 工作流程", 1)[0]

    assert "1. `finance-news-commentary`" in skill_section
    assert "2. `平台通用工具 0.0.4`" in skill_section
    assert "cron 0.0.1" not in skill_section
    assert "channel-message" not in skill_section
    assert "channel_message" not in skill_section

    for token in (
        "`ask_user_question` 是 AI 助教内置工具",
        "`cron` 是 AI 助教内置工具",
        "不作为 Skill 挂载",
        "只挂载两项专业 Skill",
    ):
        assert token in config + deployment


def test_ask_user_question_collects_only_missing_schedule_topics_and_confirmation():
    config = read(CONFIG)

    for token in (
        "学生明确的信息不重复询问",
        "每轮最多三个相关问题",
        "主题：综合财经、宏观政策、资本市场、行业或公司",
        "频率：每日、工作日、每周或自定义",
        "时间与 IANA 时区",
        "取得明确确认",
        "确认前不创建或修改任务",
    ):
        assert token in config


def test_builtin_cron_commands_are_explicit_and_always_use_agent_id():
    combined = "\n".join((read(CONFIG), read(DEPLOYMENT)))

    for token in (
        "cron list --agent-id <当前专家>",
        "cron create --agent-id <当前专家>",
        "cron get <cron_job_id> --agent-id <当前专家>",
        "cron state <cron_job_id> --agent-id <当前专家>",
        "cron pause <cron_job_id> --agent-id <当前专家>",
        "cron resume <cron_job_id> --agent-id <当前专家>",
        "cron delete <cron_job_id> --agent-id <当前专家>",
        "cron run <cron_job_id> --agent-id <当前专家>",
    ):
        assert token in combined


def test_builtin_cron_reuses_stable_task_and_validates_creation():
    config = read(CONFIG)

    for token in (
        "finance-news:{schoolId}:{userId}:{agentId}",
        "只复用任务键和当前 `agent-id` 都完全匹配的任务",
        "不得按模糊名称选取",
        "已有等价活动任务时直接回读状态，不创建第二个任务",
        "cron create --agent-id <当前专家>",
        "plan_version=1",
        "cron get",
        "cron state",
        "只有工具真实返回可查询、已启用的任务，才报告订阅成功",
    ):
        assert token in config


def test_builtin_cron_plan_switch_is_rollback_safe():
    config = read(CONFIG)

    for token in (
        "验证旧任务",
        "保存旧计划",
        "cron pause <旧任务>",
        "递增 `plan_version`",
        "候选任务应初始暂停",
        "恢复候选，再删除保持暂停的旧任务",
        "候选创建、校验或恢复失败时删除候选并恢复旧任务",
        "候选无法删除时保持新旧均暂停",
    ):
        assert token in config


def test_builtin_cron_returns_final_answer_in_current_expert_conversation():
    combined = "\n".join((read(CONFIG), read(DEPLOYMENT)))

    for token in (
        "定时任务的最终回复直接显示在创建任务的当前专家对话中",
        "不调用任何消息发送 Skill",
        "将生成的简报作为本次 Cron 唤醒的最终回复直接返回",
        "不查询、选择或保存其他会话 ID",
    ):
        assert token in combined


def test_builtin_cron_contract_has_no_session_binding_or_message_delivery_state():
    combined = "\n".join(
        (
            read(CONFIG),
            read(DEPLOYMENT),
            read(SKILL_ROOT / "references" / "data-contract.md"),
        )
    )

    for forbidden in (
        "target_session_id",
        "binding_version",
        "trigger_target_session_id",
        "trigger_binding_version",
        "message_receipt",
        "delivery_key",
        "copaw chats list",
        "copaw channels send",
    ):
        assert forbidden not in combined

    for required in (
        "trigger_job_key",
        "trigger_plan_version",
        "trigger_agent_id",
        "skipped_stale_trigger",
    ):
        assert required in combined


def test_cron_maintenance_uses_verified_task_and_real_tool_receipts():
    config = read(CONFIG)

    for token in (
        "用任务键精确定位",
        "回读状态后报告",
        "再次 list/get 确认不存在后才报告退订完成",
        "两种方式都不新建任务",
        "订阅操作回执只包含内置 Cron 实际返回",
    ):
        assert token in config


def test_deployment_clearly_marks_online_cron_as_unverified():
    deployment = read(DEPLOYMENT)

    for token in (
        "真实平台联调",
        "本地 Markdown、脚本和测试通过不能替代",
        "cron run",
        "最终简报显示在当前专家对话中",
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
