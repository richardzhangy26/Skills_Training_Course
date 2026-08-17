from skill_training_build import create_speaking_task_from_markdown as cstm


def make_rule(route_exit: str = "") -> dict:
    return {
        "routeExit": route_exit,
        "outerRelation": "or",
        "groups": [
            {
                "number": 1,
                "relation": "or",
                "conditions": [
                    "The student has explicitly chosen the target speaking scene."
                ],
            }
        ],
    }


def test_parse_condition_rule_header_accepts_route_exit_with_em_dash() -> None:
    parsed = cstm.parse_condition_rule_header(
        "**Jump Conditions (conditionRule) — Route Exit: Additional Owner Investment — Outer: OR**"
    )

    assert parsed == {
        "routeExit": "Additional Owner Investment",
        "outerRelation": "or",
        "groups": [],
    }


def test_route_exit_flow_specs_keep_each_branch_sequence() -> None:
    steps = [
        {
            "stepName": "Case Selection",
            "flowRules": [make_rule("Case A Start"), make_rule("Case B Start")],
        },
        {"stepName": "Case A Start", "flowRules": [make_rule()]},
        {"stepName": "Case A Final", "flowRules": [make_rule()]},
        {"stepName": "Case B Start", "flowRules": [make_rule()]},
        {"stepName": "Case B Final", "flowRules": [make_rule()]},
    ]

    specs = cstm.get_create_flow_specs(steps)

    assert [(spec["sourceName"], spec["targetName"]) for spec in specs] == [
        ("START", "Case Selection"),
        ("Case Selection", "Case A Start"),
        ("Case Selection", "Case B Start"),
        ("Case A Start", "Case A Final"),
        ("Case A Final", "END"),
        ("Case B Start", "Case B Final"),
        ("Case B Final", "END"),
    ]
    assert specs[1]["isDefault"] == 1
    assert specs[2]["isDefault"] == 0
    assert all(spec["flowSettingType"] == "configuration" for spec in specs[1:])
