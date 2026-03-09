"""
TXT 对话记录转 JSON 格式转换器
"""

import re
from typing import List
from types_def import DialogueData, DialogueMessage, DialogueMetadata, DialogueStage


def parse_txt_dialogue(txt_content: str) -> DialogueData:
    """
    解析 TXT 格式的对话记录，转换为 JSON 格式
    """
    lines = txt_content.strip().split("\n")

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
