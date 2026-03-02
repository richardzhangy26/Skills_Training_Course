"""
数据类定义 - 简化版

只保留评估结果相关的数据类，配置类移至 config.py
"""

from dataclasses import dataclass, field
from typing import List, Optional, Literal
from enum import Enum


class EvaluationLevel(str, Enum):
    """评测等级"""
    EXCELLENT = "优秀"
    GOOD = "良好"
    PASS = "合格"
    FAIL = "不合格"
    VETO = "一票否决"


@dataclass
class IssueItem:
    """问题项"""
    description: str
    location: str = "未定位"
    quote: str = ""
    severity: Literal["high", "medium", "low"] = "medium"
    impact: str = ""


@dataclass
class HighlightItem:
    """亮点项"""
    description: str
    location: str = "未定位"
    quote: str = ""
    impact: str = ""


@dataclass
class SubDimensionScore:
    """子维度评分结果"""
    sub_dimension: str
    score: int
    full_score: int
    rating: str = "未知"
    score_range: str = ""
    judgment_basis: str = ""
    issues: List[IssueItem] = field(default_factory=list)
    highlights: List[HighlightItem] = field(default_factory=list)


@dataclass
class DimensionScore:
    """一级维度评分结果"""
    dimension: str
    score: float
    full_score: int
    weight: float
    level: str
    analysis: str
    sub_scores: List[SubDimensionScore]
    is_veto: bool = False
    weighted_score: float = 0.0


@dataclass
class DialogueMessage:
    """对话消息"""
    role: Literal["assistant", "user"]
    content: str
    round: int = 0


@dataclass
class DialogueMetadata:
    """对话元数据"""
    task_id: str = ""
    student_level: Optional[str] = None
    created_at: Optional[str] = None
    total_rounds: int = 0


@dataclass
class DialogueStage:
    """对话阶段"""
    stage_name: str
    messages: List[DialogueMessage] = field(default_factory=list)


@dataclass
class DialogueData:
    """对话数据"""
    metadata: DialogueMetadata
    stages: List[DialogueStage] = field(default_factory=list)


@dataclass
class EvaluationReport:
    """评测报告"""
    task_id: str
    total_score: float
    final_level: EvaluationLevel
    dimensions: List[DimensionScore]
    analysis: str = ""
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    pass_criteria_met: bool = True
    veto_reasons: List[str] = field(default_factory=list)
