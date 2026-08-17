import os
import json
import requests
import re
import argparse
import copy
from pathlib import Path
import uuid
from urllib.parse import urlparse
from dotenv import load_dotenv
from nanoid import generate

# --- Configuration & Helpers ---

DEFAULT_ABILITY_TRAIN_API_BASE = "https://cloudapi.polymas.com/teacher-course/abilityTrain"
DEFAULT_TRANSITION_HISTORY_NUM = 10

STEP_DETAIL_METADATA_FIELDS = (
    "scriptStepCover",
    "scriptStepResourceList",
    "knowledgeBaseSwitch",
    "knowledgeBaseId",
    "searchEngineSwitch",
    "whiteBoardSwitch",
    "videoSwitch",
    "historyRecordNum",
    "agentVoiceId",
    "digitalHumanType",
    "projectId",
    "stepExtProperty",
    "backgroundTheme",
    "transitionDescriptionUrl",
    "customDigitalHuman",
    "knowledgeResourceList",
    "trainTime",
    "isSkipStep",
    "endStrategy",
    "refResourceDesc",
    "isTransition",
)


def load_env_config():
    """Load .env configuration."""
    current_dir = Path(__file__).parent
    env_paths = [
        current_dir.parent / '.env',
        current_dir / '.env',
        Path.cwd() / '.env'
    ]
    for path in env_paths:
        if path.exists():
            load_dotenv(path)
            print(f"✅ Loaded environment config: {path}")
            return
    print("⚠️ No .env file found, using system environment variables.")


def get_ability_train_api_base():
    """Return the configured abilityTrain API base URL."""
    return os.getenv("ABILITY_TRAIN_API_BASE", DEFAULT_ABILITY_TRAIN_API_BASE).strip().rstrip("/")


def ability_train_url(endpoint):
    return f"{get_ability_train_api_base()}/{endpoint.lstrip('/')}"


def get_headers():
    auth = os.getenv("AUTHORIZATION")
    cookie = os.getenv("COOKIE")
    if not auth or not cookie:
        raise ValueError("Missing AUTHORIZATION or COOKIE in environment.")
    return {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": auth,
        "Cookie": cookie,
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"
    }

def get_upload_headers():
    auth = os.getenv("AUTHORIZATION")
    cookie = os.getenv("COOKIE")
    if not auth or not cookie:
        raise ValueError("Missing AUTHORIZATION or COOKIE in environment.")
    return {
        "Authorization": auth,
        "Cookie": cookie,
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"
    }

def require_course_id():
    course_id = os.getenv("COURSE_ID", "").strip()
    if not course_id:
        raise ValueError("缺少 COURSE_ID，请在 .env 或系统环境变量中配置。")
    return course_id

def normalize_md_value(raw_value):
    value = raw_value.strip()
    if not value:
        return ""
    value = re.sub(r'（[^）]*选填[^）]*）', '', value)
    value = re.sub(r'\([^)]*选填[^)]*\)', '', value)
    value = re.sub(r'（[^）]*默认为空[^）]*）', '', value)
    value = re.sub(r'\([^)]*默认为空[^)]*\)', '', value)
    value = value.strip()
    if not value:
        return ""
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        value = value[1:-1].strip()
    if value.startswith("“") and value.endswith("”"):
        value = value[1:-1].strip()
    return value

def extract_md_field_value(raw_line):
    """Return field content after the first ASCII or full-width colon."""
    ascii_pos = raw_line.find(':')
    full_width_pos = raw_line.find('：')
    positions = [pos for pos in (ascii_pos, full_width_pos) if pos >= 0]
    if not positions:
        return ""
    return raw_line[min(positions) + 1:].strip()

def normalize_rule_relation(raw_relation, default="and"):
    relation = (raw_relation or default).strip().lower()
    if relation not in ("and", "or"):
        raise ValueError(f"Unsupported conditionRule relation: {raw_relation}")
    return relation

def parse_condition_rule_header(stripped_line):
    """Parse a conditionRule heading and return route/outer metadata."""
    match = re.match(r'^\*\*Jump Conditions \(conditionRule\)(?P<meta>.*?)\*\*$', stripped_line)
    if not match:
        return None

    route_exit = ""
    outer_relation = "and"
    metadata = match.group("meta") or ""
    metadata = re.sub(r'\s+[—–]\s+', ' - ', metadata)
    for part in metadata.split(" - "):
        part = part.strip(" -")
        if not part or ":" not in part:
            continue
        key, value = part.split(":", 1)
        key = key.strip().lower()
        value = normalize_md_value(value)
        if key == "route exit":
            route_exit = value
        elif key == "outer":
            outer_relation = normalize_rule_relation(value)

    return {
        "routeExit": route_exit,
        "outerRelation": outer_relation,
        "groups": [],
    }

def parse_condition_group_header(stripped_line):
    match = re.match(r'^-\s*\*\*Group\s+(\d+)\s*\((AND|OR)\):\*\*$', stripped_line, re.IGNORECASE)
    if not match:
        return None
    return {
        "number": int(match.group(1)),
        "relation": normalize_rule_relation(match.group(2)),
        "conditions": [],
    }

def parse_condition_item(stripped_line):
    if not stripped_line.startswith("- "):
        return ""
    text = stripped_line[2:].strip()
    if not text:
        return ""
    return re.sub(r'\s+', ' ', text).strip()

def upload_cover_image(file_path):
    url = "https://cloudapi.polymas.com/basic-resource/file/upload"
    identify_code = str(uuid.uuid4())

    file_path = Path(file_path)
    if not file_path.exists():
        print(f"⚠️ Background image not found: {file_path}")
        return None

    file_name = file_path.name
    file_size = file_path.stat().st_size
    file_ext = file_path.suffix.lower()
    mime_types = {
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.gif': 'image/gif'
    }
    mime_type = mime_types.get(file_ext, 'application/octet-stream')

    with open(file_path, 'rb') as f:
        files = {
            'file': (file_name, f, mime_type)
        }
        data = {
            'identifyCode': identify_code,
            'name': file_name,
            'chunk': '0',
            'chunks': '1',
            'size': str(file_size)
        }
        try:
            response = requests.post(url, headers=get_upload_headers(), data=data, files=files, timeout=20)
            result = response.json()
        except Exception as e:
            print(f"❌ Error uploading background image {file_name}: {e}")
            return None

    if not result.get('success'):
        print(f"❌ Background image upload failed: {result}")
        return None

    data = result.get('data', {})
    file_id = data.get('fileId')
    file_url = data.get('ossUrl') or data.get('fileUrl')
    if not file_id or not file_url:
        print(f"⚠️ Background image upload missing fileId/fileUrl: {result}")
        return None

    print(f"✅ Background image uploaded: {file_name}")
    return {"fileId": file_id, "fileUrl": file_url}

def is_remote_url(value):
    if not value:
        return False
    parsed = urlparse(str(value))
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)

def build_script_step_cover_from_url(file_url, existing_cover=None):
    """Build scriptStepCover from an OSS URL, preserving known platform metadata."""
    cover = copy.deepcopy(existing_cover) if isinstance(existing_cover, dict) else {}
    cover["fileUrl"] = file_url
    return cover

