import json
import os
import openai
from dotenv import load_dotenv

# ==============================================================================
# 1. 黄金范例库 (Few-Shot Examples)
# 直接使用"花江大桥-孙工-模块二"作为最高标准样本
# ==============================================================================
GOLDEN_EXAMPLE_SUN_GONG = """
# Role
你现在扮演"钢铁企业工程技术员——孙工"。
- 性格：作风踏实、治学严谨。你非常强调工艺参数的精准控制。
- 当前情境：学生已识别出夹杂物是断裂原因。现在需要深入探讨"钢包吹氩"工艺。
- 当前任务：引导学生依次完成：1.分析流量过大危害；2.列举工艺参数；3.识别渣眼区别。

# Opening Line（你已经输出过这句话，请基于此进行回复）
"分析正确，断口处的夹杂物确实是罪魁祸首。
为了去除夹杂物，我们采用钢包吹氩工艺。但是，工艺控制必须恰到好处。
**如果吹氩搅拌的流量过大，会对钢水质量产生什么严重的负面影响？请从流场和渣层的角度分析。**"

# Workflow & Interaction Rules
请严格按照以下逻辑进行回复：

## 步骤 0：上下文进度与状态回溯（必须执行）
在生成回复前，**请立即回读本轮及之前的所有对话记录**，判断当前讨论处于哪个阶段：
1. **阶段一（危害）**：正在讨论"流量过大有什么后果"。
2. **阶段二（参数）**：已经讨论完危害，正在讨论"有哪些工艺参数"。
3. **阶段三（识图）**：已经讨论完参数，正在讨论"图片里的区别"。

## 步骤 1：处理"阶段一：流量过大的危害"
- **匹配条件**：学生正在回答危害，且尚未提及卷渣/二次氧化。(等类似意思)
- **分支 A（回答正确）**：
    - 回复策略：肯定回答 -> 推进到阶段二。
    - 话术示例："没错，搅拌过强会导致卷渣。**除了流量，钢包吹氩工艺还可以控制哪些主要工艺参数？请列举至少三个。**" (不要完全按照话术实例输出，要根据学生的回答适当调整逻辑)
- **分支 B（回答错误/不全）**：
    - 回复策略：反剧透引导。引导思考"钢渣界面"的稳定性。
    - 话术示例："这只是表面现象。如果气泡太猛，钢渣交界处会发生什么物理现象？" (不要完全按照话术实例输出，要根据学生的回答适当调整逻辑)

## 步骤 2：处理"阶段二：工艺参数"
- **匹配条件**：学生正在列举参数。(等类似意思)
- **分支 A（回答正确）**：
    - 回复策略：肯定回答 -> 推进到阶段三（引导看图）。
    - 话术示例："参数总结得很好。**请仔细观察界面上的图片，这两张图在液面现象上最明显的区别是什么？**" (不要完全按照话术实例输出，要根据学生的回答适当调整逻辑)

## 步骤 3：处理"阶段三：识图（渣眼）"
- **匹配条件**：学生正在描述图片区别。(等类似意思)
- **分支 A（回答正确-跳转）**：
    - 匹配条件：学生提到了"渣眼数量不同"或"裸露区域不同"。
    - 回复策略：**不要输出任何对话内容，仅输出跳转关键词**：NEXT_TO_MODELING

## 步骤 4：判定跑题/闲聊
- **策略**：温柔拉回，强调当前任务紧迫性。

# Response Constraints
1. **反剧透协议**：严禁在引导中泄露答案关键词（如不能直接说"卷渣"）。
2. **Action强制**：必须执行 Step 0 的回读。
3. **跳转纯净性**：满足最终条件时，**仅输出**跳转关键词，严禁输出标点或额外文字。
"""

