#!/usr/bin/env python3
"""从结构化案例主数据确定性生成单文件离线 HTML。"""

from __future__ import annotations

import argparse
from html import escape
import json
from pathlib import Path
import sys
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
TEMPLATE_PATH = SCRIPT_DIR / "templates" / "case-library.html"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from library_core import resolve_active_root  # noqa: E402


RECORD_TYPE_LABELS = {
    "judicial_case": "司法裁判",
    "administrative_enforcement": "行政执法",
    "regulatory_event": "监管事件",
    "compliance_event": "合规事件",
    "security_incident": "安全事件",
    "pending_dispute": "未决争议",
    "research_material": "研究材料",
    "unclassified": "待分类",
}
STUDENT_VISIBLE_STATUSES = {"已发布"}


def safe_json_for_script(value: Any) -> str:
    """把 JSON 安全嵌入 application/json 脚本节点。"""

    return (
        json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )


def load_library(library_root: Path) -> dict[str, Any]:
    data_root = resolve_active_root(Path(library_root)) / "data"
    scenes = json.loads((data_root / "scenes.json").read_text(encoding="utf-8"))
    manifest = json.loads((data_root / "manifest.json").read_text(encoding="utf-8"))
    cases = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted((data_root / "cases").glob("DLCL-*.json"))
    ]
    if manifest["scene_count"] != len(scenes):
        raise ValueError("manifest_scene_count_mismatch")
    if manifest["case_count"] != len(cases):
        raise ValueError("manifest_case_count_mismatch")
    return {"manifest": manifest, "scenes": scenes, "cases": cases}


def render_scene_cards(scenes: list[dict[str, Any]]) -> str:
    cards: list[str] = []
    for scene in scenes:
        cards.append(
            """
            <button class="scene-card" type="button" data-scene-filter="{scene_id}">
              <span class="scene-number">{order:02d}</span>
              <span class="scene-copy">
                <strong>{name}</strong>
                <small>{count} 个案例</small>
              </span>
              <span aria-hidden="true" class="scene-arrow">↗</span>
            </button>
            """.format(
                scene_id=escape(scene["scene_id"], quote=True),
                order=int(scene["order"]),
                name=escape(scene["name"]),
                count=int(scene["case_count"]),
            ).strip()
        )
    return "\n".join(cards)


def render_case_rows(
    cases: list[dict[str, Any]], scenes_by_id: dict[str, dict[str, Any]]
) -> str:
    rows: list[str] = []
    for case in cases:
        scene = scenes_by_id[case["scene_id"]]
        search_text = " ".join(
            [
                case["title"],
                scene["name"],
                case.get("basic_facts") or "",
                " ".join(
                    item.get("citation_text", "")
                    for item in case.get("legal_provisions", [])
                ),
            ]
        )
        rows.append(
            """
            <article class="case-row" data-case-id="{case_id}" data-scene="{scene_id}" data-search="{search_text}">
              <button class="case-open" type="button" aria-label="查看案例：{title}" data-open-case="{case_id}">
                <span class="case-id">{case_id}</span>
                <span class="case-title">{title}</span>
                <span class="case-type">{record_type}</span>
                <span class="case-status">{evidence_status}</span>
                <span aria-hidden="true" class="case-arrow">→</span>
              </button>
            </article>
            """.format(
                case_id=escape(case["case_id"], quote=True),
                scene_id=escape(case["scene_id"], quote=True),
                search_text=escape(search_text.casefold(), quote=True),
                title=escape(case["title"]),
                record_type=escape(
                    RECORD_TYPE_LABELS.get(
                        case.get("record_type", "unclassified"),
                        case.get("record_type", "unclassified"),
                    )
                ),
                evidence_status=escape(case.get("evidence_status", "待补证")),
            ).strip()
        )
    return "\n".join(rows)


def render_library(library_root: Path, output_html: Path) -> dict[str, Any]:
    library = load_library(Path(library_root))
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    manifest = library["manifest"]
    scenes = library["scenes"]
    cases = [
        case
        for case in library["cases"]
        if case.get("case_status") in STUDENT_VISIBLE_STATUSES
    ]
    scenes_by_id = {scene["scene_id"]: scene for scene in scenes}
    payload = {
        "manifest": manifest,
        "scenes": scenes,
        "cases": cases,
    }
    html = (
        template.replace("{{LIBRARY_VERSION}}", escape(str(manifest["library_version"])))
        .replace("{{SCENE_COUNT}}", str(len(scenes)))
        .replace("{{CASE_COUNT}}", str(len(cases)))
        .replace("{{SCENE_CARDS}}", render_scene_cards(scenes))
        .replace("{{CASE_ROWS}}", render_case_rows(cases, scenes_by_id))
        .replace("{{CASE_DATA}}", safe_json_for_script(payload))
    )
    output_html = Path(output_html)
    output_html.parent.mkdir(parents=True, exist_ok=True)
    output_html.write_text(html, encoding="utf-8")
    return {
        "status": "artifact_ready",
        "scene_count": len(scenes),
        "case_count": len(cases),
        "library_version": manifest["library_version"],
        "output_html": str(output_html),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("library_root", type=Path)
    parser.add_argument("output_html", type=Path)
    args = parser.parse_args()
    try:
        print(
            json.dumps(
                render_library(args.library_root, args.output_html),
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
