#!/usr/bin/env python3
"""
训练阶段背景图生成器（优先读取项目 secrets.json）

解析训练剧本配置 Markdown，为每个阶段:
1. 由 LLM 理解阶段上下文，智能生成文生图提示词
2. 优先调用 secrets.json 的 providers.image 主配置（Polymas），失败时改用 fallback_*（Seedream），兼容 OpenAI Images 与 DashScope
3. 下载保存到本地 backgrounds/ 目录

依赖安装:
    pip install requests python-dotenv openai

凭证优先读取项目根 secrets.json，可用 --secrets-file 指定其他文件。
旧版环境变量（secrets 未配置对应 provider 时使用）:
    BAILIAN_API_KEY: 百炼 API 密钥
    BAILIAN_TEXT_MODEL: 文本模型名称（可选，默认 qwen3.7-plus）

使用方式:
    python generate_background.py <剧本配置.md> [--output-dir <目录>] [--model <模型名>] [--size <尺寸>] [--style <风格描述>]
    python generate_background.py <剧本配置.md> --no-llm-prompt  # 跳过 LLM 生成，直接硬拼提示词
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import requests
from dotenv import load_dotenv

# ── .env 加载 ───────────────────────────────────────────────
# 脚本位于 .claude/skills/training-background-generator/scripts/
# 优先加载 .claude/skills/.env，再用项目根 .env 补缺（load_dotenv 默认不覆盖已有变量）
_SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_SECRETS_FILE = _SCRIPT_DIR.parents[3] / "secrets.json"
for _env_file in (
    _SCRIPT_DIR.parent.parent / ".env",  # .claude/skills/.env
    _SCRIPT_DIR.parent.parent.parent.parent / ".env",  # 项目根 .env
):
    if _env_file.exists():
        load_dotenv(_env_file)

# ── 默认配置 ───────────────────────────────────────────────
DEFAULT_IMAGE_MODEL = "qwen-image-2.0-pro"
DEFAULT_SIZE = "1664x928"  # 16:9，百炼 qwen-image 系列支持
DEFAULT_STYLE_SUFFIX = (
    "写实风格，中国风元素，专业级渲染，电影级光影，高清细节，16:9宽屏构图"
)
# 百炼 DashScope 原生文生图接口（OpenAI 兼容 images 端点不可用）
BAILIAN_IMAGE_URL = (
    "https://dashscope.aliyuncs.com/api/v1/services/aigc/"
    "multimodal-generation/generation"
)
BAILIAN_CHAT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DEFAULT_TEXT_MODEL = "qwen3.7-plus"

# 下载超时（秒）
DOWNLOAD_TIMEOUT = 60
# API 调用间隔（秒），避免触发限流
API_INTERVAL = 2


def load_providers(secrets_file: str | Path | None = None) -> dict:
    """只在运行时读取凭证；显式路径或损坏配置不静默降级。"""
    path = Path(secrets_file) if secrets_file is not None else DEFAULT_SECRETS_FILE
    if secrets_file is None and not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        raise ValueError(f"secrets 文件不是有效 JSON: {path}") from None
    if not isinstance(data, dict) or not isinstance(data.get("providers", {}), dict):
        raise ValueError("secrets.providers 必须是对象")
    return data.get("providers", {})


def require_provider_fields(config: dict, provider: str, fields: tuple[str, ...]) -> None:
    for name in fields:
        if not isinstance(config.get(name), str) or not config[name].strip():
            raise ValueError(f"secrets.providers.{provider}.{name} 缺失或为空")


@dataclass(frozen=True)
class ImageConfig:
    url: str
    model: str
    size: str
    api_key: str = field(repr=False)
    fallback: ImageConfig | None = None


def resolve_image_config(
    secrets_file: str | Path | None = None,
    model: str | None = None,
    size: str | None = None,
) -> ImageConfig:
    config = load_providers(secrets_file).get("image")
    if config is not None:
        if not isinstance(config, dict):
            raise ValueError("secrets.providers.image 必须是对象")
        require_provider_fields(config, "image", ("url", "api_key", "model", "size"))
        # 明确指定备用模型时直接走备用端点与凭证；否则主服务失败后自动改用备用服务。
        prefix = "fallback_" if model and model == config.get("fallback_model") else ""
        require_provider_fields(config, "image", (prefix + "url", prefix + "api_key"))
        fallback = None
        if not prefix and config.get("fallback_model"):
            require_provider_fields(config, "image", ("fallback_url", "fallback_api_key"))
            fallback = ImageConfig(
                url=config["fallback_url"],
                model=config["fallback_model"],
                size=size or config["size"],
                api_key=config["fallback_api_key"],
            )
        return ImageConfig(
            url=config[prefix + "url"],
            model=model or config["model"],
            size=size or config["size"],
            api_key=config[prefix + "api_key"],
            fallback=fallback,
        )
    api_key = os.environ.get("BAILIAN_API_KEY")
    if not api_key:
        raise EnvironmentError("请配置 secrets.json 的 providers.image，或设置 BAILIAN_API_KEY。")
    return ImageConfig(
        url=BAILIAN_IMAGE_URL, model=model or DEFAULT_IMAGE_MODEL,
        size=size or DEFAULT_SIZE, api_key=api_key,
    )


# ── 数据结构 ───────────────────────────────────────────────
@dataclass
class StageInfo:
    """从剧本 Markdown 中提取的阶段信息"""

    number: int
    name: str
    description: str = ""
    scene_config: str = ""
    prompt: str = ""  # 最终生成的提示词


# ── Markdown 解析 ──────────────────────────────────────────
def parse_basic_config(content: str) -> dict:
    """解析 ##基础配置 section，提取任务名称和任务描述。

    Returns:
        dict with keys: task_name, task_desc, section_start, section_end,
        has_cover_field. Empty dict if section not found.
    """
    # 定位 ##基础配置 section（兼容 emoji 前缀）
    section_match = re.search(
        r"^##\s*[📋\s]*基础配置\s*$",
        content,
        re.MULTILINE,
    )
    if not section_match:
        return {}

    section_start = section_match.start()
    # section 结束于下一个 ## 标题或文件末尾
    next_section = re.search(r"^##\s+", content[section_match.end():], re.MULTILINE)
    if next_section:
        section_end = section_match.end() + next_section.start()
    else:
        section_end = len(content)

    section_text = content[section_start:section_end]

    def _extract_field(field_name: str) -> str:
        m = re.search(
            r"\*\*" + re.escape(field_name) + r"\*\*\s*[:：]\s*([^\n]+)",
            section_text,
        )
        return m.group(1).strip() if m else ""

    task_name = _extract_field("任务名称")
    task_desc = _extract_field("任务描述")
    has_cover_field = bool(re.search(r"\*\*背景图\*\*", section_text))

    return {
        "task_name": task_name,
        "task_desc": task_desc,
        "section_start": section_start,
        "section_end": section_end,
        "has_cover_field": has_cover_field,
    }


def parse_script_markdown(content: str) -> List[StageInfo]:
    """解析训练剧本配置 Markdown，提取所有阶段信息。

    识别规则:
    - 阶段标题: ### 阶段N: 名称  或  ### 阶段N：名称
    - 阶段描述: 紧跟标题后的文本段落
    - 场景配置: **场景配置** 或 #### 场景配置 下的内容
    """
    stages: List[StageInfo] = []

    # 匹配阶段标题: ### 阶段1: xxx 或 ### 阶段1：xxx
    stage_pattern = re.compile(r"^###\s*阶段\s*(\d+)\s*[:：]\s*(.+)$", re.MULTILINE)

    matches = list(stage_pattern.finditer(content))
    if not matches:
        print("⚠️  未找到阶段标题（格式: ### 阶段N: 名称），尝试其他格式...")
        # 备选: ## 阶段N 或 **阶段N**
        stage_pattern = re.compile(
            r"^#{2,3}\s*阶段\s*(\d+)\s*[:：]?\s*(.+)$", re.MULTILINE
        )
        matches = list(stage_pattern.finditer(content))

    if not matches:
        print("❌ 未能解析出任何阶段信息")
        return stages

    for i, match in enumerate(matches):
        number = int(match.group(1))
        name = match.group(2).strip()

        # 获取本阶段的内容范围
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        section = content[start:end]

        # 提取阶段描述（第一个非空段落）
        desc_lines: list[str] = []
        for line in section.split("\n"):
            stripped = line.strip()
            if not stripped:
                if desc_lines:
                    break
                continue
            # 跳过子标题和特殊标记
            if stripped.startswith("#") or stripped.startswith("**"):
                if desc_lines:
                    break
                continue
            if stripped.startswith("-") or stripped.startswith("*"):
                desc_lines.append(stripped.lstrip("-* "))
            else:
                desc_lines.append(stripped)
        description = "，".join(desc_lines)[:300]
        pro_description = re.search(
            r"^\*\*卡片描述\*\*\s*[:：]\s*([^\n]+)",
            section,
            re.MULTILINE,
        )
        if pro_description:
            description = pro_description.group(1).strip()[:300]

        # 提取场景配置
        scene_config = ""
        scene_match = re.search(
            r"(?:\*\*场景配置\*\*|####?\s*场景配置)\s*[:：]?\s*\n([\s\S]*?)(?=\n#{2,4}\s|\n\*\*[^场]|\Z)",
            section,
        )
        if scene_match:
            scene_lines: list[str] = []
            for line in scene_match.group(1).split("\n"):
                stripped = line.strip()
                if stripped and not stripped.startswith("#"):
                    scene_lines.append(stripped.lstrip("-* "))
            scene_config = "，".join(scene_lines)[:300]
        pro_background = re.search(
            r"^\*\*背景图描述\*\*\s*[:：]\s*([^\n]+)",
            section,
            re.MULTILINE,
        )
        if pro_background:
            scene_config = pro_background.group(1).strip()[:300]

        stages.append(
            StageInfo(
                number=number,
                name=name,
                description=description,
                scene_config=scene_config,
            )
        )

    return stages


# ── 提示词生成 ─────────────────────────────────────────────

# LLM 生成封面提示词的系统/用户模板
_COVER_PROMPT_SYSTEM = """你是一个专业的文生图提示词设计师。你的任务是根据训练任务的整体信息，生成适合 AI 文生图模型的封面场景描述提示词。

