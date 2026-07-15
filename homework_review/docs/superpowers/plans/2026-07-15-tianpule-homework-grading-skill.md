# 天谱乐音视频作业批阅 Skill 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 扩展 `grade-low-carbon-ai-voiceover`，使其正确批阅含人声、AI 背景音乐和视频画面的天谱乐作业，对有效相关提交实行 80 分保底，并让指定优秀样本在严格 JSON 验收中达到 90 分以上。

**Architecture:** 媒体提取脚本只负责验证文件、音频流和客观技术信息；`SKILL.md` 负责有效性、证据降级、五维评分和 JSON 输出契约；QoderCLI 验收使用真实 `作业.mp4` 检查总分、结构和原始 JSON 可解析性。评分不得依赖联网 ASR，也不得针对文件名或单一样本硬编码。

**Tech Stack:** Python 3、ffmpeg/ffprobe、pytest、QoderCLI 1.0.44、`qmodel_latest`。

## Global Constraints

- 有效相关提交必须非空、可解析、含可解码音频流、可确认属于本次天谱乐低碳主题作业，且不是空白噪音、严重损坏或完全无关内容。
- 有效相关提交最低 80 分；90 分以上必须有可复核的优秀表现依据。
- 空文件、不可播放、无有效音轨、空白噪音或完全无关提交不适用 80 分保底。
- MP4、MOV 中存在可解码音轨时，不得因视频格式扣分。
- ASR 不可用不等于没有人声，不得仅因外部转录失败扣分。
- 原始 QoderCLI stdout 第一非空字符必须为 `{`，最后一个字符必须为 `}`，顶层只有 `score` 和 `evaluations`。
- 不修改学生提交文件，不引入必须联网下载的新依赖，不硬编码验收样本文件名或固定分数。

---

### Task 1: 为视频音轨支持建立 RED 回归测试

**Files:**
- Create: `.qoder/skills/grade-low-carbon-ai-voiceover/tests/test_extract_audio.py`
- Test: `.qoder/skills/grade-low-carbon-ai-voiceover/scripts/audio_common.py`
- Test: `.qoder/skills/grade-low-carbon-ai-voiceover/scripts/extract_audio.py`

**Interfaces:**
- Consumes: `audio_common.SUPPORTED_EXTENSIONS`、`extract_audio.analyze_audio_file(path, min_duration, max_duration, tolerance)`。
- Produces: MP4/MOV 白名单和“视频中存在音轨即可播放”的测试契约。

- [ ] **Step 1: 编写失败测试**

```python
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from audio_common import SUPPORTED_EXTENSIONS
from extract_audio import analyze_audio_file


def _run_ffmpeg(*args: str) -> None:
    subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def test_video_extensions_are_supported() -> None:
    assert ".mp4" in SUPPORTED_EXTENSIONS
    assert ".mov" in SUPPORTED_EXTENSIONS


def test_mp4_with_audio_is_supported_and_playable(tmp_path: Path) -> None:
    submission = tmp_path / "submission.mp4"
    _run_ffmpeg(
        "-f", "lavfi", "-i", "color=c=green:s=160x90:d=1",
        "-f", "lavfi", "-i", "sine=frequency=440:duration=1",
        "-shortest", "-c:v", "mpeg4", "-c:a", "aac", str(submission),
    )
    result = analyze_audio_file(submission, min_duration=0.5, max_duration=2.0)
    assert result["status"] == "ok"
    assert result["technical_playable"] is True
    assert result["audio"]["supported_extension"] is True
    assert result["audio"]["has_video_stream"] is True
    assert not any("不在推荐支持列表" in item for item in result["warnings"])


def test_mp4_without_audio_is_invalid(tmp_path: Path) -> None:
    submission = tmp_path / "silent-video.mp4"
    _run_ffmpeg(
        "-f", "lavfi", "-i", "color=c=black:s=160x90:d=1",
        "-c:v", "mpeg4", "-an", str(submission),
    )
    result = analyze_audio_file(submission, min_duration=0.5, max_duration=2.0)
    assert result["status"] == "invalid"
    assert result["technical_playable"] is False
    assert "未检测到可解码音频流。" in result["errors"]
```

