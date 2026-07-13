# Surgical Gown Video Media Comparison Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 `grade-surgical-gown-glove-video` 增加精简的“学生动作 vs 标准动作”双图对比评价，使教师能直接看到 2–4 个真实关键差异，同时保持现有 21 项、100 分评分规则不变。

**Architecture:** 继续使用内置 `reference.json` 和既有标准锚点拼图作为标准侧素材；运行时用现有 `clip_media.py` 截取学生关键片段，再用 `make_contact_sheet.py` 生成学生侧细拼图。模型只在有明确动作差异、无菌风险或高价值不确定项时生成 `evaluations.key_action_comparisons`，标准视频作为学生答案时应输出空清单。

**Tech Stack:** Markdown Skill 指令、YAML Agent 配置、Python `unittest`、JSON、FFmpeg/FFprobe、Qoder CLI。

## Global Constraints

- 不修改 `score` 的 21 个评分项、分值、总分算法或证据类型。
- 不新增标准视频片段包；标准侧继续使用 `reference.json.anchors[].standard_asset`。
- 媒体数组只允许出现在 `evaluations.key_action_comparisons.items[].images[]`。
- 媒体生成成功的对比项必须恰好两张图，顺序固定为“学生”后“标准”。
- 对比项数量为 2–4 个；没有可证实动作差异时必须是空数组，不得为了凑数制造差异。
- 学生侧细拼图必须来自对应动作段的 2–8 秒片段，默认抽取 4–6 帧。
- 媒体生成失败时保留文字和证据说明，省略该项 `images`；标准素材缺失时跳过该对比项并写入 `risk_flags`。
- 不同步线上 Skill，不改 `skill_draft_sync.py`，线上发布和预览测试留到本地验收通过后单独执行。

---

## Task 1: 建立媒体对比输出契约测试

**Files:**
- Create: `tests/test_grade_surgical_gown_glove_video_contract.py`
- Read: `.qoder/skills/grade-surgical-gown-glove-video/SKILL.md`
- Read: `.qoder/skills/grade-surgical-gown-glove-video/agents/openai.yaml`
- Read: `.qoder/skills/grade-surgical-gown-glove-video/references/surgical-gown-glove-v1/reference.json`

- [ ] **Step 1: 创建会失败的契约测试**

新增以下 `unittest`，同时检查说明契约、默认提示词和标准锚点素材完整性：

