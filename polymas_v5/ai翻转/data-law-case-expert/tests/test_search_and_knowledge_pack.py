from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
LIBRARY_ROOT = ROOT / "case-library"
SEARCH_PATH = ROOT / "data-law-case-query" / "scripts" / "search_cases.py"
PACK_PATH = (
    ROOT
    / "data-law-case-maintenance"
    / "scripts"
    / "build_knowledge_pack.py"
)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def library_cases():
    return [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted((LIBRARY_ROOT / "data" / "cases").glob("*.json"))
    ]


class SearchAndKnowledgePackTests(unittest.TestCase):
    def test_ambiguous_query_returns_candidates_not_one_guess(self):
        search = load_module("search_cases", SEARCH_PATH)
        matches = search.search_cases("招聘案", library_cases(), limit=5)

        self.assertGreater(len(matches), 1)
        self.assertLessEqual(len(matches), 5)
        self.assertTrue(all(item["case_id"].startswith("DLCL-") for item in matches))

    def test_exact_title_is_first_and_returns_evidence_fields(self):
        search = load_module("search_cases", SEARCH_PATH)
        matches = search.search_cases(
            "虚假招聘侵害个人信息案涉及哪些法律条文", library_cases(), limit=5
        )

        self.assertEqual(matches[0]["case_id"], "DLCL-0001")
        self.assertIn("legal_provisions", matches[0])
        self.assertEqual(matches[0]["evidence_status"], "待补证")

    def test_unrelated_query_returns_empty_list(self):
        search = load_module("search_cases", SEARCH_PATH)
        self.assertEqual(search.search_cases("量子引力波天文学", library_cases()), [])

    def test_bundled_index_answers_without_workspace_library(self):
        search = load_module("search_cases", SEARCH_PATH)
        cases = search.load_cases(None)
        matches = search.search_cases("虚假招聘侵害个人信息案", cases, limit=5)
        self.assertGreaterEqual(len(cases), 1)
        self.assertEqual(matches[0]["title"], "虚假招聘侵害个人信息案")
        self.assertIn("个人信息保护法", json.dumps(matches[0], ensure_ascii=False))
        moon = search.search_cases("请在当前案例库查询《月球居民量子人格数据案》", cases, limit=5)
        self.assertEqual(moon, [])

    def test_embedded_json_loads_when_file_missing(self, tmp_path=None):
        search = load_module("search_cases", SEARCH_PATH)
        original = search.BUNDLED_CASES
        search.BUNDLED_CASES = Path("/tmp/does-not-exist-published-cases.json")
        try:
            cases = search.load_cases(None)
        finally:
            search.BUNDLED_CASES = original
        self.assertGreaterEqual(len(cases), 1)
        self.assertEqual(cases[0]["title"], "虚假招聘侵害个人信息案")

    def test_knowledge_pack_has_one_traceable_block_per_case(self):
        packer = load_module("build_knowledge_pack", PACK_PATH)
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "knowledge.jsonl"
            report = packer.build_knowledge_pack(LIBRARY_ROOT, output)
            lines = output.read_text(encoding="utf-8").splitlines()
            records = [json.loads(line) for line in lines]

            self.assertEqual(report["block_count"], 77)
            self.assertEqual(len(records), 77)
            self.assertEqual(records[0]["knowledge_id"], "case:DLCL-0001:v1")
            self.assertEqual(records[0]["metadata"]["case_id"], "DLCL-0001")
            self.assertIn("虚假招聘侵害个人信息案", records[0]["content"])
            self.assertIn("证据状态：待补证", records[0]["content"])


if __name__ == "__main__":
    unittest.main()
