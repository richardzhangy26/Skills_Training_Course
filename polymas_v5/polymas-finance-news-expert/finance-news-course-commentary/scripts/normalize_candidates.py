#!/usr/bin/env python3
"""Deterministically validate and prepare finance-news course briefings."""

import argparse
import ipaddress
import json
import re
import sys
import unicodedata
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path
from urllib.parse import parse_qsl, unquote, urlencode, urlsplit, urlunsplit


MAX_INPUT_BYTES = 1024 * 1024
MAX_CANDIDATES = 100
MAX_CITATIONS = 10
MAX_JSON_DEPTH = 100
MAX_TRAVERSAL_NODES = 20_000

COURSE_FIELDS = ("course_id", "course_name")
REQUIRED_CANDIDATE_FIELDS = (
    "title",
    "url",
    "source",
    "source_tier",
    "published_at",
    "fact_summary",
    "theory_analysis",
    "discussion_question",
    "theory_citations",
)
REQUIRED_CITATION_FIELDS = (
    "course_id",
    "course_name",
    "knowledge_point",
    "resource_title",
    "excerpt",
)
OUTPUT_CANDIDATE_FIELDS = tuple(
    field for field in REQUIRED_CANDIDATE_FIELDS if field != "source_tier"
) + ("source_level",)
SOURCE_TIER_LEVELS = {
    "official": 1,
    "primary": 1,
    "regulator": 1,
    "government": 1,
    "exchange": 1,
    "company_announcement": 1,
    "authoritative_media": 2,
    "media": 2,
    "other": 3,
}
OFFICIAL_HOSTS = frozenset(
    {
        "gov.cn",
        "pbc.gov.cn",
        "mof.gov.cn",
        "stats.gov.cn",
        "nfra.gov.cn",
        "csrc.gov.cn",
        "sse.com.cn",
        "szse.cn",
        "bse.cn",
        "cninfo.com.cn",
    }
)
MEDIA_HOSTS = frozenset(
    {
        "news.cn",
        "xinhuanet.com",
        "cctv.com",
        "cs.com.cn",
        "cnstock.com",
        "stcn.com",
    }
)
CANONICAL_SOURCE_LABELS = (
    ("pbc.gov.cn", "中国人民银行"),
    ("stats.gov.cn", "国家统计局"),
    ("nfra.gov.cn", "国家金融监督管理总局"),
    ("csrc.gov.cn", "中国证监会"),
    ("mof.gov.cn", "财政部"),
    ("sse.com.cn", "上海证券交易所"),
    ("szse.cn", "深圳证券交易所"),
    ("bse.cn", "北京证券交易所"),
    ("cninfo.com.cn", "巨潮资讯"),
    ("gov.cn", "中国政府网"),
    ("news.cn", "新华网"),
    ("xinhuanet.com", "新华网"),
    ("cctv.com", "央视网"),
    ("cs.com.cn", "中国证券报"),
    ("cnstock.com", "上海证券报"),
    ("stcn.com", "证券时报"),
)
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
INVESTMENT_ADVICE_PHRASES = (
    "建议投资",
    "建议买入",
    "建议买进",
    "建议购入",
    "建议卖出",
    "立即买入",
    "立即买进",
    "立即购入",
    "立即卖出",
    "推荐买入",
    "推荐买进",
    "推荐购入",
    "推荐卖出",
    "强烈买入",
    "强烈买进",
    "强烈购入",
    "强烈卖出",
    "买入",
    "买进",
    "购入",
    "卖出",
    "加仓",
    "减仓",
    "建仓",
    "清仓",
    "抄底",
    "止损",
    "止盈",
    "目标价",
    "保证收益",
    "保本收益",
    "稳赚",
    "strong buy",
    "strong sell",
    "buy now",
    "sell now",
    "target price",
    "guaranteed return",
    "guaranteed returns",
    "guaranteed profit",
    "overweight",
    "underweight",
)
INVESTMENT_ADVICE_HINTS = (
    "建议",
    "推荐",
    "应该",
    "可考虑",
    "值得",
    "维持",
    "评级",
    "看多",
    "看空",
    "recommend",
    "should",
    "consider",
    "worth",
    "maintain",
    "rating",
    "bullish",
    "bearish",
)
INVESTMENT_ADVICE_ACTIONS = (
    "持有",
    "增持",
    "减持",
    "做多",
    "做空",
    "买进",
    "购入",
    "卖出",
    "加仓",
    "减仓",
    "目标价",
    "buy",
    "sell",
    "hold",
    "long",
    "short",
    "overweight",
    "underweight",
    "target price",
    "guaranteed return",
)
UNRESERVED_URL_CHARACTERS = frozenset(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~"
)