要求：
1. 输出纯场景描述，用于生成整体任务封面图，不要包含任何解释或标记
2. 描述综合性的标志性场景：体现任务主题的核心环境、象征元素、整体氛围
3. 不要出现任何代码变量（如 ${xxx}）、Markdown 标记、模板占位符
4. 不要描述单一阶段细节，而是展现整个训练课题的全貌
5. 提示词控制在 100-200 字之间
6. 使用中文描述"""

_COVER_PROMPT_USER_TEMPLATE = """请根据以下训练任务整体信息，生成一段文生图封面场景描述提示词。

【任务名称】{task_name}
【任务描述】{task_desc}

请直接输出封面场景描述提示词，不要有任何额外内容。"""


# LLM 生成提示词的系统提示
_PROMPT_SYSTEM = """你是一个专业的文生图提示词设计师。你的任务是根据训练剧本的阶段信息，生成适合 AI 文生图模型的场景描述提示词。

要求：
1. 输出纯场景描述，用于生成背景图片，不要包含任何解释或标记
2. 描述具体的视觉元素：环境、光线、物体、氛围
3. 不要出现任何代码变量（如 ${xxx}）、Markdown 标记、模板占位符
4. 不要描述人物动作或对话内容，只描述场景环境
5. 提示词控制在 100-200 字之间
6. 使用中文描述"""

_PROMPT_USER_TEMPLATE = """请根据以下训练阶段信息，生成一段文生图场景描述提示词。

