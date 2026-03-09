#!/usr/bin/env python3
"""四川大学-IC设计基础-五道官运仿真学习 专用导入脚本。

功能：
1. 解析 stages 目录下所有阶段 Markdown。
2. 解析阶段跳转关系图（Mermaid）并与提示词中的 NEXT_TO/TASK_COMPLETE 双源校验。
3. 保留系统 START/END，删除其余节点与连线后全量重建。
4. 所有节点统一 interactiveRounds=10，统一复用同一张背景图。
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Set, Tuple

import requests
from dotenv import load_dotenv
from nanoid import generate


# -----------------------------
# 固定路径与常量（本课程专用）
# -----------------------------

ROOT_DIR = Path(__file__).resolve().parent.parent
COURSE_DIR = ROOT_DIR / "skills_training_course/四川大学-IC设计基础/五道官运仿真学习"
STAGES_DIR = COURSE_DIR / "stages"
RELATION_GRAPH_PATH = COURSE_DIR / "阶段跳转关系图.md"
UNIFIED_BACKGROUND_IMAGE = (
    COURSE_DIR
    / "backgrounds/训练剧本配置_背景图_stage_1_开场与任务说明.png"
)
UNIFIED_INTERACTIVE_ROUNDS = 10
START_FLOW_IS_DEFAULT = 0

API_BASE = "https://cloudapi.polymas.com/teacher-course/abilityTrain"
UPLOAD_API = "https://cloudapi.polymas.com/basic-resource/file/upload"

FLOW_COMMAND_PATTERN = re.compile(r"\b(NEXT_TO_[A-Z0-9_]+|TASK_COMPLETE)\b")
STAGE_FILE_PATTERN = re.compile(r"^stage(\d+)_([A-Za-z0-9_]+)\.md$")
MERMAID_STAGE_CODE_PATTERN = re.compile(
    r"阶段\s*\d+\s*<br\s*/?>\s*([A-Z0-9_]+)",
    flags=re.IGNORECASE,
)

STAGE_POSITIONS: Dict[str, Tuple[int, int]] = {
    "START": (900, 180),
    "DESIGN_REQUIREMENTS": (300, 380),
    "LAYOUT_REQUIREMENTS": (900, 380),
    "EDA_REQUIREMENTS": (1500, 380),
    "GAIN": (0, 660),
    "BANDWIDTH": (200, 660),
    "PHASE": (400, 660),
    "CMRR": (600, 660),
    "PSRR": (800, 660),
    "RANGE": (1000, 660),
    "POWER": (1200, 660),
    "EDA_QA": (1500, 660),
    "SIM_FLOW": (1700, 660),
    "LAYOUT_BASIC": (500, 940),
    "LAYOUT_18": (700, 940),
    "LAYOUT_SKILL": (900, 940),
    "LAYOUT_OPAMP": (1100, 940),
    "LAYOUT_CADENCE": (1300, 940),
}


# -----------------------------
# 数据结构
# -----------------------------

@dataclass(frozen=True)
class StageSpec:
    stage_no: int
    code: str
    step_name: str
    description: str
    prologue: str
    llm_prompt: str
    transition_prompt: str
    flow_condition: str
    trainer_name: str
    model_id: str
    agent_id: str
    avatar_nid: str
    source_rounds: Optional[int]
    jump_commands: List[str]
    source_path: Path


@dataclass(frozen=True)
class FlowSpec:
    source_code: str
    condition: str
    target_code: str  # TASK_COMPLETE 表示连到系统结束节点


@dataclass(frozen=True)
class Defaults:
    model_id: str
    agent_id: str
    trainer_name: str
    avatar_nid: str


# -----------------------------
# 通用工具
# -----------------------------

def load_env_config() -> None:
    """加载 .env（优先项目根目录）。"""
    env_paths = [
        ROOT_DIR / ".env",
        Path(__file__).resolve().parent / ".env",
        Path.cwd() / ".env",
    ]
    for env_path in env_paths:
        if env_path.exists():
            load_dotenv(env_path)
            print(f"✅ 已加载环境配置: {env_path}")
            return
    print("⚠️ 未找到 .env，将仅使用系统环境变量。")


def normalize_md_value(raw_value: str) -> str:
    value = raw_value.strip()
    if not value:
        return ""
    value = re.sub(r"（[^）]*选填[^）]*）", "", value)
    value = re.sub(r"\([^)]*选填[^)]*\)", "", value)
    value = re.sub(r"（[^）]*默认为空[^）]*）", "", value)
    value = re.sub(r"\([^)]*默认为空[^)]*\)", "", value)
    value = value.strip().strip('"').strip("'").strip()
    if value.startswith("“") and value.endswith("”"):
        value = value[1:-1].strip()
    return value


def extract_markdown_field(content: str, label: str) -> str:
    """提取类似 **字段名**：值 或代码块值。"""
    inline_pattern = re.compile(
        rf"\*\*{re.escape(label)}\*\*\s*[：:]\s*([^\n]+)"
    )
    inline_match = inline_pattern.search(content)
    if inline_match:
        return normalize_md_value(inline_match.group(1))

    block_pattern = re.compile(
        rf"\*\*{re.escape(label)}\*\*\s*[：:]\s*\n\s*```(?:[a-zA-Z0-9_-]+)?\n([\s\S]*?)```"
    )
    block_match = block_pattern.search(content)
    if block_match:
        return block_match.group(1).strip()

    return ""


def extract_section_body(content: str, section_title: str) -> str:
    pattern = re.compile(
        rf"^###\s*{re.escape(section_title)}\s*$\n?([\s\S]*?)(?=^###\s*|\Z)",
        flags=re.MULTILINE,
    )
    match = pattern.search(content)
    if not match:
        return ""
    body = match.group(1).strip()
    code_block_match = re.search(
        r"```(?:[a-zA-Z0-9_-]+)?\n([\s\S]*?)```", body
    )
    if code_block_match:
        return code_block_match.group(1).strip()
    return body.strip()


def extract_stage_heading(content: str) -> Tuple[int, str]:
    heading_match = re.search(r"^##\s*阶段\s*(\d+)\s*[：:]\s*(.+)$", content, flags=re.MULTILINE)
    if not heading_match:
        raise ValueError("缺少阶段标题（应为 '## 阶段N：标题'）。")
    stage_no = int(heading_match.group(1))
    step_name = heading_match.group(2).strip()
    return stage_no, step_name


def extract_jump_commands(prompt_text: str) -> List[str]:
    seen: Set[str] = set()
    commands: List[str] = []
    for match in FLOW_COMMAND_PATTERN.finditer(prompt_text):
        cmd = match.group(1).strip()
        if cmd not in seen:
            seen.add(cmd)
            commands.append(cmd)
    return commands


def command_to_target_code(command: str) -> str:
    if command == "TASK_COMPLETE":
        return "TASK_COMPLETE"
    if command.startswith("NEXT_TO_"):
        return command[len("NEXT_TO_") :]
    raise ValueError(f"不支持的跳转指令: {command}")


def parse_stage_markdown_file(file_path: Path) -> StageSpec:
    file_name_match = STAGE_FILE_PATTERN.match(file_path.name)
    if not file_name_match:
        raise ValueError(f"阶段文件名不符合约定: {file_path.name}")

    stage_no_by_file = int(file_name_match.group(1))
    code = file_name_match.group(2).upper()
    content = file_path.read_text(encoding="utf-8")

    stage_no_by_heading, step_name = extract_stage_heading(content)
    if stage_no_by_file != stage_no_by_heading:
        raise ValueError(
            f"{file_path.name} 阶段编号不一致: 文件名={stage_no_by_file}, 标题={stage_no_by_heading}"
        )

    description = extract_markdown_field(content, "阶段描述")
    trainer_name = extract_markdown_field(content, "虚拟训练官名字")
    model_id = extract_markdown_field(content, "模型")
    agent_id = extract_markdown_field(content, "声音")
    avatar_nid = extract_markdown_field(content, "形象")
    flow_condition = extract_markdown_field(content, "flowCondition")
    transition_prompt = extract_markdown_field(content, "transitionPrompt")

    rounds_text = extract_markdown_field(content, "互动轮次")
    rounds_match = re.search(r"\d+", rounds_text)
    source_rounds = int(rounds_match.group()) if rounds_match else None

    prologue = extract_section_body(content, "开场白")
    llm_prompt = extract_section_body(content, "提示词")
    if not llm_prompt:
        raise ValueError(f"{file_path.name} 缺少 '### 提示词' 内容。")

    jump_commands = extract_jump_commands(llm_prompt)
    if not jump_commands:
        raise ValueError(f"{file_path.name} 未在提示词中发现 NEXT_TO_* 或 TASK_COMPLETE 指令。")

    return StageSpec(
        stage_no=stage_no_by_file,
        code=code,
        step_name=step_name,
        description=description,
        prologue=prologue,
        llm_prompt=llm_prompt,
        transition_prompt=transition_prompt,
        flow_condition=flow_condition,
        trainer_name=trainer_name,
        model_id=model_id,
        agent_id=agent_id,
        avatar_nid=avatar_nid,
        source_rounds=source_rounds,
        jump_commands=jump_commands,
        source_path=file_path,
    )


def parse_stages_directory(stages_dir: Path) -> List[StageSpec]:
    if not stages_dir.exists():
        raise FileNotFoundError(f"阶段目录不存在: {stages_dir}")

    stage_files: List[Path] = []
    for file_path in stages_dir.glob("stage*.md"):
        if STAGE_FILE_PATTERN.match(file_path.name):
            stage_files.append(file_path)

    if not stage_files:
        raise ValueError(f"未找到阶段文件: {stages_dir}")

    parsed: List[StageSpec] = [parse_stage_markdown_file(path) for path in stage_files]
    parsed.sort(key=lambda item: item.stage_no)

    seen_codes: Set[str] = set()
    for stage in parsed:
        if stage.code in seen_codes:
            raise ValueError(f"阶段 code 重复: {stage.code}")
        seen_codes.add(stage.code)

    return parsed


def parse_mermaid_node_definition(line: str) -> Optional[Tuple[str, str]]:
    node_patterns = [
        re.compile(r"^([A-Za-z0-9_]+)\s*\(\[(.+?)\]\)\s*$"),
        re.compile(r"^([A-Za-z0-9_]+)\s*\[(.+?)\]\s*$"),
        re.compile(r"^([A-Za-z0-9_]+)\s*\((.+?)\)\s*$"),
    ]
    for pattern in node_patterns:
        match = pattern.match(line)
        if not match:
            continue
        mermaid_node_id = match.group(1)
        label = match.group(2)
        if "TASK_COMPLETE" in label:
            return mermaid_node_id, "TASK_COMPLETE"
        stage_code_match = MERMAID_STAGE_CODE_PATTERN.search(label)
        if stage_code_match:
            return mermaid_node_id, stage_code_match.group(1).upper()
    return None


def parse_mermaid_relationships(graph_markdown_path: Path) -> Tuple[Dict[str, str], Set[Tuple[str, str]]]:
    if not graph_markdown_path.exists():
        raise FileNotFoundError(f"跳转关系图不存在: {graph_markdown_path}")

    content = graph_markdown_path.read_text(encoding="utf-8")
    block_match = re.search(r"```mermaid\s*([\s\S]*?)```", content, flags=re.IGNORECASE)
    if not block_match:
        raise ValueError(f"{graph_markdown_path.name} 中未找到 mermaid 代码块。")

    mermaid_block = block_match.group(1)
    node_id_to_code: Dict[str, str] = {}
    raw_edges: List[Tuple[str, str]] = []

    for raw_line in mermaid_block.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("%%") or line.startswith("graph "):
            continue
        if line.startswith("classDef") or line.startswith("class "):
            continue

        edge_match = re.match(
            r"^([A-Za-z0-9_]+)\s*(?:-->|-\.->)(?:\|[^|]*\|)?\s*([A-Za-z0-9_]+)\s*$",
            line,
        )
        if edge_match:
            raw_edges.append((edge_match.group(1), edge_match.group(2)))
            continue

        node_result = parse_mermaid_node_definition(line)
        if node_result:
            node_id, code = node_result
            node_id_to_code[node_id] = code

    edges: Set[Tuple[str, str]] = set()
    unresolved_edges: List[Tuple[str, str]] = []
    for source_id, target_id in raw_edges:
        source_code = node_id_to_code.get(source_id)
        target_code = node_id_to_code.get(target_id)
        if not source_code or not target_code:
            unresolved_edges.append((source_id, target_id))
            continue
        edges.add((source_code, target_code))

    if unresolved_edges:
        unresolved_text = ", ".join([f"{src}->{dst}" for src, dst in unresolved_edges])
        raise ValueError(f"关系图存在无法解析的连线: {unresolved_text}")

    return node_id_to_code, edges


def build_prompt_edges(stages: Sequence[StageSpec]) -> Set[Tuple[str, str]]:
    stage_codes = {stage.code for stage in stages}
    edges: Set[Tuple[str, str]] = set()
    for stage in stages:
        for command in stage.jump_commands:
            target_code = command_to_target_code(command)
            if target_code != "TASK_COMPLETE" and target_code not in stage_codes:
                raise ValueError(
                    f"{stage.source_path.name} 中命令 {command} 指向未知目标: {target_code}"
                )
            edges.add((stage.code, target_code))
    return edges


def validate_jump_edges(
    prompt_edges: Set[Tuple[str, str]],
    graph_edges: Set[Tuple[str, str]],
) -> None:
    missing_in_prompt = graph_edges - prompt_edges
    extra_in_prompt = prompt_edges - graph_edges
    if not missing_in_prompt and not extra_in_prompt:
        return

    details: List[str] = []
    if missing_in_prompt:
        details.append("关系图中存在但提示词缺失的连线:")
        details.extend([f"  - {src} -> {dst}" for src, dst in sorted(missing_in_prompt)])
    if extra_in_prompt:
        details.append("提示词中存在但关系图缺失的连线:")
        details.extend([f"  - {src} -> {dst}" for src, dst in sorted(extra_in_prompt)])
    raise ValueError("\n".join(details))


def build_flow_specs(stages: Sequence[StageSpec]) -> List[FlowSpec]:
    flow_specs: List[FlowSpec] = []
    for stage in sorted(stages, key=lambda item: item.stage_no):
        seen: Set[Tuple[str, str, str]] = set()
        for command in stage.jump_commands:
            target_code = command_to_target_code(command)
            key = (stage.code, command, target_code)
            if key in seen:
                continue
            seen.add(key)
            flow_specs.append(
                FlowSpec(
                    source_code=stage.code,
                    condition=command,
                    target_code=target_code,
                )
            )
    return flow_specs


def assign_default_flags(flow_specs: Sequence[FlowSpec]) -> List[Tuple[FlowSpec, int]]:
    """同一 source_code 的第一条出边为默认分支，其余非默认。"""
    seen_source_codes: Set[str] = set()
    assigned: List[Tuple[FlowSpec, int]] = []
    for flow_spec in flow_specs:
        if flow_spec.source_code in seen_source_codes:
            is_default = 0
        else:
            seen_source_codes.add(flow_spec.source_code)
            is_default = 1
        assigned.append((flow_spec, is_default))
    return assigned


def resolve_position(stage: StageSpec, fallback_index: int) -> Dict[str, int]:
    if stage.code in STAGE_POSITIONS:
        x, y = STAGE_POSITIONS[stage.code]
    else:
        x = 200 + fallback_index * 220
        y = 1200
    return {"x": x, "y": y}


def resolve_defaults(args: argparse.Namespace) -> Defaults:
    return Defaults(
        model_id=args.default_model or os.getenv("DEFAULT_MODEL_ID") or "Doubao-Seed-1.6",
        agent_id=args.default_agent or os.getenv("DEFAULT_AGENT_ID") or "Tg3LpKo28D",
        trainer_name=args.default_trainer or os.getenv("DEFAULT_TRAINER_NAME") or "周老师",
        avatar_nid=args.default_avatar or os.getenv("DEFAULT_AVATAR_NID") or "",
    )


# -----------------------------
# API 访问
# -----------------------------

def get_headers() -> Dict[str, str]:
    auth = os.getenv("AUTHORIZATION")
    cookie = os.getenv("COOKIE")
    if not auth or not cookie:
        raise ValueError("缺少 AUTHORIZATION 或 COOKIE。")
    return {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": auth,
        "Cookie": cookie,
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/142.0.0.0 Safari/537.36"
        ),
    }


def get_upload_headers() -> Dict[str, str]:
    auth = os.getenv("AUTHORIZATION")
    cookie = os.getenv("COOKIE")
    if not auth or not cookie:
        raise ValueError("缺少 AUTHORIZATION 或 COOKIE。")
    return {
        "Authorization": auth,
        "Cookie": cookie,
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/142.0.0.0 Safari/537.36"
        ),
    }


def upload_cover_image(file_path: Path) -> Optional[Dict[str, str]]:
    if not file_path.exists():
        raise FileNotFoundError(f"统一背景图不存在: {file_path}")

    identify_code = str(uuid.uuid4())
    file_name = file_path.name
    file_size = file_path.stat().st_size
    file_ext = file_path.suffix.lower()
    mime_types = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
    }
    mime_type = mime_types.get(file_ext, "application/octet-stream")

    with file_path.open("rb") as file_obj:
        files = {"file": (file_name, file_obj, mime_type)}
        data = {
            "identifyCode": identify_code,
            "name": file_name,
            "chunk": "0",
            "chunks": "1",
            "size": str(file_size),
        }
        response = requests.post(
            UPLOAD_API,
            headers=get_upload_headers(),
            data=data,
            files=files,
            timeout=25,
        )
        result = response.json()

    if not result.get("success"):
        raise RuntimeError(f"背景图上传失败: {result}")

    data = result.get("data", {})
    file_id = data.get("fileId")
    file_url = data.get("ossUrl") or data.get("fileUrl")
    if not file_id or not file_url:
        raise RuntimeError(f"背景图上传返回缺少 fileId/fileUrl: {result}")
    return {"fileId": file_id, "fileUrl": file_url}


def get_or_upload_cover(
    file_path: Path,
    cache: Dict[Path, Dict[str, str]],
    uploader: Callable[[Path], Optional[Dict[str, str]]],
) -> Dict[str, str]:
    if file_path in cache:
        return cache[file_path]
    uploaded = uploader(file_path)
    if not uploaded:
        raise RuntimeError(f"背景图上传失败: {file_path}")
    cache[file_path] = uploaded
    return uploaded


def query_script_steps(train_task_id: str) -> List[Dict]:
    url = f"{API_BASE}/queryScriptStepList"
    payload = {"trainTaskId": train_task_id, "trainSubType": "ability"}
    response = requests.post(url, headers=get_headers(), json=payload, timeout=20)
    result = response.json()
    if result.get("code") == 200 or result.get("success") is True:
        return result.get("data", [])
    raise RuntimeError(f"查询节点失败: {result}")


def query_script_step_flows(train_task_id: str) -> List[Dict]:
    url = f"{API_BASE}/queryScriptStepFlowList"
    payload = {"trainTaskId": train_task_id}
    response = requests.post(url, headers=get_headers(), json=payload, timeout=20)
    result = response.json()
    if result.get("code") == 200 or result.get("success") is True:
        return result.get("data", [])
    raise RuntimeError(f"查询连线失败: {result}")


def delete_script_step_flow(train_task_id: str, flow_id: str) -> None:
    url = f"{API_BASE}/delScriptStepFlow"
    payload = {"trainTaskId": train_task_id, "flowId": flow_id}
    response = requests.post(url, headers=get_headers(), json=payload, timeout=20)
    result = response.json()
    if result.get("code") == 200 or result.get("success") is True:
        return
    raise RuntimeError(f"删除连线失败 {flow_id}: {result}")


def delete_script_step(train_task_id: str, step_id: str) -> None:
    url = f"{API_BASE}/delScriptStep"
    payload = {"trainTaskId": train_task_id, "stepId": step_id}
    response = requests.post(url, headers=get_headers(), json=payload, timeout=20)
    result = response.json()
    if result.get("code") == 200 or result.get("success") is True:
        return
    raise RuntimeError(f"删除节点失败 {step_id}: {result}")


def extract_start_end_ids(step_list: Sequence[Dict]) -> Tuple[Optional[str], Optional[str]]:
    start_node_id = None
    end_node_id = None
    for item in step_list:
        node_type = item.get("stepDetailDTO", {}).get("nodeType")
        if node_type == "SCRIPT_START":
            start_node_id = item.get("stepId")
        elif node_type == "SCRIPT_END":
            end_node_id = item.get("stepId")
    return start_node_id, end_node_id


def build_step_payload(
    train_task_id: str,
    step_id: str,
    stage: StageSpec,
    position: Dict[str, int],
    defaults: Defaults,
    script_step_cover: Dict[str, str],
) -> Dict:
    trainer_name = stage.trainer_name or defaults.trainer_name
    model_id = stage.model_id or defaults.model_id
    agent_id = stage.agent_id or defaults.agent_id
    avatar_nid = stage.avatar_nid or defaults.avatar_nid

    return {
        "trainTaskId": train_task_id,
        "stepId": step_id,
        "stepDetailDTO": {
            "nodeType": "SCRIPT_NODE",
            "stepName": stage.step_name,
            "description": stage.description,
            "prologue": stage.prologue,
            "modelId": model_id,
            "llmPrompt": stage.llm_prompt,
            "trainerName": trainer_name,
            "interactiveRounds": UNIFIED_INTERACTIVE_ROUNDS,
            "scriptStepCover": script_step_cover,
            "whiteBoardSwitch": 0,
            "agentId": agent_id,
            "avatarNid": avatar_nid,
            "videoSwitch": 0,
            "scriptStepResourceList": [],
            "knowledgeBaseSwitch": 1,
            "searchEngineSwitch": 1,
            "historyRecordNum": -1,
            "trainSubType": "ability",
        },
        "positionDTO": position,
    }


def create_script_step(
    train_task_id: str,
    stage: StageSpec,
    position: Dict[str, int],
    defaults: Defaults,
    script_step_cover: Dict[str, str],
) -> str:
    url = f"{API_BASE}/createScriptStep"
    new_step_id = generate(size=21)
    payload = build_step_payload(
        train_task_id=train_task_id,
        step_id=new_step_id,
        stage=stage,
        position=position,
        defaults=defaults,
        script_step_cover=script_step_cover,
    )

    response = requests.post(url, headers=get_headers(), json=payload, timeout=20)
    result = response.json()
    if result.get("code") == 200 or result.get("success") is True:
        return new_step_id
    raise RuntimeError(f"创建节点失败 {stage.step_name}: {result}")


def create_script_flow(
    train_task_id: str,
    start_id: str,
    end_id: str,
    condition_text: str,
    transition_prompt: str,
    is_default: int,
) -> str:
    if is_default not in (0, 1):
        raise ValueError(f"is_default 必须为 0 或 1，收到: {is_default}")
    url = f"{API_BASE}/createScriptStepFlow"
    flow_id = generate(size=21)
    payload = build_flow_payload(
        train_task_id=train_task_id,
        flow_id=flow_id,
        start_id=start_id,
        end_id=end_id,
        condition_text=condition_text,
        transition_prompt=transition_prompt,
        is_default=is_default,
    )

    response = requests.post(url, headers=get_headers(), json=payload, timeout=20)
    result = response.json()
    if result.get("code") == 200 or result.get("success") is True:
        return flow_id
    raise RuntimeError(
        f"创建连线失败 {start_id} -> {end_id} / {condition_text}: {result}"
    )


def build_flow_payload(
    train_task_id: str,
    flow_id: str,
    start_id: str,
    end_id: str,
    condition_text: str,
    transition_prompt: str,
    is_default: int,
) -> Dict:
    if is_default not in (0, 1):
        raise ValueError(f"is_default 必须为 0 或 1，收到: {is_default}")
    return {
        "trainTaskId": train_task_id,
        "flowId": flow_id,
        "scriptStepStartId": start_id,
        "scriptStepStartHandle": f"{start_id}-source-bottom",
        "scriptStepEndId": end_id,
        "scriptStepEndHandle": f"{end_id}-target-top",
        "flowSettingType": "quick",
        "flowCondition": condition_text,
        "flowConfiguration": {
            "relation": "and",
            "conditions": [
                {
                    "text": "条件组1",
                    "relation": "and",
                    "conditions": [{"text": condition_text}],
                }
            ],
        },
        "transitionPrompt": transition_prompt,
        "transitionHistoryNum": 0,
        "isDefault": is_default,
        "isError": False,
    }


# -----------------------------
# 主流程
# -----------------------------

def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="四川大学五道官运 stages 非线性导入脚本（统一轮次+统一背景图）"
    )
    parser.add_argument("--task-id", help="目标训练任务 ID，默认读取 .env 中 TASK_ID")
    parser.add_argument("--dry-run", action="store_true", help="仅解析与校验，不写入平台")
    parser.add_argument("--yes", action="store_true", help="删除确认自动通过")
    parser.add_argument("--default-model", help="默认模型ID（覆盖环境变量）")
    parser.add_argument("--default-agent", help="默认语音ID（覆盖环境变量）")
    parser.add_argument("--default-trainer", help="默认训练官名称（覆盖环境变量）")
    parser.add_argument("--default-avatar", help="默认头像nid（覆盖环境变量）")
    return parser


def print_parse_summary(
    stages: Sequence[StageSpec],
    prompt_edges: Set[Tuple[str, str]],
    graph_edges: Set[Tuple[str, str]],
) -> None:
    print("\n📊 解析与校验摘要")
    print(f"   - 阶段文件数: {len(stages)}")
    print(f"   - 提示词边数: {len(prompt_edges)}")
    print(f"   - 关系图边数: {len(graph_edges)}")
    print(f"   - 统一互动轮次: {UNIFIED_INTERACTIVE_ROUNDS}")
    print(f"   - 统一背景图: {UNIFIED_BACKGROUND_IMAGE}")


def confirm_rebuild(non_system_steps: Sequence[Dict], flow_list: Sequence[Dict], auto_yes: bool) -> bool:
    print("\n🧹 即将执行全量重建")
    print(f"   - 将删除连线: {len(flow_list)}")
    print(f"   - 将删除业务节点: {len(non_system_steps)}")
    if auto_yes:
        return True

    answer = input("是否继续？此操作不可撤销 (y/N): ").strip().lower()
    return answer in {"y", "yes"}


def main() -> int:
    load_env_config()
    parser = build_arg_parser()
    args = parser.parse_args()

    stages = parse_stages_directory(STAGES_DIR)
    _, graph_edges = parse_mermaid_relationships(RELATION_GRAPH_PATH)
    prompt_edges = build_prompt_edges(stages)
    validate_jump_edges(prompt_edges, graph_edges)
    print("✅ 跳转双源校验通过（提示词指令 == 关系图拓扑）")
    print_parse_summary(stages, prompt_edges, graph_edges)

    if not UNIFIED_BACKGROUND_IMAGE.exists():
        raise FileNotFoundError(f"统一背景图不存在: {UNIFIED_BACKGROUND_IMAGE}")

    if args.dry_run:
        print("\n🧪 dry-run 模式：未调用平台写接口。")
        return 0

    train_task_id = args.task_id or os.getenv("TASK_ID")
    if not train_task_id:
        raise ValueError("缺少 task-id，请通过 --task-id 或 .env TASK_ID 提供。")
    print(f"\n🎯 目标任务: {train_task_id}")

    defaults = resolve_defaults(args)
    print(
        "🧩 默认配置: "
        f"model={defaults.model_id}, agent={defaults.agent_id}, "
        f"trainer={defaults.trainer_name}, avatar={defaults.avatar_nid or '(空)'}"
    )

    step_list = query_script_steps(train_task_id)
    flow_list = query_script_step_flows(train_task_id)
    start_node_id, end_node_id = extract_start_end_ids(step_list)
    if not start_node_id or not end_node_id:
        raise RuntimeError("未找到系统 START/END 节点，无法继续。")

    non_system_steps = [
        item
        for item in step_list
        if item.get("stepDetailDTO", {}).get("nodeType") not in {"SCRIPT_START", "SCRIPT_END"}
    ]
    if not confirm_rebuild(non_system_steps, flow_list, args.yes):
        print("⏹️ 用户取消执行。")
        return 0

    for flow in flow_list:
        flow_id = flow.get("flowId")
        if flow_id:
            delete_script_step_flow(train_task_id, flow_id)
    print(f"✅ 已删除连线: {len(flow_list)}")

    for step in non_system_steps:
        step_id = step.get("stepId")
        if step_id:
            delete_script_step(train_task_id, step_id)
    print(f"✅ 已删除业务节点: {len(non_system_steps)}")

    cover_cache: Dict[Path, Dict[str, str]] = {}
    unified_cover = get_or_upload_cover(UNIFIED_BACKGROUND_IMAGE, cover_cache, upload_cover_image)
    print("✅ 统一背景图上传成功（后续节点复用该 fileId/fileUrl）")

    stage_code_to_step_id: Dict[str, str] = {}
    sorted_stages = sorted(stages, key=lambda item: item.stage_no)
    for idx, stage in enumerate(sorted_stages):
        position = resolve_position(stage, idx)
        new_step_id = create_script_step(
            train_task_id=train_task_id,
            stage=stage,
            position=position,
            defaults=defaults,
            script_step_cover=unified_cover,
        )
        stage_code_to_step_id[stage.code] = new_step_id
        print(f"✅ 创建节点: 阶段{stage.stage_no} {stage.step_name} ({stage.code}) -> {new_step_id}")

    stage1_id = stage_code_to_step_id.get("START")
    if not stage1_id:
        raise RuntimeError("未找到 code=START 的阶段节点，无法连系统开始节点。")
    create_script_flow(
        train_task_id=train_task_id,
        start_id=start_node_id,
        end_id=stage1_id,
        condition_text="",
        transition_prompt="",
        is_default=START_FLOW_IS_DEFAULT,
    )
    print("✅ 创建连线: 系统START -> 阶段1(START)")

    stage_by_code = {stage.code: stage for stage in sorted_stages}
    flow_specs = build_flow_specs(sorted_stages)

    created_flow_count = 1  # START -> stage1
    for flow_spec, is_default in assign_default_flags(flow_specs):
        source_id = stage_code_to_step_id[flow_spec.source_code]
        if flow_spec.target_code == "TASK_COMPLETE":
            target_id = end_node_id
        else:
            if flow_spec.target_code not in stage_code_to_step_id:
                raise RuntimeError(
                    f"连线目标阶段不存在: {flow_spec.source_code} --{flow_spec.condition}--> {flow_spec.target_code}"
                )
            target_id = stage_code_to_step_id[flow_spec.target_code]

        source_stage = stage_by_code[flow_spec.source_code]
        create_script_flow(
            train_task_id=train_task_id,
            start_id=source_id,
            end_id=target_id,
            condition_text=flow_spec.condition,
            transition_prompt=source_stage.transition_prompt,
            is_default=is_default,
        )
        created_flow_count += 1
        print(
            "✅ 创建连线: "
            f"{flow_spec.source_code} --{flow_spec.condition}--> {flow_spec.target_code}"
        )

    print("\n🎉 导入完成")
    print(f"   - 创建业务节点: {len(stage_code_to_step_id)}")
    print(f"   - 创建连线总数: {created_flow_count}")
    print("   - 统一互动轮次: 10（已强制）")
    print(f"   - 统一背景图复用: {UNIFIED_BACKGROUND_IMAGE.name}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"❌ 执行失败: {exc}", file=sys.stderr)
        raise SystemExit(1)
