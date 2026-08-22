#!/usr/bin/env python3
"""Deterministically validate and prepare finance-news course briefings."""

import argparse
import json
import re
import sys
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


REQUIRED_CANDIDATE_FIELDS = (
    "title",
    "url",
    "source",
    "published_at",
    "fact_summary",
    "theory_analysis",
    "discussion_question",
    "theory_citations",
)
REQUIRED_CITATION_FIELDS = (
    "course_name",
    "knowledge_point",
    "resource_title",
    "excerpt",
)
OUTPUT_CANDIDATE_FIELDS = REQUIRED_CANDIDATE_FIELDS + ("source_level",)
TRACKING_PARAMETERS = {
    "dclid",
    "fbclid",
    "from",
    "gclid",
    "mc_cid",
    "mc_eid",
    "msclkid",
    "ref",
    "source",
    "_ga",
    "_gl",
}
INVESTMENT_ADVICE_PATTERNS = (
    "建议投资",
    "建议买入",
    "建议卖出",
    "立即买入",
    "立即卖出",
    "推荐买入",
    "推荐卖出",
    "加仓",
    "减仓",
    "建仓",
    "清仓",
    "抄底",
    "止损",
    "止盈",
    "目标价",
    "保证收益",
    "稳赚",
)


class InputError(ValueError):
    """An input or command-line argument cannot produce a valid briefing."""


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message):  # pragma: no cover - argparse's formatting is not useful here.
        raise InputError(message)


def parse_timestamp(value, field_name):
    if not isinstance(value, str) or not value.strip():
        raise InputError(f"{field_name} must be an ISO8601 timestamp")
    try:
        timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise InputError(f"{field_name} must be an ISO8601 timestamp") from error
    if timestamp.tzinfo is None:
        raise InputError(f"{field_name} must include a timezone")
    return timestamp


def canonical_url(value):
    if not isinstance(value, str) or not value.strip():
        raise InputError("invalid_url")
    parsed = urlsplit(value.strip())
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
        raise InputError("invalid_url")
    if any(character.isspace() for character in parsed.netloc):
        raise InputError("invalid_url")
    hostname = parsed.hostname.lower()
    if parsed.username or parsed.password:
        raise InputError("invalid_url")
    netloc = hostname
    port = parsed.port
    if port and not (
        (parsed.scheme.lower() == "http" and port == 80)
        or (parsed.scheme.lower() == "https" and port == 443)
    ):
        netloc = f"{hostname}:{port}"
    path = parsed.path or "/"
    if path != "/":
        path = path.rstrip("/")
    query = [
        (name, content)
        for name, content in parse_qsl(parsed.query, keep_blank_values=True)
        if name.lower() not in TRACKING_PARAMETERS
        and not name.lower().startswith("utm_")
    ]
    return urlunsplit((parsed.scheme.lower(), netloc, path, urlencode(sorted(query)), ""))


def source_level(candidate):
    supplied = str(
        candidate.get("source_tier", candidate.get("source_level", ""))
    ).strip().lower()
    explicit_levels = {
        "1": 1,
        "official": 1,
        "primary": 1,
        "regulator": 1,
        "government": 1,
        "exchange": 1,
        "company_announcement": 1,
        "2": 2,
        "authoritative_media": 2,
        "media": 2,
        "3": 3,
        "other": 3,
    }
    if supplied in explicit_levels:
        return explicit_levels[supplied]

    source = str(candidate.get("source", "")).lower()
    url = str(candidate.get("url", "")).lower()
    official_markers = (
        ".gov.",
        "gov.cn",
        "pbc.gov.cn",
        "csrc.gov.cn",
        "safe.gov.cn",
        "sse.com.cn",
        "szse.cn",
        "cninfo.com.cn",
        "sec.gov",
        "中国人民银行",
        "证监会",
        "交易所",
        "公司公告",
        "监管",
    )
    media_markers = (
        "reuters",
        "路透",
        "bloomberg",
        "彭博",
        "financial times",
        "华尔街日报",
        "wsj",
        "财新",
        "cnbc",
    )
    if any(marker in source or marker in url for marker in official_markers):
        return 1
    if any(marker in source or marker in url for marker in media_markers):
        return 2
    return 3