# --- Parsing Logic (Reused/Refined) ---

def parse_markdown(markdown_path):
    """Parse Markdown file to extract step details."""
    with open(markdown_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    steps = []
    current_step = {}
    in_code_block = False
    current_code_block = []
    code_block_type = None 
    current_flow_rule = None
    current_flow_group = None
    
    for line in lines:
        stripped = line.strip()
        # Normalize only for field matching. Preserve original value punctuation.
        normalized = stripped.replace('：', ':')

        # New Step Start
        if normalized.startswith('### 阶段'):
            if current_step:
                steps.append(current_step)
            current_step = {}
            current_flow_rule = None
            current_flow_group = None
            if ':' in normalized:
                # "### Phase 1: Name" -> "Name"
                current_step['stepName'] = extract_md_field_value(stripped)
            continue

        if not in_code_block and (
            normalized.startswith('---') or (
                normalized.startswith('##') and not normalized.startswith('### 阶段')
            )
        ):
            current_flow_rule = None
            current_flow_group = None
            continue

        if not in_code_block:
            rule_header = parse_condition_rule_header(stripped)
            if rule_header is not None:
                current_step.setdefault('flowRules', []).append(rule_header)
                current_flow_rule = rule_header
                current_flow_group = None
                continue

            group_header = parse_condition_group_header(stripped)
            if group_header is not None and current_flow_rule is not None:
                current_flow_rule.setdefault('groups', []).append(group_header)
                current_flow_group = group_header
                continue

            condition_item = parse_condition_item(stripped)
            if condition_item and current_flow_group is not None:
                current_flow_group.setdefault('conditions', []).append(condition_item)
                continue

            if current_flow_rule is not None and normalized.startswith('**'):
                current_flow_rule = None
                current_flow_group = None
            
        # Fields
        if normalized.startswith('**Step ID**:'):
            # We ignore the Step ID from MD when creating NEW nodes, 
            # but we might verify if we are updating. 
            # For this script (CREATE), we usually generate NEW IDs.
            # But let's store it just in case.
            current_step['originalStepId'] = extract_md_field_value(stripped)
            continue
            
        if normalized.startswith('**虚拟训练官名字**:'):
            current_step['trainerName'] = normalize_md_value(extract_md_field_value(stripped))
            continue

        if normalized.startswith('**模型**:'):
            current_step['modelId'] = normalize_md_value(extract_md_field_value(stripped))
            continue

        if normalized.startswith('**声音**:'):
            current_step['agentId'] = normalize_md_value(extract_md_field_value(stripped))
            continue
            
        if normalized.startswith('**形象**:'):
            current_step['avatarNid'] = normalize_md_value(extract_md_field_value(stripped))
            continue
            
        if normalized.startswith('**阶段描述**:'):
            current_step['description'] = normalize_md_value(extract_md_field_value(stripped))
            continue

        if normalized.startswith('**背景图**:'):
            current_step['backgroundImage'] = normalize_md_value(extract_md_field_value(stripped))
            continue
            
        if normalized.startswith('**互动轮次**:'):
            rounds_str = extract_md_field_value(stripped)
            match = re.search(r'-?\d+', rounds_str)
            if match:
                current_step['interactiveRounds'] = int(match.group())
            continue
            
        # Code Blocks
        if normalized.startswith('**开场白**:'):
            code_block_type = 'prologue'
            continue
            
        if normalized.startswith('**提示词**:'):
            code_block_type = 'llmPrompt'
            continue

        if normalized.startswith('**transitionPrompt**:'):
            inline_value = normalize_md_value(extract_md_field_value(stripped))
            if inline_value:
                current_step['transitionPrompt'] = inline_value
                code_block_type = None
            else:
                code_block_type = 'transitionPrompt'
            continue

        if normalized.startswith('**flowCondition**:'):
            current_step['flowCondition'] = normalize_md_value(extract_md_field_value(stripped))
            continue
            
        if normalized.startswith('```'):
            if in_code_block:
                content = ''.join(current_code_block).strip() 
                if code_block_type == 'prologue':
                    current_step['prologue'] = content
                elif code_block_type == 'llmPrompt':
                    current_step['llmPrompt'] = content
                elif code_block_type == 'transitionPrompt':
                    current_step['transitionPrompt'] = content
                in_code_block = False
                current_code_block = []
                code_block_type = None
            else:
                in_code_block = True
                current_code_block = []
            continue
            
        if in_code_block:
            current_code_block.append(line)
            
    if current_step:
        steps.append(current_step)
        
    return steps

def load_step_metadata(metadata_json_path):
    """Load per-step platform metadata keyed by original Step ID."""
    if not metadata_json_path:
        return {}

    path = Path(metadata_json_path)
    if not path.exists():
        raise FileNotFoundError(f"Metadata JSON file not found: {path}")

    raw = json.loads(path.read_text(encoding='utf-8'))
    metadata_by_step_id = {}

    if isinstance(raw, dict) and isinstance(raw.get('steps'), list):
        for item in raw['steps']:
            step_id = item.get('originalStepId') or item.get('stepId')
            metadata = item.get('metadata') or {}
            if step_id and isinstance(metadata, dict):
                metadata_by_step_id[step_id] = metadata
        return metadata_by_step_id

    if isinstance(raw, dict):
        for step_id, metadata in raw.items():
            if isinstance(metadata, dict):
                metadata_by_step_id[step_id] = metadata
        return metadata_by_step_id

    raise ValueError("Metadata JSON 格式不支持，应为 steps 列表或 stepId 到 metadata 的映射。")

def apply_step_metadata(steps, metadata_by_step_id):
    """Merge whitelisted platform metadata into parsed Markdown steps."""
    if not metadata_by_step_id:
        return 0

    matched_count = 0
    for step in steps:
        original_step_id = step.get('originalStepId')
        metadata = metadata_by_step_id.get(original_step_id)
        if not metadata:
            continue
        for field in STEP_DETAIL_METADATA_FIELDS:
            if field in metadata:
                step[field] = copy.deepcopy(metadata[field])
        matched_count += 1
    return matched_count

def apply_step_detail_metadata(step_detail, step_data):
    """Apply metadata fields to a createScriptStep detail payload."""
    for field in STEP_DETAIL_METADATA_FIELDS:
        if field in step_data:
            step_detail[field] = copy.deepcopy(step_data[field])

def step_display_name(step):
    return step.get('stepName', '未命名阶段')

def has_condition_rules(steps):
    return any(step.get('flowRules') for step in steps)

def normalize_route_label(value):
    text = str(value or '').strip().lower()
    text = re.sub(r'\s+', ' ', text)
    return text

def resolve_route_exit_target_index(steps, source_idx, route_exit):
    """Resolve Route Exit labels to a unique target step index."""
    route_label = normalize_route_label(route_exit)
    if not route_label:
        raise ValueError(f"Route Exit is empty for step: {step_display_name(steps[source_idx])}")

    candidates = []
    for idx, step in enumerate(steps):
        if idx == source_idx:
            continue
        name = step_display_name(step)
        candidates.append((idx, name, normalize_route_label(name)))

    exact_matches = [(idx, name) for idx, name, normalized in candidates if normalized == route_label]
    if len(exact_matches) == 1:
        return exact_matches[0][0]
    if len(exact_matches) > 1:
        names = ', '.join(name for _, name in exact_matches)
        raise ValueError(f"Route Exit '{route_exit}' matched multiple exact targets: {names}")

    prefix_matches = [(idx, name) for idx, name, normalized in candidates if normalized.startswith(route_label)]
    if len(prefix_matches) == 1:
        return prefix_matches[0][0]
    if len(prefix_matches) > 1:
        names = ', '.join(name for _, name in prefix_matches)
        raise ValueError(f"Route Exit '{route_exit}' matched multiple prefix targets: {names}")

    contains_matches = [
        (idx, name)
        for idx, name, normalized in candidates
        if route_label in normalized or normalized in route_label
    ]
    if len(contains_matches) == 1:
        return contains_matches[0][0]
    if len(contains_matches) > 1:
        names = ', '.join(name for _, name in contains_matches)
        raise ValueError(f"Route Exit '{route_exit}' matched multiple contained targets: {names}")

    available = ', '.join(step_display_name(step) for idx, step in enumerate(steps) if idx != source_idx)
    raise ValueError(f"Route Exit '{route_exit}' did not match any target step. Available: {available}")

def build_condition_flow_configuration(flow_rule):
    groups = []
    for idx, group in enumerate(flow_rule.get('groups', []), start=1):
        conditions = [
            {"text": condition}
            for condition in group.get('conditions', [])
            if condition
        ]
        if not conditions:
            continue
        group_number = group.get('number') or idx
        groups.append({
            "text": f"条件组{group_number}",
            "relation": normalize_rule_relation(group.get('relation')),
            "conditions": conditions,
            "isEdit": False,
        })

    if not groups:
        raise ValueError("conditionRule must contain at least one non-empty condition group.")

    return {
        "relation": normalize_rule_relation(flow_rule.get('outerRelation')),
        "conditions": groups,
    }

def validate_is_default(is_default):
    if is_default not in (0, 1):
        raise ValueError(f"is_default must be 0 or 1, got: {is_default}")

def build_edit_script_step_flow_payload(
    train_task_id,
    flow_id,
    start_id,
    end_id,
    condition_text,
    flow_rule,
    transition_prompt="",
    is_default=1,
):
    validate_is_default(is_default)
    return {
        "trainTaskId": train_task_id,
        "flowId": flow_id,
        "scriptStepStartId": start_id,
        "scriptStepStartHandle": f"{start_id}-source-bottom",
        "scriptStepEndId": end_id,
        "scriptStepEndHandle": f"{end_id}-target-top",
        "flowSettingType": "configuration",
        "flowCondition": condition_text,
        "flowConfiguration": build_condition_flow_configuration(flow_rule),
        "transitionPrompt": transition_prompt,
        "transitionHistoryNum": DEFAULT_TRANSITION_HISTORY_NUM,
        "isDefault": is_default,
        "isError": False,
    }

def render_transition_prompt(raw_transition_prompt, target_step=None):
    transition_prompt = raw_transition_prompt or ""
    if "${next_stage_opening}" not in transition_prompt:
        return transition_prompt

    if not target_step:
        return ""

    next_stage_opening = target_step.get('prologue', '')
    if not next_stage_opening:
        return ""
    return transition_prompt.replace("${next_stage_opening}", next_stage_opening)

def make_flow_spec(source_idx, target_idx, source_name, target_name, condition, transition_prompt="", flow_rule=None):
    return {
        "sourceIndex": source_idx,
        "targetIndex": target_idx,
        "sourceName": source_name,
        "targetName": target_name,
        "flowCondition": condition,
        "transitionPrompt": transition_prompt,
        "flowRule": flow_rule,
        "flowSettingType": "configuration" if flow_rule else "quick",
    }

def flow_default_source_key(flow_spec):
    if flow_spec["sourceIndex"] is not None:
        return ("step", flow_spec["sourceIndex"])
    return ("special", flow_spec["sourceName"])

def assign_default_flags(flow_specs):
    """同一源节点的第一条出边为默认分支，其余非默认。"""
    seen_sources = set()
    assigned_specs = []
    for flow_spec in flow_specs:
        assigned_spec = dict(flow_spec)
        source_key = flow_default_source_key(flow_spec)
        if source_key in seen_sources:
            assigned_spec["isDefault"] = 0
        else:
            seen_sources.add(source_key)
            assigned_spec["isDefault"] = 1
        assigned_specs.append(assigned_spec)
    return assigned_specs

def should_flow_to_end_before_next_route_target(steps, source_idx, route_target_indexes):
    """End the current branch when the next Markdown stage starts another route branch."""
    return source_idx == len(steps) - 1 or (source_idx + 1) in route_target_indexes

def get_linear_create_flow_specs(steps):
    if not steps:
        return []

    specs = [make_flow_spec(None, 0, "START", step_display_name(steps[0]), "", "")]
    for idx in range(len(steps) - 1):
        source_step = steps[idx]
        target_step = steps[idx + 1]
        condition = source_step.get('flowCondition') or step_display_name(target_step)
        transition_prompt = render_transition_prompt(source_step.get('transitionPrompt', ''), target_step)
        specs.append(make_flow_spec(
            idx,
            idx + 1,
            step_display_name(source_step),
            step_display_name(target_step),
            condition,
            transition_prompt,
        ))

    last_idx = len(steps) - 1
    last_step = steps[last_idx]
    specs.append(make_flow_spec(
        last_idx,
        None,
        step_display_name(last_step),
        "END",
        last_step.get('flowCondition') or "训练结束",
        render_transition_prompt(last_step.get('transitionPrompt', ''), None),
    ))
    return specs

def get_condition_rule_create_flow_specs(steps):
    route_targets_by_rule = {}
    route_target_indexes = set()
    for source_idx, step in enumerate(steps):
        for rule_idx, flow_rule in enumerate(step.get('flowRules', [])):
            route_exit = flow_rule.get('routeExit')
            if not route_exit:
                continue
            target_idx = resolve_route_exit_target_index(steps, source_idx, route_exit)
            route_targets_by_rule[(source_idx, rule_idx)] = target_idx
            route_target_indexes.add(target_idx)

    specs = [make_flow_spec(None, 0, "START", step_display_name(steps[0]), "", "")]

    for source_idx, step in enumerate(steps):
        flow_rules = step.get('flowRules', [])
        if flow_rules:
            for rule_idx, flow_rule in enumerate(flow_rules):
                if flow_rule.get('routeExit'):
                    target_idx = route_targets_by_rule[(source_idx, rule_idx)]
                    target_step = steps[target_idx]
                    target_name = step_display_name(target_step)
                    condition = target_name
                    transition_prompt = render_transition_prompt(step.get('transitionPrompt', ''), target_step)
                elif should_flow_to_end_before_next_route_target(steps, source_idx, route_target_indexes):
                    target_idx = None
                    target_name = "END"
                    condition = "训练结束"
                    transition_prompt = render_transition_prompt(step.get('transitionPrompt', ''), None)
                else:
                    target_idx = source_idx + 1
                    target_step = steps[target_idx]
                    target_name = step_display_name(target_step)
                    condition = step.get('flowCondition') or target_name
                    transition_prompt = render_transition_prompt(step.get('transitionPrompt', ''), target_step)

                specs.append(make_flow_spec(
                    source_idx,
                    target_idx,
                    step_display_name(step),
                    target_name,
                    condition,
                    transition_prompt,
                    flow_rule,
                ))
            continue

        if should_flow_to_end_before_next_route_target(steps, source_idx, route_target_indexes):
            specs.append(make_flow_spec(
                source_idx,
                None,
                step_display_name(step),
                "END",
                step.get('flowCondition') or "训练结束",
                render_transition_prompt(step.get('transitionPrompt', ''), None),
            ))
        else:
            target_idx = source_idx + 1
            target_step = steps[target_idx]
            specs.append(make_flow_spec(
                source_idx,
                target_idx,
                step_display_name(step),
                step_display_name(target_step),
                step.get('flowCondition') or step_display_name(target_step),
                render_transition_prompt(step.get('transitionPrompt', ''), target_step),
            ))

    return specs

def get_create_flow_specs(steps):
    if not steps:
        return []
    if not has_condition_rules(steps):
        return assign_default_flags(get_linear_create_flow_specs(steps))
    return assign_default_flags(get_condition_rule_create_flow_specs(steps))

def get_create_flow_preview(steps):
    """Return the rebuilt linear flow preview for creation mode."""
    return [
        (
            spec["sourceName"],
            spec["targetName"],
            spec["flowCondition"],
            spec["transitionPrompt"],
        )
        for spec in get_create_flow_specs(steps)
    ]

def print_create_dry_run_preview(steps, metadata_match_count=0):
    """Print the create-mode dry-run plan without calling platform APIs."""
    flow_specs = get_create_flow_specs(steps)
    flows = get_create_flow_preview(steps)
    configuration_count = sum(1 for spec in flow_specs if spec.get("flowRule"))
    condition_group_count = sum(
        len(spec["flowRule"].get("groups", []))
        for spec in flow_specs
        if spec.get("flowRule")
    )
    print("\n🧪 创建模式 dry-run：不会调用创建、删除、更新或查询 API。")
    print(f"📋 将创建业务节点: {len(steps)}")
    print(f"🔗 将重建连线: {len(flows)}")
    if configuration_count:
        print(f"⚙️ configuration 连线: {configuration_count}，条件组: {condition_group_count}")
    if metadata_match_count:
        print(f"🧩 已匹配 metadata 节点: {metadata_match_count}")

    print("\n节点预览:")
    for idx, step in enumerate(steps, start=1):
        print(
            "  [{idx}] {name} | 训练官={trainer} | 轮次={rounds} | Step ID={step_id}".format(
                idx=idx,
                name=step.get('stepName', '未命名阶段'),
                trainer=step.get('trainerName', ''),
                rounds=step.get('interactiveRounds', ''),
                step_id=step.get('originalStepId', ''),
            )
        )

    print("\n连线预览:")
    for idx, spec in enumerate(flow_specs, start=1):
        source = spec["sourceName"]
        target = spec["targetName"]
        condition = spec["flowCondition"]
        transition_prompt = spec["transitionPrompt"]
        transition_flag = "有 transitionPrompt" if transition_prompt else "无 transitionPrompt"
        setting_type = spec["flowSettingType"]
        default_flag = "是" if spec.get("isDefault") == 1 else "否"
        if spec.get("flowRule"):
            group_count = len(spec["flowRule"].get("groups", []))
            print(
                f"  [{idx}] {source} -> {target} | flowCondition={condition!r} | "
                f"{transition_flag} | {setting_type}({group_count}组) | 默认跳转={default_flag}"
            )
        else:
            print(
                f"  [{idx}] {source} -> {target} | flowCondition={condition!r} | "
                f"{transition_flag} | {setting_type} | 默认跳转={default_flag}"
            )

    print("\n🧪 Dry-run complete. 未调用平台 API。")
    return {
        "dry_run": True,
        "step_count": len(steps),
        "flow_count": len(flows),
        "metadata_match_count": metadata_match_count,
        "flows": flows,
        "flow_specs": flow_specs,
    }

# --- API Interaction ---

def create_script_step(train_task_id, step_data, position):
    """Create a single script step."""
    url = ability_train_url("createScriptStep")
    
    # Generate a new ID for the new node
    new_step_id = generate(size=21)
    
    step_detail = {
        "nodeType": "SCRIPT_NODE",
        "stepName": step_data.get('stepName', ''),
        "description": step_data.get('description', ''),
        "prologue": step_data.get('prologue', ''),
        "modelId": step_data.get('modelId') or os.getenv('DEFAULT_MODEL_ID') or 'Doubao-Seed-1.6',
        "llmPrompt": step_data.get('llmPrompt', ''),
        "trainerName": step_data.get('trainerName', ''),
        "interactiveRounds": step_data.get('interactiveRounds', 0),
        # Default empty/preset values
        "scriptStepCover": step_data.get('scriptStepCover', {}),
        "whiteBoardSwitch": 0,
        "agentId": step_data.get('agentId') or os.getenv('DEFAULT_AGENT_ID') or 'Tg3LpKo28D',
        "avatarNid": step_data.get('avatarNid', ''),
        "videoSwitch": 0,
        "scriptStepResourceList": [],
        "knowledgeBaseSwitch": 1,
        "searchEngineSwitch": 1,
        "historyRecordNum": -1,
        "trainSubType": "ability"
    }
    apply_step_detail_metadata(step_detail, step_data)

    payload = {
        "trainTaskId": train_task_id,
        "stepId": new_step_id,
        "stepDetailDTO": step_detail,
        "positionDTO": position
    }

    try:
        response = requests.post(url, headers=get_headers(), json=payload, timeout=20)
        res_json = response.json()
        if res_json.get('code') == 200 or res_json.get('success') is True:
            print(f"✅ Created Step: {step_data.get('stepName')} (ID: {new_step_id})")
            return new_step_id
        else:
            print(f"❌ Failed to create step {step_data.get('stepName')}: {res_json}")
            return None
    except Exception as e:
        print(f"❌ Error creating step: {e}")
        return None

def create_start_end_nodes(train_task_id: str, course_id: str) -> tuple[str, str]:
    """为任务创建 SCRIPT_START 和 SCRIPT_END 节点"""
    url = ability_train_url("createScriptStep")

    # 创建 START 节点
    start_id = generate(size=21)
    start_payload = {
        "trainTaskId": train_task_id,
        "stepId": start_id,
        "stepDetailDTO": {
            "nodeType": "SCRIPT_START",
            "stepName": "defaultStepName",
            "description": "",
            "prologue": "",
            "modelId": "",
            "llmPrompt": "",
            "trainerName": "",
            "scriptStepCover": {},
            "whiteBoardSwitch": 0,
            "videoSwitch": 0,
            "scriptStepResourceList": [],
            "knowledgeBaseSwitch": 0,
            "searchEngineSwitch": 0,
            "trainSubType": "ability"
        },
        "positionDTO": {"x": 100, "y": 100},
        "courseId": course_id,
        "libraryFolderId": ""
    }

    # 创建 END 节点
    end_id = generate(size=21)
    end_payload = {
        "trainTaskId": train_task_id,
        "stepId": end_id,
        "stepDetailDTO": {
            "nodeType": "SCRIPT_END",
            "stepName": "defaultStepName",
            "description": "",
            "prologue": "",
            "modelId": "",
            "llmPrompt": "",
            "trainerName": "",
            "scriptStepCover": {},
            "whiteBoardSwitch": 0,
            "videoSwitch": 0,
            "scriptStepResourceList": [],
            "knowledgeBaseSwitch": 0,
            "searchEngineSwitch": 0,
            "trainSubType": "ability"
        },
        "positionDTO": {"x": 900, "y": 100},
        "courseId": course_id,
        "libraryFolderId": ""
    }

    try:
        # 创建 START
        resp = requests.post(url, headers=get_headers(), json=start_payload, timeout=20)
        result = resp.json()
        if result.get('code') != 200 and not result.get('success'):
            raise RuntimeError(f"创建 START 节点失败: {result}")

        # 创建 END
        resp = requests.post(url, headers=get_headers(), json=end_payload, timeout=20)
        result = resp.json()
        if result.get('code') != 200 and not result.get('success'):
            raise RuntimeError(f"创建 END 节点失败: {result}")

        return start_id, end_id
    except Exception as e:
        raise RuntimeError(f"创建 START/END 节点失败: {e}")

def edit_script_step_flow(payload):
    """Call editScriptStepFlow to save configuration-mode flow rules."""
    url = ability_train_url("editScriptStepFlow")
    flow_id = payload.get('flowId')
    try:
        response = requests.post(url, headers=get_headers(), json=payload, timeout=20)
        res_json = response.json()
        if res_json.get('code') == 200 or res_json.get('success') is True:
            print(f"✅ Updated Flow Configuration: {flow_id}")
            return True
        print(f"❌ Failed to update flow configuration {flow_id}: {res_json}")
        return False
    except Exception as e:
        print(f"❌ Error updating flow configuration {flow_id}: {e}")
        return False

def create_script_flow(
    train_task_id,
    start_id,
    end_id,
    condition_text,
    transition_prompt="",
    flow_rule=None,
    is_default=1,
):
    """Create a flow connection between two nodes."""
    validate_is_default(is_default)
    url = ability_train_url("createScriptStepFlow")
    
    flow_id = generate(size=21)
    
    payload = {
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
                    "conditions": [
                        {
                            "text": condition_text
                        }
                    ]
                }
            ]
        },
        "transitionPrompt": transition_prompt,
        "transitionHistoryNum": DEFAULT_TRANSITION_HISTORY_NUM,
        "isDefault": is_default,
        "isError": False
    }

    try:
        response = requests.post(url, headers=get_headers(), json=payload, timeout=20)
        res_json = response.json()
        if res_json.get('code') == 200 or res_json.get('success') is True:
            print(f"✅ Created Flow: {condition_text} -> (ID: {flow_id})")
            if flow_rule:
                edit_payload = build_edit_script_step_flow_payload(
                    train_task_id,
                    flow_id,
                    start_id,
                    end_id,
                    condition_text,
                    flow_rule,
                    transition_prompt=transition_prompt,
                    is_default=is_default,
                )
                return edit_script_step_flow(edit_payload)
            return True
        else:
            print(f"❌ Failed to create flow: {res_json}")
            return False
    except Exception as e:
        print(f"❌ Error creating flow: {e}")
        return False

