import hashlib
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).parents[1]
CONFIG = ROOT / "EXPERT_CONFIG.md"
DEPLOYMENT = ROOT / "DEPLOYMENT.md"
PACKAGER = ROOT / "scripts" / "package_skill.py"
SKILL_NAME = "finance-news-course-commentary"
CREDENTIAL_PATTERNS = (
    re.compile(
        r"(?i)[\"']?(?:authorization|cookie|token|api[_-]?key)[\"']?"
        r"\s*[:=]\s*[\"']?(?:(?:bearer|basic)\s+)?[A-Za-z0-9._~+/=-]{8,}"
    ),
    re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),
)


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


def validate_course_change_and_compensation(config):
    cron = section(config, "### 3. Cron 两阶段切换", "### 4. 定时生成与安全投递")
    course_change_steps = (
        "课程变更禁止进入同 `job_key` 计划切换",
        "创建新课程订阅候选",
        "校验新课程订阅候选",
        "启用新课程订阅",
        "停用旧课程 Cron",
        "旧订阅 `status=unsubscribed`",
        "superseded_by_job_key",
    )
    second_order_tokens = (
        "旧任务暂停失败",
        "原订阅、旧任务和旧版本保持不变",
        "恢复旧任务失败",
        "恢复旧订阅失败",
        "新旧任务均保持暂停",
        "status=paused",
        "recovery_required=true",
        "orphaned_cron_job_ids",
    )
    course_failure_tokens = (
        "新课程候选失败",
        "删除或暂停新候选",
        "旧订阅继续 `active`",
    )
    return (
        all(token in cron for token in course_change_steps)
        and [cron.index(token) for token in course_change_steps]
        == sorted(cron.index(token) for token in course_change_steps)
        and all(token in cron for token in second_order_tokens)
        and cron.index("旧任务暂停失败")
        < cron.index("创建候选任务")
        and all(token in cron for token in course_failure_tokens)
    )


def validate_delivery_ledger_and_history(config):
    route = section(config, "### 1. 任务接收与路由", "### 2. 订阅记录与版本")
    delivery = section(config, "### 4. 定时生成与安全投递", "### 5. 结果交付")
    ledger_steps = (
        "读取 delivery ledger",
        "写入 `pending`",
        "正式调用 `channel-message`",
        "原子更新为 `sent`",
    )
    ledger_states = (
        "delivery_key={job_key}:{plan_version}:{edition_id}",
        "`sent` 返回 `skipped_duplicate`",
        "`pending` 或 `uncertain` 返回 `delivery_uncertain`",
        "metadata.delivery_key",
        "发送成功但账本写入失败",
        "不自动重发",
    )
    history_tokens = (
        "finance_news/{schoolId}/{userId}/briefing_history.jsonl",
        "https://www.pbc.gov.cn/example",
        '"job_key"',
        '"course": {"course_id"',
        '"target_session_id"',
        '"message_receipt"',
        '"items": [',
        '"item_id"',
        '"title"',
        '"fact_summary"',
        '"theory_analysis"',
        '"discussion_question"',
        '"source_url"',
        '"theory_citations"',
    )
    followup_tokens = (
        "运行时 `schoolId/userId` 路径",
        "当前 `job_key`",
        "完整 `course_id/course_name`",
        "当前 `target_session_id`",
        "读取 `item_id` 之前",
    )
    return (
        all(token in delivery for token in ledger_steps + ledger_states + history_tokens)
        and [delivery.index(token) for token in ledger_steps]
        == sorted(delivery.index(token) for token in ledger_steps)
        and all(token in route for token in followup_tokens)
    )


def validate_initial_activation_and_course_migration(config):
    cron = section(config, "### 3. Cron 两阶段切换", "### 4. 定时生成与安全投递")
    initial_steps = (
        "全新订阅激活顺序",
        "`status=pending_activation`",
        "`cron_job_id=null`",
        "创建初始暂停的候选任务",
        "校验全新订阅候选",
        "写入候选 `cron_job_id`",
        "启用全新订阅候选",
        "确认任务已启用",
        "`status=active`",
    )
    initial_failures = (
        "尚未创建候选即失败",
        "删除订阅草稿",
        "独立 activation audit",
        "候选清理成功",
        "仅候选清理失败",
        "`status=paused`",
        "`activation_error`",
        "`recovery_required=true`",
        "`orphaned_cron_job_ids`",
        "禁止 active 无任务",
    )
    migration_steps = (
        "改课迁移顺序",
        "新订阅 `status=pending_activation`",
        "创建新课程订阅候选",
        "校验新课程订阅候选",
        "启用新课程订阅候选",
        "停用旧课程 Cron",
        "旧订阅 `status=unsubscribed`",
        "新订阅 `status=active`",
    )
    migration_failures = (
        "旧 Cron 停用失败",
        "旧订阅退订写入失败",
        "暂停新任务",
        "恢复旧订阅和旧任务为 `active`",
        "新订阅置为 `status=paused`",
        "`migration_error`",
        "清理新候选",
        "恢复或清理失败",
        "双方 `status=paused`",
        "`recovery_required=true`",
        "`orphaned_cron_job_ids`",
    )
    return (
        all(token in cron for token in initial_steps + initial_failures)
        and [cron.index(token) for token in initial_steps]
        == sorted(cron.index(token) for token in initial_steps)
        and all(token in cron for token in migration_steps + migration_failures)
        and [cron.index(token) for token in migration_steps]
        == sorted(cron.index(token) for token in migration_steps)
    )


