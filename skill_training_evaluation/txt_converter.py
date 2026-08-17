"""
TXT 对话记录转 JSON 格式转换器
"""

import re
from typing import List
from types_def import DialogueData, DialogueMessage, DialogueMetadata, DialogueStage


def _is_separator_line(line: str) -> bool:
    """检测是否为分隔线（全由 - 或 = 组成，且长度 >= 3）"""
    stripped = line.strip()
    return len(stripped) >= 3 and all(c in "-=" for c in stripped)


def _is_workflow_format(lines: List[str]) -> bool:
    """检测是否是 workflow_tester_base.py 生成的对话记录格式（含 Step: 和 AI:/用户:）"""
    has_dialogue_header = False
    has_step = False
    has_ai = False
    has_user = False
    for line in lines[:50]:
        s = line.strip()
        if "对话记录" in s:
            has_dialogue_header = True
        if s.startswith("Step:"):
            has_step = True
        if s.startswith("AI:") or s.startswith("AI："):
            has_ai = True
        if s.startswith("用户:") or s.startswith("用户："):
            has_user = True
        if has_dialogue_header and has_step and has_ai and has_user:
            return True
    return has_step and has_ai


def _parse_workflow_txt_dialogue(lines: List[str]) -> DialogueData:
    """解析 workflow_tester_base.py 生成的 TXT 对话记录"""
    metadata = DialogueMetadata(
        task_id="",
        student_level="",
        created_at="",
        total_rounds=0,
    )
    messages: List[DialogueMessage] = []
    current_round = 0
    max_round = 0

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # 元数据
        if line.startswith("日志创建时间:"):
            metadata.created_at = line.split(":", 1)[1].strip()
        elif line.startswith("task_id:"):
            metadata.task_id = line.split(":", 1)[1].strip()
        elif line.startswith("学生档位:"):
            metadata.student_level = line.split(":", 1)[1].strip()
        elif line.startswith("Step:"):
            round_match = re.search(r"第\s*(\d+)\s*轮", line)
            if round_match:
                current_round = int(round_match.group(1))
                max_round = max(max_round, current_round)

            # 读取该 Step 块内的消息
            i += 1
            while i < len(lines):
                msg_line = lines[i]
                stripped = msg_line.strip()

                if stripped.startswith("Step:") or _is_separator_line(stripped):
                    i -= 1
                    break

                # AI 消息
                if stripped.startswith("AI:") or stripped.startswith("AI："):
                    colon = ":" if ":" in stripped else "："
                    content = stripped.split(colon, 1)[1].strip() if colon in stripped else ""
                    content_lines = [content]
                    i += 1
                    while i < len(lines):
                        next_line = lines[i]
                        ns = next_line.strip()
                        if (
                            ns.startswith("用户:") or ns.startswith("用户：")
                            or ns.startswith("AI:") or ns.startswith("AI：")
                            or ns.startswith("Step:") or _is_separator_line(ns)
                        ):
                            i -= 1
                            break
                        content_lines.append(next_line.rstrip())
                        i += 1
                    full_content = "\n".join(content_lines).strip()
                    if full_content:
                        messages.append(
                            DialogueMessage(role="assistant", content=full_content, round=current_round)
                        )
                # 用户消息
                elif stripped.startswith("用户:") or stripped.startswith("用户："):
                    colon = ":" if ":" in stripped else "："
                    content = stripped.split(colon, 1)[1].strip() if colon in stripped else ""
                    content_lines = [content]
                    i += 1
                    while i < len(lines):
                        next_line = lines[i]
                        ns = next_line.strip()
                        if (
                            ns.startswith("AI:") or ns.startswith("AI：")
                            or ns.startswith("用户:") or ns.startswith("用户：")
                            or ns.startswith("Step:") or _is_separator_line(ns)
                        ):
                            i -= 1
                            break
                        content_lines.append(next_line.rstrip())
                        i += 1
                    full_content = "\n".join(content_lines).strip()
                    if full_content:
                        messages.append(
                            DialogueMessage(role="user", content=full_content, round=current_round)
                        )

                i += 1

        i += 1

    metadata.total_rounds = max_round
    return DialogueData(
        metadata=metadata,
        stages=[DialogueStage(stage_name="对话记录", messages=messages)],
    )


