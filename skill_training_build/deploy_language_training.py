#!/usr/bin/env python3
"""Create or migrate native Polymas oral-language training tasks.

The Polymas UI uses the shared ``abilityTrain`` API namespace for both ability
and oral training. Native oral tasks are distinguished by ``trainSubType=oral``
in the task configuration and every script-step payload.
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlencode

import requests

from skill_training_build import create_configuration_from_markdown as cfm
from skill_training_build import create_speaking_task_from_markdown as csm


ORAL_TRAIN_SUBTYPE = csm.ORAL_TRAIN_SUBTYPE
DEFAULT_ORAL_DIGITAL_HUMAN = csm.DEFAULT_ORAL_DIGITAL_HUMAN
REQUIRED_DIGITAL_HUMAN_FIELDS = csm.REQUIRED_ORAL_DIGITAL_HUMAN_FIELDS
CLOUD_API_BASE = "https://cloudapi.polymas.com"
LANGUAGE_TRAINING_BASE = "https://hike-teaching-center.polymas.com/agent-course-full"
REALTIME_MARKING_MODULES = {
    "grammatical_accuracy",
    "pronunciation_expression",
    "semantic_coherence",
    "vocabulary_application",
}


def _is_success(result: dict[str, Any]) -> bool:
    return result.get("code") == 200 or result.get("success") is True


def _post_api(
    endpoint: str,
    payload: dict[str, Any],
    *,
    post: Callable = requests.post,
) -> dict[str, Any]:
    response = post(
        csm.ability_train_url(endpoint),
        headers=csm.get_headers(),
        json=payload,
        timeout=20,
    )
    result = response.json()
    if not _is_success(result):
        raise RuntimeError(f"{endpoint} failed: {result}")
    return result


def _request_json(
    method: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    response = requests.request(
        method,
        f"{CLOUD_API_BASE}{path}",
        headers=csm.get_headers(),
        params=params,
        json=payload,
        timeout=20,
    )
    result = response.json()
    if not _is_success(result):
        raise RuntimeError(f"{path} failed: {result}")
    return result


def build_oral_marking_business_config(
    modules: list[dict[str, Any]],
) -> dict[str, Any]:
    business_config: dict[str, Any] = {}
    for module in modules:
        module_key = module.get("moduleKey")
        if not module_key:
            continue
        raw_config = module.get("config") or {}
        config = json.loads(raw_config) if isinstance(raw_config, str) else dict(raw_config)
        config["moduleName"] = module.get("moduleName") or module_key
        config["isRealTime"] = module_key in REALTIME_MARKING_MODULES
        business_config[module_key] = config
    if not business_config:
        raise ValueError("No oral-marking modules were returned by Polymas.")
    return business_config


def build_language_training_url(
    *,
    course_id: str,
    library_id: str,
    train_task_id: str,
    instance_nid: str,
    version: int | None = None,
) -> str:
    query: list[tuple[str, Any]] = [
        ("trainTaskId", train_task_id),
        ("instanceNid", instance_nid),
    ]
    if version is not None:
        query.append(("version", version))
    query.append(("libraryId", library_id))
    return (
        f"{LANGUAGE_TRAINING_BASE}/{course_id}/language-training/create?"
        f"{urlencode(query)}"
    )


def build_oral_configuration_edit_payload(
    configuration: dict[str, Any],
    *,
    course_id: str,
) -> dict[str, Any]:
    payload = copy.deepcopy(configuration)
    payload.pop("trainType", None)
    payload.pop("unpublishedChanges", None)
    payload["courseId"] = course_id
    payload["trainSubType"] = ORAL_TRAIN_SUBTYPE

    ext_config = dict(cfm.ORAL_EXT_CONFIG_DEFAULTS)
    ext_config.update(payload.get("extConfig") or {})
    ext_config["trainSubType"] = ORAL_TRAIN_SUBTYPE
    payload["extConfig"] = ext_config
    return payload


def build_oral_step_edit_payload(
    step: dict[str, Any],
    *,
    course_id: str,
    library_id: str,
    markdown_step: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = copy.deepcopy(step)
    payload["courseId"] = course_id
    payload["libraryFolderId"] = library_id

    detail = payload.setdefault("stepDetailDTO", {})
    detail["trainSubType"] = ORAL_TRAIN_SUBTYPE
    ext_property = copy.deepcopy(detail.get("stepExtProperty") or {})
    ext_property["trainSubType"] = ORAL_TRAIN_SUBTYPE
    detail["stepExtProperty"] = ext_property
    if detail.get("nodeType") == "SCRIPT_NODE":
        detail.update(csm.resolve_oral_digital_human(markdown_step))
    return payload


def apply_oral_digital_human_defaults(steps: list[dict[str, Any]]) -> None:
    csm.apply_oral_digital_human_defaults(steps)


def validate_oral_snapshot(
    configuration: dict[str, Any],
    steps: list[dict[str, Any]],
    *,
    expected_business_steps: int,
) -> list[str]:
    errors: list[str] = []
    if configuration.get("trainSubType") != ORAL_TRAIN_SUBTYPE:
        errors.append("configuration.trainSubType must be oral")
    if (configuration.get("extConfig") or {}).get("trainSubType") != ORAL_TRAIN_SUBTYPE:
        errors.append("configuration.extConfig.trainSubType must be oral")
    if not configuration.get("instanceNid"):
        errors.append("configuration.instanceNid is required for oral marking")

    node_types = [
        (item.get("stepDetailDTO") or {}).get("nodeType")
        for item in steps
    ]
    if node_types.count("SCRIPT_START") != 1:
        errors.append("exactly one SCRIPT_START node is required")
    if node_types.count("SCRIPT_END") != 1:
        errors.append("exactly one SCRIPT_END node is required")

    business_steps = [
        item
        for item in steps
        if (item.get("stepDetailDTO") or {}).get("nodeType") == "SCRIPT_NODE"
    ]
    if len(business_steps) != expected_business_steps:
        errors.append(
            "business step count mismatch: "
            f"expected {expected_business_steps}, got {len(business_steps)}"
        )

    for item in steps:
        detail = item.get("stepDetailDTO") or {}
        stored_subtype = (
            (detail.get("stepExtProperty") or {}).get("trainSubType")
            or detail.get("trainSubType")
        )
        if stored_subtype != ORAL_TRAIN_SUBTYPE:
            errors.append(
                f"step {item.get('stepId', '<unknown>')} is not stored as oral"
            )
        if detail.get("nodeType") == "SCRIPT_NODE" and not csm.has_complete_oral_digital_human(
            detail
        ):
            errors.append(
                f"step {item.get('stepId', '<unknown>')} is missing a complete digital-human profile"
            )
    return errors


def query_configuration(
    train_task_id: str,
    *,
    course_id: str,
    post: Callable = requests.post,
) -> dict[str, Any]:
    result = _post_api(
        "queryConfiguration",
        {
            "trainTaskId": train_task_id,
            "trainSubType": ORAL_TRAIN_SUBTYPE,
            "courseId": course_id,
        },
        post=post,
    )
    return result.get("data") or {}


def query_steps(
    train_task_id: str,
    *,
    course_id: str,
    post: Callable = requests.post,
) -> list[dict[str, Any]]:
    result = _post_api(
        "queryScriptStepList",
        {
            "trainTaskId": train_task_id,
            "trainSubType": ORAL_TRAIN_SUBTYPE,
            "courseId": course_id,
        },
        post=post,
    )
    return result.get("data") or []


def query_flows(
    train_task_id: str,
    *,
    post: Callable = requests.post,
) -> list[dict[str, Any]]:
    result = _post_api(
        "queryScriptStepFlowList",
        {"trainTaskId": train_task_id},
        post=post,
    )
    return result.get("data") or []


def publish_oral_training(
    train_task_id: str,
    *,
    course_id: str,
    library_id: str,
    post: Callable = requests.post,
) -> None:
    _post_api(
        "publishAbilityTrain",
        {
            "courseId": course_id,
            "trainTaskId": train_task_id,
            "publishStatus": 1,
            "libraryFolderId": library_id,
        },
        post=post,
    )


def publish_oral_marking_instance(
    *,
    instance_nid: str,
    course_id: str,
    library_id: str,
) -> dict[str, Any]:
    payload = {
        "courseAgentId": instance_nid,
        "courseId": course_id,
        "agentInstanceId": instance_nid,
        "libraryFolderId": library_id,
        "isPublish": 1,
        "businessType": "course",
        "businessId": course_id,
        "agentType": "agent_mark",
    }
    response = requests.request(
        "POST",
        f"{CLOUD_API_BASE}/basic-course/courseAgent/publish",
        headers=csm.get_headers(),
        json=payload,
        timeout=20,
    )
    result = response.json()
    if _is_success(result):
        return {"alreadyPublished": False}
    if "已经发布过" in str(result.get("msg") or ""):
        return {"alreadyPublished": True}
    raise RuntimeError(f"/basic-course/courseAgent/publish failed: {result}")


def ensure_oral_marking_instance(
    train_task_id: str,
    *,
    course_id: str,
    library_id: str,
) -> dict[str, Any]:
    configuration = query_configuration(train_task_id, course_id=course_id)
    instance_nid = configuration.get("instanceNid")
    version = configuration.get("version")

    if not instance_nid:
        agent_result = _request_json(
            "GET",
            "/ai-tools/oralPracticeMarking/agentNId",
        )
        agent_ref_nid = agent_result.get("data")
        if not agent_ref_nid:
            raise RuntimeError("Polymas returned no oral-marking agent reference ID.")

        modules_result = _request_json(
            "GET",
            "/agents/v1/agent/instant/config/v2/modules",
            params={"agentNid": agent_ref_nid, "taskId": train_task_id},
        )
        business_config = build_oral_marking_business_config(
            modules_result.get("data") or []
        )

        user_result = _request_json(
            "POST",
            "/user/user/v2/get-current-user-detail",
            payload={},
        )
        user_data = user_result.get("data") or {}
        school_info = user_data.get("schoolInfo") or {}
        create_result = _request_json(
            "POST",
            "/agents/v1/create/agent",
            payload={
                "businessType": "SMART_AGENT_COURSE",
                "agentRefNid": agent_ref_nid,
                "userId": user_data.get("userNid"),
                "schoolId": str(school_info.get("schoolId") or ""),
                "businessConfig": json.dumps(business_config, ensure_ascii=False),
                "taskId": train_task_id,
            },
        )
        create_data = create_result.get("data")
        if isinstance(create_data, dict):
            instance_nid = (
                create_data.get("instanceNid")
                or create_data.get("agentInstanceNid")
                or create_data.get("nid")
            )
            version = create_data.get("version", version)
        else:
            instance_nid = create_data
        if not instance_nid:
            raise RuntimeError("Polymas created no oral-marking instance ID.")

        edit_payload = build_oral_configuration_edit_payload(
            configuration,
            course_id=course_id,
        )
        edit_payload["instanceNid"] = instance_nid
        if version is not None:
            edit_payload["version"] = version
        _post_api("editConfiguration", edit_payload)

    publish_oral_marking_instance(
        instance_nid=instance_nid,
        course_id=course_id,
        library_id=library_id,
    )

    refreshed = query_configuration(train_task_id, course_id=course_id)
    if not refreshed.get("instanceNid"):
        edit_payload = build_oral_configuration_edit_payload(
            refreshed,
            course_id=course_id,
        )
        edit_payload["instanceNid"] = instance_nid
        if version is not None:
            edit_payload["version"] = version
        _post_api("editConfiguration", edit_payload)
        refreshed = query_configuration(train_task_id, course_id=course_id)

    if refreshed.get("instanceNid") != instance_nid:
        raise RuntimeError("Oral-marking instance was not persisted to the task.")
    return {
        "instanceNid": instance_nid,
        "version": refreshed.get("version", version),
    }


def _write_recovery_state(markdown_path: Path, train_task_id: str) -> Path:
    state_path = markdown_path.parent / ".oral_deploy_state.json"
    state_path.write_text(
        json.dumps(
            {
                "trainTaskId": train_task_id,
                "status": "created",
                "updatedAt": datetime.now().astimezone().isoformat(timespec="seconds"),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return state_path


def _create_native_configuration(
    markdown_path: Path,
    *,
    course_id: str,
) -> str:
    steps = csm.parse_markdown(markdown_path)
    base_config = cfm.parse_base_configuration(markdown_path)
    cover_path = cfm.resolve_cover_image(
        markdown_path,
        base_config,
        steps,
        required=False,
    )
    train_task_cover: dict[str, str] = {}
    if cover_path:
        train_task_cover = csm.upload_cover_image(cover_path) or {}

    train_task_id = cfm.create_configuration(
        base_config,
        course_id,
        train_task_cover,
        train_sub_type=ORAL_TRAIN_SUBTYPE,
    )
    _write_recovery_state(markdown_path, train_task_id)
    return train_task_id


def ensure_native_oral_training(
    markdown_path: Path,
    *,
    train_task_id: str,
    course_id: str,
    library_id: str,
    publish: bool,
) -> dict[str, Any]:
    markdown_steps = csm.parse_markdown(markdown_path)
    if not markdown_steps:
        raise ValueError("No stages were parsed from the Markdown file.")
    apply_oral_digital_human_defaults(markdown_steps)

    configuration = query_configuration(train_task_id, course_id=course_id)
    edit_payload = build_oral_configuration_edit_payload(
        configuration,
        course_id=course_id,
    )
    _post_api("editConfiguration", edit_payload)

    platform_steps = query_steps(train_task_id, course_id=course_id)
    business_steps = csm.get_business_script_steps(platform_steps)
    flows = query_flows(train_task_id)

    if not business_steps:
        if flows:
            raise RuntimeError(
                "Task has flows but no business nodes; refusing an ambiguous resume."
            )
        start_id, end_id = csm.extract_start_end_ids(platform_steps)
        if not start_id or not end_id:
            start_id, end_id = csm.create_start_end_nodes(
                train_task_id,
                course_id,
                train_sub_type=ORAL_TRAIN_SUBTYPE,
                library_id=library_id,
            )
        csm.build_steps_from_markdown(
            markdown_path,
            train_task_id,
            start_node_id=start_id,
            end_node_id=end_id,
            flow_list=[],
            steps=markdown_steps,
            train_sub_type=ORAL_TRAIN_SUBTYPE,
            course_id=course_id,
            library_id=library_id,
        )
    elif len(business_steps) != len(markdown_steps):
        raise RuntimeError(
            "Partial task detected; refusing to guess missing nodes. "
            f"Markdown={len(markdown_steps)}, platform={len(business_steps)}"
        )

    platform_steps = query_steps(train_task_id, course_id=course_id)
    markdown_by_name = {item.get("stepName"): item for item in markdown_steps}
    for step in platform_steps:
        detail = step.get("stepDetailDTO") or {}
        payload = build_oral_step_edit_payload(
            step,
            course_id=course_id,
            library_id=library_id,
            markdown_step=markdown_by_name.get(detail.get("stepName")),
        )
        _post_api("editScriptStep", payload)

    marking = ensure_oral_marking_instance(
        train_task_id,
        course_id=course_id,
        library_id=library_id,
    )

    if publish:
        publish_oral_training(
            train_task_id,
            course_id=course_id,
            library_id=library_id,
        )

    final_config = query_configuration(train_task_id, course_id=course_id)
    final_steps = query_steps(train_task_id, course_id=course_id)
    final_flows = query_flows(train_task_id)
    errors = validate_oral_snapshot(
        final_config,
        final_steps,
        expected_business_steps=len(markdown_steps),
    )
    expected_flow_count = len(markdown_steps) + 1
    if len(final_flows) != expected_flow_count:
        errors.append(
            f"flow count mismatch: expected {expected_flow_count}, got {len(final_flows)}"
        )
    if errors:
        raise RuntimeError("Oral verification failed: " + "; ".join(errors))

    return {
        "trainTaskId": train_task_id,
        "trainSubType": final_config.get("trainSubType"),
        "stageCount": len(markdown_steps),
        "flowCount": len(final_flows),
        "published": publish,
        "instanceNid": marking["instanceNid"],
        "version": marking.get("version"),
        "url": build_language_training_url(
            course_id=course_id,
            library_id=library_id,
            train_task_id=train_task_id,
            instance_nid=marking["instanceNid"],
            version=marking.get("version"),
        ),
    }


def deploy_language_training(
    markdown_path: Path,
    *,
    train_task_id: str | None,
    course_id: str,
    library_id: str,
    publish: bool,
) -> dict[str, Any]:
    markdown_path = Path(markdown_path).expanduser().resolve()
    if not markdown_path.exists():
        raise FileNotFoundError(markdown_path)

    if not train_task_id:
        state_path = markdown_path.parent / ".oral_deploy_state.json"
        if state_path.exists():
            state = json.loads(state_path.read_text(encoding="utf-8"))
            existing_id = state.get("trainTaskId")
            if existing_id:
                raise RuntimeError(
                    "Recovery state already contains a task ID. Resume with "
                    f"--task-id {existing_id} instead of creating a duplicate."
                )
        train_task_id = _create_native_configuration(
            markdown_path,
            course_id=course_id,
        )

    return ensure_native_oral_training(
        markdown_path,
        train_task_id=train_task_id,
        course_id=course_id,
        library_id=library_id,
        publish=publish,
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create or migrate a native Polymas oral-language training task."
    )
    parser.add_argument("markdown_path")
    parser.add_argument(
        "--task-id",
        help="Migrate/resume this existing task instead of creating a new task.",
    )
    parser.add_argument("--course-id", default=None)
    parser.add_argument("--library-id", default=None)
    parser.add_argument("--publish", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    csm.load_env_config()
    args = build_arg_parser().parse_args(argv)
    course_id = args.course_id or os.getenv("COURSE_ID", "").strip()
    library_id = args.library_id or os.getenv("LIBRARY_ID", "").strip()
    if not course_id:
        print("Missing COURSE_ID.", file=sys.stderr)
        return 2
    if not library_id:
        print("Missing LIBRARY_ID or --library-id.", file=sys.stderr)
        return 2

    try:
        result = deploy_language_training(
            Path(args.markdown_path),
            train_task_id=args.task_id,
            course_id=course_id,
            library_id=library_id,
            publish=args.publish,
        )
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
