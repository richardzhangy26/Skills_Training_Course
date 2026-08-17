"""Safely update the three remote-sensing ability-training tasks.

The module separates pure payload construction from live API mutation so every
change can be preflighted, diffed, and backed up before it is applied.
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import re
import sys
import uuid
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import requests


if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


DIGITAL_HUMAN_ID = "qqg4vg3DwY"
DIGITAL_HUMAN_NAME = "星航"
VOICE_ID = "Tg9LpKo68D"
VOICE_PARAM = "zh_male_tiancaitongsheng_mars_bigtts"
AVATAR_ID = "Pzd7n2rwRc"
TRANSITION_HISTORY_NUM = 10


class PreflightError(RuntimeError):
    """Raised when the live task no longer matches the expected safe shape."""


@dataclass(frozen=True)
class LinearChain:
    start: dict[str, Any]
    business_steps: list[dict[str, Any]]
    end: dict[str, Any]
    flows: list[dict[str, Any]]


def _node_type(step: dict[str, Any]) -> str:
    return str(step.get("stepDetailDTO", {}).get("nodeType", ""))


def _resource_groups_for_write(
    resources: list[dict[str, Any]],
    *,
    train_task_id: str,
    step_id: str,
) -> list[dict[str, Any]]:
    """Convert read rows into the editor's required stepExtProperty shape."""
    groups: dict[tuple[str, str], dict[str, Any]] = {}
    order: list[tuple[str, str]] = []
    for resource in resources:
        resource_type = str(
            resource.get("resourceTypeNid")
            or resource.get("nid")
            or "default"
        )
        category = str(resource.get("category") or "未分类")
        key = (resource_type, category)
        if key not in groups:
            groups[key] = {
                "nid": resource_type,
                "category": category,
                "list": [],
            }
            order.append(key)
        groups[key]["list"].append(
            {
                "type": resource.get("type", "resource"),
                "fileId": resource.get("fileId"),
                "fileName": resource.get("fileName"),
                "thumbnail": resource.get("thumbnail", ""),
                "fileUrl": resource.get("fileUrl"),
                "isRequired": bool(resource.get("isRequired")),
                "description": resource.get("description", ""),
                "trainTaskId": train_task_id,
                "scriptStepId": step_id,
                "sort": resource.get("sort"),
                "scriptStepResourceId": uuid.uuid4().hex[:20],
            }
        )
    return [groups[key] for key in order]


def _apply_resource_write_shape(
    detail: dict[str, Any],
    resources: list[dict[str, Any]],
    *,
    train_task_id: str,
    step_id: str,
) -> None:
    for resource in resources:
        resource["trainTaskId"] = train_task_id
        resource["scriptStepId"] = step_id
        resource.pop("scriptStepResourceId", None)
    detail["scriptStepResourceList"] = resources
    ext = copy.deepcopy(detail.get("stepExtProperty") or {})
    ext["resources"] = _resource_groups_for_write(
        resources,
        train_task_id=train_task_id,
        step_id=step_id,
    )
    detail["stepExtProperty"] = ext


def linearize_snapshot(snapshot: dict[str, Any]) -> LinearChain:
    """Return a verified START -> business nodes -> END linear chain."""
    steps = snapshot.get("steps") or []
    flows = snapshot.get("flows") or []
    starts = [step for step in steps if _node_type(step) == "SCRIPT_START"]
    ends = [step for step in steps if _node_type(step) == "SCRIPT_END"]
    if len(starts) != 1 or len(ends) != 1:
        raise PreflightError("任务必须恰好包含一个START和一个END节点")

    by_id = {step.get("stepId"): step for step in steps if step.get("stepId")}
    outgoing: dict[str, list[dict[str, Any]]] = {}
    for flow in flows:
        outgoing.setdefault(str(flow.get("scriptStepStartId")), []).append(flow)

    ordered_steps: list[dict[str, Any]] = []
    ordered_flows: list[dict[str, Any]] = []
    seen: set[str] = set()
    current_id = str(starts[0]["stepId"])
    end_id = str(ends[0]["stepId"])

    while current_id != end_id:
        if current_id in seen:
            raise PreflightError("任务流程不是无环线性结构")
        seen.add(current_id)
        next_flows = outgoing.get(current_id, [])
        if len(next_flows) != 1:
            raise PreflightError("任务流程不是单一路径的线性结构")
        flow = next_flows[0]
        ordered_flows.append(flow)
        next_id = str(flow.get("scriptStepEndId"))
        if next_id not in by_id:
            raise PreflightError(f"流程指向不存在的节点：{next_id}")
        if next_id != end_id:
            if _node_type(by_id[next_id]) != "SCRIPT_NODE":
                raise PreflightError("线性流程中出现非业务节点")
            ordered_steps.append(by_id[next_id])
        current_id = next_id

    business_ids = {
        str(step.get("stepId"))
        for step in steps
        if _node_type(step) == "SCRIPT_NODE"
    }
    if {str(step["stepId"]) for step in ordered_steps} != business_ids:
        raise PreflightError("任务存在未纳入线性链的业务节点")
    if len(ordered_flows) != len(ordered_steps) + 1:
        raise PreflightError("任务流程边数量与线性节点数量不一致")

    return LinearChain(
        start=starts[0],
        business_steps=ordered_steps,
        end=ends[0],
        flows=ordered_flows,
    )


