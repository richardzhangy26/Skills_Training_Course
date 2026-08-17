from pathlib import Path

from skill_training_build import create_task_from_markdown as ctm


def write_script_markdown(tmp_path: Path) -> Path:
    markdown_path = tmp_path / "task.md"
    markdown_path.write_text(
        "\n".join(
            [
                "# 测试任务",
                "",
                "### 阶段1: 接诊问候",
                "",
                "**虚拟训练官名字**: 陈教授",
                "**数字人**: INeLishTJz",
                "**数字人名称**: 陈教授",
                "**模型**: Doubao-Seed-1.6",
                "**声音**: Tg3LpKo28D",
                "**形象**: avatars/teacher.png",
                "**阶段描述**: 完成接诊问候",
                "**互动轮次**: 3",
                "",
                "**开场白**:",
                "```",
                "你好，请开始问诊。",
                "```",
                "",
                "**提示词**:",
                "```",
                "你是带教老师。",
                "```",
            ]
        ),
        encoding="utf-8",
    )
    return markdown_path


def test_parse_markdown_supports_digital_human_fields(tmp_path: Path) -> None:
    markdown_path = write_script_markdown(tmp_path)

    steps = ctm.parse_markdown(markdown_path)

    assert steps[0]["customDigitalHuman"] == "INeLishTJz"
    assert steps[0]["digitalHumanName"] == "陈教授"
    assert steps[0]["agentId"] == "Tg3LpKo28D"
    assert steps[0]["avatarNid"] == "avatars/teacher.png"


def test_apply_digital_human_owner_detail_backfills_step_fields() -> None:
    step = {"customDigitalHuman": "INeLishTJz"}
    owner_detail = {
        "customNid": "INeLishTJz",
        "voiceNid": "Tg3LpKo28D",
        "avatarNid": "5BWgp5oESW",
        "bigModelVoiceParam": "zh_male_qingcang_mars_bigtts",
    }

    ctm.apply_digital_human_owner_detail(step, owner_detail)

    assert step["customDigitalHuman"] == "INeLishTJz"
    assert step["agentId"] == "Tg3LpKo28D"
    assert step["avatarNid"] == "5BWgp5oESW"
    assert step["agentVoiceId"] == "zh_male_qingcang_mars_bigtts"


def test_build_script_step_detail_includes_current_digital_human_fields() -> None:
    detail = ctm.build_script_step_detail(
        {
            "stepName": "接诊问候",
            "trainerName": "陈教授",
            "modelId": "Doubao-Seed-1.6",
            "interactiveRounds": 3,
            "customDigitalHuman": "INeLishTJz",
            "agentVoiceId": "zh_male_qingcang_mars_bigtts",
            "agentId": "Tg3LpKo28D",
            "avatarNid": "5BWgp5oESW",
        }
    )

    assert detail["customDigitalHuman"] == "INeLishTJz"
    assert detail["agentVoiceId"] == "zh_male_qingcang_mars_bigtts"
    assert detail["agentId"] == "Tg3LpKo28D"
    assert detail["avatarNid"] == "5BWgp5oESW"
    assert detail["projectId"] == ""
    assert detail["trainTime"] == -1
