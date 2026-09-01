#!/usr/bin/env python3
"""把教师提供的候选案例整理为可确认的变更预览。"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from library_core import (  # noqa: E402
    evidence_validation_errors,
    find_sensitive_markers,
    resolve_active_root,
    validate_actor_reference,
)


COMPARE_FIELDS = (
    "title",
    "scene_id",
    "record_type",
    "jurisdiction",
    "basic_facts",
    "dispute_focus",
    "legal_provisions",
    "outcome_type",
    "outcome",
    "legal_analysis",
    "analysis_origin",
    "sources",
    "evidence_status",
)


def resolve_release(library_root: Path) -> Path:
    return resolve_active_root(library_root)


def load_state(library_root: Path) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    release = resolve_release(Path(library_root))
    data_root = release / "data"
    manifest = json.loads((data_root / "manifest.json").read_text(encoding="utf-8"))
    scenes = json.loads((data_root / "scenes.json").read_text(encoding="utf-8"))
    cases = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted((data_root / "cases").glob("*.json"))
    ]
    return manifest, scenes, cases


def normalize_title(value: str) -> str:
    return re.sub(r"[^0-9a-z\u3400-\u9fff]+", "", value.casefold())


def field_differences(candidate: dict[str, Any], existing: dict[str, Any]) -> list[str]:
    return [
        field
        for field in COMPARE_FIELDS
        if field in candidate and candidate.get(field) != existing.get(field)
    ]


def compute_change_set_id(
    base_version: int,
    changes: list[dict[str, Any]],
    actor_reference: str | None = None,
    confirmation_nonce: str | None = None,
) -> str:
    canonical = json.dumps(
        {
            "base_version": base_version,
            "changes": changes,
            "actor_reference": actor_reference,
            "confirmation_nonce": confirmation_nonce,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


def prepare_update(
    candidate_records: list[dict[str, Any]],
    base_version: int,
    library_root: Path,
    actor_reference: str | None = None,
    confirmation_nonce: str | None = None,
) -> dict[str, Any]:
    if not validate_actor_reference(actor_reference):
        raise ValueError("invalid_actor_reference")
    manifest, scenes, cases = load_state(Path(library_root))
    scene_ids = {scene["scene_id"] for scene in scenes}
    cases_by_title = {normalize_title(case["title"]): case for case in cases}
    cases_by_facts = {
        normalize_title(case.get("basic_facts") or ""): case
        for case in cases
        if normalize_title(case.get("basic_facts") or "")
    }
    cases_by_id = {case["case_id"]: case for case in cases}
    candidate_titles: dict[str, int] = {}
    candidate_facts: dict[str, int] = {}
    changes: list[dict[str, Any]] = []

    for index, candidate in enumerate(candidate_records, start=1):
        clean = dict(candidate)
        sensitive_markers = find_sensitive_markers(clean)
        if sensitive_markers:
            changes.append(
                {
                    "candidate_index": index,
                    "action": "sensitive_content_review_required",
                    "sensitive_markers": sensitive_markers,
                    "candidate_redacted": True,
                    "resolved": False,
                }
            )
            continue
        evidence_errors = evidence_validation_errors(clean)
        if evidence_errors:
            changes.append(
                {
                    "candidate_index": index,
                    "action": "evidence_review_required",
                    "evidence_errors": evidence_errors,
                    "candidate": clean,
                    "resolved": False,
                }
            )
            continue
        operation = clean.pop("operation", "add")
        if operation in {"update", "withdraw", "delete"}:
            target_case_id = clean.pop("target_case_id", None)
            existing = cases_by_id.get(target_case_id)
            if existing is None:
                changes.append(
                    {
                        "candidate_index": index,
                        "action": "invalid_target",
                        "reason": "target_case_not_found",
                        "target_case_id": target_case_id,
                        "candidate": clean,
                        "resolved": False,
                    }
                )
                continue
            proposed_title = clean.get("title")
            if proposed_title:
                collision = cases_by_title.get(normalize_title(proposed_title))
                if collision and collision["case_id"] != target_case_id:
                    changes.append(
                        {
                            "candidate_index": index,
                            "action": "title_collision",
                            "matched_case_id": existing["case_id"],
                            "conflicting_case_id": collision["case_id"],
                            "conflicting_title": collision["title"],
                            "candidate": clean,
                            "resolved": False,
                        }
                    )
                    continue
            proposed_facts = clean.get("basic_facts")
            if proposed_facts:
                fact_collision = cases_by_facts.get(normalize_title(proposed_facts))
                if fact_collision and fact_collision["case_id"] != target_case_id:
                    changes.append(
                        {
                            "candidate_index": index,
                            "action": "fact_collision",
                            "matched_case_id": existing["case_id"],
                            "conflicting_case_id": fact_collision["case_id"],
                            "conflicting_title": fact_collision["title"],
                            "candidate": clean,
                            "resolved": False,
                        }
                    )
                    continue
            differences = field_differences(clean, existing)
            if operation == "update" and not differences:
                changes.append(
                    {
                        "candidate_index": index,
                        "action": "no_change",
                        "matched_case_id": existing["case_id"],
                        "matched_title": existing["title"],
                        "candidate": clean,
                        "resolved": False,
                    }
                )
                continue
            changes.append(
                {
                    "candidate_index": index,
                    "action": operation,
                    "matched_case_id": existing["case_id"],
                    "matched_title": existing["title"],
                    "differences": differences,
                    "candidate": clean,
                    "resolved": True,
                }
            )
            continue
        if operation != "add":
            changes.append(
                {
                    "candidate_index": index,
                    "action": "invalid_candidate",
                    "reason": "unsupported_operation",
                    "candidate": clean,
                    "resolved": False,
                }
            )
            continue
        title = str(clean.get("title", "")).strip()
        if not title:
            changes.append(
                {
                    "candidate_index": index,
                    "action": "invalid_candidate",
                    "reason": "missing_title",
                    "candidate": clean,
                    "resolved": False,
                }
            )
            continue
        clean["title"] = title
        title_key = normalize_title(title)
        prior_title_index = candidate_titles.get(title_key)
        if prior_title_index:
            changes.append(
                {
                    "candidate_index": index,
                    "action": "possible_duplicate",
                    "matched_candidate_index": prior_title_index,
                    "match_basis": "batch_title",
                    "differences": [],
                    "candidate": clean,
                    "resolved": False,
                }
            )
            continue
        fact_key = normalize_title(clean.get("basic_facts") or "")
        prior_fact_index = candidate_facts.get(fact_key) if fact_key else None
        if prior_fact_index:
            changes.append(
                {
                    "candidate_index": index,
                    "action": "possible_duplicate",
                    "matched_candidate_index": prior_fact_index,
                    "match_basis": "batch_basic_facts",
                    "differences": [],
                    "candidate": clean,
                    "resolved": False,
                }
            )
            continue
        existing = cases_by_title.get(normalize_title(title))
        if existing:
            changes.append(
                {
                    "candidate_index": index,
                    "action": "possible_duplicate",
                    "matched_case_id": existing["case_id"],
                    "matched_title": existing["title"],
                    "match_basis": "title",
                    "differences": field_differences(clean, existing),
                    "candidate": clean,
                    "resolved": False,
                }
            )
            continue
        fact_match = cases_by_facts.get(fact_key) if fact_key else None
        if fact_match:
            changes.append(
                {
                    "candidate_index": index,
                    "action": "possible_duplicate",
                    "matched_case_id": fact_match["case_id"],
                    "matched_title": fact_match["title"],
                    "match_basis": "basic_facts",
                    "differences": field_differences(clean, fact_match),
                    "candidate": clean,
                    "resolved": False,
                }
            )
            continue
        if clean.get("scene_id") not in scene_ids:
            changes.append(
                {
                    "candidate_index": index,
                    "action": "scene_confirmation_required",
                    "scene_candidates": clean.get("scene_candidates", []),
                    "candidate": clean,
                    "resolved": False,
                }
            )
            continue
        changes.append(
            {
                "candidate_index": index,
                "action": "add",
                "candidate": clean,
                "resolved": True,
            }
        )
        candidate_titles[title_key] = index
        if fact_key:
            candidate_facts[fact_key] = index

    unresolved_count = sum(not item["resolved"] for item in changes)
    return {
        "status": "needs_resolution" if unresolved_count else "preview_ready",
        "change_set_id": compute_change_set_id(
            base_version, changes, actor_reference, confirmation_nonce
        ),
        "base_version": base_version,
        "observed_version": manifest["library_version"],
        "candidate_count": len(candidate_records),
        "unresolved_count": unresolved_count,
        "requires_confirmation": True,
        "actor_reference": actor_reference,
        "confirmation_nonce": confirmation_nonce,
        "changes": changes,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("library_root", type=Path)
    parser.add_argument("candidate_json", type=Path)
    parser.add_argument("--base-version", type=int, required=True)
    parser.add_argument("--actor-reference")
    parser.add_argument("--confirmation-nonce")
    args = parser.parse_args()
    try:
        candidates = json.loads(args.candidate_json.read_text(encoding="utf-8"))
        if not isinstance(candidates, list):
            raise ValueError("candidate_json_must_be_array")
        print(
            json.dumps(
                prepare_update(
                    candidates,
                    args.base_version,
                    args.library_root,
                    args.actor_reference,
                    args.confirmation_nonce,
                ),
                ensure_ascii=False,
            )
        )
        return 0
    except Exception as exc:  # pragma: no cover - CLI adapter
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        print(repr(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
