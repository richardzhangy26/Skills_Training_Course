#!/usr/bin/env python3
"""在本地结构化案例库中返回可解释的候选案例。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any, Iterable


STOP_CHARS = set("的了和与及或是吗呢请问可以给我具体讲讲涉及哪些什么一个这个那个中案案例")
STUDENT_VISIBLE_STATUSES = {"待补证", "已发布"}


def normalize(value: str) -> str:
    return re.sub(r"[^0-9a-z\u3400-\u9fff]+", "", value.casefold())


def query_terms(query: str) -> set[str]:
    normalized = normalize(query)
    terms = set(
        normalized[index : index + 2]
        for index in range(max(0, len(normalized) - 1))
        if not all(char in STOP_CHARS for char in normalized[index : index + 2])
    )
    latin = re.findall(r"[a-z0-9]{2,}", query.casefold())
    terms.update(latin)
    return {term for term in terms if term}


def score_case(query: str, case: dict[str, Any]) -> tuple[int, list[str]]:
    normalized_query = normalize(query)
    title = normalize(case.get("title", ""))
    facts = normalize(case.get("basic_facts") or "")
    laws = normalize(
        " ".join(
            item.get("citation_text", "")
            for item in case.get("legal_provisions", [])
        )
    )
    analysis = normalize(case.get("legal_analysis") or "")
    reasons: list[str] = []
    score = 0
    if title and title in normalized_query:
        score += 1000
        reasons.append("exact_title_in_query")
    if normalized_query and normalized_query in title:
        score += 600
        reasons.append("query_in_title")
    for term in query_terms(query):
        weight = max(1, len(term))
        if term in title:
            score += 18 * weight
            reasons.append(f"title:{term}")
        if term in facts:
            score += 5 * weight
            reasons.append(f"facts:{term}")
        if term in laws:
            score += 3 * weight
            reasons.append(f"law:{term}")
        if term in analysis:
            score += 2 * weight
            reasons.append(f"analysis:{term}")
    return score, reasons


def search_cases(
    query: str, cases: Iterable[dict[str, Any]], limit: int = 5
) -> list[dict[str, Any]]:
    if not query.strip() or limit < 1:
        return []
    scored: list[tuple[int, str, dict[str, Any], list[str]]] = []
    for case in cases:
        score, reasons = score_case(query, case)
        title_match = any(
            reason in {"exact_title_in_query", "query_in_title"} for reason in reasons
        )
        keyword_in_title = any(reason.startswith("title:") for reason in reasons)
        matched_terms = {
            reason.split(":", 1)[1] for reason in reasons if ":" in reason
        }
        if score > 0 and (title_match or keyword_in_title or len(matched_terms) >= 2):
            scored.append((score, case["case_id"], case, reasons))
    scored.sort(key=lambda item: (-item[0], item[1]))
    results: list[dict[str, Any]] = []
    for score, _, case, reasons in scored[:limit]:
        result = dict(case)
        result["match_score"] = score
        result["match_reasons"] = reasons
        results.append(result)
    return results


def load_cases(library_root: Path) -> list[dict[str, Any]]:
    library_root = Path(library_root)
    pointer = library_root / "current.json"
    if pointer.exists():
        release = json.loads(pointer.read_text(encoding="utf-8")).get("release", "")
        if not re.fullmatch(r"v\d{4}", release):
            raise ValueError("invalid_current_release")
        library_root = library_root / "releases" / release
        if not (library_root / "data" / "manifest.json").is_file():
            raise ValueError("current_release_missing")
    cases: list[dict[str, Any]] = []
    for path in sorted((library_root / "data" / "cases").glob("*.json")):
        case = json.loads(path.read_text(encoding="utf-8"))
        if case.get("case_status") in STUDENT_VISIBLE_STATUSES:
            cases.append(case)
    return cases


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("library_root", type=Path)
    parser.add_argument("query")
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args()
    try:
        result = {
            "status": "matches_found",
            "query": args.query,
            "matches": search_cases(
                args.query, load_cases(args.library_root), args.limit
            ),
        }
        if not result["matches"]:
            result["status"] = "no_match"
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except Exception as exc:  # pragma: no cover - CLI adapter
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        print(repr(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
