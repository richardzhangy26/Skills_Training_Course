"""脱敏 JSON 与 Markdown 回归报告。"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any, Mapping

from .fixtures import validate_run_id
from .private_io import write_private_bytes_atomic
from .safety import sanitize_json


sanitize_report = sanitize_json


@dataclass(frozen=True)
class ReportPaths:
    json: Path
    markdown: Path


class ReportWriter:
    def __init__(self, root: Path):
        self.root = Path(root)

    def write(self, payload: Mapping[str, Any]) -> ReportPaths:
        run_id = validate_run_id(str(payload.get("run_id", "")))
        safe = sanitize_report(payload)
        self.root.mkdir(parents=True, exist_ok=True)
        json_path = self.root / f"{run_id}.json"
        markdown_path = self.root / f"{run_id}.md"
        json_text = json.dumps(safe, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        environment = safe.get("environment", "unknown")
        status = safe.get("status", "unknown")
        markdown = (
            f"# Online E2E 报告 {run_id}\n\n"
            f"- environment: `{environment}`\n"
            f"- status: `{status}`\n\n"
            "## 脱敏结果\n\n"
            "```json\n"
            f"{json_text}```\n"
        )
        write_private_bytes_atomic(json_path, json_text.encode("utf-8"))
        write_private_bytes_atomic(markdown_path, markdown.encode("utf-8"))
        return ReportPaths(json=json_path, markdown=markdown_path)
