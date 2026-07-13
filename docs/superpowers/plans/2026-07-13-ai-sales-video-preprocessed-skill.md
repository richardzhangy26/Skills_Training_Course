# AI 销售顾问视频批阅 Skill（前置预处理版）Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 新建一个只消费平台前置提取结果、完全不包含 ASR 服务或密钥依赖的 AI 销售顾问视频批阅 Skill，并输出可分发 ZIP。

**Architecture:** 新 Skill 与现有 ASR 版并列存在，沿用相同六维评分和红线规则，但把证据入口改为前置处理后的视频文本、PPT 文本与元数据。Skill 内只保留结果校验脚本，所有音频拆分、转写和网络请求都留在批阅模块的前置数据处理层。

**Tech Stack:** Markdown、YAML、Python 3 标准库、`unittest`、ZIP

## Global Constraints

- 不修改 `homework_review/.qoder/skills/grade-ai-sales-consultant-video`。
- 新 Skill 名称固定为 `grade-ai-sales-consultant-video-preprocessed`。
- `score_type` 只使用 `dimension`，满分固定为 100。
- 评价项格式只使用 `文本式`、`清单式`、`对比式`、`标签式`。
- 不包含 MiMo 地址、`MIMO_API_KEY`、具体 ASR 模型名、硬编码密钥、音频拆分或转写脚本。
- 视频口述为主要证据，PPT 只用于事实核验和错失机会。
- 前置文本缺失或覆盖不足时输出技术占位状态，不自行调用 ASR。
- 当前会话不使用子代理，采用 `executing-plans` 在本会话内执行。

---

### Task 1: 建立无 ASR Skill 契约并创建内容文件

**Files:**
- Create: `homework_review/test/test_grade_ai_sales_consultant_video_preprocessed_skill.py`
- Create: `homework_review/.qoder/skills/grade-ai-sales-consultant-video-preprocessed/SKILL.md`
- Create: `homework_review/.qoder/skills/grade-ai-sales-consultant-video-preprocessed/agents/openai.yaml`
- Create: `homework_review/.qoder/skills/grade-ai-sales-consultant-video-preprocessed/references/rubric.md`
- Create: `homework_review/.qoder/skills/grade-ai-sales-consultant-video-preprocessed/references/overpromise_redlines.md`

**Interfaces:**
- Consumes: 平台已提取的视频口述文本、可选时间范围或片段编号、PPT 页面文本、`customer_type` 和 `course_name`。
- Produces: 一个结构完整且不依赖转写服务的 Skill 目录；后续校验器依赖其中定义的六维输出和元数据标签。

- [ ] **Step 1: Write the failing contract test**

```python
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".qoder/skills/grade-ai-sales-consultant-video-preprocessed"

class PreprocessedSkillContractTests(unittest.TestCase):
    def test_skill_uses_preprocessed_evidence_without_asr_dependencies(self):
        self.assertTrue((SKILL / "SKILL.md").is_file(), "新 Skill 尚未创建")
        skill_md = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        all_text = "\n".join(
            path.read_text(encoding="utf-8", errors="ignore")
            for path in SKILL.rglob("*") if path.is_file()
        )
        self.assertIn("前置数据处理", skill_md)
        self.assertIn("预处理片段", skill_md)
        self.assertIn("内容覆盖状态", skill_md)
        self.assertNotIn("MIMO_API_KEY", all_text)
        self.assertNotIn("api.xiaomimimo.com", all_text)
        self.assertNotIn("mimo-v2.5-asr", all_text)
        self.assertFalse((SKILL / "scripts/transcribe_mimo.py").exists())
        self.assertFalse((SKILL / "scripts/prepare_sales_evidence.py").exists())
        self.assertFalse(re.search(r"sk-[A-Za-z0-9]{12,}", all_text))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 test/test_grade_ai_sales_consultant_video_preprocessed_skill.py -v`

Expected: FAIL with `新 Skill 尚未创建`.

- [ ] **Step 3: Run the project grading-skill scaffold**

```bash
python3 .agents/skills/create-custom-homework-review-skill/scripts/scaffold_review_skill.py \
  --skill-name grade-ai-sales-consultant-video-preprocessed \
  --display-name "AI销售顾问视频批阅（前置预处理版）" \
  --assignment-type "平台已完成视频和PPT信息提取的AI应用顾问或销售顾问课程方案汇报录屏" \
  --output-dir .qoder/skills
```

- [ ] **Step 4: Replace scaffold placeholders with the approved contract**

Write `SKILL.md` with these exact behaviors:

```markdown
- 只读取前置数据处理结果，不处理原始音频。
- 视频口述文本为空、仅有摘要或覆盖不足时，输出“无法批阅（0分为技术占位）”。
- 有时间范围时使用时间范围；没有时使用“预处理片段/段落编号＋近似原话”。
- `review_metadata` 使用“前置处理来源、内容覆盖状态、证据定位精度”，不使用转写模型字段。
```

