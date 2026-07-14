# AI Sales Audio-First Grading Optimization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 通过标准化真实音轨、严格区分证据来源并统一通用评分口径，使两个线上 AI 销售顾问批阅 Skill 的优秀、良好、较差样本分别进入 82–95、63–75、20–55。

**Architecture:** 在 Skill 之外生成并验证标准化音频提交物；两个 Skill 只消费可回溯的口述证据，PPT 只作事实核验。独立验收器保存三档目标区间和反硬编码检查，线上 Skill 不包含样本名称、样本讲稿或档位分数映射。

**Tech Stack:** Python 3 标准库、`unittest`、FFmpeg/ffprobe、MiMo ASR、Markdown Skill、Polymas 草稿与 preview API

## Global Constraints

- 最多执行两轮完整优化，每轮最多两个 Skill × 三档样本共六次平台任务。
- 原始 MP4、参考 PPT 和其他 Skill 不得修改。
- 所有媒体改动只创建派生副本并记录源文件、派生文件 SHA-256。
- Skill 中不得出现测试文件名、`excellent/good/poor`、三档目标区间或样本完整讲稿。
- 优秀 82–95、良好 63–75、较差 20–55 只存在于独立验收配置。
- 事实扣分只允许 3、5、8 分，并必须有真实口述定位和直接冲突依据。
- 上游证据为空、冲突或不可回溯时输出技术状态，不把 0 分解释为学员能力。
- 不输出或新增 API Key、Authorization、Cookie；线上写入前必须备份并回读校验。
- 当前会话不使用子代理，采用 `executing-plans` 在本会话内执行。

---

### Task 1: 建立独立三档验收器

**Files:**
- Create: `homework_review/tmp/ai_sales_audio_first_loop/test_acceptance.py`
- Create: `homework_review/tmp/ai_sales_audio_first_loop/acceptance.py`
- Create: `homework_review/tmp/ai_sales_audio_first_loop/acceptance_ranges.json`

**Interfaces:**
- Consumes: 两个运行目录中每个 case 的 `report_detail.json` 和两个本地 Skill 目录。
- Produces: `evaluate_scores(scores: dict[str, int], ranges: dict[str, list[int]]) -> dict`、`evaluate_method(run_dir: Path, ranges: dict) -> dict` 与 `scan_skill_for_case_hardcoding(skill_dir: Path) -> list[str]`；CLI 支持 `--run-dir`、`--ranges`、`--out` 和 `--scan-skill`。

- [ ] **Step 1: Write the failing acceptance tests**

```python
class AcceptanceTests(unittest.TestCase):
    def test_three_tiers_must_land_in_independent_ranges(self):
        result = evaluate_scores(
            {"excellent": 86, "good": 69, "poor": 34},
            {"excellent": [82, 95], "good": [63, 75], "poor": [20, 55]},
        )
        self.assertTrue(result["passed"])

    def test_ordering_is_required(self):
        result = evaluate_scores(
            {"excellent": 64, "good": 68, "poor": 30},
            {"excellent": [60, 95], "good": [60, 75], "poor": [20, 55]},
        )
        self.assertIn("ordering", result["failures"])

    def test_online_skill_cannot_contain_case_specific_markers(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "SKILL.md").write_text("excellent 82–95", encoding="utf-8")
            self.assertTrue(scan_skill_for_case_hardcoding(root))
```

- [ ] **Step 2: Run RED**

Run: `python3 -m unittest tmp/ai_sales_audio_first_loop/test_acceptance.py -v`

Expected: FAIL because `acceptance.py` does not exist.

- [ ] **Step 3: Implement the minimal evaluator**

```python
FORBIDDEN_CASE_MARKERS = (
    "excellent", "good", "poor", "82–95", "63–75", "20–55",
    "测试样本A", "测试样本B", "测试样本C",
)

def evaluate_scores(scores: dict[str, int], ranges: dict[str, list[int]]) -> dict:
    failures = []
    for name, bounds in ranges.items():
        score = scores.get(name)
        if not isinstance(score, int) or not bounds[0] <= score <= bounds[1]:
            failures.append(f"range:{name}")
    if all(isinstance(scores.get(k), int) for k in ("excellent", "good", "poor")):
        if not scores["excellent"] > scores["good"] > scores["poor"]:
            failures.append("ordering")
    return {"passed": not failures, "scores": scores, "failures": failures}
```

