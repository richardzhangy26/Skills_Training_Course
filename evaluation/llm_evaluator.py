"""
LLM评测模块 - 交互体验性、幻觉与边界、教学策略
"""

import json
import re
import asyncio
from typing import Dict, List

import httpx

from .types import TeacherDocument, DialogueData, DimensionScore, EvaluatorConfig
from .prompts import (
    INTERACTION_EXPERIENCE_PROMPT,
    HALLUCINATION_BOUNDARY_PROMPT,
    TEACHING_STRATEGY_PROMPT,
    EVALUATION_SUMMARY_PROMPT,
    format_dialogue_for_prompt,
    format_teacher_doc_for_prompt,
)


async def evaluate(
    teacher_doc: TeacherDocument,
    dialogue_data: DialogueData,
    config: EvaluatorConfig
) -> Dict[str, DimensionScore]:
    """
    执行LLM评测

    Returns:
        Dict[str, DimensionScore]: 各维度得分
    """
    # 准备输入数据
    teacher_text = format_teacher_doc_for_prompt(teacher_doc)
    dialogue_text = format_dialogue_for_prompt(dialogue_data)

    # 并发执行三个维度的评测
    results = await asyncio.gather(
        _evaluate_interaction_experience(teacher_text, dialogue_text, config),
        _evaluate_hallucination_boundary(teacher_text, dialogue_text, config),
        _evaluate_teaching_strategy(teacher_text, dialogue_text, config),
        return_exceptions=True,
    )

    dimensions = {}

    # 处理结果
    if isinstance(results[0], Exception):
        dimensions["交互体验性"] = _create_error_score("交互体验性", str(results[0]))
    else:
        dimensions["交互体验性"] = results[0]

    if isinstance(results[1], Exception):
        dimensions["幻觉与边界"] = _create_error_score("幻觉与边界", str(results[1]))
    else:
        dimensions["幻觉与边界"] = results[1]

    if isinstance(results[2], Exception):
        dimensions["教学策略"] = _create_error_score("教学策略", str(results[2]))
    else:
        dimensions["教学策略"] = results[2]

    return dimensions


async def generate_summary(
    scores: Dict[str, DimensionScore],
    config: EvaluatorConfig
) -> str:
    """生成评测总结"""
    scores_text = "\n".join([
        f"{name}: {score.score}/{score.full_score}分"
        for name, score in scores.items()
    ])

    details_text = "\n\n".join([
        f"【{name}】\n{score.details or '无详细说明'}"
        for name, score in scores.items()
    ])

    prompt = EVALUATION_SUMMARY_PROMPT.format(
        scores_text=scores_text,
        details_text=details_text,
    )

    response = await _call_llm(prompt, config)
    return response.strip()


async def _evaluate_interaction_experience(
    teacher_text: str,
    dialogue_text: str,
    config: EvaluatorConfig
) -> DimensionScore:
    """评测交互体验性"""
    prompt = INTERACTION_EXPERIENCE_PROMPT.format(
        teacher_doc=teacher_text,
        dialogue=dialogue_text,
    )

    response = await _call_llm(prompt, config)
    result = _parse_llm_response(response)

    return DimensionScore(
        name="交互体验性",
        score=result.get("score", 10),
        full_score=20,
        details=result.get("comments", ""),
    )


async def _evaluate_hallucination_boundary(
    teacher_text: str,
    dialogue_text: str,
    config: EvaluatorConfig
) -> DimensionScore:
    """评测幻觉与边界"""
    prompt = HALLUCINATION_BOUNDARY_PROMPT.format(
        teacher_doc=teacher_text,
        dialogue=dialogue_text,
    )

    response = await _call_llm(prompt, config)
    result = _parse_llm_response(response)

    return DimensionScore(
        name="幻觉与边界",
        score=result.get("score", 10),
        full_score=20,
        details=result.get("comments", ""),
    )


async def _evaluate_teaching_strategy(
    teacher_text: str,
    dialogue_text: str,
    config: EvaluatorConfig
) -> DimensionScore:
    """评测教学策略"""
    prompt = TEACHING_STRATEGY_PROMPT.format(
        teacher_doc=teacher_text,
        dialogue=dialogue_text,
    )

    response = await _call_llm(prompt, config)
    result = _parse_llm_response(response)

    return DimensionScore(
        name="教学策略",
        score=result.get("score", 10),
        full_score=20,
        details=result.get("comments", ""),
    )


async def _call_llm(prompt: str, config: EvaluatorConfig) -> str:
    """调用LLM API"""
    headers = {
        "Authorization": f"Bearer {config.api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": config.model,
        "messages": [
            {"role": "system", "content": "你是一位专业的AI教学评测专家。请严格按照要求的格式输出评测结果。"},
            {"role": "user", "content": prompt},
        ],
        "temperature": config.temperature,
        "max_tokens": 2000,
    }

    async with httpx.AsyncClient(timeout=config.timeout) as client:
        response = await client.post(
            config.api_url + "/chat/completions",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

        if "choices" in data and len(data["choices"]) > 0:
            return data["choices"][0]["message"]["content"]
        else:
            raise ValueError(f"Unexpected API response: {data}")


def _parse_llm_response(response: str) -> dict:
    """解析LLM返回的JSON结果"""
    # 尝试直接解析整个响应
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        pass

    # 尝试从markdown代码块中提取JSON
    json_pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
    matches = re.findall(json_pattern, response)

    for match in matches:
        try:
            return json.loads(match)
        except json.JSONDecodeError:
            continue

    # 尝试提取数字作为分数
    score_pattern = r'["\']?score["\']?\s*[:：]\s*(\d+)'
    score_match = re.search(score_pattern, response)
    if score_match:
        return {
            "score": int(score_match.group(1)),
            "comments": response[:200],
        }

    # 默认返回
    return {
        "score": 10,
        "comments": "解析失败，使用默认分数",
    }


def _create_error_score(name: str, error_msg: str) -> DimensionScore:
    """创建错误状态的得分"""
    return DimensionScore(
        name=name,
        score=0,
        full_score=20,
        details=f"评测失败: {error_msg[:100]}"
    )


def evaluate_sync(
    teacher_doc: TeacherDocument,
    dialogue_data: DialogueData,
    config: EvaluatorConfig
) -> Dict[str, DimensionScore]:
    """同步执行LLM评测（供非异步环境使用）"""
    return asyncio.run(evaluate(teacher_doc, dialogue_data, config))