CANDIDATE_LENGTH_LIMITS = {
    "title": 300,
    "url": 4000,
    "source": 300,
    "source_tier": 64,
    "published_at": 100,
    "fact_summary": 4000,
    "theory_analysis": 4000,
    "discussion_question": 4000,
}
CITATION_LENGTH_LIMITS = {
    "course_id": 300,
    "course_name": 300,
    "knowledge_point": 300,
    "resource_title": 300,
    "excerpt": 2000,
}


class InputError(ValueError):
    """An input or command-line argument cannot produce a valid briefing."""


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message):  # pragma: no cover - exercised through the CLI.
        del message
        raise InputError("invalid command-line arguments")


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


def normalize_hostname(hostname):
    try:
        return hostname.casefold().rstrip(".").encode("idna").decode("ascii")
    except UnicodeError as error:
        raise InputError("invalid_url") from error


def host_is_private_or_local(hostname):
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        return (
            hostname == "localhost"
            or hostname.endswith(".localhost")
            or hostname.endswith(".local")
            or hostname.endswith(".internal")
        )
    return not address.is_global


def normalize_url_path(path):
    normalized_segments = []
    for raw_segment in path.split("/"):
        segment = re.sub(
            r"%([0-9A-Fa-f]{2})",
            lambda match: (
                chr(int(match.group(1), 16))
                if chr(int(match.group(1), 16)) in UNRESERVED_URL_CHARACTERS
                else f"%{match.group(1).upper()}"
            ),
            raw_segment,
        )
        decoded_segment = unquote(segment)
        if not segment or decoded_segment == ".":
            continue
        if decoded_segment == "..":
            if normalized_segments:
                normalized_segments.pop()
            continue
        normalized_segments.append(segment)
    return "/" + "/".join(normalized_segments) if normalized_segments else "/"


def canonical_url(value):
    if not isinstance(value, str) or not value.strip():
        raise InputError("invalid_url")
    parsed = urlsplit(value.strip())
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
        raise InputError("invalid_url")
    if any(character.isspace() for character in parsed.netloc):
        raise InputError("invalid_url")
    if parsed.username is not None or parsed.password is not None:
        raise InputError("untrusted_source")
    hostname = normalize_hostname(parsed.hostname)
    if not hostname or host_is_private_or_local(hostname):
        raise InputError("untrusted_source")
    display_hostname = f"[{hostname}]" if ":" in hostname else hostname
    try:
        port = parsed.port
    except ValueError as error:
        raise InputError("invalid_url") from error
    netloc = display_hostname
    if port and not (
        (parsed.scheme.lower() == "http" and port == 80)
        or (parsed.scheme.lower() == "https" and port == 443)
    ):
        netloc = f"{display_hostname}:{port}"
    path = normalize_url_path(parsed.path or "/")
    if path != "/":
        path = path.rstrip("/")
    query = [
        (name, content)
        for name, content in parse_qsl(parsed.query, keep_blank_values=True)
        if name.lower() not in TRACKING_PARAMETERS
        and not name.lower().startswith("utm_")
    ]
    return urlunsplit((parsed.scheme.lower(), netloc, path, urlencode(sorted(query)), ""))


def hostname_matches(hostname, allowed_hosts):
    return any(
        hostname == allowed or hostname.endswith(f".{allowed}")
        for allowed in allowed_hosts
    )


def derived_source_level(url):
    hostname = normalize_hostname(urlsplit(url).hostname or "")
    if hostname_matches(hostname, OFFICIAL_HOSTS):
        return 1
    if hostname_matches(hostname, MEDIA_HOSTS):
        return 2
    return None


