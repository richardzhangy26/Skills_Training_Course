import json
import subprocess
import sys
from pathlib import Path


SKILL_ROOT = Path(__file__).parents[1] / "finance-news-course-commentary"
NORMALIZER = SKILL_ROOT / "scripts" / "normalize_candidates.py"


def read(relative_path):
    return (SKILL_ROOT / relative_path).read_text(encoding="utf-8")


def candidate(**overrides):
    value = {
        "title": "央行发布流动性管理新工具",
        "url": "https://www.pbc.gov.cn/news/liquidity",
        "source": "中国人民银行",
        "source_tier": "official",
        "published_at": "2026-08-22T08:00:00+08:00",
        "fact_summary": "中国人民银行发布流动性管理工具说明。",
        "theory_analysis": "课程中的货币政策工具可用于解释其传导机制。",
        "discussion_question": "该工具可能如何影响市场流动性？",
        "theory_citations": [
            {
                "course_id": "course-1",
                "course_name": "货币金融学",
                "knowledge_point": "货币政策工具",
                "resource_title": "第六章 货币政策",
                "excerpt": "公开市场操作通过调节基础货币影响流动性。",
            }
        ],
    }
    value.update(overrides)
    return value


def run_normalizer(tmp_path, candidates, *, course_evidence_available=True):
    payload = {
        "course": {"course_id": "course-1", "course_name": "货币金融学"},
        "retrieved_at": "2026-08-22T01:02:03Z",
        "course_evidence_available": course_evidence_available,
        "candidates": candidates,
    }
    input_path = tmp_path / "candidates.json"
    input_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable,
            str(NORMALIZER),
            "--input",
            str(input_path),
            "--since",
            "2026-08-22T00:00:00+08:00",
            "--until",
            "2026-08-22T23:59:59+08:00",
            "--edition-date",
            "2026-08-22",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0
    assert result.stderr == ""
    return json.loads(result.stdout)


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
    assert "所有路径都调用 normalizer" in skill
    assert "强制拒绝三级来源" in skill
    assert "内部 hostname allowlist" in skill
    assert "调用方不能提升来源等级" in skill
    assert "`source_tier` 只是调用方断言" in skill
    assert "输出 `source` 由 hostname allowlist" in skill
    assert "NFKC" in skill
    assert "提示词与动作词组合" in skill
    assert "sensitive_url_parameter" in skill
    assert "单一 `SOURCE_REGISTRY`" in skill
    assert "申购/赎回/认购" in skill
    assert "course_id" in skill
    assert "untrusted_source" in skill
    assert "不进入公开网检索或 normalizer" not in skill

    citations = workflow.index("theory_citations")
    assigned_tier = workflow.index("source_tier")
    generated = workflow.index("theory_analysis")
    normalized = workflow.index("normalize_candidates.py")
    assert citations < generated < normalized
    assert assigned_tier < normalized


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
        "course_id",
        "knowledge_point",
        "resource_title",
        "excerpt",
        "skipped_no_course_evidence",
        "finance-news:{schoolId}:{userId}:{courseId}",
        "course_evidence_available",
        "status_origin",
        "candidate_filter",
        "precheck",
        "source_tier",
        "candidate_index",
        "1 MiB",
        "100",
        "10",
        "300",
        "4000",
        "2000",
    ):
        assert token in contract
    assert "不得包含会话 ID" in contract
    assert "无课程证据" in contract
    assert "retrieved_at" in contract
    assert "normalizer 的输入或输出字段" in contract
    assert "normalizer 强制拒绝三级来源" in contract
    assert "调用方直接使用 `skipped_no_course_evidence`" not in contract
    assert "`source_level` 是输出" in contract
    assert "只输出 `course_id` 和 `course_name`" in contract
    assert "不回显标题、URL 或正文" in contract
    assert "`source_tier` 只是调用方断言" in contract
    assert "忽略输入 `source`" in contract
    assert "canonical source label" in contract
    assert "sensitive_url_parameter" in contract
    assert "access_token" in contract
    assert "x-api-key" in contract
    assert "`source_tier == other`" in contract
    assert "优先返回 `untrusted_source`" in contract
    assert "单一 `SOURCE_REGISTRY`" in contract
    for tier in (
        "official",
        "primary",
        "regulator",
        "government",
        "exchange",
        "company_announcement",
        "authoritative_media",
        "media",
        "other",
    ):
        assert tier in contract


def test_source_policy_prioritizes_official_sources_and_treats_other_pages_as_leads():
    policy = read("references/source-policy.md")

    first = policy.index("监管/政府/交易所/公司公告")
    second = policy.index("权威财经媒体")
    third = policy.index("其他公开页面仅作线索")
    assert first < second < third
    assert "不得绕过" in policy
    assert "付费墙" in policy
    assert "normalizer 强制拒绝" in policy
    assert "untrusted_source" in policy
    assert "source_tier" in policy
    assert "内部 hostname allowlist" in policy
    assert "私网" in policy
    assert "userinfo" in policy
    assert "source_tier_mismatch" in policy
    assert "`source_tier` 只是调用方断言" in policy
    assert "canonical source label" in policy
    assert "`source_tier == other`" in policy
    assert "优先返回 `untrusted_source`" in policy
    assert "单一 `SOURCE_REGISTRY`" in policy
    for organization in (
        "国务院",
        "人民银行",
        "财政部",
        "国家统计局",
        "金融监管总局",
        "证监会",
        "上交所",
        "深交所",
        "北交所",
        "公司公告",
        "新华社",
        "央视财经",
        "中国证券报",
        "上海证券报",
        "证券时报",
    ):
        assert organization in policy


