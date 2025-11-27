import requests
import json
import time
import os
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

class WorkflowTester:
    def __init__(self, base_url="https://cloudapi.polymas.com"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session_id = None
        self.current_step_id = None
        self.task_id = None
        self.dialogue_round = 0
        self.base_path = Path(__file__).resolve().parent
        self.log_dir = self.base_path / "logs"
        self.run_card_log_path = None
        self.dialogue_log_path = None
        self.log_prefix = None
        
        # 从环境变量加载认证信息
        load_dotenv()
        
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }
        
        # 添加认证信息
        authorization = os.getenv("AUTHORIZATION")
        cookie = os.getenv("COOKIE")
        
        if authorization:
            self.headers["Authorization"] = authorization
        
        if cookie:
            self.headers["Cookie"] = cookie
        
        # 添加其他可选的请求头
        custom_headers = os.getenv("CUSTOM_HEADERS")
        if custom_headers:
            try:
                extra_headers = json.loads(custom_headers)
                self.headers.update(extra_headers)
            except json.JSONDecodeError:
                print("⚠️  警告: CUSTOM_HEADERS 格式不正确，已忽略")

        # 初始化 Doubao 客户端
        self.doubao_client = None
        self.doubao_model = os.getenv("DOUBAO_MODEL", "doubao-seed-1-6-251015")
        self.knowledge_base_content = None
        self._initialize_doubao_client()

    def _initialize_doubao_client(self):
        """初始化 Doubao 客户端"""
        api_key = os.getenv("ARK_API_KEY")
        base_url = os.getenv("ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")

        if api_key:
            try:
                self.doubao_client = OpenAI(api_key=api_key, base_url=base_url)
            except Exception as e:
                print(f"⚠️  警告: 初始化 Doubao 客户端失败: {str(e)}")

    def _prepare_log_files(self, task_id):
        """创建日志文件并写入开头信息"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_prefix = f"task_{task_id}_{timestamp}"
        self.run_card_log_path = self.log_dir / f"{self.log_prefix}_runcard.txt"
        self.dialogue_log_path = self.log_dir / f"{self.log_prefix}_dialogue.txt"

        header = (
            f"日志创建时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"task_id: {task_id}\n"
            + "=" * 60 + "\n"
        )
        for path, title in [
            (self.run_card_log_path, "RunCard 信息记录"),
            (self.dialogue_log_path, "对话记录"),
        ]:
            with open(path, "w", encoding="utf-8") as f:
                f.write(title + "\n")
                f.write(header)

    def _append_log(self, path, text):
        if not path:
            return
        with open(path, "a", encoding="utf-8") as f:
            f.write(text + "\n")

    def _log_run_card(self, step_id, payload, response_data):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_lines = [
            f"[{timestamp}] Step {step_id}",
            f"请求载荷: {json.dumps(payload, ensure_ascii=False)}",
            f"响应内容: {json.dumps(response_data, ensure_ascii=False)}",
            "-" * 80,
        ]
        self._append_log(self.run_card_log_path, "\n".join(log_lines))

    def _log_dialogue_entry(self, step_id, user_text=None, ai_text=None, source="chat"):
        if user_text is None and ai_text is None:
            return
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        round_info = f" | 第 {self.dialogue_round} 轮" if self.dialogue_round else ""
        header = f"[{timestamp}] Step {step_id}{round_info} | 来源: {source}"
        lines = [header]
        if user_text:
            lines.append(f"用户: {user_text}")
        if ai_text:
            lines.append(f"AI: {ai_text}")
        lines.append("-" * 80)
        self._append_log(self.dialogue_log_path, "\n".join(lines))

    def load_knowledge_base(self, kb_path):
        """加载知识库文件"""
        try:
            path = Path(kb_path)
            if not path.exists():
                print(f"❌ 知识库文件不存在: {kb_path}")
                return False

            self.knowledge_base_content = path.read_text(encoding="utf-8")
            print(f"✅ 知识库已加载: {kb_path} (大小: {len(self.knowledge_base_content)} 字符)")
            return True
        except Exception as e:
            print(f"❌ 加载知识库失败: {str(e)}")
            return False

    def generate_answer_with_doubao(self, question):
        """使用 Doubao 模型生成回答"""
        if not self.doubao_client:
            print("❌ Doubao 客户端未初始化")
            return None

        try:
            system_prompt = "你是一个能力训练助手，需要根据提供的问题和知识库内容生成恰当的学生回答。"

            if self.knowledge_base_content:
                user_message = f"""根据以下知识库内容，生成一个学生的回答。

## 知识库内容
{self.knowledge_base_content}

## 问题
{question}

请生成一个自然、恰当的学生回答（只返回回答内容，不要包含其他说明）："""
            else:
                user_message = f"""请根据问题生成一个学生的回答。

## 问题
{question}

