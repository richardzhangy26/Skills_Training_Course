"""跨进程确认消费、target 锁与原子 checkpoint。"""

from __future__ import annotations

from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import secrets
from typing import Any, Iterator

from .contracts import ConfirmationBinding
from .fixtures import validate_run_id
from .private_io import write_private_bytes_atomic, write_private_json_atomic
from .safety import ConfirmationTokenManager
from .safety import redact_sensitive


def _without_confirmation_tokens(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            str(key): _without_confirmation_tokens(item)
            for key, item in value.items()
            if "token" not in str(key).lower().replace("_", "").replace("-", "")
        }
    if isinstance(value, (list, tuple)):
        return [_without_confirmation_tokens(item) for item in value]
    if isinstance(value, str):
        return redact_sensitive(value)
    return value


class DurableConfirmations:
    def __init__(self, key: bytes, ledger_path: Path, lock_path: Path):
        self._manager = ConfirmationTokenManager(secret=key)
        self._ledger_path = ledger_path
        self._lock_path = lock_path

    def issue(self, binding: ConfirmationBinding) -> str:
        return self._manager.issue(binding)

    def verify(self, token: str, binding: ConfirmationBinding) -> bool:
        return self._manager.verify(token, binding)

    def consume(self, token: str, binding: ConfirmationBinding) -> bool:
        if not self.verify(token, binding):
            return False
        token_digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
        nonce_digest = hashlib.sha256(binding.nonce.encode("utf-8")).hexdigest()
        self._lock_path.parent.mkdir(parents=True, exist_ok=True)
        descriptor = os.open(self._lock_path, os.O_CREAT | os.O_RDWR, 0o600)
        try:
            os.fchmod(descriptor, 0o600)
            fcntl.flock(descriptor, fcntl.LOCK_EX)
            if self._ledger_path.exists():
                try:
                    ledger = json.loads(self._ledger_path.read_text(encoding="utf-8"))
                except (OSError, ValueError):
                    return False
            else:
                ledger = {"schema_version": 1, "consumed": []}
            consumed = ledger.get("consumed")
            if not isinstance(consumed, list):
                return False
            if any(
                isinstance(item, dict)
                and (item.get("token_sha256") == token_digest or item.get("nonce_sha256") == nonce_digest)
                for item in consumed
            ):
                return False
            consumed.append(
                {
                    "target_sha256": hashlib.sha256(binding.target_id.encode("utf-8")).hexdigest(),
                    "token_sha256": token_digest,
                    "nonce_sha256": nonce_digest,
                }
            )
            write_private_json_atomic(self._ledger_path, ledger)
            return True
        finally:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
            os.close(descriptor)


class DurableRunStore:
    """所有可持久运行状态的唯一入口。"""

    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        os.chmod(self.root, 0o700)
        key_path = self.root / "confirmation.key"
        lock_path = self.root / "confirmation-key.lock"
        lock_descriptor = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o600)
        try:
            os.fchmod(lock_descriptor, 0o600)
            fcntl.flock(lock_descriptor, fcntl.LOCK_EX)
            if not key_path.exists():
                write_private_bytes_atomic(key_path, secrets.token_bytes(32))
            os.chmod(key_path, 0o600)
            key = key_path.read_bytes()
        finally:
            fcntl.flock(lock_descriptor, fcntl.LOCK_UN)
            os.close(lock_descriptor)
        if len(key) != 32:
            raise ValueError("invalid_confirmation_key")
        self.confirmations = DurableConfirmations(
            key,
            self.root / "consumed.json",
            self.root / "consumed.lock",
        )

    @contextmanager
    def target_lock(self, target_id: str) -> Iterator[None]:
        safe_target = validate_run_id(target_id)
        path = self.root / "locks" / f"{safe_target}.lock"
        path.parent.mkdir(parents=True, exist_ok=True)
        os.chmod(path.parent, 0o700)
        descriptor = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
        try:
            os.fchmod(descriptor, 0o600)
            fcntl.flock(descriptor, fcntl.LOCK_EX)
            yield
        finally:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
            os.close(descriptor)

    def write_checkpoint(self, run_id: str, payload: Any) -> Path:
        safe_run_id = validate_run_id(run_id)
        path = self.root / "runs" / f"{safe_run_id}.json"
        write_private_json_atomic(path, _without_confirmation_tokens(payload))
        return path

    def read_checkpoint(self, run_id: str) -> dict[str, Any] | None:
        safe_run_id = validate_run_id(run_id)
        path = self.root / "runs" / f"{safe_run_id}.json"
        if not path.exists():
            return None
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            raise ValueError("invalid_checkpoint") from None
        if not isinstance(value, dict):
            raise ValueError("invalid_checkpoint")
        return value