# --- Main Flow ---


def query_script_steps(train_task_id):
    """Query existing script steps."""
    url = ability_train_url("queryScriptStepList")
    payload = {
        "trainTaskId": train_task_id,
        "trainSubType": "ability"
    }

    try:
        response = requests.post(url, headers=get_headers(), json=payload, timeout=20)
        res_json = response.json()
        if res_json.get('code') == 200 or res_json.get('success') is True:
            return res_json.get('data', [])
        print(f"❌ Failed to query existing steps: {res_json}")
        return []
    except Exception as e:
        print(f"❌ Error querying existing steps: {e}")
        return []

def get_business_script_steps(step_list):
    """Return platform SCRIPT_NODE items in the order returned by the API."""
    return [
        item for item in step_list
        if item.get('stepDetailDTO', {}).get('nodeType') == 'SCRIPT_NODE'
    ]

def build_edit_script_step_payload(existing_step, markdown_step, train_task_id, course_id):
    """Build editScriptStep payload from an existing platform step.

    Only content fields from Markdown are overwritten. Visual, audio,
    knowledge-base, resource, model, position, and flow-related fields are
    preserved from the existing platform step.
    """
    payload = copy.deepcopy(existing_step)
    payload['trainTaskId'] = train_task_id
    payload['stepId'] = existing_step.get('stepId')
    payload['courseId'] = course_id

    detail = payload.setdefault('stepDetailDTO', {})
    for field in ('stepName', 'description', 'interactiveRounds', 'prologue', 'llmPrompt'):
        if field in markdown_step:
            detail[field] = markdown_step[field]
    return payload

