from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DOCX = ROOT.parent / "案例提炼汇总.docx"
EXTRACTOR_PATH = (
    ROOT
    / "data-law-case-maintenance"
    / "scripts"
    / "extract_source_docx.py"
)


def load_extractor():
    spec = importlib.util.spec_from_file_location("extract_source_docx", EXTRACTOR_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SourceExtractionTests(unittest.TestCase):
    def test_extracts_ten_scenes_and_seventy_seven_cases(self):
        extractor = load_extractor()
        with tempfile.TemporaryDirectory() as tmp:
            report = extractor.extract_summary(SOURCE_DOCX, Path(tmp))

            self.assertEqual(report["scene_count"], 10)
            self.assertEqual(report["case_count"], 77)
            self.assertEqual(
                report["scene_case_counts"],
                [12, 7, 5, 3, 4, 3, 3, 3, 35, 2],
            )

    def test_writes_one_json_file_per_case_with_stable_ids(self):
        extractor = load_extractor()
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            extractor.extract_summary(SOURCE_DOCX, output)
            case_paths = sorted((output / "data" / "cases").glob("DLCL-*.json"))

            self.assertEqual(len(case_paths), 77)
            self.assertEqual(case_paths[0].stem, "DLCL-0001")
            self.assertEqual(case_paths[-1].stem, "DLCL-0077")
            first_case = json.loads(case_paths[0].read_text(encoding="utf-8"))
            self.assertEqual(first_case["title"], "虚假招聘侵害个人信息案")
            self.assertIn("3.7 万余条", first_case["basic_facts"])
            self.assertIsNone(first_case["dispute_focus"])
            self.assertIsNone(first_case["outcome"])
            self.assertEqual(first_case["evidence_status"], "待补证")

    def test_preserves_scene_names_and_manifest_source(self):
        extractor = load_extractor()
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            extractor.extract_summary(SOURCE_DOCX, output)
            scenes = json.loads(
                (output / "data" / "scenes.json").read_text(encoding="utf-8")
            )
            manifest = json.loads(
                (output / "data" / "manifest.json").read_text(encoding="utf-8")
            )

            self.assertEqual(
                scenes[0]["name"], "就业、劳动管理与跨境 HR 数据场景"
            )
            self.assertEqual(
                scenes[-1]["name"],
                "公共数据授权运营、开放利用与行政垄断风险防范场景",
            )
            self.assertEqual(manifest["source_file"], SOURCE_DOCX.name)
            self.assertEqual(manifest["library_version"], 1)

    def test_jurisdiction_inference_handles_diacritics_and_unknowns(self):
        extractor = load_extractor()
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            extractor.extract_summary(SOURCE_DOCX, output)
            cases = [
                json.loads(path.read_text(encoding="utf-8"))
                for path in sorted((output / "data" / "cases").glob("*.json"))
            ]

            self.assertEqual(cases[0]["jurisdiction"], "中国")
            self.assertEqual(cases[9]["jurisdiction"], "欧盟或欧洲国家")
            self.assertEqual(cases[73]["jurisdiction"], "以色列")


if __name__ == "__main__":
    unittest.main()
