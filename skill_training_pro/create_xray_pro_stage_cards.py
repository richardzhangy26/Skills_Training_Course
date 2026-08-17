#!/usr/bin/env python3
"""Upsert all six stage cards for the X-ray simulation Pro task.

The Markdown configuration is the source of truth. Existing cards are matched
by exact stage name, so rerunning the script updates them instead of creating
duplicates. No platform write occurs unless ``--apply`` is supplied.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import mimetypes
import os
import re
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

import requests
from dotenv import load_dotenv

try:
    from skill_training_pro.configure_xray_pro_roles import (
        DEFAULT_COURSE_ID,
        DEFAULT_EXPECTED_ACCOUNT,
        DEFAULT_LIBRARY_ID,
        DEFAULT_TASK_ID,
        PolymasClient,
        extract_id,
        replace_role_mentions,
    )
except ModuleNotFoundError:  # Direct execution from skill_training_pro/.
    from configure_xray_pro_roles import (  # type: ignore[no-redef]
        DEFAULT_COURSE_ID,
        DEFAULT_EXPECTED_ACCOUNT,
        DEFAULT_LIBRARY_ID,
        DEFAULT_TASK_ID,
        PolymasClient,
        extract_id,
        replace_role_mentions,
    )


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = (
    PROJECT_ROOT
    / "skills_training_course"
    / "临沂大学-单片机原理与应用"
    / "简易数字X光成像模拟系统单片机开发实训-Pro配置.md"
)
DEFAULT_BACKGROUND_DIR = (
    DEFAULT_CONFIG_PATH.parent
    / "简易数字X光成像模拟系统单片机开发实训"
    / "backgrounds"
)
DEFAULT_ASSET_MANIFEST = Path(__file__).with_name("xray_pro_stage_assets.json")
DEFAULT_TERM = 20271
REQUIRED_ROLE_NAMES = ("陈工", "林医生", "老周")
POSITION_GAP = 300


@dataclass(frozen=True)
class StageCard:
    number: int
    name: str
    description: str
    user_role_name: str
    user_assign_name: str
    user_description: str
    model_code: str
    skippable: bool
    prompt: str
    background_description: str


def extract_field(block: str, label: str) -> str:
    match = re.search(
        rf"^\*\*{re.escape(label)}\*\*:\s*(.*?)\s*$", block, re.MULTILINE
    )
    if not match:
        raise ValueError(f"阶段配置缺少字段：{label}")
    return match.group(1).strip()


def parse_stage_cards(config_path: Path) -> list[StageCard]:
    text = config_path.read_text(encoding="utf-8")
    matches = list(re.finditer(r"^### 阶段(\d+):\s*(.+?)\s*$", text, re.MULTILINE))
    stages: list[StageCard] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        block = text[match.start() : end]
        prompt_match = re.search(
            r"<script_prompt>\s*(.*?)\s*</script_prompt>", block, re.DOTALL
        )
        if not prompt_match:
            raise ValueError(f"阶段{match.group(1)}缺少 <script_prompt>")
        skip_text = extract_field(block, "是否可跳过")
        if skip_text not in {"是", "否"}:
            raise ValueError(f"无法识别是否可跳过：{skip_text}")
        stages.append(
            StageCard(
                number=int(match.group(1)),
                name=match.group(2).strip(),
                description=extract_field(block, "卡片描述"),
                user_role_name=extract_field(block, "用户扮演角色名称"),
                user_assign_name=extract_field(block, "AI 对用户称呼"),
                user_description=extract_field(block, "用户扮演角色描述"),
                model_code=extract_field(block, "剧本模型"),
                skippable=skip_text == "是",
                prompt=prompt_match.group(1).strip(),
                background_description=extract_field(block, "背景图描述"),
            )
        )
    if not stages:
        raise ValueError(f"没有从 {config_path} 解析到阶段")
    expected_numbers = list(range(1, len(stages) + 1))
    actual_numbers = [stage.number for stage in stages]
    if actual_numbers != expected_numbers:
        raise ValueError(f"阶段编号必须连续：{actual_numbers}")
    return stages


def inject_role_tags(prompt: str, role_ids: Mapping[str, str]) -> str:
    result = replace_role_mentions(prompt, role_ids)
    result = re.sub(
        r"达成结束条件后，跳转到【[^】]+】阶段",
        "达成结束条件后，结束本阶段",
        result,
    )
    if "<role>user</role>" not in result:
        marker = "【背景设定】"
        if marker in result:
            before, after = result.split(marker, 1)
            result = f"{before.rstrip()}\n<role>user</role>\n\n{marker}{after}"
        else:
            result = f"<role>user</role>\n{result}"
    return result


STEP_FIELDS = (
    "nid",
    "trainTaskNid",
    "stepName",
    "description",
    "modelCode",
    "llmPrompt",
    "skills",
    "positionX",
    "positionY",
    "voiceNid",
    "voiceSpeed",
    "voiceType",
    "avatarNid",
    "customDigitalHuman",
    "timeLimit",
    "useWhiteboard",
    "isSkipStep",
    "isNeedBegin",
    "isTransition",
    "flowHideSubtitle",
    "extConfig",
)


def build_step_payload(
    reference_step: Mapping[str, Any],
    stage: StageCard,
    *,
    task_id: str,
    role_ids: Mapping[str, str],
    background: Mapping[str, str],
    existing_step: Mapping[str, Any] | None,
) -> dict[str, Any]:
    source = existing_step or reference_step
    payload = {
        key: copy.deepcopy(source.get(key))
        for key in STEP_FIELDS
        if key in source
    }
    if existing_step is None:
        payload.pop("nid", None)
    payload.update(
        {
            "trainTaskNid": task_id,
            "stepName": stage.name,
            "description": stage.description,
            "modelCode": stage.model_code,
            "llmPrompt": inject_role_tags(stage.prompt, role_ids),
        }
    )

    try:
        first_x = int(reference_step.get("positionX") or 570)
        first_y = int(reference_step.get("positionY") or 100)
    except (TypeError, ValueError) as exc:
        raise ValueError("参考卡片位置不是整数") from exc
    payload["positionX"] = str(first_x)
    payload["positionY"] = str(first_y + (stage.number - 1) * POSITION_GAP)

    payload["isSkipStep"] = int(stage.skippable)
    payload["timeLimit"] = -1
    payload["useWhiteboard"] = 0
    payload["isNeedBegin"] = 1
    payload["isTransition"] = 0
    payload["flowHideSubtitle"] = 0

    ext_config = copy.deepcopy(source.get("extConfig") or reference_step.get("extConfig") or {})
    ext_config.update(
        {
            "userRoleName": stage.user_role_name,
            "userNameType": 2,
            "userAssignName": stage.user_assign_name,
            "userDescription": stage.user_description,
            "bgMediaType": 1,
            "bgMedia": background["fileUrl"],
            "bgMediaId": background["fileId"],
            "bgMediaVolume": ext_config.get("bgMediaVolume") or 80,
        }
    )
    payload["extConfig"] = ext_config
    return payload


TASK_EDIT_FIELDS = (
    "trainTaskId",
    "trainTaskName",
    "description",
    "trainTaskCover",
    "trainTime",
    "publishStatus",
    "voiceUrl",
    "openSubtitle",
    "openVideo",
    "communicateMethod",
    "entranceVoiceType",
    "entranceVoiceSpeed",
    "entranceVoiceNid",
    "firstStepId",
)


def build_task_edit_payload(
    task_detail: Mapping[str, Any], first_step_id: str
) -> dict[str, Any]:
    payload = {
        key: copy.deepcopy(task_detail.get(key))
        for key in TASK_EDIT_FIELDS
        if key in task_detail
    }
    payload["firstStepId"] = first_step_id
    return payload


def build_placeholder_payload(
    task_id: str,
    *,
    course_id: str,
    term: int,
    position_x: str,
    position_y: str,
) -> dict[str, Any]:
    return {
        "trainTaskNid": task_id,
        "stepName": "未命名阶段",
        "description": None,
        "modelCode": None,
        "llmPrompt": None,
        "skills": None,
        "positionX": position_x,
        "positionY": position_y,
        "voiceNid": None,
        "voiceSpeed": None,
        "voiceType": None,
        "avatarNid": None,
        "customDigitalHuman": None,
        "timeLimit": None,
        "useWhiteboard": None,
        "isSkipStep": 0,
        "isNeedBegin": 1,
        "isTransition": 0,
        "extConfig": {
            "userRoleName": None,
            "userNameType": None,
            "userAssignName": None,
            "userDescription": None,
            "bgMediaType": 1,
            "bgMedia": None,
            "bgMediaId": None,
            "bgMediaVolume": 80,
            "bgMediaTheme": "white",
            "bgMusicCategory": None,
            "bgMusicId": None,
            "bgMusic": None,
            "bgMusicVolume": None,
            "transitionBgMediaType": 1,
            "transitionBgMedia": None,
            "transitionBgMediaId": None,
            "transitionBgMediaVolume": 80,
            "transitionBgMediaTheme": "white",
            "transitionBgMediaFullScreen": 0,
            "transitionBgMusicCategory": None,
            "transitionBgMusicId": None,
            "transitionBgMusic": None,
            "transitionBgMusicVolume": None,
            "flowAsideContent": None,
            "flowUseAside": None,
            "flowAsideVoiceNid": None,
            "flowAsideVoiceType": None,
            "flowAsideVoiceAvatarNid": None,
            "flowAsideVoiceCustomDigitalHuman": None,
            "flowAsideVoiceSpeed": 1,
            "flowAsideVoiceVolume": None,
        },
        "flowHideSubtitle": 0,
        "courseId": course_id,
        "term": term,
    }


class StageClient(PolymasClient):
    def task_detail(self, task_id: str) -> dict[str, Any]:
        return self.request(
            "GET", "/ai-platform/ability-train/tasks/detail", params={"taskId": task_id}
        ) or {}

    def edit_task(self, payload: Mapping[str, Any]) -> None:
        self.request("POST", "/ai-platform/ability-train/tasks/edit", payload=payload)

    def create_placeholder(
        self,
        task_id: str,
        *,
        course_id: str,
        term: int,
        position_x: str,
        position_y: str,
    ) -> dict[str, Any]:
        payload = build_placeholder_payload(
            task_id,
            course_id=course_id,
            term=term,
            position_x=position_x,
            position_y=position_y,
        )
        data = self.request(
            "POST",
            "/ai-platform/ability-train/steps/create",
            payload=payload,
        )
        step_id = extract_id(data, "nid", "stepId")
        if not step_id:
            raise RuntimeError("创建阶段响应缺少阶段 ID")
        if isinstance(data, dict):
            return {**data, "nid": step_id}
        return {
            "nid": step_id,
            "trainTaskNid": task_id,
            "stepName": "未命名阶段",
            "positionX": position_x,
            "positionY": position_y,
        }

    def edit_step(self, payload: Mapping[str, Any]) -> str:
        self.request("POST", "/ai-platform/ability-train/steps/edit", payload=payload)
        return str(payload["nid"])

    def upload_background(self, file_path: Path) -> dict[str, str]:
        mime_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
        upload_headers = {
            key: value
            for key, value in self.session.headers.items()
            if key.lower() != "content-type"
        }
        form = {
            "identifyCode": str(uuid.uuid4()),
            "name": file_path.name,
            "chunk": "0",
            "chunks": "1",
            "size": str(file_path.stat().st_size),
        }
        with file_path.open("rb") as file_handle:
            response = requests.post(
                "https://cloudapi.polymas.com/basic-resource/file/upload",
                headers=upload_headers,
                data=form,
                files={"file": (file_path.name, file_handle, mime_type)},
                timeout=max(self.timeout, 60),
            )
        response.raise_for_status()
        result = response.json()
        if result.get("code") not in (200, "200") and result.get("success") is not True:
            message = result.get("msg") or result.get("message") or "未知业务错误"
            raise RuntimeError(f"上传背景失败：{message}")
        data = result.get("data") or {}
        file_id = data.get("fileId")
        file_url = data.get("ossUrl") or data.get("fileUrl")
        if not file_id or not file_url:
            raise RuntimeError("上传背景响应缺少 fileId/fileUrl")
        return {"fileId": str(file_id), "fileUrl": str(file_url)}


def find_background_file(background_dir: Path, stage_number: int) -> Path:
    matches = sorted(background_dir.glob(f"*_stage_{stage_number}_*.png"))
    if len(matches) != 1:
        raise RuntimeError(
            f"阶段{stage_number}背景图应有且仅有一张，实际找到 {len(matches)} 张"
        )
    return matches[0]


def file_sha256(file_path: Path) -> str:
    digest = hashlib.sha256()
    with file_path.open("rb") as file_handle:
        for chunk in iter(lambda: file_handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_asset_manifest(manifest_path: Path) -> dict[str, Any]:
    if not manifest_path.exists():
        return {"assets": {}}
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("assets"), dict):
        raise ValueError(f"背景上传清单格式错误：{manifest_path}")
    return data


def save_asset_manifest(manifest_path: Path, manifest: Mapping[str, Any]) -> None:
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = manifest_path.with_suffix(manifest_path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    temporary.replace(manifest_path)


def existing_background(step: Mapping[str, Any] | None) -> dict[str, str] | None:
    if not step:
        return None
    ext_config = step.get("extConfig") or {}
    file_id = ext_config.get("bgMediaId")
    file_url = ext_config.get("bgMedia")
    if file_id and file_url:
        return {"fileId": str(file_id), "fileUrl": str(file_url)}
    return None


def ensure_background(
    client: StageClient,
    *,
    stage: StageCard,
    background_file: Path,
    existing_step: Mapping[str, Any] | None,
    manifest: dict[str, Any],
    manifest_path: Path,
) -> tuple[dict[str, str], bool]:
    current = existing_background(existing_step)
    if current:
        return current, False

    checksum = file_sha256(background_file)
    key = str(stage.number)
    cached = manifest["assets"].get(key) or {}
    if (
        cached.get("sha256") == checksum
        and cached.get("fileId")
        and cached.get("fileUrl")
    ):
        return {
            "fileId": str(cached["fileId"]),
            "fileUrl": str(cached["fileUrl"]),
        }, False

    uploaded = client.upload_background(background_file)
    manifest["assets"][key] = {
        "stageName": stage.name,
        "source": str(background_file),
        "sha256": checksum,
        **uploaded,
    }
    save_asset_manifest(manifest_path, manifest)
    return uploaded, True


def editable_projection(step: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: copy.deepcopy(step.get(key))
        for key in STEP_FIELDS
        if key in step
    }


def assign_existing_steps(
    stages: Sequence[StageCard], existing_steps: Sequence[Mapping[str, Any]]
) -> tuple[dict[str, Mapping[str, Any]], list[str]]:
    named = {
        str(step.get("stepName")): step
        for step in existing_steps
        if step.get("stepName") and step.get("stepName") != "未命名阶段"
    }
    placeholders = sorted(
        (step for step in existing_steps if step.get("stepName") == "未命名阶段"),
        key=lambda step: (int(step.get("positionY") or 0), str(step.get("nid") or "")),
    )
    missing_stages = [stage for stage in stages if stage.name not in named]
    if len(placeholders) > len(missing_stages):
        raise RuntimeError(
            f"未命名占位卡数量 {len(placeholders)} 超过缺失阶段数量 {len(missing_stages)}"
        )
    assignments: dict[str, Mapping[str, Any]] = {
        stage.name: named[stage.name] for stage in stages if stage.name in named
    }
    for stage, placeholder in zip(missing_stages, placeholders):
        assignments[stage.name] = placeholder
    still_missing = [stage.name for stage in missing_stages[len(placeholders) :]]
    return assignments, still_missing


def verify_stage_cards(
    client: StageClient,
    *,
    task_id: str,
    stages: Sequence[StageCard],
    role_ids: Mapping[str, str],
    first_step_id: str,
) -> None:
    steps = client.list_steps(task_id)
    by_name = {step.get("stepName"): step for step in steps}
    errors: list[str] = []
    expected_names = {stage.name for stage in stages}
    if expected_names - set(by_name):
        errors.append(f"缺少阶段：{sorted(expected_names - set(by_name))}")

    for stage in stages:
        step = by_name.get(stage.name)
        if not step:
            continue
        ext_config = step.get("extConfig") or {}
        prompt = str(step.get("llmPrompt") or "")
        if step.get("description") != stage.description:
            errors.append(f"{stage.name} 描述不一致")
        if ext_config.get("userRoleName") != stage.user_role_name:
            errors.append(f"{stage.name} 用户角色名称不一致")
        if ext_config.get("userAssignName") != stage.user_assign_name:
            errors.append(f"{stage.name} 用户称呼不一致")
        if ext_config.get("userDescription") != stage.user_description:
            errors.append(f"{stage.name} 用户角色描述不一致")
        if not ext_config.get("bgMediaId") or not ext_config.get("bgMedia"):
            errors.append(f"{stage.name} 背景资源为空")
        if "<role>user</role>" not in prompt:
            errors.append(f"{stage.name} 缺少用户角色引用")
        for role_name, role_id in role_ids.items():
            if f"@{role_name}" in prompt:
                errors.append(f"{stage.name} 仍含 @{role_name}")
            if f"@{role_name}" in stage.prompt and f"<role>{role_id}</role>" not in prompt:
                errors.append(f"{stage.name} 缺少 {role_name} 角色引用")

    task = client.task_detail(task_id)
    if task.get("firstStepId") != first_step_id:
        errors.append("任务 firstStepId 回查不一致")
    if task.get("publishStatus") != 0:
        errors.append("任务发布状态发生了变化")
    if errors:
        raise RuntimeError("阶段卡片回查失败：\n- " + "\n- ".join(errors))


def configure_stage_cards(
    client: StageClient,
    *,
    task_id: str,
    course_id: str,
    term: int,
    config_path: Path,
    background_dir: Path,
    manifest_path: Path,
    expected_account: str,
    apply: bool,
) -> dict[str, Any]:
    user = client.current_user()
    account = str(user.get("realName") or user.get("nickName") or "")
    if expected_account and account != expected_account:
        raise RuntimeError(
            f"账号校验失败：当前为“{account}”，期望“{expected_account}”"
        )

    stages = parse_stage_cards(config_path)
    roles = client.list_roles(task_id)
    role_ids = {
        str(role["nickname"]): str(role["nid"])
        for role in roles
        if role.get("nickname") in REQUIRED_ROLE_NAMES and role.get("nid")
    }
    missing_roles = set(REQUIRED_ROLE_NAMES) - set(role_ids)
    if missing_roles:
        raise RuntimeError(f"任务缺少成员：{', '.join(sorted(missing_roles))}")

    steps = client.list_steps(task_id)
    assignments, still_missing = assign_existing_steps(stages, steps)
    reference = assignments.get(stages[0].name)
    if not reference:
        raise RuntimeError("平台缺少阶段1，无法取得稳定的卡片默认字段")

    background_files = {
        stage.number: find_background_file(background_dir, stage.number) for stage in stages
    }
    plan = {
        "account": account,
        "taskId": task_id,
        "stageCount": len(stages),
        "existingStages": [
            stage.name
            for stage in stages
            if assignments.get(stage.name, {}).get("stepName") == stage.name
        ],
        "reusedPlaceholders": [
            stage.name
            for stage in stages
            if assignments.get(stage.name, {}).get("stepName") == "未命名阶段"
        ],
        "toCreate": still_missing,
        "toUpdate": [stage.name for stage in stages if stage.name in assignments],
        "backgroundsMissing": [
            stage.name
            for stage in stages
            if not existing_background(assignments.get(stage.name))
        ],
        "apply": apply,
    }
    if not apply:
        return plan

    manifest = load_asset_manifest(manifest_path)
    created: list[str] = []
    updated: list[str] = []
    unchanged: list[str] = []
    uploaded_backgrounds: list[str] = []
    stage_ids: dict[str, str] = {}

    for stage in stages:
        existing = assignments.get(stage.name)
        if not existing:
            first_x = str(reference.get("positionX") or "570")
            first_y = int(reference.get("positionY") or 100)
            existing = client.create_placeholder(
                task_id,
                course_id=course_id,
                term=term,
                position_x=first_x,
                position_y=str(first_y + (stage.number - 1) * POSITION_GAP),
            )
            assignments[stage.name] = existing
        background, uploaded = ensure_background(
            client,
            stage=stage,
            background_file=background_files[stage.number],
            existing_step=existing,
            manifest=manifest,
            manifest_path=manifest_path,
        )
        if uploaded:
            uploaded_backgrounds.append(stage.name)
        payload = build_step_payload(
            reference,
            stage,
            task_id=task_id,
            role_ids=role_ids,
            background=background,
            existing_step=existing,
        )
        step_id = str(existing["nid"])
        stage_ids[stage.name] = step_id
        if editable_projection(existing) == payload:
            unchanged.append(stage.name)
        else:
            client.edit_step(payload)
            if stage.name in still_missing:
                created.append(stage.name)
            else:
                updated.append(stage.name)

    first_step_id = stage_ids[stages[0].name]
    task_detail = client.task_detail(task_id)
    first_step_updated = task_detail.get("firstStepId") != first_step_id
    if first_step_updated:
        client.edit_task(build_task_edit_payload(task_detail, first_step_id))

    verify_stage_cards(
        client,
        task_id=task_id,
        stages=stages,
        role_ids=role_ids,
        first_step_id=first_step_id,
    )
    return {
        **plan,
        "created": created,
        "updated": updated,
        "unchanged": unchanged,
        "uploadedBackgrounds": uploaded_backgrounds,
        "stageIds": stage_ids,
        "firstStepId": first_step_id,
        "firstStepUpdated": first_step_updated,
        "published": False,
        "verified": True,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="从 Pro Markdown 配置幂等创建简易数字X光任务的六张阶段卡片"
    )
    parser.add_argument("--task-id", default=DEFAULT_TASK_ID)
    parser.add_argument("--course-id", default=DEFAULT_COURSE_ID)
    parser.add_argument("--library-id", default=DEFAULT_LIBRARY_ID)
    parser.add_argument("--term", type=int, default=DEFAULT_TERM)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--background-dir", type=Path, default=DEFAULT_BACKGROUND_DIR)
    parser.add_argument("--asset-manifest", type=Path, default=DEFAULT_ASSET_MANIFEST)
    parser.add_argument("--expected-account", default=DEFAULT_EXPECTED_ACCOUNT)
    parser.add_argument("--env-file", default=str(PROJECT_ROOT / ".env"))
    parser.add_argument(
        "--apply",
        action="store_true",
        help="实际上传背景并创建/更新卡片；省略时只输出差异计划",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    load_dotenv(args.env_file, override=True)
    authorization = os.getenv("AUTHORIZATION", "").strip()
    cookie = os.getenv("COOKIE", "").strip()
    if not authorization or not cookie:
        raise RuntimeError(f"{args.env_file} 缺少 AUTHORIZATION 或 COOKIE")

    client = StageClient(authorization, cookie, timeout=60)
    result = configure_stage_cards(
        client,
        task_id=args.task_id,
        course_id=args.course_id,
        term=args.term,
        config_path=args.config,
        background_dir=args.background_dir,
        manifest_path=args.asset_manifest,
        expected_account=args.expected_account,
        apply=args.apply,
    )
    mode = "执行完成" if args.apply else "检查完成（未写入）"
    print(f"{mode}: {json.dumps(result, ensure_ascii=False, indent=2)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