`acceptance_ranges.json` 固定为：

```json
{
  "excellent": [82, 95],
  "good": [63, 75],
  "poor": [20, 55]
}
```

- [ ] **Step 4: Run GREEN**

Run: `python3 -m unittest tmp/ai_sales_audio_first_loop/test_acceptance.py -v`

Expected: all tests PASS.

- [ ] **Step 5: Commit the independent gate**

```bash
git add homework_review/tmp/ai_sales_audio_first_loop
git commit -m "test: add independent sales grading acceptance gate"
```

---

### Task 2: 生成并验证标准化音频提交物

**Files:**
- Create: `homework_review/tmp/ai_sales_audio_first_loop/test_prepare_audio_submissions.py`
- Create: `homework_review/tmp/ai_sales_audio_first_loop/prepare_audio_submissions.py`
- Create: `homework_review/tmp/ai_sales_audio_first_loop/audio_manifest.json`
- Create: `homework_review/review_results/AI销售顾问三档音频优先样本/*.mp3`

**Interfaces:**
- Consumes: 三条现有 MP4 与速度映射 `{"excellent": 1.10, "good": 1.0, "poor": 1.0}`。
- Produces: `prepare_one(source: Path, target: Path, speed: float) -> dict`，返回源/目标哈希、时长、编码和响度检测结果。

- [ ] **Step 1: Write the failing media test**

```python
def test_prepare_one_outputs_48khz_mono_mp3_with_audio(self):
    result = prepare_one(self.source_video, self.target_mp3, speed=1.10)
    self.assertEqual(result["codec_name"], "mp3")
    self.assertEqual(result["sample_rate"], 48000)
    self.assertEqual(result["channels"], 1)
    self.assertGreater(result["duration_sec"], 0)
    self.assertNotEqual(result["source_sha256"], result["target_sha256"])
```

- [ ] **Step 2: Run RED**

Run: `python3 -m unittest tmp/ai_sales_audio_first_loop/test_prepare_audio_submissions.py -v`

Expected: FAIL because `prepare_audio_submissions.py` does not exist.

- [ ] **Step 3: Implement one deterministic FFmpeg path**

Use this filter and output contract:

```python
filters = ["loudnorm=I=-16:LRA=7:TP=-1.5"]
if speed != 1.0:
    filters.append(f"atempo={speed:.4f}")
command = [
    "ffmpeg", "-y", "-v", "error", "-nostdin", "-i", str(source),
    "-map", "0:a:0", "-vn", "-ac", "1", "-ar", "48000",
    "-af", ",".join(filters), "-c:a", "libmp3lame", "-b:a", "96k",
    str(target),
]
```

The manifest must include `source_path`, `target_path`, both SHA-256 values, `duration_sec`, `codec_name`, `sample_rate`, `channels`, `speed`, and FFmpeg volume diagnostics.

- [ ] **Step 4: Run unit tests and generate all three files**

Run: `python3 -m unittest tmp/ai_sales_audio_first_loop/test_prepare_audio_submissions.py -v`

Run: `python3 tmp/ai_sales_audio_first_loop/prepare_audio_submissions.py`

Expected: tests PASS; excellent duration is below 210 seconds; all files are MP3/48 kHz/mono and non-silent.

- [ ] **Step 5: Verify real speech survived conversion**

Run the existing MiMo preparation/transcription scripts against all three derived files or extracted WAV equivalents. Require 100% segment coverage and verify:

- Excellent transcript contains a concrete material request, a date, and a demonstrable next deliverable.
- Good transcript contains only courtesy-style follow-up.
- Poor transcript contains the actual replacement/guarantee/price/delivery redlines.

Save only redacted transcript evidence; never save the key.

