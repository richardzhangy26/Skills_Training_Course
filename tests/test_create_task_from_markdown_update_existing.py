import json
from pathlib import Path

import pytest

from skill_training_build import create_task_from_markdown as ctm


FIXTURE_DIR = Path(__file__).resolve().parents[1] / "skill_training_build" / "test"


def load_query_steps():
    payload = json.loads(
        (FIXTURE_DIR / "queryScriptStepList_response.json").read_text(encoding="utf-8")
    )
    return payload["data"]


def write_placeholder_markdown(tmp_path: Path) -> Path:
    markdown_path = tmp_path / "task.md"
    markdown_path.write_text(
        "\n".join(
            [
                "### 阶段1: 第一阶段",
                "**互动轮次**: 1轮",
                "**开场白**:",
                "```",
                "hello",
                "```",
                "**提示词**:",
                "```",
                "prompt",
                "```",
            ]
        ),
        encoding="utf-8",
    )
    return markdown_path


def test_get_business_script_steps_filters_start_and_end() -> None:
    business_steps = ctm.get_business_script_steps(load_query_steps())

    assert len(business_steps) == 4
    assert all(
        item["stepDetailDTO"]["nodeType"] == "SCRIPT_NODE"
        for item in business_steps
    )
    assert [item["stepId"] for item in business_steps][:2] == [
        "jxyFY2lrbqQIQ2oCMU6-0",
        "wF2TYDuLdP-RWeLCV64qV",
    ]


def test_parse_markdown_preserves_negative_interactive_rounds(tmp_path: Path) -> None:
    markdown_path = tmp_path / "task.md"
    markdown_path.write_text(
        "\n".join(
            [
                "### 阶段1: 发布会预热：回应学生提问",
                "**互动轮次**: -1轮",
                "**开场白**:",
                "```",
                "hello",
                "```",
                "**提示词**:",
                "```",
                "prompt",
                "```",
            ]
        ),
        encoding="utf-8",
    )

    steps = ctm.parse_markdown(markdown_path)

    assert steps[0]["interactiveRounds"] == -1
    assert steps[0]["stepName"] == "发布会预热：回应学生提问"


def test_build_edit_payload_updates_only_content_fields() -> None:
    existing_step = ctm.get_business_script_steps(load_query_steps())[0]
    original_step = json.loads(json.dumps(existing_step, ensure_ascii=False))
    markdown_step = {
        "stepName": "更新后的阶段",
        "description": "更新后的描述",
        "interactiveRounds": 7,
        "prologue": "更新后的开场白",
        "llmPrompt": "更新后的提示词",
        "trainerName": "不应覆盖训练官",
        "modelId": "不应覆盖模型",
        "agentId": "不应覆盖声音",
        "avatarNid": "不应覆盖形象",
        "scriptStepResourceList": [{"fileId": "不应覆盖资源"}],
    }

    payload = ctm.build_edit_script_step_payload(
        existing_step,
        markdown_step,
        train_task_id="task-1",
        course_id="course-1",
    )

    detail = payload["stepDetailDTO"]
    assert payload["trainTaskId"] == "task-1"
    assert payload["courseId"] == "course-1"
    assert payload["stepId"] == existing_step["stepId"]
    assert payload["positionDTO"] == existing_step["positionDTO"]

    assert detail["stepName"] == "更新后的阶段"
    assert detail["description"] == "更新后的描述"
    assert detail["interactiveRounds"] == 7
    assert detail["prologue"] == "更新后的开场白"
    assert detail["llmPrompt"] == "更新后的提示词"

    assert detail["trainerName"] == existing_step["stepDetailDTO"]["trainerName"]
    assert detail["modelId"] == existing_step["stepDetailDTO"]["modelId"]
    assert detail["agentId"] == existing_step["stepDetailDTO"]["agentId"]
    assert detail["avatarNid"] == existing_step["stepDetailDTO"]["avatarNid"]
    assert detail["scriptStepCover"] == existing_step["stepDetailDTO"]["scriptStepCover"]
    assert detail["scriptStepResourceList"] == existing_step["stepDetailDTO"]["scriptStepResourceList"]
    assert detail["knowledgeBaseId"] == existing_step["stepDetailDTO"]["knowledgeBaseId"]

    assert existing_step == original_step


