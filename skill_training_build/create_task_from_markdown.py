import os
import json
import requests
import re
import sys
from pathlib import Path
import uuid
from dotenv import load_dotenv
from nanoid import generate

# --- Configuration & Helpers ---

def load_env_config():
    """Load .env configuration."""
    current_dir = Path(__file__).parent
    env_paths = [
        current_dir / '.env',
        current_dir.parent / '.env',
        Path.cwd() / '.env'
    ]
    for path in env_paths:
        if path.exists():
            load_dotenv(path)
            print(f"✅ Loaded environment config: {path}")
            return
    print("⚠️ No .env file found, using system environment variables.")

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
    
    for line in lines:
        stripped = line.strip()
        
        # New Step Start
        if stripped.startswith('### 阶段'):
            if current_step:
                steps.append(current_step)
            current_step = {}
            if ':' in stripped:
                # "### Phase 1: Name" -> "Name"
                current_step['stepName'] = stripped.split(':', 1)[1].strip()
            continue
            
        # Fields
        if stripped.startswith('**Step ID**:'):
            # We ignore the Step ID from MD when creating NEW nodes, 
            # but we might verify if we are updating. 
            # For this script (CREATE), we usually generate NEW IDs.
            # But let's store it just in case.
            current_step['originalStepId'] = stripped.split(':', 1)[1].strip()
            continue
            
        if stripped.startswith('**虚拟训练官名字**:'):
            current_step['trainerName'] = normalize_md_value(stripped.split(':', 1)[1])
            continue

        if stripped.startswith('**模型**:'):
            current_step['modelId'] = normalize_md_value(stripped.split(':', 1)[1])
            continue

        if stripped.startswith('**声音**:'):
            current_step['agentId'] = normalize_md_value(stripped.split(':', 1)[1])
            continue
            
        if stripped.startswith('**形象**:'):
            current_step['avatarNid'] = normalize_md_value(stripped.split(':', 1)[1])
            continue
            
        if stripped.startswith('**阶段描述**:'):
            current_step['description'] = normalize_md_value(stripped.split(':', 1)[1])
            continue

        if stripped.startswith('**背景图**:'):
            current_step['backgroundImage'] = normalize_md_value(stripped.split(':', 1)[1])
            continue
            
        if stripped.startswith('**互动轮次**:'):
            rounds_str = stripped.split(':', 1)[1].strip()
            match = re.search(r'\d+', rounds_str)
            if match:
                current_step['interactiveRounds'] = int(match.group())
            continue
            
        # Code Blocks
        if stripped.startswith('**开场白**:'):
            code_block_type = 'prologue'
            continue
            
        if stripped.startswith('**提示词**:'):
            code_block_type = 'llmPrompt'
            continue

        if stripped.startswith('**transitionPrompt**:'):
            inline_value = normalize_md_value(stripped.split(':', 1)[1])
            if inline_value:
                current_step['transitionPrompt'] = inline_value
                code_block_type = None
            else:
                code_block_type = 'transitionPrompt'
            continue

        if stripped.startswith('**flowCondition**:'):
            current_step['flowCondition'] = normalize_md_value(stripped.split(':', 1)[1])
            continue
            
        if stripped.startswith('```'):
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

# --- API Interaction ---

