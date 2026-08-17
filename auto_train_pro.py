#!/usr/bin/env python3
"""
能力训练 Pro（音频版）trainV2 协议测试工具 powered by Richard Zhang

对接 wss://cloudapi.polymas.com/ai-platform/ws/trainV2（与 skill_training_pro/auto_train_v2.py
同一端点），区别在于 Pro 任务是 agentscope 类型：阶段的角色/子任务由服务端 LLM 运行时规划，
且开启了 TTS（botAnswer 期间以二进制帧下发 MP3 语音，本脚本不保存，直接丢弃）。

阶段切换死锁修复（关键，由跨阶段 HAR 定位）：
  首阶段由 scriptStart 自动开场；但**非首阶段**服务端在收到 stepStart 后会停在
  selectRoleStart 等待——学生必须先主动应答一句（浏览器端用户手动输入“好的”之类）
  + continueCurrentStep，本阶段才会启动，否则永久卡死（selectRoleStart 后再无
  selectRoleEnd，心跳正常但对话不推进）。故本脚本在每个 step_index>=2 的 stepStart
  之后，自动补发一次“阶段开场应答”（见 _handle_stage_entry，默认发“好的”，
  可用 STAGE_ENTRY_TEXT 覆盖）。

协议要点（由 HAR 录制解码并验证）：
  连接成功 → 发 scriptStart（先于 connected）
  收 nextStep{nextStepId} → 发 stepStart{stepId}
  每个角色回合结束发恰好一次 continueCurrentStep
    - selectRoleEnd.roleNid == "user" → 学生回合：userTextInput → continueCurrentStep
    - 其它角色 → 等 botAnswerEnd（取 payload.content 整句）→ continueCurrentStep
  roleNid == "system" 为主理人教练点评（评价上一句，非对话）
  stepEnd 仅作标记；scriptEnd 结束
  heartBeat 每 30s

半交互模式：回车=AI 生成、输入文字=手动、continue=切全自动、quit=退出
"""

import asyncio
import json
import logging
import os
import sys
import secrets
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from dotenv import load_dotenv
import websockets
import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
log = logging.getLogger(__name__)

# 事件级追踪：设 TRAINPRO_TRACE=1 打印每条收/发的原始 WS 事件，用于排查协议卡死
TRACE = os.getenv("TRAINPRO_TRACE", "") == "1"

# ============ 配置 ============
load_dotenv()

# 本 Pro 音频任务的 trainTaskId（来自创建页 URL 的 trainTaskId 参数）。
# 命令行第一个参数可覆盖它，例如：python auto_train_pro.py <trainTaskId>
DEFAULT_TASK_ID = "PROuNODZ41RAJttrEuzs"

CONFIG = {
    "ws_url": "wss://cloudapi.polymas.com/ai-platform/ws/trainV2",
    # task_id 在 main() 中由 argv[1] 或 DEFAULT_TASK_ID 决定；刻意不读共享的 .env TASK_ID，
    # 以免误连到其它脚本遗留的旧任务
    "task_id": None,
    "user_id": os.getenv("USER_ID"),  # 留空则通过 API 获取
}


