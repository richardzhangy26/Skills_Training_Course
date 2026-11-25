#!/usr/bin/env python3
"""Normalize an ability-training record without inventing missing evidence."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


LIST_FIELDS = (
    "stage_runs",
    "dialogues",
    "quizzes",
    "interactions",
    "uploads",
    "media",
    "final_outputs",
    "role_selections",
    "skill_invocations",
)

STANDARD_ALIASES = (
    "evaluation_standards",
    "evaluation_standard",
    "scoring_standard",
    "rubric",
)


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def first(mapping: dict[str, Any], aliases: tuple[str, ...]) -> Any:
    for alias in aliases:
        if alias in mapping and mapping[alias] is not None:
            return mapping[alias]
    return None


def normalize(payload: dict[str, Any]) -> dict[str, Any]:
    training = payload.get("training") or payload.get("ability_training") or {}
    if not isinstance(training, dict):
        raise ValueError("training must be an object")
    evaluation_standards = first(payload, STANDARD_ALIASES) or first(
        training, STANDARD_ALIASES
    )
    if evaluation_standards is None:
        evaluation_standards = {}
    if not isinstance(evaluation_standards, dict):
        raise ValueError("evaluation_standards must be an object")

    session = payload.get("session") or payload.get("training_session") or {}
    if not isinstance(session, dict):
        raise ValueError("session must be an object")
    normalized_session = dict(session)

    raw_dialogues = (
        normalized_session.get("dialogues")
        or payload.get("chat_records")
        or payload.get("messages")
        or []
    )
    dialogues = []
    for index, item in enumerate(as_list(raw_dialogues), start=1):
        if not isinstance(item, dict):
            continue
        raw_role = item.get("role") or item.get("speaker_type")
        speaker_type = {
            "user": "learner",
            "assistant": "agent",
        }.get(raw_role, raw_role)
        dialogues.append(
            {
                **item,
                "id": item.get("id") or f"turn_{index}",
                "stage_id": item.get("stage_id") or item.get("step_Id"),
                "turn_index": item.get("turn_index") or index,
                "speaker_type": speaker_type,
                "text": item.get("text") or item.get("content") or "",
            }
        )
    normalized_session["dialogues"] = dialogues

    for field in LIST_FIELDS:
        if field == "dialogues":
            continue
        normalized_session[field] = as_list(normalized_session.get(field))
    normalized_session["role_selections"] = as_list(
        normalized_session.get("role_selections")
        or payload.get("role_selections")
        or payload.get("selected_role")
    )
    normalized_session["skill_invocations"] = as_list(
        normalized_session.get("skill_invocations")
        or payload.get("skill_invocations")
    )
    raw_stage_runs = as_list(
        normalized_session.get("stage_runs") or payload.get("stage_runs")
    )
    stage_runs = []
    for index, item in enumerate(raw_stage_runs, start=1):
        if not isinstance(item, dict):
            continue
        stage_id = first(
            item, ("stageId", "stage_id", "script_step_id", "step_Id", "id")
        )
        stage_name = first(
            item, ("stageName", "stage_name", "step_name", "name")
        )
        stage_time = first(
            item, ("time", "timestamp", "startTime", "start_time")
        )
        stage_runs.append(
            {
                **item,
                "stageId": stage_id,
                "stageName": stage_name,
                "time": str(stage_time).strip() if stage_time else f"第{index}阶段",
            }
        )
    normalized_session["stage_runs"] = stage_runs
    normalized_session["quizzes"] = as_list(
        normalized_session.get("quizzes") or payload.get("quizzes")
    )
    normalized_session["uploads"] = as_list(
        normalized_session.get("uploads") or payload.get("uploads")
    )
    return {
        "evaluation_standards": evaluation_standards,
        "training": training,
        "session": normalized_session,
        "teacher_supplement": payload.get("teacher_supplement") or "",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="Input JSON file")
    parser.add_argument("-o", "--output", help="Optional output JSON file")
    args = parser.parse_args()
    try:
        payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("input must be a JSON object")
        text = json.dumps(normalize(payload), ensure_ascii=False, indent=2)
        if args.output:
            Path(args.output).write_text(text + "\n", encoding="utf-8")
        else:
            print(text)
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        print(f"normalize_training_record: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
