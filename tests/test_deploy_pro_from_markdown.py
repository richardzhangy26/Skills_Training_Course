from pathlib import Path

import pytest

from skill_training_pro import deploy_pro_from_markdown as deployer


def member(name: str, voice: str, voice_type: str, avatar: str):
    return deployer.MemberDeploymentSpec(
        nickname=name,
        role_name=f"{name}角色",
        description="角色描述",
        prompt="角色提示词" * 20,
        model_code="Doubao-Seed-2.0-pro",
        voice_nid=voice,
        voice_type=voice_type,
        avatar_nid=avatar,
        digital_human_name=name,
        skills=(),
    )


def test_parse_deployment_config_preserves_member_model() -> None:
    path = (
        Path(__file__).resolve().parents[1]
        / "skills_training_course"
        / "首都医科大学-护理管理学"
        / "被遗忘的等待-Pro配置.md"
    )

    _, members, _, _ = deployer.parse_deployment_config(path)

    assert {item.nickname: item.model_code for item in members} == {
        "陈老师": "Doubao-Seed-2.0-pro",
        "张先生": "Doubao-Seed-2.0-pro",
    }


def test_require_pro_task_id_rejects_normal_ability_task() -> None:
    with pytest.raises(ValueError, match="能力训练 Pro"):
        deployer.require_pro_task_id("8eDVMQB1MvCpLo9MRakN")


def test_build_editor_url_always_uses_pro_route() -> None:
    url = deployer.build_pro_editor_url(
        "course-1", "library-1", task_id="PRO-task-1"
    )

    assert "/ability-training-pro/create" in url
    assert "/ability-training/create" not in url
    assert "trainTaskId=PRO-task-1" in url


def test_create_task_payload_uses_current_numeric_communication_method() -> None:
    payload = deployer.build_create_task_payload(
        name="测试能力",
        description="测试描述",
        course_id="course-1",
        term=20271,
    )

    assert payload["communicateMethod"] == 3
    assert payload["extText"] == {
        "trainScreen": False,
        "trainScreenType": 1,
    }


def test_resolve_runtime_member_requires_unambiguous_existing_human() -> None:
    spec = member("张先生", "运行时解析", "运行时解析", "运行时解析")
    humans = [
        {
            "customNid": "human-1",
            "digitalHumanName": "张先生",
            "voiceNid": "voice-1",
            "voiceType": "voice-type-1",
            "avatarNid": "avatar-1",
        }
    ]

    resolved = deployer.resolve_member_resources(
        spec,
        humans,
        available_voice_ids={"voice-1"},
        available_avatar_ids={"avatar-1"},
    )

    assert resolved.custom_digital_human == "human-1"
    assert resolved.voice_nid == "voice-1"
    assert resolved.voice_type == "voice-type-1"
    assert resolved.avatar_nid == "avatar-1"


def test_resolve_runtime_member_rejects_ambiguous_humans() -> None:
    spec = member("张先生", "运行时解析", "运行时解析", "运行时解析")
    humans = [
        {
            "customNid": "human-1",
            "digitalHumanName": "张先生",
            "voiceNid": "voice-1",
            "avatarNid": "avatar-1",
        },
        {
            "customNid": "human-2",
            "digitalHumanName": "张先生",
            "voiceNid": "voice-1",
            "avatarNid": "avatar-2",
        },
    ]

    with pytest.raises(ValueError, match="多个同名数字人"):
        deployer.resolve_member_resources(
            spec,
            humans,
            available_voice_ids={"voice-1"},
            available_avatar_ids={"avatar-1", "avatar-2"},
        )


def test_resource_override_disambiguates_runtime_member() -> None:
    spec = member("张先生", "运行时解析", "运行时解析", "运行时解析")
    humans = [
        {
            "customNid": "human-1",
            "digitalHumanName": "张先生",
            "voiceNid": "voice-1",
            "voiceType": "voice-type-1",
            "avatarNid": "avatar-1",
        },
        {
            "customNid": "human-2",
            "digitalHumanName": "张先生",
            "voiceNid": "voice-2",
            "voiceType": "voice-type-2",
            "avatarNid": "avatar-2",
        },
    ]

    resolved = deployer.resolve_member_resources(
        spec,
        humans,
        available_voice_ids={"voice-1", "voice-2"},
        available_avatar_ids={"avatar-1", "avatar-2"},
        override={"customDigitalHuman": "human-2"},
    )

    assert resolved.custom_digital_human == "human-2"
    assert resolved.voice_nid == "voice-2"
    assert resolved.avatar_nid == "avatar-2"