def get_user_info():
    """调用 API 获取当前登录用户 userNid，保证与 AUTHORIZATION 一致。"""
    url = "https://cloudapi.polymas.com/console/v1/get-current-user-detail"

    authorization = os.getenv("AUTHORIZATION")
    cookie = os.getenv("COOKIE")

    if not authorization or not cookie:
        print("❌ 错误：缺少 AUTHORIZATION 或 COOKIE 环境变量")
        print("请在 .env 文件中配置这些参数")
        sys.exit(1)

    headers = {
        "Authorization": authorization,
        "Cookie": cookie,
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        if data.get("code") != 200 or not data.get("success"):
            print(f"❌ API 调用失败：{data.get('msg', '未知错误')}")
            sys.exit(1)

        return data["data"]["userNid"]
    except requests.exceptions.RequestException as e:
        print(f"❌ 网络请求失败：{e}")
        print("请检查网络连接和认证信息（AUTHORIZATION, COOKIE）")
        sys.exit(1)
    except (KeyError, TypeError) as e:
        print(f"❌ API 响应格式错误：{e}")
        sys.exit(1)


# ============ 学生档位定义 ============
STUDENT_PROFILES = {
    "good": {
        "label": "优秀学生",
        "description": "理解透彻、表达清晰，回答结构化、条理分明，并主动总结要点。",
        "style": "语气自信、语言规范，必要时引用题目或材料中的关键信息。",
    },
    "medium": {
        "label": "需要引导的学生",
        "description": "基本理解问题但不够全面，回答中会暴露疑惑或请求提示。",
        "style": "语气略显犹豫，能覆盖核心内容，但会提出 1-2 个不确定点或寻求建议。",
    },
    "bad": {
        "label": "答非所问的学生",
        "description": "理解偏差，常常跑题或只复述与问题弱相关的信息。",
        "style": "语气随意，容易偏离重点或答非所问。",
    },
}


# ============ 日志记录器（多角色 + 音频） ============
class ConversationLogger:
    def __init__(self, log_file: Path, task_id: str, session_id: str,
                 student_profile_key: str, student_profile_label: str,
                 reference_path: Optional[str]):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

        with open(self.log_file, 'w', encoding='utf-8') as f:
            f.write("能力训练 Pro（音频版）多角色对话记录\n")
            f.write(f"日志创建时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"task_id: {task_id or 'unknown'}\n")
            f.write(f"session_id: {session_id}\n")
            f.write(f"学生档位: {student_profile_label} ({student_profile_key})\n")
            f.write(f"参考文档路径: {reference_path or '无'}\n")
            f.write("=" * 60 + "\n")

    def log(self, label: str, role_type: str, content: str,
            step_index: int, step_id: str, round_num: int):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        first_line = (
            f"[{timestamp}] Step #{step_index} | step_id: {step_id} "
            f"| 第 {round_num} 轮 | 角色: {label}({role_type})"
        )
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(first_line + "\n")
            f.write(f"{label}: {content}\n")
            f.write("-" * 80 + "\n")

        icon = {"user": "👤", "system": "🧑‍🏫", "bot": "🤖"}.get(role_type, "💬")
        print(f"{icon} {label}: {content}")


# ============ 能力训练 Pro 客户端 ============
class TrainProClient:
    def __init__(self):
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.logger: Optional[ConversationLogger] = None
        self._ws_send_lock = asyncio.Lock()
        self._done = asyncio.Event()

        self.session_id = secrets.token_urlsafe(16)[:21]
        self.session_ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.is_connected = False
        self.task_completed = False

        self.step_id: Optional[str] = None
        self.step_index = 0
        self.round_counter = 0
        self.current_role: Optional[Dict[str, str]] = None

        # 阶段开场应答文本（非首阶段进入时，学生需先主动应答一句服务端才会启动本阶段）
        self.stage_entry_text = os.getenv("STAGE_ENTRY_TEXT", "好的")
        self.stage_entry_max_tries = int(os.getenv("STAGE_ENTRY_TRIES", "12"))
        # 每次开场应答后最多等多久判定“本阶段已启动”；需 > 服务端首角色规划耗时(约37s)
        self.stage_entry_timeout = float(os.getenv("STAGE_ENTRY_TIMEOUT", "60"))
        self.stage_entry_quiet = float(os.getenv("STAGE_ENTRY_QUIET", "2.5"))
        self._event_seq = 0                    # 每收到一个事件(含音频帧)+1，用于检测“安静”
        self._stage_entry_running = False
        self._bot_spoke = asyncio.Event()      # 收到 botAnswerStart 即置位：本阶段已启动
        self._continue_superseded = asyncio.Event()  # 收到 continueSuperseded：开场被拒，需重试

        # 半交互 / 全自动
        self.auto_continue = False
        self.max_auto_turns = int(os.getenv("MAX_AUTO_TURNS", "40"))
        # 发送节流：浏览器端每个回合间有语音播放+人反应的秒级间隔；
        # 设 SEND_PACE=秒 可在推进类消息(continueCurrentStep/stepStart)前加同样的停顿
        self.send_pace = float(os.getenv("SEND_PACE", "0"))

        # 学生档位
        self.student_profile_key = "medium"

        # LLM（豆包 POST）配置
        self.llm_api_url = os.getenv(
            "LLM_API_URL",
            "http://llm-service.polymas.com/api/openai/v1/chat/completions",
        )
        self.llm_api_key = os.getenv("LLM_API_KEY", "")
        self.llm_model = os.getenv("LLM_MODEL", "Doubao-1.5-pro-32k")
        self.llm_service_code = os.getenv("LLM_SERVICE_CODE", "SI_Ability")

        # 带标签的对话历史：[{label, type, content}]
        self.conversation_history: List[Dict[str, str]] = []
        self.reference_dialogue_content: Optional[str] = None
        self.knowledge_base_content: Optional[str] = None
        self.reference_dialogue_path: Optional[str] = None
        self.knowledge_base_path: Optional[str] = None

    # ---------- 上下文加载 ----------
    def _read_text_file(self, path: Path) -> str:
        return path.read_text(encoding="utf-8")

    def _convert_docx_to_markdown(self, path: Path) -> str:
        # docx_to_md.py 位于项目根目录（与本文件同级）
        docx_to_md_path = Path(__file__).parent / "docx_to_md.py"
        if not docx_to_md_path.exists():
            raise FileNotFoundError("未找到 docx_to_md.py，无法解析 .docx 文件")
        sys.path.insert(0, str(docx_to_md_path.parent))
        try:
            from docx_to_md import docx_to_markdown_content  # type: ignore
            return docx_to_markdown_content(path, extract_images=False)
        finally:
            sys.path.pop(0)

    def _truncate_context(self, text: str, limit: int, label: str) -> str:
        if len(text) <= limit:
            return text
        log.warning(f"⚠️ {label}内容过长，已截断: {len(text)} -> {limit}")
        return text[:limit].rstrip() + "\n[...已截断]"

    def _parse_dialogue_json_to_pairs(self, data: Any) -> List[Dict[str, str]]:
        pairs: List[Dict[str, str]] = []

        # workflow_tester_base 导出结构：stages[].messages[]
        if isinstance(data, dict) and isinstance(data.get("stages"), list):
            for stage in data.get("stages", []):
                if not isinstance(stage, dict):
                    continue
                last_ai = ""
                for message in stage.get("messages", []) or []:
                    if not isinstance(message, dict):
                        continue
                    role = str(message.get("role", "")).strip().lower()
                    content = str(message.get("content", "")).strip()
                    if not content:
                        continue
                    if role in {"assistant", "ai", "bot"}:
                        last_ai = content
                    elif role in {"user", "student", "human"} and last_ai:
                        pairs.append({"ai": last_ai, "student": content})
            if pairs:
                return pairs

        # 兜底：常见列表格式
        candidate_lists: List[Any] = []
        if isinstance(data, list):
            candidate_lists.append(data)
        elif isinstance(data, dict):
            for key in ["dialogues", "conversation", "conversations", "pairs", "messages", "data"]:
                if isinstance(data.get(key), list):
                    candidate_lists.append(data[key])

        ai_keys = ["ai", "assistant", "question", "prompt", "bot", "teacher_question"]
        student_keys = ["student", "user", "answer", "response", "reply"]
        for items in candidate_lists:
            for item in items:
                if not isinstance(item, dict):
                    continue
                ai_text = next((item[k].strip() for k in ai_keys
                                if isinstance(item.get(k), str) and item[k].strip()), "")
                student_text = next((item[k].strip() for k in student_keys
                                     if isinstance(item.get(k), str) and item[k].strip()), "")
                if ai_text and student_text:
                    pairs.append({"ai": ai_text, "student": student_text})
        return pairs

    def _format_dialogue_pairs_for_prompt(self, pairs: List[Dict[str, str]]) -> str:
        lines: List[str] = []
        for idx, pair in enumerate(pairs, 1):
            ai_text = pair.get("ai", "").strip()
            student_text = pair.get("student", "").strip()
            if not ai_text or not student_text:
                continue
            lines.append(f"第{idx}轮:")
            lines.append(f"  对方: {ai_text}")
            lines.append(f"  学生: {student_text}")
        return "\n".join(lines)

    def load_reference_dialogue(self, path_str: str) -> bool:
        try:
            path = Path(path_str).expanduser()
            if not path.exists():
                log.warning(f"⚠️ 对话记录文件不存在: {path_str}")
                return False
            suffix = path.suffix.lower()
            if suffix == ".json":
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                pairs = self._parse_dialogue_json_to_pairs(data)
                if not pairs:
                    log.warning("⚠️ JSON 对话记录未提取到有效问答对")
                    return False
                content = self._format_dialogue_pairs_for_prompt(pairs)
                log.info(f"✅ JSON 对话记录提取成功: {len(pairs)} 组问答")
            elif suffix == ".docx":
                content = self._convert_docx_to_markdown(path)
            else:
                content = self._read_text_file(path)

            self.reference_dialogue_content = self._truncate_context(content, 8000, "对话记录")
            self.reference_dialogue_path = str(path.resolve())
            log.info(f"✅ 已加载对话记录: {self.reference_dialogue_path}")
            return True
        except json.JSONDecodeError as exc:
            log.warning(f"⚠️ 对话记录 JSON 解析失败: {exc}")
            return False
        except Exception as exc:
            log.warning(f"⚠️ 加载对话记录失败: {exc}")
            return False

    def load_knowledge_base(self, path_str: str) -> bool:
        try:
            path = Path(path_str).expanduser()
            if not path.exists():
                log.warning(f"⚠️ 知识库文件不存在: {path_str}")
                return False
            suffix = path.suffix.lower()
            if suffix == ".docx":
                content = self._convert_docx_to_markdown(path)
            else:
                content = self._read_text_file(path)
            self.knowledge_base_content = self._truncate_context(content, 12000, "知识库")
            self.knowledge_base_path = str(path.resolve())
            log.info(f"✅ 已加载知识库: {self.knowledge_base_path}")
            return True
        except Exception as exc:
            log.warning(f"⚠️ 加载知识库失败: {exc}")
            return False

    # ---------- 日志 ----------
    def ensure_logger(self) -> ConversationLogger:
        if self.logger is not None:
            return self.logger
        context_path = self.knowledge_base_path or self.reference_dialogue_path
        profile = STUDENT_PROFILES.get(self.student_profile_key, STUDENT_PROFILES["medium"])
        log_dir = Path(__file__).parent / "trainv2_pro_logs"
        task_id = str(CONFIG.get("task_id") or "unknown")
        log_file = log_dir / f"task_{task_id}_{self.session_ts}_trainpro.txt"
        self.logger = ConversationLogger(
            log_file=log_file, task_id=task_id, session_id=self.session_id,
            student_profile_key=self.student_profile_key,
            student_profile_label=profile["label"], reference_path=context_path,
        )
        log.info(f"📝 日志: {self.logger.log_file}")
        return self.logger

    def _record_turn(self, label: str, role_type: str, content: str):
        self.ensure_logger().log(
            label=label, role_type=role_type, content=content,
            step_index=self.step_index, step_id=self.step_id or "-",
            round_num=self.round_counter,
        )
        self.conversation_history.append({"label": label, "type": role_type, "content": content})
        if len(self.conversation_history) > 30:
            self.conversation_history = self.conversation_history[-30:]

    # ---------- WebSocket ----------
    async def connect(self):
        url = (
            f"{CONFIG['ws_url']}?taskId={CONFIG['task_id']}"
            f"&userId={CONFIG['user_id']}&sessionId={self.session_id}"
        )
        headers = {
            "Origin": "https://hike-teaching-center.polymas.com",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        }
        # 网关要求携带登录态 Cookie 才会执行 WS 升级（否则返回 HTTP 200 拒绝）
        if os.getenv("COOKIE"):
            headers["Cookie"] = os.getenv("COOKIE")
        if os.getenv("AUTHORIZATION"):
            headers["Authorization"] = os.getenv("AUTHORIZATION")
        # 不使用 WS 协议级 ping（新服务器靠应用层 heartBeat 保活，与网页端一致）
        self.ws = await websockets.connect(
            url, additional_headers=headers, proxy=None,
            ping_interval=None, max_size=None,
        )
        self.is_connected = True
        log.info(f"✅ WebSocket 连接成功 (sessionId={self.session_id})")
        await self.send_json("scriptStart")
        log.info("📤 scriptStart")

    async def disconnect(self):
        if self.ws:
            await self.ws.close()
        self.is_connected = False
        log.info("连接已断开")

    async def send_json(self, event: str, payload: Optional[dict] = None):
        msg = {"event": event}
        if payload is not None:
            msg["payload"] = payload
        if TRACE:
            log.info(f"📨 SEND {event} {payload if payload else ''}")
        async with self._ws_send_lock:
            await self.ws.send(json.dumps(msg, ensure_ascii=False))

    async def _pace(self):
        if self.send_pace > 0:
            await asyncio.sleep(self.send_pace)

    async def send_step_start(self, step_id: str):
        await self._pace()
        await self.send_json("stepStart", {"stepId": step_id})

    async def send_continue(self):
        await self._pace()
        await self.send_json("continueCurrentStep")

    async def send_user_text(self, text: str):
        await self.send_json("userTextInput", {"text": text})

    async def send_heartbeat(self):
        await self.send_json("heartBeat", {})

    # ---------- LLM ----------
    def _call_doubao_post(self, messages, temperature=0.7, max_tokens=300):
        headers = {"Content-Type": "application/json", "service-code": self.llm_service_code}
        if self.llm_api_key:
            headers["api-key"] = self.llm_api_key
        payload = {
            "model": self.llm_model, "messages": messages,
            "temperature": temperature, "max_tokens": max_tokens,
            "top_p": 0.9, "frequency_penalty": 0.3, "presence_penalty": 0.2,
        }
        try:
            response = requests.post(self.llm_api_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"].strip()
        except requests.exceptions.RequestException as e:
            log.error(f"❌ Doubao API 调用失败: {e}")
            return None
        except (KeyError, IndexError) as e:
            log.error(f"❌ 解析响应失败: {e}")
            return None

    def _format_history_for_prompt(self) -> str:
        lines: List[str] = []
        for turn in self.conversation_history[-14:]:
            t, content = turn["type"], turn["content"]
            if t == "system":
                lines.append(f"[教练点评] {content}")
            elif t == "user":
                lines.append(f"[你] {content}")
            else:
                lines.append(f"[{turn['label']}] {content}")
        return "\n".join(lines)

    def generate_ai_answer(self) -> str:
        if not self.llm_api_url or not self.llm_api_key:
            log.error("❌ Doubao API 未配置（缺少 LLM_API_KEY）")
            return "好的，我明白了。"

        profile = STUDENT_PROFILES.get(self.student_profile_key, STUDENT_PROFILES["medium"])
        log.info(
            "🧠 上下文: 参考对话=%s 知识库=%s 历史=%d 条",
            "启用" if self.reference_dialogue_content else "关闭",
            "启用" if self.knowledge_base_content else "关闭",
            len(self.conversation_history),
        )

        system_prompt = (
            "你是中文角色扮演实训中的学生学员，扮演本次实训分配给你的角色。"
            "请先根据对话历史、对方话语与教练点评，推断你的身份、立场与本轮目标，再作出回应。"
            "只用中文，只输出你这一句要说的话，不要旁白或解释。"
        )

        sections = [
            "## 角色设定",
            f"学生档位: {profile['label']}",
            f"角色特征: {profile['description']}",
            f"表达风格: {profile['style']}",
            "",
            "## 重要规则",
            "- 你的具体角色由场景决定（如客服、原告/被告、医生、销售等），不要预设固定身份，须从对话上下文推断。",
            "- [教练点评] 是主理人对你上一句的评价与纠正，请在你接下来的发言中改进，但绝不要直接回复教练。",
            "- 你的发言对象是当前与你对话的角色，围绕推进本轮实训任务目标展开（如澄清事实、表达立场、回应诉求、协商方案）。",
            "- 确认/选择类问题直接简短回应。",
            "",
        ]
        if self.reference_dialogue_content:
            sections += ["## 参考对话记录（可借鉴结论与表达，勿照搬编造）",
                         self.reference_dialogue_content, ""]
        if self.knowledge_base_content:
            sections += ["## 参考知识库（依据其作答，勿编造不存在的信息）",
                         self.knowledge_base_content, ""]

        history_text = self._format_history_for_prompt()
        if history_text:
            sections += ["## 对话历史（按时间顺序）", history_text, ""]

        sections += [
            "## 输出要求",
            "结合角色档位与上方对话历史/教练点评，生成你（学生）对“对方角色”说的下一句话。",
            "只返回这一句话本身，自然口语化，中文，控制在 60 字以内。",
            "",
        ]

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "\n".join(sections)},
        ]
        log.info("🔄 调用 Doubao 生成学生回答...")
        answer = self._call_doubao_post(messages, temperature=0.7, max_tokens=200)
        return answer or "好的，我明白了。"

    # ---------- 回合处理 ----------
    async def _get_user_answer(self) -> Optional[str]:
        """返回要发送的学生回答；返回 None 表示退出。"""
        if self.auto_continue:
            print("\n🤖 [全自动] 正在生成回答...")
            return await asyncio.to_thread(self.generate_ai_answer)

        loop = asyncio.get_running_loop()
        print("\n" + "-" * 60)
        print("💬 轮到你（学生）回答:")
        print("   [回车] AI 生成 | [输入文字] 手动 | [continue] 全自动 | [quit] 退出")
        print("-" * 60)
        user_input = (await loop.run_in_executor(None, input, ">> ")).strip()

        if user_input.lower() == "quit":
            print("👋 用户主动退出")
            return None
        if user_input.lower() == "continue":
            print("\n🚀 切换到全自动模式...")
            self.auto_continue = True
            return await asyncio.to_thread(self.generate_ai_answer)
        if user_input == "":
            print("🤖 正在生成 AI 回答...")
            return await asyncio.to_thread(self.generate_ai_answer)
        return user_input

    async def _handle_user_turn(self):
        self.round_counter += 1

        if self.auto_continue and self.round_counter > self.max_auto_turns:
            log.warning(f"⚠️ 全自动已达上限 {self.max_auto_turns} 轮，主动结束（防失控）")
            self.task_completed = True
            self._done.set()
            return

        text = await self._get_user_answer()
        if text is None:
            self.task_completed = True
            self._done.set()
            return

        self._record_turn(label="你(学生)", role_type="user", content=text)
        await self.send_user_text(text)
        await self.send_continue()

    async def _wait_quiet(self, quiet: float):
        """等服务端安静下来：连续 quiet 秒无任何事件/音频帧即返回（自适应上一阶段音频长短）。"""
        while not self.task_completed:
            prev = self._event_seq
            await asyncio.sleep(quiet)
            if self._event_seq == prev:
                return

    async def _handle_stage_entry(self):
        """非首阶段开场：stepStart 后服务端停在 selectRoleStart 等学生应答，学生须主动发一句
        （如“好的”）+ continueCurrentStep 才会启动本阶段。但过早发送会被 continueSuperseded 拒绝，
        故：等安静→发应答→等本阶段启动(bot 开口)；被拒或超时则重试，最多 stage_entry_max_tries 次。"""
        if self._stage_entry_running:
            return
        self._stage_entry_running = True
        try:
            if self.auto_continue:
                text = self.stage_entry_text
            else:
                loop = asyncio.get_running_loop()
                print("\n" + "-" * 60)
                print(f"🚪 进入新阶段，请先应答以继续（回车=“{self.stage_entry_text}” / 输入文字 / quit）:")
                print("-" * 60)
                ui = (await loop.run_in_executor(None, input, ">> ")).strip()
                if ui.lower() == "quit":
                    self.task_completed = True
                    self._done.set()
                    return
                text = ui or self.stage_entry_text
            self.round_counter += 1
            self._record_turn(label="你(学生)", role_type="user", content=text)

            for attempt in range(1, self.stage_entry_max_tries + 1):
                await self._wait_quiet(self.stage_entry_quiet)  # 等服务端安静再发，降低被拒概率
                if self.task_completed:
                    return
                self._bot_spoke.clear()
                self._continue_superseded.clear()
                log.info(f"🚪 阶段开场应答（第 {attempt}/{self.stage_entry_max_tries} 次）: {text}")
                await self.send_user_text(text)
                await self.send_continue()
                # 等本阶段真正启动（bot 开口）。服务端首角色规划可能耗时数十秒，故超时给足。
                waited = 0.0
                while waited < self.stage_entry_timeout:
                    if self._bot_spoke.is_set():
                        log.info(f"✅ 本阶段已启动（第 {attempt} 次开场生效）")
                        return
                    if self._continue_superseded.is_set():
                        log.warning(f"⚠️ 第 {attempt} 次开场被 continueSuperseded，重试")
                        break
                    if self.task_completed:
                        return
                    await asyncio.sleep(0.5)
                    waited += 0.5
                else:
                    log.warning(f"⚠️ 第 {attempt} 次开场 {self.stage_entry_timeout:.0f}s 内无响应，重试")
            log.error("❌ 阶段开场多次重试仍未启动本阶段（可能服务端异常）")
        finally:
            self._stage_entry_running = False

    # ---------- 事件分发 ----------
    async def handle_message(self, message: str):
        try:
            data = json.loads(message)
        except json.JSONDecodeError:
            return
        event = data.get("event")
        payload = data.get("payload") or {}
        self._event_seq += 1  # 记录活动，供阶段开场去抖检测“安静”

        if TRACE:
            log.info(f"📩 RECV {event} nid={data.get('nid')} "
                     f"roleNid={payload.get('roleNid')} status={payload.get('status')}")

        if event == "connected":
            log.info(f"📱 connected: connectType={payload.get('connectType')}")

        elif event == "nextStep":
            self.step_id = payload.get("nextStepId")
            self.step_index += 1
            log.info(f"➡️ nextStep #{self.step_index}: {self.step_id} (status={payload.get('status')})")
            await self.send_step_start(self.step_id)
            log.info(f"📤 stepStart: {self.step_id}")
            # 关键修复：首阶段由 scriptStart 自动开场；非首阶段服务端在 stepStart 后会
            # 停在 selectRoleStart 等待——学生必须先主动应答一句（浏览器端用户手动输入
            # “好的”之类）+ continueCurrentStep，本阶段才会启动，否则永久卡死。
            # 但必须等服务端安静下来再发（见 _handle_stage_entry），否则被 continueSuperseded 拒绝。
            if self.step_index >= 2 and not self._stage_entry_running:
                asyncio.create_task(self._handle_stage_entry())

        elif event == "selectRoleStart":
            pass

        elif event == "selectRoleEnd":
            self.current_role = {
                "nid": payload.get("roleNid", ""),
                "nickname": payload.get("roleNickname", ""),
                "name": payload.get("roleName", ""),
            }
            if self.current_role["nid"] == "user":
                await self._handle_user_turn()

        elif event == "botAnswerStart":
            self._bot_spoke.set()  # 有角色开口 = 本阶段已启动（供阶段开场重试判定成功）

        elif event == "botAnswer":
            pass  # 流式分片忽略，统一用 botAnswerEnd 的整句

        elif event == "continueSuperseded":
            # 我方 continueCurrentStep 发得过早被服务端作废（阶段中通常自动恢复；阶段开场需重试）
            self._continue_superseded.set()

        elif event == "botAnswerEnd":
            content = payload.get("content", "")
            nid = payload.get("roleNid") or (self.current_role or {}).get("nid", "")
            nickname = (payload.get("roleNickname")
                        or (self.current_role or {}).get("nickname") or "对方")
            role_type = "system" if nid == "system" else "bot"
            self._record_turn(label=nickname, role_type=role_type, content=content)
            await self.send_continue()

        elif event == "stepEnd":
            log.info("📍 stepEnd（当前步骤结束）")

        elif event == "scriptEnd":
            self.task_completed = True
            self._done.set()
            log.info("🎉 scriptEnd：剧本已完成！")

        elif event in ("audioStart", "audioEnd", "heartbeatAck"):
            pass

        elif event == "error":
            log.error(f"❌ error: {payload}")
            self.task_completed = True
            self._done.set()

    # ---------- 循环 ----------
    async def listen_loop(self):
        try:
            async for message in self.ws:
                if isinstance(message, (bytes, bytearray)):
                    # TTS 音频帧：不保存，直接丢弃；但计入活动，让阶段开场去抖等音频停下
                    self._event_seq += 1
                    if TRACE:
                        log.info(f"📦 BIN {len(message)}B")
                else:
                    await self.handle_message(message)
        except websockets.ConnectionClosed:
            pass
        finally:
            self.is_connected = False
            self._done.set()

    async def heartbeat_loop(self):
        while self.is_connected and not self.task_completed:
            await asyncio.sleep(30)
            if not self.is_connected or self.task_completed:
                break
            try:
                await self.send_heartbeat()
            except (websockets.ConnectionClosed, OSError, RuntimeError) as err:
                log.warning(f"⚠️ 心跳发送失败: {err}")
                break

    async def run(self):
        print("\n" + "=" * 60)
        print("📢 能力训练 Pro（音频版）半交互模式")
        print("   [回车] AI 生成 | [输入文字] 手动 | [continue] 全自动 | [quit] 退出")
        print("=" * 60 + "\n")

        self.ensure_logger()
        await self.connect()

        listen_task = asyncio.create_task(self.listen_loop())
        heartbeat_task = asyncio.create_task(self.heartbeat_loop())
        try:
            await self._done.wait()
        except KeyboardInterrupt:
            pass
        finally:
            listen_task.cancel()
            heartbeat_task.cancel()
            await asyncio.gather(listen_task, heartbeat_task, return_exceptions=True)
            await self.disconnect()

        if self.task_completed:
            print("\n🎉 任务已完成！")


async def main():
    print("\n" + "=" * 60)
    print("🎓 能力训练 Pro（音频版）trainV2 协议测试工具")
    print("=" * 60)

    # 任务ID：命令行参数优先，否则用本 Pro 任务的内置默认值
    if len(sys.argv) > 1 and sys.argv[1].strip():
        CONFIG["task_id"] = sys.argv[1].strip()
        task_src = "命令行参数"
    else:
        CONFIG["task_id"] = DEFAULT_TASK_ID
        task_src = "内置默认(Pro音频任务)"

    if not CONFIG["user_id"]:
        print("\n正在获取用户信息...")
        CONFIG["user_id"] = get_user_info()

    print(f"✅ 任务ID: {CONFIG['task_id']} （来源: {task_src}）")
    print(f"✅ 用户ID: {CONFIG['user_id']}")

    client = TrainProClient()

    print("\n请选择学生档位：")
    print("1. 优秀学生 - 理解透彻、表达清晰")
    print("2. 需要引导的学生 - 基本理解但略显犹豫（默认）")
    print("3. 答非所问的学生 - 容易跑题或误解")
    profile_choice = input("\n请输入选项 (1/2/3，默认 2): ").strip()
    client.student_profile_key = {"1": "good", "2": "medium", "3": "bad"}.get(profile_choice, "medium")
    print(f"✅ 已选择: {STUDENT_PROFILES[client.student_profile_key]['label']}")

    dialogue_path = input(
        "\n可选: 输入对话记录路径（md/txt/docx/*_dialogue.json，回车跳过）: "
    ).strip()
    if dialogue_path:
        client.load_reference_dialogue(dialogue_path)

    kb_path = input("\n可选: 输入知识库路径（md/txt/docx，回车跳过）: ").strip()
    if kb_path:
        client.load_knowledge_base(kb_path)

    await client.run()


if __name__ == "__main__":
    asyncio.run(main())
