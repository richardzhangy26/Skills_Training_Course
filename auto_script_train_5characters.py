import asyncio
import requests
import json
import time
import os
from datetime import datetime
from pathlib import Path
from openai import OpenAI
from workflow_tester_base import WorkflowTesterBase

class WorkflowTester(WorkflowTesterBase):
    DEFAULT_PROFILE_KEY = "S2"
    PROFILE_LABEL_FIELD_NAME = "学生角色"
    PROFILE_SELECT_TITLE = "学生角色"
    DEFAULT_STUDENT_PROFILES = {
        "S1": {
            "label": "S1 沉默寡言的学生",
            "description": "内向不主动表达，只给最简短的回应，常用词重复。",
            "speech_habit": "常说“嗯”“好”“不知道”，回答多为 1-2 句甚至只有词语。",
            "style": "语气克制、信息量少，除非被追问不会展开。",
            "test_goal": "测试 AI 是否能主动引导、追问，避免对话中断。",
        },
        "S2": {
            "label": "S2 话多跑题的学生",
            "description": "兴奋健谈，喜欢分享各种细节，常把话题带离当前问题。",
            "speech_habit": "回答冗长跳跃，经常夹杂与问题弱相关的经历或感受。",
            "style": "语速快、情绪高涨，想到什么就说什么，很难保持中心。",
            "test_goal": "测试 AI 的话题收束能力和耐心引导能力。",
        },
        "S3": {
            "label": "S3 高需求的完美主义者",
            "description": "对答案极度挑剔，持续追问细节并要求更多示例。",
            "speech_habit": "习惯反复追问“还有吗”“能具体点吗”，不断强调标准要更高。",
            "style": "语气苛求且严谨，总在寻找不足之处。",
            "test_goal": "测试 AI 的深度解答能力和面对高标准的应对策略。",
        },
        "S4": {
            "label": "S4 逻辑挑刺型学生",
            "description": "喜欢找 AI 的矛盾或漏洞，专注于质疑和反驳。",
            "speech_habit": "习惯先指出不合理点，再要求给解释，甚至抛出反例。",
            "style": "语气犀利爱辩论，动不动就说“这说不通”。",
            "test_goal": "测试 AI 的逻辑一致性与抗质疑能力。"
        },
        "S5": {
            "label": "S5 情绪化学生",
            "description": "情绪波动大，容易沮丧或生气，语言夹杂情绪词汇。",
            "speech_habit": "会突然表达“我快崩溃了”“太让人失望”等感受。",
            "style": "语气带情绪色彩，时而激动时而低落。",
            "test_goal": "测试 AI 的情绪安抚与正向引导能力。"
        }
    }

    def __init__(self, base_url=None):
        super().__init__(base_url)

        # 加载学生性格配置
        self.student_profiles = self._load_student_profiles()

        # 模型配置
        self.model_type = os.getenv("MODEL_TYPE", "doubao_post")  # doubao_sdk, doubao_post, deepseek_sdk
        self.doubao_client = None
        self.deepseek_client = None
        self.deepseek_client = None
        self.doubao_model = os.getenv("DOUBAO_MODEL", "doubao-seed-1-6-251015")
        self.deepseek_model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

        # POST 调用配置
        self.llm_api_url = os.getenv(
            "LLM_API_URL",
            "http://llm-service.polymas.com/api/openai/v1/chat/completions",
        )
        self.llm_api_key = os.getenv("LLM_API_KEY", "")
        self.llm_model = os.getenv("LLM_MODEL", "Doubao-1.5-pro-32k")
        self.llm_service_code = os.getenv("LLM_SERVICE_CODE", "SI_Ability")
        self.use_post_api = os.getenv("USE_POST_API", "false").lower() == "true"

        self._initialize_llm_client()

    def _load_student_profiles(self):
        """加载学生性格配置文件"""
        config_paths = [
            Path.cwd() / "student_profiles.custom.json",
            self.base_path / "student_profiles.json"
        ]

        for config_path in config_paths:
            if config_path.exists():
                try:
                    return self._load_config_file(config_path)
                except Exception as e:
                    print(f"⚠️  警告: 无法加载配置文件 {config_path}: {str(e)}")

        # 使用内置默认配置
        print("⚠️  未找到配置文件，使用内置默认配置")
        return self.DEFAULT_STUDENT_PROFILES

    def _load_config_file(self, config_path):
        """加载并验证配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # 验证配置文件结构
            if "profiles" not in config:
                raise ValueError("配置文件缺少 'profiles' 字段")

            profiles = config["profiles"]
            validated_profiles = {}

            # 验证并合并每个性格配置
            for profile_key in ["S1", "S2", "S3", "S4", "S5"]:
                if profile_key in profiles:
                    user_profile = profiles[profile_key]
                    default_profile = self.DEFAULT_STUDENT_PROFILES.get(profile_key, {})

                    # 合并配置：用户配置覆盖默认配置
                    merged_profile = default_profile.copy()
                    merged_profile.update(user_profile)

                    # 确保必填字段存在
                    required_fields = ["label", "description", "speech_habit", "style", "test_goal"]
                    for field in required_fields:
                        if field not in merged_profile:
                            merged_profile[field] = default_profile.get(field, "")

                    # 添加 enabled 字段（默认为 true）
                    if "enabled" not in merged_profile:
                        merged_profile["enabled"] = True

                    validated_profiles[profile_key] = merged_profile
                else:
                    # 使用默认配置
                    validated_profiles[profile_key] = self.DEFAULT_STUDENT_PROFILES[profile_key]

            print(f"✅ 已加载学生性格配置: {config_path}")
            return validated_profiles

        except json.JSONDecodeError as e:
            raise ValueError(f"配置文件格式错误: {str(e)}")
        except Exception as e:
            raise ValueError(f"加载配置文件失败: {str(e)}")

    def _initialize_llm_client(self):
        """初始化 LLM 客户端"""
        print(f"🔧 模型类型: {self.model_type}")

        if self.model_type == "doubao_post":
            print(f"   - 使用 Doubao POST API 调用模式")
            print(f"   - API URL: {self.llm_api_url}")
            print(f"   - Model: {self.llm_model}")
            print(f"   - Service Code: {self.llm_service_code}")
            if not self.llm_api_key:
                print("⚠️  警告: LLM_API_KEY 未设置")

        elif self.model_type == "doubao_sdk":
            api_key = os.getenv("ARK_API_KEY")
            base_url = os.getenv("ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")

            if api_key:
                try:
                    self.doubao_client = OpenAI(api_key=api_key, base_url=base_url)
                    print(f"   - 使用 Doubao OpenAI SDK 调用模式")
                    print(f"   - Model: {self.doubao_model}")
                except Exception as e:
                    print(f"⚠️  警告: 初始化 Doubao 客户端失败: {str(e)}")
            else:
                print("⚠️  警告: ARK_API_KEY 未设置")

        elif self.model_type == "deepseek_sdk":
            api_key = os.getenv("DEEPSEEK_API_KEY")

            if api_key:
                try:
                    self.deepseek_client = OpenAI(
                        api_key=api_key,
                        base_url="https://api.deepseek.com"
                    )
                    print(f"   - 使用 DeepSeek OpenAI SDK 调用模式")
                    print(f"   - Model: {self.deepseek_model}")
                except Exception as e:
                    print(f"⚠️  警告: 初始化 DeepSeek 客户端失败: {str(e)}")
            else:
                print("⚠️  警告: DEEPSEEK_API_KEY 未设置")
        else:
            print(f"⚠️  警告: 未知的模型类型: {self.model_type}")

    def _call_doubao_post(self, messages, temperature=0.85, max_tokens=1000):
        """使用 HTTP POST 方式调用 Doubao API"""
        headers = {
            "Content-Type": "application/json",
            "service-code": self.llm_service_code,
        }

        if self.llm_api_key:
            headers["api-key"] = self.llm_api_key

        payload = {
            "model": self.llm_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": 0.95,
            "frequency_penalty": 0.3,
            "presence_penalty": 0.2
        }

        try:
            response = requests.post(
                self.llm_api_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()
        except requests.exceptions.RequestException as e:
            print(f"❌ HTTP POST 调用失败: {str(e)}")
            return None
        except (KeyError, IndexError) as e:
            print(f"❌ 解析响应失败: {str(e)}")
            return None

    def _get_current_model_name(self):
        """获取当前模型的显示名称"""
        if self.model_type == "doubao_post":
            return self.llm_model
        elif self.model_type == "doubao_sdk":
            return self.doubao_model
        elif self.model_type == "deepseek_sdk":
            return self.deepseek_model
        return "unknown"

    def _clone_for_parallel(self):
        """复制当前实例的上下文供并发运行使用"""
        clone = WorkflowTester(self.base_url)
        clone.headers = self.headers.copy()
        clone.model_type = self.model_type
        clone.doubao_model = self.doubao_model
        clone.deepseek_model = self.deepseek_model
        clone.dialogue_samples_content = self.dialogue_samples_content
        clone.knowledge_base_content = self.knowledge_base_content
        clone.log_context_path = self.log_context_path
        # 复制 API 配置
        clone.llm_api_url = self.llm_api_url
        clone.llm_api_key = self.llm_api_key
        clone.llm_model = self.llm_model
        clone.llm_service_code = self.llm_service_code
        clone.conversation_history = []  # 每个克隆实例独立的对话历史
        clone.step_name_mapping = self.step_name_mapping.copy()  # 复制步骤名称映射
        # 重新初始化客户端
        clone._initialize_llm_client()
        return clone

    def _run_profile_workflow(self, task_id, profile_key):
        """在线程中执行单个学生角色的 LLM 流程"""
        runner = self._clone_for_parallel()
        runner.set_student_profile(profile_key)
        runner.run_with_llm(task_id)

    async def run_profiles_concurrently(self, task_id, profile_keys):
        """异步并发运行多个学生角色"""
        if not profile_keys:
            print("⚠️  未选择学生角色，无法并发运行。")
            return

        print(f"\n🚀 正在并发运行 {len(profile_keys)} 个学生角色...")
        tasks = [
            asyncio.to_thread(self._run_profile_workflow, task_id, profile_key)
            for profile_key in profile_keys
        ]
        await asyncio.gather(*tasks)
        print("\n✅ 所有选定的学生角色已运行完成。")

    def generate_answer_with_llm(self, question):
        """使用 LLM 模型生成回答"""
        # 检查是否有可用的调用方式
        if self.model_type == "doubao_sdk" and not self.doubao_client:
            print("❌ Doubao 客户端未初始化")
            return None
        elif self.model_type == "deepseek_sdk" and not self.deepseek_client:
            print("❌ DeepSeek 客户端未初始化")
            return None
        elif self.model_type == "doubao_post" and not self.llm_api_url:
            print("❌ POST API URL 未配置")
            return None

        try:
            profile_info = self._get_student_profile_info()
            system_prompt = (
                "你是一名能力训练助手，需要模拟学生角色进行回答。"
                "注意：性格特点应该自然融入对话，而非生硬套用，要保持回答的真实性和多样性。"
                "如果有角色示例对话，请优先引用或改写。"
            )

            sections = [
                "## 角色设定",
                f"学生角色: {profile_info['label']}",
                f"角色特征: {profile_info['description']}",
            ]

            if profile_info.get("speech_habit"):
                sections.append(f"说话习惯: {profile_info['speech_habit']}")

            sections.append(f"表达风格: {profile_info['style']}")

            if profile_info.get("test_goal"):
                sections.append(f"测试目的: {profile_info['test_goal']}")

            sections.append("")

            # 添加问题类型识别
            sections.extend([
                "## 问题类型识别（优先级最高）",
                "如果当前问题属于以下类型，请优先直接回答，不需要强制体现性格特点：",
                "1. **确认式问题**: 如'你准备好了吗？请回复是或否'、'确认的话请回复是'",
                "   → 直接回答'是'、'好的'、'确认'等",
                "2. **选择式问题**: 如'你选择A还是B？'、'请选择1/2/3'",
                "   → 直接说出选项，如'我选择A'、'选1'",
                "3. **角色确认问题**: 如'你是学生还是老师？'",
                "   → 直接回答角色，如'学生'",
                "",
                "**判断标准**: 如果问题中包含'请回复'、'请选择'、'是或否'、'A/B/C'等明确指示，则为封闭式问题。",
                ""
            ])

            if self.dialogue_samples_content:
                sections.extend([
                    "## 角色示例对话 (如有匹配请优先引用或改写，优先级最高)",
                    self.dialogue_samples_content,
                    "",
                ])

            if self.knowledge_base_content:
                sections.extend([
                    "## 参考知识库 (可结合使用)",
                    self.knowledge_base_content,
                    "",
                ])

            # 添加对话历史
            if self.conversation_history:
                sections.extend([
                    "## 对话历史（按时间顺序）",
                ])
                for i, turn in enumerate(self.conversation_history, 1):
                    sections.append(f"第{i}轮:")
                    sections.append(f"  AI提问: {turn['ai']}")
                    sections.append(f"  学生回答: {turn['student']}")
                sections.append("")

            sections.extend([
                "## 当前问题",
                question,
                "",
                "## 输出要求（按优先级执行）",
                "**优先级1**: 优先输出角色示例对话中的内容",
                "**优先级2**: 如果是开放式问题，再适度融入学生性格特点，但要注意：",
                "   - 性格特点应该自然体现，不要生硬套用",
                "   - 避免每次都使用相同的话术（如不要总说'这说不通'、'不知道'等）",
                "   - 保持回答的多样性和真实性，可以偶尔正常回答",
                "**优先级3**: 如果示例对话中有高度相关的回答，可以参考但需变化表达方式。",
                "**格式要求**: 仅返回学生回答内容，不要额外解释，控制在50字以内。",
                ""
            ])

            user_message = "\n".join(sections)

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]

            # 根据配置选择调用方式
            if self.model_type == "doubao_post":
                print("🔄 使用 Doubao POST API 调用...")
                answer = self._call_doubao_post(messages, temperature=0.85, max_tokens=1000)
            elif self.model_type == "doubao_sdk":
                print("🔄 使用 Doubao OpenAI SDK 调用...")
                response = self.doubao_client.chat.completions.create(
                    model=self.doubao_model,
                    messages=messages,
                    temperature=0.85,  # 提高温度增加随机性和多样性
                    top_p=0.95,
                    frequency_penalty=0.3,  # 降低重复性
                    presence_penalty=0.2    # 鼓励使用新词汇
                )
                answer = response.choices[0].message.content
            elif self.model_type == "deepseek_sdk":
                print("🔄 使用 DeepSeek OpenAI SDK 调用...")
                response = self.deepseek_client.chat.completions.create(
                    model=self.deepseek_model,
                    messages=messages,
                    temperature=0.85,  # 提高温度增加随机性和多样性
                    top_p=0.95,
                    frequency_penalty=0.3,  # 降低重复性
                    presence_penalty=0.2    # 鼓励使用新词汇
                )
                answer = response.choices[0].message.content
            else:
                print(f"❌ 未知的模型类型: {self.model_type}")
                return None

            return answer
        except Exception as e:
            print(f"❌ 调用 {self.model_type} 模型失败: {str(e)}")
            print(f"❌ 调用 {self.model_type} 模型失败: {str(e)}")
            return None

    def run_with_llm(self, task_id):
        """
        使用 LLM 模型自动生成回答并运行工作流
        """
        # 检查客户端初始化
        if self.model_type == "doubao_sdk" and not self.doubao_client:
            print("\n❌ Doubao 客户端未初始化，请检查 ARK_API_KEY 环境变量")
            return
        elif self.model_type == "deepseek_sdk" and not self.deepseek_client:
            print("\n❌ DeepSeek 客户端未初始化，请检查 DEEPSEEK_API_KEY 环境变量")
            return
        elif self.model_type == "doubao_post" and not self.llm_api_url:
            print("\n❌ POST API URL 未配置")
            return

        if not self.student_profile_key:
            default_label = self.student_profiles[self.DEFAULT_PROFILE_KEY]["label"]
            print(f"\n⚠️  未指定学生角色，默认使用 '{default_label}'。")
            self.student_profile_key = self.DEFAULT_PROFILE_KEY

        try:
            # 启动工作流
            self.start_workflow(task_id)

            round_num = 1

            # 循环对话
            while True:
                # 检查是否还有下一步
                if self.current_step_id is None:
                    print("\n✅ 工作流完成！没有更多步骤了。")
                    break

                # 安全检查：防止无限循环
                if round_num > 50:
                    print(f"\n⚠️  警告：已达到最大对话轮数（{round_num}轮），自动退出防止无限循环")
                    break

                print("\n" + "="*60)
                print(f"🤖 第 {round_num} 轮对话（{self.model_type} 自主回答）")
                print("="*60)

                # 使用 LLM 生成回答
                print(f"\n🔄 正在生成回答...")
                generated_answer = self.generate_answer_with_llm(self.question_text)

                if not generated_answer:
                    print("❌ 无法生成回答，跳过此轮")
                    break

                print(f"\n🤖 {self.model_type} 生成的回答: {generated_answer}")

                # 保存当前轮对话到历史
                self.conversation_history.append({
                    "ai": self.question_text,
                    "student": generated_answer
                })

                # 发送生成的回答
                result = self.chat(generated_answer)

                # 检查返回结果，如果 text 为 null 且 nextStepId 为 null，代表输出结束
                # 检查返回结果，如果 text 为 null 且 nextStepId 为 null，代表输出结束
                data = result.get("data") or {}
                if data.get("text") is None and data.get("nextStepId") is None:
                    print("\n✅ 工作流完成！")
                    break

                round_num += 1
                time.sleep(1)  # 稍微延迟，避免请求过快

            self._finalize_workflow()

            print("\n" + "="*60)
            print("🎉 工作流测试结束")
            print("="*60)

        except Exception as e:
            print(f"\n❌ 错误: {str(e)}")
            import traceback
            traceback.print_exc()


# 主程序
if __name__ == "__main__":
    print("="*60)
    print("📋 对话工作流自动化测试工具 v2.0")
    print("="*60)
    
    # 创建测试器
    tester = WorkflowTester()
    
    # 测试连接
    if not tester.test_connection():
        print("\n❌ 连接测试失败，请先解决问题")
        exit(1)
    
    # 获取 task_id
    task_id = os.getenv("TASK_ID")
    if not task_id:
        task_id = input("\n请输入 task_id: ").strip()
        if not task_id:
            print("❌ task_id 不能为空")
            exit(1)
    
    print(f"\n使用 task_id: {task_id}")

    # 选择日志格式
    tester.log_format = tester._get_log_format_preference()

    # 选择运行模式
    print("\n请选择运行方式：")
    print("1. 交互式运行（推荐）")
    print("2. 自动化运行（需要预设答案）")
    print("3. 大模型自主选择回答（Doubao 自动生成答案）")

    choice = input("\n请输入选项 (1/2/3): ").strip()

    if choice == "1":
        tester.run_interactive(task_id)

    elif choice == "2":
        print("\n提示: 请先在代码中配置 user_answers 列表")
        user_answers = [
            "这是第一个答案",
            "这是第二个答案",
            "这是第三个答案"
        ]
        tester.run_auto(task_id, user_answers)

    elif choice == "3":
        print("\n🤖 使用 LLM 模型自主回答模式")

        # 模型选择
        print("\n请选择 LLM 模型：")
        print("1. Doubao (OpenAI SDK)")
        print("2. Doubao (POST API)")
        print("3. DeepSeek (OpenAI SDK)")

        model_choice = input("\n请输入选项 (1/2/3，默认 1): ").strip()
        if model_choice == "2":
            tester.model_type = "doubao_post"
        elif model_choice == "3":
            tester.model_type = "deepseek_sdk"
        else:
            tester.model_type = "doubao_sdk"

        # 重新初始化客户端
        tester._initialize_llm_client()

        multi_mode = input(
            "\n是否需要同时运行多个学生角色？(y/n，默认 n): "
        ).strip().lower() == "y"
        selected_profiles = tester.prompt_student_profile(allow_multi=multi_mode)

        print("\n可选: 是否提供学生角色模拟对话 Markdown？")
        use_dialogue_md = input("是否加载模拟对话？(y/n，默认 n): ").strip().lower()
        if use_dialogue_md == "y":
            dialogue_path = input("\n请输入 Markdown 文件的绝对路径: ").strip()
            if dialogue_path:
                tester.load_student_dialogues(dialogue_path)
            else:
                print("⚠️  未提供路径，跳过加载模拟对话")

        print("\n可选: 是否使用外接知识库？")
        use_kb = input("是否使用知识库？(y/n，默认 n): ").strip().lower()
        if use_kb == "y":
            kb_path = input("\n请输入知识库 Markdown 文件的绝对路径: ").strip()
            if kb_path:
                if not tester.load_knowledge_base(kb_path):
                    print("⚠️  知识库加载失败，将以通用模式运行")
            else:
                print("⚠️  未提供知识库路径，跳过加载")

        print("\n开始工作流...")
        if multi_mode:
            asyncio.run(tester.run_profiles_concurrently(task_id, selected_profiles))
        else:
            tester.run_with_llm(task_id)

    else:
        print("❌ 无效选项")