def get_update_field_diffs(existing_step, markdown_step):
    detail = existing_step.get('stepDetailDTO', {})
    diffs = []
    for field in ('stepName', 'description', 'interactiveRounds', 'prologue', 'llmPrompt'):
        if field not in markdown_step:
            continue
        old_value = detail.get(field)
        new_value = markdown_step.get(field)
        if old_value != new_value:
            diffs.append((field, old_value, new_value))
    return diffs

def summarize_value(value, limit=80):
    if value is None:
        return "None"
    text = str(value).replace("\n", "\\n")
    if len(text) > limit:
        return f"{text[:limit]}..."
    return text

def print_update_existing_preview(mappings):
    print("\n📋 更新预览（按顺序匹配）:")
    for idx, (markdown_step, platform_step, diffs) in enumerate(mappings, start=1):
        detail = platform_step.get('stepDetailDTO', {})
        step_id = platform_step.get('stepId')
        md_name = markdown_step.get('stepName', '未命名阶段')
        platform_name = detail.get('stepName', '未命名节点')
        print(f"  [{idx}] Markdown「{md_name}」 -> 平台「{platform_name}」 ({step_id})")
        if not diffs:
            print("      内容字段无变化")
            continue
        for field, old_value, new_value in diffs:
            print(f"      {field}: {summarize_value(old_value)} -> {summarize_value(new_value)}")

