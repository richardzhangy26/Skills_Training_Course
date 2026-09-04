"""标准 SSE 字节增量解析；JSON 不完整片段保留给上层，不猜业务协议。"""
from __future__ import annotations

import codecs
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
import json
import re
from typing import Any

from .safety import redact_sensitive
from .transport import ClientError


_PERSON_IDENTITY_KEY = re.compile(
    r'(?i)^(?:from|to|sender|receiver)?(?:user|student)(?:nid|id)$'
)


def safe_event_data(value: Any) -> Any:
    """只保留明确的业务 ID；session 凭证仍走统一脱敏。"""
    if isinstance(value, dict):
        ids = {'sessionId', 'messageId', 'planId', 'traceId', 'session_id', 'message_id', 'plan_id', 'trace_id'}
        result = {}
        for key, item in value.items():
            compact_key = key.replace('_', '').replace('-', '')
            if _PERSON_IDENTITY_KEY.fullmatch(compact_key):
                result[key] = '[REDACTED]'
            elif key in ids:
                result[key] = redact_sensitive(item)
            elif redact_sensitive({key: None})[key] is not None:
                result[key] = '[REDACTED]'
            else:
                result[key] = safe_event_data(item)
        return result
    if isinstance(value, list):
        return [safe_event_data(item) for item in value]
    return redact_sensitive(value)


@dataclass(frozen=True)
class SSEEvent:
    event: str
    id: str | None
    data: Any
    terminal: bool = False


def parse_sse(chunks: Iterable[bytes], *, terminal_events: tuple[str, ...] = ('end', 'done'),
              terminal_statuses: tuple[str, ...] = (), require_terminal: bool = True,
              max_event_chars: int = 1_000_000) -> Iterator[SSEEvent]:
    decoder = codecs.getincrementaldecoder('utf-8-sig')('strict')
    buffer = ''
    data: list[str] = []
    event = 'message'
    event_id = None
    size = 0
    terminal = False

    def process(line):
        nonlocal data, event, event_id, size, terminal
        if not line:
            if not data and event not in terminal_events:
                event = 'message'
                return None
            raw = '\n'.join(data)
            terminal = raw.strip() == '[DONE]' or event in terminal_events
            try:
                value = json.loads(raw)
            except json.JSONDecodeError:
                value = raw
            if isinstance(value, dict) and value.get('status') in terminal_statuses:
                terminal = True
            result = SSEEvent(event, redact_sensitive(event_id), safe_event_data(value), terminal)
            data, event, size = [], 'message', 0
            return result
        if line.startswith(':'):
            return None
        key, _, value = line.partition(':')
        if value.startswith(' '):
            value = value[1:]
        if key == 'data':
            size += len(value)
            if size > max_event_chars:
                raise ClientError('CONTRACT_CHANGED', 'sse', '事件超过限制')
            data.append(value)
        elif key == 'event':
            event = value
        elif key == 'id' and '\x00' not in value:
            event_id = value
        return None

    try:
        for chunk in chunks:
            if not isinstance(chunk, bytes):
                raise ClientError('CONTRACT_CHANGED', 'sse', '输入必须为字节')
            buffer += decoder.decode(chunk)
            while True:
                positions = [pos for pos in (buffer.find('\r'), buffer.find('\n')) if pos >= 0]
                if not positions:
                    break
                pos = min(positions)
                if buffer[pos] == '\r' and pos == len(buffer) - 1:
                    break
                length = 2 if buffer[pos:pos + 2] == '\r\n' else 1
                line, buffer = buffer[:pos], buffer[pos + length:]
                result = process(line)
                if result is not None:
                    yield result
                    if terminal:
                        return
            if len(buffer) > max_event_chars:
                raise ClientError('CONTRACT_CHANGED', 'sse', '行超过限制')
        buffer += decoder.decode(b'', final=True)
        if buffer.endswith('\r'):
            result = process(buffer[:-1])
            if result is not None:
                yield result
        if require_terminal and not terminal:
            raise ClientError('CONTRACT_CHANGED', 'sse', '流结束但没有终止事件')
    except UnicodeDecodeError:
        raise ClientError('CONTRACT_CHANGED', 'sse', '无效 UTF-8') from None
    except ClientError:
        raise
    except Exception:
        raise ClientError('TRANSPORT_ERROR', 'sse', '流读取失败') from None
