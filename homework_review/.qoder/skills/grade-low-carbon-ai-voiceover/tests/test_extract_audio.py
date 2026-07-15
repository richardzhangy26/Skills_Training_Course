from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from audio_common import SUPPORTED_EXTENSIONS
from extract_audio import analyze_audio_file


def _run_ffmpeg(*args: str) -> None:
    subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def test_video_extensions_are_supported() -> None:
    assert ".mp4" in SUPPORTED_EXTENSIONS
    assert ".mov" in SUPPORTED_EXTENSIONS


def test_mp4_with_audio_is_supported_and_playable(tmp_path: Path) -> None:
    submission = tmp_path / "submission.mp4"
    _run_ffmpeg(
        "-f",
        "lavfi",
        "-i",
        "color=c=green:s=160x90:d=1",
        "-f",
        "lavfi",
        "-i",
        "sine=frequency=440:duration=1",
        "-shortest",
        "-c:v",
        "mpeg4",
        "-c:a",
        "aac",
        str(submission),
    )

    result = analyze_audio_file(submission, min_duration=0.5, max_duration=2.0)

    assert result["status"] == "ok"
    assert result["technical_playable"] is True
    assert result["audio"]["supported_extension"] is True
    assert result["audio"]["has_video_stream"] is True
    assert not any("不在推荐支持列表" in item for item in result["warnings"])


def test_mp4_without_audio_is_invalid(tmp_path: Path) -> None:
    submission = tmp_path / "silent-video.mp4"
    _run_ffmpeg(
        "-f",
        "lavfi",
        "-i",
        "color=c=black:s=160x90:d=1",
        "-c:v",
        "mpeg4",
        "-an",
        str(submission),
    )

    result = analyze_audio_file(submission, min_duration=0.5, max_duration=2.0)

    assert result["status"] == "invalid"
    assert result["technical_playable"] is False
    assert "未检测到可解码音频流。" in result["errors"]
