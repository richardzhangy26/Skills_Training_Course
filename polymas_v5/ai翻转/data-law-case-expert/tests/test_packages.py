from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]
PACKAGER_PATH = ROOT / "scripts" / "package_skills.py"


def load_packager():
    spec = importlib.util.spec_from_file_location("package_skills", PACKAGER_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SkillPackageTests(unittest.TestCase):
    def test_skill_archives_have_one_root_and_no_local_residue(self):
        packager = load_packager()
        with tempfile.TemporaryDirectory() as tmp:
            report = packager.build_archives(ROOT, Path(tmp))
            self.assertEqual(len(report["archives"]), 2)

            for item in report["archives"]:
                archive = Path(item["path"])
                with ZipFile(archive) as zip_file:
                    names = zip_file.namelist()
                    roots = {name.split("/")[0] for name in names}
                    self.assertEqual(roots, {item["skill_name"]})
                    self.assertIn(f"{item['skill_name']}/SKILL.md", names)
                    self.assertFalse(any("__pycache__" in name for name in names))
                    self.assertFalse(any(name.endswith((".pyc", ".DS_Store")) for name in names))
                    self.assertFalse(any("/tests/" in name for name in names))
                    for name in names:
                        if name.endswith((".md", ".py", ".html", ".json")):
                            text = zip_file.read(name).decode("utf-8")
                            self.assertNotIn("/Users/", text)
                            self.assertNotIn("-----BEGIN PRIVATE KEY-----", text)

    def test_archive_listing_is_deterministic(self):
        packager = load_packager()
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            report_a = packager.build_archives(ROOT, Path(first))
            report_b = packager.build_archives(ROOT, Path(second))
            for left, right in zip(report_a["archives"], report_b["archives"]):
                self.assertEqual(left["sha256"], right["sha256"])

    def test_packager_rejects_symlinks_and_unknown_secret_files(self):
        packager = load_packager()
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            for skill_name in ("data-law-case-query", "data-law-case-maintenance"):
                shutil.copytree(ROOT / skill_name, project / skill_name)
            secret = Path(tmp) / "credentials.pem"
            secret.write_text(
                "-----BEGIN PRIVATE KEY-----\nsecret\n-----END PRIVATE KEY-----\n",
                encoding="utf-8",
            )
            os.symlink(
                secret,
                project / "data-law-case-query" / "scripts" / "credentials.pem",
            )
            with self.assertRaisesRegex(ValueError, "symlink_not_allowed"):
                packager.build_archives(project, Path(tmp) / "dist-a")

            (project / "data-law-case-query" / "scripts" / "credentials.pem").unlink()
            shutil.copy2(
                secret,
                project / "data-law-case-query" / "scripts" / "credentials.pem",
            )
            with self.assertRaisesRegex(ValueError, "unsupported_file_type"):
                packager.build_archives(project, Path(tmp) / "dist-b")

            (project / "data-law-case-query" / "scripts" / "credentials.pem").unlink()
            credential_json = project / "data-law-case-query" / "scripts" / "credentials.json"
            credential_json.write_text(
                '{"api_key":"sk-proj-abcdefghijklmnopqrstuvwxyz123456"}',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "credential_pattern"):
                packager.build_archives(project, Path(tmp) / "dist-c")

            credential_json.unlink()
            unquoted = project / "data-law-case-query" / "scripts" / "credentials.txt"
            unquoted.write_text(
                "API_KEY=abcdefghijklmnopqrstuvwxyz123456\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "credential_pattern"):
                packager.build_archives(project, Path(tmp) / "dist-d")


if __name__ == "__main__":
    unittest.main()