def test_update_existing_dry_run_does_not_call_edit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("COURSE_ID", "course-1")
    markdown_path = write_placeholder_markdown(tmp_path)
    platform_steps = load_query_steps()
    business_steps = ctm.get_business_script_steps(platform_steps)
    markdown_steps = [
        {
            "stepName": f"阶段{i}",
            "description": f"描述{i}",
            "interactiveRounds": i,
            "prologue": f"开场白{i}",
            "llmPrompt": f"提示词{i}",
        }
        for i in range(1, len(business_steps) + 1)
    ]

    def fail_edit(_payload):
        raise AssertionError("dry-run 不应调用 editScriptStep")

    monkeypatch.setattr(ctm, "edit_script_step", fail_edit)

    result = ctm.update_existing_steps_from_markdown(
        markdown_path,
        "task-1",
        dry_run=True,
        steps=markdown_steps,
        platform_steps=platform_steps,
    )

    assert result["dry_run"] is True
    assert result["updated_count"] == 0
    assert result["matched_count"] == len(business_steps)


def test_update_existing_count_mismatch_stops_before_edit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("COURSE_ID", "course-1")
    markdown_path = write_placeholder_markdown(tmp_path)
    platform_steps = load_query_steps()
    markdown_steps = [{"stepName": "只有一个阶段"}]

    def fail_edit(_payload):
        raise AssertionError("数量不一致时不应调用 editScriptStep")

    monkeypatch.setattr(ctm, "edit_script_step", fail_edit)

    with pytest.raises(ValueError, match="阶段数与平台业务节点数不一致"):
        ctm.update_existing_steps_from_markdown(
            markdown_path,
            "task-1",
            dry_run=False,
            assume_yes=True,
            steps=markdown_steps,
            platform_steps=platform_steps,
        )


def test_apply_step_metadata_merges_only_whitelisted_fields(tmp_path: Path) -> None:
    metadata_path = tmp_path / "resources.json"
    metadata_path.write_text(
        json.dumps(
            {
                "steps": [
                    {
                        "originalStepId": "step-1",
                        "metadata": {
                            "scriptStepCover": {"fileId": "cover-1"},
                            "scriptStepResourceList": [{"fileId": "resource-1"}],
                            "knowledgeBaseSwitch": 1,
                            "knowledgeBaseId": "kb-1",
                            "prologue": "不应覆盖内容字段",
                        },
                    }
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    steps = [{"originalStepId": "step-1", "prologue": "原开场白"}]

    metadata = ctm.load_step_metadata(metadata_path)
    matched_count = ctm.apply_step_metadata(steps, metadata)

    assert matched_count == 1
    assert steps[0]["scriptStepCover"] == {"fileId": "cover-1"}
    assert steps[0]["scriptStepResourceList"] == [{"fileId": "resource-1"}]
    assert steps[0]["knowledgeBaseSwitch"] == 1
    assert steps[0]["knowledgeBaseId"] == "kb-1"
    assert steps[0]["prologue"] == "原开场白"


def test_build_script_step_cover_from_url_preserves_existing_metadata() -> None:
    cover = ctm.build_script_step_cover_from_url(
        "https://prod-polymas-oss.polymas.com/demo.png",
        existing_cover={
            "fileId": "cover-1",
            "contentType": "image/png",
            "fileUrl": "https://old.example.com/old.png",
        },
    )

    assert cover == {
        "fileId": "cover-1",
        "contentType": "image/png",
        "fileUrl": "https://prod-polymas-oss.polymas.com/demo.png",
    }


def test_create_dry_run_preview_counts_linear_rebuild(capsys: pytest.CaptureFixture[str]) -> None:
    steps = [
        {"stepName": "阶段一", "trainerName": "甲", "interactiveRounds": 0, "flowCondition": "NEXT"},
        {"stepName": "阶段二", "trainerName": "乙", "interactiveRounds": 1},
    ]

    result = ctm.print_create_dry_run_preview(steps, metadata_match_count=1)
    output = capsys.readouterr().out

    assert result["step_count"] == 2
    assert result["flow_count"] == 3
    assert "将创建业务节点: 2" in output
    assert "将重建连线: 3" in output
    assert "未调用平台 API" in output


def test_create_script_flow_uses_default_transition_history_num(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_payload = {}

    class DummyResponse:
        def json(self):
            return {"code": 200, "success": True}

    def fake_post(url, headers=None, json=None, timeout=None):
        captured_payload["url"] = url
        captured_payload["headers"] = headers
        captured_payload["json"] = json
        captured_payload["timeout"] = timeout
        return DummyResponse()

    monkeypatch.setattr(ctm.requests, "post", fake_post)
    monkeypatch.setattr(ctm, "get_headers", lambda: {"Authorization": "token"})

    result = ctm.create_script_flow(
        "task-1",
        "start-1",
        "end-1",
        "NEXT_TO_STEP",
        "下一阶段开场白",
    )

    assert result is True
    assert captured_payload["json"]["transitionHistoryNum"] == 10
    assert captured_payload["json"]["transitionPrompt"] == "下一阶段开场白"
