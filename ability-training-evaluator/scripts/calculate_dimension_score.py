#!/usr/bin/env python3
"""Build a score object from teacher-configured dimensions and judgements."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


STANDARD_ALIASES = (
    "evaluation_standards",
    "evaluation_standard",
    "scoring_standard",
    "rubric",
)
DIMENSION_ALIASES = ("dimensions", "scoring_dimensions", "criteria")
INPUT_ID_ALIASES = ("dimensionId", "dimension_id", "itemId", "item_id")
JUDGEMENT_ID_ALIASES = ("itemId", "item_id", "dimensionId", "dimension_id")
FULL_ALIASES = (
    "full",
    "full_score",
    "full_mark",
    "fullMark",
    "dimensionFullMark",
    "score",
    "分值",
    "满分值",
)


def first(mapping: dict[str, Any], aliases: tuple[str, ...]) -> Any:
    for alias in aliases:
        if alias in mapping and mapping[alias] is not None:
            return mapping[alias]
    return None


def number(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be numeric")
    return float(value)


def tidy(value: float) -> int | float:
    return int(value) if value.is_integer() else round(value, 2)


def standards(payload: dict[str, Any]) -> dict[str, Any]:
    value = first(payload, STANDARD_ALIASES)
    if not isinstance(value, dict):
        raise ValueError("missing evaluation_standards")
    return value


def configured_dimensions(standard: dict[str, Any]) -> list[dict[str, Any]]:
    raw = first(standard, DIMENSION_ALIASES)
    if not isinstance(raw, list) or not raw:
        raise ValueError("evaluation_standards.dimensions must be a non-empty array")
    if len(raw) > 10:
        raise ValueError("evaluation_standards.dimensions cannot exceed 10 items")

    result = []
    seen_item_ids: set[str] = set()
    for index, item in enumerate(raw, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"dimension[{index}] must be an object")
        resolved_id = str(first(item, INPUT_ID_ALIASES) or "").strip()
        if not resolved_id:
            raise ValueError(
                f"dimension[{index}] requires dimensionId or itemId"
            )
        if resolved_id in seen_item_ids:
            raise ValueError(f"duplicate dimension/item id: {resolved_id}")
        seen_item_ids.add(resolved_id)
        name = str(item.get("name") or item.get("维度名称") or "").strip()
        if not name:
            raise ValueError(f"dimension[{index}].name is required")
        full = number(first(item, FULL_ALIASES), f"full for dimension[{index}]")
        if full <= 0:
            raise ValueError(f"full for dimension[{index}] must be greater than 0")
        description = str(
            item.get("description")
            or item.get("evaluation_description")
            or item.get("评价描述")
            or ""
        ).strip()
        requirements = str(
            item.get("detailed_requirements")
            or item.get("requirements")
            or item.get("scoring_rule")
            or item.get("评价项详细要求")
            or ""
        ).strip()
        if not description:
            raise ValueError(f"dimension[{index}].description is required")
        if not requirements:
            raise ValueError(f"dimension[{index}].detailed_requirements is required")
        result.append(
            {
                "resolvedDimensionId": resolved_id,
                "name": name,
                "full": full,
                "criteria": f"{description}；{requirements}",
            }
        )

    calculated_full = sum(item["full"] for item in result)
    declared_full = first(standard, ("full_score", "fullMark"))
    if declared_full is not None:
        declared = number(declared_full, "evaluation_standards.full_score")
        if abs(declared - calculated_full) > 1e-9:
            raise ValueError(
                "evaluation_standards.full_score must equal the sum of dimension full marks"
            )
    return result


def calculate(payload: dict[str, Any]) -> dict[str, Any]:
    dimensions_config = configured_dimensions(standards(payload))
    judgements = payload.get("dimension_judgements")
    if not isinstance(judgements, list):
        raise ValueError("dimension_judgements must be an array")

    by_id = {
        str(first(item, JUDGEMENT_ID_ALIASES)): item
        for item in judgements
        if isinstance(item, dict) and first(item, JUDGEMENT_ID_ALIASES) is not None
    }
    dimensions = []
    total = 0.0
    for item in dimensions_config:
        judgement = by_id.get(item["resolvedDimensionId"])
        if not isinstance(judgement, dict):
            raise ValueError(
                "missing judgement for dimensionId/itemId "
                f"{item['resolvedDimensionId']}: {item['name']}"
            )
        score = number(judgement.get("score"), f"score for {item['name']}")
        if score < 0 or score > item["full"]:
            raise ValueError(
                f"score for {item['name']} must be between 0 and {tidy(item['full'])}"
            )
        reason = str(judgement.get("reason") or "").strip()
        if not reason:
            raise ValueError(f"missing reason for dimension: {item['name']}")
        dimensions.append(
            {
                "dimensionId": item["resolvedDimensionId"],
                "dimensionName": item["name"],
                "dimensionFullMark": tidy(item["full"]),
                "dimensionCriteria": item["criteria"],
                "dimensionScore": tidy(score),
                "scoreReason": reason,
            }
        )
        total += score

    full_score = sum(item["full"] for item in dimensions_config)
    return {
        "scoring": {
            "scoringType": "DIMENSIONS",
            "totalScore": tidy(total),
            "scoreData": {
                "totalScore": tidy(total),
                "fullMark": tidy(full_score),
                "dimensions": dimensions,
            },
        }
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="JSON containing standards and judgements")
    parser.add_argument("-o", "--output", help="Optional output JSON file")
    args = parser.parse_args()
    try:
        payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("input must be a JSON object")
        text = json.dumps(calculate(payload), ensure_ascii=False, indent=2)
        if args.output:
            Path(args.output).write_text(text + "\n", encoding="utf-8")
        else:
            print(text)
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        print(f"calculate_dimension_score: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
