#!/usr/bin/env python3
"""
训练阶段背景图生成器（Polymas API 版本）

解析训练剧本配置 Markdown，为每个阶段:
1. 由 LLM（Doubao 文本模型）理解阶段上下文，智能生成文生图提示词
2. 调用 Polymas 代理的 Doubao Seedream 文生图 API 生成背景图
3. 下载保存到本地 backgrounds/ 目录

依赖安装:
    pip install requests python-dotenv openai

环境变量（从 .claude/skills/.env 加载）:
    LLM_API_KEY: Polymas API 密钥（必需）
    LLM_API_URL: Polymas API 基础URL（可选，有默认值）
    LLM_MODEL: 文本模型名称（可选，默认 Doubao-1.5-pro-32k）

使用方式:
    python generate_background.py <剧本配置.md> [--output-dir <目录>] [--model <模型名>] [--size <尺寸>] [--style <风格描述>]
    python generate_background.py <剧本配置.md> --no-llm-prompt  # 跳过 LLM 生成，直接硬拼提示词
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import requests
from dotenv import load_dotenv

# ── .env 加载 ───────────────────────────────────────────────
# 脚本位于 .claude/skills/training-background-generator/scripts/
# .env 位于 .claude/skills/.env
_SCRIPT_DIR = Path(__file__).resolve().parent
_ENV_PATH = _SCRIPT_DIR.parent.parent / ".env"
if _ENV_PATH.exists():
    load_dotenv(_ENV_PATH)
else:
    # 也尝试项目根目录的 .env
    _ROOT_ENV = _SCRIPT_DIR.parent.parent.parent.parent / ".env"
    if _ROOT_ENV.exists():
        load_dotenv(_ROOT_ENV)

# ── 默认配置 ───────────────────────────────────────────────
DEFAULT_IMAGE_MODEL = "doubao-seedream-3-0-t2i-250415"
DEFAULT_SIZE = "768x432"  # 16:9，Polymas API 范围 256-768
DEFAULT_STYLE_SUFFIX = (
    "写实风格，中国风元素，专业级渲染，电影级光影，高清细节，16:9宽屏构图"
)
POLYMAS_IMAGE_URL = "https://llm-service.polymas.com/api/openai/v1/images/generations"
POLYMAS_CHAT_BASE_URL = "https://llm-service.polymas.com/api/openai/v1"
DEFAULT_TEXT_MODEL = "Claude Sonnet 4.5"

# 下载超时（秒）
DOWNLOAD_TIMEOUT = 60
# API 调用间隔（秒），避免触发限流
API_INTERVAL = 2


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


def _get_text_client():
    """创建用于生成提示词的 OpenAI 兼容客户端（通过 Polymas 代理）。"""
    from openai import OpenAI

    api_key = os.environ.get("LLM_API_KEY") or os.environ.get("ARK_API_KEY")
    if not api_key:
        raise EnvironmentError("请设置 LLM_API_KEY 或 ARK_API_KEY 环境变量。")

    # 从 LLM_API_URL 中提取 base_url（去掉末尾的 /chat/completions）
    raw_url = os.environ.get("LLM_API_URL", POLYMAS_CHAT_BASE_URL)
    base_url = re.sub(r"/chat/completions/?$", "", raw_url)

    return OpenAI(base_url=base_url, api_key=api_key)


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
            r"- \*\*背景图\*\*\s*[:：]\s*[^\n]*",
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
def generate_image(prompt: str, model: str, size: str, api_key: str) -> str:
    """调用 Polymas 代理的 Doubao Seedream 文生图 API，返回图片 URL。

    注意: Polymas API 使用 'api-key' 请求头而非 'Authorization: Bearer'。
    """
    headers = {
        "api-key": api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "prompt": prompt,
        "size": size,
        "watermark": False,
        "response_format": "url",
    }
    resp = requests.post(
        POLYMAS_IMAGE_URL,
        headers=headers,
        json=payload,
        timeout=120,
    )
    resp.raise_for_status()

    data = resp.json()
    url = data["data"][0]["url"]
    if not url:
        raise RuntimeError("API 返回的图片 URL 为空")
    return url


def download_image(url: str, save_path: Path) -> None:
    """从 URL 下载图片并保存到本地。"""
    resp = requests.get(url, timeout=DOWNLOAD_TIMEOUT)
    resp.raise_for_status()
    save_path.parent.mkdir(parents=True, exist_ok=True)
    save_path.write_bytes(resp.content)


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
            r"(\*\*背景图\*\*\s*[:：]\s*)([^\n]*)",
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
    model: str = DEFAULT_IMAGE_MODEL,
    size: str = DEFAULT_SIZE,
    style_suffix: str = DEFAULT_STYLE_SUFFIX,
    text_model: Optional[str] = None,
    use_llm_prompt: bool = True,
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

    # 2. 获取 API Key
    api_key = os.environ.get("LLM_API_KEY") or os.environ.get("ARK_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "请设置 LLM_API_KEY 或 ARK_API_KEY 环境变量。\n"
            "  在 .claude/skills/.env 中配置 LLM_API_KEY=sk-xxx"
        )

    # 3. 确定文本模型
    if text_model is None:
        text_model = os.environ.get("LLM_MODEL", DEFAULT_TEXT_MODEL)

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
            text_client_cover = _get_text_client()
            if use_llm_prompt:
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
            cover_url = generate_image(cover_prompt, model, size, api_key)
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
                "url": cover_url,
                "prompt": cover_prompt,
                "task_name": cfg_task_name,
            }
        except Exception as e:
            print(f"   ⚠️  封面图生成失败 ({e})，跳过封面图，继续阶段图生成")
            cover_result = {"error": str(e), "prompt": cover_prompt}

        # 封面生成后的间隔
        time.sleep(API_INTERVAL)

    # 5. 生成阶段提示词
    text_client = None
    if use_llm_prompt:
        print(f"\n🤖 使用 LLM ({text_model}) 智能生成提示词...")
        text_client = _get_text_client()
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
            url = generate_image(stage.prompt, model, size, api_key)
            print("   ✓ 生成成功，下载中...")

            download_image(url, save_path)
            print(f"   ✓ 已保存: {save_path}")

            results.append(
                {
                    "stage": stage.number,
                    "name": stage.name,
                    "file": str(save_path),
                    "url": url,
                    "prompt": stage.prompt,
                }
            )
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
        description="训练阶段背景图生成器 — 解析剧本 Markdown 并生成阶段背景图（Polymas API 版本）",
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
        default=DEFAULT_IMAGE_MODEL,
        help=f"文生图模型名称（默认: {DEFAULT_IMAGE_MODEL}）",
    )
    parser.add_argument(
        "--size",
        "-s",
        type=str,
        default=DEFAULT_SIZE,
        help=f"图片尺寸（默认: {DEFAULT_SIZE}）",
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
        help=f"文本模型名称，用于智能生成提示词（默认从.env读取，fallback: {DEFAULT_TEXT_MODEL}）",
    )
    parser.add_argument(
        "--no-llm-prompt",
        action="store_true",
        default=False,
        help="跳过 LLM 生成提示词，直接使用硬拼方式（fallback）",
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
