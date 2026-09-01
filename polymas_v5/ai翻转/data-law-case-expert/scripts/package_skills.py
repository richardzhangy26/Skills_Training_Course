#!/usr/bin/env python3
"""为两个 Polymas Skill 构建确定性 ZIP。"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


SKILL_NAMES = ("data-law-case-query", "data-law-case-maintenance")
ALLOWED_SUFFIXES = {".md", ".py", ".html", ".json", ".txt"}
FORBIDDEN_BYTES = (
    b"/Users/",
    b"-----BEGIN PRIVATE KEY-----",
    b"-----BEGIN OPENSSH PRIVATE KEY-----",
    b"-----BEGIN RSA PRIVATE KEY-----",
    b"-----BEGIN EC PRIVATE KEY-----",
)
SECRET_PATTERNS = (
    re.compile(rb"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),
    re.compile(
        rb"(?i)\b(?:authorization|cookie)\s*[:=]\s*(?:bearer\s+)?[^\s,;]{8,}"
    ),
    re.compile(rb"\bsk-(?:proj-)?[A-Za-z0-9_-]{16,}\b"),
    re.compile(rb"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(rb"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(rb"\bxox[baprs]-[A-Za-z0-9-]{16,}\b"),
    re.compile(
        rb"(?i)[\"']?(?:api[_-]?key|access[_-]?token|client[_-]?secret|secret_key)[\"']?\s*[:=]\s*[\"'][^\"']{8,}[\"']"
    ),
)


def included_files(skill_dir: Path) -> list[Path]:
    files: list[Path] = []
    for path in skill_dir.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"symlink_not_allowed:{path.name}")
        if not path.is_file():
            continue
        relative = path.relative_to(skill_dir)
        if any(part.startswith(".") for part in relative.parts):
            continue
        if "__pycache__" in relative.parts:
            continue
        if path.suffix in {".pyc", ".pyo"} or path.name == ".DS_Store":
            continue
        if path.suffix.lower() not in ALLOWED_SUFFIXES:
            raise ValueError(f"unsupported_file_type:{path.name}")
        files.append(path)
    return sorted(files, key=lambda item: item.relative_to(skill_dir).as_posix())


def validate_content(path: Path, data: bytes) -> None:
    for marker in FORBIDDEN_BYTES:
        if marker in data:
            raise ValueError(f"forbidden_content:{path.name}")
    if any(pattern.search(data) for pattern in SECRET_PATTERNS):
        raise ValueError(f"credential_pattern:{path.name}")


def write_deterministic_zip(skill_dir: Path, archive: Path) -> None:
    archive.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(archive, "w", compression=ZIP_DEFLATED, compresslevel=9) as zip_file:
        for path in included_files(skill_dir):
            data = path.read_bytes()
            validate_content(path, data)
            relative = path.relative_to(skill_dir)
            arcname = f"{skill_dir.name}/{relative.as_posix()}"
            info = ZipInfo(arcname, date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            zip_file.writestr(info, data)


def build_archives(project_root: Path, output_dir: Path) -> dict[str, object]:
    project_root = Path(project_root)
    output_dir = Path(output_dir)
    archives: list[dict[str, object]] = []
    for skill_name in SKILL_NAMES:
        skill_dir = project_root / skill_name
        if not (skill_dir / "SKILL.md").is_file():
            raise ValueError(f"missing_skill:{skill_name}")
        archive = output_dir / f"{skill_name}-1.0.0.zip"
        write_deterministic_zip(skill_dir, archive)
        archives.append(
            {
                "skill_name": skill_name,
                "version": "1.0.0",
                "path": str(archive),
                "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
                "file_count": len(included_files(skill_dir)),
            }
        )
    return {"status": "packaged", "archives": archives}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    try:
        print(
            json.dumps(
                build_archives(args.project_root, args.output_dir),
                ensure_ascii=False,
            )
        )
        return 0
    except Exception as exc:  # pragma: no cover - CLI adapter
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        print(repr(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
