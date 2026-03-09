"""
规则评测模块 - 目标达成度、流程遵循度
"""

import re
from typing import Dict, Any

from .types import TeacherDocument, DialogueData, DimensionScore


def evaluate(teacher_doc: TeacherDocument, dialogue_data: DialogueData) -> Dict[str, DimensionScore]:
    """
    执行规则评测

    Returns:
        Dict[str, DimensionScore]: 各维度得分
    """
    results = {}

    # 目标达成度评测
    results["目标达成度"] = evaluate_goal_achievement(teacher_doc, dialogue_data)

    # 流程遵循度评测
    results["流程遵循度"] = evaluate_process_compliance(teacher_doc, dialogue_data)

    return results


def evaluate_goal_achievement(teacher_doc: TeacherDocument, dialogue_data: DialogueData) -> DimensionScore:
    """
    评测目标达成度（20分）

    评分标准：
    - 知识点覆盖率（10分）：对话中提及的知识点 / 总知识点
    - 能力目标覆盖（10分）：检查是否覆盖教学目标中的能力要求
    """
    dialogue_text = _extract_dialogue_text(dialogue_data)
    dialogue_lower = dialogue_text.lower()

    # 知识点覆盖率计算
    key_points = teacher_doc.key_points
    if key_points:
        matched_points = 0
        for point in key_points:
            # 提取关键词进行匹配
            keywords = _extract_keywords(point)
            if any(kw in dialogue_lower for kw in keywords):
                matched_points += 1

        coverage_ratio = matched_points / len(key_points)
        knowledge_score = min(10, coverage_ratio * 10)
    else:
        # 没有明确知识点时，从raw_text中提取关键词
        knowledge_score = _evaluate_content_coverage(teacher_doc.raw_text, dialogue_text)
        knowledge_score = min(10, knowledge_score * 10)

    # 能力目标覆盖（简化处理）
    # 检查教学目标中的动词是否在对话中有所体现
    objectives = teacher_doc.teaching_objectives
    if objectives:
        ability_keywords = ["理解", "掌握", "应用", "分析", "评价", "创造",
                          "解释", "说明", "判断", "设计", "解决"]
        matched_abilities = 0
        for obj in objectives:
            if any(kw in obj for kw in ability_keywords):
                # 检查对话中是否有相应的能力体现
                if any(kw in dialogue_lower for kw in ability_keywords):
                    matched_abilities += 1

        ability_score = min(10, (matched_abilities / max(1, len(objectives))) * 10)
    else:
        ability_score = 8  # 默认中等分数

    total_score = knowledge_score + ability_score

    # 生成评价详情
    details = f"知识点覆盖率：{knowledge_score:.1f}/10分，能力目标覆盖：{ability_score:.1f}/10分"

    if total_score >= 17:
        level = "优秀"
    elif total_score >= 14:
        level = "良好"
    elif total_score >= 10:
        level = "合格"
    else:
        level = "需改进"

    return DimensionScore(
        name="目标达成度",
        score=round(total_score, 1),
        full_score=20,
        details=f"{level}。{details}"
    )