【阶段编号】{number}
【阶段名称】{name}
【阶段描述】{description}
【场景配置原文】{scene_config}

请直接输出场景描述提示词，不要有任何额外内容。"""


def _get_text_client(secrets_file: str | Path | None = None):
    """文本服务优先使用 secrets 的 llm 配置，再兼容旧百炼环境变量。"""
    from openai import OpenAI

    config = load_providers(secrets_file).get("llm")
    if config is not None:
        if not isinstance(config, dict):
            raise ValueError("secrets.providers.llm 必须是对象")
        require_provider_fields(config, "llm", ("url", "api_key", "model"))
        return OpenAI(base_url=config["url"], api_key=config["api_key"])
    api_key = os.environ.get("BAILIAN_API_KEY")
    if not api_key:
        raise EnvironmentError("请设置 BAILIAN_API_KEY 环境变量。")

    return OpenAI(base_url=BAILIAN_CHAT_BASE_URL, api_key=api_key)


def generate_cover_prompt_via_llm(
    client,
    task_name: str,
    task_desc: str,
    style_suffix: str,
    text_model: str,
) -> str:
    """调用 LLM 生成封面级文生图提示词。"""
    user_msg = _COVER_PROMPT_USER_TEMPLATE.format(
        task_name=task_name or "（未知任务）",
        task_desc=task_desc or "（无描述）",
    )
    response = client.chat.completions.create(
        model=text_model,
        messages=[
            {"role": "system", "content": _COVER_PROMPT_SYSTEM},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.7,
        max_tokens=500,
    )
    raw = response.choices[0].message.content.strip()
    prompt = f"{raw}，{style_suffix}"
    if len(prompt) > 1800:
        prompt = prompt[:1800]
    return prompt


def build_cover_prompt_fallback(task_name: str, task_desc: str, style_suffix: str) -> str:
    """Fallback: 直接拼接 task_name + task_desc + style_suffix。"""
    core = f"{task_name}，{task_desc}".rstrip("，") if task_desc else task_name
    prompt = f"{core}，{style_suffix}"
    if len(prompt) > 1800:
        prompt = prompt[:1800]
    return prompt


def update_markdown_cover_background(md_path: Path, cover_img_path: str) -> bool:
    """将封面背景图路径回填到 ##基础配置 section 的 **背景图** 字段。

    - 若 section 内已有 **背景图**: 字段 → 替换
    - 若无 → 在最后一个 `- **xxx**` 行后追加

    Returns:
        True 表示成功写入，False 表示未找到 section 或写入失败。
    """
    content = md_path.read_text(encoding="utf-8")
    config = parse_basic_config(content)
    if not config:
        return False

    sec_start = config["section_start"]
    sec_end = config["section_end"]
    section_text = content[sec_start:sec_end]

    new_field_line = f"- **背景图**: {cover_img_path}"

    if config["has_cover_field"]:
        # 替换已有字段
        updated_section = re.sub(
            r"- \*\*背景图\*\*[ \t]*[:：][ \t]*[^\n]*",
            new_field_line,
            section_text,
        )
    else:
        # 在最后一个 `- **xxx**` 行后追加
        last_field_match = None
        for m in re.finditer(r"- \*\*[^*]+\*\*\s*[:：][^\n]*", section_text):
            last_field_match = m
        if last_field_match:
            insert_pos = last_field_match.end()
            updated_section = (
                section_text[:insert_pos]
                + "\n"
                + new_field_line
                + section_text[insert_pos:]
            )
        else:
            # section 内无字段行，直接追加到末尾（section 末尾前）
            updated_section = section_text.rstrip("\n") + "\n" + new_field_line + "\n"

    new_content = content[:sec_start] + updated_section + content[sec_end:]
    md_path.write_text(new_content, encoding="utf-8")
    return True


def generate_prompt_via_llm(
    client,
    stage: StageInfo,
    style_suffix: str,
    text_model: str,
) -> str:
    """调用 LLM 理解阶段上下文，智能生成文生图提示词。"""
    user_msg = _PROMPT_USER_TEMPLATE.format(
        number=stage.number,
        name=stage.name,
        description=stage.description or "（无）",
        scene_config=stage.scene_config or "（无）",
    )

    response = client.chat.completions.create(
        model=text_model,
        messages=[
            {"role": "system", "content": _PROMPT_SYSTEM},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.7,
        max_tokens=500,
    )
    raw = response.choices[0].message.content.strip()

    # 拼接风格后缀
    prompt = f"{raw}，{style_suffix}"

    # 长度保护
    if len(prompt) > 1800:
        prompt = prompt[:1800]

    return prompt


def build_prompt_fallback(stage: StageInfo, style_suffix: str) -> str:
    """Fallback: 硬拼提示词（当 LLM 生成失败时使用）。

    优先使用场景配置（更具体），回退到阶段描述。
    """
    scene_core = stage.scene_config or stage.description or stage.name

    prompt_parts = [
        scene_core.rstrip("，。"),
        style_suffix,
    ]

    prompt = "，".join(p for p in prompt_parts if p)

    if len(prompt) > 1800:
        prompt = prompt[:1800]

    return prompt


# ── 图片生成与下载 ──────────────────────────────────────────
def generate_image(
    prompt: str, model: str, size: str, api_key: str,
    *, api_url: str = BAILIAN_IMAGE_URL,
) -> str:
    """调用配置的文生图接口，返回远程 URL 或 Base64 data URL。"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    is_dashscope = "/multimodal-generation/" in api_url
    if is_dashscope:
        payload = {
            "model": model,
            "input": {"messages": [{"role": "user", "content": [{"text": prompt}]}]},
            "parameters": {"size": size.replace("x", "*")},
        }
    else:
        payload = {"model": model, "prompt": prompt, "size": size, "n": 1}
        if "volces.com" in api_url:
            payload["watermark"] = False  # 火山方舟 Seedream 默认加水印
    resp = requests.post(
        api_url,
        headers=headers,
        json=payload,
        timeout=300,
    )
    resp.raise_for_status()

    data = resp.json()
    try:
        if is_dashscope:
            url = data["output"]["choices"][0]["message"]["content"][0]["image"]
        else:
            result = data["data"][0]
            url = result.get("url")
            if not url and result.get("b64_json"):
                url = "data:image/png;base64," + result["b64_json"]
    except (KeyError, IndexError, TypeError):
        raise RuntimeError("API 返回格式异常，缺少图片 URL 或 b64_json") from None
    if not url:
        raise RuntimeError("API 返回的图片 URL 为空")
    return url