def create_script_step(train_task_id, step_data, position):
    """Create a single script step."""
    url = "https://cloudapi.polymas.com/teacher-course/abilityTrain/createScriptStep"
    
    # Generate a new ID for the new node
    new_step_id = generate(size=21)
    
    payload = {
        "trainTaskId": train_task_id,
        "stepId": new_step_id,
        "stepDetailDTO": {
            "nodeType": "SCRIPT_NODE",
            "stepName": step_data.get('stepName', ''),
            "description": step_data.get('description', ''),
            "prologue": step_data.get('prologue', ''),
            "modelId": step_data.get('modelId') or os.getenv('DEFAULT_MODEL_ID') or 'Doubao-Seed-1.6-flash',
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
            "historyRecordNum":-1,
            "trainSubType": "ability"
        },
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

def create_script_flow(train_task_id, start_id, end_id, condition_text, transition_prompt=""):
    """Create a flow connection between two nodes."""
    url = "https://cloudapi.polymas.com/teacher-course/abilityTrain/createScriptStepFlow"
    
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
        "transitionHistoryNum": 0,
        "isDefault": 1,
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
    url = "https://cloudapi.polymas.com/teacher-course/abilityTrain/queryScriptStepList"
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

def query_script_step_flows(train_task_id):
    """Query existing script step flows."""
    url = "https://cloudapi.polymas.com/teacher-course/abilityTrain/queryScriptStepFlowList"
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
    url = "https://cloudapi.polymas.com/teacher-course/abilityTrain/delScriptStepFlow"
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
    url = "https://cloudapi.polymas.com/teacher-course/abilityTrain/delScriptStep"
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

def main():
    load_env_config()
    
    print("--- Training Task Generator ---")
    
    # 1. Train Task ID
    train_task_id = os.getenv("TASK_ID")
    print(f"---- Train Task ID: {train_task_id} ----")
    # Support passing as 2nd arg: python script.py <md> <task_id>
    if len(sys.argv) > 2:
        train_task_id = sys.argv[2]
    
    if not train_task_id:
        train_task_id = input("Please enter Train Task ID: ").strip()

    # 2. Markdown File
    target_md = None
    # Support passing as 1st arg: python script.py <md>
    if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
        candidate = Path(sys.argv[1])
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

    # Check for existing start/end nodes
    print(f"\n⏳ Fetching task info for Task ID: {train_task_id}...")
    step_list = query_script_steps(train_task_id)
    start_node_id, end_node_id = extract_start_end_ids(step_list)
    if not start_node_id or not end_node_id:
        print("⚠️ Could not find SCRIPT_START or SCRIPT_END nodes. Flow might be incomplete.")
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
                print("⚠️ 删除后未找到 SCRIPT_START 或 SCRIPT_END 节点。")
        else:
            print("ℹ️ 已保留现有节点，停止以避免重复创建。")
            return

    # 2. Parse
    print(f"📖 Parsing {target_md}...")
    steps = parse_markdown(target_md)
    if not steps:
        print("❌ No steps found in markdown.")
        return
    
    print(f"Found {len(steps)} steps.")

    # 3. Create Nodes
    # Map: Step Index (0-based) -> New Step ID
    created_steps_map = {} # index -> id
    
    x_start = 100
    y_start = 300
    x_gap = 400
    global_cover = None
    
    print("\n🚀 Creating Nodes...")
    for idx, step in enumerate(steps):
        background_image = step.get('backgroundImage')
        if background_image:
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

        # Calculate simplistic layout
        pos = {"x": x_start + (idx * x_gap), "y": y_start}
        
        new_id = create_script_step(train_task_id,step, pos)
        if new_id:
            created_steps_map[idx] = new_id
        else:
            print("❌ Stopping due to error.")
            return

    # 4. Create Flows
    print("\n🔗 Creating Flows (Sequential Match)...")
    
    # 4.1 Link START -> Step 1
    if start_node_id and len(steps) > 0:
        print(f"   Linking Task Start ({start_node_id}) -> Step 1 ({steps[0].get('stepName')})")
        # User requested no flow condition for start -> step1
        create_script_flow(train_task_id, start_node_id, created_steps_map[0], "", "")
    
    # 4.2 Link Step 1 -> Step 2 -> ... -> Step N
    for i in range(len(steps) - 1):
        current_step_id = created_steps_map.get(i)
        next_step_id = created_steps_map.get(i+1)
        
        source_step_detail = steps[i]
        target_step_detail = steps[i+1]
        
        # Condition from current step, fallback to target stepName
        condition = source_step_detail.get('flowCondition') or target_step_detail.get('stepName', '下一步')
        transition_prompt = source_step_detail.get('transitionPrompt', '')

        print(f"   Linking Step {i+1} ({source_step_detail.get('stepName')}) -> Step {i+2} ({target_step_detail.get('stepName')}) with Condition: '{condition}'")
        create_script_flow(train_task_id, current_step_id, next_step_id, condition, transition_prompt)

    # 4.3 Link Step N -> END
    if end_node_id and len(steps) > 0:
        last_idx = len(steps) - 1
        last_step_id = created_steps_map.get(last_idx)
        last_step_detail = steps[last_idx]
        # User requested '训练结束' for the last flow
        condition = last_step_detail.get('flowCondition') or "训练结束"
        transition_prompt = last_step_detail.get('transitionPrompt', '')
        
        print(f"   Linking Step {len(steps)} ({last_step_detail.get('stepName')}) -> Task End ({end_node_id})")
        create_script_flow(train_task_id, last_step_id, end_node_id, condition, transition_prompt)

    print("\n✅ Task Generation Complete.")

if __name__ == "__main__":
    main()
