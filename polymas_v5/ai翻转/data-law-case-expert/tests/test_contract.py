from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CORE_PATH = (
    ROOT
    / "data-law-case-maintenance"
    / "scripts"
    / "library_core.py"
)


def load_core():
    spec = importlib.util.spec_from_file_location("library_core", CORE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def minimal_case(**overrides):
    record = {
        "case_id": "DLCL-0001",
        "title": "虚假招聘侵害个人信息案",
        "scene_id": "scene-01",
        "record_type": "judicial_case",
        "jurisdiction": "中国",
        "case_status": "待核验",
        "basic_facts": "通过虚假招聘收集并出售简历。",
        "dispute_focus": None,
        "legal_provisions": [
            {
                "citation_text": "《个人信息保护法》第10条",
                "source_url": None,
                "evidence_status": "待补证",
            }
        ],
        "outcome_type": "judgment",
        "outcome": None,
        "outcome_evidence_status": "missing",
        "legal_analysis": "招聘平台应加强异常下载监测。",
        "analysis_origin": "source_material",
        "sources": [],
        "evidence_status": "待补证",
        "classification_review_required": True,
        "version": 1,
    }
    record.update(overrides)
    return record


class CaseContractTests(unittest.TestCase):
    def test_valid_case_has_no_contract_errors(self):
        core = load_core()
        self.assertEqual(core.validate_case(minimal_case()), [])

    def test_case_contract_rejects_outcome_without_evidence(self):
        core = load_core()
        errors = core.validate_case(
            minimal_case(outcome="判处有期徒刑三年", outcome_evidence_status="missing")
        )
        self.assertIn("outcome_requires_evidence", errors)

    def test_case_contract_requires_stable_case_id(self):
        core = load_core()
        errors = core.validate_case(minimal_case(case_id="虚假招聘侵害个人信息案"))
        self.assertIn("invalid_case_id", errors)

    def test_case_contract_requires_explicit_missing_fields(self):
        core = load_core()
        record = minimal_case()
        record.pop("dispute_focus")
        errors = core.validate_case(record)
        self.assertIn("missing_field:dispute_focus", errors)


if __name__ == "__main__":
    unittest.main()
