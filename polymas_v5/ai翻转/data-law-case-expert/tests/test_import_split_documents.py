from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPLIT_ROOT = ROOT.parent / "案例拆分文档"
IMPORTER_PATH = (
    ROOT
    / "data-law-case-maintenance"
    / "scripts"
    / "import_split_documents.py"
)


def load_importer():
    spec = importlib.util.spec_from_file_location("import_split_documents", IMPORTER_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SplitDocumentImportTests(unittest.TestCase):
    def test_imports_index_and_seventy_seven_individual_documents(self):
        importer = load_importer()
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "library"
            report = importer.import_split_documents(SPLIT_ROOT, output)

            self.assertEqual(report["scene_count"], 10)
            self.assertEqual(report["case_count"], 77)
            self.assertEqual(report["source_document_count"], 77)
            self.assertEqual(
                report["scene_case_counts"],
                [12, 7, 5, 3, 4, 3, 3, 3, 35, 2],
            )

    def test_uses_detailed_case_material_as_canonical_fields(self):
        importer = load_importer()
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "library"
            importer.import_split_documents(SPLIT_ROOT, output)
            first = json.loads(
                (output / "data" / "cases" / "DLCL-0001.json").read_text(encoding="utf-8")
            )
            child = json.loads(
                (output / "data" / "cases" / "DLCL-0028.json").read_text(encoding="utf-8")
            )

            self.assertIn("检察机关向人社、市场监管部门制发检察建议", first["basic_facts"])
            self.assertIn("儿童个人信息能否用于画像", child["dispute_focus"])
            self.assertIn("杭州互联网法院", child["outcome"])
            self.assertEqual(child["outcome_evidence_status"], "source_material")
            self.assertNotIn("fact_detail", child)
            self.assertNotIn("analysis_detail", child)
            self.assertTrue(
                first["sources"][0]["title"].startswith("场景01_案例01_")
            )
            surveillance = json.loads(
                (output / "data" / "cases" / "DLCL-0004.json").read_text(encoding="utf-8")
            )
            self.assertIn("法院判令公司销毁相关视频资料", surveillance["outcome"])
            self.assertNotIn("法院判令公司销毁相关视频资料", surveillance["basic_facts"])
            self.assertEqual(surveillance["case_status"], "已发布")

    def test_speculative_result_stays_in_review_queue(self):
        importer = load_importer()
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "library"
            importer.import_split_documents(SPLIT_ROOT, output)
            aeo = json.loads(
                (output / "data" / "cases" / "DLCL-0034.json").read_text(encoding="utf-8")
            )
            review_queue = json.loads(
                (output / "data" / "review-queue.json").read_text(encoding="utf-8")
            )

            self.assertIsNone(aeo["outcome"])
            review_by_id = {item["case_id"]: item for item in review_queue}
            self.assertEqual(
                set(review_by_id), {"DLCL-0023", "DLCL-0024", "DLCL-0034"}
            )
            self.assertEqual(review_by_id["DLCL-0034"]["reason"], "speculative_outcome")
            genetics = json.loads(
                (output / "data" / "cases" / "DLCL-0024.json").read_text(encoding="utf-8")
            )
            self.assertIsNone(genetics["outcome"])

    def test_missing_split_document_fails_closed(self):
        importer = load_importer()
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source"
            shutil.copytree(SPLIT_ROOT, source)
            next(source.glob("场景10_案例02_*.docx")).unlink()
            with self.assertRaisesRegex(ValueError, "expected_77_case_documents"):
                importer.import_split_documents(source, Path(tmp) / "library")

    def test_importer_refuses_to_overwrite_existing_library(self):
        importer = load_importer()
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "library"
            importer.import_split_documents(SPLIT_ROOT, output)
            with self.assertRaisesRegex(ValueError, "bootstrap_target_not_empty"):
                importer.import_split_documents(SPLIT_ROOT, output)


if __name__ == "__main__":
    unittest.main()
