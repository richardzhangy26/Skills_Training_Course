import os
import json
import requests
import re
from pathlib import Path
from dotenv import load_dotenv

def load_env_config():
    """
    加载.env配置文件
    """
    current_dir = Path(__file__).parent
    
    # 尝试加载多个位置的 .env
    env_paths = [
        current_dir / '.env',
        current_dir.parent / '.env',
        Path.cwd() / '.env'
    ]
    
    for path in env_paths:
        if path.exists():
            load_dotenv(path)
            print(f"✅ 已加载环境配置: {path}")
            return
            
    print("⚠️ 未找到 .env 文件，将仅使用系统环境变量")

def parse_markdown_to_steps(markdown_path):
    """
    解析 Markdown 文件提取步骤信息
    """
    with open(markdown_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 使用正则匹配每个阶段块
    # 假设每个阶段以 "### 阶段" 开头
    steps = []
    
    # 分割阶段，去掉第一个空项
    raw_steps = re.split(r'^### 阶段\d+: ', content, flags=re.MULTILINE)[1:]
    
    # 还需要获取阶段名称，splite会把分隔符去掉，所以我们用 finditer 或者 split 保留分隔符比较麻烦
    # 不如直接整体匹配
    
    # 正则策略：匹配整个块
    # 格式参考：
    # ### 阶段1: 情况概述
    # **Step ID**: ...
    # ...
    
    # 重新读取，使用更稳健的解析方式
    # 也可以按行读取状态机解析
    
    lines = content.split('\n')
    current_step = {}
    in_code_block = False
    current_code_block = []
    code_block_type = None # 'prologue' or 'llmPrompt' or 'unknown'
    
    for line in lines:
        line = line.strip()
        
        # 阶段标题
        if line.startswith('### 阶段'):
            # 保存上一个
            if current_step:
                steps.append(current_step)
            current_step = {}
            # 提取名称 "### 阶段1: 名称"
            if ':' in line:
                current_step['stepName'] = line.split(':', 1)[1].strip()
            continue
            
        # Step ID
        if line.startswith('**Step ID**:'):
            current_step['stepId'] = line.split(':', 1)[1].strip()
            continue
            
        # Trainer Name
        if line.startswith('**Trainer Name**:'):
            current_step['trainerName'] = line.split(':', 1)[1].strip()
            continue

        # Model ID
        if line.startswith('**Model ID**:'):
            current_step['modelId'] = line.split(':', 1)[1].strip()
            continue
            
        # 阶段描述
        if line.startswith('**阶段描述**:'):
            current_step['description'] = line.split(':', 1)[1].strip()
            continue
            
        # 互动轮次
        if line.startswith('**互动轮次**:'):
            rounds_str = line.split(':', 1)[1].strip()
            # 提取数字 "5轮" -> 5
            match = re.search(r'\d+', rounds_str)
            if match:
                current_step['interactiveRounds'] = int(match.group())
            continue
            
        # 开场白 - 开始/结束
        if line.startswith('**开场白**:'):
            code_block_type = 'prologue'
            continue
            
        # 提示词 - 开始/结束
        if line.startswith('**提示词**:'):
            code_block_type = 'llmPrompt'
            continue
            
        # 代码块处理
        if line.startswith('```'):
            if in_code_block:
                # 结束代码块
                content = '\n'.join(current_code_block).strip()
                if code_block_type == 'prologue':
                    current_step['prologue'] = content
                elif code_block_type == 'llmPrompt':
                    current_step['llmPrompt'] = content
                
                in_code_block = False
                current_code_block = []
                code_block_type = None
            else:
                # 开始代码块
                in_code_block = True
                current_code_block = []
            continue
            
        if in_code_block:
            current_code_block.append(line) # 这里 line 是 strip 过的，如果需要保留缩进可能要注意
            # 但通常 prompt 的缩进对于 markdown 显示是 strip 的，
            # 如果原始 markdown 是有缩进的，line.strip() 会破坏格式。
            # 应该尽量保留原始内容。
            # 为了简单起见，这里暂且 strip，如果需要通过 prompt.md 编辑，通常也不太会有复杂缩进。
            # 修正：应该使用原始行内容
            pass

    # 循环结束后，由 line.strip() 导致的缩进丢失问题修正：
    # 重新实现一个保留缩进的逻辑
    return parse_markdown_better(markdown_path)

def parse_markdown_better(markdown_path):
    with open(markdown_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    steps = []
    current_step = {}
    in_code_block = False
    current_code_block = []
    code_block_type = None 
    
    for line in lines:
        stripped = line.strip()
        
        # 阶段标题
        if stripped.startswith('### 阶段'):
            if current_step:
                steps.append(current_step)
            current_step = {}
            if ':' in stripped:
                current_step['stepName'] = stripped.split(':', 1)[1].strip()
            continue
            
        if stripped.startswith('**Step ID**:'):
            current_step['stepId'] = stripped.split(':', 1)[1].strip()
            continue
            
        if stripped.startswith('**Trainer Name**:'):
            current_step['trainerName'] = stripped.split(':', 1)[1].strip()
            continue

        if stripped.startswith('**Model ID**:'):
            current_step['modelId'] = stripped.split(':', 1)[1].strip()
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
            
        if stripped.startswith('**开场白**:'):
            code_block_type = 'prologue'
            continue
            
        if stripped.startswith('**提示词**:'):
            code_block_type = 'llmPrompt'
            continue
            
        if stripped.startswith('```'):
            if in_code_block:
                content = ''.join(current_code_block).strip() # join with newline is implicit if lines have \n
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

def update_nodes(markdown_file):
    load_env_config()
    
    # 1. 解析 Markdown
    print(f"📖 正在读取 Markdown 文件: {markdown_file}")
    steps = parse_markdown_better(markdown_file)
    print(f"✅ 解析到 {len(steps)} 个步骤")
    
    # 2. 读取 Payload 模板
    base_dir = Path(__file__).parent
    payload_template_path = base_dir / 'editScriptStep_payload.json'
    
    if not payload_template_path.exists():
        print("❌ 找不到 editScriptStep_payload.json 模板文件")
        return
        
    with open(payload_template_path, 'r', encoding='utf-8') as f:
        template_payload = json.load(f)
        
    # 3. 准备请求
    url = "https://cloudapi.polymas.com/teacher-course/abilityTrain/editScriptStep"
    authorization = os.getenv("AUTHORIZATION")
    cookie = os.getenv("COOKIE")
    
    if not authorization or not cookie:
        print("❌ 缺少 AUTHORIZATION 或 COOKIE 环境变量")
        return

    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": authorization,
        "Cookie": cookie,
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"
    }
    
    # 4. 遍历更新
    for step in steps:
        step_id = step.get('stepId')
        if not step_id:
            print(f"⚠️ 跳过无 Step ID 的步骤: {step.get('stepName')}")
            continue
            
        print(f"\n🔄 正在更新步骤: {step.get('stepName', '未命名')} (ID: {step_id})")
        
        # 构造 Payload
        # 深拷贝一份模板
        current_payload = json.loads(json.dumps(template_payload))
        
        # 更新核心字段
        current_payload['stepId'] = step_id
        
        # 更新 detail DTO
        detail = current_payload.get('stepDetailDTO', {})
        
        if 'stepName' in step:
            detail['stepName'] = step['stepName']
        if 'description' in step:
            detail['description'] = step['description']
        if 'interactiveRounds' in step:
            detail['interactiveRounds'] = step['interactiveRounds']
        if 'prologue' in step:
            detail['prologue'] = step['prologue']
        if 'llmPrompt' in step:
            detail['llmPrompt'] = step['llmPrompt']
        if 'trainerName' in step:
            detail['trainerName'] = step['trainerName']
        if 'modelId' in step and step['modelId']:
             detail['modelId'] = step['modelId']
            
        current_payload['stepDetailDTO'] = detail
        
        # 确保 trainTaskId 存在 (优先用环境变量，否则用模板里的)
        env_task_id = os.getenv("TASK_ID")
        env_course_id = os.getenv("COURSE_ID")
        if env_task_id:
            current_payload['trainTaskId'] = env_task_id
        if env_course_id:
            current_payload['courseId'] = env_course_id  
        # 发送请求
        try:
            response = requests.post(
                url,
                headers=headers,
                data=json.dumps(current_payload, ensure_ascii=False).encode("utf-8"),
                timeout=20
            )
            
            if response.status_code == 200:
                res_json = response.json()
                if res_json.get('code') == 200 or res_json.get('success') is True:
                     print("✅ 更新成功")
                else:
                     print(f"❌ 接口返回错误: {res_json}")
            else:
                print(f"❌ HTTP 错误: {response.status_code}")
                # print(response.text)
                
        except Exception as e:
            print(f"❌ 请求异常: {str(e)}")

if __name__ == "__main__":
    # 默认寻找当前目录下的 extracted_script.md 或者让用户输入
    import sys
    
    default_md = "/Users/richardzhang/工作/能力训练/script_step_f23840f9.md"
    target_md = default_md
    
    # 简单的命令行参数支持
    if len(sys.argv) > 1:
        target_md = Path(sys.argv[1])
        
    if not target_md:
        # 如果默认文件不存在，尝试寻找 script_step_*.md
        md_files = list(Path(__file__).parent.glob("script_step_*.md"))
        if md_files:
            # 取最新的一个
            md_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            target_md = md_files[0]
            print(f"ℹ️ 自动选择最新的 Markdown 文件: {target_md.name}")
        else:
            print(f"❌ 找不到 Markdown 文件: {target_md}")
            print("请先运行 test_check_node.py 导出 Markdown 文件，或手动指定文件路径")
            sys.exit(1)
            
    update_nodes(target_md)