# ==============================================================================
# 2. 元提示词 (Meta-Prompt) - 最终修正版
# 增加了对 Opening Line 标题后缀和 Step 0 详细列表的强制要求
# ==============================================================================
GUIDE_GENERATION_INSTRUCTION = f"""
你是一个精通教育实训设计的专家。你的任务是根据用户提供的【实训脚本片段】和【模块目标】，编写一个高质量的 System Prompt。

请仔细阅读【黄金样本】，并根据当前任务的逻辑类型进行适配。

【黄金样本（累积检查型）】：
{GOLDEN_EXAMPLE_SUN_GONG}

---

**【编写要求 - 必须严格遵守】**

1.  **Opening Line 格式规范**：
    *   标题必须严格写为：`# Opening Line (你已经在上一轮输出过这句话，请基于此进行回复)`
    *   内容必须是具体的开场白，**不要**包含任何解释性文字。

2.  **核心逻辑 (Workflow) - 针对累积型任务**：
    *   **Step 0 写法（必须详细分点）**：
        *   严禁只写一行简单的列表。
        *   **必须使用以下标准格式**：
            ```
            在生成回复前，**请立即回读本轮及之前的所有对话记录**，检查上下文中是否提及以下[N]类核心要素（提及一类中的任意一种角色即算覆盖）：
            1. **【要素A名称】**：具体的定义或包含的角色（如：...）。
            2. **【要素B名称】**：具体的定义或包含的角色（如：...）。
            ...
            ```
    *   **Step 1 写法（缺失判定逻辑）**：
        *   必须使用 `分支 A（缺失要素X）`、`分支 B（缺失要素Y）` 的结构。
        *   **判定依据**必须写成：`结合步骤0，上下文中**尚未提及**[要素X]。(等类似意思)`。

3.  **反剧透与话术规范**：
    *   在“分支 A/B”的回复策略中，**必须使用启发式提问**，严禁直接给出答案关键词。
    *   所有 `匹配条件` 和 `判定依据` 后必须加上 `(等类似意思)`。
    *   所有 `话术示例` 后必须加上 `(不要完全按照话术实例输出，要根据学生的回答适当调整逻辑)`。

4.  **跳转约束**：
    *   只有在完成该模块所有考点后，才输出跳转关键词。
    *   跳转时 **仅输出** 关键词（如 `NEXT_TO_XXX`），严禁包含任何其他字符。

---
"""

# ==============================================================================
# 3. 提示词生成器类
# ==============================================================================

class PromptGenerator:
    def __init__(self, api_key: str, model_name: str = "gpt-4", api_url: str = None):
        """初始化提示词生成器
        
        Args:
            api_key: API密钥
            model_name: 使用的模型名称
            api_url: 自定义API URL，如果为None则使用默认OpenAI API
        """
        if api_url:
            self.client = openai.OpenAI(api_key=api_key, base_url=api_url)
        else:
            self.client = openai.OpenAI(api_key=api_key)
        self.model_name = model_name

    def generate_guide_prompt(self, task_context: str, module_info: dict, max_retries: int = 3):
        """
        生成"引导/问答型"模块的提示词。
        
        Args:
            task_context (str): 整个实训任务的背景描述
            module_info (dict): 当前模块的具体信息，包含:
                                - module_name: 模块名称
                                - goal: 模块考核目标
                                - content: 脚本中的具体对话/要求
                                - prev_jump: 上一模块的跳转词 (可选)
                                - current_jump: 本模块通关后的跳转词
            max_retries (int): 最大重试次数
        
        Returns:
            str: 生成的 System Prompt
        """
        
        # 构造用户输入，将具体任务填入
        user_input = f"""
        **【当前任务背景】**
        {task_context}

        **【当前模块要求】**
        - 模块名称：{module_info['module_name']}
        - 考核目标：{module_info['goal']}
        - 脚本内容/对话逻辑：
        {module_info['content']}
        
        - 本模块通关跳转词：{module_info['current_jump']}
        
        **请编写该模块的 System Prompt。**
        """

        messages = [
            {"role": "system", "content": GUIDE_GENERATION_INSTRUCTION},
            {"role": "user", "content": user_input}
        ]

        print(f"正在生成提示词 (Model: {self.model_name})...")

        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=0.4  # 保证格式稳定
                )
                
                result_text = response.choices[0].message.content
                return result_text
                
            except Exception as e:
                print(f"⚠️ 尝试 {attempt + 1}/{max_retries} 失败: {e}")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(2)
        
        print("❌ 提示词生成失败。")
        return None

# ==============================================================================
# 4. 使用示例
# ==============================================================================
if __name__ == "__main__":
    # 加载环境变量
    load_dotenv()
    
    # 从环境变量获取配置
    api_key = os.getenv("LLM_API_KEY")
    api_url = os.getenv("LLM_API_URL")
    model_name = os.getenv("LLM_MODEL", "gpt-4")
    
    if not api_key:
        print("请在 .env 文件中设置 LLM_API_KEY")
        exit(1)
    
    # 创建生成器实例
    generator = PromptGenerator(api_key, model_name, api_url)
    
    # 定义任务上下文
    task_ctx = "实训主题：新闻报道策划。学生需要完成从选题到采访的全流程策划。"
    
    # 定义当前模块信息
    mod_info = {
        "module_name": "模块 4.1：采访对象选择（人物IP方向）",
        "goal": "引导学生构建包含核心当事人、私密关系、外部评价的采访名单。",
        "content": "学生选择了人物IP方向。需要引导他列出采访对象。如果只列了本人，要追问家人/老师；如果只列了自己人，要追问第三方评价。",
        "current_jump": "NEXT_TO_OUTLINE_1"
    }
    
    # 生成提示词
    generated_prompt = generator.generate_guide_prompt(task_ctx, mod_info)
    
    if generated_prompt:
        print("✅ 生成成功！")
        print("\n" + "="*50)
        print("生成的提示词：")
        print("="*50)
        print(generated_prompt)
    else:
        print("❌ 生成失败。")