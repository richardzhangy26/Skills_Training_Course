import json
import subprocess
import sys
from pathlib import Path


SCRIPT = (
    Path(__file__).parents[1]
    / "finance-news-course-commentary"
    / "scripts"
    / "normalize_candidates.py"
)


def candidate(**overrides):
    value = {
        "title": "央行发布流动性管理新工具",
        "url": "https://www.pbc.gov.cn/news/liquidity?utm_source=daily#section",
        "source": "中国人民银行",
        "published_at": "2026-08-22T08:00:00+08:00",
        "fact_summary": "中国人民银行发布流动性管理工具说明。",
        "theory_analysis": "可用于讨论货币政策工具的传导机制。",
        "discussion_question": "该工具可能如何影响市场流动性？",
        "theory_citations": [
            {
                "course_name": "货币金融学",
                "knowledge_point": "货币政策工具",
                "resource_title": "第六章 货币政策",
                "excerpt": "公开市场操作通过调节基础货币影响流动性。",
            }
        ],
    }
    value.update(overrides)
    return value


def run_cli(tmp_path, candidates, **arguments):
    payload = {
        "course": {"course_name": "货币金融学", "course_id": "course-1"},
        "candidates": candidates,
    }
    input_path = tmp_path / "candidates.json"
    input_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    command = [
        sys.executable,
        str(SCRIPT),
        "--input",
        str(input_path),
        "--since",
        arguments.get("since", "2026-08-22T00:00:00+08:00"),
        "--until",
        arguments.get("until", "2026-08-22T23:59:59+08:00"),
        "--edition-date",
        arguments.get("edition_date", "2026-08-22"),
        "--max-items",
        str(arguments.get("max_items", 3)),
    ]
    return subprocess.run(command, text=True, capture_output=True, check=False)


def output_of(result):
    assert result.stderr == ""
    return json.loads(result.stdout)


def test_cli_normalizes_tracking_parameters_and_only_emits_json(tmp_path):
    result = run_cli(tmp_path, [candidate()])

    assert result.returncode == 0
    output = output_of(result)
    assert result.stdout.strip().startswith("{")
    assert output["items"][0]["url"] == "https://www.pbc.gov.cn/news/liquidity"
    assert output["items"][0]["item_id"] == "F20260822-01"
    assert output["edition_id"] == "F20260822"


def test_cli_keeps_highest_source_level_for_duplicate_canonical_url(tmp_path):
    duplicate = candidate(
        title="媒体转述央行流动性工具",
        url="https://www.pbc.gov.cn/news/liquidity?from=media&utm_campaign=morning",
        source="财经自媒体",
        source_tier="other",
    )
    official = candidate(source_tier="official")

    result = run_cli(tmp_path, [duplicate, official])

    output = output_of(result)
    assert [item["source"] for item in output["items"]] == ["中国人民银行"]
    assert output["items"][0]["source_level"] == 1
    assert [entry["reason"] for entry in output["rejected"]] == ["duplicate_url"]


def test_cli_clusters_similar_titles_and_keeps_the_higher_ranked_source(tmp_path):
    first = candidate(
        title="央行发布流动性管理新工具",
        source="路透社",
        source_tier="authoritative_media",
        url="https://example.com/reuters/liquidity",
    )
    second = candidate(
        title="央行发布新的流动性管理工具",
        source="中国人民银行",
        source_tier="official",
        url="https://www.pbc.gov.cn/news/new-liquidity",
    )

    result = run_cli(tmp_path, [first, second])

    output = output_of(result)
    assert [item["source"] for item in output["items"]] == ["中国人民银行"]
    assert [entry["reason"] for entry in output["rejected"]] == ["similar_title"]


def test_cli_rejects_candidates_outside_the_inclusive_time_window(tmp_path):
    before = candidate(published_at="2026-08-21T23:59:59+08:00")
    boundary = candidate(
        title="窗口终点新闻",
        url="https://www.pbc.gov.cn/news/boundary",
        published_at="2026-08-22T23:59:59+08:00",
    )

    result = run_cli(tmp_path, [before, boundary])

    output = output_of(result)
    assert [item["title"] for item in output["items"]] == ["窗口终点新闻"]
    assert [entry["reason"] for entry in output["rejected"]] == ["outside_time_window"]


def test_cli_rejects_invalid_urls_and_missing_course_evidence(tmp_path):
    invalid_url = candidate(url="javascript:alert(1)")
    no_evidence = candidate(
        title="没有课程证据",
        url="https://www.pbc.gov.cn/news/no-evidence",
        theory_citations=[],
    )

    result = run_cli(tmp_path, [invalid_url, no_evidence])

    output = output_of(result)
    assert output["items"] == []
    assert {entry["reason"] for entry in output["rejected"]} == {
        "invalid_url",
        "missing_course_evidence",
    }


def test_cli_rejects_incomplete_or_wrong_course_citations(tmp_path):
    incomplete = candidate(
        title="缺少摘录",
        url="https://www.pbc.gov.cn/news/incomplete",
        theory_citations=[
            {
                "course_name": "货币金融学",
                "knowledge_point": "货币政策工具",
                "resource_title": "第六章",
            }
        ],
    )
    wrong_course = candidate(
        title="错误课程",
        url="https://www.pbc.gov.cn/news/wrong-course",
        theory_citations=[
            {
                "course_name": "证券投资学",
                "knowledge_point": "投资组合",
                "resource_title": "第三章",
                "excerpt": "分散化可以降低非系统性风险。",
            }
        ],
    )

    result = run_cli(tmp_path, [incomplete, wrong_course])

    output = output_of(result)
    assert output["items"] == []
    assert {entry["reason"] for entry in output["rejected"]} == {
        "missing_course_evidence",
        "course_mismatch",
    }


def test_cli_prioritizes_source_levels_limits_results_and_assigns_stable_ids(tmp_path):
    candidates = [
        candidate(
            title=f"候选新闻{i}",
            url=f"https://example.com/news/{i}",
            source=source,
            source_tier=tier,
            published_at=f"2026-08-22T{hour:02d}:00:00+08:00",
        )
        for i, (source, tier, hour) in enumerate(
            [
                ("其他页面", "other", 8),
                ("权威财经媒体", "authoritative_media", 9),
                ("监管公告", "official", 10),
                ("另一监管公告", "official", 7),
            ],
            start=1,
        )
    ]

    first = output_of(run_cli(tmp_path, candidates, max_items=3))
    second = output_of(run_cli(tmp_path, list(reversed(candidates)), max_items=3))

    assert [item["title"] for item in first["items"]] == [
        "候选新闻3",
        "候选新闻4",
        "候选新闻2",
    ]
    assert [item["item_id"] for item in first["items"]] == [
        "F20260822-01",
        "F20260822-02",
        "F20260822-03",
    ]
    assert first["items"] == second["items"]
    assert [entry["reason"] for entry in first["rejected"]] == ["max_items_exceeded"]


def test_cli_rejects_investment_advice_language(tmp_path):
    advice = candidate(
        theory_analysis="建议投资者立即买入并加仓该资产。",
    )

    result = run_cli(tmp_path, [advice])

    output = output_of(result)
    assert output["items"] == []
    assert output["rejected"][0]["reason"] == "investment_advice_language"


def test_cli_returns_a_single_json_error_and_nonzero_exit_for_bad_input(tmp_path):
    input_path = tmp_path / "bad.json"
    input_path.write_text("[]", encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
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

    assert result.returncode != 0
    assert result.stderr == ""
    assert json.loads(result.stdout)["error"].startswith("input")
