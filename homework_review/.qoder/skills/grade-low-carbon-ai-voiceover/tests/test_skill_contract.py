from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]


def test_skill_declares_valid_submission_floor_and_exclusions() -> None:
    text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")

    assert "有效相关提交最低 80 分" in text
    assert "完全无关" in text
    assert "不适用 80 分保底" in text


def test_skill_declares_video_and_asr_fallback() -> None:
    text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")

    assert "MP4" in text and "MOV" in text
    assert "无法转录不等于没有人声" in text
    assert "不得仅因 ASR" in text


def test_skill_declares_score_contract() -> None:
    text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")

    for dimension_id in (
        "topic_value",
        "voiceover",
        "music_mix",
        "technical_compliance",
        "creative_completion",
    ):
        assert dimension_id in text
    assert "25、20、25、15、15" in text
    assert "第一非空字符必须是 `{`" in text
    assert "最后一个字符必须是 `}`" in text