- [ ] **Step 2: 运行测试并确认正确失败**

Run: `python3 -m pytest .qoder/skills/grade-low-carbon-ai-voiceover/tests/test_extract_audio.py -v`

Expected: MP4/MOV 白名单相关断言 FAIL；无音轨视频测试 PASS。

---

### Task 2: 实现 MP4/MOV 音轨支持

**Files:**
- Modify: `.qoder/skills/grade-low-carbon-ai-voiceover/scripts/audio_common.py`
- Modify: `.qoder/skills/grade-low-carbon-ai-voiceover/scripts/extract_audio.py`
- Test: `.qoder/skills/grade-low-carbon-ai-voiceover/tests/test_extract_audio.py`

**Interfaces:**
- Consumes: Task 1 的三项媒体测试。
- Produces: `SUPPORTED_EXTENSIONS` 包含 `.mp4`、`.mov`，含音轨视频返回 `status="ok"`。

- [ ] **Step 1: 扩展媒体白名单**

```python
SUPPORTED_EXTENSIONS = {
    ".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".mp4", ".mov"
}
```

把 `extract_audio.py` 的模块说明和 CLI 说明由纯 audio 改为 audio/video media，保持 `analyze_audio_file` 函数签名不变。

- [ ] **Step 2: 运行媒体测试**

Run: `python3 -m pytest .qoder/skills/grade-low-carbon-ai-voiceover/tests/test_extract_audio.py -v`

Expected: `3 passed`。

- [ ] **Step 3: 用真实 MP4 复核**

Run:

```bash
python3 .qoder/skills/grade-low-carbon-ai-voiceover/scripts/extract_audio.py \
  "南京职业技术学校-AI音视频作业/模块二5.3 使用AI工具天谱乐生成背景音乐/作业.mp4" \
  --min-duration 30 --max-duration 60 --json
```

Expected: `status="ok"`、`audio.supported_extension=true`、`audio.has_video_stream=true`、`duration_status="within"`，warnings 不含“不在推荐支持列表”。

- [ ] **Step 4: 提交媒体支持改动**

```bash
git add -f homework_review/.qoder/skills/grade-low-carbon-ai-voiceover/scripts \
  homework_review/.qoder/skills/grade-low-carbon-ai-voiceover/tests/test_extract_audio.py
git commit -m "fix: support video audio in low-carbon grading skill"
```

---

### Task 3: 为评分与输出契约建立 RED 测试并修改 Skill

**Files:**
- Create: `.qoder/skills/grade-low-carbon-ai-voiceover/tests/test_skill_contract.py`
- Modify: `.qoder/skills/grade-low-carbon-ai-voiceover/SKILL.md`
- Modify: `.qoder/skills/grade-low-carbon-ai-voiceover/references/assignment.md`
- Modify: `.qoder/skills/grade-low-carbon-ai-voiceover/agents/openai.yaml`

**Interfaces:**
- Consumes: 有效性、80 分保底、优秀区分度、ASR 降级和 JSON-only 设计。
- Produces: 五维标识 `topic_value`、`voiceover`、`music_mix`、`technical_compliance`、`creative_completion`；满分 25、20、25、15、15。

- [ ] **Step 1: 编写失败的文本契约测试**

```python
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]


def test_skill_declares_valid_submission_floor_and_exclusions() -> None:
    text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    assert "有效相关提交最低 80 分" in text
    assert "完全无关" in text
    assert "不适用 80 分保底" in text


def test_skill_declares_video_and_asr_fallback() -> None:
    text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    assert "MP4" in text and "MOV" in text
    assert "无法转录不等于没有人声" in text
    assert "不得仅因 ASR" in text


def test_skill_declares_score_contract() -> None:
    text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    for dimension_id in (
        "topic_value", "voiceover", "music_mix",
        "technical_compliance", "creative_completion",
    ):
        assert dimension_id in text
    assert "25、20、25、15、15" in text
    assert "第一非空字符必须是 `{`" in text
    assert "最后一个字符必须是 `}`" in text
```

