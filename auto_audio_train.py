#!/usr/bin/env python3
"""
语音训练平台测试工具 - 正确处理 stepEnd → nextStep 流程
"""

import asyncio
import websockets
import json
import logging
import io
import os
import sys
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
        log_dir = Path("./logs")
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

    def log(self, role: str, content: str, step_name: str, step_id: str, round_num: int, source: str):
        """
        记录对话日志

        参数:
            role: 角色 ("AI" 或 "用户")
            content: 对话内容
            step_name: 步骤名称
            step_id: 步骤ID
            round_num: 轮次号（0表示无轮次，如 runCard 的初始消息）
            source: 来源 ("runCard" 或 "chat")
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
            f.write(f"{role}: {content}\n")
            f.write("-"*80 + "\n")

        # 终端输出
        if role == "AI":
            print(f"\n🤖 AI: {content}")
        elif role == "用户":
            print(f"\n👤 用户: {content}")

# ============ 音频处理 ============
class AudioProcessor:
    def __init__(self):
        self.sample_rate = AUDIO_CONFIG["sample_rate"]
        self.channels = AUDIO_CONFIG["channels"]
        self.sample_width = AUDIO_CONFIG["sample_width"]
        self.pcm_chunk_size = AUDIO_CONFIG["pcm_chunk_size"]
        self.frame_header = AUDIO_CONFIG["frame_header"]
    
    def mp3_to_pcm(self, mp3_data: bytes) -> bytes:
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

# ============ WebSocket客户端 ============
class TrainingClient:
    def __init__(self):
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.logger = ConversationLogger(CONFIG["task_id"])  # 传入 task_id
        self.tts = TTSEngine()
        self.audio = AudioProcessor()

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
    
    async def send_audio_frames(self, pcm_data: bytes):
        frames = self.audio.create_frames(pcm_data)
        audio_frames = len(frames) - AUDIO_CONFIG["silence_frames"]
        
        log.info(f"📤 发送: {audio_frames} 音频帧 + {AUDIO_CONFIG['silence_frames']} 静音帧")
        
        for frame in frames:
            if not self.is_connected:
                break
            await self.ws.send(frame)
            await asyncio.sleep(AUDIO_CONFIG["chunk_interval"])
        
        log.info("✅ 音频发送完成")
    
    async def speak(self, text: str):
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
                log.info("🤖 Bot开始回复...")
                
            elif event == "botAnswer":
                msg = payload.get("msg", "")
                self.current_history_id = payload.get("historyId", "")
                self.current_bot_msg += msg
                
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
                        source=source
                    )

                    # 重置 step_just_started 标志
                    if self.step_just_started:
                        self.step_just_started = False

                self.bot_speaking = False
                self.waiting_response = False
                self.current_bot_msg = ""
                
            elif event == "userTextStart":
                log.info("🎙️ ✅ 开始识别!")
                
            elif event == "userText":
                log.info(f"🎙️ 识别: {payload.get('text')}")
                
            elif event == "userTextEnd":
                text = payload.get("text", "")
                history_id = payload.get("historyId", "")

                # 轮次计数增加
                self.round_counter += 1

                # 记录用户消息
                self.logger.log(
                    role="用户",
                    content=text,
                    step_name=self.step_name,
                    step_id=self.step_id,
                    round_num=self.round_counter,
                    source="chat"
                )

                log.info(f"✅ 识别完成: {text}")
                
            elif event == "userAudioEnd":
                log.info(f"🔗 音频已保存")
                
            elif event == "stepEnd":
                # 关键：收到 stepEnd，从中获取 nextStepId
                current_step = payload.get("stepName", "")
                next_step_id = payload.get("nextStepId")
                end_type = payload.get("endType", "")
                step_desc = payload.get("stepDescription", "")

                log.info(f"📍 步骤结束: {current_step}")
                log.info(f"   结束类型: {end_type}")
                log.info(f"   步骤描述: {step_desc[:50]}...")

                if next_step_id:
                    log.info(f"➡️ 下一步: {next_step_id}")
                    self.step_id = next_step_id

                    # 重置轮次计数器（进入新步骤）
                    self.round_counter = 0

                    # 标记新步骤开始
                    self.step_just_started = True

                    # 发送 nextStep 确认
                    await self.send_next_step(next_step_id)
                else:
                    log.info("🏁 任务完成，没有下一步了！")
                    self.task_completed = True
                
            elif event == "taskEnd":
                log.info("🎉 整个任务已完成！")
                self.task_completed = True
                self.waiting_response = False
                
            elif event == "error":
                log.error(f"❌ 错误: {payload}")
                
        except json.JSONDecodeError:
            pass
    
    async def listen_loop(self):
        try:
            async for message in self.ws:
                await self.handle_message(message)
        except websockets.ConnectionClosed:
            self.is_connected = False
    
    async def heartbeat_loop(self):
        while self.is_connected:
            await asyncio.sleep(30)
            if self.is_connected:
                try:
                    await self.send_heartbeat()
                except:
                    pass
    
    async def interactive_mode(self):
        print("\n" + "="*60)
        print("📢 交互模式 ")
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
                    
                    timeout = 60
                    waited = 0
                    while self.waiting_response and waited < timeout:
                        await asyncio.sleep(0.5)
                        waited += 0.5
                    
            except EOFError:
                break
        
        if self.task_completed:
            print("\n🎉 任务已完成！")
    
    async def run(self):
        await self.connect()
        
        listen_task = asyncio.create_task(self.listen_loop())
        heartbeat_task = asyncio.create_task(self.heartbeat_loop())
        
        try:
            await self.interactive_mode()
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
    print()

    client = TrainingClient()
    await client.run()


if __name__ == "__main__":
    asyncio.run(main())