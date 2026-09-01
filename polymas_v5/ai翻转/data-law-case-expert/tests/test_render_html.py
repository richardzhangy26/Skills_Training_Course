from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
LIBRARY_ROOT = ROOT / "case-library"
RENDERER_PATH = (
    ROOT
    / "data-law-case-maintenance"
    / "scripts"
    / "render_html.py"
)


def load_renderer():
    spec = importlib.util.spec_from_file_location("render_html", RENDERER_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class HtmlRendererTests(unittest.TestCase):
    def test_rendered_html_contains_all_scenes_and_cases(self):
        renderer = load_renderer()
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "library.html"
            report = renderer.render_library(LIBRARY_ROOT, output)
            html = output.read_text(encoding="utf-8")

            self.assertEqual(report["case_count"], 77)
            self.assertEqual(report["scene_count"], 10)
            self.assertEqual(html.count('data-case-id="DLCL-'), 77)
            self.assertIn("就业、劳动管理与跨境 HR 数据场景", html)
            self.assertIn("公共数据授权运营、开放利用与行政垄断", html)
            self.assertIn('type="search"', html)
            self.assertIn("待补证", html)
            self.assertIn(">研究材料<", html)
            self.assertNotIn('class="case-type">research_material<', html)

    def test_html_is_self_contained_and_responsive(self):
        renderer = load_renderer()
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "library.html"
            renderer.render_library(LIBRARY_ROOT, output)
            html = output.read_text(encoding="utf-8")

            self.assertNotIn("fonts.googleapis.com", html)
            self.assertNotIn("<link rel=", html)
            self.assertIn("@media (max-width: 860px)", html)
            self.assertIn('id="case-data"', html)
            self.assertIn('aria-live="polite"', html)
            self.assertIn('aria-label="搜索案例"', html)
            self.assertIn('aria-label="按案例类型筛选"', html)

    def test_script_json_escapes_html_breakout(self):
        renderer = load_renderer()
        value = renderer.safe_json_for_script({"title": "</script><img src=x>"})
        self.assertNotIn("</script>", value)
        self.assertIn("\\u003c", value)


if __name__ == "__main__":
    unittest.main()