- [ ] **Step 2: 运行契约测试并确认失败**

Run: `python3 -m pytest .qoder/skills/grade-low-carbon-ai-voiceover/tests/test_skill_contract.py -v`

Expected: 三项测试因现有 skill 未声明新契约而 FAIL。

- [ ] **Step 3: 修改批阅对象和证据降级规则**

在 `SKILL.md` 增加：

```markdown
## 有效相关提交与保底规则

有效相关提交必须同时满足：文件非空且可解析、包含可解码音频流、能够从音频/画面/同目录材料/提交上下文确认属于本次天谱乐低碳主题作业，并且不是空白噪音、严重损坏或完全无关内容。

有效相关提交最低 80 分。空文件、不可播放、无有效音轨、空白噪音或完全无关提交不适用 80 分保底。先按五维独立评分；若有效相关提交的维度总分低于 80，再按作品已经完成的可验证部分合理调整到 80–84，不得给所有有效提交固定分数。

## ASR 与证据降级

完整收听或可用转录结果优先。无法转录不等于没有人声；不得仅因 ASR、Whisper、网络或模型不可用而扣分或判定无人声。结合可听音频、画面、同目录配音材料和提交上下文评分，对无法确认的具体台词标记证据限制，不得虚构。
```

- [ ] **Step 4: 修改五维评分与分档**

```markdown
| id | 维度 | 满分 |
|---|---|---:|
| `topic_value` | 主题内容与价值导向 | 25 |
| `voiceover` | 配音表达与信息传达 | 20 |
| `music_mix` | AI 背景音乐与混音 | 25 |
| `technical_compliance` | 技术质量与时长合规 | 15 |
| `creative_completion` | 创意感染力与完成度 | 15 |
```

明确 80–84 基础有效、85–89 良好、90–94 优秀、95–100 示范；90 分以上必须逐项写出可复核依据。

- [ ] **Step 5: 强化 JSON-only 正向契约**

```markdown
最终响应就是一个 JSON object，不是对批阅过程的说明。第一非空字符必须是 `{`，最后一个字符必须是 `}`。对象前后没有任何文本。顶层依次包含 `score` 和 `evaluations`，不得输出 Markdown、标题、分析摘要、工具失败说明或自然语言前后缀；所有证据限制写入字段值。
```

要求五个维度依次使用上述 id，且每项包含 `id`、`name`、`score`、`full_score`、`reason`。

- [ ] **Step 6: 同步 reference 与显示元数据**

`references/assignment.md` 增加音频/音视频成品、AI 背景音乐、80 分保底与优秀区分度要求；`agents/openai.yaml` 显示名称改为“低碳生活AI音视频批阅”，短描述改为“批阅含配音和AI背景音乐的低碳主题音视频成品”。

- [ ] **Step 7: 运行全部本地测试**

Run: `python3 -m pytest .qoder/skills/grade-low-carbon-ai-voiceover/tests -v`

Expected: `6 passed`。

- [ ] **Step 8: 提交评分契约改动**

```bash
git add -f homework_review/.qoder/skills/grade-low-carbon-ai-voiceover
git commit -m "feat: grade tianpule audio-video submissions"
```

---

### Task 4: QoderCLI GREEN 验收循环与证据报告

**Files:**
- Create: `tmp/qoder_tianpule_acceptance_20260715/stdout.json`
- Create: `tmp/qoder_tianpule_acceptance_20260715/stderr.log`
- Create: `tmp/qoder_tianpule_acceptance_20260715/validation.json`
- Create: `tmp/qoder_tianpule_acceptance_20260715/run_receipt.md`