def edit_script_step(payload):
    """Call editScriptStep with a full payload based on the existing step."""
    url = ability_train_url("editScriptStep")
    step_id = payload.get('stepId')
    try:
        response = requests.post(url, headers=get_headers(), json=payload, timeout=20)
        res_json = response.json()
        if res_json.get('code') == 200 or res_json.get('success') is True:
            print(f"✅ Updated Step: {step_id}")
            return True
        print(f"❌ Failed to update step {step_id}: {res_json}")
        return False
    except Exception as e:
        print(f"❌ Error updating step {step_id}: {e}")
        return False

def update_existing_steps_from_markdown(
    markdown_path,
    train_task_id,
    *,
    dry_run=False,
    assume_yes=False,
    steps=None,
    platform_steps=None,
):
    """Update existing SCRIPT_NODE content fields by API-return order."""
    target_md = Path(markdown_path)
    if not target_md.exists():
        raise FileNotFoundError(f"Markdown file not found: {target_md}")

    course_id = require_course_id()

    if steps is None:
        print(f"📖 Parsing {target_md}...")
        steps = parse_markdown(target_md)
    else:
        print(f"📖 Reusing parsed steps from {target_md}...")

    if not steps:
        raise ValueError("No steps found in markdown.")

    if platform_steps is None:
        print(f"\n⏳ Fetching task info for Task ID: {train_task_id}...")
        platform_steps = query_script_steps(train_task_id)

    business_steps = get_business_script_steps(platform_steps)
    print(f"Found {len(steps)} Markdown steps and {len(business_steps)} platform SCRIPT_NODE steps.")

    if len(steps) != len(business_steps):
        raise ValueError(
            "Markdown 阶段数与平台业务节点数不一致，已中止。"
            f" Markdown={len(steps)}, Platform SCRIPT_NODE={len(business_steps)}"
        )

    mappings = []
    for markdown_step, platform_step in zip(steps, business_steps):
        diffs = get_update_field_diffs(platform_step, markdown_step)
        mappings.append((markdown_step, platform_step, diffs))

    print_update_existing_preview(mappings)

    if dry_run:
        print("\n🧪 Dry-run complete. 未调用 editScriptStep。")
        return {
            "dry_run": True,
            "updated_count": 0,
            "matched_count": len(mappings),
            "mappings": mappings,
        }

    if not assume_yes:
        raise ValueError("更新已有节点需要显式确认，请添加 --yes。")

    updated_count = 0
    for markdown_step, platform_step, _diffs in mappings:
        payload = build_edit_script_step_payload(platform_step, markdown_step, train_task_id, course_id)
        if not edit_script_step(payload):
            raise RuntimeError(f"更新节点失败: {platform_step.get('stepId')}")
        updated_count += 1

    print(f"\n✅ Existing step update complete. Updated {updated_count} steps.")
    return {
        "dry_run": False,
        "updated_count": updated_count,
        "matched_count": len(mappings),
        "mappings": mappings,
    }

