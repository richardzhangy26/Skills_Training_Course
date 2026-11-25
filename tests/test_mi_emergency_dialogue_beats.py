"""Word 急救节拍检查：学生作答限制 + 对话日志覆盖。"""

from __future__ import annotations

from auto_script_train import CHINESE_STUDENT_MAX_CHARS, build_chinese_student_output_rules
from skill_training_build.mi_emergency_dialogue_beats import score_dialogue_beats


def test_student_output_rules_allow_sequential_nursing_lines():
    rules = "\n".join(build_chinese_student_output_rules())
    assert "50字以内" not in rules
    assert "禁止重复" in rules
    assert "急救顺序" in rules
    assert "鼻腔" in rules
    assert CHINESE_STUDENT_MAX_CHARS >= 80
    assert f"{CHINESE_STUDENT_MAX_CHARS}字以内" in rules


def test_repeating_first_line_fails_word_beats():
    log = """
用户: 叔叔别担心，已经到抢救室了，马上给您吸氧。家属也通知了。
AI: 哎哟胸口疼
用户: 叔叔别担心，已经到抢救室了，马上给您吸氧。家属也通知了。
AI: 哎哟胸口疼
用户: 叔叔别担心，已经到抢救室了，马上给您吸氧。家属也通知了。
AI: 哎哟胸口疼
用户: 叔叔别担心，已经到抢救室了，马上给您吸氧。家属也通知了。
AI: 哎哟胸口疼
用户: 叔叔别担心，已经到抢救室了，马上给您吸氧。家属也通知了。
AI: 哎哟胸口疼
"""
    result = score_dialogue_beats(log)
    assert result["repeated_stage"] is True
    assert "nasal" in result["missing"]
    assert result["passed"] is False


def test_word_complete_dialogue_passes():
    log = """
用户: 叔叔，已经通知了您的家属，我先检查一下您的鼻腔情况。
AI: 好
用户: 叔叔，我这样按着痛吗？吸，呼。现在给您吸上氧气。
AI: 好
用户: 帮您把手机收起来了，无金属物品。
AI: 好
用户: 叔叔，现在马上给您做心电图。
AI: 好
用户: 叔叔，您确诊了急性广泛前壁心肌梗死。
AI: 我听你们的
用户: 这个药要嚼碎了往下咽。
AI: 好
用户: 您对胶带过敏吗？
AI: 没有
用户: 他驻村的工作先放一放。刘铁柱，你怎么了，能听见我说话吗？
AI: ……
用户: 叔叔无反应。
AI: 我怎么了呀？
"""
    result = score_dialogue_beats(log)
    assert result["missing"] == []
    assert result["repeated_stage"] is False
    assert result["teacher_leak"] is False
    assert result["passed"] is True


def test_teacher_opening_is_a_leak():
    log = """
AI: 接下来我和您说说后续需要服用的药物种类，还有要复查抽血的时间和项目
用户: 好的，您说，我认真听。
"""
    result = score_dialogue_beats(log)
    assert result["teacher_leak"] is True
    assert result["passed"] is False
