"""
配置管理 - 环境变量加载
"""

import os
from pathlib import Path
from dotenv import load_dotenv

from .types import EvaluatorConfig


def find_dotenv() -> Path | None:
    """查找.env文件"""
    # 当前目录
    current_dir = Path.cwd()
    env_file = current_dir / ".env"
    if env_file.exists():
        return env_file

    # 父目录
    for parent in current_dir.parents:
        env_file = parent / ".env"
        if env_file.exists():
            return env_file

    return None


def load_config() -> EvaluatorConfig:
    """
    从环境变量加载配置

    查找顺序：
    1. 当前工作目录的.env文件
    2. 父目录的.env文件
    3. 已加载的环境变量

    Returns:
        EvaluatorConfig: 评测配置对象
    """
    # 尝试加载.env文件
    env_file = find_dotenv()
    if env_file:
        load_dotenv(env_file, override=True)

    # 必需的环境变量
    api_key = os.getenv("EVAL_API_KEY")
    if not api_key:
        # 尝试使用其他常见的API key变量名
        api_key = os.getenv("ARK_API_KEY") or os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise ValueError(
            "未找到API密钥。请设置EVAL_API_KEY环境变量，或在.env文件中配置。"
        )

    # API地址
    api_url = os.getenv("EVAL_API_URL", "https://ark.cn-beijing.volces.com/api/v3")
    if not api_url.startswith("http"):
        api_url = f"https://ark.cn-beijing.volces.com/api/v3"

    # 模型名称
    model = os.getenv("EVAL_MODEL", "doubao-1.5-pro-32k")

    return EvaluatorConfig(
        api_key=api_key,
        api_url=api_url,
        model=model,
        max_concurrent=int(os.getenv("EVAL_MAX_CONCURRENT", "3")),
        timeout=int(os.getenv("EVAL_TIMEOUT", "60")),
        temperature=float(os.getenv("EVAL_TEMPERATURE", "0.3")),
    )
