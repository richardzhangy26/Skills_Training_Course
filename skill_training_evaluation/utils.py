"""
LLM 工具函数 - 简化版
"""

import json
import re
import time
from typing import Dict, List, Any
import requests
from types_def import DialogueData, IssueItem, HighlightItem


def format_dialogue_for_llm(dialogue_data: DialogueData) -> str:
    """格式化对话记录为 LLM 可读格式"""
    lines = []
    for stage in dialogue_data.stages:
        lines.append(f"\n## {stage.stage_name}\n")
        for msg in stage.messages:
            role = "智能体" if msg.role == "assistant" else "学生"
            lines.append(f"**{role}(第{msg.round}轮):** {msg.content}\n")
    return "\n".join(lines)


def parse_llm_response(response: str) -> Dict[str, Any]:
    """解析 LLM 返回的 JSON"""
    cleaned = response.strip()
    cleaned = re.sub(r"<thinking>[\s\S]*?</thinking>", "", cleaned).strip()

    json_text = None

    # 优先查找 JSON 代码块
    code_block_match = re.search(r"```(?:json)?\s*\n?([\s\S]*?)\n?```", cleaned)
    if code_block_match:
        json_text = code_block_match.group(1).strip()

    # 尝试查找 JSON 对象
    if not json_text:
        first_brace = cleaned.find("{")
        last_brace = cleaned.rfind("}")
        if first_brace != -1 and last_brace > first_brace:
            json_text = cleaned[first_brace:last_brace + 1]

    if not json_text:
        return _default_response("无法提取 JSON")

    try:
        result = json.loads(json_text)
    except json.JSONDecodeError:
        # 尝试修复常见问题
        fixed = re.sub(r",\s*}", "}", json_text)
        fixed = re.sub(r",\s*]", "]", fixed)
        try:
            result = json.loads(fixed)
        except json.JSONDecodeError as e:
            return _default_response(f"JSON 解析失败: {e}")

    return _normalize_result(result)


def _default_response(error_message: str) -> Dict[str, Any]:
    """创建默认响应"""
    return {
        "sub_dimension": "解析失败",
        "score": 0,
        "full_score": 0,
        "rating": "解析失败",
        "score_range": "",
        "judgment_basis": error_message,
        "issues": [],
        "highlights": [],
    }


def _normalize_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """标准化解析结果"""
    return {
        "sub_dimension": result.get("sub_dimension", "未知子维度"),
        "score": int(result.get("score", 0)) if isinstance(result.get("score"), (int, float)) else 0,
        "full_score": int(result.get("full_score", 5)) if isinstance(result.get("full_score"), (int, float)) else 5,
        "rating": result.get("rating", "未知"),
        "score_range": result.get("score_range", ""),
        "judgment_basis": result.get("judgment_basis", ""),
        "issues": _normalize_issues(result.get("issues", [])),
        "highlights": _normalize_highlights(result.get("highlights", [])),
    }


def _normalize_issues(issues: List[Dict]) -> List[IssueItem]:
    """标准化问题列表"""
    result = []
    for item in issues:
        severity_val = item.get("severity")
        severity: str = severity_val if severity_val in ("high", "medium", "low") else "medium"
        result.append(IssueItem(
            description=str(item.get("description", "")),
            location=str(item.get("location", "未定位")),
            quote=str(item.get("quote", "")),
            severity=severity,  # type: ignore[arg-type]
            impact=str(item.get("impact", "")),
        ))
    return result


def _normalize_highlights(highlights: List[Dict]) -> List[HighlightItem]:
    """标准化亮点列表"""
    return [
        HighlightItem(
            description=str(item.get("description", "")),
            location=str(item.get("location", "未定位")),
            quote=str(item.get("quote", "")),
            impact=str(item.get("impact", "")),
        )
        for item in highlights
    ]


async def call_llm(
    prompt: str,
    api_key: str,
    base_url: str,
    model: str,
    temperature: float = 0.1,
    timeout: int = 180,
) -> str:
    """调用 LLM API"""
    payload = {
        "maxTokens": 4000,
        "messages": [
            {
                "role": "system",
                "content": """你是一位资深的教学质量评估专家。你的任务是分析教学智能体的对话质量并输出评分结果。

**重要规则：你必须只输出 JSON，不要输出任何其他内容！**
- 直接输出 JSON 对象，以 { 开头，以 } 结尾
- 不要写任何解释性文字""",
            },
            {"role": "user", "content": prompt},
        ],
        "model": model,
        "n": 1,
        "presencePenalty": 0.0,
        "temperature": temperature,
    }

    print(f"[LLM] 调用模型: {model}")
    start_time = time.time()

    response = requests.post(
        base_url,
        json=payload,
        headers={"api-key": api_key, "Content-Type": "application/json"},
        timeout=timeout,
    )

    elapsed = time.time() - start_time
    print(f"[LLM] 响应耗时: {elapsed:.2f}s, 状态: {response.status_code}")

    if not response.ok:
        raise ValueError(f"API请求失败 (HTTP {response.status_code}): {response.text[:200]}")

    result = response.json()
    if result.get("choices") and len(result["choices"]) > 0:
        return result["choices"][0]["message"]["content"]

    raise ValueError(f"API返回格式异常: {json.dumps(result)[:200]}")
