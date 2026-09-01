from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
from copy import deepcopy
import fcntl
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
SOURCE_LIBRARY = ROOT / "case-library"
PREPARE_PATH = (
    ROOT
    / "data-law-case-maintenance"
    / "scripts"
    / "prepare_update.py"
)
PUBLISH_PATH = (
    ROOT
    / "data-law-case-maintenance"
    / "scripts"
    / "publish_update.py"
)
RENDER_PATH = (
    ROOT
    / "data-law-case-maintenance"
    / "scripts"
    / "render_html.py"
)
PACK_PATH = (
    ROOT
    / "data-law-case-maintenance"
    / "scripts"
    / "build_knowledge_pack.py"
)
SEARCH_PATH = ROOT / "data-law-case-query" / "scripts" / "search_cases.py"
ROLLBACK_PATH = (
    ROOT
    / "data-law-case-maintenance"
    / "scripts"
    / "rollback_release.py"
)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def copy_library(tmp: str) -> Path:
    target = Path(tmp) / "library"
    shutil.copytree(SOURCE_LIBRARY, target)
    return target


def new_candidate():
    return {
        "title": "招聘平台批量下载异常监测教学案例",
        "scene_id": "scene-01",
        "record_type": "compliance_event",
        "jurisdiction": "中国",
        "basic_facts": "某招聘平台在内部审计中发现账号短时批量下载简历。",
        "dispute_focus": "平台应采取哪些安全管理措施？",
        "legal_provisions": [
            {
                "citation_text": "《个人信息保护法》第51条",
                "source_url": None,
                "evidence_status": "待补证",
            }
        ],
        "outcome_type": "not_applicable",
        "outcome": None,
        "outcome_evidence_status": "missing",
        "legal_analysis": "应采取最小权限、下载阈值与异常告警。",
        "analysis_origin": "teacher_confirmed",
        "sources": [],
        "evidence_status": "待补证",
    }


