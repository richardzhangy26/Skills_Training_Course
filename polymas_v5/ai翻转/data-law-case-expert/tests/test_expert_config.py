from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
AGENT_MD = ROOT / "Agent.md"
CONFIG = ROOT / "EXPERT_CONFIG.md"


class ExpertConfigTests(unittest.TestCase):
    def test_agent_uses_pds_template_and_routes_both_roles(self):
        text = AGENT_MD.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\nname: ${agent_name}\n---"))
        for heading in (
            "## 您的角色",
            "## 核心职责",
            "## 可用技能",
            "## 工作流程",
            "## 我不做什么",
            "## 工作风格",
            "## 最佳实践",
        ):
            self.assertIn(heading, text)
        self.assertIn("data-law-case-query", text)
        self.assertIn("data-law-case-maintenance", text)
        self.assertIn("不能仅凭用户自称教师", text)

    def test_agent_preserves_evidence_and_status_boundaries(self):
        text = AGENT_MD.read_text(encoding="utf-8")
        self.assertIn("结构化案例数据", text)
        self.assertIn("artifact_ready_knowledge_pending", text)
        self.assertIn("knowledge_verified", text)
        self.assertIn("案件当时", text)
        self.assertIn("当前有效", text)

    def test_config_delivers_fields_order_opening_and_real_integration_list(self):
        text = CONFIG.read_text(encoding="utf-8")
        for label in (
            "`${expertise}`",
            "`${core_responsibilities}`",
            "`${workflow}`",
            "`${boundaries}`",
            "`${work_style}`",
            "## 精确挂载顺序",
            "## 开场白与推荐问题",
            "## 真实联调清单",
        ):
            self.assertIn(label, text)
        self.assertIn("1. `data-law-case-query`", text)
        self.assertIn("2. `data-law-case-maintenance`", text)
        self.assertIn("PDS", text)
        self.assertIn("尚未完成线上验证", text)


if __name__ == "__main__":
    unittest.main()
