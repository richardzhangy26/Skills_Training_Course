#!/usr/bin/env python3
"""Generate capability-training assets with Doubao.

This script wraps the Doubao(OpenAI-compatible) API so that we can reproduce
the behaviour of the training-script-generator and training-dialogue-simulator
skills without depending on Anthropic. Provide an input task document and the
script will create the Markdown outputs beside that document.
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from turtle import dot
from typing import Dict, Iterable, List
from dotenv import load_dotenv
from openai import OpenAI


BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
DEFAULT_MODEL = "doubao-seed-1-6-251015"
SCRIPT_DIR = Path(__file__).resolve().parent
ARK_API_KEY = load_dotenv()

SCRIPT_SYSTEM_PROMPT = """您是“training-script-generator”技能，一名擅长将实训任务文档转换成可落地能力训练剧本配置的专家。严格基于文档内容输出 Markdown，遵循以下要点：
1. 绝不编造文档中不存在的信息。
2. 输出结构必须包含：基础配置、训练阶段（含阶段描述、互动轮次、开场白代码块、LangGPT 提示词代码块、场景配置）、阶段跳转关系、配置说明。
3. LangGPT 提示词要以代码块展示，并严格遵循 Role/Profile/Task/Workflow/Rules/Constraints/Context/Examples/跳转指令 的顺序。
4. 如果文档提供了开场白或对话示例，必须原文引用在相应字段或 Examples 部分。
5. 所有章节标题使用中文示例中的格式，例如 “## 📋 基础配置”、“### 阶段1: …”。
"""


DIALOGUE_SYSTEM_PROMPT = """您是“training-dialogue-simulator”技能，一名对话测试脚本专家。请完全依据实训文档生成完整的对话流程 Markdown，注意：
1. 智能体话术、开场白、追问必须与文档原文保持一致，不得换词。
2. 输出包含：智能体角色设定、对话目标、逐阶段对话流程（含分支、追问目的、预期回答）、至少三条不同表现水平的示例对话、评分对照表、测试要点与步骤。
3. 清晰分隔每个分支，使用四级标题 “##### 分支X: …”，并在分支内部列出学生原话、智能体追问、追问目的、预期回答。
4. Markdown 需易于复制粘贴，禁止输出额外解释。
"""


@dataclass
class SkillConfig:
    name: str
    system_prompt: str
    output_filename: str
    user_prompt_template: str
    instruction_text: str


SCRIPT_USER_TEMPLATE = """你将获得一份实训任务 Markdown 文档，请根据该文档生成完整的训练剧本配置，确保内容覆盖 instructions 中的全部要素。

# 输出要求
- 面向中国高校教师，使用正式中文。
- 使用 Markdown 组织内容。
- 仅返回最终配置，不要添加额外说明。

# 任务元数据
- 任务名称: {task_name}
- 输入文档路径: {doc_path}

# 实训任务文档
```
{doc_text}
```
"""


DIALOGUE_USER_TEMPLATE = """你将获得一份实训任务 Markdown 文档，请生成完整的能力训练对话流程模拟文档，帮助测试者验证所有分支和评分要点。

# 输出要求
- 严格复现文档中的开场、追问、关键词提示。
- 对话分支需要标注“学生说”、“智能体追问”、“追问目的”、“预期学生回答”。
- 提供优秀 / 中等 / 欠佳 三个完整示例对话，以及评分对照表和测试步骤。

# 任务元数据
- 任务名称: {task_name}
- 输入文档路径: {doc_path}