def build_step_payload(
    existing_step: dict[str, Any],
    markdown_step: dict[str, Any],
    *,
    train_task_id: str,
    resource_renames: dict[str, str] | None = None,
    excluded_file_ids: set[str] | None = None,
    allowed_resource_names: set[str] | None = None,
    required_resource_names: set[str] | None = None,
    resource_priority: list[str] | None = None,
    additional_resources: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Merge reviewed Markdown content into a full, metadata-preserving step."""
    target = copy.deepcopy(existing_step)
    detail = target.setdefault("stepDetailDTO", {})
    target["trainTaskId"] = train_task_id

    field_map = {
        "stepName": "stepName",
        "description": "description",
        "interactiveRounds": "interactiveRounds",
        "prologue": "prologue",
        "llmPrompt": "llmPrompt",
    }
    for markdown_field, platform_field in field_map.items():
        if markdown_field in markdown_step:
            detail[platform_field] = markdown_step[markdown_field]

    detail["trainerName"] = DIGITAL_HUMAN_NAME
    detail["agentId"] = VOICE_ID
    detail["agentVoiceId"] = VOICE_PARAM
    detail["avatarNid"] = AVATAR_ID
    detail["customDigitalHuman"] = DIGITAL_HUMAN_ID
    detail["isSkipStep"] = "0"

    renames = resource_renames or {}
    required = required_resource_names or set()
    priority = {
        name: index for index, name in enumerate(resource_priority or [])
    }
    resources = []
    for resource in detail.get("scriptStepResourceList") or []:
        if not resource.get("fileId"):
            continue
        if (
            excluded_file_ids is not None
            and str(resource.get("fileId")) in excluded_file_ids
        ):
            continue
        item = copy.deepcopy(resource)
        old_name = str(item.get("fileName") or "")
        item["fileName"] = renames.get(old_name, old_name)
        if (
            allowed_resource_names is not None
            and item["fileName"] not in allowed_resource_names
        ):
            continue
        item["isRequired"] = 1 if item["fileName"] in required else 0
        resources.append(item)
    seen_file_ids = {str(item.get("fileId")) for item in resources}
    seen_names = {str(item.get("fileName")) for item in resources}
    for resource in additional_resources or []:
        item = copy.deepcopy(resource)
        file_id = str(item.get("fileId") or "")
        file_name = renames.get(
            str(item.get("fileName") or ""),
            str(item.get("fileName") or ""),
        )
        if not file_id or not file_name:
            raise PreflightError("新增资源必须包含fileId和fileName")
        if file_id in seen_file_ids or file_name in seen_names:
            continue
        if (
            allowed_resource_names is not None
            and file_name not in allowed_resource_names
        ):
            continue
        item["fileName"] = file_name
        item["trainTaskId"] = train_task_id
        item["scriptStepId"] = target.get("stepId")
        item.setdefault("type", "resource")
        item.setdefault("category", "未分类")
        item.setdefault("resourceTypeNid", "jyk1f7wR5e")
        item.setdefault("description", "")
        item.setdefault("thumbnail", item.get("fileUrl"))
        item.setdefault("studied", None)
        item["isRequired"] = 1 if file_name in required else 0
        resources.append(item)
        seen_file_ids.add(file_id)
        seen_names.add(file_name)
    resources.sort(
        key=lambda item: (
            priority.get(str(item.get("fileName") or ""), len(priority) + 1),
            int(item.get("sort") or 10_000),
        )
    )
    for index, resource in enumerate(resources, start=1):
        resource["sort"] = index
    _apply_resource_write_shape(
        detail,
        resources,
        train_task_id=train_task_id,
        step_id=str(target.get("stepId") or ""),
    )
    return target


def build_flow_payload(
    existing_flow: dict[str, Any],
    *,
    train_task_id: str,
    condition: str,
    transition_prompt: str,
    start_id: str | None = None,
    end_id: str | None = None,
) -> dict[str, Any]:
    """Update one existing linear flow without changing its topology."""
    target = copy.deepcopy(existing_flow)
    target["trainTaskId"] = train_task_id
    if start_id is not None:
        target["scriptStepStartId"] = start_id
        target["scriptStepStartHandle"] = f"{start_id}-source-bottom"
    if end_id is not None:
        target["scriptStepEndId"] = end_id
        target["scriptStepEndHandle"] = f"{end_id}-target-top"
    target["flowCondition"] = condition
    try:
        nested = target["flowConfiguration"]["conditions"][0]["conditions"]
    except (KeyError, IndexError, TypeError) as exc:
        raise PreflightError("流程条件结构已变化，拒绝覆盖") from exc
    if len(nested) != 1:
        raise PreflightError("流程条件不是单条件线性结构，拒绝覆盖")
    nested[0]["text"] = condition
    target["transitionPrompt"] = transition_prompt
    target["transitionHistoryNum"] = TRANSITION_HISTORY_NUM
    return target


def build_new_flow_payload(
    *,
    train_task_id: str,
    flow_id: str,
    start_id: str,
    end_id: str,
    condition: str,
    transition_prompt: str,
) -> dict[str, Any]:
    """Build a new quick-mode edge using the platform's verified shape."""
    return {
        "trainTaskId": train_task_id,
        "flowId": flow_id,
        "scriptStepStartId": start_id,
        "scriptStepStartHandle": f"{start_id}-source-bottom",
        "scriptStepEndId": end_id,
        "scriptStepEndHandle": f"{end_id}-target-top",
        "flowSettingType": "quick",
        "flowCondition": condition,
        "flowConfiguration": {
            "relation": "and",
            "conditions": [
                {
                    "text": "条件组1",
                    "relation": "and",
                    "conditions": [{"text": condition}],
                }
            ],
        },
        "transitionPrompt": transition_prompt,
        "transitionHistoryNum": TRANSITION_HISTORY_NUM,
        "isDefault": 1,
        "isError": False,
    }


def build_inserted_step_payload(
    template_step: dict[str, Any],
    markdown_step: dict[str, Any],
    *,
    train_task_id: str,
    new_step_id: str,
    position: dict[str, Any],
    allowed_resource_names: set[str],
    required_resource_names: set[str],
    resource_renames: dict[str, str] | None = None,
    excluded_file_ids: set[str] | None = None,
    resource_priority: list[str] | None = None,
    additional_resources: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Create a new node from a reviewed neighboring stage's safe metadata."""
    target = build_step_payload(
        template_step,
        markdown_step,
        train_task_id=train_task_id,
        resource_renames=resource_renames,
        excluded_file_ids=excluded_file_ids,
        required_resource_names=required_resource_names,
        resource_priority=resource_priority,
        additional_resources=additional_resources,
    )
    target["stepId"] = new_step_id
    target["positionDTO"] = copy.deepcopy(position)
    detail = target["stepDetailDTO"]
    resources = []
    for resource in detail.get("scriptStepResourceList") or []:
        if resource.get("fileName") not in allowed_resource_names:
            continue
        item = copy.deepcopy(resource)
        item["trainTaskId"] = train_task_id
        item["scriptStepId"] = new_step_id
        resources.append(item)
    for index, resource in enumerate(resources, start=1):
        resource["sort"] = index
    _apply_resource_write_shape(
        detail,
        resources,
        train_task_id=train_task_id,
        step_id=new_step_id,
    )
    return target


def build_score_payload(
    existing_item: dict[str, Any],
    rubric_item: dict[str, Any],
    *,
    train_task_id: str,
) -> dict[str, Any]:
    """Update one score item while retaining its stable platform item ID."""
    return {
        "trainTaskId": train_task_id,
        "itemId": existing_item["itemId"],
        "itemName": rubric_item["itemName"],
        "score": rubric_item["score"],
        "description": rubric_item["description"],
        "requireDetail": rubric_item["requireDetail"],
    }


def build_configuration_payload(
    existing_configuration: dict[str, Any],
    *,
    task_id: str,
    course_id: str,
) -> dict[str, Any]:
    """Preserve the reviewed task metadata while unifying its entry voice."""
    target = copy.deepcopy(existing_configuration)
    target["trainTaskId"] = task_id
    target["courseId"] = course_id
    target["entranceVoiceNid"] = VOICE_ID
    return target


def _resource_options(spec: dict[str, Any]) -> dict[str, Any]:
    allowed = spec.get("allowed")
    return {
        "resource_renames": dict(spec.get("renames") or {}),
        "excluded_file_ids": {
            str(file_id) for file_id in spec.get("excludeFileIds") or []
        },
        "allowed_resource_names": (
            {str(name) for name in allowed} if allowed is not None else None
        ),
        "required_resource_names": {
            str(name) for name in spec.get("required") or []
        },
        "resource_priority": [
            str(name) for name in spec.get("priority") or []
        ],
        "additional_resources": [
            dict(item) for item in spec.get("add") or []
        ],
    }


def _validate_reviewed_inputs(
    markdown_steps: list[dict[str, Any]],
    rubric_items: list[dict[str, Any]],
    stage_resource_specs: list[dict[str, Any]],
) -> None:
    if not markdown_steps:
        raise PreflightError("剧本没有可同步的训练阶段")
    if len(stage_resource_specs) != len(markdown_steps):
        raise PreflightError("资源清单阶段数与剧本阶段数不一致")
    for index, (step, spec) in enumerate(
        zip(markdown_steps, stage_resource_specs), start=1
    ):
        declared_name = str(spec.get("stageName") or "").strip()
        actual_name = str(step.get("stepName") or "").strip()
        if declared_name and declared_name != actual_name:
            raise PreflightError(
                f"资源清单阶段{index}名称不匹配："
                f"{declared_name} != {actual_name}"
            )

    conditions = [
        str(step.get("flowCondition") or "").strip()
        for step in markdown_steps
    ]
    if any(not condition for condition in conditions):
        raise PreflightError("每个阶段都必须有跳转关键词")
    if len(set(conditions)) != len(conditions):
        raise PreflightError("同一剧本的跳转关键词必须唯一")
    if conditions[-1] != "训练完成":
        raise PreflightError("最后阶段的跳转关键词必须是训练完成")
    if any(
        re.search(r"(?:NEXT_TO|TASK_COMPLETE|[A-Z]{2,}_[A-Z_]+)", condition)
        for condition in conditions
    ):
        raise PreflightError("跳转关键词必须使用中文短语")

    if len(rubric_items) != 4:
        raise PreflightError("评价标准必须恰好包含4个主评分项")
    try:
        total_score = sum(float(item["score"]) for item in rubric_items)
    except (KeyError, TypeError, ValueError) as exc:
        raise PreflightError("评价标准分值无法解析") from exc
    if abs(total_score - 10) > 1e-9:
        raise PreflightError("评价标准总分必须为10分")


def build_task_update_plan(
    snapshot: dict[str, Any],
    markdown_steps: list[dict[str, Any]],
    rubric_items: list[dict[str, Any]],
    *,
    task_id: str,
    course_id: str,
    stage_resource_specs: list[dict[str, Any]],
    insert_index: int | None = None,
    new_step_id: str | None = None,
    new_flow_id: str | None = None,
    insert_position: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build an ordered, fail-closed mutation plan for one reviewed task."""
    _validate_reviewed_inputs(
        markdown_steps, rubric_items, stage_resource_specs
    )
    configured_task_id = (snapshot.get("configuration") or {}).get(
        "trainTaskId"
    )
    if configured_task_id not in (None, task_id):
        raise PreflightError(
            f"快照任务ID不匹配：{configured_task_id} != {task_id}"
        )

    chain = linearize_snapshot(snapshot)
    live_steps = chain.business_steps
    live_scores = snapshot.get("scoreItems") or []
    if len(live_scores) != len(rubric_items):
        raise PreflightError("线上评价项数量与评价标准不一致")
    score_ids = [str(item.get("itemId") or "") for item in live_scores]
    if any(not item_id for item_id in score_ids) or len(set(score_ids)) != len(
        score_ids
    ):
        raise PreflightError("线上评价项ID缺失或重复")

    is_insertion = len(markdown_steps) == len(live_steps) + 1
    if len(markdown_steps) == len(live_steps):
        is_insertion = False
    elif not (
        is_insertion
        and insert_index is not None
        and 0 < insert_index < len(markdown_steps)
    ):
        raise PreflightError(
            "线上阶段数与剧本不匹配，且不符合单阶段插入条件"
        )

    configuration_payload = build_configuration_payload(
        snapshot.get("configuration") or {},
        task_id=task_id,
        course_id=course_id,
    )
    operations: list[dict[str, Any]] = [
        {
            "kind": "edit_configuration",
            "payload": configuration_payload,
        }
    ]
    expected_step_ids: list[str] = []
    expected_step_payloads: list[dict[str, Any]] = []
    retarget_operation: dict[str, Any] | None = None

    if is_insertion:
        if not new_step_id or not new_flow_id:
            raise PreflightError("插入阶段需要预先生成新节点ID和新连线ID")
        assert insert_index is not None
        inserted_spec = stage_resource_specs[insert_index]
        inserted_allowed = inserted_spec.get("allowed")
        if inserted_allowed is None:
            raise PreflightError("插入阶段必须声明允许绑定的资源名称")
        template_step = live_steps[insert_index - 1]
        if insert_position is None:
            previous_position = template_step.get("positionDTO") or {}
            next_position = live_steps[insert_index].get("positionDTO") or {}
            try:
                x = (
                    float(previous_position.get("x", 0))
                    + float(next_position.get("x", 0))
                ) / 2
                y = (
                    float(previous_position.get("y", 0))
                    + float(next_position.get("y", 0))
                ) / 2
            except (TypeError, ValueError) as exc:
                raise PreflightError("无法计算插入阶段的位置") from exc
            insert_position = {"x": str(x), "y": str(y)}
        inserted_options = _resource_options(inserted_spec)
        inserted_payload = build_inserted_step_payload(
            template_step,
            markdown_steps[insert_index],
            train_task_id=task_id,
            new_step_id=new_step_id,
            position=insert_position,
            allowed_resource_names=set(inserted_allowed),
            required_resource_names=inserted_options[
                "required_resource_names"
            ],
            resource_renames=inserted_options["resource_renames"],
            excluded_file_ids=inserted_options["excluded_file_ids"],
            resource_priority=inserted_options["resource_priority"],
            additional_resources=inserted_options["additional_resources"],
        )
        inserted_payload["courseId"] = course_id
        operations.append(
            {"kind": "create_step", "payload": inserted_payload}
        )

        next_live_step = live_steps[insert_index]
        created_flow = build_new_flow_payload(
            train_task_id=task_id,
            flow_id=new_flow_id,
            start_id=new_step_id,
            end_id=str(next_live_step["stepId"]),
            condition=str(
                markdown_steps[insert_index]["flowCondition"]
            ).strip(),
            transition_prompt=str(
                markdown_steps[insert_index].get("transitionPrompt") or ""
            ),
        )
        operations.append(
            {"kind": "create_flow", "payload": created_flow}
        )

        existing_mapping = [
            (live_steps[index], markdown_steps[index], index)
            for index in range(insert_index)
        ] + [
            (live_steps[index], markdown_steps[index + 1], index + 1)
            for index in range(insert_index, len(live_steps))
        ]
        expected_step_ids = [
            str(step["stepId"]) for step in live_steps[:insert_index]
        ] + [new_step_id] + [
            str(step["stepId"]) for step in live_steps[insert_index:]
        ]
    else:
        existing_mapping = [
            (step, markdown_steps[index], index)
            for index, step in enumerate(live_steps)
        ]
        expected_step_ids = [str(step["stepId"]) for step in live_steps]

    for existing_step, markdown_step, markdown_index in existing_mapping:
        payload = build_step_payload(
            existing_step,
            markdown_step,
            train_task_id=task_id,
            **_resource_options(stage_resource_specs[markdown_index]),
        )
        payload["courseId"] = course_id
        expected_step_payloads.append(payload)
        operations.append({"kind": "edit_step", "payload": payload})
    if is_insertion:
        expected_step_payloads.insert(insert_index, inserted_payload)

    if is_insertion:
        assert insert_index is not None
        for markdown_index in range(len(markdown_steps)):
            if markdown_index == insert_index:
                continue
            if markdown_index == insert_index - 1:
                existing_flow = chain.flows[insert_index]
                payload = build_flow_payload(
                    existing_flow,
                    train_task_id=task_id,
                    condition=str(
                        markdown_steps[markdown_index]["flowCondition"]
                    ).strip(),
                    transition_prompt=str(
                        markdown_steps[markdown_index].get(
                            "transitionPrompt"
                        )
                        or ""
                    ),
                    end_id=new_step_id,
                )
                retarget_operation = {
                    "kind": "edit_flow",
                    "payload": payload,
                    "safety": "retarget-last",
                }
                continue
            live_stage_index = (
                markdown_index
                if markdown_index < insert_index
                else markdown_index - 1
            )
            existing_flow = chain.flows[live_stage_index + 1]
            payload = build_flow_payload(
                existing_flow,
                train_task_id=task_id,
                condition=str(
                    markdown_steps[markdown_index]["flowCondition"]
                ).strip(),
                transition_prompt=str(
                    markdown_steps[markdown_index].get("transitionPrompt")
                    or ""
                ),
            )
            operations.append({"kind": "edit_flow", "payload": payload})
    else:
        for index, markdown_step in enumerate(markdown_steps):
            payload = build_flow_payload(
                chain.flows[index + 1],
                train_task_id=task_id,
                condition=str(markdown_step["flowCondition"]).strip(),
                transition_prompt=str(
                    markdown_step.get("transitionPrompt") or ""
                ),
            )
            operations.append({"kind": "edit_flow", "payload": payload})

    score_payloads = []
    for existing_item, rubric_item in zip(live_scores, rubric_items):
        score_payload = build_score_payload(
            existing_item, rubric_item, train_task_id=task_id
        )
        score_payloads.append(score_payload)
        operations.append(
            {
                "kind": "edit_score",
                "payload": score_payload,
            }
        )
    if retarget_operation is not None:
        operations.append(retarget_operation)

    return {
        "taskId": task_id,
        "courseId": course_id,
        "inserted": is_insertion,
        "operations": operations,
        "expected": {
            "stepIds": expected_step_ids,
            "stageNames": [
                str(step.get("stepName") or "") for step in markdown_steps
            ],
            "flowConditions": [
                str(step.get("flowCondition") or "").strip()
                for step in markdown_steps
            ],
            "transitionPrompts": [
                str(step.get("transitionPrompt") or "")
                for step in markdown_steps
            ],
            "scoreItems": [
                {
                    key: item[key]
                    for key in (
                        "itemName",
                        "score",
                        "description",
                        "requireDetail",
                    )
                }
                for item in rubric_items
            ],
            "scorePayloads": score_payloads,
            "stepPayloads": expected_step_payloads,
            "configurationPayload": configuration_payload,
        },
    }


def _resource_signature(resources: list[dict[str, Any]]) -> list[tuple[Any, ...]]:
    return [
        (
            item.get("fileId"),
            item.get("fileName"),
            item.get("sort"),
            item.get("isRequired"),
        )
        for item in resources
        if item.get("fileId")
    ]


def verify_task_snapshot(
    snapshot: dict[str, Any], plan: dict[str, Any]
) -> list[str]:
    """Return exact post-update drift errors; an empty list means verified."""
    errors: list[str] = []
    expected = plan["expected"]
    configuration = snapshot.get("configuration") or {}
    if configuration.get("trainTaskId") != plan["taskId"]:
        errors.append("configuration.trainTaskId 不匹配")
    if configuration.get("entranceVoiceNid") != VOICE_ID:
        errors.append("configuration.entranceVoiceNid 未统一")

    try:
        chain = linearize_snapshot(snapshot)
    except PreflightError as exc:
        return [f"流程拓扑校验失败：{exc}"]

    actual_ids = [str(step.get("stepId")) for step in chain.business_steps]
    if actual_ids != expected["stepIds"]:
        errors.append(
            f"阶段ID顺序不一致：actual={actual_ids}, "
            f"expected={expected['stepIds']}"
        )
        return errors

    detail_fields = (
        "stepName",
        "description",
        "interactiveRounds",
        "prologue",
        "llmPrompt",
        "trainerName",
        "agentId",
        "agentVoiceId",
        "avatarNid",
        "customDigitalHuman",
        "isSkipStep",
    )
    for index, (actual_step, expected_step) in enumerate(
        zip(chain.business_steps, expected["stepPayloads"]), start=1
    ):
        actual_detail = actual_step.get("stepDetailDTO") or {}
        expected_detail = expected_step.get("stepDetailDTO") or {}
        for field in detail_fields:
            if actual_detail.get(field) != expected_detail.get(field):
                errors.append(f"阶段{index}.{field} 不匹配")
        actual_resources = _resource_signature(
            actual_detail.get("scriptStepResourceList") or []
        )
        expected_resources = _resource_signature(
            expected_detail.get("scriptStepResourceList") or []
        )
        if actual_resources != expected_resources:
            errors.append(f"阶段{index}.scriptStepResourceList 不匹配")

    actual_exit_flows = chain.flows[1:]
    if len(actual_exit_flows) != len(expected["flowConditions"]):
        errors.append("阶段出口连线数量不匹配")
    else:
        for index, flow in enumerate(actual_exit_flows, start=1):
            expected_condition = expected["flowConditions"][index - 1]
            if flow.get("flowCondition") != expected_condition:
                errors.append(f"阶段{index}.flowCondition 不匹配")
            try:
                nested_condition = flow["flowConfiguration"]["conditions"][0][
                    "conditions"
                ][0]["text"]
            except (KeyError, IndexError, TypeError):
                nested_condition = None
            if nested_condition != expected_condition:
                errors.append(f"阶段{index}.嵌套flowCondition 不匹配")
            if (
                flow.get("transitionPrompt")
                != expected["transitionPrompts"][index - 1]
            ):
                errors.append(f"阶段{index}.transitionPrompt 不匹配")
            if flow.get("transitionHistoryNum") != TRANSITION_HISTORY_NUM:
                errors.append(f"阶段{index}.transitionHistoryNum 不匹配")

    actual_scores = {
        str(item.get("itemId")): item
        for item in snapshot.get("scoreItems") or []
    }
    for expected_score in expected["scorePayloads"]:
        item_id = str(expected_score["itemId"])
        actual_score = actual_scores.get(item_id)
        if actual_score is None:
            errors.append(f"评价项 {item_id} 缺失")
            continue
        for field in ("itemName", "score", "description", "requireDetail"):
            if actual_score.get(field) != expected_score.get(field):
                errors.append(f"评价项 {item_id}.{field} 不匹配")
    return errors


def apply_update_plan(
    gateway: Any,
    plan: dict[str, Any],
    *,
    original_snapshot: dict[str, Any],
    backup_dir: Path,
) -> dict[str, Any]:
    """Back up, apply ordered mutations, then re-query and verify exactly."""
    backup_path = write_backup(
        original_snapshot, Path(backup_dir), label=plan["taskId"]
    )
    dispatch = {
        "edit_configuration": gateway.edit_configuration,
        "create_step": gateway.create_step,
        "edit_step": gateway.edit_step,
        "create_flow": gateway.create_flow,
        "edit_flow": gateway.edit_flow,
        "edit_score": gateway.edit_score,
    }
    try:
        for operation in plan["operations"]:
            dispatch[operation["kind"]](operation["payload"])
        final_snapshot = gateway.export_snapshot(plan["taskId"])
        errors = verify_task_snapshot(final_snapshot, plan)
        if errors:
            raise RuntimeError("；".join(errors))
    except Exception as exc:
        raise RuntimeError(
            f"任务 {plan['taskId']} 同步或验证失败；备份：{backup_path}；"
            f"原因：{exc}"
        ) from exc
    return {
        "taskId": plan["taskId"],
        "backupPath": str(backup_path),
        "operationCount": len(plan["operations"]),
        "verified": True,
    }


class PolymasAbilityTrainGateway:
    """Small gateway around the legacy ability-training endpoints."""

    def __init__(
        self,
        *,
        course_id: str,
        headers: dict[str, str],
        requester: Any = requests,
        api_base: str = (
            "https://cloudapi.polymas.com/teacher-course/abilityTrain"
        ),
    ) -> None:
        self.course_id = course_id
        self._headers = dict(headers)
        self._requester = requester
        self._api_base = api_base.rstrip("/")

    def _post(self, endpoint: str, payload: dict[str, Any]) -> Any:
        response = self._requester.post(
            f"{self._api_base}/{endpoint}",
            headers=self._headers,
            json=payload,
            timeout=20,
        )
        try:
            body = response.json()
        except Exception as exc:
            raise RuntimeError(
                f"{endpoint} 返回非JSON响应：http={response.status_code}"
            ) from exc
        if not (
            body.get("code") in (200, "200")
            or body.get("success") is True
        ):
            raise RuntimeError(
                f"{endpoint} 失败：http={response.status_code}, "
                f"code={body.get('code')}, msg={body.get('msg')}"
            )
        return body.get("data")

    @staticmethod
    def _assert_task(payload: dict[str, Any]) -> str:
        task_id = str(payload.get("trainTaskId") or "")
        if not task_id:
            raise PreflightError("平台写入请求缺少trainTaskId")
        return task_id

    def export_snapshot(self, task_id: str) -> dict[str, Any]:
        task_id = str(task_id)
        return {
            "configuration": self._post(
                "queryConfiguration",
                {
                    "trainTaskId": task_id,
                    "trainSubType": "ability",
                },
            )
            or {},
            "steps": self._post(
                "queryScriptStepList",
                {
                    "trainTaskId": task_id,
                    "trainSubType": "ability",
                },
            )
            or [],
            "flows": self._post(
                "queryScriptStepFlowList",
                {"trainTaskId": task_id},
            )
            or [],
            "scoreItems": self._post(
                "queryScoreItemList",
                {"trainTaskId": task_id},
            )
            or [],
        }

    def edit_configuration(self, payload: dict[str, Any]) -> None:
        target = copy.deepcopy(payload)
        self._assert_task(target)
        target["courseId"] = self.course_id
        self._post("editConfiguration", target)

    def edit_step(self, payload: dict[str, Any]) -> None:
        target = copy.deepcopy(payload)
        self._assert_task(target)
        target["courseId"] = self.course_id
        self._post("editScriptStep", target)

    def create_step(self, payload: dict[str, Any]) -> None:
        target = copy.deepcopy(payload)
        self._assert_task(target)
        target["courseId"] = self.course_id
        self._post("createScriptStep", target)

    def edit_flow(self, payload: dict[str, Any]) -> None:
        target = copy.deepcopy(payload)
        self._assert_task(target)
        self._post("editScriptStepFlow", target)

    def create_flow(self, payload: dict[str, Any]) -> None:
        target = copy.deepcopy(payload)
        self._assert_task(target)
        self._post("createScriptStepFlow", target)

    def edit_score(self, payload: dict[str, Any]) -> None:
        target = copy.deepcopy(payload)
        self._assert_task(target)
        self._post("editScoreItem", target)


def load_update_manifest(path: Path) -> dict[str, Any]:
    """Load the credential-free task/resource manifest relative to itself."""
    manifest_path = Path(path).resolve()
    try:
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PreflightError(f"无法读取平台同步清单：{manifest_path}") from exc
    course_id = str(raw.get("courseId") or "").strip()
    if not course_id:
        raise PreflightError("平台同步清单缺少courseId")
    task_specs = raw.get("tasks")
    if not isinstance(task_specs, list) or not task_specs:
        raise PreflightError("平台同步清单必须包含tasks数组")

    base_dir = manifest_path.parent
    resolved_tasks = []
    keys: list[str] = []
    task_ids: list[str] = []
    for task in task_specs:
        if not isinstance(task, dict):
            raise PreflightError("平台同步清单中的task必须是对象")
        key = str(task.get("key") or "").strip()
        task_id = str(task.get("taskId") or "").strip()
        if not key or not task_id:
            raise PreflightError("每个task必须包含key和taskId")
        keys.append(key)
        task_ids.append(task_id)
        target = copy.deepcopy(task)
        target["key"] = key
        target["taskId"] = task_id
        for source_field, target_field in (
            ("markdown", "markdownPath"),
            ("rubric", "rubricPath"),
        ):
            relative = str(task.get(source_field) or "").strip()
            if not relative:
                raise PreflightError(
                    f"任务{key}缺少{source_field}路径"
                )
            resolved = (base_dir / relative).resolve()
            if not resolved.is_file():
                raise PreflightError(
                    f"任务{key}的{source_field}文件不存在：{resolved}"
                )
            target[target_field] = resolved
        if not isinstance(target.get("stages"), list):
            raise PreflightError(f"任务{key}的stages必须是数组")
        resolved_tasks.append(target)
    if len(set(keys)) != len(keys):
        raise PreflightError("平台同步清单的task key重复")
    if len(set(task_ids)) != len(task_ids):
        raise PreflightError("平台同步清单的taskId重复")

    backup_dir = str(raw.get("backupDir") or "platform_backups")
    return {
        "courseId": course_id,
        "backupDir": (base_dir / backup_dir).resolve(),
        "tasks": resolved_tasks,
        "manifestPath": manifest_path,
    }


def prepare_task_update(
    gateway: Any,
    task_spec: dict[str, Any],
    *,
    course_id: str,
    markdown_loader: Any,
    rubric_loader: Any,
    id_factory: Any,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Read live state and build a plan without performing any mutation."""
    task_id = str(task_spec["taskId"])
    snapshot = gateway.export_snapshot(task_id)
    markdown_steps = markdown_loader(Path(task_spec["markdownPath"]))
    rubric_items = rubric_loader(Path(task_spec["rubricPath"]))
    plan = build_task_update_plan(
        snapshot,
        markdown_steps,
        rubric_items,
        task_id=task_id,
        course_id=course_id,
        stage_resource_specs=task_spec["stages"],
        insert_index=task_spec.get("insertIndex"),
        new_step_id=id_factory(),
        new_flow_id=id_factory(),
        insert_position=task_spec.get("insertPosition"),
    )
    return snapshot, plan


DEFAULT_MANIFEST_PATH = (
    Path(__file__).resolve().parent.parent
    / "skills_training_course"
    / "中国农业大学-遥感地学分析"
    / "平台同步清单.json"
)


def _print_plan_preview(task_spec: dict[str, Any], plan: dict[str, Any]) -> None:
    counts = Counter(
        operation["kind"] for operation in plan["operations"]
    )
    print(
        f"[任务{task_spec['key']}] {task_spec['taskId']}："
        f"{len(plan['expected']['stageNames'])}个阶段，"
        f"{len(plan['expected']['scoreItems'])}个评价项，"
        f"操作={dict(counts)}，插入阶段={'是' if plan['inserted'] else '否'}"
    )


def resolve_course_id(
    manifest_course_id: str, configured_course_id: str | None
) -> tuple[str, bool]:
    """Use the task-link manifest as truth; report a stale env value."""
    explicit = str(manifest_course_id or "").strip()
    if not explicit:
        raise PreflightError("平台同步清单缺少显式courseId")
    configured = str(configured_course_id or "").strip()
    return explicit, bool(configured and configured != explicit)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="安全同步三个遥感地学能力训练任务"
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST_PATH,
        help="资源与任务映射清单",
    )
    parser.add_argument(
        "--task",
        default="all",
        help="只处理指定任务key（1/2/3），默认all",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="执行平台写入；不传时只做只读预检",
    )
    args = parser.parse_args(argv)

    from nanoid import generate

    from skill_training_build.create_score_items_from_rubric import (
        parse_rubric_markdown,
    )
    from skill_training_build.create_task_from_markdown import (
        get_headers,
        load_env_config,
        parse_markdown,
    )

    manifest = load_update_manifest(args.manifest)
    selected = manifest["tasks"]
    if args.task != "all":
        selected = [task for task in selected if task["key"] == args.task]
        if not selected:
            raise PreflightError(f"清单中不存在任务key：{args.task}")

    load_env_config()
    configured_course_id = str(os.getenv("COURSE_ID") or "").strip()
    course_id, stale_course_warning = resolve_course_id(
        manifest["courseId"], configured_course_id
    )
    if stale_course_warning:
        print(
            "⚠️ 环境变量COURSE_ID与本次任务链接不同；"
            "已使用平台同步清单中的显式课程ID。"
        )
    gateway = PolymasAbilityTrainGateway(
        course_id=course_id,
        headers=get_headers(),
    )

    prepared = []
    for task_spec in selected:
        snapshot, plan = prepare_task_update(
            gateway,
            task_spec,
            course_id=course_id,
            markdown_loader=parse_markdown,
            rubric_loader=parse_rubric_markdown,
            id_factory=lambda: generate(size=21),
        )
        prepared.append((task_spec, snapshot, plan))
        _print_plan_preview(task_spec, plan)

    if not args.apply:
        print("只读预检通过；未调用任何平台写入接口。")
        return 0

    for task_spec, snapshot, plan in prepared:
        report = apply_update_plan(
            gateway,
            plan,
            original_snapshot=snapshot,
            backup_dir=manifest["backupDir"],
        )
        print(
            f"[任务{task_spec['key']}] 同步并回读验证通过；"
            f"备份={report['backupPath']}"
        )
    return 0


def _remove_secret_keys(value: Any) -> Any:
    if isinstance(value, dict):
        sanitized = {}
        for key, item in value.items():
            normalized = str(key).lower().replace("_", "").replace("-", "")
            if any(
                secret in normalized
                for secret in (
                    "authorization",
                    "cookie",
                    "accesstoken",
                    "refreshtoken",
                    "password",
                    "jwt",
                )
            ):
                continue
            sanitized[key] = _remove_secret_keys(item)
        return sanitized
    if isinstance(value, list):
        return [_remove_secret_keys(item) for item in value]
    return value


def write_backup(
    snapshot: dict[str, Any], backup_dir: Path, *, label: str
) -> Path:
    """Write a credential-free snapshot before any live mutation."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    target_dir = Path(backup_dir) / f"{label}_{timestamp}"
    target_dir.mkdir(parents=True, exist_ok=False)
    target_path = target_dir / "snapshot.json"
    target_path.write_text(
        json.dumps(_remove_secret_keys(snapshot), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return target_path


if __name__ == "__main__":
    raise SystemExit(main())
