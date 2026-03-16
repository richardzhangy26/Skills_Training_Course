#!/usr/bin/env python3
"""根据训练剧本 Markdown 自动创建能力训练基础配置。

默认只创建基础配置；通过 --with-steps 可以在创建成功后继续导入阶段节点和连线。
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List

import requests
from nanoid import generate

try:
    from skill_training_build.create_task_from_markdown import (
        build_steps_from_markdown,
        delete_existing_steps_and_flows,
        extract_start_end_ids,
        get_headers,
        load_env_config,
        normalize_md_value,
        parse_markdown,
        query_script_step_flows,
        query_script_steps,
        upload_cover_image,
    )
except ImportError:
    from create_task_from_markdown import (
        build_steps_from_markdown,
        delete_existing_steps_and_flows,
        extract_start_end_ids,
        get_headers,
        load_env_config,
        normalize_md_value,
        parse_markdown,
        query_script_step_flows,
        query_script_steps,
        upload_cover_image,
    )


API_URL = "https://cloudapi.polymas.com/teacher-course/abilityTrain/createConfiguration"
ROOT_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
PLACEHOLDER_VALUES = {
    "",
    "待生成",
    "(待生成)",
    "（待生成）",
    "选填",
    "(选填)",
    "（选填）",
}


@dataclass(frozen=True)
class BaseConfiguration:
    train_task_name: str
    description: str
    background_image: str = ""


def extract_base_field(content: str, label: str) -> str:
    pattern = re.compile(
        rf"^\s*-\s*\*\*{re.escape(label)}\*\*\s*[：:]\s*(.+?)\s*$",
        flags=re.MULTILINE,
    )
    match = pattern.search(content)
    if not match:
        return ""
    return normalize_md_value(match.group(1))


def is_placeholder_value(value: str) -> bool:
    normalized = normalize_md_value(value).strip()
    compact = normalized.replace(" ", "")
    return compact in PLACEHOLDER_VALUES


def parse_base_configuration(markdown_path: Path) -> BaseConfiguration:
    content = markdown_path.read_text(encoding="utf-8")
    train_task_name = extract_base_field(content, "任务名称")
    description = extract_base_field(content, "任务描述")
    background_image = extract_base_field(content, "背景图")

    if not train_task_name:
        raise ValueError("Markdown 缺少基础配置字段：任务名称")
    if not description:
        raise ValueError("Markdown 缺少基础配置字段：任务描述")

    return BaseConfiguration(
        train_task_name=train_task_name,
        description=description,
        background_image=background_image,
    )


def resolve_image_path(markdown_path: Path, image_value: str) -> Path:
    if re.match(r"^[a-zA-Z]+://", image_value):
        raise ValueError(f"背景图必须是本地文件路径，当前值不支持：{image_value}")

    image_path = Path(image_value)
    if not image_path.is_absolute():
        image_path = (markdown_path.parent / image_path).resolve()

    if not image_path.exists():
        raise FileNotFoundError(f"背景图不存在：{image_path}")
    return image_path


def resolve_cover_image(markdown_path: Path, base_config: BaseConfiguration, steps: List[Dict]) -> Path:
    candidates = []
    if not is_placeholder_value(base_config.background_image):
        candidates.append(base_config.background_image)

    for step in steps:
        background_image = normalize_md_value(step.get("backgroundImage", ""))
        if not is_placeholder_value(background_image):
            candidates.append(background_image)
            break

    for candidate in candidates:
        if candidate:
            return resolve_image_path(markdown_path, candidate)

    raise ValueError("未找到可用背景图：基础配置背景图为空，且第一阶段背景图也为空。")


def require_course_id() -> str:
    course_id = os.getenv("COURSE_ID", "").strip()
    if not course_id:
        raise ValueError("缺少 COURSE_ID，请在 .env 或系统环境变量中配置。")
    return course_id


def write_root_task_id(train_task_id: str, env_path: Path = ROOT_ENV_PATH) -> Path:
    env_path = Path(env_path)
    task_line = f'TASK_ID="{train_task_id}"\n'

    if env_path.exists():
        original_text = env_path.read_text(encoding="utf-8")
        lines = original_text.splitlines(keepends=True)
        kept_lines = [
            line for line in lines
            if not re.match(r"^\s*TASK_ID\s*=", line)
        ]
        new_text = "".join(kept_lines)
        if new_text and not new_text.endswith("\n"):
            new_text += "\n"
        new_text += task_line
    else:
        env_path.parent.mkdir(parents=True, exist_ok=True)
        new_text = task_line

    env_path.write_text(new_text, encoding="utf-8")
    os.environ["TASK_ID"] = train_task_id
    return env_path


def build_create_configuration_payload(
    base_config: BaseConfiguration,
    course_id: str,
    train_task_id: str,
    train_task_cover: Dict[str, str],
) -> Dict:
    return {
        "trainTaskName": base_config.train_task_name,
        "description": base_config.description,
        "trainType": "voice",
        "trainTaskCover": train_task_cover,
        "trainTime": -1,
        "courseId": course_id,
        "trainTaskId": train_task_id,
    }


def create_configuration(
    base_config: BaseConfiguration,
    course_id: str,
    train_task_cover: Dict[str, str],
    *,
    post: Callable = requests.post,
    id_factory: Callable[[], str] | None = None,
) -> str:
    if id_factory is None:
        id_factory = lambda: generate(size=21)

    train_task_id = id_factory()
    payload = build_create_configuration_payload(
        base_config=base_config,
        course_id=course_id,
        train_task_id=train_task_id,
        train_task_cover=train_task_cover,
    )

    response = post(API_URL, headers=get_headers(), json=payload, timeout=20)
    result = response.json()
    if result.get("code") == 200 or result.get("success") is True:
        return result.get("data", {}).get("trainTaskId") or train_task_id
    raise RuntimeError(f"创建基础配置失败：{result}")


def create_from_markdown(markdown_path: Path, *, with_steps: bool = False) -> Dict[str, str]:
    markdown_path = Path(markdown_path).expanduser().resolve()
    if not markdown_path.exists():
        raise FileNotFoundError(f"Markdown 文件不存在：{markdown_path}")

    steps = parse_markdown(markdown_path)
    base_config = parse_base_configuration(markdown_path)
    cover_path = resolve_cover_image(markdown_path, base_config, steps)
    course_id = require_course_id()

    print(f"🖼️ 上传任务背景图：{cover_path.name}")
    train_task_cover = upload_cover_image(cover_path)
    if not train_task_cover:
        raise RuntimeError(f"背景图上传失败：{cover_path}")

    print(f"🚀 创建基础配置：{base_config.train_task_name}")
    train_task_id = create_configuration(base_config, course_id, train_task_cover)
    print(f"✅ 基础配置创建成功，trainTaskId={train_task_id}")
    env_path = write_root_task_id(train_task_id)
    print(f"📝 已写入根目录 .env: {env_path}")

    if with_steps:
        print("🧩 准备导入阶段节点和连线...")
        step_list = query_script_steps(train_task_id)
        flow_list = query_script_step_flows(train_task_id)
        existing_steps = [
            item for item in step_list
            if item.get("stepDetailDTO", {}).get("nodeType") not in ("SCRIPT_START", "SCRIPT_END")
        ]
        if existing_steps or flow_list:
            if not delete_existing_steps_and_flows(train_task_id, existing_steps, flow_list):
                raise RuntimeError("清理新任务默认节点/连线失败。")
            step_list = query_script_steps(train_task_id)

        start_node_id, end_node_id = extract_start_end_ids(step_list)
        if not start_node_id or not end_node_id:
            raise RuntimeError("新任务中未找到 SCRIPT_START 或 SCRIPT_END 节点。")

        build_steps_from_markdown(
            markdown_path,
            train_task_id,
            start_node_id=start_node_id,
            end_node_id=end_node_id,
            flow_list=[],
            steps=steps,
        )

    return {
        "trainTaskId": train_task_id,
        "trainTaskName": base_config.train_task_name,
    }


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="根据 Markdown 创建能力训练基础配置")
    parser.add_argument("markdown_path", help="训练剧本 Markdown 文件路径")
    parser.add_argument(
        "--with-steps",
        action="store_true",
        help="基础配置创建成功后，继续自动创建阶段节点和连线",
    )
    return parser


def main() -> int:
    load_env_config()
    args = build_arg_parser().parse_args()
    try:
        create_from_markdown(Path(args.markdown_path), with_steps=args.with_steps)
        return 0
    except Exception as exc:
        print(f"❌ {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