def extract_start_end_ids(step_list):
    start_node_id = None
    end_node_id = None
    for item in step_list:
        node_type = item.get('stepDetailDTO', {}).get('nodeType')
        if node_type == 'SCRIPT_START':
            start_node_id = item.get('stepId')
        elif node_type == 'SCRIPT_END':
            end_node_id = item.get('stepId')
    return start_node_id, end_node_id


def create_start_end_nodes(train_task_id: str, course_id: str) -> tuple[str, str]:
    """为任务创建 SCRIPT_START 和 SCRIPT_END 节点"""
    url = ability_train_url("createScriptStep")

    start_id = generate(size=21)
    start_payload = {
        "trainTaskId": train_task_id,
        "stepId": start_id,
        "stepDetailDTO": {
            "nodeType": "SCRIPT_START",
            "stepName": "defaultStepName",
            "description": "",
            "prologue": "",
            "modelId": "",
            "llmPrompt": "",
            "trainerName": "",
            "scriptStepCover": {},
            "whiteBoardSwitch": 0,
            "videoSwitch": 0,
            "scriptStepResourceList": [],
            "knowledgeBaseSwitch": 0,
            "searchEngineSwitch": 0,
            "trainSubType": "ability"
        },
        "positionDTO": {"x": 100, "y": 100},
        "courseId": course_id,
        "libraryFolderId": ""
    }

    end_id = generate(size=21)
    end_payload = {
        "trainTaskId": train_task_id,
        "stepId": end_id,
        "stepDetailDTO": {
            "nodeType": "SCRIPT_END",
            "stepName": "defaultStepName",
            "description": "",
            "prologue": "",
            "modelId": "",
            "llmPrompt": "",
            "trainerName": "",
            "scriptStepCover": {},
            "whiteBoardSwitch": 0,
            "videoSwitch": 0,
            "scriptStepResourceList": [],
            "knowledgeBaseSwitch": 0,
            "searchEngineSwitch": 0,
            "trainSubType": "ability"
        },
        "positionDTO": {"x": 900, "y": 100},
        "courseId": course_id,
        "libraryFolderId": ""
    }

    try:
        resp = requests.post(url, headers=get_headers(), json=start_payload, timeout=20)
        result = resp.json()
        if result.get('code') != 200 and not result.get('success'):
            raise RuntimeError(f"创建 START 节点失败: {result}")

        resp = requests.post(url, headers=get_headers(), json=end_payload, timeout=20)
        result = resp.json()
        if result.get('code') != 200 and not result.get('success'):
            raise RuntimeError(f"创建 END 节点失败: {result}")

        return start_id, end_id
    except Exception as e:
        raise RuntimeError(f"创建 START/END 节点失败: {e}")

def query_script_step_flows(train_task_id):
    """Query existing script step flows."""
    url = ability_train_url("queryScriptStepFlowList")
    payload = {"trainTaskId": train_task_id}

    try:
        response = requests.post(url, headers=get_headers(), json=payload, timeout=20)
        res_json = response.json()
        if res_json.get('code') == 200 or res_json.get('success') is True:
            return res_json.get('data', [])
        print(f"❌ Failed to query existing flows: {res_json}")
        return []
    except Exception as e:
        print(f"❌ Error querying existing flows: {e}")
        return []

def delete_script_step_flow(train_task_id, flow_id):
    """Delete a flow by flowId."""
    url = ability_train_url("delScriptStepFlow")
    payload = {
        "trainTaskId": train_task_id,
        "flowId": flow_id
    }

    try:
        response = requests.post(url, headers=get_headers(), json=payload, timeout=20)
        res_json = response.json()
        if res_json.get('code') == 200 or res_json.get('success') is True:
            print(f"✅ Deleted Flow: {flow_id}")
            return True
        print(f"❌ Failed to delete flow {flow_id}: {res_json}")
        return False
    except Exception as e:
        print(f"❌ Error deleting flow {flow_id}: {e}")
        return False

def delete_script_step(train_task_id, step_id):
    """Delete a step by stepId."""
    url = ability_train_url("delScriptStep")
    payload = {
        "trainTaskId": train_task_id,
        "stepId": step_id
    }

    try:
        response = requests.post(url, headers=get_headers(), json=payload, timeout=20)
        res_json = response.json()
        if res_json.get('code') == 200 or res_json.get('success') is True:
            print(f"✅ Deleted Step: {step_id}")
            return True
        print(f"❌ Failed to delete step {step_id}: {res_json}")
        return False
    except Exception as e:
        print(f"❌ Error deleting step {step_id}: {e}")
        return False

