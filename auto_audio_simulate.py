#!/usr/bin/env python3
"""
语音训练平台 AI 模拟对话脚本（精简版）

相比 auto_audio_train.py 的改进：
- 发送显式的 {"event":"mute"} 结束录音，替代不稳定的“静音帧 + VAD”方案
- 状态机极简：只靠 bot_done / round_done / task_completed 三个信号驱动
- 直接复用 auto_audio_train.py 里的 TTSEngine / AudioProcessor / ConversationLogger / STUDENT_PROFILES
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Optional

import requests
import websockets
from dotenv import load_dotenv

from auto_audio_train import (
    AUDIO_CONFIG,
    CONFIG,
    STUDENT_PROFILES,
    AudioProcessor,
    ConversationLogger,
    TTSEngine,
    get_user_info,
)

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
log = logging.getLogger(__name__)


BOT_TOTAL_TIMEOUT = float(os.getenv("BOT_TOTAL_TIMEOUT", "120"))
ROUND_TIMEOUT = float(os.getenv("ROUND_TIMEOUT", "120"))


LANG_CONFIGS = {
    "zh": {
        "tts_voice": "zh-CN-XiaoxiaoNeural",
        "system_prompt": "你是一名中文能力训练助手，需要严格按照给定的学生档位扮演角色。你只能用中文回答。",
        "format_requirement": "**格式要求**: 仅返回学生回答内容，不要额外解释，控制在50字以内。",
        "fallback_answer": "好的，我明白了。",
        "confirm_examples": "   → 直接回答'是'、'好的'、'我准备好了'等",
        "choice_examples": "   → 直接说出选项，如'A'、'B'、'1'、'2'等",
    },
    "en": {
        "tts_voice": "en-US-GuyNeural",
        "system_prompt": "你是一名英语口语能力训练助手，需要严格按照给定的学生档位扮演角色。你只能用英语回答。",
        "format_requirement": "**格式要求**: 仅返回学生回答内容，不要额外解释，控制在30字以内。",
        "fallback_answer": "ok, i understand.",
        "confirm_examples": "   → 直接回答'yes'、'ok'、'i am ready'等",
        "choice_examples": "   → 直接说出选项，如'option A'、'option B'等",
    },
}


class SimulatedTrainingClient:
    def __init__(self, lang: str = "en"):
        self.lang = lang if lang in LANG_CONFIGS else "en"
        self.lang_config = LANG_CONFIGS[self.lang]
        self.tts = TTSEngine(voice=self.lang_config["tts_voice"])
        self.audio = AudioProcessor()
        self.logger = ConversationLogger(CONFIG["task_id"])

        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.is_connected = False
        self._ws_send_lock = asyncio.Lock()

        self.session_id: Optional[str] = None
        self.step_id: Optional[str] = None
        self.step_name: Optional[str] = None

        self.bot_msg_buffer: str = ""
        self.last_bot_msg: str = ""
        self.pending_user_text: Optional[str] = None
        self.pending_next_step_id: Optional[str] = None
        self.step_just_started: bool = True
        self.round_counter: int = 0
        self.task_completed: bool = False

        self.bot_done = asyncio.Event()
        self.round_done = asyncio.Event()

        self.auto_continue = False
        self.student_profile_key = "medium"

        # LLM config (mirror auto_audio_train.py)
        self.llm_api_url = os.getenv(
            "LLM_API_URL",
            "http://llm-service.polymas.com/api/openai/v1/chat/completions",
        )
        self.llm_api_key = os.getenv("LLM_API_KEY", "")
        self.llm_model = os.getenv("LLM_MODEL", "Doubao-1.5-pro-32k")
        self.llm_service_code = os.getenv("LLM_SERVICE_CODE", "SI_Ability")

        self.conversation_history: list[dict] = []
        self.reference_dialogue_content: Optional[str] = None
        self.knowledge_base_content: Optional[str] = None

    # ---------- WebSocket plumbing ----------

    async def connect(self) -> None:
        url = f"{CONFIG['ws_url']}?taskId={CONFIG['task_id']}"
        headers = {
            "Origin": "https://hike-teaching-center.polymas.com",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        }
        self.ws = await websockets.connect(
            url,
            additional_headers=headers,
            proxy=None,
            ping_interval=20,
            ping_timeout=10,
        )
        self.is_connected = True
        log.info("✅ WebSocket 已连接")

    async def disconnect(self) -> None:
        if self.ws:
            await self.ws.close()
        self.is_connected = False
        log.info("连接已断开")

    async def send_event(self, event: str, payload: dict) -> None:
        msg = json.dumps({"event": event, "payload": payload})
        async with self._ws_send_lock:
            await self.ws.send(msg)
        log.info(f"📤 {event}: {json.dumps(payload, ensure_ascii=False)}")

    async def send_audio_and_mute(self, pcm_data: bytes) -> None:
        """按 0.1s 节奏推送 PCM 分片，结束后显式发送 mute。"""
        chunk_size = AUDIO_CONFIG["pcm_chunk_size"]
        total = len(pcm_data)
        frames = (total + chunk_size - 1) // chunk_size if total else 0
        log.info(f"📤 发送音频: {frames} 帧 ({total} bytes)")

        async with self._ws_send_lock:
            for i in range(0, total, chunk_size):
                if not self.is_connected:
                    break
                chunk = pcm_data[i : i + chunk_size]
                await self.ws.send(self.audio.create_frame(chunk))
                await asyncio.sleep(AUDIO_CONFIG["chunk_interval"])
            # 显式通知服务端停止录音，对应 UI 的“点击静音”按钮
            if self.is_connected:
                await self.ws.send(json.dumps({"event": "mute", "payload": {}}))
        log.info("📤 mute 已发送")

    # ---------- Event handling ----------

    def handle_event(self, event: str, payload: dict) -> None:
        """纯同步状态转换。网络/异步副作用放到主循环里做。"""
        if event == "connected":
            self.session_id = payload.get("sessionId")
            self.step_id = payload.get("stepId")
            self.step_name = payload.get("stepName") or self.step_id
            self.step_just_started = True
            self.bot_done.clear()
            self.round_done.clear()
            log.info(f"📱 会话 {self.session_id} / 步骤 {self.step_name}")

        elif event == "botAnswerStart":
            self.bot_msg_buffer = ""
            self.bot_done.clear()
            # 对本轮而言，bot 开始讲话意味着上一轮已经彻底结束
            self.round_done.set()

        elif event == "botAnswer":
            chunk = payload.get("msg", "")
            if chunk:
                self.bot_msg_buffer += chunk

        elif event == "botAnswerEnd":
            if self.bot_msg_buffer:
                source = "runCard" if self.step_just_started else "chat"
                self.logger.log(
                    role="AI",
                    content=self.bot_msg_buffer,
                    step_name=self.step_name or "",
                    step_id=self.step_id or "",
                    round_num=self.round_counter,
                    source=source,
                    user_content=self.pending_user_text if source == "chat" else None,
                )
                self.last_bot_msg = self.bot_msg_buffer
                self.step_just_started = False
                self.pending_user_text = None
            self.bot_done.set()

        elif event == "userTextEnd":
            self.pending_user_text = payload.get("text")

        elif event == "userAudioEnd":
            # 服务器已落盘音频，继续等待 botAnswerStart / stepEnd / scriptEnd
            pass

        elif event == "stepEnd":
            self.pending_next_step_id = payload.get("nextStepId")
            next_name = payload.get("nextStepName") or payload.get("stepName") or ""
            if self.pending_next_step_id:
                log.info(
                    f"➡️ 步骤结束: {payload.get('stepName')} → 下一步 {self.pending_next_step_id}"
                )
                self.step_name = next_name or self.pending_next_step_id
                self.step_id = self.pending_next_step_id
                self.step_just_started = True
            else:
                log.info("🏁 所有步骤结束")
                self.task_completed = True
            # stepEnd 也意味着本轮结束
            self.bot_done.set()
            self.round_done.set()

        elif event == "scriptEnd":
            log.info("🎉 scriptEnd 收到，任务完成")
            self.task_completed = True
            self.bot_done.set()
            self.round_done.set()

        elif event == "error":
            log.error(f"❌ 服务器错误: {payload}")
            self.bot_done.set()
            self.round_done.set()

        elif event in {"userTextStart", "userText", "heartBeatResponse", "TTSSentenceEnd"}:
            pass

    async def listen_loop(self) -> None:
        try:
            async for raw in self.ws:
                if isinstance(raw, bytes):
                    continue  # 忽略服务端返回的二进制帧
                try:
                    data = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                event = data.get("event")
                payload = data.get("payload") or {}
                self.handle_event(event, payload)

                # connected 后立即 startScript（需要异步发送，所以放在这里）
                if event == "connected":
                    await self.send_event(
                        "startScript",
                        {
                            "sessionId": self.session_id,
                            "userId": CONFIG["user_id"],
                            "taskId": CONFIG["task_id"],
                            "schoolId": CONFIG["school_id"],
                            "stepId": self.step_id,
                        },
                    )
        except websockets.ConnectionClosed:
            self.is_connected = False

    async def heartbeat_loop(self) -> None:
        while self.is_connected:
            await asyncio.sleep(30)
            if not self.is_connected:
                break
            try:
                await self.send_event("heartBeat", {})
            except (websockets.ConnectionClosed, OSError, RuntimeError) as err:
                log.warning(f"⚠️ 心跳失败: {err}")
                return

    # ---------- LLM student generator ----------

    def _call_doubao_post(self, messages, temperature=0.7, max_tokens=200) -> Optional[str]:
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
            "top_p": 0.9,
            "frequency_penalty": 0.3,
            "presence_penalty": 0.2,
        }
        try:
            resp = requests.post(self.llm_api_url, headers=headers, json=payload, timeout=30)
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"].strip()
        except Exception as exc:
            log.error(f"❌ Doubao 调用失败: {exc}")
            return None

    def generate_ai_answer(self, bot_question: str) -> str:
        if not bot_question:
            return self.lang_config["fallback_answer"]
        profile = STUDENT_PROFILES.get(self.student_profile_key, STUDENT_PROFILES["medium"])
        system_prompt = self.lang_config["system_prompt"]

        sections = [
            "## 角色设定",
            f"学生档位: {profile['label']}",
            f"角色特征: {profile['description']}",
            f"表达风格: {profile['style']}",
            "",
            "## 问题类型识别（优先级最高）",
            "1. **确认式问题**（如“你准备好了吗？”）",
            self.lang_config["confirm_examples"],
            "2. **选择式问题**（如“选A还是B？”）",
            self.lang_config["choice_examples"],
            "",
        ]
        if self.reference_dialogue_content:
            sections += ["## 参考对话记录", self.reference_dialogue_content, ""]
        if self.knowledge_base_content:
            sections += ["## 参考知识库", self.knowledge_base_content, ""]
        if self.conversation_history:
            sections.append("## 对话历史")
            for i, turn in enumerate(self.conversation_history[-5:], 1):
                sections.append(f"第{i}轮:")
                sections.append(f"  AI提问: {turn['ai']}")
                sections.append(f"  学生回答: {turn['student']}")
            sections.append("")
        sections += [
            "## 当前问题",
            bot_question,
            "",
            "## 输出要求",
            self.lang_config["format_requirement"],
        ]
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "\n".join(sections)},
        ]
        answer = self._call_doubao_post(messages)
        return answer or self.lang_config["fallback_answer"]

    def _append_history(self, ai_text: str, student_text: str) -> None:
        self.conversation_history.append({"ai": ai_text, "student": student_text})
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]

    # ---------- Main dialogue loop ----------

    async def speak_as_student(self, text: str) -> bool:
        try:
            mp3 = await self.tts.synthesize(text)
            pcm = self.audio.mp3_to_pcm(mp3)
            await self.send_audio_and_mute(pcm)
            return True
        except Exception as exc:
            log.error(f"❌ TTS/发送失败: {exc}")
            return False

    async def _wait_for_bot(self) -> bool:
        try:
            await asyncio.wait_for(self.bot_done.wait(), timeout=BOT_TOTAL_TIMEOUT)
            return True
        except asyncio.TimeoutError:
            log.warning(f"⏰ 等待 bot 回复超过 {BOT_TOTAL_TIMEOUT}s")
            return False

    async def _wait_for_round_end(self) -> bool:
        try:
            await asyncio.wait_for(self.round_done.wait(), timeout=ROUND_TIMEOUT)
            return True
        except asyncio.TimeoutError:
            log.warning(f"⏰ mute 后等待服务器响应超过 {ROUND_TIMEOUT}s")
            return False

    async def _advance_step_if_needed(self) -> None:
        if self.pending_next_step_id:
            next_id = self.pending_next_step_id
            self.pending_next_step_id = None
            self.bot_done.clear()
            self.round_done.clear()
            await self.send_event("nextStep", {"stepId": next_id})

    async def _prompt_user(self) -> Optional[str]:
        """半交互模式：返回要发送的文本；None 代表退出。"""
        print("\n" + "-" * 60)
        print("💬 [回车] AI 生成 | [输入文字] 手动 | [continue] 全自动 | [quit] 退出")
        print("-" * 60)
        loop = asyncio.get_event_loop()
        user_input = (await loop.run_in_executor(None, input, ">> ")).strip()
        if user_input.lower() == "quit":
            return None
        if user_input.lower() == "continue":
            self.auto_continue = True
            print("🚀 切换到全自动模式")
            return self.generate_ai_answer(self.last_bot_msg)
        if user_input == "":
            return self.generate_ai_answer(self.last_bot_msg)
        return user_input

    async def run_dialogue(self, mode: str) -> None:
        while self.is_connected and not self.task_completed:
            if not await self._wait_for_bot():
                break
            if self.task_completed:
                break

            if mode == "auto" or self.auto_continue:
                student_text = self.generate_ai_answer(self.last_bot_msg)
                print(f"🤖 AI: {student_text}")
            else:
                result = await self._prompt_user()
                if result is None:
                    print("👋 退出")
                    break
                student_text = result
                print(f"🎤 学生: {student_text}")

            self._append_history(self.last_bot_msg, student_text)
            self.round_counter += 1
            self.round_done.clear()

            if not await self.speak_as_student(student_text):
                log.warning("⚠️ 本轮 TTS 失败，跳过")
                continue

            await self._wait_for_round_end()
            await self._advance_step_if_needed()

        if self.task_completed:
            print("🎉 任务已完成")

    async def run(self, mode: str = "semi") -> None:
        await self.connect()
        listen_task = asyncio.create_task(self.listen_loop())
        heartbeat_task = asyncio.create_task(self.heartbeat_loop())
        try:
            await self.run_dialogue(mode)
        except KeyboardInterrupt:
            pass
        finally:
            listen_task.cancel()
            heartbeat_task.cancel()
            await asyncio.gather(listen_task, heartbeat_task, return_exceptions=True)
            await self.disconnect()


# ============ CLI ============

def _pick_language() -> str:
    print("\n请选择测试语言：")
    print("1. 英文（默认）")
    print("2. 中文")
    choice = input("请输入选项 (1/2): ").strip()
    return {"1": "en", "2": "zh"}.get(choice, "en")


def _pick_profile() -> str:
    print("\n请选择学生档位：")
    print("1. 优秀学生")
    print("2. 需要引导的学生（默认）")
    print("3. 答非所问的学生")
    choice = input("请输入选项 (1/2/3): ").strip()
    return {"1": "good", "2": "medium", "3": "bad"}.get(choice, "medium")


def _pick_mode() -> str:
    print("\n请选择运行模式：")
    print("1. 半交互模式（回车=AI，文字=手动，continue=全自动）")
    print("2. 全自动模式（一路 AI 跑到 scriptEnd）")
    choice = input("请输入选项 (1/2): ").strip()
    return "auto" if choice == "2" else "semi"


async def main() -> None:
    print("\n" + "=" * 60)
    print("🎓 能力训练 WebSocket AI 模拟器（精简版）")
    print("=" * 60)
    user_id, school_id = get_user_info()
    CONFIG["user_id"] = user_id
    CONFIG["school_id"] = school_id
    print(f"✅ user_id={user_id}  school_id={school_id}  task_id={CONFIG['task_id']}")

    lang = _pick_language()
    profile = _pick_profile()
    mode = _pick_mode()

    client = SimulatedTrainingClient(lang=lang)
    client.student_profile_key = profile
    print(f"\n启动: lang={lang}  profile={profile}  mode={mode}")
    await client.run(mode=mode)


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        # 用 voice_test.json 对 handle_event 做回放校验
        import re

        har_path = Path(__file__).parent / "voice_test.json"
        if not har_path.exists():
            print("voice_test.json 不存在，跳过 self-test")
            sys.exit(1)

        txt = har_path.read_text()
        pat = re.compile(
            r'"type"\s*:\s*"(send|receive)"\s*,\s*"time"\s*:\s*([0-9.]+)\s*,'
            r'\s*"opcode"\s*:\s*(\d+)\s*,\s*"data"\s*:\s*"((?:[^"\\]|\\.)*)"',
            re.DOTALL,
        )

        # 用最小构造绕开 __init__ 里的网络依赖
        client = SimulatedTrainingClient.__new__(SimulatedTrainingClient)
        client.bot_msg_buffer = ""
        client.last_bot_msg = ""
        client.pending_user_text = None
        client.pending_next_step_id = None
        client.step_just_started = True
        client.round_counter = 0
        client.task_completed = False
        client.session_id = None
        client.step_id = None
        client.step_name = None
        client.bot_done = asyncio.Event()
        client.round_done = asyncio.Event()

        class _NoopLogger:
            def log(self, **kwargs):
                pass

        client.logger = _NoopLogger()

        expected_bot_msg_first = (
            "Hello and welcome to the Sanxingdui Museum! "
            "I'm Lin Xiao, your museum guide today. "
        )
        expected_next_step_id = "GEaZp9kQg3C4WoEPoxjM"

        concatenated = ""
        saw_script_end = False
        saw_step_end_next = None
        first_botend_msg = None

        for d, t, op, data in pat.findall(txt):
            if op != "1" or d != "receive":
                continue
            try:
                decoded = bytes(data, "utf-8").decode("unicode_escape")
                obj = json.loads(decoded)
            except Exception:
                continue
            ev = obj.get("event")
            pl = obj.get("payload") or {}
            client.handle_event(ev, pl)
            if ev == "botAnswer":
                concatenated += pl.get("msg", "")
            elif ev == "botAnswerEnd" and first_botend_msg is None:
                first_botend_msg = client.last_bot_msg
            elif ev == "stepEnd":
                saw_step_end_next = pl.get("nextStepId")
            elif ev == "scriptEnd":
                saw_script_end = True

        print(f"concatenated prefix match: {concatenated.startswith(expected_bot_msg_first)}")
        print(f"stepEnd.nextStepId == {expected_next_step_id}: {saw_step_end_next == expected_next_step_id}")
        print(f"scriptEnd flipped task_completed: {client.task_completed}")
        print(f"first botAnswerEnd buffered text (first 80): {first_botend_msg[:80] if first_botend_msg else 'None'}")
        assert concatenated.startswith(expected_bot_msg_first)
        assert saw_step_end_next == expected_next_step_id
        assert client.task_completed is True
        assert saw_script_end is True
        print("✅ self-test passed")
        sys.exit(0)

    asyncio.run(main())
