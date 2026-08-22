from pathlib import Path


SKILL_ROOT = Path(__file__).parents[1] / "finance-news-course-commentary"


def read(relative_path):
    return (SKILL_ROOT / relative_path).read_text(encoding="utf-8")


def test_skill_package_declares_the_required_polymas_workflow_and_boundaries():
    skill = read("SKILL.md")

    assert "name: finance-news-course-commentary" in skill
    assert "description: Use when" in skill
    for heading in (
        "## 技能说明",
        "## 触发/不触发",
        "## 项目结构",
        "## 执行流程",
        "## 暂停确认规则",
        "## 执行流程强制约束",
    ):
        assert heading in skill

    stages = (
        "学生教学计划/学习资源",
        "平台通用工具公开网检索",
        "知识检索助手课程证据",
        "normalize_candidates.py",
        "briefing",
    )
    workflow = skill[skill.index("## 执行流程") : skill.index("## 暂停确认规则")]
    positions = [workflow.index(stage) for stage in stages]
    assert positions == sorted(positions)
    assert "不创建 Cron" in skill
    assert "不调用 channel-message" in skill
    assert "不保存订阅" in skill
    assert "前置课程证据查询为空" in skill
    assert "直接输出 `skipped_no_course_evidence`" in skill
    assert "不得把三级来源传入 normalizer 作为可展示候选" in skill


def test_data_contract_enforces_course_evidence_stable_ids_and_session_independent_job_key():
    contract = read("references/data-contract.md")

    for token in (
        "status",
        "edition_id",
        "course",
        "items",
        "rejected",
        "item_id",
        "FYYYYMMDD-01",
        "theory_citations",
        "course_name",
        "knowledge_point",
        "resource_title",
        "excerpt",
        "skipped_no_course_evidence",
        "finance-news:{schoolId}:{userId}:{courseId}",
    ):
        assert token in contract
    assert "不得包含会话 ID" in contract
    assert "无课程证据" in contract
    assert "retrieved_at" in contract
    assert "normalizer 不负责拒绝三级来源" in contract


def test_source_policy_prioritizes_official_sources_and_treats_other_pages_as_leads():
    policy = read("references/source-policy.md")

    first = policy.index("监管/政府/交易所/公司公告")
    second = policy.index("权威财经媒体")
    third = policy.index("其他公开页面仅作线索")
    assert first < second < third
    assert "不得绕过" in policy
    assert "付费墙" in policy
    assert "不得把三级来源传入 normalizer 作为可展示候选" in policy


def test_briefing_template_separates_facts_course_evidence_analysis_and_discussion():
    briefing = read("output_format/briefing.md")

    for token in (
        "新闻事实",
        "课程依据",
        "理论分析",
        "讨论问题",
        "财经内容仅用于课程学习，不构成投资建议",
        "skipped_no_course_evidence",
    ):
        assert token in briefing