def test_briefing_template_separates_facts_course_evidence_analysis_and_discussion():
    briefing = read("output_format/briefing.md")

    for token in (
        "新闻事实",
        "课程依据",
        "理论分析",
        "讨论问题",
        "财经内容仅用于课程学习，不构成投资建议",
        "skipped_no_course_evidence",
        "status_origin",
        "retrieved_at",
    ):
        assert token in briefing


def test_package_exercises_normalizer_tier_three_rejection(tmp_path):
    output = run_normalizer(
        tmp_path,
        [
            candidate(
                source="未署名聚合页",
                source_tier="other",
                url="https://example.com/untrusted",
            )
        ],
    )

    assert output["status"] == "no_eligible_candidates"
    assert output["status_origin"] == "normalizer"
    assert output["items"] == []
    assert output["rejected"] == [
        {
            "candidate_index": 0,
            "reason": "untrusted_source",
        }
    ]


def test_package_exercises_normalizer_ready_official_candidate_contract(tmp_path):
    output = run_normalizer(tmp_path, [candidate()])

    assert output["status"] == "ready"
    assert output["status_origin"] == "normalizer"
    assert output["retrieved_at"] == "2026-08-22T01:02:03+00:00"
    assert output["rejected"] == []
    assert output["items"] == [
        {
            "title": "央行发布流动性管理新工具",
            "url": "https://www.pbc.gov.cn/news/liquidity",
            "source": "中国人民银行",
            "published_at": "2026-08-22T08:00:00+08:00",
            "fact_summary": "中国人民银行发布流动性管理工具说明。",
            "theory_analysis": "课程中的货币政策工具可用于解释其传导机制。",
            "discussion_question": "该工具可能如何影响市场流动性？",
            "theory_citations": [
                {
                    "course_id": "course-1",
                    "course_name": "货币金融学",
                    "knowledge_point": "货币政策工具",
                    "resource_title": "第六章 货币政策",
                    "excerpt": "公开市场操作通过调节基础货币影响流动性。",
                }
            ],
            "source_level": 1,
            "item_id": "F20260822-01",
        }
    ]


def test_package_exercises_normalizer_requires_source_tier_and_rejects_input_source_level(
    tmp_path,
):
    missing_tier = candidate()
    missing_tier.pop("source_tier")
    supplied_output_field = candidate(url="https://www.pbc.gov.cn/news/forged-level")
    supplied_output_field.pop("source_tier")
    supplied_output_field["source_level"] = 1

    output = run_normalizer(tmp_path, [missing_tier, supplied_output_field])

    assert output["status"] == "no_eligible_candidates"
    assert output["status_origin"] == "normalizer"
    assert output["items"] == []
    assert [entry["reason"] for entry in output["rejected"]] == [
        "missing_source_tier",
        "missing_source_tier",
    ]


def test_package_exercises_normalizer_cross_course_evidence_rejection(tmp_path):
    output = run_normalizer(
        tmp_path,
        [
            candidate(
                theory_citations=[
                    {
                        "course_id": "course-2",
                        "course_name": "证券投资学",
                        "knowledge_point": "投资组合",
                        "resource_title": "第三章",
                        "excerpt": "分散化可以降低非系统性风险。",
                    }
                ]
            )
        ],
    )

    assert output["status"] == "skipped_no_course_evidence"
    assert output["status_origin"] == "candidate_filter"
    assert output["items"] == []
    assert output["rejected"][0]["reason"] == "course_mismatch"


def test_package_exercises_normalizer_all_missing_evidence_status(tmp_path):
    output = run_normalizer(
        tmp_path,
        [
            candidate(
                title="缺少课程证据的候选",
                url="https://www.pbc.gov.cn/news/no-evidence",
                theory_citations=[],
            )
        ],
    )

    assert output["status"] == "skipped_no_course_evidence"
    assert output["status_origin"] == "candidate_filter"
    assert output["items"] == []
    assert output["rejected"][0]["reason"] == "missing_course_evidence"


def test_package_exercises_normalizer_global_evidence_precheck_and_retrieval_echo(tmp_path):
    output = run_normalizer(
        tmp_path,
        [candidate()],
        course_evidence_available=False,
    )

    assert output["status"] == "skipped_no_course_evidence"
    assert output["status_origin"] == "precheck"
    assert output["course_evidence_available"] is False
    assert output["retrieved_at"] == "2026-08-22T01:02:03+00:00"
    assert output["items"] == []
    assert output["rejected"] == [
        {"candidate_index": 0, "reason": "course_evidence_unavailable"}
    ]
