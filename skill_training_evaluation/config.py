"""
评估维度配置 - 简化版

维度配置从 prompts.json 动态读取，此处只保留评分规则
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import json
from pathlib import Path


@dataclass
class SubDimensionConfig:
    """子维度配置"""
    key: str
    name: str
    full_score: int


@dataclass
class DimensionConfig:
    """维度配置"""
    name: str
    weight: float
    full_score: int
    is_veto: bool = False
    veto_threshold: Optional[int] = None
    is_bonus: bool = False
    sub_dimensions: List[SubDimensionConfig] = field(default_factory=list)


# 默认评分规则（子维度分数）
DEFAULT_SUB_SCORES: Dict[str, int] = {
    "知识点覆盖率": 10,
    "能力覆盖率": 10,
    "环节准入条件": 4,
    "环节内部顺序": 4,
    "全局环节流转": 4,
    "环节准出检查": 4,
    "非线性跳转处理": 4,
    "人设语言风格": 4,
    "表达自然度": 4,
    "上下文衔接": 4,
    "循环僵局": 4,
    "回复长度控制": 4,
    "事实正确性": 5,
    "逻辑自洽性": 5,
    "未知承认": 3,
    "安全围栏": 3,
    "干扰抵抗": 4,
    "启发式提问频率": 5,
    "正向激励机制": 5,
    "纠错引导路径": 5,
    "深度追问技巧": 5,
}

# 维度元数据
DIMENSION_META: Dict[str, Dict] = {
    "目标达成度": {"weight": 0.2, "is_veto": True, "veto_threshold": 12},
    "流程遵循度": {"weight": 0.2},
    "交互体验性": {"weight": 0.2},
    "幻觉与边界": {"weight": 0.2},
    "教学策略": {"weight": 0.2, "is_bonus": True},
}


def load_prompts(prompts_path: Optional[str] = None) -> Dict[str, Dict[str, str]]:
    """加载提示词文件"""
    path = prompts_path if prompts_path else str(Path(__file__).parent / "prompts.json")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_dimensions_config(prompts_path: Optional[str] = None) -> Dict[str, DimensionConfig]:
    """
    从 prompts.json 动态构建维度配置

    prompts.json 结构:
    {
        "目标达成度": {
            "知识点覆盖率": "提示词...",
            "能力覆盖率": "提示词..."
        },
        ...
    }
    """
    prompts = load_prompts(prompts_path)
    configs: Dict[str, DimensionConfig] = {}

    for dim_name, sub_dims in prompts.items():
        meta = DIMENSION_META.get(dim_name, {"weight": 0.2})

        sub_dimension_configs = [
            SubDimensionConfig(
                key=sub_name,
                name=sub_name,
                full_score=DEFAULT_SUB_SCORES.get(sub_name, 5)
            )
            for sub_name in sub_dims.keys()
        ]

        full_score = sum(s.full_score for s in sub_dimension_configs)

        configs[dim_name] = DimensionConfig(
            name=dim_name,
            weight=meta.get("weight", 0.2),
            full_score=full_score,
            is_veto=meta.get("is_veto", False),
            veto_threshold=meta.get("veto_threshold"),
            is_bonus=meta.get("is_bonus", False),
            sub_dimensions=sub_dimension_configs,
        )

    return configs
