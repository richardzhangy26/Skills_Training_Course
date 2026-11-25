import importlib
import importlib.util


def load_deployer():
    module_name = "skill_training_build.deploy_language_training"
    assert importlib.util.find_spec(module_name) is not None, (
        "A dedicated native oral-training deployer is required."
    )
    return importlib.import_module(module_name)


def test_dedicated_oral_deployer_builds_native_configuration_payload() -> None:
    deployer = load_deployer()
    payload = deployer.build_oral_configuration_edit_payload(
        {
            "trainTaskId": "task-1",
            "trainTaskName": "Oral Task",
            "description": "Description",
            "trainType": "voice",
            "trainTaskCover": {"fileId": "cover-1"},
            "trainTime": -1,
            "extConfig": {
                "trainSubType": "ability",
                "dialogueLanguage": "en",
                "translationAssistantEnabled": True,
            },
        },
        course_id="course-1",
    )

    assert payload["trainTaskId"] == "task-1"
    assert payload["trainSubType"] == "oral"
    assert "trainType" not in payload
    assert payload["extConfig"]["trainSubType"] == "oral"
    assert payload["extConfig"]["dialogueLanguage"] == "en"
    assert payload["extConfig"]["translationAssistantEnabled"] is True


def test_dedicated_oral_deployer_builds_native_step_payload() -> None:
    deployer = load_deployer()
    payload = deployer.build_oral_step_edit_payload(
        {
            "trainTaskId": "task-1",
            "stepId": "step-1",
            "stepDetailDTO": {
                "nodeType": "SCRIPT_NODE",
                "stepName": "Roleplay",
                "trainSubType": "ability",
                "stepExtProperty": {"backgroundTheme": "white"},
            },
            "positionDTO": {"x": 100, "y": 200},
        },
        course_id="course-1",
        library_id="library-1",
    )

    assert payload["courseId"] == "course-1"
    assert payload["libraryFolderId"] == "library-1"
    assert payload["stepDetailDTO"]["trainSubType"] == "oral"
    assert payload["stepDetailDTO"]["stepExtProperty"]["trainSubType"] == "oral"
    assert payload["stepDetailDTO"]["stepExtProperty"]["backgroundTheme"] == "white"
    assert payload["stepDetailDTO"]["agentId"] == "TgbLpKo08D"
    assert payload["stepDetailDTO"]["avatarNid"] == "6ikwydCEOp"
    assert payload["stepDetailDTO"]["agentVoiceId"] == (
        "en_female_sarah_new_conversation_wvae_bigtts"
    )
    assert payload["stepDetailDTO"]["customDigitalHuman"] == "3cNI5DCVT3"
    assert payload["stepDetailDTO"]["customDigitalHumanSpeechRate"] == 1


def test_dedicated_oral_deployer_overwrites_existing_digital_human() -> None:
    deployer = load_deployer()
    payload = deployer.build_oral_step_edit_payload(
        {
            "trainTaskId": "task-1",
            "stepId": "step-1",
            "stepDetailDTO": {
                "nodeType": "SCRIPT_NODE",
                "stepName": "Roleplay",
                "trainSubType": "oral",
                "agentId": "TTS2cuBjD",
                "avatarNid": "retztwDJCE",
                "agentVoiceId": "ICL_uranus_en_male_michael_tob",
                "customDigitalHuman": "w2Z8O4rt3V",
                "customDigitalHumanSpeechRate": 1,
                "stepExtProperty": {"backgroundTheme": "white"},
            },
        },
        course_id="course-1",
        library_id="library-1",
    )

    assert payload["stepDetailDTO"]["agentId"] == "TgbLpKo08D"
    assert payload["stepDetailDTO"]["avatarNid"] == "6ikwydCEOp"
    assert payload["stepDetailDTO"]["customDigitalHuman"] == "3cNI5DCVT3"


def test_dedicated_oral_deployer_uses_markdown_digital_human() -> None:
    deployer = load_deployer()
    payload = deployer.build_oral_step_edit_payload(
        {
            "trainTaskId": "task-1",
            "stepId": "step-1",
            "stepDetailDTO": {
                "nodeType": "SCRIPT_NODE",
                "stepName": "Roleplay",
                "trainSubType": "oral",
                "stepExtProperty": {},
            },
        },
        course_id="course-1",
        library_id="library-1",
        markdown_step={
            "stepName": "Roleplay",
            "agentId": "TTS2cuBjH",
            "avatarNid": "S7eyvPv3fb",
            "agentVoiceId": "en_male_tim_uranus_bigtts",
            "customDigitalHuman": "ZwSEJL9DOU",
            "customDigitalHumanSpeechRate": 1,
        },
    )

    assert payload["stepDetailDTO"]["agentId"] == "TTS2cuBjH"
    assert payload["stepDetailDTO"]["avatarNid"] == "S7eyvPv3fb"
    assert payload["stepDetailDTO"]["agentVoiceId"] == "en_male_tim_uranus_bigtts"
    assert payload["stepDetailDTO"]["customDigitalHuman"] == "ZwSEJL9DOU"