```python
from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / ".qoder/skills/grade-surgical-gown-glove-video"
SKILL_TEXT = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
REFERENCE_PATH = SKILL_DIR / "references/surgical-gown-glove-v1/reference.json"


class SurgicalGownMediaComparisonContractTest(unittest.TestCase):
    def test_skill_defines_concise_media_comparison_contract(self) -> None:
        required_fragments = (
            "key_action_comparisons",
            "2-4",
            "没有明确动作差异",
            '"label": "学生"',
            '"label": "标准"',
            "恰好包含 2 个对象",
            "2-8 秒",
            "4-6 帧",
        )
        for fragment in required_fragments:
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, SKILL_TEXT)

    def test_media_fields_are_scoped_to_key_comparisons(self) -> None:
        self.assertIn(
            "媒体数组只允许出现在 `key_action_comparisons.items[].images[]`",
            SKILL_TEXT,
        )
        self.assertNotIn("不得写 `items[].images` 或媒体嵌入字段", SKILL_TEXT)
        self.assertNotIn("输出中不得出现 `时间轴式`、`items[].images`", SKILL_TEXT)

    def test_observable_anchor_assets_exist(self) -> None:
        reference = json.loads(REFERENCE_PATH.read_text(encoding="utf-8"))
        anchors = {anchor["anchor_id"]: anchor for anchor in reference["anchors"]}
        observable_anchor_ids = {
            anchor_id
            for item in reference["rubric_items"]
            if item["evidence_type"] == "observable_anchor"
            for anchor_id in item["anchor_ids"]
        }

        for anchor_id in sorted(observable_anchor_ids):
            with self.subTest(anchor_id=anchor_id):
                asset = anchors[anchor_id]["standard_asset"]
                self.assertTrue((REFERENCE_PATH.parent / asset).is_file(), asset)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行测试并确认预期失败**

Run:

```bash
python3 -m unittest tests/test_grade_surgical_gown_glove_video_contract.py -v
```

Expected: `test_skill_defines_concise_media_comparison_contract` 和 `test_media_fields_are_scoped_to_key_comparisons` 失败；`test_observable_anchor_assets_exist` 通过。失败原因只能是新契约尚未写入，不得出现 JSON 解析错误或标准素材缺失。

- [ ] **Step 3: 暂不提交失败状态**

失败测试与实现一起进入 Task 2，避免提交一个主分支必然失败的中间状态。

---

## Task 2: 在 Skill 中实现精简双图对比流程

**Files:**
- Modify: `.qoder/skills/grade-surgical-gown-glove-video/SKILL.md:25-58`
- Modify: `.qoder/skills/grade-surgical-gown-glove-video/SKILL.md:121-235`
- Test: `tests/test_grade_surgical_gown_glove_video_contract.py`

- [ ] **Step 1: 扩展批阅流程，加入“筛选差异 → 生成双图”**

在现有“生成学生细证据”后增加独立步骤，要求：

1. 先根据评分结果筛选关键差异，不先生成素材。
2. 只选实际扣分动作、明确无菌风险，或有同相位正向证据支持的高价值不确定项。
3. 对速度快慢、停顿时长、单帧模糊等无法由静态图可靠证明的问题，不生成双图卡片。
4. 正常数量为 2–4 个；没有明确动作差异时为 0 个。
5. 先按学生实际时间戳截取 2–8 秒片段，再从片段中抽 4–6 帧细拼图。
6. 从对应锚点的 `standard_asset` 读取标准侧拼图，不重新处理标准视频。

在 Skill 中写入可直接执行的命令模板：

```bash
python3 scripts/clip_media.py <学生视频> \
  --start <学生动作开始时间> \
  --end <学生动作结束时间> \
  --output <工作目录>/comparison-<seq>-student.mp4 \
  --reencode --json --overwrite

python3 scripts/make_contact_sheet.py \
  <工作目录>/comparison-<seq>-student.mp4 \
  --output <工作目录>/comparison-<seq>-student.jpg \
  --every <片段时长除以目标帧数后的采样间隔> \
  --max-frames 6 --cols 3 --json --overwrite
```

明确提示：采样间隔应使实际帧数落在 4–6 帧，不足 4 帧时缩短 `--every` 后重做；图像必须对应同一动作相位。

- [ ] **Step 2: 替换媒体字段的全局禁止规则**

将现有“不得写 `items[].images` 或媒体嵌入字段”改为：

```markdown
- 媒体数组只允许出现在 `key_action_comparisons.items[].images[]`；其他评价项不得写 `images` 或媒体嵌入字段。
```

仍保留“不得使用 `时间轴式`”和顶层只有 `score`、`evaluations` 的约束。

- [ ] **Step 3: 新增评价项定义和字段映射**

在“改进建议”之后、“动作段对齐”之前新增表格行：

```markdown
| 关键动作双图对比 | 只展示最需要复核的学生动作与标准动作 | 精简模式输出 2-4 项；没有明确动作差异时输出空清单。 | 清单式 |
```

新增字段映射：

```markdown
**关键动作双图对比 · 清单式**

