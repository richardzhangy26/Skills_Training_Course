from pathlib import Path

from skill_training_build import create_speaking_task_from_markdown as csm


ROOT_DIR = Path(__file__).resolve().parents[2]
SCRIPT_PATH = (
    ROOT_DIR
    / "skills_training_course"
    / "中南财经大学-大学英语"
    / "book_units_v2"
    / "book1_unit2_a_break_for_fun"
    / "English_Training_Script.md"
)
BOOK2_UNIT1_SCRIPT_PATH = (
    ROOT_DIR
    / "skills_training_course"
    / "中南财经大学-大学英语"
    / "book_units_v2"
    / "book2_unit1_life_is_a_learning_curve"
    / "English_Training_Script.md"
)


def test_parse_condition_rules_from_current_speaking_script() -> None:
    steps = csm.parse_markdown(SCRIPT_PATH)

    assert [step["stepName"] for step in steps] == [
        "Route Selection",
        "Situation 1 - Birthday Dinner Recommendation",
        "Situation 2 - Campus Part-Time Job Recommendation",
        "Task 3 - Two-Minute Opinion Speech",
    ]
    assert [len(step.get("flowRules", [])) for step in steps] == [3, 1, 1, 1]

    route_rule = steps[0]["flowRules"][0]
    assert route_rule["routeExit"] == "Situation 1"
    assert route_rule["outerRelation"] == "or"
    assert route_rule["groups"][0]["relation"] == "or"
    assert len(route_rule["groups"][0]["conditions"]) == 3


def test_route_exit_rules_map_to_target_steps_and_leaf_rules_map_to_end() -> None:
    steps = csm.parse_markdown(SCRIPT_PATH)
    flow_specs = csm.get_create_flow_specs(steps)

    assert len(flow_specs) == 7

    route_specs = [
        spec
        for spec in flow_specs
        if spec["sourceName"] == "Route Selection" and spec["flowSettingType"] == "configuration"
    ]
    assert [spec["targetName"] for spec in route_specs] == [
        "Situation 1 - Birthday Dinner Recommendation",
        "Situation 2 - Campus Part-Time Job Recommendation",
        "Task 3 - Two-Minute Opinion Speech",
    ]
    assert [spec["flowCondition"] for spec in route_specs] == [
        "Situation 1 - Birthday Dinner Recommendation",
        "Situation 2 - Campus Part-Time Job Recommendation",
        "Task 3 - Two-Minute Opinion Speech",
    ]
    assert [spec["isDefault"] for spec in route_specs] == [1, 0, 0]

    leaf_names = {
        "Situation 1 - Birthday Dinner Recommendation",
        "Situation 2 - Campus Part-Time Job Recommendation",
        "Task 3 - Two-Minute Opinion Speech",
    }
    leaf_specs = [spec for spec in flow_specs if spec["sourceName"] in leaf_names]
    assert len(leaf_specs) == 3
    assert all(spec["targetName"] == "END" for spec in leaf_specs)
    assert all(spec["flowCondition"] == "训练结束" for spec in leaf_specs)
    assert all(spec["flowSettingType"] == "configuration" for spec in leaf_specs)
    assert all(spec["isDefault"] == 1 for spec in leaf_specs)

    assert not any(
        spec["sourceName"] == "Situation 1 - Birthday Dinner Recommendation"
        and spec["targetName"] == "Situation 2 - Campus Part-Time Job Recommendation"
        for spec in flow_specs
    )
    assert not any(
        spec["sourceName"] == "Situation 2 - Campus Part-Time Job Recommendation"
        and spec["targetName"] == "Task 3 - Two-Minute Opinion Speech"
        for spec in flow_specs
    )