- [ ] **Step 6: Commit generator and manifest, not generated media binaries**

```bash
git add homework_review/tmp/ai_sales_audio_first_loop/prepare_audio_submissions.py \
  homework_review/tmp/ai_sales_audio_first_loop/test_prepare_audio_submissions.py \
  homework_review/tmp/ai_sales_audio_first_loop/audio_manifest.json
git commit -m "feat: prepare normalized sales grading audio"
```

---

### Task 3: Repair evidence provenance in the MiMo-flow Skill

**Files:**
- Create: `homework_review/.qoder/skills/grade-ai-sales-consultant-video/tests/test_skill_contract.py`
- Modify: `homework_review/.qoder/skills/grade-ai-sales-consultant-video/SKILL.md`
- Modify: `homework_review/.qoder/skills/grade-ai-sales-consultant-video/references/rubric.md`
- Modify: `homework_review/.qoder/skills/grade-ai-sales-consultant-video/scripts/validate_review_result.py`
- Modify: `homework_review/.qoder/skills/grade-ai-sales-consultant-video/tests/test_validate_review_result.py`

**Interfaces:**
- Consumes: MiMo transcript metadata or direct complete audio listening evidence.
- Produces: review metadata containing `证据来源`, `ASR提供方`, `ASR模型`, `音频覆盖率`, and `局限说明` that agrees with the actual evidence path.

- [ ] **Step 1: Write failing contract and validator tests**

Tests must require:

```python
self.assertIn("不得根据 PPT 或页面内容补写顾问口述", skill_text)
self.assertIn("provider=xiaomi-mimo", skill_text)
self.assertIn("直接音频听写", skill_text)
self.assertIn("无法取得完整真实口述时输出技术失败", skill_text)
```

Add validator tests proving that `证据来源=MiMo ASR` is rejected unless provider, model and 100% coverage tags are present, and that `证据来源=直接音频听写` cannot claim a MiMo model.

- [ ] **Step 2: Run RED**

Run: `python3 -m unittest discover -s .qoder/skills/grade-ai-sales-consultant-video/tests -p 'test_*.py' -v`

Expected: new provenance tests FAIL for missing contract and metadata validation.

- [ ] **Step 3: Implement the minimal evidence gate**

The Skill decision must be:

```text
MiMo metadata complete and coverage=100% -> use MiMo ASR evidence
else full direct audio listening available -> use direct-audio evidence and name it honestly
else -> technical failure; do not infer speech from PPT
```

Align the new-customer rubric with the preprocessed version: absence of a case study alone does not force 0–4 when the spoken solution is clearly course-specific and establishes basic professional trust.

For poor presentations, evaluate feature coverage and recognizable sequencing in their own dimensions; do not duplicate R1–R7 penalties outside fact/boundary scoring and total cap.

- [ ] **Step 4: Run GREEN and static anti-hardcode scan**

Run: `python3 -m unittest discover -s .qoder/skills/grade-ai-sales-consultant-video/tests -p 'test_*.py' -v`

Run: `python3 tmp/ai_sales_audio_first_loop/acceptance.py --scan-skill .qoder/skills/grade-ai-sales-consultant-video`

Expected: tests PASS and no case-specific marker found.

- [ ] **Step 5: Commit the MiMo-flow candidate**

```bash
git add homework_review/.qoder/skills/grade-ai-sales-consultant-video
git commit -m "fix: gate sales grading on real audio evidence"
```

---

### Task 4: Repair evidence quality handling in the preprocessed Skill

**Files:**
- Modify: `homework_review/.qoder/skills/grade-ai-sales-consultant-video-preprocessed/SKILL.md`
- Modify: `homework_review/.qoder/skills/grade-ai-sales-consultant-video-preprocessed/references/rubric.md`
- Modify: `homework_review/.qoder/skills/grade-ai-sales-consultant-video-preprocessed/scripts/validate_review_result.py`
- Modify: `homework_review/.qoder/skills/grade-ai-sales-consultant-video-preprocessed/tests/test_skill_contract.py`
- Modify: `homework_review/.qoder/skills/grade-ai-sales-consultant-video-preprocessed/tests/test_validate_review_result.py`

