#!/usr/bin/env python3
"""通用能力训练 Pro Markdown 导入器。

教学内容来自 Pro 配置 Markdown；账号相关资源、阶段背景和平台评分项来自
独立 JSON 资源映射。默认只做预检，只有 ``--apply`` 才写入平台，只有
``--publish`` 才发布。
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence
from urllib.parse import urlencode

from dotenv import load_dotenv

from skill_training_pro.create_xray_pro_stage_cards import (
    StageCard,
    build_step_payload,
    build_task_edit_payload,
    parse_stage_cards,
)
from skill_training_pro.deploy_thermodynamics_pro import (
    CUSTOM_SKILL_TYPE_NID,
    DeployClient,
    GlobalSpec,
    SkillSpec,
    global_field,
    parse_members,
)


RUNTIME_VALUE = "运行时解析"


@dataclass(frozen=True)
class MemberDeploymentSpec:
    nickname: str
    role_name: str
    description: str
    prompt: str
    model_code: str
    voice_nid: str
    voice_type: str
    avatar_nid: str
    digital_human_name: str
    skills: tuple[SkillSpec, ...]


@dataclass(frozen=True)
class ResolvedMemberResources:
    voice_nid: str
    voice_type: str
    avatar_nid: str
    custom_digital_human: str | None


@dataclass(frozen=True)
class StageIdentity:
    number: int
    name: str


class ProDeployClient(DeployClient):
    def create_task(self, payload: Mapping[str, Any]) -> str:
        data = self.request(
            "POST", "/ai-platform/ability-train/tasks/create", payload=payload
        )
        if isinstance(data, str) and data:
            return data
        if isinstance(data, dict):
            for key in ("trainTaskId", "taskId", "nid"):
                if data.get(key):
                    return str(data[key])
        raise RuntimeError("创建 Pro 任务响应缺少任务 ID")

    def edit_skill(self, payload: Mapping[str, Any]) -> None:
        self.request("POST", "/ai-platform/ability-train/skills/edit", payload=payload)

    def score_items(self, task_id: str) -> list[dict[str, Any]]:
        data = self.request(
            "GET",
            "/ai-platform/ability-train/score-items/detail",
            params={"trainTaskNid": task_id},
        )
        if isinstance(data, dict) and isinstance(data.get("items"), list):
            return data["items"]
        return []

    def edit_score_items(self, payload: Mapping[str, Any]) -> None:
        self.request(
            "POST", "/ai-platform/ability-train/score-items/edit", payload=payload
        )

    def remove_step(self, step_id: str) -> None:
        self.request(
            "POST",
            "/ai-platform/ability-train/steps/remove",
            params={"stepId": step_id},
        )


def require_pro_task_id(task_id: str) -> str:
    task_id = task_id.strip()
    if not task_id.startswith("PRO"):
        raise ValueError(
            f"任务 ID {task_id!r} 不是能力训练 Pro ID；请从能力训练 Pro 入口创建"
        )
    return task_id


def build_pro_editor_url(
    course_id: str, library_id: str, *, task_id: str | None = None
) -> str:
    query = {
        "libraryId": library_id,
        "businessType": "course",
        "businessId": course_id,
    }
    if task_id:
        query["trainTaskId"] = require_pro_task_id(task_id)
    return (
        "https://hike-teaching-center.polymas.com/agent-course-full/"
        f"{course_id}/ability-training-pro/create?{urlencode(query)}"
    )


def _section_blocks(text: str, pattern: str) -> list[tuple[str, str]]:
    matches = list(re.finditer(pattern, text, re.MULTILINE))
    blocks: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        blocks.append((match.group(1).strip(), text[match.start() : end]))
    return blocks


def _member_field(block: str, name: str) -> str:
    match = re.search(
        rf"^- \*\*{re.escape(name)}\*\*:\s*(.*)$", block, re.MULTILINE
    )
    if not match:
        raise ValueError(f"成员配置缺少字段：{name}")
    return match.group(1).strip()


def parse_deployment_config(
    config_path: Path,
) -> tuple[GlobalSpec, list[MemberDeploymentSpec], list[StageCard], str]:
    text = config_path.read_text(encoding="utf-8")
    global_spec, parsed_members = parse_members(config_path)
    parsed_by_name = {member.nickname: member for member in parsed_members}
    members: list[MemberDeploymentSpec] = []
    for nickname, block in _section_blocks(text, r"^### 成员\d+:\s*(.+)$"):
        base = parsed_by_name[nickname]
        members.append(
            MemberDeploymentSpec(
                nickname=nickname,
                role_name=base.role_name,
                description=base.description,
                prompt=base.prompt,
                model_code=_member_field(block, "模型"),
                voice_nid=base.voice_nid,
                voice_type=base.voice_type,
                avatar_nid=_member_field(block, "形象资源ID"),
                digital_human_name=base.digital_human_name,
                skills=base.skills,
            )
        )
    ability_name = global_field(text, "能力名称")
    if not ability_name:
        raise ValueError("全局配置缺少能力名称")
    return global_spec, members, parse_stage_cards(config_path), ability_name


def _human_id(item: Mapping[str, Any]) -> str:
    for key in ("customNid", "digitalHumanNid", "nid"):
        if item.get(key):
            return str(item[key])
    return ""


def _human_name(item: Mapping[str, Any]) -> str:
    return str(item.get("digitalHumanName") or item.get("name") or "")


def resolve_member_resources(
    spec: MemberDeploymentSpec,
    humans: Sequence[Mapping[str, Any]],
    *,
    available_voice_ids: set[str],
    available_avatar_ids: set[str],
    override: Mapping[str, Any] | None = None,
) -> ResolvedMemberResources:
    override = override or {}
    custom_override = str(override.get("customDigitalHuman") or "")
    candidates = [item for item in humans if _human_name(item) == spec.digital_human_name]
    selected: Mapping[str, Any] | None = None
    if custom_override:
        selected = next(
            (item for item in humans if _human_id(item) == custom_override), None
        )
        if selected is None:
            raise ValueError(
                f"成员 {spec.nickname} 指定的数字人 {custom_override} 不在当前账号资源中"
            )

    fixed_voice = "" if spec.voice_nid == RUNTIME_VALUE else spec.voice_nid
    fixed_avatar = "" if spec.avatar_nid == RUNTIME_VALUE else spec.avatar_nid
    if selected is None and (fixed_voice or fixed_avatar):
        matching = [
            item
            for item in candidates
            if (not fixed_voice or str(item.get("voiceNid") or "") == fixed_voice)
            and (not fixed_avatar or str(item.get("avatarNid") or "") == fixed_avatar)
        ]
        if len(matching) == 1:
            selected = matching[0]
        elif len(matching) > 1:
            raise ValueError(
                f"成员 {spec.nickname} 存在多个同名数字人，请在资源映射中指定 customDigitalHuman"
            )
    elif selected is None:
        if len(candidates) == 1:
            selected = candidates[0]
        elif len(candidates) > 1:
            raise ValueError(
                f"成员 {spec.nickname} 存在多个同名数字人，请在资源映射中指定 customDigitalHuman"
            )

    voice_nid = str(
        override.get("voiceNid")
        or fixed_voice
        or (selected or {}).get("voiceNid")
        or ""
    )
    voice_type = str(
        override.get("voiceType")
        or ("" if spec.voice_type == RUNTIME_VALUE else spec.voice_type)
        or (selected or {}).get("voiceType")
        or (selected or {}).get("bigModelVoiceParam")
        or ""
    )
    avatar_nid = str(
        override.get("avatarNid")
        or fixed_avatar
        or (selected or {}).get("avatarNid")
        or ""
    )
    if not voice_nid or not voice_type or not avatar_nid:
        raise ValueError(
            f"成员 {spec.nickname} 的声音或形象仍为运行时解析；请补充资源映射"
        )
    if voice_nid not in available_voice_ids:
        raise ValueError(f"成员 {spec.nickname} 的声音 {voice_nid} 在当前账号不可用")
    if avatar_nid not in available_avatar_ids:
        raise ValueError(f"成员 {spec.nickname} 的形象 {avatar_nid} 在当前账号不可用")
    return ResolvedMemberResources(
        voice_nid=voice_nid,
        voice_type=voice_type,
        avatar_nid=avatar_nid,
        custom_digital_human=_human_id(selected or {}) or None,
    )


def _empty_placeholder(step: Mapping[str, Any]) -> bool:
    if step.get("stepName") != "未命名阶段":
        return False
    if str(step.get("description") or "").strip():
        return False
    if str(step.get("llmPrompt") or "").strip():
        return False
    ext = step.get("extConfig") or {}
    return not ext.get("bgMedia") and not ext.get("bgMediaId")


def assign_stage_steps(
    stages: Sequence[StageIdentity], existing_steps: Sequence[Mapping[str, Any]]
) -> tuple[dict[str, Mapping[str, Any]], list[str], list[str]]:
    named = {
        str(step.get("stepName")): step
        for step in existing_steps
        if step.get("stepName") and step.get("stepName") != "未命名阶段"
    }
    placeholders = sorted(
        (step for step in existing_steps if step.get("stepName") == "未命名阶段"),
        key=lambda item: (int(item.get("positionY") or 0), str(item.get("nid") or "")),
    )
    missing_stages = [stage for stage in stages if stage.name not in named]
    assignments: dict[str, Mapping[str, Any]] = {
        stage.name: named[stage.name] for stage in stages if stage.name in named
    }
    for stage, placeholder in zip(missing_stages, placeholders):
        assignments[stage.name] = placeholder
    missing = [stage.name for stage in missing_stages[len(placeholders) :]]
    surplus = placeholders[len(missing_stages) :]
    unsafe = [str(item.get("nid") or "") for item in surplus if not _empty_placeholder(item)]
    if unsafe:
        raise ValueError(f"存在含内容的未命名阶段，拒绝自动删除：{', '.join(unsafe)}")
    removable = [str(item.get("nid")) for item in surplus if item.get("nid")]
    return assignments, missing, removable


def build_score_items_payload(
    task_id: str, items: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    if not items:
        raise ValueError("能力训练 Pro 至少需要一条平台评价标准")
    normalized: list[dict[str, Any]] = []
    names: set[str] = set()
    for index, item in enumerate(items, start=1):
        name = str(item.get("name") or "").strip()
        requirement = str(item.get("requirement") or "").strip()
        try:
            score = float(item.get("score"))
        except (TypeError, ValueError) as exc:
            raise ValueError(f"评价标准 {index} 的 score 必须是正数") from exc
        if not name or not requirement or score <= 0:
            raise ValueError(f"评价标准 {index} 必须包含 name、正数 score 和 requirement")
        if name in names:
            raise ValueError(f"评价标准名称重复：{name}")
        names.add(name)
        normalized.append(
            {
                "name": name,
                "score": int(score) if score.is_integer() else score,
                "description": str(item.get("description") or "").strip(),
                "requirement": requirement,
            }
        )
    return {"trainTaskNid": require_pro_task_id(task_id), "items": normalized}


def _validate_remote_asset(value: Mapping[str, Any], label: str) -> dict[str, str]:
    file_id = str(value.get("fileId") or "").strip()
    file_url = str(value.get("fileUrl") or "").strip()
    path = str(value.get("path") or "").strip()
    if file_id and file_url:
        return {"fileId": file_id, "fileUrl": file_url}
    if path and Path(path).is_file():
        return {"path": str(Path(path).resolve())}
    raise ValueError(f"{label} 必须提供 fileId+fileUrl，或有效的本地 path")


def load_resource_map(
    path: Path, *, stage_names: Sequence[str]
) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("资源映射必须是 JSON 对象")
    if not isinstance(data.get("scoreItems"), list) or not data["scoreItems"]:
        raise ValueError("资源映射缺少非空 scoreItems")
    backgrounds = data.get("stageBackgrounds")
    if not isinstance(backgrounds, dict):
        raise ValueError("资源映射缺少 stageBackgrounds")
    normalized_backgrounds: dict[str, dict[str, str]] = {}
    for index, stage_name in enumerate(stage_names, start=1):
        value = backgrounds.get(stage_name) or backgrounds.get(str(index))
        if not isinstance(value, dict):
            raise ValueError(f"stageBackgrounds 缺少阶段：{stage_name}")
        normalized_backgrounds[stage_name] = _validate_remote_asset(
            value, f"阶段 {stage_name} 背景"
        )
    result = copy.deepcopy(data)
    result["stageBackgrounds"] = normalized_backgrounds
    build_score_items_payload("PRO-preflight", result["scoreItems"])
    entrance = result.get("entranceVoice")
    if not isinstance(entrance, dict):
        raise ValueError("资源映射缺少 entranceVoice")
    if not entrance.get("voiceNid") or not entrance.get("voiceType"):
        raise ValueError("entranceVoice 必须包含 voiceNid 和 voiceType")
    try:
        speed = float(entrance.get("speed", 1))
    except (TypeError, ValueError) as exc:
        raise ValueError("entranceVoice.speed 必须是正数") from exc
    if speed <= 0:
        raise ValueError("entranceVoice.speed 必须是正数")
    entrance["speed"] = int(speed) if speed.is_integer() else speed
    if result.get("cover"):
        result["cover"] = _validate_remote_asset(result["cover"], "任务封面")
    return result


def build_create_task_payload(
    *,
    name: str,
    description: str,
    course_id: str,
    term: int,
) -> dict[str, Any]:
    return {
        "trainTaskName": name,
        "description": description,
        "trainTaskCover": None,
        "trainTime": -1,
        "firstStepId": None,
        "publishStatus": None,
        "voiceUrl": None,
        "openSubtitle": 0,
        "openVideo": 0,
        # 当前 Pro 前端使用数值枚举：VOICE=1、TEXT=2、SELF=3。
        # 旧字符串 "SELF" 会被服务端统一包装成业务 500。
        "communicateMethod": 3,
        "entranceVoiceType": None,
        "entranceVoiceSpeed": None,
        "entranceVoiceNid": None,
        "extText": {"trainScreen": False, "trainScreenType": 1},
        "courseId": course_id,
        "term": term,
    }


def _materialize_asset(
    client: ProDeployClient, asset: Mapping[str, str], *, apply: bool
) -> dict[str, str]:
    if asset.get("fileId") and asset.get("fileUrl"):
        return {"fileId": asset["fileId"], "fileUrl": asset["fileUrl"]}
    if not apply:
        return {"fileId": "待上传", "fileUrl": asset["path"]}
    return client.upload_background(Path(asset["path"]))


def task_cover_edit_value(asset: Mapping[str, str]) -> str:
    """Return the current Pro task-edit shape for a materialized cover."""
    file_url = str(asset.get("fileUrl") or "").strip()
    if not file_url:
        raise ValueError("Pro 任务封面缺少 fileUrl")
    return file_url


def _configure_client_context(
    client: ProDeployClient,
    *,
    course_id: str,
    library_id: str,
    task_id: str | None,
) -> None:
    client.session.headers.update(
        {
            "route": build_pro_editor_url(
                course_id, library_id, task_id=task_id
            ),
            "User-Agent": "Mozilla/5.0",
            "Accept-Language": "zh-CN",
        }
    )


def deploy(
    client: ProDeployClient,
    *,
    config_path: Path,
    resource_map_path: Path,
    course_id: str,
    library_id: str,
    term: int,
    task_id: str | None,
    apply: bool,
    publish: bool,
) -> dict[str, Any]:
    global_spec, members, stages, ability_name = parse_deployment_config(config_path)
    resources = load_resource_map(
        resource_map_path, stage_names=[stage.name for stage in stages]
    )
    if task_id:
        task_id = require_pro_task_id(task_id)
    _configure_client_context(
        client,
        course_id=course_id,
        library_id=library_id,
        task_id=task_id,
    )
    user = client.current_user()
    user_nid = str(user.get("userNid") or "")
    if not user_nid:
        raise RuntimeError("当前账号缺少 userNid")
    voices = client.list_voices(course_id)
    avatars = client.list_avatars(user_nid, course_id, library_id)
    humans = client.list_digital_humans(user_nid, course_id, library_id)
    voice_ids = {str(item.get("nid")) for item in voices if item.get("nid")}
    avatar_ids = {str(item.get("nid")) for item in avatars if item.get("nid")}
    overrides = resources.get("members") or {}
    entrance_voice_id = str(resources["entranceVoice"]["voiceNid"])
    if entrance_voice_id not in voice_ids:
        raise ValueError(f"入场音色 {entrance_voice_id} 在当前账号不可用")
    resolved = {
        member.nickname: resolve_member_resources(
            member,
            humans,
            available_voice_ids=voice_ids,
            available_avatar_ids=avatar_ids,
            override=overrides.get(member.nickname),
        )
        for member in members
    }
    plan = {
        "mode": "apply" if apply else "preflight",
        "taskId": task_id,
        "taskAction": "reuse" if task_id else "create",
        "proEditorUrl": build_pro_editor_url(
            course_id, library_id, task_id=task_id
        ),
        "members": [member.nickname for member in members],
        "stages": [stage.name for stage in stages],
        "scoreItems": [item["name"] for item in resources["scoreItems"]],
        "published": False,
    }
    if not apply:
        return plan

    if task_id is None:
        task_id = require_pro_task_id(
            client.create_task(
                build_create_task_payload(
                    name=ability_name,
                    description=global_spec.description,
                    course_id=course_id,
                    term=term,
                )
            )
        )
        _configure_client_context(
            client,
            course_id=course_id,
            library_id=library_id,
            task_id=task_id,
        )

    custom_ids: dict[str, str] = {}
    created_humans: list[str] = []
    for member in members:
        item = resolved[member.nickname]
        custom_id = item.custom_digital_human
        if not custom_id:
            custom_id = client.create_digital_human(
                {
                    "userNid": user_nid,
                    "type": "NORMAL",
                    "voiceNid": item.voice_nid,
                    "avatarNid": item.avatar_nid,
                    "digitalHumanName": member.digital_human_name,
                    "courseId": course_id,
                    "term": term,
                    "libraryFolderId": library_id,
                }
            )
            created_humans.append(member.nickname)
        custom_ids[member.nickname] = custom_id

    existing_skills = client.list_skills(task_id)
    skill_ids_by_member: dict[str, list[str]] = {}
    for member in members:
        ids: list[str] = []
        for skill in member.skills:
            existing = next(
                (item for item in existing_skills if item.get("name") == skill.name),
                None,
            )
            skill_payload = {
                "trainTaskNid": task_id,
                "typeNid": CUSTOM_SKILL_TYPE_NID,
                "name": skill.name,
                "packageName": skill.name,
                "description": skill.description,
                "businessConfig": None,
                "instruction": skill.instruction,
            }
            if existing:
                skill_payload["nid"] = existing["nid"]
                client.edit_skill(skill_payload)
                skill_id = str(existing["nid"])
            else:
                skill_id = client.create_skill(skill_payload)
                existing_skills.append({"nid": skill_id, "name": skill.name})
            ids.append(skill_id)
        skill_ids_by_member[member.nickname] = ids

    existing_roles = client.list_roles(task_id)
    role_ids: dict[str, str] = {}
    for member in members:
        item = resolved[member.nickname]
        payload = {
            "trainTaskNid": task_id,
            "nickname": member.nickname,
            "roleName": member.role_name,
            "modelCode": member.model_code,
            "prompt": member.prompt,
            "voiceNid": item.voice_nid,
            "voiceType": item.voice_type,
            "voiceSpeed": 1,
            "avatarNid": item.avatar_nid,
            "customDigitalHuman": custom_ids[member.nickname],
            "description": member.description,
            "skills": ",".join(skill_ids_by_member[member.nickname]),
            "searchEngine": 0,
            "knowledgeSearch": 0,
            "knowledgeFileIds": [],
        }
        existing = next(
            (
                role
                for role in existing_roles
                if role.get("nickname") == member.nickname
            ),
            None,
        )
        if existing:
            payload["nid"] = existing["nid"]
            role_id = client.edit_role(payload)
        else:
            role_id = client.create_role(payload)
            existing_roles.append({"nid": role_id, "nickname": member.nickname})
        role_ids[member.nickname] = role_id

    existing_steps = client.list_steps(task_id)
    identities = [StageIdentity(stage.number, stage.name) for stage in stages]
    assignments, missing_names, removable = assign_stage_steps(
        identities, existing_steps
    )
    for step_id in removable:
        client.remove_step(step_id)
    for stage_name in missing_names:
        stage = next(item for item in stages if item.name == stage_name)
        placeholder = client.create_placeholder(
            task_id,
            course_id=course_id,
            term=term,
            position_x="570",
            position_y=str(100 + (stage.number - 1) * 300),
        )
        refreshed = next(
            (
                item
                for item in client.list_steps(task_id)
                if str(item.get("nid")) == str(placeholder["nid"])
            ),
            None,
        )
        assignments[stage_name] = refreshed or placeholder

    stage_ids: dict[str, str] = {}
    for stage in stages:
        existing = assignments[stage.name]
        background = _materialize_asset(
            client, resources["stageBackgrounds"][stage.name], apply=True
        )
        payload = build_step_payload(
            existing,
            stage,
            task_id=task_id,
            role_ids=role_ids,
            background=background,
            existing_step=existing,
        )
        client.edit_step(payload)
        stage_ids[stage.name] = str(existing["nid"])

    score_payload = build_score_items_payload(task_id, resources["scoreItems"])
    client.edit_score_items(score_payload)

    task = client.task_detail(task_id)
    cover_spec = resources.get("cover") or resources["stageBackgrounds"][stages[0].name]
    cover = _materialize_asset(client, cover_spec, apply=True)
    task_payload = build_task_edit_payload(task, stage_ids[stages[0].name])
    task_payload.update(
        {
            "trainTaskName": ability_name,
            "description": global_spec.description,
            "trainTaskCover": task_cover_edit_value(cover),
            "openSubtitle": int(global_field(config_path.read_text(), "默认打开字幕") == "是"),
            "openVideo": int(global_field(config_path.read_text(), "全程开启摄像头") == "是"),
        }
    )
    entrance = resources["entranceVoice"]
    task_payload.update(
        {
            "entranceVoiceNid": entrance["voiceNid"],
            "entranceVoiceType": entrance["voiceType"],
            "entranceVoiceSpeed": entrance["speed"],
            "extText": task.get("extText")
            or {"trainScreen": False, "trainScreenType": 1},
        }
    )
    client.edit_task(task_payload)

    published = False
    if publish:
        client.publish_task(task_id, course_id, library_id)
        published = True

    verified_steps = client.list_steps(task_id)
    actual_names = {str(item.get("stepName")) for item in verified_steps}
    expected_names = {stage.name for stage in stages}
    if not expected_names.issubset(actual_names):
        raise RuntimeError(f"阶段回查不完整：{sorted(expected_names - actual_names)}")
    if any(not _empty_placeholder(item) for item in verified_steps if item.get("stepName") == "未命名阶段"):
        raise RuntimeError("回查发现含内容的未命名阶段")
    actual_score_items = client.score_items(task_id)
    expected_scores = {
        (item["name"], float(item["score"])) for item in score_payload["items"]
    }
    actual_scores = {
        (str(item.get("name")), float(item.get("score") or 0))
        for item in actual_score_items
    }
    if expected_scores != actual_scores:
        raise RuntimeError("平台评价标准回查不一致")
    verified_task = client.task_detail(task_id)
    if verified_task.get("firstStepId") != stage_ids[stages[0].name]:
        raise RuntimeError("首阶段回查不一致")

    return {
        **plan,
        "taskId": task_id,
        "proEditorUrl": build_pro_editor_url(
            course_id, library_id, task_id=task_id
        ),
        "createdDigitalHumans": created_humans,
        "roleIds": role_ids,
        "stageIds": stage_ids,
        "published": published,
        "verified": True,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="从 Markdown 导入能力训练 Pro")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--resource-map", type=Path, required=True)
    parser.add_argument("--course-id", required=True)
    parser.add_argument("--library-id", required=True)
    parser.add_argument("--term", type=int, required=True)
    parser.add_argument("--task-id")
    parser.add_argument("--env-file", default=".env")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--publish", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.publish and not args.apply:
        raise ValueError("--publish 必须与 --apply 一起使用")
    load_dotenv(args.env_file, override=True)
    authorization = os.getenv("AUTHORIZATION", "").strip()
    cookie = os.getenv("COOKIE", "").strip()
    if not authorization or not cookie:
        raise RuntimeError("环境缺少 AUTHORIZATION 或 COOKIE")
    client = ProDeployClient(authorization, cookie, timeout=90)
    result = deploy(
        client,
        config_path=args.config,
        resource_map_path=args.resource_map,
        course_id=args.course_id,
        library_id=args.library_id,
        term=args.term,
        task_id=args.task_id,
        apply=args.apply,
        publish=args.publish,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
