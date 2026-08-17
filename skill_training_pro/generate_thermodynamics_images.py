#!/usr/bin/env python3
"""Generate digital-human portraits and stage backgrounds for the
thermodynamics museum Pro task.

Reuses the image generation engine of the training-background-generator
skill (Bailian qwen-image via DashScope). Prompts come from the Pro
configuration Markdown: member 形象描述 for portraits, stage 背景图描述
for backgrounds. Existing files are skipped unless --force is supplied.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
GENERATOR_PATH = (
    PROJECT_ROOT
    / ".claude"
    / "skills"
    / "training-background-generator"
    / "scripts"
    / "generate_background.py"
)
DEFAULT_CONFIG_PATH = (
    PROJECT_ROOT
    / "skills_training_course"
    / "skill_training_pro"
    / "天津大学-热力学"
    / "热力学名人博物馆沉浸式训练-Pro配置.md"
)
DEFAULT_OUTPUT_DIR = DEFAULT_CONFIG_PATH.parent / "backgrounds"
DEFAULT_MODEL = "qwen-image-2.0-pro"
PORTRAIT_SIZE = "928x1664"
BACKGROUND_SIZE = "1664x928"
PORTRAIT_SUFFIX = (
    "，正面半身肖像，人物居中，头部完整入镜，目光直视镜头，"
    "博物馆暖色灯光背景虚化，高清细腻，写实复古油画质感"
)
BACKGROUND_SUFFIX = "，写实复古风格，画面中不出现人物，16:9横幅构图"
COVER_SUFFIX = "，写实复古油画质感，画面庄重大气，横幅构图"
API_INTERVAL_SECONDS = 15
RETRY_LIMIT = 4
RETRY_BASE_WAIT = 30


def load_generator_module():
    spec = importlib.util.spec_from_file_location("generate_background", GENERATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules["generate_background"] = module
    spec.loader.exec_module(module)
    return module


def member_field(block: str, name: str) -> str:
    match = re.search(rf"^- \*\*{re.escape(name)}\*\*:\s*(.*)$", block, re.MULTILINE)
    if not match:
        raise ValueError(f"成员配置缺少字段：{name}")
    return match.group(1).strip()


def stage_field(block: str, name: str) -> str:
    match = re.search(rf"^\*\*{re.escape(name)}\*\*:\s*(.*)$", block, re.MULTILINE)
    if not match:
        raise ValueError(f"阶段配置缺少字段：{name}")
    return match.group(1).strip()


def parse_image_specs(config_path: Path) -> tuple[list[dict], list[dict]]:
    text = config_path.read_text(encoding="utf-8")

    members: list[dict] = []
    member_matches = list(re.finditer(r"^### 成员\d+:\s*(.+?)\s*$", text, re.MULTILINE))
    for index, match in enumerate(member_matches):
        end = (
            member_matches[index + 1].start()
            if index + 1 < len(member_matches)
            else text.find("## 训练剧本")
        )
        block = text[match.start() : end]
        members.append(
            {
                "nickname": match.group(1).strip(),
                "description": member_field(block, "形象描述"),
            }
        )

    stages: list[dict] = []
    stage_matches = list(re.finditer(r"^### 阶段(\d+):\s*(.+?)\s*$", text, re.MULTILINE))
    for index, match in enumerate(stage_matches):
        end = stage_matches[index + 1].start() if index + 1 < len(stage_matches) else len(text)
        block = text[match.start() : end]
        stages.append(
            {
                "number": int(match.group(1)),
                "name": match.group(2).strip(),
                "description": stage_field(block, "背景图描述"),
            }
        )

    if not members or not stages:
        raise ValueError(f"未能从 {config_path} 解析成员或阶段")
    return members, stages


def global_field(config_path: Path, name: str) -> str:
    text = config_path.read_text(encoding="utf-8")
    match = re.search(rf"^- \*\*{re.escape(name)}\*\*:\s*(.*)$", text, re.MULTILINE)
    if not match:
        raise ValueError(f"全局配置缺少字段：{name}")
    return match.group(1).strip()


def sanitize(name: str) -> str:
    cleaned = re.sub(r"[<>:\"/\\|?*：:，,]", "_", name)
    return cleaned.strip(" ._")


def generate_one(
    generator,
    *,
    api_key: str,
    model: str,
    prompt: str,
    size: str,
    save_path: Path,
    force: bool,
    record: dict,
    record_path: Path,
) -> bool:
    if save_path.exists() and not force:
        print(f"跳过已存在: {save_path.name}")
        return False
    url = None
    for attempt in range(1, RETRY_LIMIT + 1):
        try:
            url = generator.generate_image(prompt, model, size, api_key)
            break
        except requests.HTTPError as exc:
            if exc.response is not None and exc.response.status_code == 429 and attempt < RETRY_LIMIT:
                wait_seconds = RETRY_BASE_WAIT * attempt
                print(f"限流(429)，{wait_seconds}s 后重试（{attempt}/{RETRY_LIMIT - 1}）: {save_path.name}")
                time.sleep(wait_seconds)
                continue
            raise
    assert url
    generator.download_image(url, save_path)
    record[str(save_path)] = {
        "prompt": prompt,
        "model": model,
        "size": size,
        "url": url,
    }
    record_path.write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"已生成: {save_path.name}")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="生成热力学博物馆 Pro 任务的形象与背景图")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--force", action="store_true", help="重新生成已存在的图片")
    args = parser.parse_args()

    load_dotenv(PROJECT_ROOT / ".env", override=True)
    api_key = os.getenv("BAILIAN_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(".env 缺少 BAILIAN_API_KEY")

    generator = load_generator_module()
    members, stages = parse_image_specs(args.config)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    record_path = args.output_dir / "generation_record.json"
    record = (
        json.loads(record_path.read_text(encoding="utf-8"))
        if record_path.exists()
        else {}
    )

    generated = 0
    cover_prompt = global_field(args.config, "封面图描述") + COVER_SUFFIX
    cover_path = args.output_dir / f"cover_{sanitize(global_field(args.config, '能力名称'))}.png"
    if generate_one(
        generator,
        api_key=api_key,
        model=args.model,
        prompt=cover_prompt,
        size=BACKGROUND_SIZE,
        save_path=cover_path,
        force=args.force,
        record=record,
        record_path=record_path,
    ):
        generated += 1
        time.sleep(API_INTERVAL_SECONDS)

    for member in members:
        prompt = member["description"] + PORTRAIT_SUFFIX
        save_path = args.output_dir / f"avatar_{member['nickname']}.png"
        if generate_one(
            generator,
            api_key=api_key,
            model=args.model,
            prompt=prompt,
            size=PORTRAIT_SIZE,
            save_path=save_path,
            force=args.force,
            record=record,
            record_path=record_path,
        ):
            generated += 1
            time.sleep(API_INTERVAL_SECONDS)

    for stage in stages:
        prompt = stage["description"] + BACKGROUND_SUFFIX
        save_path = args.output_dir / f"background_stage_{stage['number']}_{sanitize(stage['name'])}.png"
        if generate_one(
            generator,
            api_key=api_key,
            model=args.model,
            prompt=prompt,
            size=BACKGROUND_SIZE,
            save_path=save_path,
            force=args.force,
            record=record,
            record_path=record_path,
        ):
            generated += 1
            time.sleep(API_INTERVAL_SECONDS)

    print(f"完成：新生成 {generated} 张，输出目录 {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