def generate_with_fallback(prompt: str, config: ImageConfig) -> tuple[str, str, str | None]:
    """主服务失败时改用备用配置；返回 (图片 URL, 实际模型, 主服务错误)。"""
    try:
        url = generate_image(prompt, config.model, config.size, config.api_key, api_url=config.url)
        return url, config.model, None
    except Exception as e:
        if config.fallback is None:
            raise
        primary_error = str(e)
    fallback = config.fallback
    print(f"   ⚠️  主服务 {config.model} 失败 ({primary_error})，改用备用 {fallback.model}")
    try:
        url = generate_image(
            prompt, fallback.model, fallback.size, fallback.api_key, api_url=fallback.url
        )
    except Exception as e:
        raise RuntimeError(f"主服务失败: {primary_error}；备用 {fallback.model} 失败: {e}") from None
    return url, fallback.model, primary_error


def download_image(url: str, save_path: Path) -> None:
    """下载远程图片或解码 Base64 图片后保存到本地。"""
    if url.startswith("data:image/") and ";base64," in url:
        content = base64.b64decode(url.split(",", 1)[1], validate=True)
    else:
        resp = requests.get(url, timeout=DOWNLOAD_TIMEOUT)
        resp.raise_for_status()
        content = resp.content
    save_path.parent.mkdir(parents=True, exist_ok=True)
    save_path.write_bytes(content)


