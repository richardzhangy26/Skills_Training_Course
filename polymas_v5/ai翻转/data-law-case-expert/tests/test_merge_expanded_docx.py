from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SUMMARY_DOCX = ROOT.parent / "案例提炼汇总.docx"
EXPANDED_DOCX = ROOT.parent / "AI时代一体化数字营销与法律回望.docx"
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


class ExpandedDocumentMergeTests(unittest.TestCase):
    def test_expanded_cases_enrich_without_increasing_case_count(self):
        extractor = load_extractor()
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            extractor.extract_summary(SUMMARY_DOCX, output)
            report = extractor.merge_expanded_document(
                EXPANDED_DOCX, output, allow_bootstrap_merge=True
            )

            self.assertEqual(report["total_after_merge"], 77)
            self.assertEqual(report["matched_count"], 4)
            self.assertEqual(report["unmatched_count"], 0)
            self.assertEqual(report["review_required_count"], 1)

    def test_source_backed_outcomes_merge_but_speculation_stays_null(self):
        extractor = load_extractor()
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            extractor.extract_summary(SUMMARY_DOCX, output)
            extractor.merge_expanded_document(
                EXPANDED_DOCX, output, allow_bootstrap_merge=True
            )
            cases = [
                json.loads(path.read_text(encoding="utf-8"))
                for path in sorted((output / "data" / "cases").glob("*.json"))
            ]
            app_case = next(case for case in cases if case["title"].startswith("App 强制"))
            aeo_case = next(case for case in cases if case["title"].startswith("AEO/GEO"))

            self.assertIn("构成侵权", app_case["outcome"])
            self.assertEqual(app_case["outcome_evidence_status"], "source_material")
            self.assertIsNone(aeo_case["outcome"])
            self.assertEqual(aeo_case["outcome_evidence_status"], "missing")

            review_queue = json.loads(
                (output / "data" / "review-queue.json").read_text(encoding="utf-8")
            )
            self.assertEqual(review_queue[0]["case_id"], aeo_case["case_id"])
            self.assertEqual(review_queue[0]["reason"], "speculative_outcome")
            self.assertNotIn("fact_detail", app_case)
            self.assertNotIn("analysis_detail", app_case)


if __name__ == "__main__":
    unittest.main()