def normalized_title(value):
    return re.sub(r"[\W_]+", "", value.casefold(), flags=re.UNICODE)


def similar_title(left, right):
    left_title = normalized_title(left)
    right_title = normalized_title(right)
    if left_title == right_title:
        return True
    if not left_title or not right_title:
        return False
    character_overlap = len(set(left_title) & set(right_title)) / len(
        set(left_title) | set(right_title)
    )
    sequence_similarity = SequenceMatcher(None, left_title, right_title).ratio()
    return character_overlap >= 0.82 and sequence_similarity >= 0.78


def course_name(course):
    for key in ("course_name", "name", "title"):
        value = course.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def validate_course_evidence(candidate, selected_course):
    citations = candidate.get("theory_citations")
    if not isinstance(citations, list) or not citations:
        return "missing_course_evidence"
    valid_citations = []
    for citation in citations:
        if not isinstance(citation, dict) or any(
            not isinstance(citation.get(field), str) or not citation[field].strip()
            for field in REQUIRED_CITATION_FIELDS
        ):
            return "missing_course_evidence"
        valid_citations.append(citation)
    expected_name = course_name(selected_course)
    if expected_name and not any(
        citation["course_name"].strip() == expected_name for citation in valid_citations
    ):
        return "course_mismatch"
    return None


