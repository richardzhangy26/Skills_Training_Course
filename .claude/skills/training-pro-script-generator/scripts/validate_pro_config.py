#!/usr/bin/env python3
"""Validate generated Ability Training Pro Markdown configuration."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = SKILL_ROOT / "references" / "resource_catalog.json"
RUNTIME_VALUE = "运行时解析"


def load_catalog() -> dict:
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def section_blocks(text: str, pattern: str) -> list[tuple[str, str]]:
    matches = list(re.finditer(pattern, text, re.MULTILINE))
    blocks = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        blocks.append((match.group(1).strip(), text[match.start():end]))
    return blocks


def field(block: str, name: str) -> str:
    match = re.search(rf"^- \*\*{re.escape(name)}\*\*:\s*(.*)$", block, re.MULTILINE)
    return match.group(1).strip() if match else ""


def stage_field(block: str, name: str) -> str:
    match = re.search(rf"^\*\*{re.escape(name)}\*\*:\s*(.*)$", block, re.MULTILINE)
    return match.group(1).strip() if match else ""


def validate_member(
    name: str,
    block: str,
    voice_by_id: dict[str, dict],
    avatar_ids: set[str],
) -> list[str]:
    errors = []
    required = (
        "角色名称",
        "角色描述",
        "角色提示词",
        "模型",
        "数字人名称",
        "数字人类型",
        "声音名称",
        "声音资源ID",
        "声音参数",
        "声音选择条件",
        "形象资源ID",
        "形象描述",
        "数字人组合ID",
    )
    for item in required:
        if not field(block, item):
            errors.append(f"成员 {name} 缺少字段：{item}")

    prompt = field(block, "角色提示词")
    if prompt and len(prompt) < 80:
        errors.append(f"成员 {name} 的角色提示词少于 80 字")

    voice_id = field(block, "声音资源ID")
    voice_type = field(block, "声音参数")
    if voice_id and voice_id != RUNTIME_VALUE:
        voice = voice_by_id.get(voice_id)
        if not voice:
            errors.append(f"成员 {name} 使用未知声音资源ID：{voice_id}")
        elif voice_type != voice.get("voiceType"):
            errors.append(f"成员 {name} 的声音资源ID与声音参数不匹配")

    avatar_id = field(block, "形象资源ID")
    if avatar_id and avatar_id != RUNTIME_VALUE and avatar_id not in avatar_ids:
        errors.append(f"成员 {name} 使用未知形象资源ID：{avatar_id}")

    if field(block, "数字人组合ID") != RUNTIME_VALUE:
        errors.append(f"成员 {name} 的数字人组合ID必须写“{RUNTIME_VALUE}”")

    instructions = re.findall(
        r"<skill_instruction>(.*?)</skill_instruction>", block, re.DOTALL
    )
    if not instructions:
        errors.append(f"成员 {name} 至少需要一个 skill_instruction")
    instruction_headings = (
        "### 命令",
        "### 使用场景",
        "### 执行规则",
        "### 输出解释",
        "### 示例",
    )
    for index, instruction in enumerate(instructions, start=1):
        for heading in instruction_headings:
            if heading not in instruction:
                errors.append(f"成员 {name} 的技能 {index} 缺少 {heading}")
    return errors


def validate_text(text: str) -> list[str]:
    catalog = load_catalog()
    voice_by_id = {item["nid"]: item for item in catalog["voices"]}
    avatar_ids = {item["nid"] for item in catalog["avatars"]}
    errors: list[str] = []

    for heading in ("## 全局配置", "## 全局成员配置", "## 训练剧本"):
        if heading not in text:
            errors.append(f"缺少章节：{heading}")

    placeholder = re.search(
        r"\[[^\]]*(?:从文档|填写|成员名|阶段名|描述xxx|具体操作|选填)[^\]]*\]",
        text,
    )
    if placeholder:
        errors.append(f"存在模板占位符：{placeholder.group(0)}")

    if re.search(r"NEXT_TO_|GOTO_|conditionRule|flowCondition", text, re.IGNORECASE):
        errors.append("存在普通版能力训练的旧版跳转指令")

    members = section_blocks(text, r"^### 成员\d+:\s*(.+)$")
    if not members:
        errors.append("至少需要一个全局成员")
    member_names = {name for name, _ in members}
    for name, block in members:
        errors.extend(validate_member(name, block, voice_by_id, avatar_ids))

    stages = section_blocks(text, r"^### 阶段\d+:\s*(.+)$")
    if not stages:
        errors.append("至少需要一个训练阶段")
    dimensions = (
        "【阶段触发条件】",
        "【背景设定】",
        "【完整执行流程】",
        "【阶段结束判定】",
        "【行为边界规范】",
    )
    for index, (name, block) in enumerate(stages):
        for item in (
            "卡片描述",
            "用户扮演角色名称",
            "AI 对用户称呼",
            "用户扮演角色描述",
            "剧本模型",
            "对话结束策略",
            "是否可跳过",
            "后继阶段",
            "背景图描述",
        ):
            if not stage_field(block, item):
                errors.append(f"阶段 {name} 缺少字段：{item}")
        for dimension in dimensions:
            if dimension not in block:
                errors.append(f"阶段 {name} 缺少 {dimension}")

        expected_next = stages[index + 1][0] if index + 1 < len(stages) else "END"
        actual_next = stage_field(block, "后继阶段")
        if actual_next and actual_next != expected_next:
            errors.append(
                f"阶段 {name} 的后继阶段应为 {expected_next}，实际为 {actual_next}"
            )

    script_prompts = re.findall(r"<script_prompt>(.*?)</script_prompt>", text, re.DOTALL)
    for script_prompt in script_prompts:
        for mention in re.findall(r"@([^\s，。；、：:（）()]+)", script_prompt):
            if mention not in member_names:
                errors.append(f"引用了未定义成员 @{mention}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="校验能力训练 Pro 配置 Markdown")
    parser.add_argument("config", type=Path)
    args = parser.parse_args()
    errors = validate_text(args.config.read_text(encoding="utf-8"))
    if errors:
        print("校验失败：")
        for error in errors:
            print(f"- {error}")
        return 1
    print("校验通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
