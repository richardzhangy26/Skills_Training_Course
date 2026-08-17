#!/usr/bin/env python3
"""Record browser WebSocket frames and export dialogue logs.

This tool is intentionally protocol-tolerant:
- it always writes raw WebSocket frames as JSONL first;
- it then tries to parse dialogue messages with optional field paths;
- if paths are not provided, it falls back to conservative heuristics.

Install optional dependency:
    pip install playwright
    python -m playwright install chromium
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


SENSITIVE_KEY_RE = re.compile(
    r"(authorization|cookie|token|access[_-]?token|refresh[_-]?token|jwt|secret|password)",
    re.IGNORECASE,
)

SENSITIVE_VALUE_RE = re.compile(
    r"(?i)(authorization|cookie|token)\s*[:=]\s*([^\s,;]+)"
)

ID_LIKE_RE = re.compile(r"^[A-Za-z0-9_\-]{12,}$")
URL_RE = re.compile(r"^wss?://|^https?://", re.IGNORECASE)

STEP_KEYS = (
    "stepId",
    "step_id",
    "currentStepId",
    "current_step_id",
    "scriptStepId",
    "script_step_id",
    "flowStepId",
    "flow_step_id",
)
STEP_NAME_KEYS = (
    "stepName",
    "step_name",
    "stageName",
    "stage_name",
    "nodeName",
    "node_name",
)
MESSAGE_TYPE_KEYS = (
    "messageType",
    "message_type",
    "type",
    "event",
    "action",
    "cmd",
)
ROLE_KEYS = ("role", "sender", "from", "speaker")

SENT_CONTENT_KEYS = (
    "userAnswer",
    "user_answer",
    "answer",
    "input",
    "query",
    "content",
    "text",
    "message",
    "msg",
    "speechText",
    "speech_text",
    "transcript",
)
RECEIVED_CONTENT_KEYS = (
    "questionText",
    "question_text",
    "question",
    "reply",
    "response",
    "answer",
    "content",
    "text",
    "message",
    "msg",
    "speechText",
    "speech_text",
    "transcript",
)
IGNORED_TEXT_KEYS = {
    "id",
    "uid",
    "uuid",
    "taskId",
    "task_id",
    "stepId",
    "step_id",
    "sessionId",
    "session_id",
    "instanceId",
    "instance_id",
    "url",
    "path",
    "type",
    "event",
    "action",
    "cmd",
    "status",
}


@dataclass
class FrameRecord:
    timestamp: str
    direction: str
    ws_url: str
    payload_text: Optional[str]
    payload_base64: Optional[str]
    payload_json: Optional[Any]


@dataclass
class ParsedMessage:
    timestamp: str
    direction: str
    ws_url: str
    role: str
    content: str
    step_id: str
    step_name: str
    round: int
    source: str
    message_type: Optional[str]
    need_skip_step: Optional[bool]
    raw_frame_index: int
    content_path: Optional[str]


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def read_json_file(path: Optional[str]) -> Optional[Dict[str, Any]]:
    if not path:
        return None
    p = Path(path).expanduser()
    with p.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"JSON config must be an object: {p}")
    return data


def redact_value(value: Any) -> Any:
    if isinstance(value, dict):
        cleaned: Dict[str, Any] = {}
        for key, item in value.items():
            if SENSITIVE_KEY_RE.search(str(key)):
                cleaned[key] = "[REDACTED]"
            else:
                cleaned[key] = redact_value(item)
        return cleaned
    if isinstance(value, list):
        return [redact_value(item) for item in value]
    if isinstance(value, str):
        return SENSITIVE_VALUE_RE.sub(r"\1=[REDACTED]", value)
    return value


def decode_payload(payload: Any) -> Tuple[Optional[str], Optional[str]]:
    if isinstance(payload, bytes):
        try:
            return payload.decode("utf-8"), None
        except UnicodeDecodeError:
            return None, base64.b64encode(payload).decode("ascii")
    if isinstance(payload, str):
        return payload, None
    return str(payload), None


def parse_json_payload(text: Optional[str]) -> Optional[Any]:
    if not text:
        return None
    stripped = text.strip()
    if not stripped:
        return None
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        return None


def split_paths(value: Optional[Any]) -> List[str]:
    if not value:
        return []
    if isinstance(value, list):
        return [str(part).strip() for part in value if str(part).strip()]
    return [part.strip() for part in value.split(",") if part.strip()]


def get_by_path(data: Any, path: str) -> Optional[Any]:
    current = data
    for part in path.split("."):
        if isinstance(current, dict):
            if part not in current:
                return None
            current = current[part]
        elif isinstance(current, list):
            try:
                current = current[int(part)]
            except (ValueError, IndexError):
                return None
        else:
            return None
    return current


def iter_key_values(data: Any, prefix: str = "") -> Iterable[Tuple[str, str, Any]]:
    if isinstance(data, dict):
        for key, value in data.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            yield path, str(key), value
            yield from iter_key_values(value, path)
    elif isinstance(data, list):
        for index, value in enumerate(data):
            path = f"{prefix}.{index}" if prefix else str(index)
            yield from iter_key_values(value, path)


def first_scalar_by_keys(data: Any, keys: Sequence[str]) -> Optional[Any]:
    key_set = set(keys)
    for _path, key, value in iter_key_values(data):
        if key in key_set and isinstance(value, (str, int, float, bool)):
            return value
    return None


def normalize_role(value: Optional[Any], direction: str) -> str:
    if value is None:
        return "user" if direction == "sent" else "assistant"
    text = str(value).strip().lower()
    if text in {"user", "student", "human", "client", "teacher"}:
        return "user"
    if text in {"assistant", "ai", "bot", "system", "agent"}:
        return "assistant"
    return "user" if direction == "sent" else "assistant"


def text_score(key: str, value: str, preferred_keys: Sequence[str]) -> int:
    if key in IGNORED_TEXT_KEYS or SENSITIVE_KEY_RE.search(key):
        return -100
    if URL_RE.search(value) or ID_LIKE_RE.match(value):
        return -100
    stripped = value.strip()
    if len(stripped) < 1:
        return -100
    if len(stripped) > 5000:
        return -20

    score = min(len(stripped), 160)
    if key in preferred_keys:
        score += 220
    elif key.lower() in {item.lower() for item in preferred_keys}:
        score += 180
    if any(ch in stripped for ch in "，。！？；：、"):
        score += 40
    if re.search(r"[\u4e00-\u9fff]", stripped):
        score += 50
    if len(stripped) <= 3 and stripped.lower() in {"ok", "yes", "ping", "pong"}:
        score -= 150
    return score


def extract_text_by_paths(data: Any, paths: Sequence[str]) -> Tuple[Optional[str], Optional[str]]:
    for path in paths:
        value = get_by_path(data, path)
        if isinstance(value, str) and value.strip():
            return value.strip(), path
        if isinstance(value, (int, float)):
            return str(value), path
    return None, None


def extract_text_heuristic(
    data: Any,
    direction: str,
    sent_paths: Sequence[str],
    received_paths: Sequence[str],
) -> Tuple[Optional[str], Optional[str]]:
    explicit_paths = sent_paths if direction == "sent" else received_paths
    text, path = extract_text_by_paths(data, explicit_paths)
    if text:
        return text, path

    preferred = SENT_CONTENT_KEYS if direction == "sent" else RECEIVED_CONTENT_KEYS
    candidates: List[Tuple[int, str, str]] = []
    for item_path, key, value in iter_key_values(data):
        if isinstance(value, str):
            candidates.append((text_score(key, value, preferred), item_path, value.strip()))
        elif isinstance(value, (int, float)) and key in preferred:
            candidates.append((100, item_path, str(value)))
    if not candidates:
        return None, None
    candidates.sort(reverse=True, key=lambda item: item[0])
    best_score, best_path, best_text = candidates[0]
    if best_score < 80:
        return None, None
    return best_text, best_path


def payload_to_record(ws_url: str, direction: str, payload: Any, redact: bool) -> FrameRecord:
    payload_text, payload_base64 = decode_payload(payload)
    payload_json = parse_json_payload(payload_text)

    if redact:
        payload_text = redact_value(payload_text)
        payload_json = redact_value(payload_json)

    return FrameRecord(
        timestamp=now_iso(),
        direction=direction,
        ws_url=ws_url,
        payload_text=payload_text,
        payload_base64=payload_base64,
        payload_json=payload_json,
    )


def parse_frame(
    frame: FrameRecord,
    frame_index: int,
    args: argparse.Namespace,
) -> Optional[ParsedMessage]:
    data = frame.payload_json
    if data is None:
        data = parse_json_payload(frame.payload_text)
    if data is None:
        return None

    if args.message_type_filter:
        message_type_value = first_scalar_by_keys(data, MESSAGE_TYPE_KEYS)
        message_type = str(message_type_value) if message_type_value is not None else None
        if message_type not in args.message_type_filter:
            return None
    else:
        message_type_value = first_scalar_by_keys(data, MESSAGE_TYPE_KEYS)
        message_type = str(message_type_value) if message_type_value is not None else None

    role_path = args.sent_role_path if frame.direction == "sent" else args.received_role_path
    role_value = get_by_path(data, role_path) if role_path else first_scalar_by_keys(data, ROLE_KEYS)
    role = normalize_role(role_value, frame.direction)

    text, content_path = extract_text_heuristic(
        data,
        frame.direction,
        args.sent_content_paths,
        args.received_content_paths,
    )
    if not text:
        return None

    if args.min_content_length and len(text.strip()) < args.min_content_length:
        return None

    if args.max_content_length and len(text.strip()) > args.max_content_length:
        return None

    step_id = None
    for path in args.step_id_paths:
        value = get_by_path(data, path)
        if value:
            step_id = str(value)
            break
    if not step_id:
        step_id_value = first_scalar_by_keys(data, STEP_KEYS)
        step_id = str(step_id_value) if step_id_value else "unknown"

    step_name = None
    for path in args.step_name_paths:
        value = get_by_path(data, path)
        if value:
            step_name = str(value)
            break
    if not step_name:
        step_name_value = first_scalar_by_keys(data, STEP_NAME_KEYS)
        step_name = str(step_name_value) if step_name_value else step_id

    need_skip = first_scalar_by_keys(data, ("needSkipStep", "need_skip_step"))
    if isinstance(need_skip, str):
        need_skip_bool: Optional[bool] = need_skip.lower() in {"true", "1", "yes"}
    elif isinstance(need_skip, bool):
        need_skip_bool = need_skip
    else:
        need_skip_bool = None

    return ParsedMessage(
        timestamp=frame.timestamp,
        direction=frame.direction,
        ws_url=frame.ws_url,
        role=role,
        content=text.strip(),
        step_id=step_id,
        step_name=step_name,
        round=0,
        source="websocket",
        message_type=message_type,
        need_skip_step=need_skip_bool,
        raw_frame_index=frame_index,
        content_path=content_path,
    )


def dedupe_messages(messages: Sequence[ParsedMessage]) -> List[ParsedMessage]:
    result: List[ParsedMessage] = []
    last_key: Optional[Tuple[str, str, str]] = None
    for msg in messages:
        key = (msg.role, msg.step_id, msg.content)
        if key == last_key:
            continue
        result.append(msg)
        last_key = key
    return result


def assign_rounds(messages: Sequence[ParsedMessage]) -> None:
    round_num = 0
    for msg in messages:
        if msg.role == "user":
            round_num += 1
        msg.round = round_num


def build_dialogue_json(
    messages: Sequence[ParsedMessage],
    task_id: str,
    profile: str,
    start_time: str,
    end_time: str,
) -> Dict[str, Any]:
    stages: Dict[str, Dict[str, Any]] = {}
    for msg in messages:
        if msg.step_id not in stages:
            stages[msg.step_id] = {
                "stage_index": len(stages) + 1,
                "stage_name": msg.step_name or msg.step_id,
                "step_id": msg.step_id,
                "messages": [],
            }
        stages[msg.step_id]["messages"].append(
            {
                "round": msg.round,
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp,
                "source": msg.source,
            }
        )

    return {
        "metadata": {
            "task_id": task_id,
            "student_profile": profile,
            "student_profile_label": profile,
            "workflow_start_time": start_time,
            "workflow_end_time": end_time,
            "total_rounds": max((msg.round for msg in messages), default=0),
            "total_steps": len(stages),
            "source": "websocket_recorder",
        },
        "stages": list(stages.values()),
    }


def write_dialogue_txt(messages: Sequence[ParsedMessage], path: Path, task_id: str, profile: str) -> None:
    lines = [
        "对话记录",
        f"日志创建时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"task_id: {task_id}",
        f"学生档位: {profile}",
        "=" * 60,
    ]
    for msg in messages:
        role_label = "用户" if msg.role == "user" else "AI"
        round_info = f" | 第 {msg.round} 轮" if msg.round else ""
        lines.extend(
            [
                (
                    f"[{msg.timestamp}] Step: {msg.step_name} | step_id: {msg.step_id}"
                    f"{round_info} | 来源: websocket"
                ),
                f"{role_label}: {msg.content}",
                "-" * 80,
            ]
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def make_output_paths(args: argparse.Namespace) -> Dict[str, Path]:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    task_part = f"task_{args.task_id}" if args.task_id else "websocket"
    profile = args.profile or "manual"
    output_dir = Path(args.output_dir).expanduser()
    if not args.flat_output and args.task_id:
        output_dir = output_dir / f"task_{args.task_id}" / profile
    output_dir.mkdir(parents=True, exist_ok=True)
    prefix = f"{task_part}_{timestamp}"
    return {
        "dir": output_dir,
        "raw": output_dir / f"{prefix}_raw_ws_frames.jsonl",
        "parsed": output_dir / f"{prefix}_parsed_messages.jsonl",
        "dialogue_json": output_dir / f"{prefix}_dialogue.json",
        "dialogue_txt": output_dir / f"{prefix}_dialogue.txt",
        "meta": output_dir / f"{prefix}_recorder_meta.json",
    }


def write_jsonl(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


async def run_recorder(args: argparse.Namespace) -> int:
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("Missing optional dependency: playwright", file=sys.stderr)
        print("Install with: pip install playwright && python -m playwright install chromium", file=sys.stderr)
        return 2

    paths = make_output_paths(args)
    frames: List[FrameRecord] = []
    start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def should_capture_url(ws_url: str) -> bool:
        if not args.ws_url_filter:
            return True
        return args.ws_url_filter in ws_url

    async with async_playwright() as p:
        if args.cdp_url:
            browser = await p.chromium.connect_over_cdp(args.cdp_url)
            context = browser.contexts[0] if browser.contexts else await browser.new_context()
        else:
            browser = await p.chromium.launch(headless=args.headless)
            context_kwargs: Dict[str, Any] = {}
            if args.storage_state:
                context_kwargs["storage_state"] = args.storage_state
            context = await browser.new_context(**context_kwargs)

        page = context.pages[0] if context.pages else await context.new_page()

        def on_websocket(ws: Any) -> None:
            if not should_capture_url(ws.url):
                return
            print(f"Capturing WebSocket: {ws.url}")

            def on_frame_sent(payload: Any) -> None:
                frames.append(payload_to_record(ws.url, "sent", payload, args.redact))

            def on_frame_received(payload: Any) -> None:
                frames.append(payload_to_record(ws.url, "received", payload, args.redact))

            ws.on("framesent", on_frame_sent)
            ws.on("framereceived", on_frame_received)

        page.on("websocket", on_websocket)

        if args.url:
            await page.goto(args.url, wait_until=args.wait_until, timeout=args.goto_timeout_ms)

        print("Recorder is running.")
        print(f"Output directory: {paths['dir']}")
        print("Interact with the page, then press Enter here to stop.")

        if args.duration:
            await asyncio.sleep(args.duration)
        else:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, sys.stdin.readline)

        end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if not args.keep_browser_open and not args.cdp_url:
            await context.close()
            await browser.close()

    write_jsonl(paths["raw"], (asdict(frame) for frame in frames))

    parsed: List[ParsedMessage] = []
    for index, frame in enumerate(frames):
        msg = parse_frame(frame, index, args)
        if msg:
            parsed.append(msg)
    parsed = dedupe_messages(parsed)
    assign_rounds(parsed)

    write_jsonl(paths["parsed"], (asdict(msg) for msg in parsed))
    dialogue_json = build_dialogue_json(
        parsed,
        args.task_id or "unknown",
        args.profile or "manual",
        start_time,
        end_time,
    )
    paths["dialogue_json"].write_text(
        json.dumps(dialogue_json, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_dialogue_txt(parsed, paths["dialogue_txt"], args.task_id or "unknown", args.profile or "manual")

    meta = {
        "url": args.url,
        "task_id": args.task_id,
        "profile": args.profile,
        "frame_count": len(frames),
        "parsed_message_count": len(parsed),
        "paths": {key: str(value) for key, value in paths.items()},
        "redact": args.redact,
        "ws_url_filter": args.ws_url_filter,
        "sent_content_paths": args.sent_content_paths,
        "received_content_paths": args.received_content_paths,
        "step_id_paths": args.step_id_paths,
        "step_name_paths": args.step_name_paths,
    }
    paths["meta"].write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Recorded frames: {len(frames)}")
    print(f"Parsed dialogue messages: {len(parsed)}")
    print(f"Raw frames: {paths['raw']}")
    print(f"Dialogue JSON: {paths['dialogue_json']}")
    print(f"Dialogue TXT: {paths['dialogue_txt']}")
    return 0


def load_config_into_args(args: argparse.Namespace) -> argparse.Namespace:
    config = read_json_file(args.config)
    if not config:
        return args
    for key, value in config.items():
        if not hasattr(args, key):
            raise ValueError(f"Unknown config key: {key}")
        if getattr(args, key) in (None, "", [], False):
            setattr(args, key, value)
    return args


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Record browser WebSocket frames and export dialogue logs."
    )
    parser.add_argument("--url", help="Page URL to open. If omitted, record the first existing page.")
    parser.add_argument("--task-id", default="", help="Task id for output metadata.")
    parser.add_argument("--profile", default="manual", help="Profile name for output metadata.")
    parser.add_argument("--output-dir", default="log", help="Output directory.")
    parser.add_argument(
        "--flat-output",
        action="store_true",
        help="Write directly to output-dir instead of log/task_<task_id>/<profile>/.",
    )
    parser.add_argument("--config", help="Optional JSON config file for parser paths.")
    parser.add_argument("--cdp-url", help="Connect to an existing Chrome CDP endpoint.")
    parser.add_argument("--storage-state", help="Playwright storage_state JSON file.")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode.")
    parser.add_argument("--duration", type=int, help="Recording duration in seconds. Default waits for Enter.")
    parser.add_argument("--keep-browser-open", action="store_true")
    parser.add_argument("--ws-url-filter", help="Only capture WebSocket URLs containing this text.")
    parser.add_argument("--wait-until", default="domcontentloaded")
    parser.add_argument("--goto-timeout-ms", type=int, default=60000)
    parser.add_argument("--no-redact", action="store_true", help="Do not redact sensitive-looking fields.")
    parser.add_argument("--min-content-length", type=int, default=1)
    parser.add_argument("--max-content-length", type=int, default=2000)
    parser.add_argument(
        "--sent-content-path",
        default="",
        help="Comma-separated JSON paths for user/sent message content.",
    )
    parser.add_argument(
        "--received-content-path",
        default="",
        help="Comma-separated JSON paths for assistant/received message content.",
    )
    parser.add_argument("--sent-role-path", default="")
    parser.add_argument("--received-role-path", default="")
    parser.add_argument("--step-id-path", default="", help="Comma-separated JSON paths for step id.")
    parser.add_argument("--step-name-path", default="", help="Comma-separated JSON paths for step name.")
    parser.add_argument(
        "--message-type-filter",
        default="",
        help="Comma-separated message types/events to keep.",
    )
    return parser


def normalize_args(args: argparse.Namespace) -> argparse.Namespace:
    args = load_config_into_args(args)
    args.redact = not args.no_redact
    args.sent_content_paths = split_paths(args.sent_content_path)
    args.received_content_paths = split_paths(args.received_content_path)
    args.step_id_paths = split_paths(args.step_id_path)
    args.step_name_paths = split_paths(args.step_name_path)
    args.message_type_filter = set(split_paths(args.message_type_filter))
    return args


def main() -> int:
    parser = build_parser()
    args = normalize_args(parser.parse_args())
    return asyncio.run(run_recorder(args))


if __name__ == "__main__":
    raise SystemExit(main())