def record_image_url(url: str) -> str | None:
    """Base64 内容仅写入图片文件，生成台账只保留远程 URL。"""
    return None if url.startswith("data:") else url


def sanitize_filename(name: str) -> str:
    """清理文件名中的不安全字符。"""
    cleaned = re.sub(r'[<>:"/\\|?*]', "_", name)
    return cleaned.strip(". ")


def update_markdown_backgrounds(
    md_path: Path,
    stage_path_map: dict[int, str],
) -> int:
    """将生成的背景图绝对路径回填到剧本 Markdown 的 **背景图** 字段。

    在每个 '### 阶段N' 区块内，匹配 '**背景图**:' 行并替换为图片绝对路径。

    Args:
        md_path: 剧本 Markdown 文件路径
        stage_path_map: {阶段编号: 图片绝对路径} 映射

    Returns:
        成功回填的阶段数量
    """
    content = md_path.read_text(encoding="utf-8")
    updated_count = 0

    for stage_num, img_path in sorted(stage_path_map.items()):
        # 匹配该阶段区块内的 **背景图**: xxx 行
        # 兼容中英文冒号，以及冒号后有任意内容（包括默认提示语）
        pattern = re.compile(
            r"(###\s*阶段\s*" + str(stage_num) + r"\s*[:：].*?)"
            r"(\*\*背景图\*\*[ \t]*[:：][ \t]*)([^\n]*)",
            re.DOTALL,
        )
        match = pattern.search(content)
        if match:
            new_line = match.group(2) + img_path
            content = content[: match.start(2)] + new_line + content[match.end(3) :]
            updated_count += 1

    if updated_count:
        md_path.write_text(content, encoding="utf-8")

    return updated_count