- `key_action_comparisons.format` ← `清单式`。
- `key_action_comparisons.items` ← 正常为 2-4 项；没有明确动作差异时必须为 `[]`。
- `items[].seq` ← 序号，从 1 开始。
- `items[].title` ← 动作名称和差异主题，避免使用笼统标题。
- `items[].standard_time` ← `reference.json` 中对应老师标准时间。
- `items[].student_time` ← 学生视频中的实际同相位时间段。
- `items[].text` ← 同时写明标准要求、学生可见表现、明确差异和纠正方法。
- `items[].images` ← 成功生成媒体时恰好包含 2 个对象，顺序固定为学生、标准；每个对象只有 `label`、`path`、`caption`。
- `items[].evidence` ← 学生关键片段路径、细拼图路径和同相位对齐依据。
```

补充失败降级：学生媒体生成失败时省略该项 `images` 并在 `evidence` 写明失败；标准素材不存在时不输出该对比项，并在 `risk_flags` 记录。

- [ ] **Step 4: 更新 JSON 示例**

在 `evaluations` 示例中按以下顺序插入：

```json
"key_action_comparisons": {
  "format": "清单式",
  "items": [
    {
      "seq": 1,
      "title": "动作名称——差异主题",
      "standard_time": "00:00-00:00",
      "student_time": "00:00-00:00",
      "text": "标准要求：...；学生表现：...；关键差异：...；改进：...。",
      "images": [
        {
          "label": "学生",
          "path": "/absolute/path/comparison-1-student.jpg",
          "caption": "学生同相位 4-6 帧细拼图"
        },
        {
          "label": "标准",
          "path": "references/surgical-gown-glove-v1/assets/anchors/example.jpg",
          "caption": "标准锚点细拼图"
        }
      ],
      "evidence": "学生片段：/absolute/path/comparison-1-student.mp4；对齐依据：同一动作起始、关键接触相位和结束相位。"
    }
  ]
}
```

最终总结构示例必须包含：

```json
"key_action_comparisons": { "format": "清单式", "items": [] }
```

- [ ] **Step 5: 加入输出前自检**

在输出核对中增加：

- 只有可复核的真实差异才生成对比项，标准视频或无明确动作差异的提交必须输出空数组。
- 非空时数量为 2–4 项；每项学生时间来自学生视频实际相位，标准时间来自对应锚点。
- 媒体成功时 `images` 恰好两项且顺序为学生、标准；其他评价项不出现媒体数组。
- 学生细拼图来自 2–8 秒同相位片段并包含 4–6 帧。
- 媒体缺失已按规则降级，不能伪造不存在的路径。

- [ ] **Step 6: 运行契约测试，确认全部通过**

Run:

```bash
python3 -m unittest tests/test_grade_surgical_gown_glove_video_contract.py -v
```

Expected: 3 个测试全部 `ok`，末行 `OK`。

- [ ] **Step 7: 提交 Skill 契约和测试**

```bash
git add -f \
  homework_review/.qoder/skills/grade-surgical-gown-glove-video/SKILL.md \
  homework_review/tests/test_grade_surgical_gown_glove_video_contract.py
git commit -m "feat: add surgical video media comparison contract"
```

---

## Task 3: 更新默认 Agent 提示词

**Files:**
- Modify: `.qoder/skills/grade-surgical-gown-glove-video/agents/openai.yaml:4`
- Test: `tests/test_grade_surgical_gown_glove_video_contract.py`

- [ ] **Step 1: 为默认提示词增加失败测试**

在测试模块常量区增加：

```python
AGENT_TEXT = (SKILL_DIR / "agents/openai.yaml").read_text(encoding="utf-8")
```

在测试类中增加：

```python
def test_default_prompt_requests_concise_comparisons(self) -> None:
    self.assertIn("关键动作双图对比", AGENT_TEXT)
    self.assertIn("没有明确差异时返回空清单", AGENT_TEXT)
