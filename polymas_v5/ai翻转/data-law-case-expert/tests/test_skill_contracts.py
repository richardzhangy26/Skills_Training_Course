from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
QUERY_SKILL = ROOT / "data-law-case-query" / "SKILL.md"
MAINTENANCE_SKILL = ROOT / "data-law-case-maintenance" / "SKILL.md"


class QuerySkillContractTests(unittest.TestCase):
    def test_query_skill_has_polymas_structure_and_read_only_boundary(self):
        text = QUERY_SKILL.read_text(encoding="utf-8")
        self.assertIn("name: data-law-case-query", text)
        for heading in (
            "## 技能说明",
            "## 触发条件",
            "## 不触发条件",
            "## 项目结构",
            "## 执行流程",
            "## 暂停确认规则",
            "## 执行流程强制约束",
        ):
            self.assertIn(heading, text)
        self.assertIn("只读", text)
        self.assertIn("不得修改", text)

    def test_query_skill_disambiguates_and_separates_evidence(self):
        text = QUERY_SKILL.read_text(encoding="utf-8")
        self.assertIn("[DETERMINE]", text)
        self.assertIn("[CALL]", text)
        self.assertIn("[FILTER]", text)
        self.assertIn("[BUILD]", text)
        self.assertIn("ask_user_question", text)
        self.assertIn("候选", text)
        self.assertIn("案例库记载", text)
        self.assertIn("教学分析", text)
        self.assertIn("材料边界", text)
        self.assertIn("案件当时", text)
        self.assertIn("当前有效", text)


class MaintenanceSkillContractTests(unittest.TestCase):
    def test_maintenance_skill_requires_role_and_real_confirmation(self):
        text = MAINTENANCE_SKILL.read_text(encoding="utf-8")
        self.assertIn("name: data-law-case-maintenance", text)
        self.assertIn("不能仅凭用户自称教师", text)
        self.assertIn("[CONFIRM]", text)
        self.assertIn("ask_user_question", text)
        self.assertIn("真正等待", text)

    def test_maintenance_skill_distinguishes_artifact_and_knowledge_status(self):
        text = MAINTENANCE_SKILL.read_text(encoding="utf-8")
        self.assertIn("artifact_ready_knowledge_pending", text)
        self.assertIn("knowledge_verified", text)
        self.assertIn("knowledge_state_unknown", text)
        self.assertIn("version_conflict", text)
        self.assertIn("polymas-file-upload", text)
        self.assertIn("polymas-teacher-knowledge-distillation", text)
        self.assertIn("HTML", text)
        self.assertIn("回读", text)
        self.assertIn("--confirmation-change-set-id", text)
        self.assertIn("rollback_confirmation_id", text)
        self.assertIn("actor_reference", text)
        self.assertIn("敏感内容只返回风险标记", text)
        self.assertIn("ai_draft", text)
        self.assertIn("仅用于空库初始化", text)
        self.assertIn("confirmation_already_used", text)
        self.assertIn("candidate_release_invalid", text)
        self.assertIn("学号", text)
        self.assertIn("证据状态", text)
        self.assertIn("发布状态", text)


if __name__ == "__main__":
    unittest.main()