# ── 主流程 ─────────────────────────────────────────────────
def process(
    md_path: str,
    output_dir: Optional[str] = None,
    model: str | None = None,
    size: str | None = None,
    style_suffix: str = DEFAULT_STYLE_SUFFIX,
    text_model: Optional[str] = None,
    use_llm_prompt: bool = True,
    secrets_file: str | Path | None = None,
) -> dict:
    """完整处理流程: 解析 → LLM 生成提示词 → 文生图 API → 下载保存。

    Args:
        md_path: 训练剧本配置 Markdown 文件路径
        output_dir: 输出目录（默认: 剧本文件同级 backgrounds/）
        model: 文生图模型名称
        size: 图片尺寸
        style_suffix: 风格后缀描述
        text_model: 文本模型名称（用于生成提示词），None 时从环境变量读取
        use_llm_prompt: 是否使用 LLM 生成提示词（False 时直接硬拼）

    Returns:
        结果摘要字典
    """
    md_file = Path(md_path)
    if not md_file.exists():
        raise FileNotFoundError(f"文件不存在: {md_file}")

    content = md_file.read_text(encoding="utf-8")

    # 1. 解析阶段
    print("📖 解析训练剧本...")
    stages = parse_script_markdown(content)
    if not stages:
        raise ValueError("未能从文档中解析出任何阶段信息")
    print(f"   ✓ 发现 {len(stages)} 个阶段")

    # 2. secrets 优先；明确传入的模型/尺寸覆盖其默认值。
    image_config = resolve_image_config(secrets_file, model, size)
    model, size = image_config.model, image_config.size
    fallback_model = image_config.fallback.model if image_config.fallback else None
    print(f"   生图模型: {model}，尺寸: {size}" + (f"，备用: {fallback_model}" if fallback_model else ""))

    # 3. 确定文本模型
    if text_model is None:
        llm_config = load_providers(secrets_file).get("llm") or {}
        if not isinstance(llm_config, dict):
            raise ValueError("secrets.providers.llm 必须是对象")
        text_model = llm_config.get("model") or os.environ.get("BAILIAN_TEXT_MODEL", DEFAULT_TEXT_MODEL)

    # 4. 确定输出目录（提前，封面图也需要）
    task_name = md_file.stem.replace("training_background_generator_", "")
    if output_dir:
        bg_dir = Path(output_dir) / f"backgrounds_{task_name}"
    else:
        bg_dir = md_file.parent / "backgrounds"
    bg_dir.mkdir(parents=True, exist_ok=True)
    print(f"\n📁 输出目录: {bg_dir}")

    # 4.5 封面图子流程
    cover_result: dict = {}
    print("\n🖼️  生成任务封面背景图...")
    basic_config = parse_basic_config(content)
    if not basic_config:
        print("   ⚠️  未找到 ##基础配置 section，跳过封面图生成")
    else:
        cfg_task_name = basic_config.get("task_name") or task_name
        cfg_task_desc = basic_config.get("task_desc", "")
        print(f"   任务名称: {cfg_task_name}")

        # 生成封面提示词
        try:
            if use_llm_prompt:
                text_client_cover = _get_text_client(secrets_file)
                cover_prompt = generate_cover_prompt_via_llm(
                    text_client_cover, cfg_task_name, cfg_task_desc, style_suffix, text_model
                )
                print(f"   ✓ LLM 封面提示词: {cover_prompt[:60]}...")
            else:
                cover_prompt = build_cover_prompt_fallback(cfg_task_name, cfg_task_desc, style_suffix)
                print(f"   封面提示词(fallback): {cover_prompt[:60]}...")
        except Exception as e:
            print(f"   ⚠️  封面提示词生成失败 ({e})，使用 fallback")
            cover_prompt = build_cover_prompt_fallback(cfg_task_name, cfg_task_desc, style_suffix)

        # 生成并下载封面图
        cover_filename = f"{sanitize_filename(cfg_task_name)}_cover.png"
        cover_save_path = bg_dir / cover_filename
        try:
            cover_url, cover_model, cover_primary_error = generate_with_fallback(cover_prompt, image_config)
            download_image(cover_url, cover_save_path)
            print(f"   ✓ 封面图已保存: {cover_save_path}")

            # 回填到 ##基础配置
            filled = update_markdown_cover_background(md_file, str(cover_save_path.resolve()))
            if filled:
                print("   ✓ 封面背景图路径已回填到 ##基础配置")
            else:
                print("   ⚠️  封面图路径回填失败（section 未找到）")

            cover_result = {
                "file": str(cover_save_path),
                "url": record_image_url(cover_url),
                "model": cover_model,
                "prompt": cover_prompt,
                "task_name": cfg_task_name,
            }
            if cover_primary_error:
                cover_result["primary_error"] = cover_primary_error
        except Exception as e:
            print(f"   ⚠️  封面图生成失败 ({e})，跳过封面图，继续阶段图生成")
            cover_result = {"error": str(e), "prompt": cover_prompt}

        # 封面生成后的间隔
        time.sleep(API_INTERVAL)

    # 5. 生成阶段提示词
    text_client = None
    if use_llm_prompt:
        print(f"\n🤖 使用 LLM ({text_model}) 智能生成提示词...")
        text_client = _get_text_client(secrets_file)
        llm_fail_count = 0
        for stage in stages:
            try:
                stage.prompt = generate_prompt_via_llm(
                    text_client, stage, style_suffix, text_model
                )
                print(f"   ✓ 阶段{stage.number} [{stage.name}]: {stage.prompt[:60]}...")
            except Exception as e:
                print(f"   ⚠️  阶段{stage.number} LLM 生成失败 ({e})，使用 fallback")
                stage.prompt = build_prompt_fallback(stage, style_suffix)
                llm_fail_count += 1
            # LLM 调用间隔
            time.sleep(1)
        if llm_fail_count:
            print(f"   ⚠️  {llm_fail_count} 个阶段使用了 fallback 硬拼提示词")
    else:
        print("\n🎨 使用 fallback 硬拼提示词...")
        for stage in stages:
            stage.prompt = build_prompt_fallback(stage, style_suffix)
            print(f"   阶段{stage.number} [{stage.name}]: {stage.prompt[:60]}...")

    # 6. 逐阶段生成并下载
    results: list[dict] = []
    failed: list[dict] = []

    for idx, stage in enumerate(stages):
        # 包含任务名称信息
        filename = f"{task_name}_stage_{stage.number}_{sanitize_filename(stage.name)}.png"
        save_path = bg_dir / filename

        print(f"\n🖼️  阶段{stage.number}: {stage.name}")
        print(f"   提示词: {stage.prompt[:80]}...")

        try:
            url, used_model, primary_error = generate_with_fallback(stage.prompt, image_config)
            print(f"   ✓ 生成成功（{used_model}），下载中...")

            download_image(url, save_path)
            print(f"   ✓ 已保存: {save_path}")

            entry = {
                "stage": stage.number,
                "name": stage.name,
                "file": str(save_path),
                "url": record_image_url(url),
                "model": used_model,
                "prompt": stage.prompt,
            }
            if primary_error:
                entry["primary_error"] = primary_error
            results.append(entry)
        except Exception as e:
            print(f"   ❌ 失败: {e}")
            failed.append(
                {
                    "stage": stage.number,
                    "name": stage.name,
                    "error": str(e),
                    "prompt": stage.prompt,
                }
            )

        # API 限流保护
        if idx < len(stages) - 1:
            time.sleep(API_INTERVAL)

    # 7. 回填背景图路径到剧本 Markdown
    if results:
        stage_path_map = {r["stage"]: str(Path(r["file"]).resolve()) for r in results}
        filled = update_markdown_backgrounds(md_file, stage_path_map)
        if filled:
            print(f"\n📝 已回填 {filled} 个阶段的背景图路径到剧本文件")
        else:
            print("\n⚠️  未能回填背景图路径（可能剧本中缺少 **背景图** 字段）")

    # 8. 保存生成记录
    record_path = bg_dir / "generation_record.json"
    record = {
        "source": str(md_file),
        "model": model,
        "fallback_model": fallback_model,
        "text_model": text_model if use_llm_prompt else None,
        "size": size,
        "style_suffix": style_suffix,
        "prompt_mode": "llm" if use_llm_prompt else "fallback",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "cover": cover_result,
        "success": results,
        "failed": failed,
    }
    record_path.write_text(
        json.dumps(record, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\n📋 生成记录已保存: {record_path}")

    # 9. 汇总
    print(f"\n{'=' * 50}")
    print(f"✨ 完成! 成功: {len(results)}/{len(stages)}")
    if failed:
        print(f"❌ 失败: {len(failed)} 个阶段")
        for f in failed:
            print(f"   - 阶段{f['stage']} {f['name']}: {f['error']}")

    return record


# ── CLI ────────────────────────────────────────────────────
def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="训练阶段背景图生成器 — 优先使用 secrets.json 的图片主配置，失败时改用备用配置",
    )
    parser.add_argument(
        "markdown_file",
        type=str,
        help="训练剧本配置 Markdown 文件路径",
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        type=str,
        default=None,
        help="输出目录（默认: 剧本文件同级 backgrounds/）",
    )
    parser.add_argument(
        "--model",
        "-m",
        type=str,
        default=None,
        help="文生图模型（默认读取 secrets 的 providers.image.model；无配置时使用百炼）",
    )
    parser.add_argument(
        "--size",
        "-s",
        type=str,
        default=None,
        help="图片尺寸（默认读取 secrets 的 providers.image.size）",
    )
    parser.add_argument(
        "--style",
        type=str,
        default=DEFAULT_STYLE_SUFFIX,
        help="风格描述后缀，会附加到每个阶段提示词末尾",
    )
    parser.add_argument(
        "--text-model",
        type=str,
        default=None,
        help=f"文本模型（默认读取 secrets.providers.llm.model，再读取.env，最后为 {DEFAULT_TEXT_MODEL}）",
    )
    parser.add_argument(
        "--no-llm-prompt",
        action="store_true",
        default=False,
        help="跳过 LLM 生成提示词，直接使用硬拼方式（fallback）",
    )
    parser.add_argument(
        "--secrets-file", type=str, default=None,
        help=f"凭证文件路径（默认: {DEFAULT_SECRETS_FILE}）",
    )
    return parser.parse_args(argv)


def main() -> int:
    args = parse_args()
    try:
        process(
            md_path=args.markdown_file,
            output_dir=args.output_dir,
            model=args.model,
            size=args.size,
            style_suffix=args.style,
            text_model=args.text_model,
            use_llm_prompt=not args.no_llm_prompt,
            secrets_file=args.secrets_file,
        )
        return 0
    except FileNotFoundError as e:
        print(f"❌ {e}", file=sys.stderr)
        return 1
    except EnvironmentError as e:
        print(f"❌ {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"❌ {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"❌ 未预期的错误: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