def delete_existing_steps_and_flows(train_task_id, steps, flows):
    """Delete all flows first, then delete steps (excluding START/END)."""
    ok = True
    if flows:
        print(f"🧹 Deleting {len(flows)} flows...")
        for flow in flows:
            flow_id = flow.get('flowId')
            if not flow_id:
                print(f"⚠️ Skipping flow with missing flowId: {flow}")
                ok = False
                continue
            if not delete_script_step_flow(train_task_id, flow_id):
                ok = False
    if steps:
        print(f"🧹 Deleting {len(steps)} steps...")
        for step in steps:
            step_id = step.get('stepId')
            if not step_id:
                print(f"⚠️ Skipping step with missing stepId: {step}")
                ok = False
                continue
            if not delete_script_step(train_task_id, step_id):
                ok = False
    return ok

def find_flow_to_step(flows, target_step_id):
    """找到指向目标节点的流程（target_step_id 作为终点）"""
    for flow in flows:
        if flow.get('scriptStepEndId') == target_step_id:
            return flow
    return None

def find_flows_from_step(flows, source_step_id):
    """找到从源节点出发的所有流程"""
    return [f for f in flows if f.get('scriptStepStartId') == source_step_id]

def build_steps_from_markdown(
    markdown_path,
    train_task_id,
    *,
    start_node_id=None,
    end_node_id=None,
    flow_list=None,
    insert_after_step_id=None,
    insert_after_step_name=None,
    steps=None,
    metadata_by_step_id=None,
):
    """Parse markdown and create script steps/flows for a task."""
    target_md = Path(markdown_path)
    if not target_md.exists():
        raise FileNotFoundError(f"Markdown file not found: {target_md}")

    if steps is None:
        print(f"📖 Parsing {target_md}...")
        steps = parse_markdown(target_md)
    else:
        print(f"📖 Reusing parsed steps from {target_md}...")

    if not steps:
        raise ValueError("No steps found in markdown.")

    metadata_match_count = apply_step_metadata(steps, metadata_by_step_id)
    if metadata_by_step_id:
        print(f"🧩 Applied metadata to {metadata_match_count}/{len(steps)} steps.")

    print(f"Found {len(steps)} steps.")

    if start_node_id is None or end_node_id is None:
        print(f"\n⏳ Fetching task info for Task ID: {train_task_id}...")
        step_list = query_script_steps(train_task_id)
        start_node_id, end_node_id = extract_start_end_ids(step_list)

    if flow_list is None:
        flow_list = query_script_step_flows(train_task_id)

    if insert_after_step_id:
        print(f"✅ 将在「{insert_after_step_name}」后面插入 {len(steps)} 个新节点")

    created_steps_map = {}
    x_start = 100
    y_start = 300
    x_gap = 400
    global_cover = None

    print("\n🚀 Creating Nodes...")
    for idx, step in enumerate(steps):
        background_image = step.get('backgroundImage')
        if background_image:
            if is_remote_url(background_image):
                cover = build_script_step_cover_from_url(
                    background_image,
                    existing_cover=step.get('scriptStepCover'),
                )
                step['scriptStepCover'] = cover
                if idx == 0:
                    global_cover = cover
            else:
                image_path = Path(background_image)
                if not image_path.is_absolute():
                    image_path = (target_md.parent / image_path).resolve()
                cover = upload_cover_image(image_path)
                if cover:
                    step['scriptStepCover'] = cover
                    if idx == 0:
                        global_cover = cover
                else:
                    print(f"⚠️ Failed to upload background image for step: {step.get('stepName')}")
        elif idx == 0 and step.get('scriptStepCover'):
            global_cover = step.get('scriptStepCover')
        elif idx > 0 and global_cover and not step.get('scriptStepCover'):
            step['scriptStepCover'] = global_cover

        pos = {"x": x_start + (idx * x_gap), "y": y_start}
        new_id = create_script_step(train_task_id, step, pos)
        if new_id:
            created_steps_map[idx] = new_id
        else:
            raise RuntimeError(f"Failed to create step: {step.get('stepName')}")

    print("\n🔗 Creating Flows...")

    if insert_after_step_id:
        outgoing_flows = find_flows_from_step(flow_list, insert_after_step_id)
        first_condition = ""
        first_transition = ""
        if outgoing_flows:
            first_condition = outgoing_flows[0].get('flowCondition', '')
            first_transition = outgoing_flows[0].get('transitionPrompt', '')

        first_new_step_id = created_steps_map[0]
        first_new_name = steps[0].get('stepName', '新节点')
        print(f"   Linking {insert_after_step_name} -> {first_new_name} (并行分支)")
        if not create_script_flow(train_task_id, insert_after_step_id, first_new_step_id, first_condition, first_transition):
            raise RuntimeError("Failed to create flow from insert point to first step.")

        for i in range(len(steps) - 1):
            current_step_id = created_steps_map.get(i)
            next_step_id = created_steps_map.get(i + 1)
            source_step_detail = steps[i]
            target_step_detail = steps[i + 1]
            condition = source_step_detail.get('flowCondition') or target_step_detail.get('stepName', '下一步')
            transition_prompt = source_step_detail.get('transitionPrompt', '')
            print(f"   Linking {source_step_detail.get('stepName')} -> {target_step_detail.get('stepName')}")
            if not create_script_flow(train_task_id, current_step_id, next_step_id, condition, transition_prompt):
                raise RuntimeError(f"Failed to create flow: {source_step_detail.get('stepName')} -> {target_step_detail.get('stepName')}")

        last_idx = len(steps) - 1
        last_new_step_id = created_steps_map.get(last_idx)
        last_step_detail = steps[last_idx]
        condition = last_step_detail.get('flowCondition') or "训练结束"
        transition_prompt = last_step_detail.get('transitionPrompt', '')
        print(f"   Linking {last_step_detail.get('stepName')} -> Task End (并行分支)")
        if end_node_id and not create_script_flow(train_task_id, last_new_step_id, end_node_id, condition, transition_prompt):
            raise RuntimeError(f"Failed to create flow: {last_step_detail.get('stepName')} -> Task End")
    else:
        flow_specs = get_create_flow_specs(steps)
        for idx, flow_spec in enumerate(flow_specs, start=1):
            source_idx = flow_spec["sourceIndex"]
            target_idx = flow_spec["targetIndex"]
            source_step_id = start_node_id if source_idx is None else created_steps_map.get(source_idx)
            target_step_id = end_node_id if target_idx is None else created_steps_map.get(target_idx)

            if not source_step_id or not target_step_id:
                raise RuntimeError(
                    f"Failed to resolve flow endpoint: {flow_spec['sourceName']} -> {flow_spec['targetName']}"
                )

            print(
                f"   Linking [{idx}] {flow_spec['sourceName']} -> {flow_spec['targetName']} "
                f"with Condition: '{flow_spec['flowCondition']}' "
                f"({flow_spec['flowSettingType']})"
            )
            if not create_script_flow(
                train_task_id,
                source_step_id,
                target_step_id,
                flow_spec["flowCondition"],
                flow_spec["transitionPrompt"],
                flow_rule=flow_spec.get("flowRule"),
                is_default=flow_spec["isDefault"],
            ):
                raise RuntimeError(
                    f"Failed to create flow: {flow_spec['sourceName']} -> {flow_spec['targetName']}"
                )

    print("\n✅ Task Generation Complete.")
    return {
        "steps": steps,
        "created_steps_map": created_steps_map,
        "start_node_id": start_node_id,
        "end_node_id": end_node_id,
    }

