#!/usr/bin/env python3
"""经确认后把案例库当前指针切换到已存在的历史版本。"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import fcntl
import json
import os
from pathlib import Path
import sys
import tempfile
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from library_core import read_json, validate_release_root, write_json  # noqa: E402
from build_knowledge_pack import build_knowledge_pack  # noqa: E402
from prepare_update import resolve_release  # noqa: E402
from render_html import render_library  # noqa: E402


def release_digest(release: Path) -> str:
    digest = hashlib.sha256()
    paths = sorted(
        [
            path
            for folder in (release / "data", release / "exports")
            if folder.is_dir()
            for path in folder.rglob("*")
            if path.is_file()
        ],
        key=lambda path: path.relative_to(release).as_posix(),
    )
    for path in paths:
        relative = path.relative_to(release).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def prepare_rollback(
    library_root: Path,
    target_version: int,
    actor_reference: str | None = None,
    confirmation_nonce: str | None = None,
) -> dict[str, Any]:
    library_root = Path(library_root)
    if not actor_reference:
        return {"status": "audit_context_required", "target_version": target_version}
    target = library_root / "releases" / f"v{target_version:04d}"
    manifest_path = target / "data" / "manifest.json"
    if not manifest_path.is_file():
        return {"status": "target_version_not_found", "target_version": target_version}
    required = (
        target / "data" / "scenes.json",
        target / "exports" / "数据法学案例库.html",
        target / "exports" / "案例专家知识包.jsonl",
    )
    missing = [path.name for path in required if not path.is_file()]
    if missing or not (target / "data" / "cases").is_dir():
        return {
            "status": "target_artifact_missing",
            "target_version": target_version,
            "missing": missing or ["cases"],
        }
    manifest = read_json(manifest_path)
    if int(manifest.get("library_version", -1)) != target_version:
        return {"status": "target_version_invalid", "target_version": target_version}
    release_errors = validate_release_root(target, require_exports=True)
    if not release_errors:
        with tempfile.TemporaryDirectory() as tmp:
            temporary = Path(tmp)
            expected_html = temporary / "数据法学案例库.html"
            expected_knowledge = temporary / "案例专家知识包.jsonl"
            render_library(target, expected_html)
            build_knowledge_pack(target, expected_knowledge)
            if expected_html.read_bytes() != (
                target / "exports" / "数据法学案例库.html"
            ).read_bytes():
                release_errors.append("html_not_reproducible")
            if expected_knowledge.read_bytes() != (
                target / "exports" / "案例专家知识包.jsonl"
            ).read_bytes():
                release_errors.append("knowledge_not_reproducible")
    if release_errors:
        return {
            "status": "target_release_invalid",
            "target_version": target_version,
            "errors": release_errors,
        }
    current = resolve_release(library_root)
    current_manifest = read_json(current / "data" / "manifest.json")
    payload = {
        "from_release": current.name,
        "from_version": current_manifest["library_version"],
        "to_release": target.name,
        "to_version": target_version,
        "target_digest": release_digest(target),
        "actor_reference": actor_reference,
        "confirmation_nonce": confirmation_nonce,
    }
    rollback_confirmation_id = hashlib.sha256(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()[:16]
    return {
        "status": "preview_ready",
        "rollback_confirmation_id": rollback_confirmation_id,
        **payload,
    }


def rollback_release(
    library_root: Path,
    target_version: int,
    confirmed: bool,
    confirmation_rollback_id: str | None = None,
    actor_reference: str | None = None,
    confirmation_nonce: str | None = None,
    _lock_held: bool = False,
) -> dict[str, Any]:
    library_root = Path(library_root)
    if confirmed and not _lock_held:
        library_root.mkdir(parents=True, exist_ok=True)
        with (library_root / ".publish.lock").open("a+", encoding="utf-8") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            return rollback_release(
                library_root,
                target_version,
                confirmed,
                confirmation_rollback_id,
                actor_reference,
                confirmation_nonce,
                _lock_held=True,
            )
    plan = prepare_rollback(
        library_root, target_version, actor_reference, confirmation_nonce
    )
    if plan["status"] != "preview_ready":
        return plan
    if not confirmed:
        return {
            "status": "awaiting_confirmation",
            "target_version": target_version,
            "rollback_confirmation_id": plan["rollback_confirmation_id"],
        }
    if confirmation_rollback_id != plan["rollback_confirmation_id"]:
        return {
            "status": "confirmation_mismatch",
            "target_version": target_version,
        }
    target = library_root / "releases" / f"v{target_version:04d}"
    manifest_path = target / "data" / "manifest.json"
    manifest = read_json(manifest_path)

    current = resolve_release(library_root)
    current_manifest = read_json(current / "data" / "manifest.json")
    transaction_dir = library_root / "rollback-transactions"
    pending_path = transaction_dir / f"{confirmation_rollback_id}.pending.json"
    complete_path = transaction_dir / f"{confirmation_rollback_id}.complete.json"
    if pending_path.exists() or complete_path.exists():
        return {
            "status": "confirmation_already_used",
            "target_version": target_version,
        }
    transaction = {
        "status": "pending",
        "from_version": current_manifest["library_version"],
        "to_version": target_version,
        "requested_at": datetime.now(timezone.utc).isoformat(),
        "actor_reference": actor_reference,
        "rollback_confirmation_id": confirmation_rollback_id,
        "knowledge_sync_status": "not_verified",
    }
    try:
        transaction_dir.mkdir(parents=True, exist_ok=True)
        write_json(pending_path, transaction)
    except Exception as exc:
        return {
            "status": "audit_write_failed",
            "target_version": target_version,
            "error": str(exc),
        }
    pointer_tmp = library_root / f".rollback-current-{target_version:04d}.json"
    try:
        write_json(
            pointer_tmp,
            {
                "release": target.name,
                "library_version": target_version,
                "knowledge_sync_status": "not_verified",
            },
        )
        os.replace(pointer_tmp, library_root / "current.json")
    except Exception as exc:
        if pointer_tmp.exists():
            pointer_tmp.unlink()
        transaction["status"] = "pointer_switch_failed"
        transaction["error"] = str(exc)
        try:
            write_json(pending_path, transaction)
        except Exception:
            pass
        return {
            "status": "pointer_switch_failed",
            "target_version": target_version,
            "current_version": current_manifest["library_version"],
            "error": str(exc),
        }

    transaction["status"] = "applied"
    transaction["applied_at"] = datetime.now(timezone.utc).isoformat()
    completion_tmp = transaction_dir / f".{confirmation_rollback_id}.complete.json"
    try:
        write_json(completion_tmp, transaction)
        os.replace(completion_tmp, complete_path)
        pending_path.unlink()
    except Exception as exc:
        if completion_tmp.exists():
            completion_tmp.unlink()
        return {
            "status": "rollback_applied_audit_incomplete",
            "library_version": target_version,
            "release": target.name,
            "knowledge_sync_status": "not_verified",
            "audit_error": str(exc),
        }
    return {
        "status": "artifact_ready_knowledge_pending",
        "library_version": target_version,
        "case_count": manifest["case_count"],
        "release": target.name,
        "html_path": str(target / "exports" / "数据法学案例库.html"),
        "knowledge_pack_path": str(target / "exports" / "案例专家知识包.jsonl"),
        "knowledge_sync_status": "not_verified",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("library_root", type=Path)
    parser.add_argument("target_version", type=int)
    parser.add_argument("--confirmed", action="store_true")
    parser.add_argument("--confirmation-rollback-id")
    parser.add_argument("--actor-reference")
    parser.add_argument("--confirmation-nonce")
    args = parser.parse_args()
    try:
        print(
            json.dumps(
                rollback_release(
                    args.library_root,
                    args.target_version,
                    args.confirmed,
                    args.confirmation_rollback_id,
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
