"""
工具函数
"""

import json
from pathlib import Path
from typing import Any


def save_json_report(report: Any, output_path: str) -> None:
    """
    保存评测报告为JSON文件

    Args:
        report: 评测报告对象或字典
        output_path: 输出文件路径
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # 如果是Pydantic模型，使用model_dump
    if hasattr(report, "model_dump"):
        data = report.model_dump()
    else:
        data = report

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_json_file(path: str) -> Any:
    """
    加载JSON文件

    Args:
        path: 文件路径

    Returns:
        解析后的数据
    """
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def format_score_report(report: Any) -> str:
    """
    格式化评分为可读文本

    Args:
        report: 评测报告

    Returns:
        格式化后的文本
    """
    # 处理字典或Pydantic模型
    if hasattr(report, "model_dump"):
        data = report.model_dump()
    else:
        data = report

    lines = []
    lines.append("=" * 50)
    lines.append(f"任务ID: {data.get('task_id', 'N/A')}")
    lines.append(f"评测时间: {data.get('evaluated_at', 'N/A')}")
    lines.append("-" * 50)
    lines.append(f"总分: {data.get('total_score', 0)} / 100")
    lines.append(f"等级: {data.get('level', 'N/A')}")
    lines.append("-" * 50)
    lines.append("各维度得分:")

    for dim in data.get("dimensions", []):
        if hasattr(dim, "name"):
            lines.append(f"  • {dim.name}: {dim.score}/{dim.full_score}")
        else:
            lines.append(f"  • {dim.get('name', 'Unknown')}: {dim.get('score', 0)}/{dim.get('full_score', 20)}")

    lines.append("-" * 50)
    lines.append("评价总结:")
    lines.append(data.get("summary", "无"))
    lines.append("=" * 50)

    return "\n".join(lines)


def find_dialogue_files(directory: str, extensions: list[str] = None) -> list[str]:
    """
    查找目录下的所有对话文件

    Args:
        directory: 目录路径
        extensions: 文件扩展名列表，默认[".json", ".txt"]

    Returns:
        文件路径列表
    """
    if extensions is None:
        extensions = [".json", ".txt"]

    dir_path = Path(directory)
    if not dir_path.exists():
        return []

    files = []
    for ext in extensions:
        files.extend(dir_path.glob(f"*{ext}"))

    return sorted([str(f) for f in files])


def truncate_text(text: str, max_length: int = 1000) -> str:
    """
    截断文本到指定长度

    Args:
        text: 原始文本
        max_length: 最大长度

    Returns:
        截断后的文本
    """
    if len(text) <= max_length:
        return text
    return text[:max_length] + f"\n... (已截断，共{len(text)}字符)"