**Interfaces:**
- Consumes: platform preprocessing JSON/text.
- Produces: explicit `证据类型=verbatim|summary|none/conflict` and scoring behavior tied to that type.

- [ ] **Step 1: Write failing evidence-kind tests**

Contract tests must require the observable predicates:

```python
self.assertIn("verbatim", skill_text)
self.assertIn("summary", skill_text)
self.assertIn("none/conflict", skill_text)
self.assertIn("摘要未提及的内容不得判定为学员缺失", skill_text)
self.assertIn("音质清晰", skill_text)
self.assertIn("无音频", skill_text)
```

Validator tests must reject a completed score without a non-empty `证据类型` tag and reject `none/conflict` combined with `批阅状态=完成`.

- [ ] **Step 2: Run RED**

Run: `python3 -m unittest discover -s .qoder/skills/grade-ai-sales-consultant-video-preprocessed/tests -p 'test_*.py' -v`

Expected: new evidence-kind tests FAIL.

- [ ] **Step 3: Implement the three evidence paths**

Rules:

```text
verbatim -> six-dimensional scoring; fact deductions require direct quoted conflict
summary -> positive themes only; unmentioned CTA/backing/innovation/facts remain unconfirmed
none/conflict -> technical placeholder and preprocessing retry request
```

Keep the same new-customer and non-duplicated-redline rubric behavior as Task 3.

- [ ] **Step 4: Run GREEN and anti-hardcode scan**

Run: `python3 -m unittest discover -s .qoder/skills/grade-ai-sales-consultant-video-preprocessed/tests -p 'test_*.py' -v`

Run: `python3 tmp/ai_sales_audio_first_loop/acceptance.py --scan-skill .qoder/skills/grade-ai-sales-consultant-video-preprocessed`

Expected: tests PASS and no case-specific marker found.

- [ ] **Step 5: Commit the preprocessed candidate**

```bash
git add homework_review/.qoder/skills/grade-ai-sales-consultant-video-preprocessed
git commit -m "fix: classify upstream speech evidence before grading"
```

---

### Task 5: Back up and upload round-one candidates

**Files:**
- Create: `homework_review/tmp/ai_sales_audio_first_loop/sync_mimo.json`
- Create: `homework_review/tmp/ai_sales_audio_first_loop/sync_preprocessed.json`
- Create: `homework_review/tmp/ai_sales_audio_first_loop/e2e_mimo_audio.json`
- Create: `homework_review/tmp/ai_sales_audio_first_loop/e2e_preprocessed_audio.json`

**Interfaces:**
- Consumes: the two candidate Skill directories, three normalized audio files and existing credentials from `.env`.
- Produces: remote backups, verified draft hashes and two three-case E2E configs.

- [ ] **Step 1: Build neutral E2E configurations**

Use case IDs `case_a`, `case_b`, `case_c`; student-facing text must be identical and must not reveal tier. Put the score ranges only in each `expected` field:

```json
{"min_score": 82, "max_score": 95}
{"min_score": 63, "max_score": 75}
{"min_score": 20, "max_score": 55}
```

- [ ] **Step 2: Run local config dry-runs**

Run both:

```bash
python3 skill_preview_e2e.py --config tmp/ai_sales_audio_first_loop/e2e_mimo_audio.json --dry-run
python3 skill_preview_e2e.py --config tmp/ai_sales_audio_first_loop/e2e_preprocessed_audio.json --dry-run
```

Expected: both configs normalize and produce payload previews without network writes.

- [ ] **Step 3: Probe pure-audio upload compatibility**

Run this probe without printing credentials and confirm the returned attachment suffix is `mp3`:

```bash
python3 - <<'PY'
from pathlib import Path
import skill_preview_e2e as preview

env = preview.load_env_file(Path('.env'))
client = preview.SkillPreviewClient(env['AUTHORIZATION'], env['COOKIE'])
upload = client.upload_file(Path('review_results/AI销售顾问三档音频优先样本/AI销售顾问-良好档-音频优先.mp3'))
print({'fileName': upload['fileName'], 'suffix': upload['suffix'], 'size': upload.get('size')})
assert upload['suffix'].lower() == 'mp3'
PY
```