def validate_atomic_delivery_and_next_run(config):
    delivery = section(config, "### 4. 定时生成与安全投递", "### 5. 结果交付")
    atomic_tokens = (
        "平台持久化层的原子 `create-if-absent`/唯一约束",
        "`channel-message` 原生幂等键",
        "只有拿到原子锁的执行者",
        "正式调用 `channel-message`",
        "`sent` 返回 `skipped_duplicate`",
        "`pending` 或 `uncertain` 返回 `delivery_uncertain`",
        "`delivery_atomicity_unavailable`",
        "禁用自动发送",
        "不得用普通“读后追加”冒充原子锁",
    )
    next_run_tokens = (
        "无论 `sent`、`skipped`、`failed` 或 `uncertain`",
        "从当前 Cron 状态回读",
        "更新 `next_run_at`",
        "`last_success_at` 仅在 `sent`",
    )
    return (
        all(token in delivery for token in atomic_tokens + next_run_tokens)
        and delivery.index("只有拿到原子锁的执行者")
        < delivery.index("正式调用 `channel-message`")
    )


def validate_persistent_atomicity_disable_and_recovery(config):
    subscription = section(config, "### 2. 订阅记录与版本", "### 3. Cron 两阶段切换")
    delivery = section(config, "### 4. 定时生成与安全投递", "### 5. 结果交付")
    route = section(config, "### 1. 任务接收与路由", "### 2. 订阅记录与版本")
    fields = (
        '"auto_delivery_status": "enabled | disabled_atomicity"',
        '"delivery_error": null',
    )
    disable_steps = (
        "原子能力不可用持久停发顺序",
        "暂停当前 Cron（显式传当前 `--agent-id`）",
        "`status=paused`",
        "`auto_delivery_status=disabled_atomicity`",
        "`delivery_error=delivery_atomicity_unavailable`",
        "`next_run_at=null`",
    )
    disable_failures = (
        "Cron 暂停或订阅写入任一失败",
        "`recovery_required=true`",
        "记录真实错误",
        "仍不得发送",
    )
    recovery = (
        "原子能力恢复门禁",
        "重新验证原子能力",
        "清空 `delivery_error`",
        "`auto_delivery_status=enabled`",
        "恢复 Cron",
        "否则禁止写 `active`",
    )
    return (
        all(token in subscription for token in fields)
        and all(token in delivery for token in disable_steps + disable_failures)
        and [delivery.index(token) for token in disable_steps]
        == sorted(delivery.index(token) for token in disable_steps)
        and all(token in route for token in recovery)
    )


