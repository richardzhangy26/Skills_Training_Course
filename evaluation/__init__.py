"""
AI对话式教学训练质量评测模块

提供教师文档解析、对话日志评测、评分报告生成功能。
"""

from .types import (
    DimensionScore,
    EvaluationReport,
    DialogueData,
    DialogueMetadata,
    DialogueStage,
    TeacherDocument,
    EvaluatorConfig,
)
from .parsers import parse_teacher_doc, parse_dialogue
from .evaluator import evaluate
from .config import load_config

__version__ = "1.0.0"
__all__ = [
    "DimensionScore",
    "EvaluationReport",
    "DialogueData",
    "DialogueMetadata",
    "DialogueStage",
    "TeacherDocument",
    "EvaluatorConfig",
    "parse_teacher_doc",
    "parse_dialogue",
    "evaluate",
    "load_config",
]