```

Run:

```bash
python3 -m unittest tests/test_grade_surgical_gown_glove_video_contract.py -v
```

Expected: 新增的 `test_default_prompt_requests_concise_comparisons` 失败，原有 3 个测试继续通过。

- [ ] **Step 2: 强化默认提示词**

将 `default_prompt` 更新为单行 YAML 字符串，必须同时包含：只输入学生视频、按内置参考包评分、生成精简关键动作双图对比、没有明确差异时返回空清单、JSON-only。

目标内容：

```yaml
default_prompt: "使用 $grade-surgical-gown-glove-video 批阅学生提交的单个操作视频；只需要学生视频附件，按内置标准参考包逐项评分，并生成精简的关键动作双图对比；没有明确差异时返回空清单。最终回复首字符必须是 {，只输出一个包含 score 和 evaluations 的合法 JSON 对象，不要 Markdown 或任何说明文字。"
```

- [ ] **Step 3: 运行完整契约测试**

Run:

```bash
python3 -m unittest tests/test_grade_surgical_gown_glove_video_contract.py -v
```

Expected: 4 个测试全部 `ok`，末行 `OK`。

- [ ] **Step 4: 提交 Agent 配置和新增测试断言**

```bash
git add -f \
  homework_review/.qoder/skills/grade-surgical-gown-glove-video/agents/openai.yaml \
  homework_review/tests/test_grade_surgical_gown_glove_video_contract.py
git commit -m "feat: request concise surgical action comparisons"
```

---

## Task 4: 静态校验和媒体脚本烟测

**Files:**
- Verify: `.qoder/skills/grade-surgical-gown-glove-video/`
- Input: `批阅技能与素材/皖南医科大学-外科手术学/1.穿手术衣-视频批阅/老师操作视频.mp4`
- Output: `/tmp/surgical-gown-media-comparison-smoke/`

- [ ] **Step 1: 运行 Skill 快速校验**

Run:

```bash
python3 /Users/zhangyichi/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  .qoder/skills/grade-surgical-gown-glove-video
```

Expected: `Skill is valid!`

- [ ] **Step 2: 编译媒体脚本**

Run:

```bash
python3 -m py_compile \
  .qoder/skills/grade-surgical-gown-glove-video/scripts/clip_media.py \
  .qoder/skills/grade-surgical-gown-glove-video/scripts/make_contact_sheet.py
```

Expected: exit code 0，无 stderr。

- [ ] **Step 3: 用老师视频模拟生成学生关键片段**

Run:

```bash
mkdir -p /tmp/surgical-gown-media-comparison-smoke
python3 .qoder/skills/grade-surgical-gown-glove-video/scripts/clip_media.py \
  "批阅技能与素材/皖南医科大学-外科手术学/1.穿手术衣-视频批阅/老师操作视频.mp4" \
  --start 75 --end 81 \
  --output /tmp/surgical-gown-media-comparison-smoke/student-glove-01.mp4 \
  --reencode --json --overwrite \
  > /tmp/surgical-gown-media-comparison-smoke/clip.json
```

Expected: `clip.json` 可被 `json.loads` 解析，`ok` 为 `true`，片段时长接近 6 秒。

- [ ] **Step 4: 从片段生成 6 帧学生细拼图**

Run:

```bash
python3 .qoder/skills/grade-surgical-gown-glove-video/scripts/make_contact_sheet.py \
  /tmp/surgical-gown-media-comparison-smoke/student-glove-01.mp4 \
  --output /tmp/surgical-gown-media-comparison-smoke/student-glove-01.jpg \
  --every 1 --max-frames 6 --cols 3 --json --overwrite \
  > /tmp/surgical-gown-media-comparison-smoke/contact-sheet.json
```

Expected: `contact-sheet.json` 可解析，`ok` 为 `true`，`frame_count` 在 4–6 之间，JPG 文件存在且可打开。

- [ ] **Step 5: 自动核对烟测产物**

Run:

```bash
python3 - <<'PY'
import json
from pathlib import Path