请生成一个自然、恰当的学生回答（只返回回答内容，不要包含其他说明）："""

            response = self.doubao_client.chat.completions.create(
                model=self.doubao_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                top_p=0.9
            )

            answer = response.choices[0].message.content
            return answer
        except Exception as e:
            print(f"❌ 调用 Doubao 模型失败: {str(e)}")
            return None

    def test_connection(self):
        """测试接口连接和认证是否正常"""
        print("\n" + "="*60)
        print("🔍 开始测试接口连接...")
        print("="*60)
        
        # 检查环境变量
        print("\n1️⃣  检查环境变量:")
        auth = os.getenv("AUTHORIZATION")
        cookie = os.getenv("COOKIE")
        
        if not auth and not cookie:
            print("❌ 错误: 未找到 AUTHORIZATION 或 COOKIE")
            return False
        
        if auth:
            print(f"✅ AUTHORIZATION: {auth[:20]}...")
        if cookie:
            print(f"✅ COOKIE: {cookie[:50]}...")
        
        # 测试网络连接
        print("\n2️⃣  测试网络连接:")
        try:
            response = requests.get(self.base_url, timeout=5)
            print(f"✅ 服务器可访问 (状态码: {response.status_code})")
            return True
        except requests.exceptions.RequestException as e:
            print(f"❌ 网络连接失败: {str(e)}")
            return False
    
    def query_script_step_list(self, task_id):
        """
        获取工作流的步骤列表，返回第一个 stepId
        """
        url = f"{self.base_url}/teacher-course/abilityTrain/queryScriptStepList"
        payload = {
            "trainTaskId": task_id,
            "trainSubType": "ability"
        }
        
        print(f"\n=== 获取步骤列表 ===")
        print(f"请求URL: {url}")
        # print(f"请求载荷: {json.dumps(payload, indent=2, ensure_ascii=False)}")
        
        try:
            response = self.session.post(url, json=payload, headers=self.headers, timeout=30)
            result = response.json()
            
            print(f"响应状态码: {response.status_code}")
            # print(f"响应内容: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            if result.get("code") == 200 and result.get("success"):
                data = result.get("data", [])
                if data and len(data) > 0:
                    first_step_id = data[2].get("stepId")
                    print(f"\n✅ 获取到第一个步骤ID: {first_step_id}")
                    return first_step_id
                else:
                    raise Exception("步骤列表为空")
            else:
                raise Exception(f"获取步骤列表失败: {result.get('msg')}")
                
        except requests.exceptions.Timeout:
            raise Exception("请求超时")
        except requests.exceptions.RequestException as e:
            raise Exception(f"网络请求失败: {str(e)}")
    
    def run_card(self, task_id, step_id, session_id=None):
        """
        运行工作流卡片
        """
        url = f"{self.base_url}/ai-tools/trainRun/runCard"
        
        payload = {
            "taskId": task_id,
            "stepId": step_id,
            "sessionId": session_id
        }
        
        # 如果有 sessionId，添加到载荷中
        if session_id:
            payload["sessionId"] = session_id
        
        print(f"\n=== 运行卡片 (stepId: {step_id}) ===")
        print(f"请求URL: {url}")
        print(f"请求载荷: {json.dumps(payload, indent=2, ensure_ascii=False)}")
        
        try:
            response = self.session.post(url, json=payload, headers=self.headers, timeout=30)
            result = response.json()
            self._log_run_card(step_id, payload, result)
            
            print(f"响应状态码: {response.status_code}")
            # print(f"响应内容: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            if result.get("code") == 200 and result.get("success"):
                data = result.get("data", {})
                self.session_id = data.get("sessionId")
                self.current_step_id = step_id
                
                self.question_text = data.get("text")
                need_skip = data.get("needSkipStep", False)
                
                if self.question_text:
                    print(f"\n📝 AI 说: {self.question_text}")
                    self._log_dialogue_entry(step_id, ai_text=self.question_text, source="runCard")
                
                return result
            else:
                raise Exception(f"运行卡片失败: {result.get('msg')}")
                
        except requests.exceptions.Timeout:
            raise Exception("请求超时")
        except requests.exceptions.RequestException as e:
            raise Exception(f"网络请求失败: {str(e)}")
    
    def chat(self, user_input, step_id=None):
        """
        发送用户回答
        """
        url = f"{self.base_url}/ai-tools/trainRun/chat"
        
        if step_id is None:
            step_id = self.current_step_id
        
        payload = {
            "taskId": self.task_id,
            "stepId": step_id,
            "text": user_input,
            "sessionId": self.session_id
        }
        
        print(f"\n=== 发送用户回答 ===")
        print(f"👤 用户说: {user_input}")
        # print(f"请求载荷: {json.dumps(payload, indent=2, ensure_ascii=False)}")
        
        try:
            response = self.session.post(url, json=payload, headers=self.headers, timeout=30)
            result = response.json()
            
            print(f"响应状态码: {response.status_code}")
            # print(f"响应内容: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            if result.get("code") == 200 and result.get("success"):
                data = result.get("data", {})
                next_step_id = data.get("nextStepId")
                need_skip = data.get("needSkipStep", False)
                ai_text = data.get("text")
                self.dialogue_round += 1
                self._log_dialogue_entry(step_id, user_text=user_input, ai_text=ai_text, source="chat")
                
                if ai_text:
                    print(f"\n📝 AI 说: {ai_text}")

                # 关键逻辑：如果 needSkipStep=true 且 nextStepId 不为空，需要调用 runCard
                if need_skip and next_step_id:
                    print(f"\n⏭️  需要跳转到下一步骤: {next_step_id}")
                    print("自动调用 runCard...")
                    self.current_step_id=next_step_id
                    if not ai_text:
                        print("\n✅ 训练结束返回")
                        return result 
                    return self.run_card(self.task_id, next_step_id, self.session_id)
                else:
                    return result
            else:
                raise Exception(f"发送消息失败: {result.get('msg')}")
                
        except requests.exceptions.Timeout:
            raise Exception("请求超时")
        except requests.exceptions.RequestException as e:
            raise Exception(f"网络请求失败: {str(e)}")
    
    def start_workflow(self, task_id):
        """
        启动工作流
        1. 获取第一个 stepId
        2. 调用 runCard 开始第一步
        """
        print("\n" + "="*60)
        print("🚀 启动工作流")
        print("="*60)
        
        self.task_id = task_id
        self.dialogue_round = 0
        self._prepare_log_files(task_id)
        
        # 1. 获取第一个步骤ID
        first_step_id = self.query_script_step_list(task_id)

        # 2. 运行第一个卡片
        result = self.run_card(task_id, first_step_id)
        
        return result
    
    def run_interactive(self, task_id):
        """
        交互式运行工作流
        """
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
                
                print("\n" + "="*60)
                print(f"💬 第 {round_num} 轮对话")
                print("="*60)
                
                user_answer = input("请输入你的回答（输入 'quit' 退出）: ").strip()
                
                if user_answer.lower() == 'quit':
                    print("👋 用户主动退出")
                    break
                
                if not user_answer:
                    print("⚠️  回答不能为空，请重新输入")
                    continue
                
                # 发送用户回答
                result = self.chat(user_answer)
                
                # 检查返回结果中的 nextStepId
                data = result.get("data", {})
                if data.get("nextStepId") is None:
                    print("\n✅ 工作流完成！")
                    break
                
                round_num += 1
                time.sleep(0.5)  # 稍微延迟，避免请求过快
                
        except Exception as e:
            print(f"\n❌ 错误: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def run_auto(self, task_id, user_answers):
        """
        自动化运行工作流（使用预设答案）
        """
        try:
            # 启动工作流
            self.start_workflow(task_id)

            # 循环回答问题
            for i, answer in enumerate(user_answers, 1):
                if self.current_step_id is None:
                    print("\n✅ 工作流已结束")
                    break

                print(f"\n--- 第 {i} 轮对话 ---")
                time.sleep(1)

                result = self.chat(answer)

                # 检查是否完成
                data = result.get("data", {})
                if data.get("nextStepId") is None:
                    print("\n✅ 工作流完成！")
                    break

            print("\n" + "="*60)
            print("🎉 工作流测试结束")
            print("="*60)

        except Exception as e:
            print(f"\n❌ 错误: {str(e)}")
            import traceback
            traceback.print_exc()

    def run_with_doubao(self, task_id):
        """
        使用 Doubao 模型自动生成回答并运行工作流
        """
        if not self.doubao_client:
            print("\n❌ Doubao 客户端未初始化，请检查 ARK_API_KEY 环境变量")
            return

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

                print("\n" + "="*60)
                print(f"🤖 第 {round_num} 轮对话（Doubao 自主回答）")
                print("="*60)

                # 使用 Doubao 生成回答
                print(f"\n🔄 正在生成回答...")
                generated_answer = self.generate_answer_with_doubao(self.question_text)

                if not generated_answer:
                    print("❌ 无法生成回答，跳过此轮")
                    break

                print(f"\n🤖 Doubao 生成的回答: {generated_answer}")

                # 发送生成的回答
                result = self.chat(generated_answer)

                # 检查返回结果中的text,如果为null代表输出结束 
                data = result.get("data", {})
                if data.get("text") is None:
                    print("\n✅ 工作流完成！")
                    break

                round_num += 1
                time.sleep(1)  # 稍微延迟，避免请求过快

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
        print("\n🤖 使用 Doubao 模型自主回答模式")
        print("可选: 是否使用外接知识库？")
        use_kb = input("\n是否使用知识库？(y/n，默认 n): ").strip().lower()

        if use_kb == "y":
            kb_path = input("\n请输入知识库 Markdown 文件的绝对路径: ").strip()
            if kb_path:
                if tester.load_knowledge_base(kb_path):
                    print(f"✅ 知识库已加载，开始工作流...")
                    tester.run_with_doubao(task_id)
                else:
                    print("❌ 知识库加载失败，请检查路径")
            else:
                print("⚠️  未提供知识库路径，将以通用模式运行...")
                tester.run_with_doubao(task_id)
        else:
            print("\n开始工作流（不使用外接知识库）...")
            tester.run_with_doubao(task_id)

    else:
        print("❌ 无效选项")
