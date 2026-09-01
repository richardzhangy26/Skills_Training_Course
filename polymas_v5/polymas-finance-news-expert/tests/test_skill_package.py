import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).parents[1]
SKILL_ROOT = ROOT / "finance-news-commentary"
SKILL = SKILL_ROOT / "SKILL.md"
CONTRACT = SKILL_ROOT / "references" / "data-contract.md"
SOURCE_POLICY = SKILL_ROOT / "references" / "source-policy.md"
BRIEFING = SKILL_ROOT / "output_format" / "briefing.md"
NORMALIZER = SKILL_ROOT / "scripts" / "normalize_candidates.py"


def read(path):
    return path.read_text(encoding="utf-8")


def candidate(**overrides):
    value = {
        "title": "央行发布流动性管理新工具",
        "url": "https://www.pbc.gov.cn/news/liquidity",
        "source": "中国人民银行",
        "source_tier": "official",
        "published_at": "2026-08-22T08:00:00+08:00",
        "fact_summary": "中国人民银行发布流动性管理工具说明。",
        "theory_analysis": "该工具可通过基础货币变化影响市场流动性。",
        "discussion_question": "这一工具可能通过哪些渠道影响市场？",
    }
    value.update(overrides)
    return value


def run_normalizer(tmp_path, candidates):
    input_path = tmp_path / "candidates.json"
    input_path.write_text(
        json.dumps(
            {
                "retrieved_at": "2026-08-22T00:00:00Z",
                "candidates": candidates,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return subprocess.run(
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
            "--max-items",
            "3",
        ],
        text=True,
        capture_output=True,
        check=False,
    )


def test_skill_has_expected_structure_and_frontmatter():
    assert SKILL_ROOT.is_dir()
    for path in (SKILL, CONTRACT, SOURCE_POLICY, BRIEFING, NORMALIZER):
        assert path.is_file()

    skill = read(SKILL)
    assert skill.startswith("---\nname: finance-news-commentary\n")
    assert "description: Use when" in skill
    assert "without selecting a course" in skill


def test_skill_routes_only_public_search_analysis_normalizer_and_briefing():
    skill = read(SKILL)

    for token in (
        "[DETERMINE] 时间窗与主题",
        "[CALL] 平台通用工具公开网检索",
        "[FILTER] 事实核对",
        "[BUILD] 通用财经分析",
        "[BUILD] normalize_candidates.py",
        "[BUILD] briefing",
        "无需课程、课程 ID、课程资源或课程证据",
    ):
        assert token in skill
    for forbidden in (
        "学生班课查询",
        "学生教学计划查询",
        "学生学习资源助手",
        "知识检索助手",
        "skipped_no_course_evidence",
    ):
        assert forbidden not in skill


def test_data_contract_has_no_course_or_identity_inputs():
    contract = read(CONTRACT)

    for token in (
        '"retrieved_at"',
        '"candidates"',
        "theory_analysis",
        "discussion_question",
        "ready",
        "no_eligible_candidates",
        "finance-news:{schoolId}:{userId}:{agentId}",
        "只用于平台私有 Cron 元数据",
    ):
        assert token in contract
    for forbidden in (
        '"course": {',
        '"course_id":',
        '"course_name":',
        '"course_evidence_available":',
        '"theory_citations":',
        "skipped_no_course_evidence",
    ):
        assert forbidden not in contract
    assert "不得静默忽略旧课程字段" in contract


def test_briefing_separates_fact_analysis_and_interaction_without_course_section():
    briefing = read(BRIEFING)

    for token in (
        "新闻事实",
        "财经知识分析",
        "互动问题",
        "item.fact_summary",
        "item.theory_analysis",
        "item.discussion_question",
        "仅用于财经学习，不构成投资建议",
        "no_eligible_candidates",
    ):
        assert token in briefing
    assert "课程依据" not in briefing
    assert "citation." not in briefing


def test_source_policy_uses_public_sources_and_topic_relevance():
    policy = read(SOURCE_POLICY)

    for token in (
        "监管/政府/交易所/公司公告",
        "权威财经媒体",
        "其他公开页面仅作线索",
        "学生已选财经主题",
        "SOURCE_REGISTRY",
        "不把推测写成新闻事实",
    ):
        assert token in policy
    assert "课程证据" not in policy


def test_normalizer_outputs_general_finance_briefing_without_course_fields(tmp_path):
    result = run_normalizer(tmp_path, [candidate()])

    assert result.returncode == 0
    assert result.stderr == ""
    output = json.loads(result.stdout)
    assert output["status"] == "ready"
    assert output["items"][0]["source"] == "中国人民银行"
    assert output["items"][0]["source_level"] == 1
    assert "course" not in output
    assert "theory_citations" not in output["items"][0]


def test_normalizer_rejects_investment_advice_and_sensitive_urls(tmp_path):
    result = run_normalizer(
        tmp_path,
        [
            candidate(theory_analysis="立即买入这只股票"),
            candidate(
                title="敏感 URL",
                url="https://www.pbc.gov.cn/news/sensitive?token=do-not-echo-secret",
            ),
        ],
    )

    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["items"] == []
    assert {entry["reason"] for entry in output["rejected"]} == {
        "investment_advice_language",
        "sensitive_url_parameter",
    }
    assert "do-not-echo-secret" not in result.stdout


def test_normalizer_returns_no_eligible_candidates_without_placeholder(tmp_path):
    result = run_normalizer(tmp_path, [])

    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output == {
        "edition_id": "F20260822",
        "items": [],
        "rejected": [],
        "retrieved_at": "2026-08-22T00:00:00+00:00",
        "status": "no_eligible_candidates",
        "status_origin": "normalizer",
    }
