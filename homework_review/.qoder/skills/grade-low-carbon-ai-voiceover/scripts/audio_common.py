#!/usr/bin/env python3
"""Shared ffmpeg/ffprobe helpers for low-carbon audio/video grading."""

from __future__ import annotations

import json
import math
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any


SUPPORTED_EXTENSIONS = {
    ".mp3",
    ".wav",
    ".m4a",
    ".aac",
    ".flac",
    ".ogg",
    ".mp4",
    ".mov",
}


class AudioToolError(RuntimeError):
    """Raised when ffmpeg/ffprobe cannot analyze the audio."""


def rounded(value: float | None, digits: int = 2) -> float | None:
    if value is None or math.isnan(value) or math.isinf(value):
        return None
    return round(value, digits)


def ensure_tool(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise AudioToolError(f"未找到 {name}，请先安装 ffmpeg 工具链。")
    return path


def run_command(args: list[str]) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            args,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr if isinstance(exc.stderr, str) else str(exc.stderr)
        raise AudioToolError(detail.strip() or f"命令执行失败：{' '.join(args)}") from exc


def ffprobe_full(path: str | Path) -> dict[str, Any]:
    ensure_tool("ffprobe")
    completed = run_command(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=format_name,duration,bit_rate,size:stream=index,codec_type,codec_name,sample_rate,channels,channel_layout,bit_rate,duration,disposition",
            "-of",
            "json",
            str(path),
        ]
    )
    return json.loads(completed.stdout)


def audio_streams(probe: dict[str, Any]) -> list[dict[str, Any]]:
    return [stream for stream in probe.get("streams", []) if stream.get("codec_type") == "audio"]


def first_audio_stream(probe: dict[str, Any]) -> dict[str, Any] | None:
    streams = audio_streams(probe)
    return streams[0] if streams else None


def safe_float(value: Any) -> float | None:
    try:
        if value in (None, "N/A"):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def safe_int(value: Any) -> int | None:
    try:
        if value in (None, "N/A"):
            return None
        return int(float(value))
    except (TypeError, ValueError):
        return None


def format_duration(seconds: float | None) -> str:
    if seconds is None:
        return "未知"
    minutes = int(seconds // 60)
    rest = seconds - minutes * 60
    return f"{minutes:02d}:{rest:05.2f}"


def volume_detect(path: str | Path, duration: float | None = 60.0) -> dict[str, Any]:
    ensure_tool("ffmpeg")
    args = ["ffmpeg", "-hide_banner", "-nostdin", "-i", str(path), "-map", "0:a:0"]
    if duration:
        args.extend(["-t", str(duration)])
    args.extend(["-af", "volumedetect", "-f", "null", "-"])
    try:
        completed = subprocess.run(args, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as exc:
        raise AudioToolError(exc.stderr.strip() or "volumedetect 失败") from exc
    text = completed.stderr
    mean_match = re.search(r"mean_volume:\s*([-0-9.]+)\s*dB", text)
    max_match = re.search(r"max_volume:\s*([-0-9.]+)\s*dB", text)
    histogram_match = re.search(r"histogram_0db:\s*(\d+)", text)
    return {
        "mean_volume_db": safe_float(mean_match.group(1)) if mean_match else None,
        "max_volume_db": safe_float(max_match.group(1)) if max_match else None,
        "histogram_0db_samples": safe_int(histogram_match.group(1)) if histogram_match else 0,
    }


def silence_detect(
    path: str | Path,
    *,
    noise: str = "-45dB",
    min_silence_duration: float = 0.5,
    duration: float | None = None,
) -> dict[str, Any]:
    ensure_tool("ffmpeg")
    args = ["ffmpeg", "-hide_banner", "-nostdin", "-i", str(path), "-map", "0:a:0"]
    if duration:
        args.extend(["-t", str(duration)])
    args.extend(["-af", f"silencedetect=noise={noise}:d={min_silence_duration}", "-f", "null", "-"])
    try:
        completed = subprocess.run(args, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as exc:
        raise AudioToolError(exc.stderr.strip() or "silencedetect 失败") from exc
    text = completed.stderr
    durations = [safe_float(value) for value in re.findall(r"silence_duration:\s*([0-9.]+)", text)]
    total_silence = sum(value for value in durations if value is not None)
    return {
        "silence_count": len(durations),
        "total_silence_seconds": round(total_silence, 3),
        "noise_threshold": noise,
    }


def print_output(data: dict[str, Any], json_output: bool) -> None:
    if json_output:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(data, ensure_ascii=False, indent=2))
