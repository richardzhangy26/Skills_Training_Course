import os
import time
import re
import openai
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(
    filename='pipeline.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    encoding='utf-8'
)

def log_print(msg):
    print(msg)
    logging.info(msg)

# 加载环境变量
load_dotenv()

# 初始化 OpenAI 客户端
api_key = os.getenv("LLM_API_KEY")
api_url = os.getenv("LLM_API_URL")
model_name = os.getenv("LLM_MODEL", "gpt-4")

if api_url:
    client = openai.OpenAI(api_key=api_key, base_url=api_url)
else:
    client = openai.OpenAI(api_key=api_key)

def call_llm_api(system_prompt: str, user_prompt: str, temperature: float = 1, max_retries: int = 5) -> str:
    """调用 LLM API 返回文本结果，带改进的重试机制"""
    import time

    for attempt in range(max_retries):
        try:
            log_print(f"DEBUG: Calling LLM ({model_name}) | System len: {len(system_prompt)} | User len: {len(user_prompt)} | Attempt {attempt + 1}/{max_retries}")
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                timeout=300  # 增加到 300 秒
            )
            return response.choices[0].message.content
        except Exception as e:
            error_msg = str(e)
            log_print(f"LLM API Error (Attempt {attempt + 1}/{max_retries}): {error_msg}")

            # 如果是最后一次尝试，返回空字符串
            if attempt == max_retries - 1:
                log_print(f"❌ All {max_retries} attempts failed for this request")
                return ""

            # 检查是否是可重试的错误
            if "502" in error_msg or "503" in error_msg or "504" in error_msg or "timeout" in error_msg.lower():
                # 指数退避 + 随机抖动，避免惊群效应
                wait_time = (2 ** attempt) * 5 + (attempt * 5)  # 5s, 15s, 35s, 75s, 155s
                log_print(f"⏳ Server error detected, retrying in {wait_time} seconds (exponential backoff)...")
                time.sleep(wait_time)
            else:
                # 不可重试的错误（如认证错误），直接返回
                log_print(f"❌ Non-retryable error, giving up")
                return ""

def process_step_1(input_file: str, prompt_file: str, output_file: str):
    """
    第一步：读取 input_task.txt 和 shixiaoxun_prompt.md，生成中间任务文档。
    """
    if not os.path.exists(input_file) or not os.path.exists(prompt_file):
        log_print("❌ Error: Input or prompt file not found for Step 1.")
        return

    with open(input_file, "r", encoding="utf-8") as f:
        task_content = f.read()
    with open(prompt_file, "r", encoding="utf-8") as f:
        system_prompt = f.read()
        
    user_prompt = f"请根据以下任务书内容，生成情景化实训任务书。\n\n【任务书内容】:\n{task_content}"
    
    log_print("🚀 Starting Step 1: generating task document...")
    start_time = time.time()
    result = call_llm_api(system_prompt, user_prompt, temperature=0.7)
    
    if result:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(result)
        log_print(f"✨ Step 1 completed in {time.time()-start_time:.1f}s -> {output_file}")

# ==========================================
# 模块类型 → Skill 文件 映射表
# 说明：key 是模块标签（会做模糊匹配），value 是对应的 skill 文件路径
# ==========================================
SKILL_MAP = {
    "循序询问型": "skill_guoguan.md",    # 循序过关型，追问引导
    "模拟人物型": "skill_moni.md",       # 被动等待，角色扮演
    "总结型":    "skill_zongjie.md",    # 总结复盘型
}

def load_skill(tag: str, skill_map: dict) -> str:
    """
    根据模块标签模糊匹配 skill_map，返回对应 skill 文件的文本内容。
    如果找不到匹配项，回退到第一个可用的 skill 文件。
    """
    for key, filepath in skill_map.items():
        if key in tag:
            if os.path.exists(filepath):
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                # 检测是否是占位符（未正式填入 skill）
                if "待填入" in content:
                    log_print(f"  ⚠️  Skill file '{filepath}' is a placeholder. Please fill in the real skill template!")
                log_print(f"  📖 Loaded skill: '{filepath}' for tag '{tag}'")
                return content
            else:
                log_print(f"  ❌ Skill file '{filepath}' not found for tag '{tag}'.")
    
    # 回退：使用第一个存在的 skill 文件
    for key, filepath in skill_map.items():
        if os.path.exists(filepath):
            log_print(f"  ⚠️  No matching skill for tag '{tag}', falling back to '{filepath}'.")
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read()
    
    log_print(f"  ❌ No skill files found at all!")
    return ""