def canonical_source_label(url):
    hostname = normalize_hostname(urlsplit(url).hostname or "")
    for allowed_hostname, label in CANONICAL_SOURCE_LABELS:
        if hostname_matches(hostname, {allowed_hostname}):
            return label
    raise InputError("untrusted_source")


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


def normalize_advice_text(value):
    normalized_value = unicodedata.normalize("NFKC", value).casefold()
    return "".join(
        character
        for character in normalized_value
        if unicodedata.category(character)[0] in {"L", "N"}
    )


NORMALIZED_ADVICE_PHRASES = tuple(
    normalize_advice_text(phrase) for phrase in INVESTMENT_ADVICE_PHRASES
)
NORMALIZED_ADVICE_HINTS = tuple(
    normalize_advice_text(phrase) for phrase in INVESTMENT_ADVICE_HINTS
)
NORMALIZED_ADVICE_ACTIONS = tuple(
    normalize_advice_text(phrase) for phrase in INVESTMENT_ADVICE_ACTIONS
)


def bounded_string_values(value):
    stack = [value]
    visited = 0
    while stack:
        current = stack.pop()
        visited += 1
        if visited > MAX_TRAVERSAL_NODES:
            raise InputError("input exceeds traversal limits")
        if isinstance(current, str):
            yield current
        elif isinstance(current, dict):
            for key, nested_value in current.items():
                stack.append(nested_value)
                stack.append(key)
        elif isinstance(current, (list, tuple)):
            stack.extend(current)


def contains_investment_advice(value):
    for text in bounded_string_values(value):
        normalized = normalize_advice_text(text)
        if any(pattern in normalized for pattern in NORMALIZED_ADVICE_PHRASES):
            return True
        if any(hint in normalized for hint in NORMALIZED_ADVICE_HINTS) and any(
            action in normalized for action in NORMALIZED_ADVICE_ACTIONS
        ):
            return True
    return False


def validate_json_structure(value):
    stack = [(value, 0)]
    visited = 0
    while stack:
        current, depth = stack.pop()
        visited += 1
        if visited > MAX_TRAVERSAL_NODES:
            raise InputError("input exceeds traversal limits")
        if depth > MAX_JSON_DEPTH:
            raise InputError(f"input JSON nesting exceeds {MAX_JSON_DEPTH} levels")
        if isinstance(current, dict):
            stack.extend((item, depth + 1) for pair in current.items() for item in pair)
        elif isinstance(current, list):
            stack.extend((item, depth + 1) for item in current)


def validate_course(course):
    if not isinstance(course, dict):
        raise InputError("input.course must be an object")
    selected_course = {}
    for field in COURSE_FIELDS:
        value = course.get(field)
        if not isinstance(value, str) or not value.strip():
            raise InputError(f"input.course.{field} is required")
        if len(value) > 300:
            raise InputError(f"input.course.{field} exceeds 300 characters")
        selected_course[field] = value.strip()
    if contains_investment_advice(selected_course):
        raise InputError("input.course contains investment advice language")
    return selected_course


def validate_course_evidence(candidate, selected_course):
    citations = candidate.get("theory_citations")
    if not isinstance(citations, list) or not citations:
        return None, "missing_course_evidence"
    if len(citations) > MAX_CITATIONS:
        return None, "too_many_theory_citations"
    validated = []
    for citation in citations:
        if not isinstance(citation, dict):
            return None, "missing_course_evidence"
        safe_citation = {}
        for field in REQUIRED_CITATION_FIELDS:
            value = citation.get(field)
            if not isinstance(value, str) or not value.strip():
                return None, "missing_course_evidence"
            if len(value) > CITATION_LENGTH_LIMITS[field]:
                return None, "field_too_long"
            safe_citation[field] = value.strip()
        if contains_investment_advice(safe_citation):
            return None, "investment_advice_language"
        if any(
            safe_citation[field] != selected_course[field]
            for field in COURSE_FIELDS
        ):
            return None, "course_mismatch"
        validated.append(safe_citation)
    return validated, None


def rejected_candidate(candidate_index, reason):
    return {"candidate_index": candidate_index, "reason": reason}


