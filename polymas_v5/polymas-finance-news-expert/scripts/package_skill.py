#!/usr/bin/env python3
"""Create a deterministic, upload-ready archive for the finance-news Skill."""

from __future__ import annotations

import argparse
import json
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


def write_archive(output: Path) -> list[str]:
    output.parent.mkdir(parents=True, exist_ok=True)
    members = archive_members()
    with zipfile.ZipFile(
        output,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as archive:
        for source, archive_name in members:
            info = zipfile.ZipInfo(archive_name, date_time=FIXED_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            info.create_system = 3
            archive.writestr(info, source.read_bytes(), compress_type=zipfile.ZIP_DEFLATED)
    return [archive_name for _, archive_name in members]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="生成可上传的财经新闻课程点评 Skill ZIP")
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / f"{SKILL_NAME}.zip",
        help="ZIP 输出路径",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
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
