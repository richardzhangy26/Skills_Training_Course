# Recent Homework Review Materials Sync Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Copy the approved recent student submissions into the existing classified materials directory, then add verified Polymas Skill links, validation states, authenticity labels, and capability boundaries to the catalog README.

**Architecture:** Treat the existing source folders as the source of truth and `批阅技能与素材/` as a read-only-style snapshot catalog updated through explicit entity copies. Keep all platform identifiers in the root README, record each copy in `整理清单.tsv`, and validate every binary copy with byte size plus SHA-256.

**Tech Stack:** macOS shell utilities (`mkdir`, `cp`, `find`, `stat`, `shasum`), Markdown, TSV, local Polymas scenario JSON.

## Global Constraints

- Use the existing `01` through `06` classification hierarchy; do not create a parallel recent-materials category.
- Copy only approved student submissions and course/calibration samples; do not place teacher references or grading standards in `学生作业/`.
- Distinguish real student submissions, course samples, and calibration samples in `README.md`.
- Use only confirmed `skillNid` and `skillVersionId` pairs.
- Do not modify `.qoder/skills`, platform drafts, existing reports, or source materials.
- Do not rebuild, overwrite, or change `批阅技能与素材/批阅技能与素材.zip`.
- Do not use symbolic links.
- Do not push or deploy.

---

## File Structure

**Create student material directories:**

- `批阅技能与素材/01-波形图与数字逻辑/通用波形图作业/学生作业/`
- `批阅技能与素材/03-视频与动作/AI销售顾问视频批阅/学生作业/`
- `批阅技能与素材/03-视频与动作/南京职校即梦AI文生视频/学生作业/`
- `批阅技能与素材/03-视频与动作/南京职校即梦AI图生视频/学生作业/`
- `批阅技能与素材/03-视频与动作/南京职校环保配音字幕/学生作业/`
- `批阅技能与素材/03-视频与动作/南京职校天谱乐低碳音视频/学生作业/`
- `批阅技能与素材/03-视频与动作/青岛农业大学无菌操作斜面接种/学生作业/`
- `批阅技能与素材/04-音频与口语/基础汉语第一课问好口语/学生作业/`
- `批阅技能与素材/05-文字作业与试卷/基础汉语第一课问好作文/学生作业/`

**Modify catalog files:**

- `批阅技能与素材/README.md`: add recent material paths, backend links, validation states, authenticity labels, and capability boundaries.
- `批阅技能与素材/整理清单.tsv`: append one completed copy row per new student file.

## Approved Copy Matrix

| Material type | Source | Target directory |
|---|---|---|
| Real student submission | `测试题拆分结果/测试题-学生提交.docx` | `01-波形图与数字逻辑/通用波形图作业/学生作业/` |
| Real student submission | `视频作业批阅素材-教发/AI应用顾问/符欣宇-大学英语大师版智能体课程教发.mp4` | `03-视频与动作/AI销售顾问视频批阅/学生作业/` |
| Course samples | All 4 MP4 and 4 TXT files directly under `南京职业技术学校-AI音视频作业/模块二4.2 使用即梦AI进行文生视频/` | `03-视频与动作/南京职校即梦AI文生视频/学生作业/` |
| Course samples | `优秀作业.mp4`, `普通作业.mp4` under module 4.3 | `03-视频与动作/南京职校即梦AI图生视频/学生作业/` |
| Course samples | `优秀作业.mp4`, `普通作业.mp4`, `优秀配音.mp3`, `普通配音.mp3` under module 5.2 | `03-视频与动作/南京职校环保配音字幕/学生作业/` |
| Course sample | `作业.mp4`, `跃动晨光.mp3`, `配音.mp3` under module 5.3 | `03-视频与动作/南京职校天谱乐低碳音视频/学生作业/` |
| Real student submissions | All 4 MP4 files under `视频批阅-食品微生物学-青岛农业大学/学生演示视频/` | `03-视频与动作/青岛农业大学无菌操作斜面接种/学生作业/` |
| Calibration samples | `基础汉语/foreigner_chinese_good.mp3`, `foreigner_chinese_mid.mp3`, `foreigner_chinese_poor.mp3` | `04-音频与口语/基础汉语第一课问好口语/学生作业/` |
| Calibration samples | Both DOCX files under `基础汉语/第一课-问好-作文批阅/学生样本/` | `05-文字作业与试卷/基础汉语第一课问好作文/学生作业/` |