def candidate_limit_problem(candidate):
    if not isinstance(candidate, dict):
        return None
    for field, limit in CANDIDATE_LENGTH_LIMITS.items():
        value = candidate.get(field)
        if isinstance(value, str) and len(value) > limit:
            return "field_too_long"
    citations = candidate.get("theory_citations")
    if isinstance(citations, list):
        if len(citations) > MAX_CITATIONS:
            return "too_many_theory_citations"
        for citation in citations:
            if not isinstance(citation, dict):
                continue
            for field, limit in CITATION_LENGTH_LIMITS.items():
                value = citation.get(field)
                if isinstance(value, str) and len(value) > limit:
                    return "field_too_long"
    return None


def sort_rejected(rejected):
    rejected.sort(key=lambda entry: (entry["reason"], entry["candidate_index"]))


def result_payload(
    status,
    status_origin,
    edition_id,
    course,
    retrieved_at,
    course_evidence_available,
    items,
    rejected,
):
    sort_rejected(rejected)
    result = {
        "status": status,
        "status_origin": status_origin,
        "edition_id": edition_id,
        "course": course,
        "retrieved_at": retrieved_at.isoformat(),
        "course_evidence_available": course_evidence_available,
        "items": items,
        "rejected": rejected,
    }
    if contains_investment_advice(result):
        raise InputError("output contains investment advice language")
    return result


def validate_candidate(candidate, candidate_index, since, until, selected_course):
    reject = lambda reason: (None, rejected_candidate(candidate_index, reason))
    if not isinstance(candidate, dict):
        return reject("invalid_candidate")
    for field in REQUIRED_CANDIDATE_FIELDS:
        if field not in candidate:
            return reject(f"missing_{field}")
        if field == "theory_citations":
            continue
        value = candidate[field]
        if field == "source_tier":
            if not isinstance(value, str):
                return reject("invalid_source_tier")
            if not value.strip():
                return reject("missing_source_tier")
        elif not isinstance(value, str) or not value.strip():
            return reject(f"missing_{field}")
        if isinstance(value, str) and len(value) > CANDIDATE_LENGTH_LIMITS[field]:
            return reject("field_too_long")
    citations, evidence_problem = validate_course_evidence(candidate, selected_course)
    if evidence_problem:
        return reject(evidence_problem)
    try:
        url = canonical_url(candidate["url"])
    except (InputError, ValueError, UnicodeError) as error:
        reason = str(error) if str(error) == "untrusted_source" else "invalid_url"
        return reject(reason)
    try:
        published_at = parse_timestamp(candidate["published_at"], "published_at")
    except InputError:
        return reject("invalid_published_at")
    if not since <= published_at <= until:
        return reject("outside_time_window")
    source_tier = candidate["source_tier"].strip().lower()
    if source_tier not in SOURCE_TIER_LEVELS:
        return reject("invalid_source_tier")
    derived_level = derived_source_level(url)
    if derived_level is None:
        return reject("untrusted_source")
    if SOURCE_TIER_LEVELS[source_tier] != derived_level:
        return reject("source_tier_mismatch")
    prepared = {
        "title": candidate["title"].strip(),
        "url": url,
        "source": canonical_source_label(url),
        "published_at": candidate["published_at"].strip(),
        "fact_summary": candidate["fact_summary"].strip(),
        "theory_analysis": candidate["theory_analysis"].strip(),
        "discussion_question": candidate["discussion_question"].strip(),
        "theory_citations": citations,
        "source_level": derived_level,
        "_published_at": published_at,
        "_candidate_index": candidate_index,
    }
    if contains_investment_advice(
        {key: value for key, value in prepared.items() if not key.startswith("_")}
    ):
        return reject("investment_advice_language")
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
    if "retrieved_at" not in payload:
        raise InputError("input.retrieved_at is required")
    retrieved_at = parse_timestamp(payload["retrieved_at"], "retrieved_at")
    if "course_evidence_available" not in payload or type(
        payload["course_evidence_available"]
    ) is not bool:
        raise InputError("input.course_evidence_available must be a boolean")
    course_evidence_available = payload["course_evidence_available"]
    course = validate_course(payload.get("course"))
    candidates = payload.get("candidates")
    if not isinstance(candidates, list):
        raise InputError("input.candidates must be an array")
    if len(candidates) > MAX_CANDIDATES:
        raise InputError(f"input.candidates exceeds {MAX_CANDIDATES} items")
    if max_items < 1 or max_items > 3:
        raise InputError("max-items must be between 1 and 3")
    edition_id = f"F{edition_date.strftime('%Y%m%d')}"
    if not course_evidence_available:
        rejected = [
            rejected_candidate(
                index,
                candidate_limit_problem(candidate) or "course_evidence_unavailable",
            )
            for index, candidate in enumerate(candidates)
        ]
        return result_payload(
            "skipped_no_course_evidence",
            "precheck",
            edition_id,
            course,
            retrieved_at,
            course_evidence_available,
            [],
            rejected,
        )

    rejected = []
    accepted = []
    for candidate_index, candidate in enumerate(candidates):
        prepared, rejected_entry = validate_candidate(
            candidate, candidate_index, since, until, course
        )
        if rejected_entry:
            rejected.append(rejected_entry)
        else:
            accepted.append(prepared)

    url_unique = []
    seen_urls = set()
    for candidate in sorted(accepted, key=candidate_sort_key):
        if candidate["url"] in seen_urls:
            rejected.append(
                rejected_candidate(candidate["_candidate_index"], "duplicate_url")
            )
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
            rejected_candidate(candidate["_candidate_index"], "similar_title")
            for candidate in members
            if candidate is not winner
        )
    canonical.sort(key=candidate_sort_key)

    selected, excess = canonical[:max_items], canonical[max_items:]
    rejected.extend(
        rejected_candidate(candidate["_candidate_index"], "max_items_exceeded")
        for candidate in excess
    )
    items = []
    for position, candidate in enumerate(selected, start=1):
        item = {key: value for key, value in candidate.items() if not key.startswith("_")}
        item["item_id"] = f"{edition_id}-{position:02d}"
        items.append(item)

    rejection_reasons = {entry["reason"] for entry in rejected}
    status = "ready" if items else "no_eligible_candidates"
    status_origin = "normalizer"
    if not items and rejection_reasons and rejection_reasons <= {
        "missing_course_evidence",
        "course_mismatch",
    }:
        status = "skipped_no_course_evidence"
        status_origin = "candidate_filter"
    return result_payload(
        status,
        status_origin,
        edition_id,
        course,
        retrieved_at,
        course_evidence_available,
        items,
        rejected,
    )