def test_oral_snapshot_validation_rejects_ability_task() -> None:
    deployer = load_deployer()
    errors = deployer.validate_oral_snapshot(
        {"trainSubType": "ability", "extConfig": {"trainSubType": "oral"}},
        [
            {
                "stepDetailDTO": {
                    "nodeType": "SCRIPT_START",
                    "stepExtProperty": {"trainSubType": "oral"},
                }
            }
        ],
        expected_business_steps=0,
    )

    assert "configuration.trainSubType must be oral" in errors


def test_oral_snapshot_validation_rejects_missing_digital_human() -> None:
    deployer = load_deployer()
    errors = deployer.validate_oral_snapshot(
        {"trainSubType": "oral", "extConfig": {"trainSubType": "oral"}},
        [
            {
                "stepId": "start",
                "stepDetailDTO": {
                    "nodeType": "SCRIPT_START",
                    "stepExtProperty": {"trainSubType": "oral"},
                },
            },
            {
                "stepId": "stage-1",
                "stepDetailDTO": {
                    "nodeType": "SCRIPT_NODE",
                    "stepExtProperty": {"trainSubType": "oral"},
                    "agentId": "",
                    "avatarNid": "",
                    "agentVoiceId": "",
                    "customDigitalHuman": "",
                },
            },
            {
                "stepId": "end",
                "stepDetailDTO": {
                    "nodeType": "SCRIPT_END",
                    "stepExtProperty": {"trainSubType": "oral"},
                },
            },
        ],
        expected_business_steps=1,
    )

    assert "step stage-1 is missing a complete digital-human profile" in errors


def test_build_oral_marking_business_config_uses_platform_module_defaults() -> None:
    deployer = load_deployer()
    business_config = deployer.build_oral_marking_business_config(
        [
            {
                "moduleKey": "grammatical_accuracy",
                "moduleName": "语法准确度",
                "config": '{"isOpen": true, "fullMark": 25}',
            },
            {
                "moduleKey": "mastery_theme",
                "moduleName": "主题掌握度",
                "config": '{"isOpen": false, "fullMark": 20}',
            },
        ]
    )

    assert business_config["grammatical_accuracy"] == {
        "isOpen": True,
        "fullMark": 25,
        "moduleName": "语法准确度",
        "isRealTime": True,
    }
    assert business_config["mastery_theme"] == {
        "isOpen": False,
        "fullMark": 20,
        "moduleName": "主题掌握度",
        "isRealTime": False,
    }


def test_language_training_url_includes_marking_instance() -> None:
    deployer = load_deployer()
    url = deployer.build_language_training_url(
        course_id="course-1",
        library_id="library-1",
        train_task_id="task-1",
        instance_nid="instance-1",
        version=3,
    )

    assert url == (
        "https://hike-teaching-center.polymas.com/agent-course-full/course-1/"
        "language-training/create?trainTaskId=task-1&instanceNid=instance-1&"
        "version=3&libraryId=library-1"
    )


def test_oral_snapshot_validation_rejects_missing_marking_instance() -> None:
    deployer = load_deployer()
    errors = deployer.validate_oral_snapshot(
        {
            "trainSubType": "oral",
            "extConfig": {"trainSubType": "oral"},
            "instanceNid": None,
        },
        [
            {
                "stepId": "start",
                "stepDetailDTO": {
                    "nodeType": "SCRIPT_START",
                    "stepExtProperty": {"trainSubType": "oral"},
                },
            },
            {
                "stepId": "end",
                "stepDetailDTO": {
                    "nodeType": "SCRIPT_END",
                    "stepExtProperty": {"trainSubType": "oral"},
                },
            },
        ],
        expected_business_steps=0,
    )

    assert "configuration.instanceNid is required for oral marking" in errors


def test_marking_publish_is_idempotent_when_instance_was_already_published(
    monkeypatch,
) -> None:
    deployer = load_deployer()

    class DummyResponse:
        def json(self):
            return {
                "code": 500,
                "success": False,
                "msg": "智能体实例已经发布过，不能重复发布",
            }

    monkeypatch.setattr(
        deployer.requests,
        "request",
        lambda *args, **kwargs: DummyResponse(),
    )
    monkeypatch.setattr(
        deployer.csm,
        "get_headers",
        lambda: {"Authorization": "token", "Cookie": "cookie"},
    )

    result = deployer.publish_oral_marking_instance(
        instance_nid="instance-1",
        course_id="course-1",
        library_id="library-1",
    )

    assert result["alreadyPublished"] is True


def test_oral_snapshot_validation_rejects_azure_tts_agent_id() -> None:
    deployer = load_deployer()
    errors = deployer.validate_oral_snapshot(
        {"trainSubType": "oral", "extConfig": {"trainSubType": "oral"}},
        [
            {
                "stepId": "stage-1",
                "stepDetailDTO": {
                    "nodeType": "SCRIPT_NODE",
                    "stepExtProperty": {"trainSubType": "oral"},
                    "agentId": "en-US-GuyNeural",
                    "avatarNid": "6ikwydCEOp",
                    "agentVoiceId": "en_female_sarah_new_conversation_wvae_bigtts",
                    "customDigitalHuman": "3cNI5DCVT3",
                },
            }
        ],
        expected_business_steps=1,
    )

    assert "step stage-1 is missing a complete digital-human profile" in errors
