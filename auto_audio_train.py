#!/usr/bin/env python3
"""
语音训练平台测试工具 powered by Richard Zhang
"""

import asyncio
import websockets
import json
import logging
import io
import os
import sys
import math
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, List
from dotenv import load_dotenv
import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
log = logging.getLogger(__name__)

# ============ 配置 ============
# 加载环境变量
load_dotenv()

CONFIG = {
    "ws_url": "wss://cloudapi.polymas.com/ai-tools/ws/v2/trainFlow",
    "task_id": os.getenv("TASK_ID"),
    "user_id": None,  # 稍后通过 API 获取
    "school_id": None,  # 稍后通过 API 获取
}

def get_user_info():
    """
    调用 API 获取用户和学校信息
    失败时退出程序并提示错误
    """
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
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, headers=headers)
        response.raise_for_status()  # 检查 HTTP 错误

        data = response.json()

        if data.get("code") != 200 or not data.get("success"):
            print(f"❌ API 调用失败：{data.get('msg', '未知错误')}")
            sys.exit(1)

        user_id = data["data"]["userNid"]
        school_id = data["data"]["schoolInfo"]["nid"]

        return user_id, school_id

    except requests.exceptions.RequestException as e:
        print(f"❌ 网络请求失败：{e}")
        print("请检查网络连接和认证信息（AUTHORIZATION, COOKIE）")
        sys.exit(1)
    except (KeyError, TypeError) as e:
        print(f"❌ API 响应格式错误：{e}")
        print("响应数据格式不符合预期")
        sys.exit(1)

AUDIO_CONFIG = {
    "sample_rate": 16000,
    "channels": 1,
    "sample_width": 2,
    "pcm_chunk_size": 3200,
    "frame_header": bytes([0x11, 0x20, 0x10, 0x00, 0x00, 0x00, 0x0c, 0x80]),
    "chunk_interval": 0.1,
    "silence_frames": 15,
}