root = Path('/tmp/surgical-gown-media-comparison-smoke')
clip = json.loads((root / 'clip.json').read_text(encoding='utf-8'))
sheet = json.loads((root / 'contact-sheet.json').read_text(encoding='utf-8'))
assert clip['ok'] is True
assert 5.5 <= float(clip['output_duration']) <= 6.5
assert sheet['ok'] is True
assert 4 <= int(sheet['frame_count']) <= 6
assert (root / 'student-glove-01.jpg').stat().st_size > 0
print('media smoke passed')
PY
```

Expected: 输出 `media smoke passed`。

---

## Task 5: 使用标准视频做 Qoder CLI 校准烟测

**Files:**
- Input: `批阅技能与素材/皖南医科大学-外科手术学/1.穿手术衣-视频批阅/老师操作视频.mp4`
- Output: `review_results/qodercli_runs/surgical-gown-media-comparison-standard/`

- [ ] **Step 1: 创建烟测输出目录**

```bash
mkdir -p review_results/qodercli_runs/surgical-gown-media-comparison-standard
```

- [ ] **Step 2: 按项目统一命令运行标准视频烟测**

```bash
qodercli -m qmodel_latest --yolo -p \
  --cwd /Users/zhangyichi/工作/能力训练/homework_review \
  --attachment "/Users/zhangyichi/工作/能力训练/homework_review/批阅技能与素材/皖南医科大学-外科手术学/1.穿手术衣-视频批阅/老师操作视频.mp4" \
  '使用 $grade-surgical-gown-glove-video 批阅附件。该附件是老师标准视频作为学生答案的校准样本。只输出一个有效 JSON 对象，顶层只有 score 和 evaluations；没有明确动作差异时 key_action_comparisons.items 必须为空；不要解释、不要 Markdown、不要代码块。' \
  > review_results/qodercli_runs/surgical-gown-media-comparison-standard/stdout.json \
  2> review_results/qodercli_runs/surgical-gown-media-comparison-standard/stderr.log
```

Expected: 命令完成且 stdout 中只有 JSON。

- [ ] **Step 3: 校验模型输出**

```bash
python3 - <<'PY'
import json
from pathlib import Path

path = Path('review_results/qodercli_runs/surgical-gown-media-comparison-standard/stdout.json')
data = json.loads(path.read_text(encoding='utf-8'))
assert set(data) == {'score', 'evaluations'}
assert data['score']['score_type'] == 'item'
assert data['score']['full_score'] == 100
assert len(data['score']['items']) == 21
assert data['score']['total'] == sum(item['score'] for item in data['score']['items'])
comparisons = data['evaluations']['key_action_comparisons']
assert comparisons['format'] == '清单式'
assert comparisons['items'] == []
assert '时间轴式' not in path.read_text(encoding='utf-8')
print('qoder standard-video calibration passed')
PY
```

Expected: 输出 `qoder standard-video calibration passed`。口述或画面不可确认项可以扣分，但可见标准动作不得被虚构为差异对比。

- [ ] **Step 4: 若 JSON-only 或空对比校准失败，按系统化调试处理**

先保存 stdout/stderr，不手工清洗模型输出作为通过依据。定位是 Skill 指令冲突、工具未执行、媒体路径失败还是模型误判，再只修改对应约束，重复 Task 1–5 的全部测试。

- [ ] **Step 5: 最终工作区检查**

```bash
git status --short -- \
  homework_review/.qoder/skills/grade-surgical-gown-glove-video \
  homework_review/tests/test_grade_surgical_gown_glove_video_contract.py \
  homework_review/docs/superpowers
```

Expected: 只出现本计划涉及的文件；烟测输出保持未跟踪或被忽略，不提交模型生成结果和 `/tmp` 产物。

---

## Completion Criteria

- 契约测试 4 项全部通过。
- Skill 快速校验和两个媒体脚本编译通过。
- 6 秒片段能生成 4–6 帧学生细拼图。
- 输出结构包含 `evaluations.key_action_comparisons`，且媒体字段只在该评价项中出现。
- 标准视频校准输出中 `key_action_comparisons.items` 为空，不制造差异。
- 21 项评分、100 分满分和总分求和规则无变化。
- 未执行线上同步或覆盖线上 Skill。
