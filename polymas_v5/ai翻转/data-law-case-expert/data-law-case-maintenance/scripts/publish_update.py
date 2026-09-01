#!/usr/bin/env python3
"""把已确认变更发布为版本化案例数据、HTML 和知识包候选。"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import build_knowledge_pack as canonical_knowledge_module  # noqa: E402
import render_html as canonical_render_module  # noqa: E402
from build_knowledge_pack import build_knowledge_pack  # noqa: E402
from library_core import (  # noqa: E402
    validate_actor_reference,
    validate_case,
    validate_confirmation_nonce,
    validate_release_root,
    write_json,
)
from prepare_update import (  # noqa: E402
    compute_change_set_id,
    load_state,
    resolve_release,
)
from render_html import render_library  # noqa: E402


UPDATABLE_FIELDS = {
    "title",
    "scene_id",
    "record_type",
    "jurisdiction",
    "basic_facts",
    "dispute_focus",
    "legal_provisions",
    "outcome_type",
    "outcome",
    "outcome_evidence_status",
    "legal_analysis",
    "analysis_origin",
    "sources",
    "evidence_status",
    "classification_review_required",
}
VISIBLE_STATUSES = {"已发布"}


def materialize_case(candidate: dict[str, Any], case_id: str) -> dict[str, Any]:
    analysis_origin = candidate.get("analysis_origin")
    if analysis_origin not in {
        "source_material",
        "teacher_confirmed",
        "ai_draft",
    }:
        raise ValueError("analysis_origin_required")
    record = {
        "case_id": case_id,
        "title": candidate["title"],
        "scene_id": candidate["scene_id"],
        "record_type": candidate.get("record_type", "unclassified"),
        "jurisdiction": candidate.get("jurisdiction", "待确认"),
        "case_status": "草稿" if analysis_origin == "ai_draft" else "已发布",
        "basic_facts": candidate.get("basic_facts"),
        "dispute_focus": candidate.get("dispute_focus"),
        "legal_provisions": candidate.get("legal_provisions", []),
        "outcome_type": candidate.get("outcome_type", "unknown"),
        "outcome": candidate.get("outcome"),
        "outcome_evidence_status": candidate.get(
            "outcome_evidence_status", "missing"
        ),
        "legal_analysis": candidate.get("legal_analysis"),
        "analysis_origin": analysis_origin,
        "sources": candidate.get("sources", []),
        "evidence_status": candidate.get("evidence_status", "待补证"),
        "classification_review_required": candidate.get(
            "classification_review_required", False
        ),
        "version": 1,
    }
    errors = validate_case(record)
    if errors:
        raise ValueError(f"candidate_contract_errors:{','.join(errors)}")
    return record


def copy_release_content(source: Path, destination: Path) -> None:
    shutil.copytree(source / "data", destination / "data")
    if (source / "exports").is_dir():
        shutil.copytree(source / "exports", destination / "exports")


def ensure_snapshot(library_root: Path, current_release: Path, version: int) -> Path:
    snapshot = library_root / "releases" / f"v{version:04d}"
    if snapshot.exists():
        return snapshot
    snapshot.mkdir(parents=True)
    try:
        copy_release_content(current_release, snapshot)
    except Exception:
        shutil.rmtree(snapshot)
        raise
    return snapshot


def max_historical_case_sequence(
    library_root: Path, current_cases: list[dict[str, Any]]
) -> int:
    sequences = [int(case["case_id"].split("-")[1]) for case in current_cases]
    for path in (Path(library_root) / "releases").glob(
        "v[0-9][0-9][0-9][0-9]/data/cases/DLCL-*.json"
    ):
        sequences.append(int(path.stem.split("-")[1]))
    return max(sequences, default=0)


def publish_update(
    change_set: dict[str, Any],
    confirmed: bool,
    library_root: Path,
    confirmation_change_set_id: str | None = None,
    _lock_held: bool = False,
) -> dict[str, Any]:
    library_root = Path(library_root)
    if not confirmed:
        return {
            "status": "awaiting_confirmation",
            "change_set_id": change_set.get("change_set_id"),
        }
    stored_change_set_id = change_set.get("change_set_id")
    if not validate_actor_reference(change_set.get("actor_reference")) or not change_set.get(
        "actor_reference"
    ):
        return {
            "status": "invalid_actor_reference",
            "change_set_id": stored_change_set_id,
        }
    if not validate_confirmation_nonce(change_set.get("confirmation_nonce")):
        return {
            "status": "confirmation_nonce_required",
            "change_set_id": stored_change_set_id,
        }
    if (
        not confirmation_change_set_id
        or confirmation_change_set_id != stored_change_set_id
    ):
        return {
            "status": "confirmation_mismatch",
            "change_set_id": stored_change_set_id,
        }
    recomputed_change_set_id = compute_change_set_id(
        int(change_set.get("base_version", -1)),
        change_set.get("changes", []),
        change_set.get("actor_reference"),
        change_set.get("confirmation_nonce"),
    )
    if recomputed_change_set_id != stored_change_set_id:
        return {
            "status": "invalid_change_set",
            "change_set_id": stored_change_set_id,
        }
    allowed_actions = {"add", "update", "withdraw", "delete"}
    raw_changes = change_set.get("changes", [])
    unresolved_items = [
        item
        for item in raw_changes
        if not item.get("resolved") or item.get("action") not in allowed_actions
    ]
    if unresolved_items:
        return {
            "status": "unresolved_changes",
            "change_set_id": change_set.get("change_set_id"),
            "unresolved_count": len(unresolved_items),
        }
    changes = list(raw_changes)
    if not changes:
        return {"status": "no_changes"}
    if any(item["action"] == "delete" for item in changes) and not change_set.get(
        "actor_reference"
    ):
        return {
            "status": "audit_context_required",
            "change_set_id": stored_change_set_id,
        }
    if not _lock_held:
        library_root.mkdir(parents=True, exist_ok=True)
        with (library_root / ".publish.lock").open("a+", encoding="utf-8") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            return publish_update(
                change_set,
                confirmed,
                library_root,
                confirmation_change_set_id,
                _lock_held=True,
            )

    manifest, scenes, cases = load_state(library_root)
    if manifest["library_version"] != change_set.get("base_version"):
        return {
            "status": "version_conflict",
            "base_version": change_set.get("base_version"),
            "current_version": manifest["library_version"],
        }

    current_release = resolve_release(library_root)
    current_version = int(manifest["library_version"])
    releases_root = library_root / "releases"
    releases_root.mkdir(parents=True, exist_ok=True)
    historical_versions = [
        int(path.name[1:])
        for path in releases_root.iterdir()
        if path.is_dir() and re.fullmatch(r"v\d{4}", path.name)
    ]
    new_version = max([current_version, *historical_versions]) + 1
    final_release = releases_root / f"v{new_version:04d}"
    if final_release.exists():
        return {"status": "release_exists", "library_version": new_version}

    transactions_root = library_root / "publish-transactions"
    transaction_path = transactions_root / f"{stored_change_set_id}.json"
    if transaction_path.exists():
        return {
            "status": "confirmation_already_used",
            "change_set_id": stored_change_set_id,
        }
    transactions_root.mkdir(parents=True, exist_ok=True)
    write_json(
        transaction_path,
        {
            "status": "pending",
            "change_set_id": stored_change_set_id,
            "base_version": current_version,
            "actor_reference": change_set.get("actor_reference"),
        },
    )

    staging = Path(
        tempfile.mkdtemp(prefix=f".v{new_version:04d}-", dir=releases_root)
    )
    release_created = False
    pointer_tmp: Path | None = None
    published_at = datetime.now(timezone.utc).isoformat()
    try:
        shutil.copytree(current_release / "data", staging / "data")
        staged_cases_dir = staging / "data" / "cases"
        max_id = max_historical_case_sequence(library_root, cases)
        scene_counts = {scene["scene_id"]: int(scene["case_count"]) for scene in scenes}
        cases_by_id = {case["case_id"]: case for case in cases}
        next_id = max_id
        deletion_audit: list[dict[str, Any]] = []
        for change in changes:
            action = change["action"]
            if action == "add":
                next_id += 1
                case_id = f"DLCL-{next_id:04d}"
                record = materialize_case(change["candidate"], case_id)
                write_json(staged_cases_dir / f"{case_id}.json", record)
                cases_by_id[case_id] = record
                if record["case_status"] in VISIBLE_STATUSES:
                    scene_counts[record["scene_id"]] += 1
                continue

            case_id = change["matched_case_id"]
            existing = cases_by_id[case_id]
            case_path = staged_cases_dir / f"{case_id}.json"
            if action == "update":
                updated = dict(existing)
                old_scene_id = updated["scene_id"]
                old_visible = updated.get("case_status") in VISIBLE_STATUSES
                for field, value in change["candidate"].items():
                    if field in UPDATABLE_FIELDS:
                        updated[field] = value
                if "basic_facts" in change["candidate"]:
                    updated.pop("fact_detail", None)
                if "legal_analysis" in change["candidate"]:
                    updated.pop("analysis_detail", None)
                if updated.get("analysis_origin") == "ai_draft":
                    updated["case_status"] = "草稿"
                elif existing.get("case_status") == "草稿":
                    updated["case_status"] = "已发布"
                updated["case_id"] = case_id
                updated["version"] = int(existing["version"]) + 1
                errors = validate_case(updated)
                if errors:
                    raise ValueError(
                        f"candidate_contract_errors:{','.join(errors)}"
                    )
                if updated["scene_id"] not in scene_counts:
                    raise ValueError("invalid_scene_id")
                new_visible = updated.get("case_status") in VISIBLE_STATUSES
                if old_visible:
                    scene_counts[old_scene_id] -= 1
                if new_visible:
                    scene_counts[updated["scene_id"]] += 1
                write_json(case_path, updated)
                cases_by_id[case_id] = updated
                continue

            if action == "withdraw":
                withdrawn = dict(existing)
                if withdrawn.get("case_status") in VISIBLE_STATUSES:
                    scene_counts[withdrawn["scene_id"]] -= 1
                withdrawn["case_status"] = "已撤下"
                withdrawn["version"] = int(existing["version"]) + 1
                write_json(case_path, withdrawn)
                cases_by_id[case_id] = withdrawn
                continue

            if existing.get("case_status") in VISIBLE_STATUSES:
                scene_counts[existing["scene_id"]] -= 1
            case_path.unlink()
            cases_by_id.pop(case_id)
            deletion_audit.append(
                {
                    "case_id": case_id,
                    "title": existing["title"],
                    "deleted_from_version": current_version,
                    "change_set_id": change_set.get("change_set_id"),
                    "deleted_at": published_at,
                    "actor_reference": change_set["actor_reference"],
                }
            )

        if deletion_audit:
            audit_path = staging / "data" / "deletion-audit.jsonl"
            existing_audit = (
                audit_path.read_text(encoding="utf-8") if audit_path.exists() else ""
            )
            audit_path.write_text(
                existing_audit
                + "".join(
                    json.dumps(item, ensure_ascii=False, separators=(",", ":"))
                    + "\n"
                    for item in deletion_audit
                ),
                encoding="utf-8",
            )

        for scene in scenes:
            scene["case_count"] = scene_counts[scene["scene_id"]]
        write_json(staging / "data" / "scenes.json", scenes)
        manifest["library_version"] = new_version
        manifest["case_count"] = len(cases_by_id)
        manifest["visible_case_count"] = sum(
            case.get("case_status") in VISIBLE_STATUSES
            for case in cases_by_id.values()
        )
        manifest["knowledge_sync_status"] = "not_verified"
        manifest["release_status"] = "artifact_ready_knowledge_pending"
        manifest["previous_version"] = current_version
        manifest["change_set_id"] = change_set.get("change_set_id")
        manifest["published_at"] = published_at
        write_json(staging / "data" / "manifest.json", manifest)

        html_path = staging / "exports" / "数据法学案例库.html"
        knowledge_path = staging / "exports" / "案例专家知识包.jsonl"
        html_report = render_library(staging, html_path)
        knowledge_report = build_knowledge_pack(staging, knowledge_path)
        candidate_errors = validate_release_root(staging, require_exports=True)
        with tempfile.TemporaryDirectory() as verification_tmp:
            verification_root = Path(verification_tmp)
            expected_html = verification_root / "数据法学案例库.html"
            expected_knowledge = verification_root / "案例专家知识包.jsonl"
            canonical_render_module.render_library(staging, expected_html)
            canonical_knowledge_module.build_knowledge_pack(
                staging, expected_knowledge
            )
            if expected_html.read_bytes() != html_path.read_bytes():
                candidate_errors.append("html_not_reproducible")
            if expected_knowledge.read_bytes() != knowledge_path.read_bytes():
                candidate_errors.append("knowledge_not_reproducible")
        if candidate_errors:
            raise ValueError(
                "candidate_release_invalid:" + ",".join(candidate_errors)
            )

        ensure_snapshot(library_root, current_release, current_version)
        staging.rename(final_release)
        release_created = True
        pointer_tmp = library_root / f".current-{new_version:04d}.json"
        write_json(
            pointer_tmp,
            {
                "release": final_release.name,
                "library_version": new_version,
                "knowledge_sync_status": "not_verified",
            },
        )
        os.replace(pointer_tmp, library_root / "current.json")
    except Exception:
        if pointer_tmp and pointer_tmp.exists():
            pointer_tmp.unlink()
        if staging.exists():
            shutil.rmtree(staging)
        if release_created and final_release.exists():
            shutil.rmtree(final_release)
        if transaction_path.exists():
            transaction_path.unlink()
        raise

    try:
        write_json(
            transaction_path,
            {
                "status": "applied",
                "change_set_id": stored_change_set_id,
                "base_version": current_version,
                "library_version": new_version,
                "release": final_release.name,
                "actor_reference": change_set.get("actor_reference"),
                "applied_at": published_at,
            },
        )
    except Exception as exc:
        return {
            "status": "published_confirmation_ledger_incomplete",
            "library_version": new_version,
            "release": final_release.name,
            "knowledge_sync_status": "not_verified",
            "ledger_error": str(exc),
        }

    return {
        "status": "artifact_ready_knowledge_pending",
        "library_version": new_version,
        "case_count": manifest["case_count"],
        "visible_case_count": manifest["visible_case_count"],
        "release": final_release.name,
        "html_path": str(final_release / "exports" / "数据法学案例库.html"),
        "knowledge_pack_path": str(
            final_release / "exports" / "案例专家知识包.jsonl"
        ),
        "html_case_count": html_report["case_count"],
        "knowledge_block_count": knowledge_report["block_count"],
        "knowledge_sync_status": "not_verified",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("library_root", type=Path)
    parser.add_argument("change_set_json", type=Path)
    parser.add_argument("--confirmed", action="store_true")
    parser.add_argument("--confirmation-change-set-id")
    args = parser.parse_args()
    try:
        change_set = json.loads(args.change_set_json.read_text(encoding="utf-8"))
        print(
            json.dumps(
                publish_update(
                    change_set,
                    args.confirmed,
                    args.library_root,
                    args.confirmation_change_set_id,
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