Copy the approved six-dimension rubric and R1-R7 redlines into the two reference files without adding media fields or unsupported evaluation formats.

- [ ] **Step 5: Run the contract test**

Run: `python3 -m unittest test/test_grade_ai_sales_consultant_video_preprocessed_skill.py -v`

Expected: PASS and no forbidden ASR or secret patterns found.

### Task 2: 添加前置处理元数据校验器

**Files:**
- Create: `homework_review/.qoder/skills/grade-ai-sales-consultant-video-preprocessed/tests/test_validate_review_result.py`
- Create: `homework_review/.qoder/skills/grade-ai-sales-consultant-video-preprocessed/scripts/validate_review_result.py`

**Interfaces:**
- Consumes: 顶层只有 `score`、`evaluations` 的候选结果 JSON。
- Produces: `apply_score_cap(result: dict) -> dict` 和 `validate_result(result: dict) -> list[str]`。

- [ ] **Step 1: Write validator tests before the script exists**

Use a loader that leaves behavior tests skipped until the script exists, while the existence test fails cleanly:

```python
SCRIPT = SKILL_DIR / "scripts/validate_review_result.py"

def load_validator():
    if not SCRIPT.is_file():
        return None
    spec = importlib.util.spec_from_file_location("preprocessed_validator", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

validator = load_validator()

class ValidateReviewResultTests(unittest.TestCase):
    def test_validator_script_exists(self):
        self.assertTrue(SCRIPT.is_file(), "结果校验器尚未实现")
```

Decorate behavior tests with `@unittest.skipIf(validator is None, "等待结果校验器实现")`. Cover:

```python
def test_validate_requires_preprocessing_metadata():
    result = valid_result()
    result["evaluations"]["review_metadata"]["tags"] = [
        tag for tag in result["evaluations"]["review_metadata"]["tags"]
        if tag["label"] != "内容覆盖状态"
    ]
    errors = validator.validate_result(result)
    assert any("内容覆盖状态" in error for error in errors)

def test_validate_accepts_segment_locator_without_timestamp():
    result = valid_result()
    result["evaluations"]["key_evidence"]["items"] = [
        {"seq": 1, "text": "预处理片段3＋近似原话＋判定"}
    ]
    assert validator.validate_result(result) == []
```

Also retain tests for six dimensions, fixed 3/5/8 deductions, `old/new/unknown`, R1-R7 caps, and supported evaluation formats.

- [ ] **Step 2: Run tests to verify RED**

Run: `python3 -m unittest discover -s .qoder/skills/grade-ai-sales-consultant-video-preprocessed/tests -p 'test_*.py' -v`

Expected: one FAIL with `结果校验器尚未实现`; behavior tests are skipped rather than erroring.

- [ ] **Step 3: Implement the minimal validator**

Define:

```python
REQUIRED_METADATA_LABELS = {
    "批阅状态", "客户类型", "课程", "前置处理来源", "内容覆盖状态",
    "证据定位精度", "严重红线类别", "总分封顶", "局限说明",
}
```

Validate that each label is present, preserve the six-dimension score checks, and preserve exact fact deductions and cap calculations from the approved ASR version.

- [ ] **Step 4: Run validator and contract tests**

Run: `python3 -m unittest discover -s .qoder/skills/grade-ai-sales-consultant-video-preprocessed/tests -p 'test_*.py' -v`

Run: `python3 test/test_grade_ai_sales_consultant_video_preprocessed_skill.py -v`

Expected: all tests PASS.

### Task 3: 验证并制作无密钥 ZIP

**Files:**
- Create: `homework_review/dist/grade-ai-sales-consultant-video-preprocessed-20260713.zip`

**Interfaces:**
- Consumes: 已通过测试的 Skill 目录。
- Produces: 顶层目录为 `grade-ai-sales-consultant-video-preprocessed/` 的可分发 ZIP。

- [ ] **Step 1: Validate structure and run all tests**

Run:

```bash
python3 /Users/zhangyichi/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  .qoder/skills/grade-ai-sales-consultant-video-preprocessed
python3 -m unittest discover \
  -s .qoder/skills/grade-ai-sales-consultant-video-preprocessed/tests \
  -p 'test_*.py' -v
python3 test/test_grade_ai_sales_consultant_video_preprocessed_skill.py -v
```

Expected: skill valid and all tests PASS.

- [ ] **Step 2: Package only approved files**

Copy the Skill to a temporary directory excluding `__pycache__`, `*.pyc`, `.DS_Store`, and `.env`, then create the ZIP from the temporary parent so the archive has one top-level Skill directory.

- [ ] **Step 3: Verify the archive**

Check that:

```text
No compressed-data errors
No MIMO_API_KEY
No api.xiaomimimo.com
No mimo-v2.5-asr
No sk-<credential>
No transcribe_mimo.py
No prepare_sales_evidence.py
No .env, __pycache__, *.pyc, or .DS_Store
```

Run the packaged tests from a temporary extraction directory and require zero failures. Delete every temporary copy afterward.