Do not execute a grading task during the probe. If the endpoint rejects MP3, create a minimal MP4 containing the same audio and a static neutral frame, then update all three configs to those derived wrappers.

- [ ] **Step 4: Back up and upload each draft**

Run `skill_draft_sync.py --dry-run` first for each config. Inspect planned remote paths and hashes, then run without `--dry-run`. Require every `verify.*.match` to be true.

- [ ] **Step 5: Commit only sanitized configs**

Run `rg -n 'Authorization|Cookie|Bearer|sk-' tmp/ai_sales_audio_first_loop/*.json` and require no matches, then:

```bash
git add homework_review/tmp/ai_sales_audio_first_loop/sync_mimo.json \
  homework_review/tmp/ai_sales_audio_first_loop/sync_preprocessed.json \
  homework_review/tmp/ai_sales_audio_first_loop/e2e_mimo_audio.json \
  homework_review/tmp/ai_sales_audio_first_loop/e2e_preprocessed_audio.json
git commit -m "test: configure audio-first platform grading runs"
```

---

### Task 6: Run round one and choose one justified round-two change

**Files:**
- Create: `homework_review/review_results/AI销售顾问音频优先平台验收/round-1/**`
- Create: `homework_review/tmp/ai_sales_audio_first_loop/round_1_acceptance.json`
- Conditionally modify only one evidence-supported input for round two.

**Interfaces:**
- Consumes: two uploaded drafts and the three normalized submissions.
- Produces: six platform reports plus independent range/order/evidence evaluation.

- [ ] **Step 1: Execute both three-case E2E runs**

Run the two E2E commands concurrently. Poll by task status; do not classify timeout, upload failure or technical placeholder as a passing student score.

- [ ] **Step 2: Evaluate round one independently**

Run `acceptance.py` against both run directories. Require all six ranges, ordering, evidence-source consistency and no technical misclassification.

- [ ] **Step 3: Stop on success or select exactly one next variable**

If all checks pass, stop with `Success`. Otherwise inspect the new evidence and choose only one of:

- media wrapper compatibility;
- evidence-kind classification wording;
- generic dimension boundary wording.

Do not change multiple categories in round two.

- [ ] **Step 4: If justified, run the same RED/GREEN/upload/six-case check once more**

Round two uses identical acceptance ranges and neutral case text. Stop after round two as `Success`, `Blocked`, `Exhausted`, or `No progress`.

---

### Task 7: Final verification and handoff

**Files:**
- Create: `homework_review/review_results/AI销售顾问音频优先平台验收/final_comparison.md`
- Create: `homework_review/review_results/AI销售顾问音频优先平台验收/final_comparison.html`

**Interfaces:**
- Consumes: retained candidate, media manifest, online backup logs and final six reports.
- Produces: reproducible verification evidence and Loopy run receipt.

- [ ] **Step 1: Run all local tests**

```bash
python3 -m unittest discover -s .qoder/skills/grade-ai-sales-consultant-video/tests -p 'test_*.py' -v
python3 -m unittest discover -s .qoder/skills/grade-ai-sales-consultant-video-preprocessed/tests -p 'test_*.py' -v
python3 -m unittest discover -s tmp/ai_sales_audio_first_loop -p 'test_*.py' -v
```

- [ ] **Step 2: Run media and remote-hash verification**

Verify all derived files have audio, match the manifest, and the retained remote Skill files match local SHA-256 values.

- [ ] **Step 3: Re-run the independent acceptance command**

Require a fresh exit code 0. If any case is outside its range or technically invalid, report the actual terminal state instead of success.

- [ ] **Step 4: Generate the comparison report and Loopy receipt**

Report per-case score, dimensions, task ID, evidence source, technical status, retained action and any platform-side blocker. Exclude credentials and unredacted request headers.