def evaluate_process_compliance(teacher_doc: TeacherDocument, dialogue_data: DialogueData) -> DimensionScore:
    """
    评测流程遵循度（20分）

    评分标准：
    - 环节完整性（10分）：检查对话是否完整经历所有教学环节
    - 顺序正确性（10分）：检查环节流转是否符合设计顺序
    """
    workflow = teacher_doc.workflow

    if not workflow:
        # 没有明确流程时，使用通用评测
        return _evaluate_generic_process(dialogue_data)

    dialogue_text = _extract_dialogue_text(dialogue_data)
    dialogue_lower = dialogue_text.lower()

    # 环节完整性检查
    matched_steps = 0
    step_positions = []

    for step in workflow:
        step_keywords = _extract_keywords(step)
        # 检查流程步骤是否在对话中体现
        if any(kw in dialogue_lower for kw in step_keywords):
            matched_steps += 1
            # 记录位置用于顺序检查
            for kw in step_keywords:
                pos = dialogue_lower.find(kw)
                if pos >= 0:
                    step_positions.append((pos, step))
                    break

    completeness_ratio = matched_steps / len(workflow)
    completeness_score = min(10, completeness_ratio * 10)

    # 顺序正确性检查
    if len(step_positions) >= 2:
        step_positions.sort(key=lambda x: x[0])
        # 检查是否按预期顺序出现
        order_correct = True
        for i in range(len(step_positions) - 1):
            if step_positions[i][0] > step_positions[i + 1][0]:
                order_correct = False
                break

        order_score = 10 if order_correct else 5
    else:
        order_score = 5  # 步骤太少无法判断顺序

    total_score = completeness_score + order_score

    details = f"环节完整性：{completeness_score:.1f}/10分（{matched_steps}/{len(workflow)}个环节），"
    details += f"顺序正确性：{order_score:.1f}/10分"

    if total_score >= 17:
        level = "优秀"
    elif total_score >= 14:
        level = "良好"
    elif total_score >= 10:
        level = "合格"
    else:
        level = "需改进"

    return DimensionScore(
        name="流程遵循度",
        score=round(total_score, 1),
        full_score=20,
        details=f"{level}。{details}"
    )


def _evaluate_generic_process(dialogue_data: DialogueData) -> DimensionScore:
    """
    通用流程评测（当没有明确流程时使用）
    """
    messages = []
    for stage in dialogue_data.stages:
        messages.extend(stage.messages)

    # 检查对话结构
    ai_count = sum(1 for m in messages if m.role == "ai")
    student_count = sum(1 for m in messages if m.role == "student")

    # 基本检查：是否有开场和结束
    has_opening = False
    has_closing = False

    if messages:
        first_msg = messages[0].content.lower()
        if any(word in first_msg for word in ["你好", "欢迎", "开始", "介绍"]):
            has_opening = True

        last_msg = messages[-1].content.lower()
        if any(word in last_msg for word in ["结束", "总结", "再见", "谢谢", "完成"]):
            has_closing = True

    # 评分
    score = 10  # 基础分
    if has_opening:
        score += 5
    if has_closing:
        score += 5

    # 根据对话轮数调整
    if student_count >= 5:
        score = min(20, score + 2)

    details = f"AI消息数：{ai_count}，学生消息数：{student_count}"
    if has_opening:
        details += "，有开场白"
    if has_closing:
        details += "，有结束语"

    return DimensionScore(
        name="流程遵循度",
        score=round(score, 1),
        full_score=20,
        details=details
    )


def _extract_dialogue_text(dialogue_data: DialogueData) -> str:
    """提取对话文本"""
    parts = []
    for stage in dialogue_data.stages:
        for msg in stage.messages:
            parts.append(msg.content)
    return "\n".join(parts)


def _extract_keywords(text: str) -> list[str]:
    """从文本中提取关键词"""
    # 移除常见停用词
    stop_words = {"的", "了", "和", "是", "在", "有", "我", "都", "个", "与", "也", "对",
                  "可以", "进行", "通过", "使用", "需要", "要求", "学生", "教师", "教学"}

    # 提取中文词汇
    words = re.findall(r'[\u4e00-\u9fff]+', text)

    # 过滤停用词和短词
    keywords = [w for w in words if len(w) >= 2 and w not in stop_words]

    # 如果关键词太少，返回原文
    if len(keywords) < 2:
        return [text]

    return keywords[:5]  # 最多返回5个关键词


def _evaluate_content_coverage(teacher_text: str, dialogue_text: str) -> float:
    """
    评估内容覆盖率

    Returns:
        float: 覆盖率（0-1之间）
    """
    teacher_keywords = _extract_keywords(teacher_text)
    dialogue_lower = dialogue_text.lower()

    if not teacher_keywords:
        return 0.5

    matched = sum(1 for kw in teacher_keywords if kw in dialogue_lower)
    return matched / len(teacher_keywords)