def build_parser():
    parser = JsonArgumentParser(add_help=False)
    parser.add_argument("--input", required=True)
    parser.add_argument("--since", required=True)
    parser.add_argument("--until", required=True)
    parser.add_argument("--edition-date", required=True)
    parser.add_argument("--max-items", type=int, default=3)
    return parser


def read_payload(input_path):
    try:
        path = Path(input_path)
        if path.stat().st_size > MAX_INPUT_BYTES:
            raise InputError(f"input file exceeds {MAX_INPUT_BYTES} bytes")
        raw = path.read_bytes()
        if len(raw) > MAX_INPUT_BYTES:
            raise InputError(f"input file exceeds {MAX_INPUT_BYTES} bytes")
        payload = json.loads(raw.decode("utf-8"))
    except InputError:
        raise
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise InputError("input must be a readable JSON object") from error
    except RecursionError as error:
        raise InputError("input JSON nesting exceeds parser limits") from error
    validate_json_structure(payload)
    return payload


def error_message(error):
    if isinstance(error, MemoryError):
        return "input exceeds memory limits"
    if isinstance(error, RecursionError):
        return "input JSON nesting exceeds parser limits"
    return str(error) or "input could not be processed"


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
        payload = read_payload(arguments.input)
        output = normalize(payload, since, until, edition_date, arguments.max_items)
        print(
            json.dumps(
                output,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
        )
        return 0
    except (InputError, ValueError, RecursionError, MemoryError) as error:
        print(
            json.dumps(
                {"error": error_message(error)},
                ensure_ascii=False,
                separators=(",", ":"),
            )
        )
        return 2


if __name__ == "__main__":
    sys.exit(main())
