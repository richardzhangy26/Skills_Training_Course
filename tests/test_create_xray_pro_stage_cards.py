from copy import deepcopy
from pathlib import Path

from skill_training_pro import create_xray_pro_stage_cards as cards


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = (
    PROJECT_ROOT
    / "skills_training_course"
    / "临沂大学-单片机原理与应用"
    / "简易数字X光成像模拟系统单片机开发实训-Pro配置.md"
)


def test_parse_stage_cards_reads_all_six_stages() -> None:
    stages = cards.parse_stage_cards(CONFIG_PATH)

    assert [stage.number for stage in stages] == [1, 2, 3, 4, 5, 6]
    assert stages[0].name == "绪论与研发背景问答"
    assert stages[-1].name == "系统总结、缺陷与优化拓展"
    assert stages[1].user_role_name == "系统方案设计学生工程师"
    assert stages[1].user_assign_name == "用户"
    assert "【完整执行流程】" in stages[1].prompt


def test_inject_role_tags_replaces_members_adds_user_and_removes_jump_wording() -> None:
    prompt = (
        "【阶段触发条件】\n满足条件。\n\n【背景设定】\n"
        "@陈工请@林医生和@老周发言。达成结束条件后，跳转到【下一阶段】阶段"
    )

    result = cards.inject_role_tags(
        prompt,
        {"陈工": "role-chen", "林医生": "role-lin", "老周": "role-zhou"},
    )

    assert "@陈工" not in result
    assert "@林医生" not in result
    assert "@老周" not in result
    assert "跳转到【" not in result
    assert "达成结束条件后，结束本阶段" in result
    assert result.count("<role>user</role>") == 1
    assert "<role>role-chen</role>" in result
    assert "<role>role-lin</role>" in result
    assert "<role>role-zhou</role>" in result


def test_inject_role_tags_replaces_explicit_user_mention() -> None:
    prompt = (
        "【阶段触发条件】\n满足条件。\n\n【背景设定】\n"
        "@陈工 提问并等待@用户 回答，随后由@用户 完成选择。"
    )

    result = cards.inject_role_tags(prompt, {"陈工": "role-chen"})

    assert "@用户" not in result
    assert result.count("<role>user</role>") == 2
    assert "<role>role-chen</role>" in result


def test_build_step_payload_clones_reference_and_overrides_stage_fields() -> None:
    reference = {
        "nid": "stage-1",
        "trainTaskNid": "task-1",
        "stepName": "旧名称",
        "description": "旧描述",
        "modelCode": "old-model",
        "llmPrompt": "old-prompt",
        "skills": None,
        "positionX": "570",
        "positionY": "100",
        "voiceNid": None,
        "voiceSpeed": None,
        "voiceType": None,
        "avatarNid": None,
        "customDigitalHuman": None,
        "timeLimit": -1,
        "useWhiteboard": 0,
        "isSkipStep": 1,
        "isNeedBegin": 1,
        "isTransition": 0,
        "flowHideSubtitle": 0,
        "extConfig": {
            "userRoleName": "旧角色",
            "userNameType": 2,
            "userAssignName": "同学",
            "userDescription": "旧描述",
            "bgMediaType": 1,
            "bgMedia": None,
            "bgMediaId": None,
            "bgMediaVolume": 80,
            "flowUseAside": None,
        },
    }
    original = deepcopy(reference)
    stage = cards.StageCard(
        number=2,
        name="阶段二",
        description="阶段二描述",
        user_role_name="方案设计学生",
        user_assign_name="用户",
        user_description="用户职责",
        model_code="Doubao-Seed-2.0-pro",
        skippable=False,
        prompt="@陈工主持。",
        background_description="背景",
    )

    payload = cards.build_step_payload(
        reference,
        stage,
        task_id="task-1",
        role_ids={"陈工": "role-chen"},
        background={"fileId": "file-2", "fileUrl": "https://img/2.png"},
        existing_step=None,
    )

    assert "nid" not in payload
    assert payload["stepName"] == "阶段二"
    assert payload["positionX"] == "570"
    assert payload["positionY"] == "400"
    assert payload["isSkipStep"] == 0
    assert payload["timeLimit"] == -1
    assert payload["llmPrompt"].count("<role>user</role>") == 1
    assert payload["extConfig"]["userRoleName"] == "方案设计学生"
    assert payload["extConfig"]["userDescription"] == "用户职责"
    assert payload["extConfig"]["bgMediaId"] == "file-2"
    assert payload["extConfig"]["flowUseAside"] is None
    assert reference == original


