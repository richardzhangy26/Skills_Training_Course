#!/usr/bin/env python3
"""Extract objective audio metadata for low-carbon AI audio/video submissions."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from audio_common import (
    SUPPORTED_EXTENSIONS,
    AudioToolError,
    audio_streams,
    ffprobe_full,
    first_audio_stream,
    format_duration,
    print_output,
    rounded,
    safe_float,
    safe_int,
    silence_detect,
    volume_detect,
)


def classify_duration(
    duration: float | None,
    *,
    min_duration: float,
    max_duration: float,
    tolerance: float,
) -> tuple[str, str]:
    if duration is None:
        return "unknown", "无法从文件元数据读取时长"
    if min_duration <= duration <= max_duration:
        return "within", f"时长 {duration:.2f} 秒，符合 {min_duration:.0f}-{max_duration:.0f} 秒要求"
    if min_duration - tolerance <= duration < min_duration:
        return "slightly_short", f"时长 {duration:.2f} 秒，略低于 {min_duration:.0f} 秒，可按编码误差宽松处理"
    if max_duration < duration <= max_duration + tolerance:
        return "slightly_long", f"时长 {duration:.2f} 秒，略高于 {max_duration:.0f} 秒，可按编码误差宽松处理"
    if duration < min_duration:
        return "too_short", f"时长 {duration:.2f} 秒，明显低于 {min_duration:.0f} 秒要求"
    return "too_long", f"时长 {duration:.2f} 秒，明显超过 {max_duration:.0f} 秒要求"


def label_bool(value: bool) -> str:
    return "是" if value else "否"


def analyze_audio_file(
    path: str | Path,
    *,
    min_duration: float = 30.0,
    max_duration: float = 60.0,
    tolerance: float = 3.0,
) -> dict[str, Any]:
    audio_path = Path(path)
    errors: list[str] = []
    warnings: list[str] = []

    if not audio_path.exists():
        return {
            "status": "invalid",
            "technical_playable": False,
            "duration_status": "unknown",
            "errors": [f"文件不存在：{audio_path}"],
            "warnings": [],
            "path": str(audio_path),
            "display_tags": [{"label": "文件状态", "value": "文件不存在"}],
        }

    extension = audio_path.suffix.lower()
    supported_extension = extension in SUPPORTED_EXTENSIONS
    if not supported_extension:
        warnings.append(f"扩展名 {extension or '无'} 不在推荐支持列表内。")

    try:
        probe = ffprobe_full(audio_path)
    except AudioToolError as exc:
        return {
            "status": "invalid",
            "technical_playable": False,
            "duration_status": "unknown",
            "errors": [str(exc)],
            "warnings": warnings,
            "path": str(audio_path),
            "display_tags": [
                {"label": "文件格式", "value": extension or "未知"},
                {"label": "文件状态", "value": "无法解析音频"},
            ],
        }

    audio = first_audio_stream(probe)
    streams = audio_streams(probe)
    if not audio:
        errors.append("未检测到可解码音频流。")

    duration = safe_float(probe.get("format", {}).get("duration"))
    if duration is None and audio:
        duration = safe_float(audio.get("duration"))

    duration_status, duration_note = classify_duration(
        duration,
        min_duration=min_duration,
        max_duration=max_duration,
        tolerance=tolerance,
    )
    if duration_status == "unknown":
        warnings.append(duration_note)
    elif duration_status in {"too_short", "too_long"}:
        warnings.append(duration_note)

    volume: dict[str, Any] = {}
    silence: dict[str, Any] = {}
    if audio:
        sample_duration = min(duration if duration is not None else 60.0, 60.0)
        try:
            volume = volume_detect(audio_path, duration=sample_duration)
        except AudioToolError as exc:
            warnings.append(f"音量检测失败：{exc}")
        try:
            silence = silence_detect(audio_path, duration=min(duration if duration is not None else 120.0, 120.0))
        except AudioToolError as exc:
            warnings.append(f"静音检测失败：{exc}")

    bitrate = safe_int(audio.get("bit_rate") if audio else None) or safe_int(probe.get("format", {}).get("bit_rate"))
    sample_rate = safe_int(audio.get("sample_rate") if audio else None)
    channels = safe_int(audio.get("channels") if audio else None)
    non_audio_streams = [stream for stream in probe.get("streams", []) if stream.get("codec_type") != "audio"]
    has_video_stream = any(stream.get("codec_type") == "video" for stream in non_audio_streams)
    clipping_risk = bool(volume.get("histogram_0db_samples"))

    technical_playable = not errors and bool(audio)
    duration_acceptable = duration_status in {"within", "slightly_short", "slightly_long"}
    audio_info = {
        "file_name": audio_path.name,
        "file_size_bytes": audio_path.stat().st_size,
        "extension": extension,
        "supported_extension": supported_extension,
        "format_name": probe.get("format", {}).get("format_name"),
        "codec_name": audio.get("codec_name") if audio else None,
        "duration_seconds": rounded(duration, 3),
        "duration_label": format_duration(duration),
        "duration_status": duration_status,
        "duration_note": duration_note,
        "duration_acceptable": duration_acceptable,
        "sample_rate_hz": sample_rate,
        "channels": channels,
        "channel_layout": audio.get("channel_layout") if audio else None,
        "bit_rate_bps": bitrate,
        "audio_stream_count": len(streams),
        "non_audio_stream_count": len(non_audio_streams),
        "has_video_stream": has_video_stream,
        "mean_volume_db": volume.get("mean_volume_db"),
        "max_volume_db": volume.get("max_volume_db"),
        "histogram_0db_samples": volume.get("histogram_0db_samples"),
        "clipping_risk": clipping_risk,
        "silence_count_first_120s": silence.get("silence_count"),
        "total_silence_seconds_first_120s": silence.get("total_silence_seconds"),
    }

    display_tags = [
        {"label": "文件名", "value": audio_info["file_name"]},
        {"label": "文件格式", "value": audio_info["format_name"] or extension or "未知"},
        {"label": "支持格式", "value": label_bool(supported_extension)},
        {"label": "可播放音频流", "value": label_bool(technical_playable)},
        {"label": "音频时长", "value": audio_info["duration_label"]},
        {"label": "时长合规", "value": duration_note},
        {"label": "采样率", "value": f"{sample_rate} Hz" if sample_rate else "未知"},
        {"label": "声道数", "value": str(channels) if channels else "未知"},
        {"label": "编码格式", "value": audio_info["codec_name"] or "未知"},
        {"label": "码率", "value": f"{round(bitrate / 1000)} kbps" if bitrate else "未知"},
        {
            "label": "平均音量",
            "value": f"{volume.get('mean_volume_db')} dB" if volume.get("mean_volume_db") is not None else "未知",
        },
        {
            "label": "最大音量",
            "value": f"{volume.get('max_volume_db')} dB" if volume.get("max_volume_db") is not None else "未知",
        },
        {
            "label": "静音片段",
            "value": str(silence.get("silence_count")) if silence.get("silence_count") is not None else "未知",
        },
        {"label": "削波风险", "value": label_bool(clipping_risk)},
        {"label": "附带非音频流", "value": label_bool(has_video_stream)},
    ]

    return {
        "status": "ok" if technical_playable else "invalid",
        "technical_playable": technical_playable,
        "duration_status": duration_status,
        "duration_acceptable": duration_acceptable,
        "recommended_min_score_note": (
            "若音频内容基本围绕低碳生活且可听懂，按本技能宽松规则通常应给 80 分以上。"
            if technical_playable and duration_acceptable
            else "请结合内容听辨和提交有效性判断是否低于 80 分。"
        ),
        "min_duration_seconds": min_duration,
        "max_duration_seconds": max_duration,
        "duration_tolerance_seconds": tolerance,
        "path": str(audio_path),
        "audio": audio_info,
        "display_tags": display_tags,
        "errors": errors,
        "warnings": warnings,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract low-carbon audio/video media metadata.")
    parser.add_argument("audio", help="Path to student audio or video file.")
    parser.add_argument("--min-duration", type=float, default=30.0, help="Minimum target duration in seconds.")
    parser.add_argument("--max-duration", type=float, default=60.0, help="Maximum target duration in seconds.")
    parser.add_argument("--tolerance", type=float, default=3.0, help="Lenient duration tolerance in seconds.")
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    args = parser.parse_args()
    print_output(
        analyze_audio_file(
            args.audio,
            min_duration=args.min_duration,
            max_duration=args.max_duration,
            tolerance=args.tolerance,
        ),
        args.json,
    )


if __name__ == "__main__":
    main()