def process_step_2(step1_output_file: str, skill_map: dict, output_dir: str):
    """
    第二步：解析 Step 1 的输出模块，根据每个模块的标签选择对应的 Skill 文件，
    然后逐个调用 LLM 生成对应的 Prompt 文件。
    """
    if not os.path.exists(step1_output_file):
        log_print(f"❌ Error: {step1_output_file} not found. Run step 1 first.")
        return
        
    with open(step1_output_file, "r", encoding="utf-8") as f:
        step1_content = f.read()

    # 1. 解析模块（根据 "### 模块" 分割，并过滤掉空块）
    parts = re.split(r'(?=### 模块)', step1_content)
    modules = [p.strip() for p in parts if p.strip().startswith('### 模块')]
    
    if not modules:
        log_print("⚠️ No modules found in output_step1.md.")
        return
        
    log_print(f"🚀 Starting Step 2: Found {len(modules)} modules. Generating prompts one by one...")
    os.makedirs(output_dir, exist_ok=True)
    
    # 2. 构造简练的元提示词 (System Prompt)
    meta_system_prompt = """你是提示词模板融合专家。你的任务是：
1. 理解【当前模块信息】中的具体内容和目标，请你尤其注意哪些是学生需要回答的内容，哪些是直接我们会提供给学生的信息
2. 参考【专属技能模板】的结构和逻辑
3. 将模块内容精确融入模板框架中

**核心要求**：
- 输出仅为完整的提示词文本，不需要任何前缀或解释

【专属技能模板】:
=========================
{skill_template}
=========================
"""

    # 2. 逐个处理模块
    for i, module_text in enumerate(modules):
        module_name_match = re.search(r'### 模块(.*?)[：:](.*?)\s*<标签[：:](.*?)>', module_text)
        if module_name_match:
            mod_title = module_name_match.group(2).strip()
            mod_tag = module_name_match.group(3).strip()
        else:
            mod_title = f"Module_{i+1}"
            mod_tag = "Unknown"
            
        log_print(f"\n⏳ Processing Module {i+1}/{len(modules)}: {mod_title} [{mod_tag}]...")
        
        # ✨ 核心：根据模块标签动态加载对应的 Skill
        skill_template = load_skill(mod_tag, skill_map)
        if not skill_template:
            log_print(f"  ❌ Skipping module '{mod_title}' due to missing skill file.")
            continue
        
        # 构造元提示词（将动态 skill_template 注入）
        meta_system_prompt_for_module = meta_system_prompt.format(skill_template=skill_template)
        
        user_prompt = f"请为以下模块生成其专属的聊天机器人提示词（Markdown格式）：\n\n【当前模块信息】\n{module_text}"
        
        start_time = time.time()
        result = call_llm_api(meta_system_prompt_for_module, user_prompt, temperature=0.3)
        
        if result:
            safe_title = re.sub(r'[\\/:*?"<>|]', '_', mod_title)
            safe_title = safe_title[:20] if len(safe_title) > 20 else safe_title
            out_filename = os.path.join(output_dir, f"prompt_module_{i+1}_{safe_title}.md")
            with open(out_filename, "w", encoding="utf-8") as f:
                f.write(result)
            log_print(f"✅ Generated prompt for '{mod_title}' in {time.time()-start_time:.1f}s -> {out_filename}")
        else:
            log_print(f"❌ Failed to generate prompt for module: {mod_title}")
        
        # 模块间延迟，避免快速连续请求触发速率限制
        if i < len(modules) - 1:
            delay = 3  # 每个模块间隔 3 秒
            log_print(f"  ⏳ Waiting {delay}s before next module...")
            time.sleep(delay)

if __name__ == "__main__":
    INPUT_FILE = "input_task.txt"
    PROMPT_FILE = "shixiaoxun_prompt.md"
    OUTPUT_STEP1 = "output_step1.md"
    OUTPUT_DIR = "generated_prompts"
    
    # ================= 运行开关 =================
    # 你可以直接在这里修改 True / False 来单独控制运行哪一步
    RUN_STEP_1 = False  # 是否运行第一步（将初始任务书转为模块切分）
    RUN_STEP_2 = True   # 是否运行第二步（读取切分好的模块，逐个生成提示词）
    # ============================================
    
    if RUN_STEP_1:
        process_step_1(INPUT_FILE, PROMPT_FILE, OUTPUT_STEP1)
        
    if RUN_STEP_2:
        process_step_2(OUTPUT_STEP1, SKILL_MAP, OUTPUT_DIR)