---

### Task 1: Preflight Sources and Protect Existing Data

**Files:**
- Read: all sources in the Approved Copy Matrix
- Protect: `批阅技能与素材/批阅技能与素材.zip`

- [ ] **Step 1: Record the protected ZIP baseline**

Run:

```bash
stat -f '%z' "批阅技能与素材/批阅技能与素材.zip"
shasum -a 256 "批阅技能与素材/批阅技能与素材.zip"
```

Expected:

```text
1577933426
e9d6a9732d2904db4910052b719785e0d7ae6007b69c92b8fb67662c6ff94c92  批阅技能与素材/批阅技能与素材.zip
```

- [ ] **Step 2: Verify every source exists**

Run explicit `test -f` checks for the 28 approved source files. Expected: exit code `0` and no output.

- [ ] **Step 3: Inspect target conflicts**

For each target, if absent continue; if present, compare SHA-256 with the source. Expected: no differing same-name target. Stop before copying if any differing target exists.

---

### Task 2: Copy Document and Audio Materials

**Files:**
- Create: the waveform, basic-Chinese audio, and basic-Chinese writing `学生作业/` directories
- Copy: 1 waveform DOCX, 3 MP3 files, and 2 writing DOCX files

- [ ] **Step 1: Create destination directories**

Run:

```bash
mkdir -p \
  "批阅技能与素材/01-波形图与数字逻辑/通用波形图作业/学生作业" \
  "批阅技能与素材/04-音频与口语/基础汉语第一课问好口语/学生作业" \
  "批阅技能与素材/05-文字作业与试卷/基础汉语第一课问好作文/学生作业"
```

Expected: exit code `0`.

- [ ] **Step 2: Copy the six approved files without overwriting**

Use `cp -p -n` with one explicit source and target directory per file. Expected: six readable target files.

- [ ] **Step 3: Verify document and audio copies**

Compare source and target byte sizes and SHA-256 values. Expected: six exact matches.

---

### Task 3: Copy Video and Multimedia Materials

**Files:**
- Create: the six approved video-project `学生作业/` directories
- Copy: 22 approved video, audio, and prompt files

- [ ] **Step 1: Create destination directories**

Run:

```bash
mkdir -p \
  "批阅技能与素材/03-视频与动作/AI销售顾问视频批阅/学生作业" \
  "批阅技能与素材/03-视频与动作/南京职校即梦AI文生视频/学生作业" \
  "批阅技能与素材/03-视频与动作/南京职校即梦AI图生视频/学生作业" \
  "批阅技能与素材/03-视频与动作/南京职校环保配音字幕/学生作业" \
  "批阅技能与素材/03-视频与动作/南京职校天谱乐低碳音视频/学生作业" \
  "批阅技能与素材/03-视频与动作/青岛农业大学无菌操作斜面接种/学生作业"
```

Expected: exit code `0`.

- [ ] **Step 2: Copy the 22 approved files without overwriting**

Use `cp -p -n` for:

- 1 AI sales MP4
- 8 text-to-video MP4/TXT files
- 2 image-to-video MP4 files
- 4 eco dubbing MP4/MP3 files
- 3 Tianpule MP4/MP3 files
- 4 aseptic inoculation MP4 files

Expected: 22 readable target files.

- [ ] **Step 3: Verify multimedia copies**

Compare source and target byte sizes and SHA-256 values. Expected: 22 exact matches.

---

### Task 4: Update the Copy Manifest