def validate_activation_recovery_gate_and_final_migration_compensation(config):
    route = section(config, "### 1. 任务接收与路由", "### 2. 订阅记录与版本")
    cron = section(config, "### 3. Cron 两阶段切换", "### 4. 定时生成与安全投递")
    recovery_gate = (
        "`cron_job_id == null`",
        "`activation_error` 非空",
        "`recovery_required == true`",
        "禁止直接写 `active`",
        "重新执行完整激活流程",
        "人工恢复流程",
    )
    final_migration = (
        "新订阅 active 提交失败或回执不确定",
        "立即暂停新 Cron",
        "将旧订阅从 `unsubscribed` 恢复为 `active`",
        "恢复旧 Cron",
        "新订阅写 `status=paused` 和 `migration_error`",
        "清理新候选",
        "恢复或清理任一失败",
        "双方 `status=paused`",
        "`recovery_required=true`",
        "`orphaned_cron_job_ids`",
        "active 提交确认成功前不得视为迁移完成",
    )
    return all(token in route for token in recovery_gate) and all(
        token in cron for token in final_migration
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
    assert "综合财经" in config
    assert "仅作推荐项" in config
    assert "学生确认后" in config


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


def test_expert_config_separates_course_migration_and_covers_second_order_compensation():
    config = read(CONFIG)

    assert validate_course_change_and_compensation(config)


def test_course_change_and_compensation_validator_rejects_missing_critical_tokens():
    config = read(CONFIG)

    for token in (
        "课程变更禁止进入同 `job_key` 计划切换",
        "旧任务暂停失败",
        "恢复旧任务失败",
        "恢复旧订阅失败",
        "recovery_required=true",
        "superseded_by_job_key",
    ):
        assert not validate_course_change_and_compensation(config.replace(token, ""))


def test_expert_config_defines_delivery_idempotency_and_complete_edition_history():
    config = read(CONFIG)

    assert validate_delivery_ledger_and_history(config)


def test_delivery_and_history_validator_rejects_missing_state_or_scope_check():
    config = read(CONFIG)

    for token in (
        "delivery_key={job_key}:{plan_version}:{edition_id}",
        "写入 `pending`",
        "发送成功但账本写入失败",
        "finance_news/{schoolId}/{userId}/briefing_history.jsonl",
        "运行时 `schoolId/userId` 路径",
        "完整 `course_id/course_name`",
    ):
        assert not validate_delivery_ledger_and_history(config.replace(token, ""))


def test_expert_config_defines_safe_initial_activation_and_course_migration():
    assert validate_initial_activation_and_course_migration(read(CONFIG))


def test_activation_and_migration_validator_rejects_missing_failure_state():
    config = read(CONFIG)

    for token in (
        "`status=pending_activation`",
        "`activation_error`",
        "禁止 active 无任务",
        "新订阅 `status=pending_activation`",
        "`migration_error`",
        "双方 `status=paused`",
    ):
        assert not validate_initial_activation_and_course_migration(
            config.replace(token, "")
        )


def test_expert_config_requires_atomic_delivery_and_refreshes_next_run_every_trigger():
    assert validate_atomic_delivery_and_next_run(read(CONFIG))


def test_atomic_delivery_validator_rejects_read_then_append_or_missing_fallback():
    config = read(CONFIG)
    assert not validate_atomic_delivery_and_next_run(
        config.replace(
            "平台持久化层的原子 `create-if-absent`/唯一约束",
            "普通读取后追加",
        )
    )
    assert not validate_atomic_delivery_and_next_run(
        config.replace("`delivery_atomicity_unavailable`", "")
    )
    assert not validate_atomic_delivery_and_next_run(
        config.replace("更新 `next_run_at`", "")
    )


def test_expert_config_persistently_disables_delivery_without_atomicity():
    assert validate_persistent_atomicity_disable_and_recovery(read(CONFIG))


def test_persistent_atomicity_validator_rejects_nonpersistent_or_unsafe_recovery():
    config = read(CONFIG)
    for token in (
        "`auto_delivery_status=disabled_atomicity`",
        "`next_run_at=null`",
        "Cron 暂停或订阅写入任一失败",
        "重新验证原子能力",
        "否则禁止写 `active`",
    ):
        assert not validate_persistent_atomicity_disable_and_recovery(
            config.replace(token, "")
        )


def test_expert_config_deletes_failed_initial_draft_and_compensates_final_migration():
    config = read(CONFIG)
    assert validate_initial_activation_and_course_migration(config)
    assert validate_activation_recovery_gate_and_final_migration_compensation(config)
    assert "删除订阅草稿，或保留" not in config


def test_activation_and_final_migration_validator_rejects_missing_safety_branch():
    config = read(CONFIG)
    for token in (
        "`cron_job_id == null`",
        "禁止直接写 `active`",
        "新订阅 active 提交失败或回执不确定",
        "将旧订阅从 `unsubscribed` 恢复为 `active`",
        "active 提交确认成功前不得视为迁移完成",
    ):
        assert not validate_activation_recovery_gate_and_final_migration_compensation(
            config.replace(token, "")
        )


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
        "课程变更",
        "superseded_by_job_key",
        "recovery_required=true",
        "delivery_key",
        "skipped_duplicate",
        "delivery_uncertain",
        "briefing_history.jsonl",
        "pending_activation",
        "activation_error",
        "migration_error",
        "create-if-absent",
        "delivery_atomicity_unavailable",
        "next_run_at",
        "last_success_at",
        "auto_delivery_status",
        "disabled_atomicity",
        "delivery_error",
        "activation-audit.jsonl",
        "active 提交失败",
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
        for name in names:
            body = archive.read(name)
            relative = Path(name).relative_to(SKILL_NAME)
            source = ROOT / SKILL_NAME / relative
            assert hashlib.sha256(body).digest() == hashlib.sha256(source.read_bytes()).digest()
            text = body.decode("utf-8")
            assert all(pattern.search(text) is None for pattern in CREDENTIAL_PATTERNS)


def test_packager_unknown_arguments_return_stdout_json_and_nonzero():
    result = subprocess.run(
        [sys.executable, str(PACKAGER), "--unexpected"],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert result.stderr == ""
    assert json.loads(result.stdout) == {"error": "invalid command-line arguments"}


def test_packager_help_returns_stdout_json_and_zero_without_usage_stderr():
    result = subprocess.run(
        [sys.executable, str(PACKAGER), "--help"],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stderr == ""
    assert json.loads(result.stdout) == {
        "help": "生成可上传的财经新闻课程点评 Skill ZIP",
        "options": ["--output"],
    }


def test_zip_credential_patterns_detect_json_token_and_authorization_examples():
    examples = (
        '"token": "secretvalue123"',
        "Authorization: Bearer abcdefghijklmnopqrstuvwxyz",
        "Authorization: Basic dXNlcjpwYXNz",
        '"authorization": "Basic dXNlcjpwYXNz"',
    )

    for example in examples:
        assert any(pattern.search(example) for pattern in CREDENTIAL_PATTERNS)
