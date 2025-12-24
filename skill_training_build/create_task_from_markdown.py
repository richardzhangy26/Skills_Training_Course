import os
import json
import requests
import re
import sys
from pathlib import Path
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
            current_step['trainerName'] = stripped.split(':', 1)[1].strip()
            continue

        if stripped.startswith('**模型**:'):
            current_step['modelId'] = stripped.split(':', 1)[1].strip()
            continue

        if stripped.startswith('**声音**:'):
            current_step['agentId'] = stripped.split(':', 1)[1].strip()
            continue
            
        if stripped.startswith('**形象**:'):
            current_step['avatarNid'] = stripped.split(':', 1)[1].strip()
            continue
            
        if stripped.startswith('**阶段描述**:'):
            current_step['description'] = stripped.split(':', 1)[1].strip()
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
            
        if stripped.startswith('```'):
            if in_code_block:
                content = ''.join(current_code_block).strip() 
                if code_block_type == 'prologue':
                    current_step['prologue'] = content
                elif code_block_type == 'llmPrompt':
                    current_step['llmPrompt'] = content
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
            "modelId": step_data.get('modelId', 'Doubao-Seed-1.6-flash'),
            "llmPrompt": step_data.get('llmPrompt', ''),
            "trainerName": step_data.get('trainerName', ''),
            "interactiveRounds": step_data.get('interactiveRounds', 0),
            # Default empty/preset values
            "scriptStepCover": {},
            "whiteBoardSwitch": 0,
            "agentId": step_data.get('agentId', 'Tg3LpKo28D'),
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

def create_script_flow(train_task_id, start_id, end_id, condition_text):
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
                            "text": ""
                        }
                    ]
                }
            ]
        },
        "transitionPrompt": "",
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


def get_existing_steps(train_task_id):
    """Query existing script steps to find START and END nodes."""
    url = "https://cloudapi.polymas.com/teacher-course/abilityTrain/queryScriptStepList"
    payload = {
        "trainTaskId": train_task_id,
        "trainSubType": "ability"
    }
    
    try:
        response = requests.post(url, headers=get_headers(), json=payload, timeout=20)
        res_json = response.json()
        
        start_node_id = None
        end_node_id = None
        
        if res_json.get('code') == 200 or res_json.get('success') is True:
            data_list = res_json.get('data', [])
            for item in data_list:
                node_type = item.get('stepDetailDTO', {}).get('nodeType')
                if node_type == 'SCRIPT_START':
                    start_node_id = item.get('stepId')
                elif node_type == 'SCRIPT_END':
                    end_node_id = item.get('stepId')
            return start_node_id, end_node_id
        else:
            print(f"❌ Failed to query existing steps: {res_json}")
            return None, None
    except Exception as e:
        print(f"❌ Error querying existing steps: {e}")
        return None, None

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
    start_node_id, end_node_id = get_existing_steps(train_task_id)
    if not start_node_id or not end_node_id:
        print("⚠️ Could not find SCRIPT_START or SCRIPT_END nodes. Flow might be incomplete.")
    else:
        print(f"✅ Found Start Node: {start_node_id}, End Node: {end_node_id}")

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
    
    print("\n🚀 Creating Nodes...")
    for idx, step in enumerate(steps):
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
        create_script_flow(train_task_id, start_node_id, created_steps_map[0], "")
    
    # 4.2 Link Step 1 -> Step 2 -> ... -> Step N
    for i in range(len(steps) - 1):
        current_step_id = created_steps_map.get(i)
        next_step_id = created_steps_map.get(i+1)
        
        source_step_detail = steps[i]
        target_step_detail = steps[i+1]
        
        # Condition is target stepName (e.g. Linking Step 1 -> Step 2 with Condition: 'Step 2 Name')
        condition = target_step_detail.get('stepName', '下一步')

        print(f"   Linking Step {i+1} ({source_step_detail.get('stepName')}) -> Step {i+2} ({target_step_detail.get('stepName')}) with Condition: '{condition}'")
        create_script_flow(train_task_id, current_step_id, next_step_id, condition)

    # 4.3 Link Step N -> END
    if end_node_id and len(steps) > 0:
        last_idx = len(steps) - 1
        last_step_id = created_steps_map.get(last_idx)
        last_step_detail = steps[last_idx]
        # User requested '训练结束' for the last flow
        condition = "训练结束"
        
        print(f"   Linking Step {len(steps)} ({last_step_detail.get('stepName')}) -> Task End ({end_node_id})")
        create_script_flow(train_task_id, last_step_id, end_node_id, condition)

    print("\n✅ Task Generation Complete.")

if __name__ == "__main__":
    main()