def test_build_step_payload_accepts_decimal_reference_positions() -> None:
    reference = {
        "positionX": "557.0628173733919",
        "positionY": "211.5",
        "extConfig": {},
    }
    stage = cards.StageCard(
        2, "阶段二", "描述", "用户角色", "用户", "职责", "model", False, "提示词", "背景"
    )

    payload = cards.build_step_payload(
        reference,
        stage,
        task_id="task-1",
        role_ids={},
        background={"fileId": "file-2", "fileUrl": "https://img/2.png"},
        existing_step=None,
    )

    assert payload["positionX"] == "557.0628173733919"
    assert payload["positionY"] == "511.5"


def test_build_step_payload_preserves_existing_decimal_position() -> None:
    existing = {
        "nid": "stage-2",
        "positionX": "557.0628173733919",
        "positionY": "511.5",
        "extConfig": {},
    }
    stage = cards.StageCard(
        2, "阶段二", "描述", "用户角色", "用户", "职责", "model", False, "提示词", "背景"
    )

    payload = cards.build_step_payload(
        existing,
        stage,
        task_id="task-1",
        role_ids={},
        background={"fileId": "file-2", "fileUrl": "https://img/2.png"},
        existing_step=existing,
    )

    assert payload["positionX"] == "557.0628173733919"
    assert payload["positionY"] == "511.5"


def test_assign_existing_steps_reuses_unnamed_placeholder() -> None:
    stages = [
        cards.StageCard(1, "阶段一", "", "", "", "", "model", False, "", ""),
        cards.StageCard(2, "阶段二", "", "", "", "", "model", False, "", ""),
        cards.StageCard(3, "阶段三", "", "", "", "", "model", False, "", ""),
    ]
    existing = [
        {"nid": "step-1", "stepName": "阶段一"},
        {"nid": "placeholder", "stepName": "未命名阶段"},
    ]

    assignments, still_missing = cards.assign_existing_steps(stages, existing)

    assert assignments["阶段一"]["nid"] == "step-1"
    assert assignments["阶段二"]["nid"] == "placeholder"
    assert "阶段三" in still_missing


def test_build_task_edit_payload_preserves_task_configuration() -> None:
    detail = {
        "trainTaskId": "task-1",
        "trainTaskName": "任务",
        "description": "描述",
        "trainTaskCover": "cover",
        "trainTime": None,
        "publishStatus": 0,
        "voiceUrl": "voice.mp3",
        "openSubtitle": 0,
        "openVideo": 0,
        "communicateMethod": 3,
        "entranceVoiceType": None,
        "entranceVoiceSpeed": 0.0,
        "entranceVoiceNid": None,
        "firstStepId": None,
        "serverOnly": "omit",
    }

    payload = cards.build_task_edit_payload(detail, "stage-1")

    assert payload["firstStepId"] == "stage-1"
    assert payload["communicateMethod"] == 3
    assert payload["voiceUrl"] == "voice.mp3"
    assert "serverOnly" not in payload


def test_build_placeholder_payload_uses_full_pro_card_shape() -> None:
    payload = cards.build_placeholder_payload(
        "task-1",
        course_id="course-1",
        term=20271,
        position_x="570",
        position_y="700",
    )

    assert payload["trainTaskNid"] == "task-1"
    assert payload["stepName"] == "未命名阶段"
    assert payload["courseId"] == "course-1"
    assert payload["term"] == 20271
    assert payload["positionY"] == "700"
    assert payload["isSkipStep"] == 0
    assert payload["extConfig"]["bgMediaTheme"] == "white"
    assert payload["extConfig"]["transitionBgMediaType"] == 1
