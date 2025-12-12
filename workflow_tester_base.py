import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv


class WorkflowTesterBase:
    """Common workflow tester logic shared by auto_script_train*.py scripts.

    Subclasses should:
    - Set DEFAULT_PROFILE_KEY / PROFILE_LABEL_FIELD_NAME / PROFILE_SELECT_TITLE if needed.
    - Populate self.student_profiles in __init__ (e.g., from class constant or config file).
    - Override _post_json to add retries if desired.
    - Override _log_run_card / _log_dialogue_entry if log format must differ.
    """

    DEFAULT_PROFILE_KEY: str = ""
    PROFILE_LABEL_FIELD_NAME: str = "学生档位"
    PROFILE_SELECT_TITLE: str = "学生档位"

    def __init__(self, base_url: str = "https://cloudapi.polymas.com"):
        self.base_url = base_url
        self.session = requests.Session()

        # Workflow state
        self.session_id: Optional[str] = None
        self.current_step_id: Optional[str] = None
        self.task_id: Optional[str] = None
        self.dialogue_round: int = 0

        # Paths/logging
        self.base_path = Path(__file__).resolve().parent
        self.log_root = self.base_path / "log"
        self.run_card_log_path: Optional[Path] = None
        self.dialogue_log_path: Optional[Path] = None
        self.log_prefix: Optional[str] = None
        self.log_context_path: Optional[Path] = None

        # Log format / JSON logging (subclasses may enable)
        self.log_format: str = "txt"  # "txt" | "json" | "both"
        self.json_log_enabled: bool = False
        self.json_log_path: Optional[Path] = None
        self.json_stages: Dict[str, Any] = {}
        self.workflow_start_time: Optional[datetime] = None

        # Student profiles
        self.student_profile_key: Optional[str] = None
        self.student_profiles: Dict[str, Dict[str, Any]] = {}
        self.dialogue_samples_content: Optional[str] = None
        self.knowledge_base_content: Optional[str] = None
        self.conversation_history: List[Dict[str, str]] = []

        # Step name mapping for nicer logs (optional)
        self.step_name_mapping: Dict[str, str] = {}

        # From environment
        load_dotenv()
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }

        authorization = os.getenv("AUTHORIZATION")
        cookie = os.getenv("COOKIE")
        if authorization:
            self.headers["Authorization"] = authorization
        if cookie:
            self.headers["Cookie"] = cookie

        custom_headers = os.getenv("CUSTOM_HEADERS")
        if custom_headers:
            try:
                extra_headers = json.loads(custom_headers)
                if isinstance(extra_headers, dict):
                    self.headers.update(extra_headers)
                else:
                    print("⚠️  警告: CUSTOM_HEADERS 必须是 JSON 对象，已忽略")
            except json.JSONDecodeError:
                print("⚠️  警告: CUSTOM_HEADERS 格式不正确，已忽略")

    # ---- Request helper ----
    def _post_json(self, url: str, payload: Dict[str, Any], timeout: int):
        """POST helper. Subclasses can override to add retries."""
        return self.session.post(url, json=payload, headers=self.headers, timeout=timeout)

    # ---- Logging ----
    def _prepare_log_files(self, task_id: str):
        """Create log files (TXT/JSON) and write headers."""
        timestamp = datetime.now()
        self.workflow_start_time = timestamp

        log_dir = self._determine_log_directory(task_id)
        log_dir.mkdir(parents=True, exist_ok=True)
        self.log_prefix = f"task_{task_id}_{timestamp.strftime('%Y%m%d_%H%M%S')}"

        fmt = getattr(self, "log_format", "txt")
        if fmt in ["json", "both"]:
            self.json_log_enabled = True
            self.json_log_path = log_dir / f"{self.log_prefix}_dialogue.json"
            self.json_stages = {}

        if fmt in ["txt", "both"]:
            self.run_card_log_path = log_dir / f"{self.log_prefix}_runcard.txt"
            self.dialogue_log_path = log_dir / f"{self.log_prefix}_dialogue.txt"
            profile_label = "未设置"
            if self.student_profile_key:
                try:
                    profile_label = self._get_student_profile_info().get("label", profile_label)
                except Exception:
                    pass

            header_lines = [
                f"日志创建时间: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
                f"task_id: {task_id}",
                f"{self.PROFILE_LABEL_FIELD_NAME}: {profile_label}",
            ]
            if self.log_context_path:
                header_lines.append(f"参考文档: {str(self.log_context_path)}")
            header_lines.append("=" * 60)
            header = "\n".join(header_lines) + "\n"

            for path, title in [
                (self.run_card_log_path, "RunCard 信息记录"),
                (self.dialogue_log_path, "对话记录"),
            ]:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(title + "\n")
                    f.write(header)

    def _append_log(self, path: Optional[Path], text: str):
        if not path:
            return
        with open(path, "a", encoding="utf-8") as f:
            f.write(text + "\n")

    def _get_step_display_name(self, step_id: Optional[str]) -> str:
        """Return readable name for step_id if mapping available."""
        if not step_id:
            return "未知步骤"
        mapping = getattr(self, "step_name_mapping", None)
        if isinstance(mapping, dict):
            return mapping.get(step_id, step_id)
        return step_id

    def _log_run_card(self, step_id: str, payload: Dict[str, Any], response_data: Dict[str, Any]):
        step_name = self._get_step_display_name(step_id)
        log_lines = [
            f"Step: {step_name}",
            f"请求载荷: {json.dumps(payload, ensure_ascii=False)}",
            f"响应内容: {json.dumps(response_data, ensure_ascii=False)}",
            "-" * 40,
        ]
        self._append_log(self.run_card_log_path, "\n".join(log_lines))

    def _log_dialogue_entry(
        self,
        step_id: str,
        user_text: Optional[str] = None,
        ai_text: Optional[str] = None,
        source: str = "chat",
    ):
        if user_text is None and ai_text is None:
            return
        step_name = self._get_step_display_name(step_id)
        round_info = f" | 第 {self.dialogue_round} 轮" if self.dialogue_round else ""
        header = f"Step: {step_name}{round_info} | 来源: {source}"
        lines = [header]
        if user_text:
            lines.append(f"用户: {user_text}")
        if ai_text:
            lines.append(f"AI: {ai_text}")
        lines.append("-" * 40)
        self._append_log(self.dialogue_log_path, "\n".join(lines))

        if user_text and hasattr(self, "_collect_stage_data"):
            try:
                self._collect_stage_data(step_id, self.dialogue_round, "user", user_text)
            except Exception:
                pass
        if ai_text and hasattr(self, "_collect_stage_data"):
            try:
                self._collect_stage_data(step_id, self.dialogue_round, "assistant", ai_text)
            except Exception:
                pass

    def _get_log_context_parts(self) -> List[str]:
        if not self.log_context_path:
            return []

        path = self.log_context_path
        if not isinstance(path, Path):
            path = Path(path)

        try:
            path = path.resolve()
        except Exception:
            pass

        try:
            relative = path.relative_to(self.base_path)
        except ValueError:
            relative = path

        parts = list(relative.parts)
        if not parts:
            return []

        if "skills_training_course" in parts:
            idx = parts.index("skills_training_course")
            parts = parts[idx + 1 :]

        if not parts:
            return []

        trimmed: List[str] = []
        for i, part in enumerate(parts):
            if i == len(parts) - 1:
                trimmed.append(Path(part).stem)
            else:
                trimmed.append(part)
        return trimmed

    def _determine_log_directory(self, task_id: str) -> Path:
        profile_key = self.student_profile_key or "unassigned"
        context_parts = self._get_log_context_parts()
        if context_parts:
            return self.log_root.joinpath(*context_parts, profile_key)
        return self.log_root / f"task_{task_id}" / profile_key

    def _update_log_context(self, new_path: Any):
        if not new_path:
            return

        try:
            path = Path(new_path).expanduser().resolve()
        except Exception:
            path = Path(new_path)

        priority = "skills_training_course" in path.parts
        if priority or not self.log_context_path:
            self.log_context_path = path

    # ---- Profiles ----
    def _get_student_profile_info(self) -> Dict[str, Any]:
        key = self.student_profile_key or self.DEFAULT_PROFILE_KEY
        if key and key in self.student_profiles:
            return self.student_profiles[key]
        if self.DEFAULT_PROFILE_KEY and self.DEFAULT_PROFILE_KEY in self.student_profiles:
            return self.student_profiles[self.DEFAULT_PROFILE_KEY]
        return next(iter(self.student_profiles.values()), {})

    def set_student_profile(self, profile_key: str):
        title = self.PROFILE_SELECT_TITLE
        if profile_key not in self.student_profiles:
            raise ValueError(f"未知的{title}: {profile_key}")
        self.student_profile_key = profile_key
        info = self._get_student_profile_info()
        print(f"\n🎓 已选择{title}: {info.get('label', profile_key)}")

    def prompt_student_profile(self, allow_multi: bool = False) -> List[str]:
        """Interactive selection of student profiles. Returns selected keys."""
        title = self.PROFILE_SELECT_TITLE
        print(f"\n请选择{title}：")
        options: Dict[str, str] = {}
        enabled_profiles = {
            k: v for k, v in self.student_profiles.items() if v.get("enabled", True)
        }

        for idx, (key, info) in enumerate(enabled_profiles.items(), 1):
            options[str(idx)] = key
            desc = info.get("description", "")
            print(f"{idx}. {info.get('label', key)} - {desc}")

        default_choice = next(
            (num for num, key in options.items() if key == self.DEFAULT_PROFILE_KEY),
            "1",
        )

        tip = "可输入多个编号并用逗号分隔" if allow_multi else "只需输入一个编号"
        prompt_template = f"\n请输入选项 (1-{len(options)}，默认 {default_choice}，{tip}): "

        while True:
            raw_choice = input(prompt_template).strip()
            if not raw_choice:
                raw_choice = default_choice

            selections = [c.strip() for c in raw_choice.split(",") if c.strip()]
            if not selections:
                selections = [default_choice]

            if all(choice in options for choice in selections):
                chosen_keys: List[str] = []
                for choice in selections:
                    mapped = options[choice]
                    if mapped not in chosen_keys:
                        chosen_keys.append(mapped)

                if not allow_multi:
                    self.set_student_profile(chosen_keys[0])
                    return chosen_keys

                labels = "，".join(
                    self.student_profiles[key].get("label", key) for key in chosen_keys
                )
                print(f"\n🎯 已选择 {len(chosen_keys)} 个{title}: {labels}")
                return chosen_keys

            print("⚠️  无效选项，请重新输入。")

    # ---- Optional content loading ----
    def load_student_dialogues(self, md_path: str) -> bool:
        """Load role example dialogues from a Markdown file."""
        try:
            path = Path(md_path)
            if not path.exists():
                print(f"❌ 模拟对话文件不存在: {md_path}")
                return False
            self.dialogue_samples_content = path.read_text(encoding="utf-8")
            print(
                f"✅ 已加载模拟对话: {md_path} (大小: {len(self.dialogue_samples_content)} 字符)"
            )
            self._update_log_context(path)
            return True
        except Exception as e:
            print(f"❌ 加载模拟对话失败: {str(e)}")
            return False

    def load_knowledge_base(self, kb_path: str) -> bool:
        """Load knowledge base Markdown file."""
        try:
            path = Path(kb_path)
            if not path.exists():
                print(f"❌ 知识库文件不存在: {kb_path}")
                return False

            self.knowledge_base_content = path.read_text(encoding="utf-8")
            print(
                f"✅ 知识库已加载: {kb_path} (大小: {len(self.knowledge_base_content)} 字符)"
            )
            self._update_log_context(path)
            return True
        except Exception as e:
            print(f"❌ 加载知识库失败: {str(e)}")
            return False

    # ---- Workflow API ----
    def test_connection(self) -> bool:
        """Check auth env vars and basic connectivity."""
        print("\n" + "=" * 60)
        print("🔍 开始测试接口连接...")
        print("=" * 60)

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

        print("\n2️⃣  测试网络连接:")
        try:
            response = requests.get(self.base_url, timeout=10)
            print(f"✅ 服务器可访问 (状态码: {response.status_code})")
            return True
        except requests.exceptions.RequestException as e:
            print(f"❌ 网络连接失败: {str(e)}")
            return False

    def query_script_step_list(self, task_id: str) -> str:
        """Get step list and return the first real stepId."""
        url = f"{self.base_url}/teacher-course/abilityTrain/queryScriptStepList"
        payload = {"trainTaskId": task_id, "trainSubType": "ability"}

        print(f"\n=== 获取步骤列表 ===")
        print(f"请求URL: {url}")

        timeout = getattr(self, "base_timeout", 60)
        try:
            response = self._post_json(url, payload, timeout=timeout)
            result = response.json()

            print(f"响应状态码: {response.status_code}")

            if result.get("code") == 200 and result.get("success"):
                data = result.get("data") or []
                if not data:
                    raise Exception("步骤列表为空")

                if isinstance(self.step_name_mapping, dict):
                    self.step_name_mapping.clear()
                    for step_item in data:
                        step_id = step_item.get("stepId")
                        step_detail = step_item.get("stepDetailDTO", {}) or {}
                        step_name = step_detail.get("stepName", "未命名步骤")
                        if step_id:
                            self.step_name_mapping[step_id] = step_name
                    if self.step_name_mapping:
                        print(f"✅ 已加载 {len(self.step_name_mapping)} 个步骤名称映射")

                first_idx = 2 if len(data) > 2 else 0
                first_step_id = data[first_idx].get("stepId")
                first_step_name = self._get_step_display_name(first_step_id)
                print(f"✅ 获取到第一个步骤: {first_step_name} ({first_step_id})")
                return first_step_id

            raise Exception(f"获取步骤列表失败: {result.get('msg')}")

        except requests.exceptions.Timeout:
            raise Exception("请求超时")
        except requests.exceptions.RequestException as e:
            raise Exception(f"网络请求失败: {str(e)}")

    def run_card(self, task_id: str, step_id: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Run a workflow card."""
        url = f"{self.base_url}/ai-tools/trainRun/runCard"
        payload = {"taskId": task_id, "stepId": step_id, "sessionId": session_id}
        if session_id:
            payload["sessionId"] = session_id

        print(f"\n=== 运行卡片 (stepId: {step_id}) ===")
        print(f"请求URL: {url}")
        print(f"请求载荷: {json.dumps(payload, indent=2, ensure_ascii=False)}")

        timeout = getattr(self, "base_timeout", 60)
        try:
            response = self._post_json(url, payload, timeout=timeout)
            result = response.json()
            self._log_run_card(step_id, payload, result)

            print(f"响应状态码: {response.status_code}")

            if result.get("code") == 200 and result.get("success"):
                data = result.get("data") or {}
                self.session_id = data.get("sessionId")
                self.current_step_id = step_id

                self.question_text = data.get("text")
                if self.question_text:
                    print(f"\n📝 AI 说: {self.question_text}")
                    self._log_dialogue_entry(step_id, ai_text=self.question_text, source="runCard")

                return result

            print("训练完成")
            return result

        except requests.exceptions.Timeout:
            raise Exception("请求超时")
        except requests.exceptions.RequestException as e:
            raise Exception(f"网络请求失败: {str(e)}")

    def chat(self, user_input: str, step_id: Optional[str] = None) -> Dict[str, Any]:
        """Send user answer to the workflow."""
        url = f"{self.base_url}/ai-tools/trainRun/chat"
        if step_id is None:
            step_id = self.current_step_id

        payload = {
            "taskId": self.task_id,
            "stepId": step_id,
            "text": user_input,
            "sessionId": self.session_id,
        }

        print(f"\n=== 发送用户回答 ===")
        print(f"👤 用户说: {user_input}")

        timeout = getattr(self, "base_timeout", 60)
        try:
            response = self._post_json(url, payload, timeout=timeout)
            result = response.json()

            print(f"响应状态码: {response.status_code}")

            if result.get("code") == 200 and result.get("success"):
                data = result.get("data") or {}
                next_step_id = data.get("nextStepId")
                need_skip = data.get("needSkipStep", False)
                ai_text = data.get("text")
                self.dialogue_round += 1
                self._log_dialogue_entry(
                    step_id, user_text=user_input, ai_text=ai_text, source="chat"
                )

                if ai_text:
                    print(f"\n📝 AI 说: {ai_text}")
                    self.question_text = ai_text

                if need_skip and next_step_id:
                    print(f"\n⏭️  需要跳转到下一步骤: {next_step_id}")
                    print("自动调用 runCard...")
                    self.current_step_id = next_step_id
                    return self.run_card(self.task_id, next_step_id, self.session_id)

                return result

            raise Exception(f"发送消息失败: {result.get('msg')}")

        except requests.exceptions.Timeout:
            raise Exception("请求超时")
        except requests.exceptions.RequestException as e:
            raise Exception(f"网络请求失败: {str(e)}")

    def start_workflow(self, task_id: str) -> Dict[str, Any]:
        """Start workflow by fetching first step and running it."""
        print("\n" + "=" * 60)
        print("🚀 启动工作流")
        print("=" * 60)

        self.task_id = task_id
        self.dialogue_round = 0
        self.conversation_history = []
        self._prepare_log_files(task_id)

        first_step_id = self.query_script_step_list(task_id)
        return self.run_card(task_id, first_step_id)

    def _finalize_workflow(self):
        """Optional finalize hook (e.g., write JSON logs)."""
        if hasattr(self, "_write_json_log") and getattr(self, "json_log_enabled", False):
            try:
                self._write_json_log()
            except Exception as e:
                print(f"⚠️  警告: JSON 日志写入失败: {str(e)}")

    def run_interactive(self, task_id: str):
        """Run workflow interactively."""
        try:
            self.start_workflow(task_id)
            round_num = 1

            while True:
                if self.current_step_id is None:
                    print("\n✅ 工作流完成！没有更多步骤了。")
                    break

                print("\n" + "=" * 60)
                print(f"💬 第 {round_num} 轮对话")
                print("=" * 60)

                user_answer = input("请输入你的回答（输入 'quit' 退出）: ").strip()
                if user_answer.lower() == "quit":
                    print("👋 用户主动退出")
                    break
                if not user_answer:
                    print("⚠️  回答不能为空，请重新输入")
                    continue

                result = self.chat(user_answer)
                data = result.get("data") or {}
                if data.get("nextStepId") is None:
                    print("\n✅ 工作流完成！")
                    break

                round_num += 1
                time.sleep(0.5)

            self._finalize_workflow()

        except Exception as e:
            print(f"\n❌ 错误: {str(e)}")
            import traceback

            traceback.print_exc()

    def run_auto(self, task_id: str, user_answers: List[str]):
        """Run workflow using preset answers."""
        try:
            self.start_workflow(task_id)

            for i, answer in enumerate(user_answers, 1):
                if self.current_step_id is None:
                    print("\n✅ 工作流已结束")
                    break

                print(f"\n--- 第 {i} 轮对话 ---")
                time.sleep(1)

                result = self.chat(answer)
                data = result.get("data") or {}
                if data.get("nextStepId") is None:
                    print("\n✅ 工作流完成！")
                    break

            self._finalize_workflow()

            print("\n" + "=" * 60)
            print("🎉 工作流测试结束")
            print("=" * 60)

        except Exception as e:
            print(f"\n❌ 错误: {str(e)}")
            import traceback

            traceback.print_exc()