def test_condition_rule_configuration_payload_matches_platform_shape() -> None:
    steps = csm.parse_markdown(SCRIPT_PATH)
    flow_rule = steps[0]["flowRules"][0]

    payload = csm.build_edit_script_step_flow_payload(
        "task-1",
        "flow-1",
        "source-1",
        "target-1",
        "Situation 1 - Birthday Dinner Recommendation",
        flow_rule,
        transition_prompt="下一阶段开场白",
        is_default=0,
    )

    assert payload["flowSettingType"] == "configuration"
    assert payload["flowCondition"] == "Situation 1 - Birthday Dinner Recommendation"
    assert payload["transitionPrompt"] == "下一阶段开场白"
    assert payload["transitionHistoryNum"] == 10
    assert payload["isDefault"] == 0
    assert payload["flowConfiguration"]["relation"] == "or"

    group = payload["flowConfiguration"]["conditions"][0]
    assert group["text"] == "条件组1"
    assert group["relation"] == "or"
    assert group["isEdit"] is False
    assert group["conditions"] == [
        {"text": "The student has explicitly selected Situation 1 in this route-selection stage."},
        {
            "text": (
                "The student has explicitly said they want to practice the "
                "birthday-dinner recommendation roleplay in this route-selection stage."
            )
        },
        {
            "text": (
                "The student has explicitly chosen to ask for a restaurant "
                "recommendation in this route-selection stage."
            )
        },
    ]


def test_book2_unit1_transition_prompt_after_condition_rules_imports_to_flows() -> None:
    steps = csm.parse_markdown(BOOK2_UNIT1_SCRIPT_PATH)

    assert [len(step.get("flowRules", [])) for step in steps] == [3, 1, 1, 1]
    assert all(step.get("transitionPrompt") for step in steps)

    flow_specs = csm.get_create_flow_specs(steps)
    route_specs = [
        spec
        for spec in flow_specs
        if spec["sourceName"] == "Route Selection" and spec["flowSettingType"] == "configuration"
    ]

    assert [spec["isDefault"] for spec in route_specs] == [1, 0, 0]
    assert all(spec["transitionPrompt"] for spec in route_specs)
    assert all("${next_stage_opening}" not in spec["transitionPrompt"] for spec in route_specs)
    assert "Great, let's do Situation 1." in route_specs[0]["transitionPrompt"]
    assert "Great, let's do Situation 2." in route_specs[1]["transitionPrompt"]
    assert "Alright, let's do Task 3." in route_specs[2]["transitionPrompt"]

    leaf_specs = [
        spec
        for spec in flow_specs
        if spec["sourceName"] != "Route Selection"
        and spec["targetName"] == "END"
        and spec["flowSettingType"] == "configuration"
    ]
    assert len(leaf_specs) == 3
    assert all(spec["transitionPrompt"] == "" for spec in leaf_specs)


def test_create_script_flow_passes_transition_prompt_to_configuration_edit(monkeypatch) -> None:
    steps = csm.parse_markdown(BOOK2_UNIT1_SCRIPT_PATH)
    flow_rule = steps[0]["flowRules"][0]
    captured_payloads = []

    class DummyResponse:
        def json(self):
            return {"code": 200, "success": True}

    def fake_post(url, headers=None, json=None, timeout=None):
        captured_payloads.append({"url": url, "json": json})
        return DummyResponse()

    monkeypatch.setattr(csm.requests, "post", fake_post)
    monkeypatch.setattr(csm, "get_headers", lambda: {"Authorization": "token"})

    result = csm.create_script_flow(
        "task-1",
        "source-1",
        "target-1",
        "Situation 1 - Advice About an 18-Year-Old Son",
        "请直接输出下一阶段开场白",
        flow_rule=flow_rule,
        is_default=0,
    )

    assert result is True
    assert len(captured_payloads) == 2
    assert captured_payloads[0]["url"].endswith("/createScriptStepFlow")
    assert captured_payloads[1]["url"].endswith("/editScriptStepFlow")

    edit_payload = captured_payloads[1]["json"]
    assert edit_payload["flowSettingType"] == "configuration"
    assert edit_payload["transitionPrompt"] == "请直接输出下一阶段开场白"
    assert edit_payload["transitionHistoryNum"] == 10
    assert edit_payload["isDefault"] == 0