def parse_txt_dialogue(txt_content: str) -> DialogueData:
    """
    解析 TXT 格式的对话记录，转换为 JSON 格式。
    自动兼容两种格式：
    1. [时间戳] 格式（如 training-evaluator 原始格式）
    2. Step: 格式（如 workflow_tester_base.py 生成的对话日志）
    """
    lines = txt_content.strip().split("\n")

    # 自动检测格式
    if _is_workflow_format(lines):
        return _parse_workflow_txt_dialogue(lines)

    # 原有 [时间戳] 格式解析
    metadata = DialogueMetadata(
        task_id="",
        student_level="",
        created_at="",
        total_rounds=0,
    )

    messages: List[DialogueMessage] = []
    current_round = 0
    max_round = 0

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # 解析元数据字段
        if line.startswith("日志创建时间:"):
            metadata.created_at = line.split(":", 1)[1].strip()
        elif line.startswith("task_id:"):
            metadata.task_id = line.split(":", 1)[1].strip()
        elif line.startswith("学生档位:"):
            metadata.student_level = line.split(":", 1)[1].strip()
        # 解析消息块 - 检测时间戳行 [YYYY-MM-DD HH:MM:SS]
        elif line.startswith("[") and "]" in line:
            # 提取轮次信息
            round_match = re.search(r"第\s*(\d+)\s*轮", line)
            if round_match:
                current_round = int(round_match.group(1))
                max_round = max(max_round, current_round)
            else:
                current_round = 0

            # 读取后续的消息内容
            i += 1
            while i < len(lines):
                msg_line = lines[i]

                # 遇到分隔线或下一个时间戳，结束当前消息块
                if msg_line.strip().startswith("---") or (msg_line.strip().startswith("[") and "]" in msg_line):
                    break

                # 解析 AI 消息
                if msg_line.startswith("AI:") or msg_line.startswith("AI："):
                    colon = ":" if ":" in msg_line else "："
                    content = msg_line.split(colon, 1)[1].strip() if colon in msg_line else ""

                    content_lines = [content]
                    i += 1
                    while i < len(lines):
                        next_line = lines[i]
                        if (
                            next_line.startswith("用户:")
                            or next_line.startswith("用户：")
                            or next_line.strip().startswith("---")
                            or (next_line.strip().startswith("[") and "]" in next_line)
                        ):
                            i -= 1
                            break
                        content_lines.append(next_line)
                        i += 1

                    full_content = "\n".join(content_lines).strip()
                    if full_content:
                        messages.append(
                            DialogueMessage(
                                role="assistant", content=full_content, round=current_round
                            )
                        )
                # 解析用户消息
                elif msg_line.startswith("用户:") or msg_line.startswith("用户："):
                    colon = ":" if ":" in msg_line else "："
                    content = msg_line.split(colon, 1)[1].strip() if colon in msg_line else ""

                    content_lines = [content]
                    i += 1
                    while i < len(lines):
                        next_line = lines[i]
                        if (
                            next_line.startswith("AI:")
                            or next_line.startswith("AI：")
                            or next_line.strip().startswith("---")
                            or (next_line.strip().startswith("[") and "]" in next_line)
                        ):
                            i -= 1
                            break
                        content_lines.append(next_line)
                        i += 1

                    full_content = "\n".join(content_lines).strip()
                    if full_content:
                        messages.append(
                            DialogueMessage(
                                role="user", content=full_content, round=current_round
                            )
                        )
                else:
                    i += 1
                    continue

                i += 1
            continue

        i += 1

    metadata.total_rounds = max_round

    return DialogueData(
        metadata=metadata,
        stages=[DialogueStage(stage_name="对话记录", messages=messages)],
    )