**Files:**
- Modify: `批阅技能与素材/整理清单.tsv`

- [ ] **Step 1: Append one row per copied file**

For each of the 28 files append:

```text
<source>	<target>	复制	近期批阅 Skill 学生提交或明确标注的课程/校准样本	完成
```

Use exact source and target paths. Do not add teacher or synthetic AI-sales calibration files.

- [ ] **Step 2: Validate TSV shape**

Run:

```bash
awk -F '\t' 'NF != 5 { print NR ":" NF ":" $0; bad=1 } END { exit bad }' "批阅技能与素材/整理清单.tsv"
```

Expected: exit code `0` and no output.

- [ ] **Step 3: Verify manifest target paths**

For every appended row with action `复制`, confirm the target exists. Expected: all 28 new targets exist.

---

### Task 5: Update the Catalog README

**Files:**
- Modify: `批阅技能与素材/README.md`

- [ ] **Step 1: Update the introductory snapshot note**

State that the catalog now includes the 2026-07-10 through 2026-07-23 increment, while formal Skill source remains in `.qoder/skills`.

- [ ] **Step 2: Add the recent-material table**

Add one row for each of the nine projects. Each row must contain:

- category and project
- Skill name
- relative student-material link
- authenticity label
- verified backend Skill link
- status: `已验证`, `部分验证`, or `未逐份验证`

- [ ] **Step 3: Add platform links for medical video Skills without student copies**

Add configuration links for:

- `XrHkVSBRFn` / `Tl4tyFXR74`
- `hyG0ScQ8rl` / `1GWfaRjVCT`
- `EdZdWASt6K` / `8kylSyTXEA`
- `0EBc4OMp8m` / `VvLjsY8jgf`

State that current local material is teacher reference/calibration and was not copied as student work.

- [ ] **Step 4: Add capability-boundary sections**

Add concise four-level boundaries for:

- waveform and engineering diagrams
- action and experiment video
- speech, sales, and dubbing video
- spoken-language audio
- DOCX and scanned documents

Each section must distinguish stable recognition, conditional recognition, current non-reliable judgments, and manual-review triggers.

- [ ] **Step 5: Add authenticity and status definitions**

Define:

- real student submission
- course sample
- calibration sample
- teacher calibration
- `已验证`
- `部分验证`
- `未逐份验证`

---

### Task 6: Final Verification

**Files:**
- Verify: all 28 copied files
- Verify: `批阅技能与素材/README.md`
- Verify: `批阅技能与素材/整理清单.tsv`
- Protect: `批阅技能与素材/批阅技能与素材.zip`

- [ ] **Step 1: Verify file counts**

Expected counts:

```text
waveform: 1
AI sales: 1
text-to-video: 8
image-to-video: 2
eco dubbing: 4
Tianpule: 3
aseptic inoculation: 4
basic Chinese audio: 3
basic Chinese writing: 2
total: 28
```

- [ ] **Step 2: Verify all copy hashes**

Expected: every source SHA-256 equals its target SHA-256.

- [ ] **Step 3: Verify student directories contain no forbidden teacher material**

Search names for `教师`, `老师`, `标准答案`, `评分表`, `reference`, and Skill ZIP files. Expected: no matches in the nine new `学生作业/` directories.

- [ ] **Step 4: Verify README local links and platform IDs**

Confirm each relative material link resolves locally and each backend URL contains the corresponding confirmed `skillNid` and `skillVersionId`.

- [ ] **Step 5: Verify the protected ZIP is unchanged**

Expected:

```text
size: 1577933426
sha256: e9d6a9732d2904db4910052b719785e0d7ae6007b69c92b8fb67662c6ff94c92
```

- [ ] **Step 6: Inspect the final change scope**

Expected changed scope:

- new entity copies under the nine approved `学生作业/` directories
- `批阅技能与素材/README.md`
- `批阅技能与素材/整理清单.tsv`

No `.qoder/skills`, platform config, source material, report, or ZIP change is allowed.
