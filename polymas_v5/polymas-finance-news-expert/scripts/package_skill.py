#!/usr/bin/env python3
"""Create a deterministic, upload-ready archive for the finance-news Skill."""

from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_NAME = "finance-news-course-commentary"
SKILL_ROOT = ROOT / SKILL_NAME
INCLUDED_FILES = (
    "SKILL.md",
    "output_format/briefing.md",
    "references/data-contract.md",
    "references/source-policy.md",
    "scripts/normalize_candidates.py",
)
FIXED_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
HELP_TEXT = "生成可上传的财经新闻课程点评 Skill ZIP"
CREDENTIAL_PATTERNS = (
    re.compile(
        r"(?i)[\"']?[A-Za-z0-9_-]*(?:authorization|cookie|token|api[_-]?key|password|passwd|secret(?:[_-]access)?[_-]?key|private[_-]?key|client[_-]?secret|session(?:[_-]?(?:id|token))?|credential|access[_-]?key|database[_-]?url)[A-Za-z0-9_-]*[\"']?"
        r"\s*[:=]\s*[\"']?(?:(?:bearer|basic)\s+)?[A-Za-z0-9._~+/:@?&%=-]{8,}"
    ),
    re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"(?i)\bssh-(?:rsa|ed25519)\s+AAAA[A-Za-z0-9+/=]{8,}"),
    re.compile(r"(?i)\b[a-z][a-z0-9+.-]*://[^/\s:@]+:[^/\s@]+@"),
    re.compile(
        r"\b(?:(?:AKIA|ASIA)[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|xox[baprs]-[A-Za-z0-9-]{10,}|sk-[A-Za-z0-9_-]{20,})\b"
    ),
)


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message):  # pragma: no cover - exercised through the CLI.
        del message
        raise ValueError("invalid command-line arguments")


def archive_members() -> list[tuple[Path, str]]:
    """Return the sole allowlisted files, in stable archive-name order."""
    members = []
    for relative in INCLUDED_FILES:
        source = SKILL_ROOT / relative
        if not source.is_file():
            raise FileNotFoundError(f"缺少打包所需文件：{source}")
        archive_name = f"{SKILL_NAME}/{relative}"
        members.append((source, archive_name))
    return sorted(members, key=lambda member: member[1])


def contains_potential_credential(text: str) -> bool:
    """Fail closed on common credential assignments and token formats."""
    return any(pattern.search(text) for pattern in CREDENTIAL_PATTERNS)


def write_archive(output: Path) -> list[str]:
    members = archive_members()
    payloads = []
    for source, archive_name in members:
        body = source.read_bytes()
        try:
            text = body.decode("utf-8")
        except UnicodeDecodeError as error:
            raise ValueError(f"打包文件不是 UTF-8 文本：{archive_name}") from error
        if contains_potential_credential(text):
            raise ValueError(f"检测到疑似凭证，拒绝打包：{archive_name}")
        payloads.append((body, archive_name))

    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(
        output,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as archive:
        for body, archive_name in payloads:
            info = zipfile.ZipInfo(archive_name, date_time=FIXED_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            info.create_system = 3
            archive.writestr(info, body, compress_type=zipfile.ZIP_DEFLATED)
    return [archive_name for _, archive_name in members]


def parse_args(argv=None) -> argparse.Namespace:
    parser = JsonArgumentParser(description=HELP_TEXT, add_help=False)
    parser.add_argument("--help", action="store_true")
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / f"{SKILL_NAME}.zip",
        help="ZIP 输出路径",
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    try:
        args = parse_args(argv)
        if args.help:
            print(
                json.dumps(
                    {"help": HELP_TEXT, "options": ["--help", "--output"]},
                    ensure_ascii=False,
                    sort_keys=True,
                )
            )
            return 0
        members = write_archive(args.output)
    except (OSError, ValueError, zipfile.BadZipFile) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False))
        return 1
    print(
        json.dumps(
            {"output": str(args.output), "members": members}, ensure_ascii=False, sort_keys=True
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
