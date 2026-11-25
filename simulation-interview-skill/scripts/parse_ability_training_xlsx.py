#!/usr/bin/env python3
"""Parse ordinary ability-training XLSX records into the normalized input contract."""

from __future__ import annotations

import argparse
import json
import posixpath
import re
import sys
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any


MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
NS = {"m": MAIN_NS, "r": REL_NS, "p": PKG_NS}


def column_index(reference: str) -> int:
    match = re.match(r"[A-Z]+", reference)
    if not match:
        raise ValueError(f"invalid cell reference: {reference}")
    value = 0
    for letter in match.group():
        value = value * 26 + ord(letter) - 64
    return value - 1


def shared_strings(archive: zipfile.ZipFile) -> list[str]:
    try:
        root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
    except KeyError:
        return []
    return [
        "".join(node.text or "" for node in item.iterfind(".//m:t", NS))
        for item in root.findall("m:si", NS)
    ]


def workbook_sheets(archive: zipfile.ZipFile) -> dict[str, str]:
    workbook = ET.fromstring(archive.read("xl/workbook.xml"))
    rels = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    targets = {
        rel.attrib["Id"]: rel.attrib["Target"]
        for rel in rels.findall("p:Relationship", NS)
    }
    result = {}
    for sheet in workbook.findall("m:sheets/m:sheet", NS):
        target = targets[sheet.attrib[f"{{{REL_NS}}}id"]]
        result[sheet.attrib["name"]] = posixpath.normpath(
            posixpath.join("xl", target.lstrip("/"))
        )
    return result


def read_rows(
    archive: zipfile.ZipFile, path: str, shared: list[str]
) -> list[list[str]]:
    root = ET.fromstring(archive.read(path))
    rows: list[list[str]] = []
    for row in root.findall("m:sheetData/m:row", NS):
        values: dict[int, str] = {}
        for cell in row.findall("m:c", NS):
            reference = cell.attrib["r"]
            value_node = cell.find("m:v", NS)
            value = "" if value_node is None else value_node.text or ""
            if cell.attrib.get("t") == "s" and value:
                value = shared[int(value)]
            elif cell.attrib.get("t") == "inlineStr":
                value = "".join(
                    node.text or "" for node in cell.iterfind(".//m:t", NS)
                )
            values[column_index(reference)] = value
        width = max(values, default=-1) + 1
        rows.append([values.get(index, "") for index in range(width)])
    return rows


def records(rows: list[list[str]]) -> list[dict[str, str]]:
    if not rows:
        return []
    headers = rows[0]
    return [
        {
            header: row[index] if index < len(row) else ""
            for index, header in enumerate(headers)
            if header
        }
        for row in rows[1:]
        if any(row)
    ]


def parse(path: Path) -> dict[str, Any]:
    with zipfile.ZipFile(path) as archive:
        shared = shared_strings(archive)
        sheets = workbook_sheets(archive)
        required = {"阶段名称", "聊天记录"}
        missing = required - sheets.keys()
        if missing:
            raise ValueError(f"missing worksheets: {', '.join(sorted(missing))}")
        stage_records = records(read_rows(archive, sheets["阶段名称"], shared))
        chat_records = records(read_rows(archive, sheets["聊天记录"], shared))

    stages = [
        {
            "id": item.get("script_step_id", ""),
            "name": item.get("step_name", ""),
        }
        for item in stage_records
        if item.get("script_step_id")
    ]
    stage_names = {item["id"]: item["name"] for item in stages}

    dialogues = []
    stage_message_counts: Counter[str] = Counter()
    stage_user_counts: Counter[str] = Counter()
    seen_stage_ids = []
    for index, item in enumerate(chat_records, start=1):
        stage_id = item.get("step_Id") or ""
        role = item.get("role") or ""
        if stage_id and stage_id not in seen_stage_ids:
            seen_stage_ids.append(stage_id)
        stage_message_counts[stage_id] += 1
        if role == "user":
            stage_user_counts[stage_id] += 1
        dialogues.append(
            {
                "id": f"turn_{index}",
                "stage_id": stage_id,
                "stage_name": stage_names.get(stage_id, ""),
                "turn_index": index,
                "speaker_type": {
                    "user": "learner",
                    "assistant": "agent",
                }.get(role, role),
                "raw_role": role,
                "text": item.get("content") or "",
            }
        )

    stage_runs = [
        {
            "stage_id": stage_id,
            "stage_name": stage_names.get(stage_id, ""),
            "time": f"第{index}阶段",
            "sequence": index,
            "status": "observed",
            "message_count": stage_message_counts[stage_id],
            "learner_message_count": stage_user_counts[stage_id],
        }
        for index, stage_id in enumerate(seen_stage_ids, start=1)
    ]

    return {
        "training": {
            "name": path.stem,
            "version": "ordinary",
            "stages": stages,
        },
        "session": {
            "source_file": path.name,
            "stage_runs": stage_runs,
            "dialogues": dialogues,
            "quizzes": [],
            "interactions": [],
            "uploads": [],
            "media": [],
            "final_outputs": [],
            "role_selections": [],
            "skill_invocations": [],
        },
        "teacher_supplement": "",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="Ordinary ability-training XLSX file")
    parser.add_argument("-o", "--output", help="Optional output JSON file")
    args = parser.parse_args()
    try:
        output = json.dumps(
            parse(Path(args.input)), ensure_ascii=False, indent=2
        )
        if args.output:
            Path(args.output).write_text(output + "\n", encoding="utf-8")
        else:
            print(output)
    except (OSError, ValueError, KeyError, zipfile.BadZipFile, ET.ParseError) as exc:
        print(f"parse_ability_training_xlsx: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
