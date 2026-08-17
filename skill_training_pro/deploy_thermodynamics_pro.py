#!/usr/bin/env python3
"""Deploy the thermodynamics museum Pro task to Polymas.

Reads the Pro configuration Markdown as the single source of truth and
performs, in order: portrait upload -> avatar sync -> named digital human
creation -> skill creation -> global member upsert -> stage card upsert ->
task description/entrance voice/firstStepId. Idempotent by member nickname,
skill name, digital-human (name + voice + avatar), step name and image hash.
No platform write occurs unless ``--apply`` is supplied; publishing requires
the explicit ``--publish`` flag and runs only after the post-deploy
verification passes.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from dotenv import load_dotenv

try:
    from skill_training_pro.configure_xray_pro_roles import (
        PolymasClient,
        extract_id,
        instruction_from_detail,
        normalize_list,
    )
    from skill_training_pro.create_xray_pro_stage_cards import (
        POSITION_GAP,
        StageClient,
        build_step_payload,
        build_task_edit_payload,
        ensure_background,
        file_sha256,
        find_background_file,
        inject_role_tags,
        load_asset_manifest,
        parse_stage_cards,
    )
except ModuleNotFoundError:  # Direct execution from skill_training_pro/.
    from configure_xray_pro_roles import (  # type: ignore[no-redef]
        PolymasClient,
        extract_id,
        instruction_from_detail,
        normalize_list,
    )
    from create_xray_pro_stage_cards import (  # type: ignore[no-redef]
        POSITION_GAP,
        StageClient,
        build_step_payload,
        build_task_edit_payload,
        ensure_background,
        file_sha256,
        find_background_file,
        inject_role_tags,
        load_asset_manifest,
        parse_stage_cards,
    )


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = (
    PROJECT_ROOT
    / "skills_training_course"
    / "skill_training_pro"
    / "天津大学-热力学"
    / "热力学名人博物馆沉浸式训练-Pro配置.md"
)
DEFAULT_BACKGROUND_DIR = DEFAULT_CONFIG_PATH.parent / "backgrounds"
DEFAULT_ASSET_MANIFEST = Path(__file__).with_name("thermodynamics_pro_assets.json")

DEFAULT_TASK_ID = "PRO10dbLxubBuEWcIYkJ"
DEFAULT_COURSE_ID = "87dB026lL5HYXvwrbDZ2"
DEFAULT_LIBRARY_ID = "q49MmIcbou"
DEFAULT_TERM = 20271
DEFAULT_EXPECTED_ACCOUNT = "天津省区"
MODEL_CODE = "Doubao-Seed-2.0-pro"
CUSTOM_SKILL_TYPE_NID = "a1b2c3d4e5"
ENTRANCE_VOICE_BY_NAME = {"灿灿": ("Tg2LpKo18D", "zh_female_cancan_mars_bigtts")}


@dataclass(frozen=True)
class SkillSpec:
    name: str
    description: str
    instruction: str


@dataclass(frozen=True)
class MemberSpec:
    nickname: str
    role_name: str
    description: str
    prompt: str
    voice_nid: str
    voice_type: str
    digital_human_name: str
    skills: tuple[SkillSpec, ...]


@dataclass(frozen=True)
class GlobalSpec:
    description: str
    entrance_voice_name: str


def member_field(block: str, name: str) -> str:
    match = re.search(rf"^- \*\*{re.escape(name)}\*\*:\s*(.*)$", block, re.MULTILINE)
    if not match:
        raise ValueError(f"成员配置缺少字段：{name}")
    return match.group(1).strip()


def global_field(text: str, name: str) -> str:
    match = re.search(rf"^- \*\*{re.escape(name)}\*\*:\s*(.*)$", text, re.MULTILINE)
    return match.group(1).strip() if match else ""


def parse_members(config_path: Path) -> tuple[GlobalSpec, list[MemberSpec]]:
    text = config_path.read_text(encoding="utf-8")
    global_spec = GlobalSpec(
        description=global_field(text, "描述"),
        entrance_voice_name=global_field(text, "入场音色"),
    )
    if not global_spec.description:
        raise ValueError("全局配置缺少描述")

    members: list[MemberSpec] = []
    matches = list(re.finditer(r"^### 成员\d+:\s*(.+?)\s*$", text, re.MULTILINE))
    if not matches:
        raise ValueError("配置中没有成员")
    for index, match in enumerate(matches):
        end = (
            matches[index + 1].start()
            if index + 1 < len(matches)
            else text.index("## 训练剧本")
        )
        block = text[match.start() : end]
        nickname = match.group(1).strip()

        skills: list[SkillSpec] = []
        skill_pattern = re.compile(
            r"-\s*(?P<name>[^|\n]+?)\s*\|\s*类型:\s*custom_skill\s*\|\s*描述:\s*(?P<desc>[^\n]+?)\s*\n"
            r"\s*<skill_instruction>(?P<instruction>.*?)</skill_instruction>",
            re.DOTALL,
        )
        for skill_match in skill_pattern.finditer(block):
            skills.append(
                SkillSpec(
                    name=skill_match.group("name").strip(),
                    description=skill_match.group("desc").strip(),
                    instruction=textwrap.dedent(
                        skill_match.group("instruction")
                    ).strip(),
                )
            )
        if not skills:
            raise ValueError(f"成员 {nickname} 没有解析到技能")

        members.append(
            MemberSpec(
                nickname=nickname,
                role_name=member_field(block, "角色名称"),
                description=member_field(block, "角色描述"),
                prompt=member_field(block, "角色提示词"),
                voice_nid=member_field(block, "声音资源ID"),
                voice_type=member_field(block, "声音参数"),
                digital_human_name=member_field(block, "数字人名称"),
                skills=tuple(skills),
            )
        )
    return global_spec, members


def load_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"images": {}}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data.get("images"), dict):
        raise ValueError(f"资产清单格式错误：{path}")
    return data


def save_manifest(path: Path, manifest: Mapping[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


class DeployClient(StageClient):
    def save_avatar(self, user_nid: str, image_url: str) -> str:
        data = self.request(
            "POST",
            "/ai-profile/ai_avatar/saveAndSyncResource",
            payload={
                "userNid": user_nid,
                "avatarUrl": image_url,
                "avatarDynamicUrl": image_url,
                "sync": False,
            },
        )
        avatar_nid = extract_id(data, "avatarNid", "nid")
        if not avatar_nid:
            raise RuntimeError("形象同步响应缺少 avatarNid")
        return avatar_nid

    def publish_task(self, task_id: str, course_id: str, library_id: str) -> None:
        self.request(
            "POST",
            "/ai-platform/ability-train/tasks/publish",
            payload={
                "courseId": course_id,
                "taskId": task_id,
                "libraryFolderId": library_id,
            },
        )


def ensure_avatar(
    client: DeployClient,
    *,
    user_nid: str,
    image_path: Path,
    manifest: dict[str, Any],
    manifest_path: Path,
    apply: bool,
) -> str:
    from skill_training_pro.create_xray_pro_stage_cards import file_sha256

    checksum = file_sha256(image_path)
    cached = manifest["images"].get(checksum) or {}
    if cached.get("avatarNid"):
        return str(cached["avatarNid"])
    if not apply:
        return ""
    if not cached.get("fileId"):
        uploaded = client.upload_background(image_path)
        cached.update({"source": str(image_path), **uploaded})
    avatar_nid = client.save_avatar(user_nid, str(cached["fileUrl"]))
    cached["avatarNid"] = avatar_nid
    manifest["images"][checksum] = cached
    save_manifest(manifest_path, manifest)
    return avatar_nid


def find_exact_digital_human(
    owners: Sequence[Mapping[str, Any]],
    *,
    name: str,
    voice_nid: str,
    avatar_nid: str,
) -> str:
    for owner in owners:
        owner_name = owner.get("digitalHumanName") or owner.get("name")
        if (
            owner_name == name
            and owner.get("voiceNid") == voice_nid
            and owner.get("avatarNid") == avatar_nid
        ):
            return extract_id(owner, "customNid", "digitalHumanNid", "nid")
    return ""


def ensure_skill(
    client: DeployClient,
    task_id: str,
    spec: SkillSpec,
    existing_skills: list[dict[str, Any]],
) -> tuple[str, bool]:
    existing = next((item for item in existing_skills if item.get("name") == spec.name), None)
    if existing:
        return str(existing["nid"]), False
    payload = {
        "trainTaskNid": task_id,
        "typeNid": CUSTOM_SKILL_TYPE_NID,
        "name": spec.name,
        "packageName": spec.name,
        "description": spec.description,
        "businessConfig": None,
        "instruction": spec.instruction,
    }
    skill_id = client.create_skill(payload)
    existing_skills.append({"nid": skill_id, "name": spec.name})
    return skill_id, True


def build_role_payload(
    task_id: str,
    spec: MemberSpec,
    *,
    skill_ids: Sequence[str],
    avatar_nid: str,
    custom_digital_human: str,
) -> dict[str, Any]:
    return {
        "trainTaskNid": task_id,
        "nickname": spec.nickname,
        "roleName": spec.role_name,
        "modelCode": MODEL_CODE,
        "prompt": spec.prompt,
        "voiceNid": spec.voice_nid,
        "voiceType": spec.voice_type,
        "voiceSpeed": 1,
        "avatarNid": avatar_nid,
        "customDigitalHuman": custom_digital_human,
        "description": spec.description,
        "skills": ",".join(skill_ids),
        "searchEngine": 0,
        "knowledgeSearch": 0,
        "knowledgeFileIds": [],
    }


def upsert_role(
    client: DeployClient,
    task_id: str,
    spec: MemberSpec,
    *,
    skill_ids: Sequence[str],
    avatar_nid: str,
    custom_digital_human: str,
    existing_roles: list[dict[str, Any]],
) -> tuple[str, bool]:
    payload = build_role_payload(
        task_id,
        spec,
        skill_ids=skill_ids,
        avatar_nid=avatar_nid,
        custom_digital_human=custom_digital_human,
    )
    existing = next(
        (item for item in existing_roles if item.get("nickname") == spec.nickname), None
    )
    if existing:
        payload["nid"] = existing["nid"]
        client.edit_role(payload)
        return str(existing["nid"]), False
    role_id = client.create_role(payload)
    existing_roles.append({"nid": role_id, "nickname": spec.nickname})
    return role_id, True


def upsert_step(
    client: DeployClient,
    *,
    task_id: str,
    course_id: str,
    term: int,
    stage: Any,
    role_ids: Mapping[str, str],
    background: Mapping[str, str],
    existing_steps: list[dict[str, Any]],
) -> tuple[str, bool]:
    existing = next(
        (item for item in existing_steps if item.get("stepName") == stage.name), None
    )
    if existing is None:
        placeholder = client.create_placeholder(
            task_id,
            course_id=course_id,
            term=term,
            position_x="570",
            position_y=str(100 + (stage.number - 1) * POSITION_GAP),
        )
        refreshed = next(
            (item for item in client.list_steps(task_id) if str(item.get("nid")) == str(placeholder["nid"])),
            None,
        )
        existing = refreshed or placeholder
        existing_steps.append(existing)
        created = True
    else:
        created = False

    payload = build_step_payload(
        existing,
        stage,
        task_id=task_id,
        role_ids=role_ids,
        background=background,
        existing_step=existing,
    )
    client.edit_step(payload)
    existing.update(payload)
    return str(existing["nid"]), created


def ensure_task_meta(
    client: DeployClient,
    *,
    task_id: str,
    global_spec: GlobalSpec,
    first_step_id: str,
) -> bool:
    detail = client.task_detail(task_id)
    payload = build_task_edit_payload(detail, first_step_id)
    entrance = ENTRANCE_VOICE_BY_NAME.get(global_spec.entrance_voice_name)
    if entrance:
        payload["entranceVoiceNid"] = entrance[0]
        payload["entranceVoiceType"] = entrance[1]
        payload["entranceVoiceSpeed"] = 1
    payload["description"] = global_spec.description
    if all(payload.get(key) == detail.get(key) for key in payload):
        return False
    client.edit_task(payload)
    return True


def verify_deployment(
    client: DeployClient,
    *,
    task_id: str,
    members: Sequence[MemberSpec],
    stages: Sequence[Any],
    role_ids: Mapping[str, str],
    expected_custom: Mapping[str, str],
    first_step_id: str,
    global_spec: GlobalSpec,
    initial_publish_status: Any,
) -> None:
    errors: list[str] = []
    roles = client.list_roles(task_id)
    role_by_name = {item.get("nickname"): item for item in roles}
    skills = client.list_skills(task_id)
    skill_by_name = {item.get("name"): item for item in skills}

    for spec in members:
        listed = role_by_name.get(spec.nickname)
        if not listed:
            errors.append(f"成员列表缺少 {spec.nickname}")
            continue
        detail = client.role_detail(str(listed["nid"]))
        for field, expected in (
            ("voiceNid", spec.voice_nid),
            ("voiceType", spec.voice_type),
            ("roleName", spec.role_name),
        ):
            if detail.get(field) != expected:
                errors.append(f"{spec.nickname}.{field} 回查不一致")
        if str(detail.get("customDigitalHuman") or "") != expected_custom.get(spec.nickname, ""):
            errors.append(f"{spec.nickname}.customDigitalHuman 回查不一致")
        if not detail.get("avatarNid"):
            errors.append(f"{spec.nickname}.avatarNid 为空")
        if len(str(detail.get("prompt") or "")) < 100:
            errors.append(f"{spec.nickname}.prompt 长度异常")
        actual_skill_names = {
            item.get("name") for item in (detail.get("skillList") or []) if isinstance(item, dict)
        }
        if actual_skill_names != {skill.name for skill in spec.skills}:
            errors.append(f"{spec.nickname} 技能不一致: {sorted(actual_skill_names)}")
        for skill_spec in spec.skills:
            listed_skill = skill_by_name.get(skill_spec.name)
            if not listed_skill:
                errors.append(f"技能列表缺少 {skill_spec.name}")
                continue
            skill_detail = client.skill_detail(str(listed_skill["nid"]))
            if instruction_from_detail(skill_detail).strip() != skill_spec.instruction.strip():
                errors.append(f"技能指令回查不一致: {skill_spec.name}")

    steps = client.list_steps(task_id)
    step_by_name = {step.get("stepName"): step for step in steps}
    for stage in stages:
        step = step_by_name.get(stage.name)
        if not step:
            errors.append(f"步骤列表缺少 {stage.name}")
            continue
        ext_config = step.get("extConfig") or {}
        prompt = str(step.get("llmPrompt") or "")
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
        for name, role_id in role_ids.items():
            if re.search(rf"@{re.escape(name)}(?![A-Za-z0-9_])", prompt):
                errors.append(f"{stage.name} 仍含 @{name}")
            if f"@{name}" in stage.prompt and f"<role>{role_id}</role>" not in prompt:
                errors.append(f"{stage.name} 缺少 {name} 的角色引用")

    task = client.task_detail(task_id)
    if task.get("firstStepId") != first_step_id:
        errors.append("任务 firstStepId 回查不一致")
    if task.get("description") != global_spec.description:
        errors.append("任务描述回查不一致")
    if task.get("publishStatus") != initial_publish_status:
        errors.append("任务发布状态发生了变化")

    if errors:
        raise RuntimeError("部署回查失败:\n- " + "\n- ".join(errors))


def deploy(
    client: DeployClient,
    *,
    task_id: str,
    course_id: str,
    library_id: str,
    term: int,
    config_path: Path,
    background_dir: Path,
    manifest_path: Path,
    expected_account: str,
    apply: bool,
    publish: bool,
) -> dict[str, Any]:
    user = client.current_user()
    account = str(user.get("realName") or user.get("nickName") or "")
    user_nid = str(user.get("userNid") or "")
    if not user_nid:
        raise RuntimeError("当前用户响应缺少 userNid")
    if expected_account and account != expected_account:
        raise RuntimeError(f"账号校验失败：当前为“{account}”，期望“{expected_account}”")

    global_spec, members = parse_members(config_path)
    stages = parse_stage_cards(config_path)

    roles = client.list_roles(task_id)
    skills = client.list_skills(task_id)
    steps = client.list_steps(task_id)
    voices = client.list_voices(course_id)
    owners = client.list_digital_humans(user_nid, course_id, library_id)

    voice_ids = {str(item.get("nid")) for item in voices}
    missing_voices = {spec.voice_nid for spec in members} - voice_ids
    if missing_voices:
        raise RuntimeError(f"当前账号声音库缺少 ID: {', '.join(sorted(missing_voices))}")

    portrait_paths = {}
    background_paths = {}
    for spec in members:
        path = background_dir / f"avatar_{spec.nickname}.png"
        if not path.exists():
            raise RuntimeError(f"缺少形象图：{path}（先运行 generate_thermodynamics_images.py）")
        portrait_paths[spec.nickname] = path
    for stage in stages:
        background_paths[stage.number] = find_background_file(background_dir, stage.number)

    plan: dict[str, Any] = {
        "account": account,
        "taskId": task_id,
        "members": [spec.nickname for spec in members],
        "stages": [stage.name for stage in stages],
        "existingRoleNames": [item.get("nickname") for item in roles],
        "existingStepNames": [item.get("stepName") for item in steps],
        "apply": apply,
    }
    if not apply:
        return plan

    initial_publish_status = client.task_detail(task_id).get("publishStatus")
    manifest = load_manifest(manifest_path)
    role_ids: dict[str, str] = {}
    custom_ids: dict[str, str] = {}
    created_avatars: list[str] = []
    created_humans: list[str] = []
    created_skills: list[str] = []
    created_roles: list[str] = []

    for spec in members:
        avatar_nid = ensure_avatar(
            client,
            user_nid=user_nid,
            image_path=portrait_paths[spec.nickname],
            manifest=manifest,
            manifest_path=manifest_path,
            apply=apply,
        )
        if not avatar_nid:
            raise RuntimeError(f"{spec.nickname} 形象同步失败")

        custom_id = find_exact_digital_human(
            owners,
            name=spec.digital_human_name,
            voice_nid=spec.voice_nid,
            avatar_nid=avatar_nid,
        )
        if not custom_id:
            custom_id = client.create_digital_human(
                {
                    "userNid": user_nid,
                    "type": "NORMAL",
                    "voiceNid": spec.voice_nid,
                    "avatarNid": avatar_nid,
                    "digitalHumanName": spec.digital_human_name,
                }
            )
            owners.append(
                {
                    "customNid": custom_id,
                    "digitalHumanName": spec.digital_human_name,
                    "voiceNid": spec.voice_nid,
                    "avatarNid": avatar_nid,
                }
            )
            created_humans.append(spec.digital_human_name)

        skill_ids: list[str] = []
        for skill_spec in spec.skills:
            skill_id, created = ensure_skill(client, task_id, skill_spec, skills)
            skill_ids.append(skill_id)
            if created:
                created_skills.append(skill_spec.name)

        role_id, created = upsert_role(
            client,
            task_id,
            spec,
            skill_ids=skill_ids,
            avatar_nid=avatar_nid,
            custom_digital_human=custom_id,
            existing_roles=roles,
        )
        role_ids[spec.nickname] = role_id
        custom_ids[spec.nickname] = custom_id
        if created:
            created_roles.append(spec.nickname)

    from skill_training_pro.create_xray_pro_stage_cards import (
        ensure_background,
        load_asset_manifest,
        save_asset_manifest,
    )

    background_manifest_path = manifest_path.with_name("thermodynamics_pro_backgrounds.json")
    background_manifest = load_asset_manifest(background_manifest_path)
    created_steps: list[str] = []
    updated_steps: list[str] = []
    stage_ids: dict[str, str] = {}
    for stage in stages:
        background, uploaded = ensure_background(
            client,
            stage=stage,
            background_file=background_paths[stage.number],
            existing_step=next(
                (item for item in steps if item.get("stepName") == stage.name), None
            ),
            manifest=background_manifest,
            manifest_path=background_manifest_path,
        )
        step_id, created = upsert_step(
            client,
            task_id=task_id,
            course_id=course_id,
            term=term,
            stage=stage,
            role_ids=role_ids,
            background=background,
            existing_steps=steps,
        )
        stage_ids[stage.name] = step_id
        (created_steps if created else updated_steps).append(stage.name)

    first_step_id = stage_ids[stages[0].name]
    task_meta_updated = ensure_task_meta(
        client,
        task_id=task_id,
        global_spec=global_spec,
        first_step_id=first_step_id,
    )

    verify_deployment(
        client,
        task_id=task_id,
        members=members,
        stages=stages,
        role_ids=role_ids,
        expected_custom=custom_ids,
        first_step_id=first_step_id,
        global_spec=global_spec,
        initial_publish_status=initial_publish_status,
    )

    published = False
    if publish:
        client.publish_task(task_id, course_id, library_id)
        status = client.task_detail(task_id).get("publishStatus")
        if status in (0, None):
            raise RuntimeError(f"发布后回查 publishStatus 异常: {status!r}")
        published = True

    return {
        **plan,
        "roleIds": role_ids,
        "customDigitalHumans": custom_ids,
        "createdAvatars": created_avatars,
        "createdDigitalHumans": created_humans,
        "createdSkills": created_skills,
        "createdRoles": created_roles,
        "createdSteps": created_steps,
        "updatedSteps": updated_steps,
        "stageIds": stage_ids,
        "firstStepId": first_step_id,
        "taskMetaUpdated": task_meta_updated,
        "published": published,
        "verified": True,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="部署热力学名人博物馆 Pro 任务的数字人、成员与阶段卡片"
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
        help="实际写入平台数据；省略时仅检查并输出计划",
    )
    parser.add_argument(
        "--publish",
        action="store_true",
        help="部署并回查通过后发布任务（tasks/publish），需与 --apply 一起使用",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.publish and not args.apply:
        raise RuntimeError("--publish 必须与 --apply 一起使用")
    load_dotenv(args.env_file, override=True)
    authorization = os.getenv("AUTHORIZATION", "").strip()
    cookie = os.getenv("COOKIE", "").strip()
    if not authorization or not cookie:
        raise RuntimeError(f"{args.env_file} 缺少 AUTHORIZATION 或 COOKIE")

    client = DeployClient(authorization, cookie, timeout=60)
    result = deploy(
        client,
        task_id=args.task_id,
        course_id=args.course_id,
        library_id=args.library_id,
        term=args.term,
        config_path=args.config,
        background_dir=args.background_dir,
        manifest_path=args.asset_manifest,
        expected_account=args.expected_account,
        apply=args.apply,
        publish=args.publish,
    )
    mode = "执行完成" if args.apply else "检查完成（未写入）"
    print(f"{mode}: {json.dumps(result, ensure_ascii=False, indent=2)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
