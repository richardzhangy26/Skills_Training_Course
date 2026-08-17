from pathlib import Path

import pytest

from skill_training_build import create_configuration_from_markdown as cfm


def write_markdown(tmp_path: Path, background_value: str) -> Path:
    markdown_path = tmp_path / "task.md"
    markdown_path.write_text(
        "\n".join(
            [
                "# 测试任务",
                "",
                "## 📋 基础配置",
                "- **任务名称**: 学术英语模拟论文答辩口语训练",
                "- **任务描述**：用于测试基础配置自动创建",
                f"- **背景图**: {background_value}",
                "",
                "### 阶段1: 热身与论文主题介绍",
                "",
                "**背景图**: stage1.png",
                "",
                "**开场白**:",
                "```",
                "hello",
                "```",
                "",
                "**提示词**:",
                "```",
                "prompt",
                "```",
            ]
        ),
        encoding="utf-8",
    )
    return markdown_path


def test_parse_base_configuration_supports_current_format(tmp_path: Path) -> None:
    markdown_path = write_markdown(tmp_path, "cover.png")

    parsed = cfm.parse_base_configuration(markdown_path)

    assert parsed.train_task_name == "学术英语模拟论文答辩口语训练"
    assert parsed.description == "用于测试基础配置自动创建"
    assert parsed.background_image == "cover.png"


def test_resolve_cover_image_falls_back_to_first_stage_background(tmp_path: Path) -> None:
    markdown_path = write_markdown(tmp_path, "(待生成)")
    stage_cover = tmp_path / "stage1.png"
    stage_cover.write_bytes(b"fake-image")

    base_config = cfm.parse_base_configuration(markdown_path)
    steps = [{"backgroundImage": "stage1.png"}]

    resolved = cfm.resolve_cover_image(markdown_path, base_config, steps)

    assert resolved == stage_cover.resolve()


def test_require_course_id_raises_when_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("COURSE_ID", raising=False)

    with pytest.raises(ValueError, match="COURSE_ID"):
        cfm.require_course_id()


def test_build_create_configuration_payload_uses_expected_defaults() -> None:
    base_config = cfm.BaseConfiguration(
        train_task_name="任务名称",
        description="任务描述",
        background_image="cover.png",
    )
    payload = cfm.build_create_configuration_payload(
        base_config=base_config,
        course_id="course-1",
        train_task_id="task-1",
        train_task_cover={"fileId": "file-1", "fileUrl": "https://example.com/1.png"},
    )

    assert payload == {
        "trainTaskName": "任务名称",
        "description": "任务描述",
        "trainType": "voice",
        "trainTaskCover": {"fileId": "file-1", "fileUrl": "https://example.com/1.png"},
        "trainTime": -1,
        "courseId": "course-1",
        "trainTaskId": "task-1",
    }


def test_write_root_task_id_updates_existing_value(tmp_path: Path) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "AUTHORIZATION=abc\nTASK_ID=\"old-task\"\nCOOKIE=xyz\nTASK_ID=older\n",
        encoding="utf-8",
    )

    written_path = cfm.write_root_task_id("new-task", env_path=env_path)

    assert written_path == env_path
    assert env_path.read_text(encoding="utf-8") == (
        "AUTHORIZATION=abc\nCOOKIE=xyz\nTASK_ID=\"new-task\"\n"
    )


def test_write_root_task_id_creates_env_file_when_missing(tmp_path: Path) -> None:
    env_path = tmp_path / ".env"

    cfm.write_root_task_id("created-task", env_path=env_path)

    assert env_path.read_text(encoding="utf-8") == 'TASK_ID="created-task"\n'


def test_create_from_markdown_with_steps_uses_created_task_id(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    markdown_path = write_markdown(tmp_path, "cover.png")
    (tmp_path / "cover.png").write_bytes(b"fake-image")
    monkeypatch.setenv("COURSE_ID", "course-123")

    captured = {}

    monkeypatch.setattr(
        cfm,
        "parse_markdown",
        lambda _: [{"stepName": "阶段1", "backgroundImage": ""}],
    )
    monkeypatch.setattr(
        cfm,
        "upload_cover_image",
        lambda _: {"fileId": "file-1", "fileUrl": "https://example.com/cover.png"},
    )
    monkeypatch.setattr(cfm, "create_configuration", lambda *args, **kwargs: "task-123")
    monkeypatch.setattr(cfm, "write_root_task_id", lambda task_id: tmp_path / f"{task_id}.env")
    monkeypatch.setattr(
        cfm,
        "query_script_steps",
        lambda _: [
            {"stepId": "start", "stepDetailDTO": {"nodeType": "SCRIPT_START"}},
            {"stepId": "end", "stepDetailDTO": {"nodeType": "SCRIPT_END"}},
        ],
    )
    monkeypatch.setattr(cfm, "query_script_step_flows", lambda _: [])

    def fake_build_steps(markdown_path_arg, train_task_id, **kwargs):
        captured["markdown_path"] = Path(markdown_path_arg)
        captured["train_task_id"] = train_task_id
        captured["kwargs"] = kwargs
        return {}

    monkeypatch.setattr(cfm, "build_steps_from_markdown", fake_build_steps)

    result = cfm.create_from_markdown(markdown_path, with_steps=True)

    assert result["trainTaskId"] == "task-123"
    assert captured["markdown_path"] == markdown_path.resolve()
    assert captured["train_task_id"] == "task-123"
    assert captured["kwargs"]["start_node_id"] == "start"
    assert captured["kwargs"]["end_node_id"] == "end"


def test_create_from_markdown_writes_task_id_to_root_env(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    markdown_path = write_markdown(tmp_path, "cover.png")
    (tmp_path / "cover.png").write_bytes(b"fake-image")
    monkeypatch.setenv("COURSE_ID", "course-123")

    captured = {}

    monkeypatch.setattr(
        cfm,
        "parse_markdown",
        lambda _: [{"stepName": "阶段1", "backgroundImage": ""}],
    )
    monkeypatch.setattr(
        cfm,
        "upload_cover_image",
        lambda _: {"fileId": "file-1", "fileUrl": "https://example.com/cover.png"},
    )
    monkeypatch.setattr(cfm, "create_configuration", lambda *args, **kwargs: "task-888")

    def fake_write_root_task_id(task_id: str):
        captured["task_id"] = task_id
        return tmp_path / ".env"

    monkeypatch.setattr(cfm, "write_root_task_id", fake_write_root_task_id)

    result = cfm.create_from_markdown(markdown_path, with_steps=False)

    assert result["trainTaskId"] == "task-888"
    assert captured["task_id"] == "task-888"
