#!/usr/bin/env python3
"""Optionally parse DOCX inputs; other formats are handled by platform extraction."""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import Any


WORD_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": WORD_NS}


def docx_lines(path: Path) -> list[str]:
    try:
        with zipfile.ZipFile(path) as archive:
            root = ET.fromstring(archive.read("word/document.xml"))
    except (KeyError, zipfile.BadZipFile, ET.ParseError) as exc:
        raise ValueError(f"cannot read Word document {path.name}: {exc}") from exc

    lines: list[str] = []
    for paragraph in root.findall(".//w:p", NS):
        text = "".join(node.text or "" for node in paragraph.findall(".//w:t", NS))
        text = text.strip()
        if text:
            lines.append(text)
    return lines


HEADING_RE = re.compile(
    r"^(?:#{1,4}\s*)?(?:\d+[.、]\s*)?(?P<name>.+?)\s*"
    r"[（(]\s*满分\s*[：:]\s*(?P<full>\d+(?:\.\d+)?)\s*分?\s*[）)]\s*$"
)
ID_RE = re.compile(r"(?:dimensionId|itemId)\s*[：:]\s*([A-Za-z0-9_-]+)", re.I)
DETAIL_RE = re.compile(r"(?:详细要求|评价项详细要求)\s*[：:]\s*(.+)")


def parse_rubric(lines: list[str]) -> dict[str, Any]:
    dimensions: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    description_lines: list[str] = []

    def finish() -> None:
        nonlocal current, description_lines
        if current is None:
            return
        current["description"] = " ".join(description_lines).strip()
        missing = [
            key
            for key in ("itemId", "name", "full", "description", "detailed_requirements")
            if not current.get(key)
        ]
        if missing:
            raise ValueError(
                f"rubric dimension {current.get('name') or len(dimensions) + 1} "
                f"missing: {', '.join(missing)}"
            )
        dimensions.append(current)
        current = None
        description_lines = []

    for raw in lines:
        line = raw.lstrip("- ").strip()
        heading = HEADING_RE.match(line)
        if heading:
            finish()
            full = float(heading.group("full"))
            current = {
                "name": heading.group("name").strip(),
                "full": int(full) if full.is_integer() else full,
            }
            continue
        if current is None:
            continue
        id_match = ID_RE.search(line)
        if id_match:
            current["itemId"] = id_match.group(1)
            continue
        detail_match = DETAIL_RE.search(line)
        if detail_match:
            current["detailed_requirements"] = detail_match.group(1).strip()
            continue
        if line not in {"描述内容", "评价描述"}:
            description_lines.append(line)
    finish()

    if not dimensions:
        raise ValueError("teacher Word contains no recognizable rubric dimensions")
    ids = [item["itemId"] for item in dimensions]
    if len(ids) != len(set(ids)):
        raise ValueError("teacher Word contains duplicate itemId values")
    return {"dimensions": dimensions}


STAGE_RE = re.compile(r"^(?:#{1,4}\s*)?阶段\s*(\d+)?\s*[：:]?\s*(.+)$")
DIALOGUE_RE = re.compile(r"^([^：:]{1,40})[：:]\s*[\"“]?(.*?)[\"”]?$", re.S)


def parse_training_record(lines: list[str]) -> dict[str, Any]:
    stage_runs: list[dict[str, Any]] = []
    dialogues: list[dict[str, Any]] = []
    stage_id = "stage_1"
    stage_name = "训练记录"

    for line in lines:
        stage = STAGE_RE.match(line)
        if stage:
            sequence = len(stage_runs) + 1
            stage_id = f"stage_{stage.group(1) or sequence}"
            stage_name = stage.group(2).strip()
            stage_runs.append(
                {
                    "stageId": stage_id,
                    "stageName": stage_name,
                    "time": f"第{sequence}阶段",
                    "sequence": sequence,
                }
            )
            continue
        dialogue = DIALOGUE_RE.match(line)
        if not dialogue:
            continue
        speaker = dialogue.group(1).strip()
        text = dialogue.group(2).strip()
        if not text or speaker in {"itemId", "dimensionId", "详细要求", "满分"}:
            continue
        lowered = speaker.lower()
        is_agent = any(token in lowered for token in ("bot", "agent", "assistant", "智能体"))
        is_student = any(token in lowered for token in ("student", "user", "学生", "学员", "用户", "testshen"))
        if not (is_agent or is_student):
            continue
        dialogues.append(
            {
                "id": f"turn_{len(dialogues) + 1}",
                "stage_id": stage_id,
                "stage_name": stage_name,
                "turn_index": len(dialogues) + 1,
                "speaker": speaker,
                "speaker_type": "agent" if is_agent else "learner",
                "text": text,
            }
        )

    if not dialogues:
        raise ValueError("student Word contains no recognizable dialogue records")
    if not stage_runs:
        stage_runs.append(
            {"stageId": stage_id, "stageName": stage_name, "time": "第1阶段", "sequence": 1}
        )
    return {"stage_runs": stage_runs, "dialogues": dialogues}


def parse(teacher_word: Path, student_word: Path) -> dict[str, Any]:
    return {
        "evaluation_standards": parse_rubric(docx_lines(teacher_word)),
        "training": {"source": student_word.name},
        "session": {
            **parse_training_record(docx_lines(student_word)),
            "quizzes": [],
            "interactions": [],
            "uploads": [],
            "media": [],
            "final_outputs": [],
            "role_selections": [],
            "skill_invocations": [],
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("teacher_word", help="Teacher rubric DOCX from assignment requirements")
    parser.add_argument("student_word", help="Student training-record DOCX from submission")
    parser.add_argument("-o", "--output", help="Optional output JSON file")
    args = parser.parse_args()
    try:
        result = parse(Path(args.teacher_word), Path(args.student_word))
        text = json.dumps(result, ensure_ascii=False, indent=2)
        if args.output:
            Path(args.output).write_text(text + "\n", encoding="utf-8")
        else:
            print(text)
    except (OSError, ValueError) as exc:
        print(f"parse_docx_inputs: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