def string_values(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for nested_value in value.values():
            yield from string_values(nested_value)
    elif isinstance(value, list):
        for nested_value in value:
            yield from string_values(nested_value)


def contains_investment_advice(value):
    return any(
        pattern in text
        for text in string_values(value)
        for pattern in INVESTMENT_ADVICE_PATTERNS
    )


def rejected_candidate(candidate, reason):
    return {
        "title": candidate.get("title", "") if isinstance(candidate, dict) else "",
        "url": candidate.get("url", "") if isinstance(candidate, dict) else "",
        "reason": reason,
    }


def validate_candidate(candidate, since, until, selected_course):
    if not isinstance(candidate, dict):
        return None, rejected_candidate(candidate, "invalid_candidate")
    for field in REQUIRED_CANDIDATE_FIELDS:
        if field not in candidate or (
            field != "theory_citations"
            and (not isinstance(candidate[field], str) or not candidate[field].strip())
        ):
            return None, rejected_candidate(candidate, f"missing_{field}")
    try:
        url = canonical_url(candidate["url"])
    except (InputError, ValueError):
        return None, rejected_candidate(candidate, "invalid_url")
    try:
        published_at = parse_timestamp(candidate["published_at"], "published_at")
    except InputError:
        return None, rejected_candidate(candidate, "invalid_published_at")
    if not since <= published_at <= until:
        return None, rejected_candidate(candidate, "outside_time_window")
    if contains_investment_advice(candidate):
        return None, rejected_candidate(candidate, "investment_advice_language")
    evidence_problem = validate_course_evidence(candidate, selected_course)
    if evidence_problem:
        return None, rejected_candidate(candidate, evidence_problem)
    prepared = {field: candidate[field] for field in REQUIRED_CANDIDATE_FIELDS}
    prepared["url"] = url
    prepared["source_level"] = source_level(candidate)
    prepared["_published_at"] = published_at
    return prepared, None


def candidate_sort_key(candidate):
    return (
        candidate["source_level"],
        -candidate["_published_at"].timestamp(),
        normalized_title(candidate["title"]),
        candidate["url"],
        json.dumps(
            {key: candidate[key] for key in OUTPUT_CANDIDATE_FIELDS},
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ),
    )


def normalize(payload, since, until, edition_date, max_items):
    if not isinstance(payload, dict):
        raise InputError("input must be an object")
    course = payload.get("course")
    candidates = payload.get("candidates")
    if not isinstance(course, dict):
        raise InputError("input.course must be an object")
    if not isinstance(candidates, list):
        raise InputError("input.candidates must be an array")
    if not course_name(course):
        raise InputError("input.course must include a recognizable name")
    if contains_investment_advice(course):
        raise InputError("input.course contains investment advice language")
    if max_items < 1 or max_items > 3:
        raise InputError("max-items must be between 1 and 3")

    rejected = []
    accepted = []
    for candidate in candidates:
        prepared, rejected_entry = validate_candidate(candidate, since, until, course)
        if rejected_entry:
            rejected.append(rejected_entry)
        else:
            accepted.append(prepared)

    url_unique = []
    seen_urls = set()
    for candidate in sorted(accepted, key=candidate_sort_key):
        if candidate["url"] in seen_urls:
            rejected.append(rejected_candidate(candidate, "duplicate_url"))
            continue
        seen_urls.add(candidate["url"])
        url_unique.append(candidate)

    parents = list(range(len(url_unique)))

    def find(index):
        while parents[index] != index:
            parents[index] = parents[parents[index]]
            index = parents[index]
        return index

    def union(left, right):
        left_root, right_root = find(left), find(right)
        if left_root != right_root:
            parents[right_root] = left_root

    for left in range(len(url_unique)):
        for right in range(left + 1, len(url_unique)):
            if similar_title(url_unique[left]["title"], url_unique[right]["title"]):
                union(left, right)

    clusters = {}
    for index, candidate in enumerate(url_unique):
        clusters.setdefault(find(index), []).append(candidate)
    canonical = []
    for members in clusters.values():
        winner = min(members, key=candidate_sort_key)
        canonical.append(winner)
        rejected.extend(
            rejected_candidate(candidate, "similar_title")
            for candidate in members
            if candidate is not winner
        )
    canonical.sort(key=candidate_sort_key)

    selected, excess = canonical[:max_items], canonical[max_items:]
    rejected.extend(rejected_candidate(candidate, "max_items_exceeded") for candidate in excess)
    edition_id = f"F{edition_date.strftime('%Y%m%d')}"
    items = []
    for position, candidate in enumerate(selected, start=1):
        item = {key: value for key, value in candidate.items() if not key.startswith("_")}
        item["item_id"] = f"{edition_id}-{position:02d}"
        items.append(item)

    rejection_reasons = {entry["reason"] for entry in rejected}
    status = "ready" if items else "no_eligible_candidates"
    if not items and rejection_reasons and rejection_reasons <= {
        "missing_course_evidence",
        "course_mismatch",
    }:
        status = "skipped_no_course_evidence"
    rejected.sort(key=lambda entry: (entry["reason"], str(entry["title"]), str(entry["url"])))
    return {
        "status": status,
        "edition_id": edition_id,
        "course": course,
        "items": items,
        "rejected": rejected,
    }


def build_parser():
    parser = JsonArgumentParser(add_help=False)
    parser.add_argument("--input", required=True)
    parser.add_argument("--since", required=True)
    parser.add_argument("--until", required=True)
    parser.add_argument("--edition-date", required=True)
    parser.add_argument("--max-items", type=int, default=3)
    return parser


def main(argv=None):
    try:
        arguments = build_parser().parse_args(argv)
        since = parse_timestamp(arguments.since, "since")
        until = parse_timestamp(arguments.until, "until")
        if since > until:
            raise InputError("since must not be after until")
        try:
            edition_date = datetime.strptime(arguments.edition_date, "%Y-%m-%d").date()
        except ValueError as error:
            raise InputError("edition-date must use YYYY-MM-DD") from error
        try:
            payload = json.loads(Path(arguments.input).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise InputError("input must be a readable JSON object") from error
        print(
            json.dumps(
                normalize(payload, since, until, edition_date, arguments.max_items),
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
        )
        return 0
    except (InputError, ValueError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False, separators=(",", ":")))
        return 2


if __name__ == "__main__":
    sys.exit(main())