**Interfaces:**
- Consumes: 修改后的 skill、真实 `作业.mp4`、`qmodel_latest`。
- Produces: 命令、退出码、原始输出、结构验证、总分和 Loopy 运行收据。

- [ ] **Step 1: 使用真实 MP4 运行 QoderCLI**

```bash
run_dir="/Users/zhangyichi/工作/能力训练/homework_review/tmp/qoder_tianpule_acceptance_20260715"
mkdir -p "$run_dir"
qodercli -m qmodel_latest --yolo -p \
  --cwd /Users/zhangyichi/工作/能力训练/homework_review \
  --attachment "/Users/zhangyichi/工作/能力训练/homework_review/南京职业技术学校-AI音视频作业/模块二5.3 使用AI工具天谱乐生成背景音乐/作业.mp4" \
  '使用 $grade-low-carbon-ai-voiceover 批阅附件。只输出一个有效 JSON 对象，顶层只有 score 和 evaluations；不要解释、不要 Markdown、不要代码块。' \
  >"$run_dir/stdout.json" 2>"$run_dir/stderr.log"
```

Expected: exit code 0。

- [ ] **Step 2: 严格验证原始输出**

```python
import json
from pathlib import Path

stdout_path = "/Users/zhangyichi/工作/能力训练/homework_review/tmp/qoder_tianpule_acceptance_20260715/stdout.json"
obj = json.loads(Path(stdout_path).read_text(encoding="utf-8"))
assert list(obj) == ["score", "evaluations"]
score = obj["score"]
assert score["score_type"] == "dimension"
assert score["full_score"] == 100
assert score["total"] >= 90
dimensions = score["dimensions"]
assert [item["id"] for item in dimensions] == [
    "topic_value", "voiceover", "music_mix",
    "technical_compliance", "creative_completion",
]
assert [item["full_score"] for item in dimensions] == [25, 20, 25, 15, 15]
assert sum(item["score"] for item in dimensions) == score["total"]
assert all(0 <= item["score"] <= item["full_score"] for item in dimensions)
assert set(obj["evaluations"]) == {
    "综合评语", "改进建议", "任务要求核对", "音频基础属性"
}
assert obj["evaluations"]["综合评语"]["format"] == "文本式"
assert obj["evaluations"]["改进建议"]["format"] == "清单式"
assert obj["evaluations"]["任务要求核对"]["format"] == "对比式"
assert obj["evaluations"]["音频基础属性"]["format"] == "标签式"
```

Expected: 所有断言通过，`score.total >= 90`。

- [ ] **Step 3: 人工复核高分理由**

- 明确识别 MP4 内有效音轨；
- 不因 MP4 格式扣分；
- 不把 ASR 不可用当作无人声；
- 高分理由覆盖主题、配音、背景音乐/混音、技术质量和视听完成度；
- 不出现固定样本触发分数或无法验证的具体台词。

- [ ] **Step 4: 只针对失败项做一次最小迭代**

若 JSON、结构、分数或证据规则失败，记录失败项，只修改能解释该失败的一个契约或脚本判断，然后重复 Steps 1–3。成功即停止；一轮修改未改善对应失败项则以“无进展”停止；外部故障无法通过 skill 修复则以“阻塞”停止。

- [ ] **Step 5: 写入 Loopy 运行收据**

`run_receipt.md` 记录 loop 定义、skill 版本、附件、模型、命令、日志位置、验收条件、每轮改动、每轮分数、JSON 验证结果和最终终止状态。

---

## 最终验证

- [ ] `python3 -m pytest .qoder/skills/grade-low-carbon-ai-voiceover/tests -v` 全部通过。
- [ ] 真实 MP4 提取结果显示格式受支持且音轨可播放。
- [ ] QoderCLI 退出码为 0，原始 stdout 可直接 `json.loads`。
- [ ] 总分不低于 90，维度之和及评价项格式正确。
- [ ] git diff 只包含本任务授权的 skill、测试、计划和验收产物，不覆盖用户其他改动。
