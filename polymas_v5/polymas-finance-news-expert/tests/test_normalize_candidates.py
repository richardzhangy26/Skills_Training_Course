import json
import subprocess
import sys
from pathlib import Path

import pytest


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
        "source_tier": "official",
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
        "course": arguments.get(
            "course", {"course_name": "货币金融学", "course_id": "course-1"}
        ),
        "candidates": candidates,
    }
    if not arguments.get("omit_retrieved_at"):
        payload["retrieved_at"] = arguments.get(
            "retrieved_at", "2026-08-22T00:00:00Z"
        )
    if not arguments.get("omit_course_evidence_available"):
        payload["course_evidence_available"] = arguments.get(
            "course_evidence_available", True
        )
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
    assert output["retrieved_at"] == "2026-08-22T00:00:00+00:00"
    assert output["status_origin"] == "normalizer"


def test_cli_keeps_highest_source_level_for_duplicate_canonical_url(tmp_path):
    duplicate = candidate(
        title="媒体转述央行流动性工具",
        url="https://www.pbc.gov.cn/news/liquidity?from=media&utm_campaign=morning",
        source="财经自媒体",
        source_tier="authoritative_media",
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
    assert output["status"] == "no_eligible_candidates"
    assert output["status_origin"] == "normalizer"
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
    assert output["status"] == "skipped_no_course_evidence"
    assert output["status_origin"] == "candidate_filter"
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
                ("另一权威财经媒体", "authoritative_media", 8),
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


@pytest.mark.parametrize(
    "citation_field",
    ["course_name", "knowledge_point", "resource_title", "excerpt"],
)
def test_cli_rejects_investment_advice_in_each_citation_string(tmp_path, citation_field):
    prohibited_text = "建议买入该资产"
    citation = dict(candidate()["theory_citations"][0])
    citation[citation_field] = prohibited_text

    result = run_cli(
        tmp_path,
        [
            candidate(
                theory_citations=[citation],
                url=f"https://www.pbc.gov.cn/news/advice-{citation_field}",
            )
        ],
    )

    output = output_of(result)
    assert output["items"] == []
    assert output["rejected"][0]["reason"] == "investment_advice_language"


def test_cli_rejects_investment_advice_in_course_metadata_before_output(tmp_path):
    result = run_cli(
        tmp_path,
        [],
        course={"course_name": "建议买入该资产", "course_id": "course-1"},
    )

    assert result.returncode != 0
    assert result.stderr == ""
    assert json.loads(result.stdout)["error"] == "input.course contains investment advice language"


def test_cli_rejects_investment_advice_in_course_metadata_key_before_output(tmp_path):
    result = run_cli(
        tmp_path,
        [],
        course={"course_name": "货币金融学", "建议买入该资产": "课程备注"},
    )

    assert result.returncode != 0
    assert result.stderr == ""
    assert json.loads(result.stdout)["error"] == "input.course contains investment advice language"


def test_cli_uses_complete_content_tie_breaker_independent_of_input_order(tmp_path):
    alpha = candidate(
        source_tier="official",
        fact_summary="alpha fact summary",
        url="https://www.pbc.gov.cn/news/same-rank?utm_source=a",
    )
    beta = candidate(
        source_tier="official",
        fact_summary="beta fact summary",
        url="https://www.pbc.gov.cn/news/same-rank?utm_source=b",
    )

    forward = output_of(run_cli(tmp_path, [alpha, beta]))
    reverse = output_of(run_cli(tmp_path, [beta, alpha]))

    assert forward == reverse
    assert forward["items"][0]["fact_summary"] == "alpha fact summary"
    assert forward["rejected"][0]["reason"] == "duplicate_url"


def test_cli_clusters_transitively_similar_titles_before_selecting_winner(tmp_path):
    prefix = "财经新闻abcdefghijklmnopqrstu0123456789"
    first = candidate(
        title=f"{prefix}甲乙丙丁",
        url="https://example.com/cluster/a",
        source="权威财经媒体",
        source_tier="authoritative_media",
    )
    bridge = candidate(
        title=f"{prefix}甲乙戊己",
        url="https://example.com/cluster/b",
        source="另一权威财经媒体",
        source_tier="authoritative_media",
    )
    winner = candidate(
        title=f"{prefix}庚辛戊己",
        url="https://example.com/cluster/c",
        source="监管公告",
        source_tier="official",
    )

    output = output_of(run_cli(tmp_path, [first, bridge, winner]))

    assert [item["title"] for item in output["items"]] == [winner["title"]]
    assert [entry["reason"] for entry in output["rejected"]] == [
        "similar_title",
        "similar_title",
    ]


def test_cli_treats_default_ports_as_the_same_canonical_url(tmp_path):
    explicit_default_port = candidate(
        title="明确默认端口",
        url="https://www.pbc.gov.cn:443/news/default-port",
    )
    implicit_default_port = candidate(
        title="省略默认端口",
        url="https://www.pbc.gov.cn/news/default-port",
    )

    output = output_of(run_cli(tmp_path, [explicit_default_port, implicit_default_port]))

    assert len(output["items"]) == 1
    assert output["items"][0]["url"] == "https://www.pbc.gov.cn/news/default-port"
    assert output["rejected"][0]["reason"] == "duplicate_url"


def test_cli_preserves_ipv6_brackets_while_normalizing_default_port(tmp_path):
    explicit_default_port = candidate(
        title="IPv6 明确默认端口",
        url="https://[2001:db8::1]:443/a",
    )
    implicit_default_port = candidate(
        title="IPv6 省略默认端口",
        url="https://[2001:db8::1]/a",
    )

    output = output_of(run_cli(tmp_path, [explicit_default_port, implicit_default_port]))

    assert len(output["items"]) == 1
    assert output["items"][0]["url"] == "https://[2001:db8::1]/a"
    assert output["rejected"][0]["reason"] == "duplicate_url"


def test_cli_rejects_course_without_a_recognizable_name(tmp_path):
    result = run_cli(tmp_path, [candidate()], course={"course_id": "course-1"})

    assert result.returncode != 0
    assert result.stderr == ""
    assert json.loads(result.stdout)["error"] == "input.course must include a recognizable name"


def test_cli_rejects_max_items_above_three(tmp_path):
    result = run_cli(tmp_path, [candidate()], max_items=4)

    assert result.returncode != 0
    assert result.stderr == ""
    assert json.loads(result.stdout)["error"] == "max-items must be between 1 and 3"


def test_cli_requires_retrieved_at_with_timezone(tmp_path):
    missing = run_cli(tmp_path, [candidate()], omit_retrieved_at=True)
    without_timezone = run_cli(
        tmp_path, [candidate()], retrieved_at="2026-08-22T00:00:00"
    )

    assert missing.returncode != 0
    assert missing.stderr == ""
    assert json.loads(missing.stdout)["error"] == "input.retrieved_at is required"
    assert without_timezone.returncode != 0
    assert without_timezone.stderr == ""
    assert json.loads(without_timezone.stdout)["error"] == "retrieved_at must include a timezone"


@pytest.mark.parametrize("value", [None, "false", 1])
def test_cli_requires_boolean_course_evidence_available(tmp_path, value):
    result = run_cli(tmp_path, [candidate()], course_evidence_available=value)

    assert result.returncode != 0
    assert result.stderr == ""
    assert (
        json.loads(result.stdout)["error"]
        == "input.course_evidence_available must be a boolean"
    )


def test_cli_skips_all_candidates_when_course_evidence_precheck_is_false(tmp_path):
    result = run_cli(
        tmp_path,
        [{"title": "即使结构无效也不能绕过预检"}],
        course_evidence_available=False,
    )

    output = output_of(result)
    assert output["status"] == "skipped_no_course_evidence"
    assert output["status_origin"] == "precheck"
    assert output["course_evidence_available"] is False
    assert output["items"] == []
    assert output["rejected"] == [
        {
            "title": "",
            "url": "",
            "reason": "course_evidence_unavailable",
        }
    ]


def test_cli_precheck_does_not_echo_investment_advice_from_candidate_title(tmp_path):
    prohibited_text = "建议买入"
    result = run_cli(
        tmp_path,
        [candidate(title=f"{prohibited_text}该资产")],
        course_evidence_available=False,
    )

    output = output_of(result)
    assert prohibited_text not in result.stdout
    assert output["status"] == "skipped_no_course_evidence"
    assert output["status_origin"] == "precheck"
    assert output["rejected"] == [
        {
            "title": "",
            "url": "",
            "reason": "course_evidence_unavailable",
        }
    ]


def test_cli_rejects_tier_three_source_before_candidate_selection(tmp_path):
    result = run_cli(
        tmp_path,
        [
            candidate(
                source="普通公开页面",
                source_tier="other",
                url="https://example.com/untrusted-source",
            )
        ],
    )

    output = output_of(result)
    assert output["status"] == "no_eligible_candidates"
    assert output["status_origin"] == "normalizer"
    assert output["items"] == []
    assert output["rejected"][0]["reason"] == "untrusted_source"


@pytest.mark.parametrize("tier", ["", "   "])
def test_cli_rejects_empty_source_tier(tmp_path, tier):
    result = run_cli(tmp_path, [candidate(source_tier=tier)])

    output = output_of(result)
    assert output["items"] == []
    assert output["rejected"][0]["reason"] == "missing_source_tier"


@pytest.mark.parametrize("tier", [None, 1, True, [], {}])
def test_cli_rejects_non_string_source_tier_without_crashing(tmp_path, tier):
    result = run_cli(tmp_path, [candidate(source_tier=tier)])

    assert result.returncode == 0
    assert result.stderr == ""
    output = json.loads(result.stdout)
    assert output["items"] == []
    assert output["rejected"][0]["reason"] == "invalid_source_tier"


def test_cli_rejects_missing_source_tier_even_when_source_level_is_injected(tmp_path):
    injected = candidate(source_level=1)
    del injected["source_tier"]

    output = output_of(run_cli(tmp_path, [injected]))

    assert output["items"] == []
    assert output["rejected"][0]["reason"] == "missing_source_tier"


def test_cli_rejects_unknown_source_tier_without_falling_back_to_source_name(tmp_path):
    output = output_of(
        run_cli(tmp_path, [candidate(source_tier="governmental")])
    )

    assert output["items"] == []
    assert output["rejected"][0]["reason"] == "invalid_source_tier"


def test_cli_ignores_injected_source_level_when_source_tier_is_valid(tmp_path):
    output = output_of(
        run_cli(tmp_path, [candidate(source_tier="official", source_level=3)])
    )

    assert output["items"][0]["source_level"] == 1


@pytest.mark.parametrize(
    ("tier", "expected_level"),
    [
        ("official", 1),
        ("primary", 1),
        ("regulator", 1),
        ("government", 1),
        ("exchange", 1),
        ("company_announcement", 1),
        ("authoritative_media", 2),
        ("media", 2),
        ("other", 3),
    ],
)
def test_cli_maps_each_allowed_source_tier_deterministically(
    tmp_path, tier, expected_level
):
    output = output_of(
        run_cli(
            tmp_path,
            [
                candidate(
                    source_tier=tier,
                    url=f"https://example.com/source-tier/{tier}",
                )
            ],
        )
    )

    if expected_level == 3:
        assert output["items"] == []
        assert output["rejected"][0]["reason"] == "untrusted_source"
    else:
        assert output["items"][0]["source_level"] == expected_level


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
