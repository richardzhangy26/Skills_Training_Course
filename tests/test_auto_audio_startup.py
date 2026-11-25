import asyncio
import json
import unittest
from unittest.mock import AsyncMock, Mock, patch

import websockets

from auto_audio_train import AUDIO_CONFIG, CONFIG, TrainingClient


class AudioStartupTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.client = TrainingClient()
        self.client.ensure_logger = Mock()
        self.client.speak = AsyncMock(return_value=False)
        self.client.generate_ai_answer = Mock(return_value="Good morning.")
        self.client.startup_timeout = 0.1
        self.client.send_json = AsyncMock()
        self.client.is_connected = True

    async def event(self, name, **payload):
        await self.client.handle_message(json.dumps({"event": name, "payload": payload}))

    async def test_auto_waits_for_complete_question_and_stops_on_send_failure(self):
        client = self.client
        client.auto_continue = True
        with patch("builtins.input", side_effect=AssertionError("unexpected stdin")):
            task = asyncio.create_task(client.semi_interactive_mode())
            await asyncio.sleep(0)
            await self.event("connected", sessionId="session", stepId="step")
            await self.event("botAnswerStart")
            await self.event("botAnswer", msg="Ready?")
            await asyncio.sleep(0)
            client.generate_ai_answer.assert_not_called()
            await self.event("botAnswerEnd")
            with self.assertRaisesRegex(RuntimeError, "发送失败"):
                await asyncio.wait_for(task, 2)
        client.generate_ai_answer.assert_called_once_with("Ready?")
        client.speak.assert_awaited_once()

    async def test_auto_times_out_without_sending(self):
        self.client.auto_continue = True
        with self.assertRaisesRegex(RuntimeError, "connected"):
            await asyncio.wait_for(self.client.semi_interactive_mode(), 2)
        self.client.generate_ai_answer.assert_not_called()
        self.client.speak.assert_not_awaited()

    async def test_eof_reports_local_exit(self):
        with patch("builtins.input", side_effect=EOFError), self.assertLogs(level="INFO") as logs:
            await self.client.semi_interactive_mode()
        self.assertIn("标准输入已结束", " ".join(logs.output))

    async def test_platform_error_stops_before_tts(self):
        with self.assertRaisesRegex(RuntimeError, "平台返回 error"):
            await self.event("error", code="invalid_task")
        self.client.speak.assert_not_awaited()

    async def test_question_in_final_event(self):
        await self.event("botAnswerStart")
        await self.event("botAnswerEnd", msg="What is a tanker?")
        self.assertEqual(self.client.current_bot_msg, "What is a tanker?")

    async def test_remote_close_wakes_dialogue(self):
        client = self.client

        class ClosedSocket:
            close_code = 1000
            close_reason = "finished"

            async def __aiter__(self):
                for frame in ():
                    yield frame

        client.connect = AsyncMock()
        client.disconnect = AsyncMock()
        client.ws = ClosedSocket()
        with self.assertRaisesRegex(RuntimeError, "code=1000"):
            await asyncio.wait_for(client.run("auto"), 1)
        client.disconnect.assert_awaited_once()
        client.generate_ai_answer.assert_not_called()

    async def test_loopback_voice_round(self):
        observed = []

        async def server(ws):
            async def send(event, **payload):
                await ws.send(json.dumps({"event": event, "payload": payload}))

            await send("connected", sessionId="session", stepId="intro")
            observed.append(json.loads(await ws.recv())["event"])
            await send("botAnswerStart")
            await send("botAnswer", msg="Ready?")
            await send("botAnswerEnd")
            observed.append(type(await ws.recv()))
            observed.append(json.loads(await ws.recv())["event"])
            await send("userTextEnd", text="Ready.")
            await send("taskEnd")

        client = TrainingClient()
        client.ensure_logger = Mock()
        client.tts.synthesize = AsyncMock(return_value=b"mock audio")
        client.audio.mp3_to_pcm = Mock(return_value=bytes(3200))
        client.generate_ai_answer = Mock(return_value="Ready.")
        async with websockets.serve(server, "127.0.0.1", 0) as listener:
            port = listener.sockets[0].getsockname()[1]
            with patch.dict(CONFIG, ws_url=f"ws://127.0.0.1:{port}", task_id="test"), patch.dict(
                AUDIO_CONFIG, silence_frames=0, chunk_interval=0
            ):
                await asyncio.wait_for(client.run("auto"), 3)
        self.assertEqual(observed, ["startScript", bytes, "mute"])
        self.assertTrue(client.task_completed)
        self.assertEqual(client.round_counter, 1)
        client.generate_ai_answer.assert_called_once_with("Ready?")