class UpdatePipelineTests(unittest.TestCase):
    def test_prepare_marks_duplicate_with_differences_unresolved(self):
        prepare = load_module("prepare_update", PREPARE_PATH)
        with tempfile.TemporaryDirectory() as tmp:
            library = copy_library(tmp)
            candidate = new_candidate()
            candidate["title"] = "虚假招聘侵害个人信息案"
            candidate["basic_facts"] = "与原记录不同的新材料。"
            preview = prepare.prepare_update([candidate], 1, library)

            self.assertEqual(preview["status"], "needs_resolution")
            self.assertEqual(preview["unresolved_count"], 1)
            self.assertEqual(preview["changes"][0]["action"], "possible_duplicate")
            self.assertIn("basic_facts", preview["changes"][0]["differences"])

    def test_prepare_requires_scene_resolution(self):
        prepare = load_module("prepare_update", PREPARE_PATH)
        with tempfile.TemporaryDirectory() as tmp:
            library = copy_library(tmp)
            candidate = new_candidate()
            candidate.pop("scene_id")
            candidate["scene_candidates"] = ["scene-01", "scene-06"]
            preview = prepare.prepare_update([candidate], 1, library)

            self.assertEqual(preview["status"], "needs_resolution")
            self.assertEqual(preview["changes"][0]["action"], "scene_confirmation_required")

    def test_prepare_detects_renamed_fact_duplicate_and_update_title_collision(self):
        prepare = load_module("prepare_update", PREPARE_PATH)
        with tempfile.TemporaryDirectory() as tmp:
            library = copy_library(tmp)
            first = json.loads(
                (library / "data" / "cases" / "DLCL-0001.json").read_text(encoding="utf-8")
            )
            second = json.loads(
                (library / "data" / "cases" / "DLCL-0002.json").read_text(encoding="utf-8")
            )
            renamed = new_candidate()
            renamed["title"] = "换了名称但事实相同的招聘案例"
            renamed["basic_facts"] = first["basic_facts"]
            duplicate = prepare.prepare_update([renamed], 1, library)

            collision = prepare.prepare_update(
                [
                    {
                        "operation": "update",
                        "target_case_id": "DLCL-0001",
                        "title": "智联招聘员工参与倒卖简历案",
                    }
                ],
                1,
                library,
            )
            fact_collision = prepare.prepare_update(
                [
                    {
                        "operation": "update",
                        "target_case_id": "DLCL-0001",
                        "basic_facts": second["basic_facts"],
                    }
                ],
                1,
                library,
            )
            batch_first = new_candidate()
            batch_second = deepcopy(batch_first)
            batch = prepare.prepare_update([batch_first, batch_second], 1, library)

            self.assertEqual(duplicate["status"], "needs_resolution")
            self.assertEqual(duplicate["changes"][0]["action"], "possible_duplicate")
            self.assertEqual(duplicate["changes"][0]["match_basis"], "basic_facts")
            self.assertEqual(collision["status"], "needs_resolution")
            self.assertEqual(collision["changes"][0]["action"], "title_collision")
            self.assertEqual(fact_collision["status"], "needs_resolution")
            self.assertEqual(fact_collision["changes"][0]["action"], "fact_collision")
            self.assertEqual(batch["status"], "needs_resolution")
            self.assertEqual(batch["changes"][1]["action"], "possible_duplicate")
            self.assertEqual(batch["changes"][1]["matched_candidate_index"], 1)

    def test_prepare_blocks_nested_sensitive_content(self):
        prepare = load_module("prepare_update", PREPARE_PATH)
        with tempfile.TemporaryDirectory() as tmp:
            library = copy_library(tmp)
            candidate = new_candidate()
            candidate["basic_facts"] = "联系人手机号为13812345678。"
            candidate["sources"] = [
                {"title": "内部材料", "note": "Authorization: Bearer secret-token-value"}
            ]
            preview = prepare.prepare_update([candidate], 1, library)

            self.assertEqual(preview["status"], "needs_resolution")
            self.assertEqual(
                preview["changes"][0]["action"],
                "sensitive_content_review_required",
            )
            self.assertIn("phone_number", preview["changes"][0]["sensitive_markers"])
            self.assertIn("authorization_credential", preview["changes"][0]["sensitive_markers"])
            serialized = json.dumps(preview, ensure_ascii=False)
            self.assertNotIn("13812345678", serialized)
            self.assertNotIn("secret-token-value", serialized)

    def test_prepare_rejects_unbacked_official_evidence_claim(self):
        prepare = load_module("prepare_update", PREPARE_PATH)
        with tempfile.TemporaryDirectory() as tmp:
            library = copy_library(tmp)
            candidate = new_candidate()
            candidate["evidence_status"] = "官方来源已核验"
            candidate["sources"] = []
            preview = prepare.prepare_update([candidate], 1, library)

            self.assertEqual(preview["status"], "needs_resolution")
            self.assertEqual(preview["changes"][0]["action"], "evidence_review_required")
            self.assertIn(
                "official_evidence_requires_source",
                preview["changes"][0]["evidence_errors"],
            )

    def test_prepare_rejects_speculative_or_unbacked_source_outcome(self):
        prepare = load_module("prepare_update", PREPARE_PATH)
        with tempfile.TemporaryDirectory() as tmp:
            library = copy_library(tmp)
            speculative = new_candidate()
            speculative["outcome"] = "若进入司法程序，平台可能被判承担责任。"
            speculative["outcome_evidence_status"] = "source_material"
            speculative["sources"] = [{"title": "教师材料", "source_tier": "source_material"}]
            speculative_preview = prepare.prepare_update([speculative], 1, library)

            unbacked = new_candidate()
            unbacked["outcome"] = "监管机构作出处罚。"
            unbacked["outcome_evidence_status"] = "source_material"
            unbacked["sources"] = []
            unbacked_preview = prepare.prepare_update([unbacked], 1, library)

            self.assertIn(
                "speculative_outcome_requires_review",
                speculative_preview["changes"][0]["evidence_errors"],
            )
            self.assertIn(
                "source_outcome_requires_source",
                unbacked_preview["changes"][0]["evidence_errors"],
            )

    def test_prepare_blocks_email_student_id_and_minor_name(self):
        prepare = load_module("prepare_update", PREPARE_PATH)
        with tempfile.TemporaryDirectory() as tmp:
            library = copy_library(tmp)
            candidate = new_candidate()
            candidate["basic_facts"] = (
                "学生ID：2023123456；邮箱：student@example.edu；未成年人姓名：张小明。"
            )
            preview = prepare.prepare_update([candidate], 1, library)
            markers = preview["changes"][0]["sensitive_markers"]

            self.assertIn("student_identifier", markers)
            self.assertIn("email_address", markers)
            self.assertIn("minor_name", markers)
            serialized = json.dumps(preview, ensure_ascii=False)
            self.assertNotIn("2023123456", serialized)
            self.assertNotIn("student@example.edu", serialized)
            self.assertNotIn("张小明", serialized)

    def test_publish_rejects_unconfirmed_and_stale_changes(self):
        prepare = load_module("prepare_update", PREPARE_PATH)
        publish = load_module("publish_update", PUBLISH_PATH)
        with tempfile.TemporaryDirectory() as tmp:
            library = copy_library(tmp)
            change_set = prepare.prepare_update([new_candidate()], 1, library)

            self.assertEqual(
                publish.publish_update(change_set, False, library)["status"],
                "awaiting_confirmation",
            )
            manifest_path = library / "data" / "manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["library_version"] = 2
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
            self.assertEqual(
                publish.publish_update(
                    change_set,
                    True,
                    library,
                    confirmation_change_set_id=change_set["change_set_id"],
                )["status"],
                "version_conflict",
            )

    def test_confirmed_update_creates_release_and_keeps_old_version(self):
        prepare = load_module("prepare_update", PREPARE_PATH)
        publish = load_module("publish_update", PUBLISH_PATH)
        with tempfile.TemporaryDirectory() as tmp:
            library = copy_library(tmp)
            change_set = prepare.prepare_update([new_candidate()], 1, library)
            result = publish.publish_update(
                change_set,
                True,
                library,
                confirmation_change_set_id=change_set["change_set_id"],
            )

            self.assertEqual(result["status"], "artifact_ready_knowledge_pending")
            self.assertEqual(result["library_version"], 2)
            self.assertEqual(result["case_count"], 78)
            self.assertEqual(result["knowledge_sync_status"], "not_verified")
            current = json.loads((library / "current.json").read_text(encoding="utf-8"))
            self.assertEqual(current["release"], "v0002")
            self.assertTrue((library / "releases" / "v0001" / "data").is_dir())
            self.assertTrue(
                (library / "releases" / "v0002" / "exports" / "数据法学案例库.html").is_file()
            )
            self.assertEqual(
                len(list((library / "releases" / "v0002" / "data" / "cases").glob("*.json"))),
                78,
            )

    def test_all_consumers_follow_current_release_pointer(self):
        prepare = load_module("prepare_update", PREPARE_PATH)
        publish = load_module("publish_update", PUBLISH_PATH)
        renderer = load_module("render_html", RENDER_PATH)
        packer = load_module("build_knowledge_pack", PACK_PATH)
        search = load_module("search_cases", SEARCH_PATH)
        with tempfile.TemporaryDirectory() as tmp:
            library = copy_library(tmp)
            change_set = prepare.prepare_update([new_candidate()], 1, library)
            publish.publish_update(
                change_set,
                True,
                library,
                confirmation_change_set_id=change_set["change_set_id"],
            )

            html_report = renderer.render_library(library, Path(tmp) / "current.html")
            pack_report = packer.build_knowledge_pack(library, Path(tmp) / "current.jsonl")
            active_cases = search.load_cases(library)

            self.assertEqual(html_report["case_count"], 78)
            self.assertEqual(pack_report["block_count"], 78)
            self.assertEqual(len(active_cases), 78)
            self.assertEqual(active_cases[-1]["title"], new_candidate()["title"])

    def test_pointer_failure_removes_orphan_candidate_release(self):
        prepare = load_module("prepare_update", PREPARE_PATH)
        publish = load_module("publish_update", PUBLISH_PATH)
        with tempfile.TemporaryDirectory() as tmp:
            library = copy_library(tmp)
            change_set = prepare.prepare_update([new_candidate()], 1, library)
            with patch.object(publish.os, "replace", side_effect=OSError("pointer failed")):
                with self.assertRaises(OSError):
                    publish.publish_update(
                        change_set,
                        True,
                        library,
                        confirmation_change_set_id=change_set["change_set_id"],
                    )

            self.assertFalse((library / "current.json").exists())
            self.assertFalse((library / "releases" / "v0002").exists())
            self.assertEqual(len(list((library / "data" / "cases").glob("*.json"))), 77)

    def test_update_preserves_case_id_and_increments_case_version(self):
        prepare = load_module("prepare_update", PREPARE_PATH)
        publish = load_module("publish_update", PUBLISH_PATH)
        with tempfile.TemporaryDirectory() as tmp:
            library = copy_library(tmp)
            candidate = {
                "operation": "update",
                "target_case_id": "DLCL-0001",
                "basic_facts": "教师依据补充材料确认后的修订案情。",
                "evidence_status": "材料已核对",
            }
            change_set = prepare.prepare_update([candidate], 1, library)
            self.assertEqual(change_set["changes"][0]["action"], "update")
            result = publish.publish_update(
                change_set,
                True,
                library,
                confirmation_change_set_id=change_set["change_set_id"],
            )

            self.assertEqual(result["case_count"], 77)
            updated = json.loads(
                (library / "releases" / "v0002" / "data" / "cases" / "DLCL-0001.json").read_text(encoding="utf-8")
            )
            self.assertEqual(updated["case_id"], "DLCL-0001")
            self.assertEqual(updated["version"], 2)
            self.assertEqual(updated["basic_facts"], candidate["basic_facts"])

    def test_withdraw_hides_case_from_student_artifacts_and_search(self):
        prepare = load_module("prepare_update", PREPARE_PATH)
        publish = load_module("publish_update", PUBLISH_PATH)
        search = load_module("search_cases", SEARCH_PATH)
        with tempfile.TemporaryDirectory() as tmp:
            library = copy_library(tmp)
            change_set = prepare.prepare_update(
                [{"operation": "withdraw", "target_case_id": "DLCL-0001"}],
                1,
                library,
            )
            result = publish.publish_update(
                change_set,
                True,
                library,
                confirmation_change_set_id=change_set["change_set_id"],
            )
            html = Path(result["html_path"]).read_text(encoding="utf-8")
            active_cases = search.load_cases(library)

            self.assertEqual(result["case_count"], 77)
            self.assertEqual(result["visible_case_count"], 76)
            self.assertNotIn('data-case-id="DLCL-0001"', html)
            self.assertNotIn("DLCL-0001", {case["case_id"] for case in active_cases})

    def test_delete_records_audit_and_rollback_restores_old_release(self):
        prepare = load_module("prepare_update", PREPARE_PATH)
        publish = load_module("publish_update", PUBLISH_PATH)
        rollback = load_module("rollback_release", ROLLBACK_PATH)
        search = load_module("search_cases", SEARCH_PATH)
        with tempfile.TemporaryDirectory() as tmp:
            library = copy_library(tmp)
            change_set = prepare.prepare_update(
                [{"operation": "delete", "target_case_id": "DLCL-0001"}],
                1,
                library,
                actor_reference="audit:test-teacher",
            )
            result = publish.publish_update(
                change_set,
                True,
                library,
                confirmation_change_set_id=change_set["change_set_id"],
            )

            self.assertEqual(result["case_count"], 76)
            self.assertNotIn("audit:test-teacher", Path(result["html_path"]).read_text(encoding="utf-8"))
            self.assertTrue(
                (library / "releases" / "v0002" / "data" / "deletion-audit.jsonl").is_file()
            )
            audit = json.loads(
                (library / "releases" / "v0002" / "data" / "deletion-audit.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()[-1]
            )
            self.assertIn("deleted_at", audit)
            self.assertEqual(audit["actor_reference"], "audit:test-teacher")
            rollback_plan = rollback.prepare_rollback(
                library, 1, actor_reference="audit:test-teacher"
            )
            self.assertEqual(
                rollback.rollback_release(
                    library,
                    1,
                    False,
                    actor_reference="audit:test-teacher",
                )["status"],
                "awaiting_confirmation",
            )
            rollback_result = rollback.rollback_release(
                library,
                1,
                True,
                rollback_plan["rollback_confirmation_id"],
                "audit:test-teacher",
            )
            self.assertEqual(rollback_result["status"], "artifact_ready_knowledge_pending")
            self.assertEqual(rollback_result["library_version"], 1)
            self.assertEqual(len(search.load_cases(library)), 77)

    def test_confirmation_is_bound_to_immutable_change_set(self):
        prepare = load_module("prepare_update", PREPARE_PATH)
        publish = load_module("publish_update", PUBLISH_PATH)
        with tempfile.TemporaryDirectory() as tmp:
            library = copy_library(tmp)
            change_set = prepare.prepare_update([new_candidate()], 1, library)

            missing_binding = publish.publish_update(
                change_set, True, library, confirmation_change_set_id=None
            )
            self.assertEqual(missing_binding["status"], "confirmation_mismatch")

            tampered = deepcopy(change_set)
            tampered["changes"][0]["candidate"]["basic_facts"] = "确认后被替换的内容"
            invalid = publish.publish_update(
                tampered,
                True,
                library,
                confirmation_change_set_id=change_set["change_set_id"],
            )
            self.assertEqual(invalid["status"], "invalid_change_set")

    def test_publish_confirmation_is_single_use_even_after_rollback(self):
        prepare = load_module("prepare_update", PREPARE_PATH)
        publish = load_module("publish_update", PUBLISH_PATH)
        rollback = load_module("rollback_release", ROLLBACK_PATH)
        with tempfile.TemporaryDirectory() as tmp:
            library = copy_library(tmp)
            change_set = prepare.prepare_update([new_candidate()], 1, library)
            first = publish.publish_update(
                change_set,
                True,
                library,
                confirmation_change_set_id=change_set["change_set_id"],
            )
            self.assertEqual(first["status"], "artifact_ready_knowledge_pending")
            rollback_plan = rollback.prepare_rollback(
                library,
                1,
                actor_reference="audit:test-teacher",
                confirmation_nonce="rollback-once",
            )
            rollback.rollback_release(
                library,
                1,
                True,
                rollback_plan["rollback_confirmation_id"],
                "audit:test-teacher",
                "rollback-once",
            )
            replay = publish.publish_update(
                change_set,
                True,
                library,
                confirmation_change_set_id=change_set["change_set_id"],
            )
            self.assertEqual(replay["status"], "confirmation_already_used")

    def test_candidate_release_is_validated_before_pointer_switch(self):
        prepare = load_module("prepare_update", PREPARE_PATH)
        publish = load_module("publish_update", PUBLISH_PATH)
        with tempfile.TemporaryDirectory() as tmp:
            library = copy_library(tmp)
            change_set = prepare.prepare_update([new_candidate()], 1, library)

            def corrupt_pack(library_root, output_path):
                Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                Path(output_path).write_text("", encoding="utf-8")
                return {"status": "artifact_ready_knowledge_pending", "block_count": 0}

            with patch.object(publish, "build_knowledge_pack", side_effect=corrupt_pack):
                with self.assertRaisesRegex(ValueError, "candidate_release_invalid"):
                    publish.publish_update(
                        change_set,
                        True,
                        library,
                        confirmation_change_set_id=change_set["change_set_id"],
                    )
            self.assertFalse((library / "current.json").exists())
            self.assertFalse((library / "releases" / "v0002").exists())

    def test_unresolved_state_is_derived_from_changes_not_trusted_counter(self):
        prepare = load_module("prepare_update", PREPARE_PATH)
        publish = load_module("publish_update", PUBLISH_PATH)
        with tempfile.TemporaryDirectory() as tmp:
            library = copy_library(tmp)
            sensitive = new_candidate()
            sensitive["title"] = "包含敏感内容的候选"
            sensitive["basic_facts"] = "联系人手机号为13812345678。"
            change_set = prepare.prepare_update([new_candidate(), sensitive], 1, library)
            tampered = deepcopy(change_set)
            tampered["unresolved_count"] = 0
            result = publish.publish_update(
                tampered,
                True,
                library,
                confirmation_change_set_id=change_set["change_set_id"],
            )

            self.assertEqual(result["status"], "unresolved_changes")
            self.assertFalse((library / "current.json").exists())

    def test_publish_after_rollback_allocates_new_monotonic_release(self):
        prepare = load_module("prepare_update", PREPARE_PATH)
        publish = load_module("publish_update", PUBLISH_PATH)
        rollback = load_module("rollback_release", ROLLBACK_PATH)
        with tempfile.TemporaryDirectory() as tmp:
            library = copy_library(tmp)
            first = prepare.prepare_update([new_candidate()], 1, library)
            publish.publish_update(
                first,
                True,
                library,
                confirmation_change_set_id=first["change_set_id"],
            )
            rollback_plan = rollback.prepare_rollback(
                library, 1, actor_reference="audit:test-teacher"
            )
            rollback.rollback_release(
                library,
                1,
                True,
                rollback_plan["rollback_confirmation_id"],
                "audit:test-teacher",
            )
            second_candidate = new_candidate()
            second_candidate["title"] = "回滚后新增的另一个教学案例"
            second = prepare.prepare_update([second_candidate], 1, library)
            result = publish.publish_update(
                second,
                True,
                library,
                confirmation_change_set_id=second["change_set_id"],
            )

            self.assertEqual(result["library_version"], 3)
            self.assertEqual(result["release"], "v0003")
            self.assertTrue((library / "releases" / "v0002").is_dir())
            self.assertTrue((library / "releases" / "v0003").is_dir())

    def test_deleted_highest_case_id_is_never_reused(self):
        prepare = load_module("prepare_update", PREPARE_PATH)
        publish = load_module("publish_update", PUBLISH_PATH)
        with tempfile.TemporaryDirectory() as tmp:
            library = copy_library(tmp)
            deletion = prepare.prepare_update(
                [{"operation": "delete", "target_case_id": "DLCL-0077"}],
                1,
                library,
                actor_reference="audit:test-teacher",
            )
            publish.publish_update(
                deletion,
                True,
                library,
                confirmation_change_set_id=deletion["change_set_id"],
            )
            addition = prepare.prepare_update([new_candidate()], 2, library)
            result = publish.publish_update(
                addition,
                True,
                library,
                confirmation_change_set_id=addition["change_set_id"],
            )

            self.assertEqual(result["release"], "v0003")
            self.assertTrue(
                (library / "releases" / "v0003" / "data" / "cases" / "DLCL-0078.json").is_file()
            )
            self.assertFalse(
                (library / "releases" / "v0003" / "data" / "cases" / "DLCL-0077.json").is_file()
            )

    def test_ai_draft_is_excluded_from_student_html_knowledge_and_search(self):
        prepare = load_module("prepare_update", PREPARE_PATH)
        publish = load_module("publish_update", PUBLISH_PATH)
        search = load_module("search_cases", SEARCH_PATH)
        with tempfile.TemporaryDirectory() as tmp:
            library = copy_library(tmp)
            candidate = new_candidate()
            candidate["title"] = "尚未经教师确认的 AI 草稿案例"
            candidate["analysis_origin"] = "ai_draft"
            change_set = prepare.prepare_update([candidate], 1, library)
            result = publish.publish_update(
                change_set,
                True,
                library,
                confirmation_change_set_id=change_set["change_set_id"],
            )
            html = Path(result["html_path"]).read_text(encoding="utf-8")
            knowledge = Path(result["knowledge_pack_path"]).read_text(encoding="utf-8")

            self.assertEqual(result["case_count"], 78)
            self.assertEqual(result["visible_case_count"], 77)
            scenes = json.loads(
                (library / "releases" / "v0002" / "data" / "scenes.json").read_text(encoding="utf-8")
            )
            self.assertEqual(sum(scene["case_count"] for scene in scenes), 77)
            self.assertNotIn(candidate["title"], html)
            self.assertNotIn(candidate["title"], knowledge)
            self.assertNotIn(candidate["title"], {case["title"] for case in search.load_cases(library)})

    def test_updating_expanded_case_replaces_visible_canonical_fields(self):
        prepare = load_module("prepare_update", PREPARE_PATH)
        publish = load_module("publish_update", PUBLISH_PATH)
        with tempfile.TemporaryDirectory() as tmp:
            library = copy_library(tmp)
            new_facts = "教师修订后的儿童推荐案情。"
            new_analysis = "教师修订后的儿童数据教学分析。"
            candidate = {
                "operation": "update",
                "target_case_id": "DLCL-0028",
                "basic_facts": new_facts,
                "legal_analysis": new_analysis,
                "analysis_origin": "teacher_confirmed",
            }
            change_set = prepare.prepare_update([candidate], 1, library)
            result = publish.publish_update(
                change_set,
                True,
                library,
                confirmation_change_set_id=change_set["change_set_id"],
            )
            html = Path(result["html_path"]).read_text(encoding="utf-8")
            knowledge = Path(result["knowledge_pack_path"]).read_text(encoding="utf-8")
            updated = json.loads(
                (library / "releases" / "v0002" / "data" / "cases" / "DLCL-0028.json").read_text(encoding="utf-8")
            )

            self.assertEqual(updated["basic_facts"], new_facts)
            self.assertEqual(updated["legal_analysis"], new_analysis)
            self.assertNotIn("fact_detail", updated)
            self.assertNotIn("analysis_detail", updated)
            self.assertIn(new_facts, html)
            self.assertIn(new_analysis, knowledge)
            self.assertNotIn("某科技公司运营的某短视频App", html)

    def test_rollback_confirmation_is_bound_and_artifacts_are_complete(self):
        prepare = load_module("prepare_update", PREPARE_PATH)
        publish = load_module("publish_update", PUBLISH_PATH)
        rollback = load_module("rollback_release", ROLLBACK_PATH)
        with tempfile.TemporaryDirectory() as tmp:
            library = copy_library(tmp)
            change_set = prepare.prepare_update([new_candidate()], 1, library)
            publish.publish_update(
                change_set,
                True,
                library,
                confirmation_change_set_id=change_set["change_set_id"],
            )
            plan = rollback.prepare_rollback(
                library, 1, actor_reference="audit:test-teacher"
            )
            self.assertEqual(plan["status"], "preview_ready")
            self.assertEqual(
                rollback.rollback_release(
                    library,
                    1,
                    True,
                    None,
                    "audit:test-teacher",
                )["status"],
                "confirmation_mismatch",
            )

            (library / "releases" / "v0001" / "exports" / "案例专家知识包.jsonl").unlink()
            invalid = rollback.prepare_rollback(
                library, 1, actor_reference="audit:test-teacher"
            )
            self.assertEqual(invalid["status"], "target_artifact_missing")

    def test_rollback_audit_intent_failure_does_not_switch_pointer(self):
        prepare = load_module("prepare_update", PREPARE_PATH)
        publish = load_module("publish_update", PUBLISH_PATH)
        rollback = load_module("rollback_release", ROLLBACK_PATH)
        with tempfile.TemporaryDirectory() as tmp:
            library = copy_library(tmp)
            change_set = prepare.prepare_update([new_candidate()], 1, library)
            publish.publish_update(
                change_set,
                True,
                library,
                confirmation_change_set_id=change_set["change_set_id"],
            )
            plan = rollback.prepare_rollback(
                library, 1, actor_reference="audit:test-teacher"
            )
            original_write_json = rollback.write_json

            def fail_intent(path, value):
                if path.name.endswith(".pending.json"):
                    raise OSError("audit unavailable")
                return original_write_json(path, value)

            with patch.object(rollback, "write_json", side_effect=fail_intent):
                result = rollback.rollback_release(
                    library,
                    1,
                    True,
                    plan["rollback_confirmation_id"],
                    "audit:test-teacher",
                )

            self.assertEqual(result["status"], "audit_write_failed")
            current = json.loads((library / "current.json").read_text(encoding="utf-8"))
            self.assertEqual(current["library_version"], 2)

    def test_prepare_rollback_rejects_structurally_corrupt_release(self):
        prepare = load_module("prepare_update", PREPARE_PATH)
        publish = load_module("publish_update", PUBLISH_PATH)
        rollback = load_module("rollback_release", ROLLBACK_PATH)
        with tempfile.TemporaryDirectory() as tmp:
            library = copy_library(tmp)
            change_set = prepare.prepare_update([new_candidate()], 1, library)
            publish.publish_update(
                change_set,
                True,
                library,
                confirmation_change_set_id=change_set["change_set_id"],
            )
            case_path = library / "releases" / "v0001" / "data" / "cases" / "DLCL-0001.json"
            damaged = json.loads(case_path.read_text(encoding="utf-8"))
            damaged.pop("title")
            case_path.write_text(json.dumps(damaged, ensure_ascii=False), encoding="utf-8")

            result = rollback.prepare_rollback(
                library, 1, actor_reference="audit:test-teacher"
            )
            self.assertEqual(result["status"], "target_release_invalid")
            self.assertIn("missing_field:title", result["errors"])

    def test_prepare_rollback_rejects_tampered_html_and_knowledge_content(self):
        prepare = load_module("prepare_update", PREPARE_PATH)
        publish = load_module("publish_update", PUBLISH_PATH)
        rollback = load_module("rollback_release", ROLLBACK_PATH)
        with tempfile.TemporaryDirectory() as tmp:
            library = copy_library(tmp)
            change_set = prepare.prepare_update([new_candidate()], 1, library)
            publish.publish_update(
                change_set,
                True,
                library,
                confirmation_change_set_id=change_set["change_set_id"],
            )
            target = library / "releases" / "v0001"
            html_path = target / "exports" / "数据法学案例库.html"
            html_path.write_text(
                html_path.read_text(encoding="utf-8").replace("数据法学案例库", "被篡改的案例库", 1),
                encoding="utf-8",
            )
            knowledge_path = target / "exports" / "案例专家知识包.jsonl"
            knowledge_path.write_text(
                knowledge_path.read_text(encoding="utf-8").replace("虚假招聘", "篡改招聘", 1),
                encoding="utf-8",
            )

            result = rollback.prepare_rollback(
                library,
                1,
                actor_reference="audit:test-teacher",
                confirmation_nonce="tamper-check",
            )
            self.assertEqual(result["status"], "target_release_invalid")
            self.assertIn("html_not_reproducible", result["errors"])
            self.assertIn("knowledge_not_reproducible", result["errors"])

    def test_rollback_and_publish_share_one_write_lock(self):
        prepare = load_module("prepare_update", PREPARE_PATH)
        publish = load_module("publish_update", PUBLISH_PATH)
        rollback = load_module("rollback_release", ROLLBACK_PATH)
        with tempfile.TemporaryDirectory() as tmp:
            library = copy_library(tmp)
            first = prepare.prepare_update([new_candidate()], 1, library)
            publish.publish_update(
                first,
                True,
                library,
                confirmation_change_set_id=first["change_set_id"],
            )
            rollback_plan = rollback.prepare_rollback(
                library, 1, actor_reference="audit:test-teacher"
            )
            candidate = new_candidate()
            candidate["title"] = "与回滚并发的新增案例"
            candidate["basic_facts"] = "与既有记录不同的并发新增案例事实。"
            second = prepare.prepare_update([candidate], 2, library)
            change_path = Path(tmp) / "change.json"
            change_path.write_text(json.dumps(second, ensure_ascii=False), encoding="utf-8")
            lock_path = library / ".publish.lock"
            with lock_path.open("a+", encoding="utf-8") as lock_handle:
                fcntl.flock(lock_handle, fcntl.LOCK_EX)
                rollback_process = subprocess.Popen(
                    [
                        sys.executable,
                        str(ROLLBACK_PATH),
                        str(library),
                        "1",
                        "--confirmed",
                        "--confirmation-rollback-id",
                        rollback_plan["rollback_confirmation_id"],
                        "--actor-reference",
                        "audit:test-teacher",
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                publish_process = subprocess.Popen(
                    [
                        sys.executable,
                        str(PUBLISH_PATH),
                        str(library),
                        str(change_path),
                        "--confirmed",
                        "--confirmation-change-set-id",
                        second["change_set_id"],
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                time.sleep(0.15)
                fcntl.flock(lock_handle, fcntl.LOCK_UN)
            outputs = []
            for process in (rollback_process, publish_process):
                stdout, _ = process.communicate(timeout=10)
                outputs.append(json.loads(stdout.strip()))
            statuses = {item["status"] for item in outputs}
            self.assertTrue(
                statuses
                in (
                    {"artifact_ready_knowledge_pending", "version_conflict"},
                    {"artifact_ready_knowledge_pending", "confirmation_mismatch"},
                ),
                outputs,
            )

    def test_concurrent_publish_serializes_and_rejects_stale_writer(self):
        prepare = load_module("prepare_update", PREPARE_PATH)
        with tempfile.TemporaryDirectory() as tmp:
            library = copy_library(tmp)
            candidate_a = new_candidate()
            candidate_a["title"] = "并发候选 A"
            candidate_b = new_candidate()
            candidate_b["title"] = "并发候选 B"
            change_a = prepare.prepare_update([candidate_a], 1, library)
            change_b = prepare.prepare_update([candidate_b], 1, library)
            path_a = Path(tmp) / "change-a.json"
            path_b = Path(tmp) / "change-b.json"
            path_a.write_text(json.dumps(change_a, ensure_ascii=False), encoding="utf-8")
            path_b.write_text(json.dumps(change_b, ensure_ascii=False), encoding="utf-8")
            lock_path = library / ".publish.lock"
            with lock_path.open("a+", encoding="utf-8") as lock_handle:
                fcntl.flock(lock_handle, fcntl.LOCK_EX)
                processes = [
                    subprocess.Popen(
                        [
                            sys.executable,
                            str(PUBLISH_PATH),
                            str(library),
                            str(change_path),
                            "--confirmed",
                            "--confirmation-change-set-id",
                            change["change_set_id"],
                        ],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                    )
                    for change_path, change in ((path_a, change_a), (path_b, change_b))
                ]
                time.sleep(0.15)
                fcntl.flock(lock_handle, fcntl.LOCK_UN)
            results = []
            for process in processes:
                stdout, _ = process.communicate(timeout=10)
                results.append(json.loads(stdout.strip()))

            self.assertEqual(
                {result["status"] for result in results},
                {"artifact_ready_knowledge_pending", "version_conflict"},
            )
            current = json.loads((library / "current.json").read_text(encoding="utf-8"))
            self.assertEqual(current["library_version"], 2)

    def test_delete_requires_trusted_audit_context(self):
        prepare = load_module("prepare_update", PREPARE_PATH)
        publish = load_module("publish_update", PUBLISH_PATH)
        with tempfile.TemporaryDirectory() as tmp:
            library = copy_library(tmp)
            change_set = prepare.prepare_update(
                [{"operation": "delete", "target_case_id": "DLCL-0001"}],
                1,
                library,
            )
            result = publish.publish_update(
                change_set,
                True,
                library,
                confirmation_change_set_id=change_set["change_set_id"],
            )
            self.assertEqual(result["status"], "audit_context_required")


if __name__ == "__main__":
    unittest.main()
