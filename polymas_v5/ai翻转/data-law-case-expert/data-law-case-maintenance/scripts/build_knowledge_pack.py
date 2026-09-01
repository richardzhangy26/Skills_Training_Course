#!/usr/bin/env python3
"""把案例主数据生成一案例一知识块的 JSONL。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from library_core import build_knowledge_block, resolve_active_root  # noqa: E402


STUDENT_VISIBLE_STATUSES = {"已发布"}


def load_library(library_root: Path) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    data_root = resolve_active_root(Path(library_root)) / "data"
    manifest = json.loads((data_root / "manifest.json").read_text(encoding="utf-8"))
    scenes = json.loads((data_root / "scenes.json").read_text(encoding="utf-8"))
    cases = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted((data_root / "cases").glob("DLCL-*.json"))
    ]
    return manifest, {scene["scene_id"]: scene for scene in scenes}, cases


def build_knowledge_pack(library_root: Path, output_path: Path) -> dict[str, Any]:
    manifest, scenes, cases = load_library(Path(library_root))
    blocks = [
        build_knowledge_block(case, scenes[case["scene_id"]])
        for case in cases
        if case.get("case_status") in STUDENT_VISIBLE_STATUSES
    ]
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        "".join(
            json.dumps(block, ensure_ascii=False, separators=(",", ":")) + "\n"
            for block in blocks
        ),
        encoding="utf-8",
    )
    return {
        "status": "artifact_ready_knowledge_pending",
        "library_version": manifest["library_version"],
        "block_count": len(blocks),
        "output_path": str(output_path),
        "knowledge_sync_status": "not_verified",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("library_root", type=Path)
    parser.add_argument("output_path", type=Path)
    args = parser.parse_args()
    try:
        print(
            json.dumps(
                build_knowledge_pack(args.library_root, args.output_path),
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
