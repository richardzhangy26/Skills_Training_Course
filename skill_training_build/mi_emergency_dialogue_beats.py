"""对照《260901AI模拟人对话 终版》检查急救护理对话日志是否覆盖 Word 节拍。"""

from __future__ import annotations

import re
from pathlib import Path

WORD_BEATS = (
    ("nasal", r"鼻腔|按着痛|吸，呼|吸,呼"),
    ("oxygen_on", r"吸上氧|给你吸上氧气|给您吸上氧|现在给您吸上氧气"),
    ("phone_metal", r"手机|金属"),
    ("ecg", r"心电图"),
    ("mi_dx", r"急性广泛前壁心肌梗死|广泛前壁心梗|急性前壁心梗"),
    ("chew", r"嚼碎"),
    ("tape", r"胶带"),
    ("village", r"驻村"),
    ("hear", r"能听见|无反应|你怎么了"),
    ("what_happened", r"我怎么了|我咋了"),
)


def nurse_utterances(dialogue_text: str) -> list[str]:
    """Extract 用户/护士 lines from a dialogue.txt or markdown simulation."""
    lines = []
    for raw in dialogue_text.splitlines():
        stripped = raw.strip()
        for prefix in ("用户:", "用户：", "**学生**:", "**学生**："):
            if stripped.startswith(prefix):
                lines.append(stripped[len(prefix) :].strip())
                break
    return lines


def patient_utterances(dialogue_text: str) -> list[str]:
    lines = []
    for raw in dialogue_text.splitlines():
        stripped = raw.strip()
        for prefix in ("AI:", "AI：", "**智能体**:", "**智能体**："):
            if stripped.startswith(prefix):
                lines.append(stripped[len(prefix) :].strip())
                break
    return lines


def score_dialogue_beats(dialogue_text: str) -> dict:
    """Return coverage of Word beats and whether any stage is a single repeated nurse line."""
    found = {}
    missing = []
    for name, pattern in WORD_BEATS:
        ok = re.search(pattern, dialogue_text) is not None
        found[name] = ok
        if not ok:
            missing.append(name)

    nurse = nurse_utterances(dialogue_text)
    repeated_stage = False
    if nurse:
        # A stage fails if 5+ consecutive nurse lines are identical after stripping ellipsis/space.
        normalized = [re.sub(r"\s+", "", n) for n in nurse]
        run = 1
        for i in range(1, len(normalized)):
            if normalized[i] == normalized[i - 1] and normalized[i]:
                run += 1
                if run >= 5:
                    repeated_stage = True
                    break
            else:
                run = 1

    teacher_leak = bool(
        re.search(r"服用的药物种类|复查抽血的时间|我和您说说后续", dialogue_text)
    )
    return {
        "found": found,
        "missing": missing,
        "repeated_stage": repeated_stage,
        "teacher_leak": teacher_leak,
        "passed": not missing and not repeated_stage and not teacher_leak,
    }


def score_dialogue_file(path: str | Path) -> dict:
    text = Path(path).read_text(encoding="utf-8")
    result = score_dialogue_beats(text)
    result["path"] = str(path)
    return result