# ============ 日志记录器 ============
class ConversationLogger:
    def __init__(self, task_id: str):
        log_dir = Path("./audio_logs")
        log_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = log_dir / f"task_{task_id}_{timestamp}.txt"

        # 保存task_id和创建时间用于头部显示
        self.task_id = task_id
        self.creation_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 创建日志文件并写入头部
        with open(self.log_file, 'w', encoding='utf-8') as f:
            f.write("对话记录\n")
            f.write(f"日志创建时间: {self.creation_time}\n")
            f.write(f"task_id: {task_id}\n")
            f.write("="*60 + "\n")

    def log(self, role: str, content: str, step_name: str, step_id: str, round_num: int, source: str, user_content: str = None):
        """
        记录对话日志

        参数:
            role: 角色 ("AI" 或 "用户")
            content: 对话内容（AI的回复）
            step_name: 步骤名称
            step_id: 步骤ID
            round_num: 轮次号（0表示无轮次，如 runCard 的初始消息）
            source: 来源 ("runCard" 或 "chat")
            user_content: 用户消息内容（可选，仅在同一轮对话时提供）
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 构建第一行
        first_line = f"[{timestamp}] Step: {step_name} | step_id: {step_id}"
        if round_num > 0:
            first_line += f" | 第 {round_num} 轮"
        first_line += f" | 来源: {source}"

        # 写入日志文件
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(first_line + "\n")

            # 如果有用户消息（chat模式），先写用户消息
            if user_content:
                f.write(f"用户: {user_content}\n")
                print(f"\n👤 用户: {user_content}")

            # 写入AI消息
            f.write(f"AI: {content}\n")
            f.write("-"*80 + "\n")

        # 终端输出AI消息
        print(f"🤖 AI: {content}")

# ============ 音频处理 ============
class AudioProcessor:
    def __init__(self):
        self.sample_rate = AUDIO_CONFIG["sample_rate"]
        self.channels = AUDIO_CONFIG["channels"]
        self.sample_width = AUDIO_CONFIG["sample_width"]
        self.pcm_chunk_size = AUDIO_CONFIG["pcm_chunk_size"]
        self.frame_header = AUDIO_CONFIG["frame_header"]

        # 检测并选择音频后端
        self.backend = self._detect_audio_backend()
        log.info(f"🎵 音频后端: {self.backend}")

    def _detect_audio_backend(self) -> str:
        """检测可用的音频后端"""
        backend_preference = os.getenv("AUDIO_BACKEND", "auto").lower()

        if backend_preference == "pydub":
            return "pydub"
        elif backend_preference == "miniaudio":
            return "miniaudio"

        # auto 模式：优先 miniaudio
        try:
            import miniaudio
            import samplerate
            return "miniaudio"
        except ImportError:
            log.warning("⚠️ miniaudio 不可用，回退到 pydub")
            return "pydub"

    def mp3_to_pcm(self, mp3_data: bytes) -> bytes:
        """
        将 MP3 转换为 PCM
        支持两种后端：
        - miniaudio: 无需 ffmpeg (推荐)
        - pydub: 需要 ffmpeg (备选)
        """
        if self.backend == "miniaudio":
            return self._mp3_to_pcm_miniaudio(mp3_data)
        else:
            return self._mp3_to_pcm_pydub(mp3_data)

    def _mp3_to_pcm_miniaudio(self, mp3_data: bytes) -> bytes:
        """使用 miniaudio + samplerate，无需 ffmpeg"""
        try:
            import miniaudio
            import numpy as np

            # 解码 MP3
            decoded = miniaudio.decode(mp3_data, output_format=miniaudio.SampleFormat.SIGNED16)

            audio_array = np.frombuffer(decoded.samples, dtype=np.int16)

            # 转单声道
            if decoded.nchannels == 2:
                audio_array = audio_array.reshape(-1, 2).mean(axis=1).astype(np.int16)
            elif decoded.nchannels != 1:
                raise ValueError(f"不支持的声道数: {decoded.nchannels}")

            # 重采样
            if decoded.sample_rate != self.sample_rate:
                import samplerate
                # samplerate 需要归一化的浮点数组 [-1.0, 1.0]
                audio_float = audio_array.astype(np.float32) / 32768.0
                ratio = self.sample_rate / decoded.sample_rate
                audio_resampled = samplerate.resample(audio_float, ratio, 'sinc_fastest')
                audio_array = (audio_resampled * 32768.0).astype(np.int16)

            return audio_array.tobytes()

        except Exception as e:
            log.error(f"❌ miniaudio 转换失败: {e}，尝试回退到 pydub")
            # 回退到 pydub
            self.backend = "pydub"
            return self._mp3_to_pcm_pydub(mp3_data)

    def _mp3_to_pcm_pydub(self, mp3_data: bytes) -> bytes:
        """使用 pydub + ffmpeg (备选方案)"""
        from pydub import AudioSegment
        audio = AudioSegment.from_mp3(io.BytesIO(mp3_data))
        audio = audio.set_frame_rate(self.sample_rate)
        audio = audio.set_channels(self.channels)
        audio = audio.set_sample_width(self.sample_width)
        return audio.raw_data
    
    def create_frame(self, pcm_chunk: bytes) -> bytes:
        if len(pcm_chunk) < self.pcm_chunk_size:
            pcm_chunk = pcm_chunk + b'\x00' * (self.pcm_chunk_size - len(pcm_chunk))
        return self.frame_header + pcm_chunk
    
    def create_silence_frame(self) -> bytes:
        silence = b'\x00' * self.pcm_chunk_size
        return self.frame_header + silence
    
    def create_frames(self, pcm_data: bytes) -> List[bytes]:
        frames = []
        for i in range(0, len(pcm_data), self.pcm_chunk_size):
            pcm_chunk = pcm_data[i:i + self.pcm_chunk_size]
            frames.append(self.create_frame(pcm_chunk))
        
        for _ in range(AUDIO_CONFIG["silence_frames"]):
            frames.append(self.create_silence_frame())
        
        return frames

# ============ TTS引擎 ============
class TTSEngine:
    def __init__(self, voice: str = "en-US-GuyNeural"):
        self.voice = voice
    
    async def synthesize(self, text: str) -> bytes:
        import edge_tts
        communicate = edge_tts.Communicate(text, self.voice)
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
        return audio_data

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
        "style": "语气略显犹豫，能覆盖核心内容，但会提出 1-2 个不确定点或寻求老师建议。",
    },
    "bad": {
        "label": "答非所问的学生",
        "description": "理解偏差，常常跑题或只复述与问题弱相关的信息。",
        "style": "语气随意，容易偏离重点或答非所问。",
    }
}

# ============ WebSocket客户端 ============
class TrainingClient:
    def __init__(self):
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.logger = ConversationLogger(CONFIG["task_id"])  # 传入 task_id
        self.tts = TTSEngine()
        self.audio = AudioProcessor()

        # WebSocket 发送互斥锁：避免音频帧与控制消息（nextStep/heartBeat 等）交错发送
        self._ws_send_lock = asyncio.Lock()

        self.session_id = None
        self.step_id = None
        self.step_name = None
        self.is_connected = False
        self.bot_speaking = False
        self.waiting_response = False
        self.current_bot_msg = ""
        self.current_history_id = ""
        self.task_completed = False

        # 新增状态变量
        self.round_counter = 0  # 轮次计数器
        self.step_just_started = False  # 标记是否刚进入新步骤
        self.pending_user_message = None  # 缓存用户消息，等待与AI回复一起记录

        # 半交互模式相关
        self.auto_continue = False  # 全自动模式标志

        # 超时重试相关
        self.last_sent_text = None           # 记录最后发送的消息，用于重试
        self.max_retries = int(os.getenv("MAX_RETRIES", "3"))  # 最大重试次数
        self.base_timeout = float(os.getenv("BASE_TIMEOUT", "90"))  # 基础超时时间（秒）
        self.heartbeat_without_response = 0  # 无响应的心跳计数

        # 音频发送控制：用于在 userAudioEnd/stepEnd/botAnswerStart 时提前停止发送，避免跨步骤串音触发再次识别
        self._audio_stop_event: Optional[asyncio.Event] = None
        self._audio_sending = False
        self._audio_sending_done = asyncio.Event()
        self._audio_sending_done.set()
        self._next_step_task: Optional[asyncio.Task] = None

        # Bot 回复超时控制：避免 botAnswerStart 后一直不结束导致永远不重试
        self.bot_idle_timeout = float(os.getenv("BOT_IDLE_TIMEOUT", "45"))  # bot无输出超时（秒）
        self.bot_total_timeout = float(os.getenv("BOT_TOTAL_TIMEOUT", "240"))  # bot回复总时长上限（秒）
        self.bot_answer_started_at: Optional[float] = None
        self.last_bot_activity_at: Optional[float] = None

        # 学生档位配置
        self.student_profile_key = "medium"  # 默认：需要引导的学生

        # Doubao API 配置
        self.model_type = os.getenv("MODEL_TYPE", "doubao_post")
        self.llm_api_url = os.getenv(
            "LLM_API_URL",
            "http://llm-service.polymas.com/api/openai/v1/chat/completions"
        )
        self.llm_api_key = os.getenv("LLM_API_KEY", "")
        self.llm_model = os.getenv("LLM_MODEL", "Doubao-1.5-pro-32k")
        self.llm_service_code = os.getenv("LLM_SERVICE_CODE", "SI_Ability")

        # 对话历史（用于提供上下文）
        self.conversation_history = []
    
    async def connect(self):
        url = f"{CONFIG['ws_url']}?taskId={CONFIG['task_id']}"
        headers = {
            "Origin": "https://hike-teaching-center.polymas.com",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        }
        
        self.ws = await websockets.connect(
            url, additional_headers=headers, proxy=None,
            ping_interval=20, ping_timeout=10
        )
        self.is_connected = True
        log.info("✅ WebSocket连接成功")
    
    async def disconnect(self):
        if self.ws:
            await self.ws.close()
        self.is_connected = False
        log.info("连接已断开")
    
    async def send_json(self, event: str, payload: dict):
        msg = json.dumps({"event": event, "payload": payload})
        async with self._ws_send_lock:
            await self.ws.send(msg)
        log.info(f"📤 {event}: {json.dumps(payload, ensure_ascii=False)}")
    
    async def start_script(self):
        await self.send_json("startScript", {
            "sessionId": self.session_id,
            "userId": CONFIG["user_id"],
            "taskId": CONFIG["task_id"],
            "schoolId": CONFIG["school_id"],
            "stepId": self.step_id
        })
    
    async def send_next_step(self, step_id: str):
        """发送 nextStep 确认进入下一步"""
        await self.send_json("nextStep", {"stepId": step_id})
    
    async def send_heartbeat(self):
        await self.send_json("heartBeat", {})
    
    def _request_stop_audio_sending(self, reason: str):
        stop_event = self._audio_stop_event
        if stop_event and not stop_event.is_set():
            stop_event.set()
            log.info(f"🛑 停止发送音频: {reason}")

    async def send_audio_frames(self, pcm_data: bytes):
        # 为本次发送创建 stop 事件（用于提前终止）
        self._audio_stop_event = asyncio.Event()
        stop_event = self._audio_stop_event

        self._audio_sending = True
        self._audio_sending_done.clear()

        chunk_size = AUDIO_CONFIG["pcm_chunk_size"]
        audio_frame_count = int(math.ceil(len(pcm_data) / chunk_size)) if pcm_data else 0

        log.info(f"📤 发送: {audio_frame_count} 音频帧 + {AUDIO_CONFIG['silence_frames']} 静音帧(最多)")

        try:
            async with self._ws_send_lock:
                # 先发送语音内容帧
                for i in range(0, len(pcm_data), chunk_size):
                    if not self.is_connected or stop_event.is_set():
                        break

                    pcm_chunk = pcm_data[i:i + chunk_size]
                    await self.ws.send(self.audio.create_frame(pcm_chunk))
                    await asyncio.sleep(AUDIO_CONFIG["chunk_interval"])

                # 再发送静音帧（允许提前停止）
                for _ in range(AUDIO_CONFIG["silence_frames"]):
                    if not self.is_connected or stop_event.is_set():
                        break

                    await self.ws.send(self.audio.create_silence_frame())
                    await asyncio.sleep(AUDIO_CONFIG["chunk_interval"])

        finally:
            self._audio_sending = False
            self._audio_sending_done.set()
            log.info("✅ 音频发送完成")

    def _call_doubao_post(self, messages, temperature=0.7, max_tokens=1000):
        """
        使用 HTTP POST 方式调用 Doubao API

        参数:
            messages: 消息列表 [{"role": "system", "content": "..."}, ...]
            temperature: 温度参数 (0-1)
            max_tokens: 最大输出长度

        返回:
            AI 生成的文本，失败返回 None
        """
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
            log.error(f"❌ Doubao API 调用失败: {str(e)}")
            return None
        except (KeyError, IndexError) as e:
            log.error(f"❌ 解析响应失败: {str(e)}")
            return None

    def generate_ai_answer(self, bot_question: str) -> str:
        """
        使用 Doubao API 生成学生回答

        参数:
            bot_question: Bot 的提问

        返回:
            AI 生成的学生回答
        """
        if not self.llm_api_url or not self.llm_api_key:
            log.error("❌ Doubao API 未配置")
            return "好的"

        try:
            # 获取学生档位信息
            profile_info = STUDENT_PROFILES.get(self.student_profile_key, STUDENT_PROFILES["medium"])

            # 构建系统提示
            system_prompt = "你是一名英语口语能力训练助手，需要严格按照给定的学生档位扮演角色。你只能用英语回答。"

            # 构建用户提示
            sections = [
                "## 角色设定",
                f"学生档位: {profile_info['label']}",
                f"角色特征: {profile_info['description']}",
                f"表达风格: {profile_info['style']}",
                "",
                "## 问题类型识别（优先级最高）",
                "如果当前问题属于以下类型，请优先直接回答，不需要强制体现性格特点：",
                "1. **确认式问题**: 如'你准备好了吗？请回复是或否'",
                "   → 直接回答'yes'、'ok'、'i am ready'等",
                "2. **选择式问题**: 如'你选择A还是B？'、'请选择1/2/3'",
                "   → 直接说出选项，如'option A'、'option B'、'option C'等",
                "",
            ]

            # 添加对话历史
            if self.conversation_history:
                sections.append("## 对话历史（按时间顺序）")
                for i, turn in enumerate(self.conversation_history[-5:], 1):  # 只保留最近5轮
                    sections.append(f"第{i}轮:")
                    sections.append(f"  AI提问: {turn['ai']}")
                    sections.append(f"  学生回答: {turn['student']}")
                sections.append("")

            sections.extend([
                "## 当前问题",
                bot_question,
                "",
                "## 输出要求",
                "**优先级1**: 如果是封闭式问题（确认式/选择式），直接简短回答",
                "**优先级2**: 如果是开放式问题，适度融入学生档位特点",
                "**格式要求**: 仅返回学生回答内容，不要额外解释，控制在30字以内。",
                ""
            ])

            user_message = "\n".join(sections)

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]

            # 调用 Doubao API
            log.info("🔄 使用 Doubao POST API 生成回答...")
            answer = self._call_doubao_post(messages, temperature=0.7, max_tokens=200)

            if answer:
                return answer
            else:
                # 回退到简单回答
                return "ok, i understand."

        except Exception as e:
            log.error(f"❌ 生成回答失败: {str(e)}")
            return "ok, i understand."

    async def speak(self, text: str):
        self.last_sent_text = text  # 记录发送内容，用于重试
        log.info(f"🎤 准备发送: {text}")
        
        while self.bot_speaking:
            await asyncio.sleep(0.1)
        
        try:
            log.info("🔄 生成语音...")
            mp3_data = await self.tts.synthesize(text)
            log.info(f"✅ MP3: {len(mp3_data)} bytes")
            
            pcm_data = self.audio.mp3_to_pcm(mp3_data)
            log.info(f"✅ PCM: {len(pcm_data)} bytes")
            
            self.waiting_response = True
            await self.send_audio_frames(pcm_data)
            
            log.info("⏳ 等待响应...")
            
        except Exception as e:
            log.error(f"❌ 错误: {e}")
            import traceback
            traceback.print_exc()
    
    async def handle_message(self, message):
        if isinstance(message, bytes):
            return
        
        try:
            data = json.loads(message)
            event = data.get("event")
            payload = data.get("payload", {})
            
            if event == "connected":
                self.session_id = payload.get("sessionId")
                self.step_id = payload.get("stepId")
                self.step_name = payload.get("stepName")
                log.info(f"📱 会话: {self.session_id}")
                log.info(f"📍 步骤: {self.step_name} ({self.step_id})")
                self.step_just_started = True  # 标记新步骤开始
                await self.start_script()
                
            elif event == "botAnswerStart":
                self.bot_speaking = True
                self.current_bot_msg = ""
                # 注意：不要在这里设置 waiting_response = False
                # 应该等到 botAnswerEnd 时才认为响应完成，确保 current_bot_msg 已完整接收
                self.heartbeat_without_response = 0  # 重置心跳计数
                self._request_stop_audio_sending("botAnswerStart")
                now = time.monotonic()
                self.bot_answer_started_at = now
                self.last_bot_activity_at = now
                log.info("🤖 Bot开始回复...")

            elif event == "botAnswer":
                msg = payload.get("msg", "")
                self.current_history_id = payload.get("historyId", "")
                self.current_bot_msg += msg
                self.last_bot_activity_at = time.monotonic()
                
            elif event == "botAnswerEnd":
                if self.current_bot_msg:
                    # 确定来源
                    source = "runCard" if self.step_just_started else "chat"

                    # 记录日志
                    self.logger.log(
                        role="AI",
                        content=self.current_bot_msg,
                        step_name=self.step_name,
                        step_id=self.step_id,
                        round_num=self.round_counter,
                        source=source,
                        user_content=self.pending_user_message if source == "chat" else None
                    )

                    # 重置 step_just_started 标志
                    if self.step_just_started:
                        self.step_just_started = False

                    # 清空缓存的用户消息
                    self.pending_user_message = None

                    # 保留 current_bot_msg 不清空，供半交互模式的 AI 生成回答使用
                    # 在 botAnswerStart 时会重新清空

                self.bot_speaking = False
                self.waiting_response = False
                self.heartbeat_without_response = 0  # 重置心跳计数
                self.bot_answer_started_at = None
                self.last_bot_activity_at = time.monotonic()

            elif event == "userTextStart":
                log.info("🎙️ ✅ 开始识别!")
                
            elif event == "userText":
                log.info(f"🎙️ 识别: {payload.get('text')}")
                
            elif event == "userTextEnd":
                text = payload.get("text", "")
                history_id = payload.get("historyId", "")

                # 轮次计数增加
                self.round_counter += 1

                # 缓存用户消息，等待与AI回复一起记录
                self.pending_user_message = text

                log.info(f"✅ 识别完成: {text}")
                
            elif event == "userAudioEnd":
                log.info(f"🔗 音频已保存")
                self._request_stop_audio_sending("userAudioEnd")
                
            elif event == "stepEnd":
                # 关键：收到 stepEnd，从中获取 nextStepId
                current_step = payload.get("stepName", "")
                next_step_id = payload.get("nextStepId")
                next_step_name = payload.get("nextStepName", "")  # 尝试获取下一步骤名称
                end_type = payload.get("endType", "")
                step_desc = payload.get("stepDescription", "")

                # step 结束说明服务器已经不再需要当前音频流，停止继续发送避免跨步骤触发识别
                self._request_stop_audio_sending("stepEnd")

                log.info(f"📍 步骤结束: {current_step}")
                log.info(f"   结束类型: {end_type}")
                log.info(f"   步骤描述: {step_desc[:50]}...")

                if next_step_id:
                    log.info(f"➡️ 下一步: {next_step_id}")
                    self.step_id = next_step_id

                    # 更新步骤名称（如果服务器没有返回，用step_id作为临时名称）
                    if next_step_name:
                        self.step_name = next_step_name
                    else:
                        self.step_name = current_step

                    # 轮次计数器不重置，持续累加

                    # 标记新步骤开始
                    self.step_just_started = True

                    # 清空缓存的用户消息（跨步骤不携带）
                    self.pending_user_message = None

                    # 发送 nextStep 确认（等待音频发送结束后再发，避免音频串到下一步触发再次识别）
                    if self._next_step_task and not self._next_step_task.done():
                        self._next_step_task.cancel()
                    self._next_step_task = asyncio.create_task(self._send_next_step_safely(next_step_id))
                else:
                    log.info("🏁 任务完成，没有下一步了！")
                    self.task_completed = True
                
            elif event == "taskEnd":
                log.info("🎉 整个任务已完成！")
                self.task_completed = True
                self.waiting_response = False
                self._request_stop_audio_sending("taskEnd")
                
            elif event == "error":
                log.error(f"❌ 错误: {payload}")
                # 出错时尽量解锁等待状态，避免永远卡在 bot_speaking
                self.bot_speaking = False
                self.bot_answer_started_at = None
                self.last_bot_activity_at = time.monotonic()
                
        except json.JSONDecodeError:
            pass
    
    async def listen_loop(self):
        try:
            async for message in self.ws:
                await self.handle_message(message)
        except websockets.ConnectionClosed:
            self.is_connected = False

    async def _send_next_step_safely(self, step_id: str):
        """
        等待当前音频发送结束后再发送 nextStep。
        避免在发送音频帧过程中切步，导致剩余音频被当作下一步输入触发再次识别/卡死。
        """
        try:
            await asyncio.wait_for(self._audio_sending_done.wait(), timeout=10)
        except asyncio.TimeoutError:
            log.warning("⚠️ 等待音频发送结束超时，仍尝试发送 nextStep")
        await self.send_next_step(step_id)

    async def wait_for_response_with_retry(self, text: str) -> bool:
        """等待服务器响应，超时后自动重试（但如果 Bot 正在回复则继续等待）"""
        retry_count = 0

        while retry_count <= self.max_retries:
            timeout = self.base_timeout
            start_wait = time.monotonic()

            while True:
                await asyncio.sleep(0.5)

                # 响应已完成（botAnswerEnd 触发）
                if not self.waiting_response:
                    return True

                now = time.monotonic()

                # Bot 正在回复：如果长时间无输出/总时长过长，判定卡住，允许重试
                if self.bot_speaking:
                    if self.last_bot_activity_at and (now - self.last_bot_activity_at) >= self.bot_idle_timeout:
                        log.warning(f"⚠️ Bot 已 {int(now - self.last_bot_activity_at)} 秒无输出，判定卡住")
                        self.bot_speaking = False
                        break
                    if self.bot_answer_started_at and (now - self.bot_answer_started_at) >= self.bot_total_timeout:
                        log.warning(f"⚠️ Bot 回复超过 {int(now - self.bot_answer_started_at)} 秒仍未结束，判定卡住")
                        self.bot_speaking = False
                        break
                    continue

                # 还没进入 botAnswerStart：按基础超时判断
                if (now - start_wait) >= timeout:
                    break

            log.warning(f"⏰ 等待 {int(timeout)} 秒无响应")
            retry_count += 1

            if retry_count <= self.max_retries:
                log.warning(f"⚠️ 第 {retry_count} 次重试...")
                self.waiting_response = True
                await self.speak(text)

        log.error(f"❌ 服务器无响应，已重试 {self.max_retries} 次")
        self.waiting_response = False
        return False

    async def heartbeat_loop(self):
        while self.is_connected:
            await asyncio.sleep(30)
            if self.is_connected:
                try:
                    await self.send_heartbeat()
                    # 监控无响应的心跳次数
                    if self.waiting_response:
                        self.heartbeat_without_response += 1
                        if self.heartbeat_without_response >= 3:  # 90秒无响应
                            log.warning(f"⚠️ 服务器已 {self.heartbeat_without_response * 30} 秒无响应")
                    else:
                        self.heartbeat_without_response = 0
                except:
                    pass

    async def semi_interactive_mode(self):
        """
        半交互模式：
        - 回车 = AI 自动生成回答
        - 输入内容 = 使用用户输入
        - continue = 切换到全自动模式
        - quit = 退出
        """
        print("\n" + "="*60)
        print("📢 半交互模式")
        print("="*60)
        print("说明：")
        print("  - [回车] AI 自动生成回答")
        print("  - [输入文字] 使用你的回答")
        print("  - [continue] 切换到全自动模式")
        print("  - [quit] 退出")
        print("="*60 + "\n")

        while self.is_connected and not self.task_completed:
            try:
                if self.auto_continue:
                    # 全自动模式：直接生成AI回答
                    print(f"\n🤖 [全自动模式] 正在生成AI回答...")
                    await asyncio.sleep(1)  # 稍等一下让用户看到 Bot 消息

                    # 生成 AI 回答
                    ai_answer = self.generate_ai_answer(self.current_bot_msg)
                    print(f"🤖 AI: {ai_answer}")

                    # 保存对话历史
                    self.conversation_history.append({
                        "ai": self.current_bot_msg,
                        "student": ai_answer
                    })
                    # 限制历史长度
                    if len(self.conversation_history) > 10:
                        self.conversation_history = self.conversation_history[-10:]

                    await self.speak(ai_answer)
                else:
                    # 半交互模式：等待用户输入
                    print("\n" + "-" * 60)
                    print("💬 请输入回答:")
                    print("   [回车] AI 生成 | [输入文字] 手动 | [continue] 全自动 | [quit] 退出")
                    print("-" * 60)

                    user_input = await asyncio.get_event_loop().run_in_executor(
                        None, input, ">> "
                    )

                    user_input = user_input.strip()

                    if user_input.lower() == 'quit':
                        print("👋 用户主动退出")
                        break

                    if user_input.lower() == 'continue':
                        print("\n🚀 切换到全自动模式...")
                        self.auto_continue = True
                        # 本轮也自动回答
                        ai_answer = self.generate_ai_answer(self.current_bot_msg)
                        print(f"🤖 AI: {ai_answer}")

                        # 保存对话历史
                        self.conversation_history.append({
                            "ai": self.current_bot_msg,
                            "student": ai_answer
                        })
                        # 限制历史长度
                        if len(self.conversation_history) > 10:
                            self.conversation_history = self.conversation_history[-10:]

                        await self.speak(ai_answer)
                    elif user_input == "":
                        # 回车：使用 AI 生成
                        print(f"\n🤖 正在生成AI回答...")
                        ai_answer = self.generate_ai_answer(self.current_bot_msg)
                        print(f"🤖 AI: {ai_answer}")

                        # 保存对话历史
                        self.conversation_history.append({
                            "ai": self.current_bot_msg,
                            "student": ai_answer
                        })
                        # 限制历史长度
                        if len(self.conversation_history) > 10:
                            self.conversation_history = self.conversation_history[-10:]

                        await self.speak(ai_answer)
                    else:
                        # 用户手动输入
                        print(f"\n👤 用户: {user_input}")

                        # 保存对话历史
                        self.conversation_history.append({
                            "ai": self.current_bot_msg,
                            "student": user_input
                        })
                        # 限制历史长度
                        if len(self.conversation_history) > 10:
                            self.conversation_history = self.conversation_history[-10:]

                        await self.speak(user_input)

                # 等待响应（支持超时重试）
                success = await self.wait_for_response_with_retry(self.last_sent_text)
                if not success:
                    log.warning("⚠️ 服务器持续无响应，继续下一轮...")

            except EOFError:
                break

        if self.task_completed:
            print("\n🎉 任务已完成！")

    async def interactive_mode(self):
        """纯手动交互模式（保留原功能）"""
        print("\n" + "="*60)
        print("📢 手动交互模式 ")
        print("   ✅ 自动处理 stepEnd → nextStep")
        print("   输入文字按回车发送，quit 退出")
        print("="*60 + "\n")
        
        while self.is_connected and not self.task_completed:
            try:
                user_input = await asyncio.get_event_loop().run_in_executor(
                    None, input, "💬 输入: "
                )
                
                if user_input.lower() == 'quit':
                    break
                
                if user_input.strip():
                    await self.speak(user_input)

                    # 等待响应（支持超时重试）
                    success = await self.wait_for_response_with_retry(self.last_sent_text)
                    if not success:
                        log.warning("⚠️ 服务器持续无响应，继续下一轮...")
                    
            except EOFError:
                break
        
        if self.task_completed:
            print("\n🎉 任务已完成！")
    
    async def run(self, mode='semi'):
        """
        运行客户端

        参数:
            mode: 'semi' = 半交互模式, 'manual' = 纯手动模式
        """
        await self.connect()

        listen_task = asyncio.create_task(self.listen_loop())
        heartbeat_task = asyncio.create_task(self.heartbeat_loop())

        try:
            if mode == 'manual':
                await self.interactive_mode()
            else:
                await self.semi_interactive_mode()
        except KeyboardInterrupt:
            pass
        finally:
            heartbeat_task.cancel()
            await self.disconnect()


async def main():
    # 先获取用户信息
    print("\n" + "="*60)
    print("🎓 口语能力训练平台测试工具")
    print("="*60)
    print("\n正在获取用户信息...")

    user_id, school_id = get_user_info()
    CONFIG["user_id"] = user_id
    CONFIG["school_id"] = school_id

    print(f"✅ 用户ID: {user_id}")
    print(f"✅ 学校ID: {school_id}")
    print(f"✅ 任务ID: {CONFIG['task_id']}")

    print("\n流程:")
    print("  1. 用户发送音频")
    print("  2. 服务器: userTextStart → userTextEnd → userAudioEnd")
    print("  3. 服务器: stepEnd (包含 nextStepId)")
    print("  4. 客户端: nextStep (确认进入下一步)")
    print("  5. 服务器: botAnswerStart → botAnswerEnd")

    # 选择模式
    print("\n请选择运行模式：")
    print("1. 半交互模式（推荐）- 回车AI回答，输入手动回答")
    print("2. 纯手动模式 - 只能手动输入")

    mode_choice = input("\n请输入选项 (1/2，默认 1): ").strip()
    # mode_choice = "1"

    client = TrainingClient()

    # 如果选择半交互模式，让用户选择学生档位
    if mode_choice != "2":
        print("\n请选择学生档位：")
        print("1. 优秀学生 - 理解透彻、表达清晰")
        print("2. 需要引导的学生 - 基本理解但略显犹豫（默认）")
        print("3. 答非所问的学生 - 容易跑题或误解")

        profile_choice = input("\n请输入选项 (1/2/3，默认 2): ").strip()
        # profile_choice = "2"

        profile_map = {
            "1": "good",
            "2": "medium",
            "3": "bad"
        }
        client.student_profile_key = profile_map.get(profile_choice, "medium")

        selected_profile = STUDENT_PROFILES[client.student_profile_key]
        print(f"\n✅ 已选择: {selected_profile['label']}")
        print(f"   特征: {selected_profile['description']}")

    if mode_choice == "2":
        await client.run(mode='manual')
    else:
        await client.run(mode='semi')


if __name__ == "__main__":
    asyncio.run(main())
