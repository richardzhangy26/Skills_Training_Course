"""确认令牌、脱敏与本地状态文件的安全原语。"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import tempfile
from threading import Lock
from typing import Any

from .contracts import ConfirmationBinding


_SENSITIVE_KEY = re.compile(
    r"(?i)(authorization|cookie|jwt|token|secret|api[_-]?key|password|credential|session)"
)
_LABELED_CREDENTIAL = re.compile(
    r"(?i)\b(authorization|cookie|jwt|access[_-]?token|refresh[_-]?token|api[_-]?key|token)"
    r"\s*([:=])\s*(?:bearer\s+)?[^\s,;]+"
)
_JSON_QUOTED_CREDENTIAL = re.compile(
    r"(?i)((?:\\?[\"'])"
    r"(?:authorization|cookie|jwt|access[_-]?token|refresh[_-]?token|api[_-]?key|token)"
    r"(?:\\?[\"'])\s*:\s*(?:\\?[\"']))"
    r"(?:bearer\s+)?[^\"\\']+"
)
_JWT = re.compile(
    r"\beyJ[A-Za-z0-9_-]{5,}\.[A-Za-z0-9_-]{5,}\.[A-Za-z0-9_-]{5,}\b"
)
_COMMON_BARE_TOKEN = re.compile(
    r"(?<![A-Za-z0-9_-])(?:sk-(?:proj-)?|ghp_|github_pat_|xox[baprs]-)"
    r"[A-Za-z0-9_-]{20,}(?![A-Za-z0-9_-])"
)
_REDACTED = "[REDACTED]"


def _encode_binding(binding: ConfirmationBinding) -> bytes:
    return json.dumps(
        {
            "diff_digest": binding.diff_digest,
            "expected_digest": binding.expected_digest,
            "knowledge_version": binding.knowledge_version,
            "nonce": binding.nonce,
            "snapshot_digest": binding.snapshot_digest,
            "target_id": binding.target_id,
        },
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _base64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


class ConfirmationTokenManager:
    """在单个联调进程内签发、校验并消费一次性确认令牌。"""

    def __init__(self, *, secret: bytes):
        if not secret:
            raise ValueError("confirmation_secret_required")
        self._secret = secret
        self._consumed: set[str] = set()
        self._lock = Lock()

    def issue(self, binding: ConfirmationBinding) -> str:
        payload = _encode_binding(binding)
        signature = hmac.new(self._secret, payload, hashlib.sha256).digest()
        return f"v1.{_base64url(payload)}.{_base64url(signature)}"

    def verify(self, token: str, binding: ConfirmationBinding) -> bool:
        try:
            version, encoded_payload, encoded_signature = token.split(".", 2)
        except ValueError:
            return False
        if version != "v1":
            return False
        payload = _encode_binding(binding)
        if not hmac.compare_digest(encoded_payload, _base64url(payload)):
            return False
        expected_signature = _base64url(
            hmac.new(self._secret, payload, hashlib.sha256).digest()
        )
        return hmac.compare_digest(encoded_signature, expected_signature)

    def consume(self, token: str, binding: ConfirmationBinding) -> bool:
        """只在绑定校验通过且尚未消费时返回 True。"""

        if not self.verify(token, binding):
            return False
        token_digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
        with self._lock:
            if token_digest in self._consumed:
                return False
            self._consumed.add(token_digest)
            return True


def _redact_text(value: str) -> str:
    value = _JSON_QUOTED_CREDENTIAL.sub(
        lambda match: f"{match.group(1)}{_REDACTED}", value
    )
    value = _LABELED_CREDENTIAL.sub(
        lambda match: f"{match.group(1)}{match.group(2)}{_REDACTED}", value
    )
    value = _JWT.sub(_REDACTED, value)
    return _COMMON_BARE_TOKEN.sub(_REDACTED, value)


def redact_sensitive(value: Any) -> Any:
    """递归脱敏适合进入日志、报告和 checkpoint 的值。"""

    if isinstance(value, dict):
        return {
            str(key): (
                _REDACTED
                if _SENSITIVE_KEY.search(str(key))
                else redact_sensitive(item)
            )
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple, set)):
        return [redact_sensitive(item) for item in value]
    if isinstance(value, str):
        return _redact_text(value)
    return value


def write_checkpoint_atomic(path: Path, payload: Any) -> Path:
    """以 0600 文件权限原子保存已脱敏的 JSON checkpoint。"""

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(
        redact_sensitive(payload), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
    )
    temporary_path = Path(temporary_name)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_path, path)
        os.chmod(path, 0o600)
        directory_descriptor = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
        return path
    finally:
        if temporary_path.exists():
            temporary_path.unlink()