# 实训任务文档
```
{doc_text}
```
"""


def load_instruction(*relative_parts: str) -> str:
    path = SCRIPT_DIR / Path(*relative_parts)
    if not path.exists():
        raise FileNotFoundError(f"Skill instruction file not found: {path}")
    return path.read_text(encoding="utf-8")


def combine_instructions(paths: List[List[str]]) -> str:
    chunks: List[str] = []
    for parts in paths:
        text = load_instruction(*parts)
        filename = parts[-1]
        chunks.append(f"## {filename}\n{text}")
    return "\n\n".join(chunks)


SKILLS: Dict[str, SkillConfig] = {
    "script": SkillConfig(
        name="训练剧本配置",
        system_prompt=SCRIPT_SYSTEM_PROMPT,
        output_filename="训练剧本配置.md",
        user_prompt_template=SCRIPT_USER_TEMPLATE,
        instruction_text=combine_instructions(
            [
                ["training-script-generator", "SKILL.md"],
                ["training-script-generator", "reference.md"],
                ["training-script-generator", "examples.md"],
            ]
        ),
    ),
    "dialogue": SkillConfig(
        name="对话流程模拟",
        system_prompt=DIALOGUE_SYSTEM_PROMPT,
        output_filename="对话流程模拟.md",
        user_prompt_template=DIALOGUE_USER_TEMPLATE,
        instruction_text=combine_instructions(
            [
                ["training-dialogue-simulator", "SKILL.md"],
                ["training-dialogue-simulator", "examples.md"],
            ]
        ),
    ),
}


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Use Doubao to run training-script-generator and training-dialogue-simulator skills",
    )
    parser.add_argument(
        "document",
        type=Path,
        help="Path to the input training task Markdown document",
    )
    parser.add_argument(
        "--skills",
        nargs="+",
        choices=SKILLS.keys(),
        default=list(SKILLS.keys()),
        help="Which skills to run (default: both)",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Doubao model ID (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--api-key",
        default=os.getenv("ARK_API_KEY"),
        help="API key, falls back to ARK_API_KEY env var",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.2,
        help="Sampling temperature for the completion",
    )
    parser.add_argument(
        "--top-p",
        type=float,
        default=0.9,
        help="Top-p value for nucleus sampling",
    )
    return parser.parse_args(list(argv))


def ensure_api_key(value: str | None) -> str:
    if not value:
        raise SystemExit(
            "Missing API key. Provide --api-key or export ARK_API_KEY before running this script."
        )
    return value


def read_document(path: Path) -> str:
    if not path.exists():
        raise SystemExit(f"Document not found: {path}")
    return path.read_text(encoding="utf-8")


def create_client(api_key: str) -> OpenAI:
    return OpenAI(base_url=BASE_URL, api_key=api_key)


def call_skill(
    client: OpenAI,
    *,
    config: SkillConfig,
    doc_text: str,
    doc_path: Path,
    model: str,
    temperature: float,
    top_p: float,
) -> str:
    task_name = doc_path.stem
    user_prompt = config.user_prompt_template.format(
        task_name=task_name,
        doc_path=str(doc_path),
        doc_text=doc_text,
    )
    full_system_prompt = (
        f"{config.system_prompt}\n\n# 技能文档\n{config.instruction_text}"
    )
    response = client.chat.completions.create(
        model=model,
        temperature=temperature,
        top_p=top_p,
        messages=[
            {"role": "system", "content": full_system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    message = response.choices[0].message
    if message is None or message.content is None:
        raise RuntimeError("Doubao returned an empty response")
    return message.content


def write_output(doc_path: Path, filename: str, content: str) -> Path:
    target_dir = doc_path.parent / doc_path.stem
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / filename
    target_path.write_text(content, encoding="utf-8")
    return target_path


def main(argv: Iterable[str]) -> int:
    args = parse_args(argv)
    api_key = ensure_api_key(args.api_key)
    doc_text = read_document(args.document)
    client = create_client(api_key)

    outputs: List[str] = []
    for skill_key in args.skills:
        config = SKILLS[skill_key]
        print(f"Running {skill_key} skill for {args.document} …", file=sys.stderr)
        content = call_skill(
            client,
            config=config,
            doc_text=doc_text,
            doc_path=args.document,
            model=args.model,
            temperature=args.temperature,
            top_p=args.top_p,
        )
        output_path = write_output(args.document, config.output_filename, content)
        outputs.append(f"{config.name}: {output_path}")

    print("\n生成完成:")
    for line in outputs:
        print(f"- {line}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