def parse_cli_args(argv=None):
    parser = argparse.ArgumentParser(description="从 Markdown 创建或更新能力训练脚本节点")
    parser.add_argument("markdown_path", nargs="?", help="训练剧本配置 Markdown 文件路径")
    parser.add_argument("train_task_id", nargs="?", help="目标训练任务 ID")
    parser.add_argument(
        "--update-existing",
        action="store_true",
        help="按平台返回顺序更新已有 SCRIPT_NODE 内容字段，不创建节点和连线",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="创建模式仅解析并打印重建计划；更新模式仅打印映射和字段差异，不调用 API",
    )
    parser.add_argument(
        "--metadata-json",
        help="节点资源 metadata JSON；创建节点时按 Markdown Step ID 合并封面、资源、知识库等字段",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="确认执行更新已有节点；仅 --update-existing 非 dry-run 时需要",
    )
    return parser.parse_args(argv)

def main():
    args = parse_cli_args()
    load_env_config()
    
    print("--- Training Task Generator ---")
    
    # 1. Train Task ID
    train_task_id = os.getenv("TASK_ID")
    print(f"---- Train Task ID: {train_task_id} ----")
    # Support passing as 2nd arg: python script.py <md> <task_id>
    if args.train_task_id:
        train_task_id = args.train_task_id
    
    if not train_task_id:
        train_task_id = input("Please enter Train Task ID: ").strip()

    # 2. Markdown File
    target_md = None
    # Support passing as 1st arg: python script.py <md>
    if args.markdown_path:
        candidate = Path(args.markdown_path)
        if candidate.exists():
            target_md = candidate
        
    if not target_md:
        md_input = input("Please enter the path to the Markdown file: ").strip()
        # Handle drag-and-drop quotes
        md_input = md_input.replace("'", "").replace('"', "").strip()
        if md_input:
            target_md = Path(md_input)
            
    if not target_md or not target_md.exists():
        print(f"❌ Markdown file not found or invalid: {target_md}")
        return

    metadata_by_step_id = {}
    if args.metadata_json:
        try:
            metadata_by_step_id = load_step_metadata(args.metadata_json)
            print(f"🧩 Loaded metadata for {len(metadata_by_step_id)} original steps: {args.metadata_json}")
        except Exception as exc:
            print(f"❌ {exc}")
            return

    if args.update_existing:
        try:
            update_existing_steps_from_markdown(
                target_md,
                train_task_id,
                dry_run=args.dry_run,
                assume_yes=args.yes,
            )
        except Exception as exc:
            print(f"❌ {exc}")
        return

    if args.dry_run:
        try:
            print(f"📖 Parsing {target_md}...")
            steps = parse_markdown(target_md)
            if not steps:
                raise ValueError("No steps found in markdown.")
            metadata_match_count = apply_step_metadata(steps, metadata_by_step_id)
            print_create_dry_run_preview(steps, metadata_match_count=metadata_match_count)
        except Exception as exc:
            print(f"❌ {exc}")
        return

    # Check for existing start/end nodes
    print(f"\n⏳ Fetching task info for Task ID: {train_task_id}...")
    step_list = query_script_steps(train_task_id)
    start_node_id, end_node_id = extract_start_end_ids(step_list)
    if not start_node_id or not end_node_id:
        print("🔧 未找到 START/END 节点，正在自动创建...")
        course_id = os.getenv("COURSE_ID", "")
        if not course_id:
            print("❌ 缺少 COURSE_ID 环境变量，无法创建 START/END 节点")
            return
        start_node_id, end_node_id = create_start_end_nodes(train_task_id, course_id)
        print(f"✅ 已创建 START 节点: {start_node_id}")
        print(f"✅ 已创建 END 节点: {end_node_id}")
    else:
        print(f"✅ Found Start Node: {start_node_id}, End Node: {end_node_id}")

    flow_list = query_script_step_flows(train_task_id)
    existing_steps = [
        item for item in step_list
        if item.get('stepDetailDTO', {}).get('nodeType') not in ('SCRIPT_START', 'SCRIPT_END')
    ]
    if existing_steps:
        step_names = [
            item.get('stepDetailDTO', {}).get('stepName', '未命名步骤')
            for item in existing_steps
        ]
        print(f"⚠️ Detected existing nodes ({len(existing_steps)}): {', '.join(step_names)}")
        confirm = input("是否删除当前所有节点并重新创建? (y/N): ").strip().lower()
        if confirm in ("y", "yes"):
            if not delete_existing_steps_and_flows(train_task_id, existing_steps, flow_list):
                print("❌ 删除现有节点/连线失败，已停止创建。")
                return
            step_list = query_script_steps(train_task_id)
            start_node_id, end_node_id = extract_start_end_ids(step_list)
            if not start_node_id or not end_node_id:
                print("🔧 删除后未找到 START/END 节点，正在自动创建...")
                course_id = os.getenv("COURSE_ID", "")
                if not course_id:
                    print("❌ 缺少 COURSE_ID 环境变量，无法创建 START/END 节点")
                    return
                start_node_id, end_node_id = create_start_end_nodes(train_task_id, course_id)
                print(f"✅ 已创建 START 节点: {start_node_id}")
                print(f"✅ 已创建 END 节点: {end_node_id}")
            # 重置插入模式变量
            insert_after_step_id = None
            insert_after_step_name = None
        else:
            # 显示现有节点列表供用户选择
            print("\n📋 现有节点列表:")
            for i, item in enumerate(existing_steps):
                name = item.get('stepDetailDTO', {}).get('stepName', '未命名步骤')
                print(f"  [{i+1}] {name}")
            print(f"  [0] 在 START 节点后插入（作为第一个节点）")

            # 获取用户选择
            while True:
                choice = input("\n请选择要在哪个节点后面插入新节点 (输入编号): ").strip()
                try:
                    idx = int(choice)
                    if 0 <= idx <= len(existing_steps):
                        break
                    print(f"⚠️ 请输入 0 到 {len(existing_steps)} 之间的数字")
                except ValueError:
                    print("⚠️ 请输入有效的数字")

            if idx == 0:
                insert_after_step_id = start_node_id
                insert_after_step_name = "START"
            else:
                insert_after_step_id = existing_steps[idx-1].get('stepId')
                insert_after_step_name = existing_steps[idx-1].get('stepDetailDTO', {}).get('stepName', '未命名步骤')

    else:
        insert_after_step_id = None
        insert_after_step_name = None

    try:
        build_steps_from_markdown(
            target_md,
            train_task_id,
            start_node_id=start_node_id,
            end_node_id=end_node_id,
            flow_list=flow_list,
            insert_after_step_id=insert_after_step_id,
            insert_after_step_name=insert_after_step_name,
            metadata_by_step_id=metadata_by_step_id,
        )
    except Exception as exc:
        print(f"❌ {exc}")
        return

if __name__ == "__main__":
    main()