def test_assign_stage_steps_reuses_ui_placeholder_before_creating() -> None:
    stages = [
        deployer.StageIdentity(1, "阶段一"),
        deployer.StageIdentity(2, "阶段二"),
    ]
    existing = [{"nid": "placeholder-1", "stepName": "未命名阶段"}]

    assignments, missing, removable = deployer.assign_stage_steps(stages, existing)

    assert assignments["阶段一"]["nid"] == "placeholder-1"
    assert missing == ["阶段二"]
    assert removable == []


def test_assign_stage_steps_marks_only_empty_surplus_placeholders_removable() -> None:
    stages = [deployer.StageIdentity(1, "阶段一")]
    existing = [
        {"nid": "stage-1", "stepName": "阶段一"},
        {
            "nid": "empty-placeholder",
            "stepName": "未命名阶段",
            "description": None,
            "llmPrompt": None,
        },
    ]

    assignments, missing, removable = deployer.assign_stage_steps(stages, existing)

    assert assignments["阶段一"]["nid"] == "stage-1"
    assert missing == []
    assert removable == ["empty-placeholder"]


def test_score_items_are_required_and_serialized_for_platform() -> None:
    with pytest.raises(ValueError, match="至少.*一条平台评价标准"):
        deployer.build_score_items_payload("PRO-task-1", [])

    payload = deployer.build_score_items_payload(
        "PRO-task-1",
        [
            {
                "name": "案例分析能力",
                "score": 45,
                "description": "评价案例分析表现",
                "requirement": "依据用户实际分析内容评分",
            },
            {
                "name": "实战互动能力",
                "score": 55,
                "description": "评价沟通实战表现",
                "requirement": "依据用户对家属的实际表达评分",
            },
        ],
    )

    assert payload["trainTaskNid"] == "PRO-task-1"
    assert [item["score"] for item in payload["items"]] == [45, 55]


def test_load_resource_map_rejects_missing_stage_background_and_score_items(
    tmp_path: Path,
) -> None:
    path = tmp_path / "resources.json"
    path.write_text('{"members": {}}', encoding="utf-8")

    with pytest.raises(ValueError, match="scoreItems"):
        deployer.load_resource_map(path, stage_names=["阶段一"])


def test_load_resource_map_requires_entrance_voice(tmp_path: Path) -> None:
    path = tmp_path / "resources.json"
    path.write_text(
        """{
          "scoreItems": [{
            "name": "综合表现",
            "score": 100,
            "description": "",
            "requirement": "依据实际表现评价"
          }],
          "stageBackgrounds": {
            "阶段一": {"fileId": "file-1", "fileUrl": "https://img/1.png"}
          }
        }""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="entranceVoice"):
        deployer.load_resource_map(path, stage_names=["阶段一"])


def test_load_resource_map_accepts_complete_minimum_mapping(tmp_path: Path) -> None:
    path = tmp_path / "resources.json"
    path.write_text(
        """{
          "scoreItems": [{
            "name": "综合表现",
            "score": 100,
            "description": "",
            "requirement": "依据实际表现评价"
          }],
          "stageBackgrounds": {
            "阶段一": {"fileId": "file-1", "fileUrl": "https://img/1.png"}
          },
          "entranceVoice": {
            "voiceNid": "voice-1",
            "voiceType": "voice-type-1",
            "speed": 1
          }
        }""",
        encoding="utf-8",
    )

    result = deployer.load_resource_map(path, stage_names=["阶段一"])

    assert result["entranceVoice"]["voiceNid"] == "voice-1"


def test_pro_task_cover_edit_value_is_the_asset_url() -> None:
    asset = {
        "fileId": "file-1",
        "fileUrl": "https://img.example/cover.png",
    }

    assert deployer.task_cover_edit_value(asset) == "https://img.example/cover.png"
