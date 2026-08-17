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
DEFAULT_POLYMAS_API_BASE = "https://cloudapi.polymas.com"
DEFAULT_TRANSITION_HISTORY_NUM = 10
DEFAULT_VOICE_TEMPLATE_TYPE = "ONLINE_DOUBAO"
DEFAULT_DIGITAL_HUMAN_OWNER_LIST_TYPE = "NORMAL"

DEFAULT_ABILITY_STEP_EXT_PROPERTY = {
    "trainSubType": "ability",
    "resources": None,
    "bgMediaType": 1,
    "bgMediaVolume": 80,
    "bgMusic": {},
    "bgMusicVolume": 30,
    "transitionBgMedia": None,
    "transitionBgMediaType": 1,
    "transitionBgMediaVolume": 30,
    "useTransitionBgMediaTransition": 0,
    "transitionBgMusic": None,
    "transitionBgMusicVolume": 30,
    "flowAsideContent": "",
    "flowAsideVoiceType": None,
    "flowAsideVoiceNid": None,
    "flowAsideVoiceSpeed": 50,
    "flowAsideVoiceVolume": 30,
    "flowAsideMp3Url": "",
    "hideSubtitle": 0,
    "useAsideTransition": 0,
}

STEP_DETAIL_METADATA_FIELDS = (
    "scriptStepCover",
    "scriptStepResourceList",
    "knowledgeBaseSwitch",
    "knowledgeBaseId",
    "searchEngineSwitch",
    "whiteBoardSwitch",
    "videoSwitch",
    "historyRecordNum",
    "agentId",
    "agentVoiceId",
    "avatarNid",
    "digitalHumanType",
    "digitalHumanInfo",
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
    "contentSkip",
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


def get_polymas_api_base():
    """Return the configured Polymas cloud API base URL."""
    return os.getenv("POLYMAS_API_BASE", DEFAULT_POLYMAS_API_BASE).strip().rstrip("/")


def polymas_api_url(endpoint):
    return f"{get_polymas_api_base()}/{endpoint.lstrip('/')}"


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

def optional_str(value):
    if value is None:
        return ""
    return str(value).strip()

def first_non_empty(*values):
    for value in values:
        text = optional_str(value)
        if text:
            return text
    return ""

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

def guess_mime_type(file_path):
    file_ext = Path(file_path).suffix.lower()
    mime_types = {
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.gif': 'image/gif',
        '.webp': 'image/webp',
    }
    return mime_types.get(file_ext, 'application/octet-stream')

def upload_basic_resource_file(file_path, *, hidden=None, label="file"):
    """Upload a local file through the current frontend upload endpoint shape."""
    url = polymas_api_url("basic-resource/file/upload")
    if hidden is not None:
        url = f"{url}?hidden={'true' if hidden else 'false'}"
    identify_code = str(uuid.uuid4())

    file_path = Path(file_path)
    if not file_path.exists():
        print(f"⚠️ {label} not found: {file_path}")
        return None

    file_name = file_path.name
    file_size = file_path.stat().st_size
    mime_type = guess_mime_type(file_path)

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
            print(f"❌ Error uploading {label} {file_name}: {e}")
            return None

    if not result.get('success'):
        print(f"❌ {label} upload failed: {result}")
        return None

    data = result.get('data', {})
    file_id = data.get('fileId')
    file_url = data.get('ossUrl') or data.get('fileUrl')
    if not file_id or not file_url:
        print(f"⚠️ {label} upload missing fileId/fileUrl: {result}")
        return None

    print(f"✅ {label} uploaded: {file_name}")
    return {
        "fileId": file_id,
        "fileUrl": file_url,
        "ossUrl": data.get('ossUrl') or file_url,
        "raw": data,
    }

def upload_cover_image(file_path):
    upload_result = upload_basic_resource_file(file_path, label="Background image")
    if not upload_result:
        return None
    return {"fileId": upload_result["fileId"], "fileUrl": upload_result["fileUrl"]}

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
    collect_pdfs = False

    for line in lines:
        stripped = line.strip()
        # Normalize only for field matching. Preserve original value punctuation.
        normalized = stripped.replace('：', ':')

        # Collect PDF list items for 配套知识库
        if collect_pdfs and normalized.startswith('- '):
            pdf_name = normalized[2:].strip()
            current_step.setdefault('knowledgeBasePDFs', []).append(pdf_name)
            continue
        if collect_pdfs and (normalized.startswith('**') or normalized.startswith('### ')):
            collect_pdfs = False

        # New Step Start
        if normalized.startswith('### 阶段'):
            if current_step:
                steps.append(current_step)
            current_step = {}
            if ':' in normalized:
                # "### Phase 1: Name" -> "Name"
                current_step['stepName'] = extract_md_field_value(stripped)
            continue
            
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

        if normalized.startswith('**数字人**:') or normalized.startswith('**数字人配置**:'):
            current_step['customDigitalHuman'] = normalize_md_value(extract_md_field_value(stripped))
            continue

        if normalized.startswith('**数字人名称**:') or normalized.startswith('**数字人名字**:'):
            current_step['digitalHumanName'] = normalize_md_value(extract_md_field_value(stripped))
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

        if normalized.startswith('**配套知识库'):
            collect_pdfs = True
            current_step.setdefault('knowledgeBasePDFs', [])
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

def post_polymas_json(endpoint, payload, *, timeout=20):
    response = requests.post(polymas_api_url(endpoint), headers=get_headers(), json=payload, timeout=timeout)
    try:
        return response.json()
    except Exception as exc:
        raise RuntimeError(f"Polymas API returned non-JSON response for {endpoint}: {exc}") from exc

def is_success_response(response_json):
    return response_json.get('code') == 200 or response_json.get('code') == "200" or response_json.get('success') is True

def get_current_user_detail():
    result = post_polymas_json("console/v1/get-current-user-detail", {})
    if not is_success_response(result):
        raise RuntimeError(f"获取当前用户失败: {result}")
    return result.get('data') or {}

def get_current_user_nid():
    env_user_nid = first_non_empty(os.getenv("POLYMAS_USER_NID"), os.getenv("USER_NID"))
    if env_user_nid:
        return env_user_nid
    user_detail = get_current_user_detail()
    user_nid = first_non_empty(user_detail.get('userNid'))
    if not user_nid:
        raise RuntimeError(f"当前用户信息缺少 userNid: {user_detail}")
    return user_nid

def get_app_code():
    return first_non_empty(os.getenv("APP_CODE"))

def query_ai_voice_list(course_id=""):
    payload = {"voiceTemplateType": DEFAULT_VOICE_TEMPLATE_TYPE}
    if course_id:
        payload["courseId"] = course_id
    result = post_polymas_json("ai-profile/ai_voice/list", payload)
    if not is_success_response(result):
        raise RuntimeError(f"查询音色列表失败: {result}")
    return result.get('data') or []

def query_digital_human_owner_list(user_nid, *, app_code="", course_id="", owner_list_type=DEFAULT_DIGITAL_HUMAN_OWNER_LIST_TYPE):
    payload = {
        "userNid": user_nid,
        "sort": 2,
    }
    if app_code:
        payload["appCode"] = app_code
    if course_id:
        payload["courseId"] = course_id
    if owner_list_type:
        payload["type"] = owner_list_type
    result = post_polymas_json("ai-profile/digital_human/owner/list", payload)
    if not is_success_response(result):
        raise RuntimeError(f"查询数字人列表失败: {result}")
    return result.get('data') or []

def save_owner_avatar_resource(user_nid, *, app_code="", avatar_url="", avatar_dynamic_url="", avatar_nid=""):
    if not avatar_url:
        raise ValueError("保存数字人形象需要 avatar_url")
    payload = {
        "userNid": user_nid,
        "avatarUrl": avatar_url,
        "avatarDynamicUrl": avatar_dynamic_url or avatar_url,
    }
    if app_code:
        payload["appCode"] = app_code
    if avatar_nid:
        payload["avatarNid"] = avatar_nid
    result = post_polymas_json("ai-profile/ai_avatar/saveAndSyncResource", {**payload, "sync": False})
    if not is_success_response(result):
        raise RuntimeError(f"同步数字人形象失败: {result}")
    data = result.get('data') or {}
    return first_non_empty(data.get('avatarNid'), data.get('nid'), avatar_nid)

def create_custom_digital_human(user_nid, *, app_code="", voice_nid="", avatar_nid="", digital_human_name="", digital_human_type="NORMAL", rtc_digital_human_nid=""):
    if not user_nid:
        raise ValueError("创建数字人需要 userNid")
    if not voice_nid:
        raise ValueError("创建数字人需要 voiceNid")
    if not digital_human_name:
        raise ValueError("创建数字人需要 digitalHumanName")

    payload = {
        "userNid": user_nid,
        "type": digital_human_type,
        "voiceNid": voice_nid,
        "digitalHumanName": digital_human_name,
    }
    if app_code:
        payload["appCode"] = app_code
    if digital_human_type == "RTC":
        payload["digitalHumanNid"] = rtc_digital_human_nid
    else:
        if not avatar_nid:
            raise ValueError("NORMAL 数字人需要 avatarNid")
        payload["avatarNid"] = avatar_nid

    result = post_polymas_json("ai-profile/digital_human/custom/addAndSyncResource", payload)
    if not is_success_response(result):
        raise RuntimeError(f"创建数字人失败: {result}")
    data = result.get('data') or {}
    custom_nid = first_non_empty(data.get('customNid'), data.get('nid'), data.get('digitalHumanNid'))
    if not custom_nid:
        raise RuntimeError(f"创建数字人响应缺少 customNid: {result}")
    return custom_nid

def find_ai_voice(voice_list, value):
    target = optional_str(value)
    if not target:
        return None
    for voice in voice_list:
        candidates = (
            voice.get('nid'),
            voice.get('voiceTone'),
            voice.get('voiceParam'),
            voice.get('bigModelVoiceParam'),
        )
        if any(optional_str(candidate) == target for candidate in candidates):
            return voice
    return None

def get_digital_human_identifier(owner_detail):
    if not isinstance(owner_detail, dict):
        return ""
    return first_non_empty(
        owner_detail.get('customNid'),
        owner_detail.get('digitalHumanNid'),
        owner_detail.get('nid'),
        owner_detail.get('avatarNid'),
    )

def find_digital_human_owner(owner_list, *, identifier="", name="", voice_nid="", avatar_nid=""):
    identifier = optional_str(identifier)
    name = optional_str(name)
    voice_nid = optional_str(voice_nid)
    avatar_nid = optional_str(avatar_nid)

    if identifier:
        for owner in owner_list:
            candidates = (
                owner.get('customNid'),
                owner.get('digitalHumanNid'),
                owner.get('nid'),
                owner.get('avatarNid'),
                owner.get('digitalHumanName'),
                owner.get('name'),
            )
            if any(optional_str(candidate) == identifier for candidate in candidates):
                return owner

    if name:
        for owner in owner_list:
            owner_name = first_non_empty(owner.get('digitalHumanName'), owner.get('name'))
            if owner_name != name:
                continue
            if voice_nid and optional_str(owner.get('voiceNid')) != voice_nid:
                continue
            if avatar_nid and optional_str(owner.get('avatarNid')) != avatar_nid:
                continue
            return owner

    if voice_nid and avatar_nid:
        for owner in owner_list:
            if optional_str(owner.get('voiceNid')) == voice_nid and optional_str(owner.get('avatarNid')) == avatar_nid:
                return owner
    return None

def apply_digital_human_owner_detail(step, owner_detail):
    """Backfill script-step fields from digital_human/owner/list response data."""
    if not isinstance(owner_detail, dict):
        return step

    custom_nid = get_digital_human_identifier(owner_detail)
    if custom_nid:
        step['customDigitalHuman'] = custom_nid

    voice_nid = first_non_empty(owner_detail.get('voiceNid'), owner_detail.get('voiceTemplateNid'))
    if voice_nid:
        step['agentId'] = voice_nid

    avatar_nid = first_non_empty(owner_detail.get('avatarNid'))
    if avatar_nid:
        step['avatarNid'] = avatar_nid

    agent_voice_id = first_non_empty(owner_detail.get('bigModelVoiceParam'))
    if agent_voice_id:
        step['agentVoiceId'] = agent_voice_id

    if 'digitalHumanType' in owner_detail:
        step['digitalHumanType'] = owner_detail.get('digitalHumanType')
    if 'projectId' in owner_detail:
        step['projectId'] = owner_detail.get('projectId') or ""
    return step

def build_script_step_detail(step_data):
    """Build the current createScriptStep detail payload from parsed Markdown data."""
    step_detail = {
        "nodeType": "SCRIPT_NODE",
        "stepName": step_data.get('stepName', ''),
        "description": step_data.get('description', ''),
        "prologue": step_data.get('prologue', ''),
        "modelId": step_data.get('modelId') or os.getenv('DEFAULT_MODEL_ID') or 'Doubao-Seed-1.6',
        "llmPrompt": step_data.get('llmPrompt', ''),
        "trainerName": step_data.get('trainerName', ''),
        "interactiveRounds": step_data.get('interactiveRounds', 0),
        "scriptStepCover": step_data.get('scriptStepCover', {}),
        "whiteBoardSwitch": 0,
        "agentId": step_data.get('agentId') or os.getenv('DEFAULT_AGENT_ID') or 'Tg3LpKo28D',
        "agentVoiceId": step_data.get('agentVoiceId', ''),
        "avatarNid": step_data.get('avatarNid', ''),
        "customDigitalHuman": step_data.get('customDigitalHuman', ''),
        "digitalHumanType": step_data.get('digitalHumanType'),
        "projectId": step_data.get('projectId', ''),
        "videoSwitch": 0,
        "scriptStepResourceList": [],
        "knowledgeBaseSwitch": 1,
        "searchEngineSwitch": 1,
        "historyRecordNum": -1,
        "trainTime": step_data.get('trainTime', -1),
        "stepExtProperty": copy.deepcopy(DEFAULT_ABILITY_STEP_EXT_PROPERTY),
        "trainSubType": "ability"
    }
    apply_step_detail_metadata(step_detail, step_data)
    return step_detail

def step_needs_digital_human_resolution(step):
    return any(
        optional_str(step.get(field))
        for field in ("customDigitalHuman", "digitalHumanName", "agentId", "avatarNid")
    )

def build_digital_human_context(course_id=""):
    return {
        "course_id": optional_str(course_id),
        "user_nid": first_non_empty(os.getenv("POLYMAS_USER_NID"), os.getenv("USER_NID")),
        "app_code": get_app_code(),
        "voice_list": None,
        "owner_list": None,
        "avatar_cache": {},
        "created_cache": {},
    }

def ensure_digital_human_user_nid(context):
    if not context.get("user_nid"):
        context["user_nid"] = get_current_user_nid()
    return context["user_nid"]

def ensure_voice_list(context):
    if context.get("voice_list") is None:
        context["voice_list"] = query_ai_voice_list(context.get("course_id", ""))
    return context["voice_list"]

def ensure_owner_list(context, *, refresh=False):
    if refresh or context.get("owner_list") is None:
        user_nid = ensure_digital_human_user_nid(context)
        context["owner_list"] = query_digital_human_owner_list(
            user_nid,
            app_code=context.get("app_code", ""),
            course_id=context.get("course_id", ""),
        )
    return context["owner_list"]

def looks_like_local_image(value):
    text = optional_str(value)
    if not text or is_remote_url(text):
        return False
    suffix = Path(text).suffix.lower()
    return suffix in {".png", ".jpg", ".jpeg", ".gif", ".webp"}

def resolve_avatar_image_path(avatar_value, markdown_path):
    avatar_path = Path(avatar_value)
    if not avatar_path.is_absolute():
        avatar_path = (Path(markdown_path).parent / avatar_path).resolve()
    return avatar_path

def save_avatar_url_once(context, avatar_url, *, existing_avatar_nid=""):
    avatar_url = optional_str(avatar_url)
    if not avatar_url:
        return ""
    cache_key = (avatar_url, optional_str(existing_avatar_nid))
    if cache_key in context["avatar_cache"]:
        return context["avatar_cache"][cache_key]
    user_nid = ensure_digital_human_user_nid(context)
    avatar_nid = save_owner_avatar_resource(
        user_nid,
        app_code=context.get("app_code", ""),
        avatar_url=avatar_url,
        avatar_dynamic_url=avatar_url,
        avatar_nid=existing_avatar_nid,
    )
    context["avatar_cache"][cache_key] = avatar_nid
    return avatar_nid

def resolve_avatar_nid_for_step(step, markdown_path, context, voice_detail=None):
    avatar_value = optional_str(step.get('avatarNid'))

    if avatar_value and is_remote_url(avatar_value):
        return save_avatar_url_once(context, avatar_value)

    if avatar_value and looks_like_local_image(avatar_value):
        avatar_path = resolve_avatar_image_path(avatar_value, markdown_path)
        upload_result = upload_basic_resource_file(avatar_path, hidden=False, label="Digital human avatar")
        if not upload_result:
            raise RuntimeError(f"数字人形象上传失败: {avatar_path}")
        return save_avatar_url_once(context, upload_result["ossUrl"])

    if avatar_value:
        return avatar_value

    if isinstance(voice_detail, dict):
        voice_avatar_url = first_non_empty(
            voice_detail.get('avatar'),
            voice_detail.get('digitalHumanAvatarUrl'),
            voice_detail.get('voiceAvatarUrl'),
        )
        if voice_avatar_url:
            return save_avatar_url_once(context, voice_avatar_url)
    return ""

def resolve_step_digital_human(step, markdown_path, context):
    if not step_needs_digital_human_resolution(step):
        return step

    custom_identifier = optional_str(step.get('customDigitalHuman'))
    digital_human_name = first_non_empty(
        step.get('digitalHumanName'),
        step.get('trainerName'),
        step.get('stepName'),
    )
    voice_value = optional_str(step.get('agentId'))
    voice_detail = None
    voice_nid = voice_value

    if voice_value:
        voice_detail = find_ai_voice(ensure_voice_list(context), voice_value)
        if voice_detail:
            voice_nid = first_non_empty(voice_detail.get('nid'), voice_value)
            step['agentId'] = voice_nid
            agent_voice_id = first_non_empty(voice_detail.get('bigModelVoiceParam'))
            if agent_voice_id:
                step['agentVoiceId'] = agent_voice_id

    owner_list = ensure_owner_list(context)
    owner_detail = find_digital_human_owner(
        owner_list,
        identifier=custom_identifier,
        name=digital_human_name,
        voice_nid=voice_nid,
    )
    if owner_detail and not optional_str(step.get('avatarNid')):
        return apply_digital_human_owner_detail(step, owner_detail)
    if owner_detail and custom_identifier:
        return apply_digital_human_owner_detail(step, owner_detail)

    if custom_identifier and not voice_nid and not optional_str(step.get('avatarNid')):
        print(f"⚠️ 未在数字人列表中找到 {custom_identifier}，将仅写入 customDigitalHuman。")
        return step

    if not voice_nid:
        print(f"⚠️ 阶段「{step.get('stepName', '')}」缺少声音，无法自动创建数字人。")
        return step

    avatar_nid = resolve_avatar_nid_for_step(step, markdown_path, context, voice_detail=voice_detail)
    if not avatar_nid:
        print(f"⚠️ 阶段「{step.get('stepName', '')}」缺少形象，无法自动创建数字人。")
        return step

    owner_detail = find_digital_human_owner(
        owner_list,
        identifier=custom_identifier,
        name=digital_human_name,
        voice_nid=voice_nid,
        avatar_nid=avatar_nid,
    )
    if owner_detail:
        return apply_digital_human_owner_detail(step, owner_detail)

    cache_key = (digital_human_name, voice_nid, avatar_nid)
    custom_nid = context["created_cache"].get(cache_key)
    if not custom_nid:
        custom_nid = create_custom_digital_human(
            ensure_digital_human_user_nid(context),
            app_code=context.get("app_code", ""),
            voice_nid=voice_nid,
            avatar_nid=avatar_nid,
            digital_human_name=digital_human_name,
        )
        context["created_cache"][cache_key] = custom_nid
        print(f"✅ Created digital human: {digital_human_name} ({custom_nid})")

    synthetic_owner = {
        "customNid": custom_nid,
        "voiceNid": voice_nid,
        "avatarNid": avatar_nid,
        "bigModelVoiceParam": step.get('agentVoiceId', ''),
    }
    owner_list.append(synthetic_owner)
    return apply_digital_human_owner_detail(step, synthetic_owner)

def resolve_steps_digital_humans(steps, markdown_path, *, course_id=""):
    if not any(step_needs_digital_human_resolution(step) for step in steps):
        return 0
    context = build_digital_human_context(course_id=course_id)
    resolved_count = 0
    for step in steps:
        before = optional_str(step.get('customDigitalHuman'))
        resolve_step_digital_human(step, markdown_path, context)
        after = optional_str(step.get('customDigitalHuman'))
        if after:
            resolved_count += 1
    return resolved_count

def get_create_flow_preview(steps):
    """Return the rebuilt linear flow preview for creation mode."""
    if not steps:
        return []

    flows = [("START", steps[0].get('stepName', '未命名阶段'), "", "")]
    for idx in range(len(steps) - 1):
        source_step = steps[idx]
        target_step = steps[idx + 1]
        condition = source_step.get('flowCondition') or target_step.get('stepName', '下一步')
        transition_prompt = source_step.get('transitionPrompt', '')
        flows.append((
            source_step.get('stepName', '未命名阶段'),
            target_step.get('stepName', '未命名阶段'),
            condition,
            transition_prompt,
        ))

    last_step = steps[-1]
    flows.append((
        last_step.get('stepName', '未命名阶段'),
        "END",
        last_step.get('flowCondition') or "训练结束",
        last_step.get('transitionPrompt', ''),
    ))
    return flows

def print_create_dry_run_preview(steps, metadata_match_count=0):
    """Print the create-mode dry-run plan without calling platform APIs."""
    flows = get_create_flow_preview(steps)
    print("\n🧪 创建模式 dry-run：不会调用创建、删除、更新或查询 API。")
    print(f"📋 将创建业务节点: {len(steps)}")
    print(f"🔗 将重建连线: {len(flows)}")
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
    for idx, (source, target, condition, transition_prompt) in enumerate(flows, start=1):
        transition_flag = "有 transitionPrompt" if transition_prompt else "无 transitionPrompt"
        print(f"  [{idx}] {source} -> {target} | flowCondition={condition!r} | {transition_flag}")

    print("\n🧪 Dry-run complete. 未调用平台 API。")
    return {
        "dry_run": True,
        "step_count": len(steps),
        "flow_count": len(flows),
        "metadata_match_count": metadata_match_count,
        "flows": flows,
    }

# --- API Interaction ---

def create_script_step(train_task_id, step_data, position):
    """Create a single script step."""
    url = ability_train_url("createScriptStep")
    
    # Generate a new ID for the new node
    new_step_id = generate(size=21)
    
    step_detail = build_script_step_detail(step_data)

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

def create_script_flow(train_task_id, start_id, end_id, condition_text, transition_prompt="", is_default=True):
    """Create a flow connection between two nodes."""
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
        "isDefault": 1 if is_default else 0,
        "isError": False
    }

    try:
        response = requests.post(url, headers=get_headers(), json=payload, timeout=20)
        res_json = response.json()
        if res_json.get('code') == 200 or res_json.get('success') is True:
            print(f"✅ Created Flow: {condition_text} -> (ID: {flow_id})")
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

    digital_human_count = resolve_steps_digital_humans(
        steps,
        target_md,
        course_id=os.getenv("COURSE_ID", ""),
    )
    if digital_human_count:
        print(f"🧑‍🏫 Resolved digital human config for {digital_human_count}/{len(steps)} steps.")

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
        if start_node_id and len(steps) > 0:
            print(f"   Linking Task Start ({start_node_id}) -> Step 1 ({steps[0].get('stepName')})")
            if not create_script_flow(train_task_id, start_node_id, created_steps_map[0], "", ""):
                raise RuntimeError("Failed to create flow from task start to first step.")

        for i in range(len(steps) - 1):
            current_step_id = created_steps_map.get(i)
            next_step_id = created_steps_map.get(i + 1)
            source_step_detail = steps[i]
            target_step_detail = steps[i + 1]
            condition = source_step_detail.get('flowCondition') or target_step_detail.get('stepName', '下一步')
            transition_prompt = source_step_detail.get('transitionPrompt', '')

            print(f"   Linking Step {i+1} ({source_step_detail.get('stepName')}) -> Step {i+2} ({target_step_detail.get('stepName')}) with Condition: '{condition}'")
            if not create_script_flow(train_task_id, current_step_id, next_step_id, condition, transition_prompt):
                raise RuntimeError(f"Failed to create flow: {source_step_detail.get('stepName')} -> {target_step_detail.get('stepName')}")

        if end_node_id and len(steps) > 0:
            last_idx = len(steps) - 1
            last_step_id = created_steps_map.get(last_idx)
            last_step_detail = steps[last_idx]
            condition = last_step_detail.get('flowCondition') or "训练结束"
            transition_prompt = last_step_detail.get('transitionPrompt', '')

            print(f"   Linking Step {len(steps)} ({last_step_detail.get('stepName')}) -> Task End ({end_node_id})")
            if not create_script_flow(train_task_id, last_step_id, end_node_id, condition, transition_prompt):
                raise RuntimeError(f"Failed to create flow: {last_step_detail.get('stepName')} -> Task End")

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
