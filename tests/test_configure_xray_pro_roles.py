from copy import deepcopy

from skill_training_pro import configure_xray_pro_roles as config


class FakeClient:
    def __init__(self):
        self.created_skills = []
        self.created_roles = []
        self.edited_roles = []

    def create_skill(self, payload):
        self.created_skills.append(payload)
        return f"skill-{len(self.created_skills)}"

    def create_role(self, payload):
        self.created_roles.append(payload)
        return f"role-{len(self.created_roles)}"

    def edit_role(self, payload):
        self.edited_roles.append(payload)
        return payload["nid"]


def test_replace_role_mentions_replaces_all_exact_mentions() -> None:
    prompt = "@林医生先提问；@老周反馈。不要改 @林医生助理。"

    result = config.replace_role_mentions(
        prompt,
        {"林医生": "role-lin", "老周": "role-zhou"},
    )

    assert result == (
        "<role>role-lin</role>先提问；<role>role-zhou</role>反馈。"
        "不要改 @林医生助理。"
    )


def test_build_step_edit_payload_preserves_existing_fields() -> None:
    existing = {
        "nid": "step-1",
        "trainTaskNid": "task-1",
        "stepName": "阶段一",
        "description": "原描述",
        "llmPrompt": "请 @林医生 和 @老周 发言",
        "modelCode": "Doubao-Seed-2.0-pro",
        "skills": "skill-a",
        "skillList": [{"nid": "skill-a"}],
        "positionX": "570",
        "positionY": "100",
        "voiceNid": None,
        "voiceSpeed": None,
        "voiceType": None,
        "avatarNid": None,
        "customDigitalHuman": None,
        "timeLimit": -1,
        "useWhiteboard": 0,
        "isSkipStep": 0,
        "isNeedBegin": 1,
        "isTransition": 0,
        "flowHideSubtitle": 0,
        "extConfig": {"userRoleName": "学生", "bgMedia": "cover.png"},
        "serverOnlyField": "must-not-be-sent",
    }
    original = deepcopy(existing)

    payload = config.build_step_edit_payload(
        existing,
        {"林医生": "role-lin", "老周": "role-zhou"},
    )

    assert payload["llmPrompt"] == (
        "请 <role>role-lin</role> 和 <role>role-zhou</role> 发言"
    )
    assert payload["skills"] == "skill-a"
    assert payload["extConfig"] == existing["extConfig"]
    assert payload["positionX"] == "570"
    assert "serverOnlyField" not in payload
    assert existing == original


def test_ensure_skill_reuses_same_name() -> None:
    client = FakeClient()
    spec = config.SkillSpec("技能甲", "描述", "指令")
    existing = [{"nid": "existing-skill", "name": "技能甲"}]

    skill_id, created = config.ensure_skill(
        client,
        "task-1",
        "custom-type",
        spec,
        existing,
    )

    assert skill_id == "existing-skill"
    assert created is False
    assert client.created_skills == []


def test_upsert_role_edits_same_nickname_instead_of_creating() -> None:
    client = FakeClient()
    spec = config.RoleSpec(
        nickname="林医生",
        role_name="影像科医生",
        description="角色描述",
        prompt="角色提示词",
        voice_nid="voice-1",
        voice_type="voice-param",
        avatar_nid="avatar-1",
        digital_human_name="林医生",
        skills=(),
    )
    existing = [{"nid": "role-lin", "nickname": "林医生"}]

    role_id, created = config.upsert_role(
        client,
        "task-1",
        spec,
        skill_ids=["skill-1"],
        custom_digital_human="human-1",
        existing_roles=existing,
    )

    assert role_id == "role-lin"
    assert created is False
    assert client.created_roles == []
    assert client.edited_roles[0]["skills"] == "skill-1"
    assert client.edited_roles[0]["customDigitalHuman"] == "human-1"
