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


def section(text, heading, next_heading):
    return text[text.index(heading) : text.index(next_heading, text.index(heading))]


def validate_workflow_text(config):
    """Validate the documented stale-trigger and no-double-send safety seam."""
    cron = section(config, "### 3. Cron 两阶段切换", "### 4. 定时生成与安全投递")
    delivery = section(config, "### 4. 定时生成与安全投递", "### 5. 结果交付")
    cron_steps = (
        "暂停已验证旧任务",
        "创建候选任务",
        "初始暂停",
        "校验候选任务",
        "写订阅新ID/version",
        "启用候选任务",
        "删除旧任务",
    )
    trigger_fields = (
        "trigger_cron_job_id",
        "trigger_job_key",
        "trigger_plan_version",
        "trigger_agent_id",
    )
    required_delivery = (
        "发送前重读 subscription",
        "当前 `cron_job_id`",
        "当前 `job_key`",
        "当前 `plan_version`",
        "当前专家 `agent-id`",
        "skipped_stale_trigger",
        "不调用 `channel-message`",
        "不更新成功历史",
    )
    compensation_branches = (
        (
            "候选创建失败",
            "恢复旧任务",
            "订阅保持旧ID/version",
        ),
        (
            "候选创建成功但校验失败",
            "先删除候选",
            "删除成功后恢复旧订阅/旧任务",
            "删除失败则新旧均保持暂停",
            "orphaned_candidate",
            "订阅status=paused",
            "停止投递",
        ),
        (
            "候选校验成功但写订阅新ID/version失败",
            "先删除候选",
            "删除成功后恢复旧订阅/旧任务",
            "删除失败则新旧均保持暂停",
            "orphaned_candidate",
            "订阅status=paused",
            "停止投递",
        ),
        (
            "候选启用失败",
            "先删除候选",
            "删除成功后恢复旧订阅/旧任务",
            "删除失败则新旧均保持暂停",
            "orphaned_candidate",
            "订阅status=paused",
            "停止投递",
        ),
    )
    if any(branch[0] not in cron for branch in compensation_branches):
        return False

    def branch_has_ordered_compensation(index):
        branch = compensation_branches[index]
        start = cron.index(branch[0])
        end = (
            cron.index(compensation_branches[index + 1][0])
            if index + 1 < len(compensation_branches)
            else len(cron)
        )
        branch_text = cron[start:end]
        return all(token in branch_text for token in branch) and [
            branch_text.index(token) for token in branch
        ] == sorted(branch_text.index(token) for token in branch)

    return (
        all(token in cron for token in cron_steps)
        and [cron.index(step) for step in cron_steps]
        == sorted(cron.index(step) for step in cron_steps)
        and "候选启用失败" in cron
        and "删除候选" in cron
        and "恢复旧订阅/旧任务" in cron
        and "候选删除失败" in cron
        and "新旧均保持暂停" in cron
        and "禁止双发" in cron
        and all(branch_has_ordered_compensation(index) for index in range(len(compensation_branches)))
        and all(token in delivery for token in trigger_fields + required_delivery)
        and delivery.index("发送前重读 subscription")
        < delivery.index("channel-message 0.0.1")
        and "briefing_history.jsonl" in delivery
        and all(
            field in delivery
            for field in (
                "edition_id",
                "item_id",
                "source_url",
                "theory_citations",
                "course_id",
                "target_session_id",
                "message_receipt",
            )
        )
    )


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
    for plan_field in ("频率", "每日", "工作日", "每周", "自定义", "星期", "时间", "IANA时区", "主题"):
        assert plan_field in config
    assert "真正等待确认" in config


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

    assert validate_workflow_text(config)


def test_workflow_validator_rejects_missing_trigger_id_and_send_before_second_read():
    config = read(CONFIG)
    delivery = section(config, "### 4. 定时生成与安全投递", "### 5. 结果交付")
    missing_delivery = delivery.replace("trigger_cron_job_id", "")
    missing_trigger = config.replace(delivery, missing_delivery, 1)
    assert not validate_workflow_text(missing_trigger)

    reordered_delivery = (
        delivery.replace("发送前重读 subscription", "TEMP", 1)
        .replace(
            "channel-message 0.0.1",
            "发送前重读 subscription\n使用 channel-message 0.0.1",
            1,
        )
        .replace("TEMP", "使用 channel-message 0.0.1", 1)
    )
    reordered = config.replace(delivery, reordered_delivery, 1)
    assert not validate_workflow_text(reordered)


def test_workflow_validator_rejects_each_required_cron_failure_branch():
    config = read(CONFIG)

    for failure_sentence in (
        "候选创建失败",
        "候选创建成功但校验失败",
        "候选校验成功但写订阅新ID/version失败",
    ):
        assert not validate_workflow_text(config.replace(failure_sentence, "", 1))


def test_expert_config_records_delivered_briefing_history_and_limits_expansion_scope():
    config = read(CONFIG)
    delivery = section(config, "### 4. 定时生成与安全投递", "### 5. 结果交付")
    route = section(config, "### 1. 任务接收与路由", "### 2. 订阅记录与版本")

    assert "成功投递后" in delivery
    assert "briefing_history.jsonl" in delivery
    assert "最近已投递记录" in route
    assert "同一学生/课程/会话" in route


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
        "候选创建失败",
        "候选创建成功但校验失败",
        "候选校验成功但写订阅新ID/version失败",
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
