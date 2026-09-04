"""私有运行态文件的唯一原子写实现。"""

from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
from typing import Any


def _private_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    os.chmod(path, 0o700)


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def write_private_bytes_atomic(path: Path, data: bytes) -> Path:
    path = Path(path)
    if not isinstance(data, bytes):
        raise TypeError("private_data_must_be_bytes")
    _private_directory(path.parent)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
    )
    temporary = Path(temporary_name)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        os.chmod(path, 0o600)
        _fsync_directory(path.parent)
        return path
    finally:
        if temporary.exists():
            temporary.unlink()


def write_private_json_atomic(path: Path, value: Any) -> Path:
    data = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return write_private_bytes_atomic(path, data)
