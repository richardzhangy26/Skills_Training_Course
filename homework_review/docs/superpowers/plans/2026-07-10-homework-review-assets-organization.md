# 批阅技能与素材分类整理实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在不改变 `.qoder/skills` 正式技能发现路径的前提下，把 `homework_review` 根目录中可匹配的批阅素材归入统一分类目录，并提供技能、运行输出和测试包入口。

**Architecture:** 使用“素材实移、技能保位、运行目录链接”的结构。课程素材和独立历史技能移动到 `批阅技能与素材/`；20 个正式 Qoder 技能仍留在 `.qoder/skills`，分类项目中使用相对符号链接；`output/`、`test_bundles/` 等运行目录保留原位并建立交叉入口。

**Tech Stack:** macOS/zsh 文件操作、相对符号链接、Markdown 索引、TSV 迁移清单、Git（仅提交设计与计划文档，不提交大体积媒体素材）。

## Global Constraints

- 正式技能保留在 `.qoder/skills`，整理前后正式 `SKILL.md` 数量必须均为 20。
- 不修改技能评分逻辑、提示词、脚本或评价结构。
- 不覆盖同名文件，不删除非完全重复文件，不提交大体积媒体素材到 Git。
- `output/`、`test_bundles/`、`tmp/`、`test/` 和核心 Python 程序保持原位。
- 无法可靠匹配的素材进入 `99-待确认`；已识别但没有专用技能的项目标记为“技能待补”。
- 每次移动记录源路径、目标路径、动作、分类依据和状态。

---

### Task 1: 建立迁移前基线和分类骨架

**Files:**
- Create: `批阅技能与素材/README.md`
- Create: `批阅技能与素材/整理清单.tsv`
- Create: `批阅技能与素材/01-波形图与数字逻辑/`
- Create: `批阅技能与素材/02-图片识别与PPT/`
- Create: `批阅技能与素材/03-实验报告与综合文档/`
- Create: `批阅技能与素材/04-视频与动作/`
- Create: `批阅技能与素材/05-音频与口语/`
- Create: `批阅技能与素材/06-文字作业与试卷/`
- Create: `批阅技能与素材/07-通用技能与工具/`
- Create: `批阅技能与素材/99-待确认/`

**Interfaces:**
- Consumes: 当前 `homework_review` 根目录、`.qoder/skills` 和设计文档。
- Produces: 后续任务共同使用的分类根目录和迁移前基线。

- [ ] **Step 1: 记录正式技能数量和根目录素材基线**

Run:

```bash
find .qoder/skills -mindepth 2 -maxdepth 2 -type f -name SKILL.md | sort > /tmp/homework-review-skills-before.txt
test "$(wc -l < /tmp/homework-review-skills-before.txt | tr -d ' ')" = "20"
find . -mindepth 1 -maxdepth 1 -print | sort > /tmp/homework-review-root-before.txt
```

Expected: 两个命令均退出码为 `0`，技能基线共有 `20` 行。

- [ ] **Step 2: 建立八个分类目录**

Run:

```bash
mkdir -p \
  '批阅技能与素材/01-波形图与数字逻辑' \
  '批阅技能与素材/02-图片识别与PPT' \
  '批阅技能与素材/03-实验报告与综合文档' \
  '批阅技能与素材/04-视频与动作' \
  '批阅技能与素材/05-音频与口语' \
  '批阅技能与素材/06-文字作业与试卷' \
  '批阅技能与素材/07-通用技能与工具' \
  '批阅技能与素材/99-待确认'
```

Expected: 八个目录全部存在。

- [ ] **Step 3: 创建迁移清单表头**

使用 `apply_patch` 创建 `批阅技能与素材/整理清单.tsv`，首行为：

```text
原路径	目标路径	动作	分类依据	状态
```

Expected: 文件使用 UTF-8 编码，包含且只包含一个表头行。

---

### Task 2: 整理波形图、数字逻辑和图片识别素材

**Files:**
- Move: `波形图作业批阅/` -> `批阅技能与素材/01-波形图与数字逻辑/四题数字逻辑图题/原始素材/波形图作业批阅/`
- Move: `信息工程大学-通信原理-作业批阅/` -> `批阅技能与素材/01-波形图与数字逻辑/四题数字逻辑图题/原始素材/信息工程大学-通信原理-作业批阅/`
- Move: `grade-digital-logic-four-questions/` -> `批阅技能与素材/01-波形图与数字逻辑/四题数字逻辑图题/历史版本/grade-digital-logic-four-questions/`
- Move: `grade-digital-logic-four-questions.zip` -> `批阅技能与素材/01-波形图与数字逻辑/四题数字逻辑图题/交付包/`
- Move: `四题数字逻辑图题标准答案及评分要点汇总.docx` -> `批阅技能与素材/01-波形图与数字逻辑/四题数字逻辑图题/教师基准/`
- Move: `作业批阅技能测试-波形图.docx` -> `批阅技能与素材/01-波形图与数字逻辑/四题数字逻辑图题/学生样例/`
- Move: `无关答案.png` -> `批阅技能与素材/01-波形图与数字逻辑/四题数字逻辑图题/学生样例/边界测试-无关答案.png`
- Move: `水生生物学藻类易混种辨认/` -> `批阅技能与素材/02-图片识别与PPT/水生生物学藻类易混种辨认/`

**Interfaces:**
- Consumes: Task 1 的分类骨架。
- Produces: 数字逻辑、通用波形图和藻类识别三个项目入口。

- [ ] **Step 1: 创建项目子目录并移动素材**

Run:

```bash
mkdir -p \
  '批阅技能与素材/01-波形图与数字逻辑/通用波形图作业/技能入口' \
  '批阅技能与素材/01-波形图与数字逻辑/四题数字逻辑图题/'{技能入口,原始素材,教师基准,学生样例,交付包,历史版本}
mv '波形图作业批阅' '批阅技能与素材/01-波形图与数字逻辑/四题数字逻辑图题/原始素材/'
mv '信息工程大学-通信原理-作业批阅' '批阅技能与素材/01-波形图与数字逻辑/四题数字逻辑图题/原始素材/'
mv 'grade-digital-logic-four-questions' '批阅技能与素材/01-波形图与数字逻辑/四题数字逻辑图题/历史版本/'
mv 'grade-digital-logic-four-questions.zip' '批阅技能与素材/01-波形图与数字逻辑/四题数字逻辑图题/交付包/'
mv '四题数字逻辑图题标准答案及评分要点汇总.docx' '批阅技能与素材/01-波形图与数字逻辑/四题数字逻辑图题/教师基准/'
mv '作业批阅技能测试-波形图.docx' '批阅技能与素材/01-波形图与数字逻辑/四题数字逻辑图题/学生样例/'
mv '无关答案.png' '批阅技能与素材/01-波形图与数字逻辑/四题数字逻辑图题/学生样例/边界测试-无关答案.png'
mv '水生生物学藻类易混种辨认' '批阅技能与素材/02-图片识别与PPT/'
```

Expected: 八个源路径均不再以普通文件或目录存在，八个目标均存在。

- [ ] **Step 2: 建立三个正式技能入口**

Run:

```bash
mkdir -p '批阅技能与素材/02-图片识别与PPT/水生生物学藻类易混种辨认/技能入口'
ln -s '../../../../.qoder/skills/grade-waveform-homework' '批阅技能与素材/01-波形图与数字逻辑/通用波形图作业/技能入口/grade-waveform-homework'
ln -s '../../../../.qoder/skills/grade-digital-logic-four-questions' '批阅技能与素材/01-波形图与数字逻辑/四题数字逻辑图题/技能入口/grade-digital-logic-four-questions'
ln -s '../../../../.qoder/skills/grade-aquatic-algae-confusable-species' '批阅技能与素材/02-图片识别与PPT/水生生物学藻类易混种辨认/技能入口/grade-aquatic-algae-confusable-species'
```

Expected: 三个符号链接通过 `test -e` 检查。

- [ ] **Step 3: 把本任务的每个移动和链接追加到迁移清单**

使用 `apply_patch` 在 `整理清单.tsv` 中逐行写入原路径、目标路径、`移动` 或 `链接`、名称/内容匹配依据和 `完成` 状态。

Expected: Task 2 的十一项操作均有记录。

---

### Task 3: 整理实验报告和综合文档素材

**Files:**
- Move: `实验报告批阅智能体/` -> `批阅技能与素材/03-实验报告与综合文档/实验报告批阅智能体/`
- Move: `燃烧学-西安交通大学-作业批阅/` -> `批阅技能与素材/03-实验报告与综合文档/燃烧学-西安交通大学-作业批阅/`
- Move: `doc_test/` -> `批阅技能与素材/03-实验报告与综合文档/燃烧学-西安交通大学-作业批阅/测试素材/doc_test/`
- Create compatibility link: `燃烧学-西安交通大学-作业批阅` -> 分类后的项目目录。

**Interfaces:**
- Consumes: Task 1 的分类骨架和现有燃烧学脚本默认路径。
- Produces: 两个实验报告项目；燃烧学旧路径仍可被现有脚本访问。

- [ ] **Step 1: 移动两个实验报告项目和燃烧学测试文档**

Run:

```bash
mv '实验报告批阅智能体' '批阅技能与素材/03-实验报告与综合文档/'
mv '燃烧学-西安交通大学-作业批阅' '批阅技能与素材/03-实验报告与综合文档/'
mkdir -p '批阅技能与素材/03-实验报告与综合文档/燃烧学-西安交通大学-作业批阅/测试素材'
mv 'doc_test' '批阅技能与素材/03-实验报告与综合文档/燃烧学-西安交通大学-作业批阅/测试素材/'
```

Expected: 三个目标目录存在。

- [ ] **Step 2: 创建燃烧学旧路径兼容入口**

Run:

```bash
ln -s '批阅技能与素材/03-实验报告与综合文档/燃烧学-西安交通大学-作业批阅' '燃烧学-西安交通大学-作业批阅'
test -d '燃烧学-西安交通大学-作业批阅/作业批阅智能体-燃烧学'
```

Expected: 旧路径是符号链接，现有三个燃烧学脚本无需修改即可访问资料。

- [ ] **Step 3: 记录素材齐全但缺少专用正式技能的状态**

使用 `apply_patch` 创建两个项目的 `README.md`，明确“当前有教师基准、学生样例和批阅结果，但 `.qoder/skills` 中没有同名专用技能”。

Expected: 两个 README 均包含 `技能状态：待补`。

---

### Task 4: 整理视频、动作和英语多模态素材

**Files:**
- Move: `舞蹈动作批阅/` -> `批阅技能与素材/04-视频与动作/通用动作视频批阅/舞蹈动作批阅/`
- Move: `action-video-review0612/` -> `批阅技能与素材/04-视频与动作/通用动作视频批阅/历史版本/action-video-review0612/`
- Move: `皖南医科大学-外科手术学/` -> `批阅技能与素材/04-视频与动作/皖南医科大学-外科手术学/`
- Move: `南京职业技术学校/` -> `批阅技能与素材/04-视频与动作/南京职业技术学校-AI音视频作业/`
- Move: `英文演讲作业样例（需上交的Word文档）/` -> `批阅技能与素材/04-视频与动作/英语演讲与辩论模联/原始素材/`
- Create compatibility link: `舞蹈动作批阅` -> 分类后的舞蹈素材目录。

**Interfaces:**
- Consumes: Task 1 分类骨架及保留原绝对路径的历史动作视频清单。
- Produces: 七个视频类正式技能入口和三组课程素材。

- [ ] **Step 1: 移动四组视频课程素材和独立旧技能**

Run:

```bash
mkdir -p \
  '批阅技能与素材/04-视频与动作/通用动作视频批阅/历史版本' \
  '批阅技能与素材/04-视频与动作/英语演讲与辩论模联/原始素材'
mv '舞蹈动作批阅' '批阅技能与素材/04-视频与动作/通用动作视频批阅/'
mv 'action-video-review0612' '批阅技能与素材/04-视频与动作/通用动作视频批阅/历史版本/'
mv '皖南医科大学-外科手术学' '批阅技能与素材/04-视频与动作/'
mv '南京职业技术学校' '批阅技能与素材/04-视频与动作/南京职业技术学校-AI音视频作业'
mv '英文演讲作业样例（需上交的Word文档）' '批阅技能与素材/04-视频与动作/英语演讲与辩论模联/原始素材/'
ln -s '批阅技能与素材/04-视频与动作/通用动作视频批阅/舞蹈动作批阅' '舞蹈动作批阅'
```

Expected: 五个目标存在，舞蹈旧路径仍能访问标准视频。

- [ ] **Step 2: 创建七个正式视频技能入口**

Run:

```bash
mkdir -p \
  '批阅技能与素材/04-视频与动作/通用动作视频批阅/技能入口' \
  '批阅技能与素材/04-视频与动作/皖南医科大学-外科手术学/技能入口' \
  '批阅技能与素材/04-视频与动作/南京职业技术学校-AI音视频作业/技能入口' \
  '批阅技能与素材/04-视频与动作/英语演讲与辩论模联/技能入口'
ln -s '../../../../.qoder/skills/grade-action-video-comparison' '批阅技能与素材/04-视频与动作/通用动作视频批阅/技能入口/grade-action-video-comparison'
ln -s '../../../../.qoder/skills/grade-surgical-gown-glove-video' '批阅技能与素材/04-视频与动作/皖南医科大学-外科手术学/技能入口/grade-surgical-gown-glove-video'
ln -s '../../../../.qoder/skills/grade-jimeng-text-to-video-homework' '批阅技能与素材/04-视频与动作/南京职业技术学校-AI音视频作业/技能入口/grade-jimeng-text-to-video-homework'
ln -s '../../../../.qoder/skills/grade-jimeng-image-to-video-heavy-equipment' '批阅技能与素材/04-视频与动作/南京职业技术学校-AI音视频作业/技能入口/grade-jimeng-image-to-video-heavy-equipment'
ln -s '../../../../.qoder/skills/grade-hailuo-bijian-eco-dubbing-subtitles' '批阅技能与素材/04-视频与动作/南京职业技术学校-AI音视频作业/技能入口/grade-hailuo-bijian-eco-dubbing-subtitles'
ln -s '../../../../.qoder/skills/grade-english-speech-presentation' '批阅技能与素材/04-视频与动作/英语演讲与辩论模联/技能入口/grade-english-speech-presentation'
ln -s '../../../../.qoder/skills/grade-english-debate-mun' '批阅技能与素材/04-视频与动作/英语演讲与辩论模联/技能入口/grade-english-debate-mun'
```

Expected: 七个链接通过 `find 批阅技能与素材/04-视频与动作 -type l` 和 `test -e` 检查。

- [ ] **Step 3: 链接英语演讲与辩论测试包**

Run:

```bash
mkdir -p '批阅技能与素材/04-视频与动作/英语演讲与辩论模联/测试结果'
ln -s '../../../../test_bundles/english_speech_debate_review_test_bundle_20260702_143055' '批阅技能与素材/04-视频与动作/英语演讲与辩论模联/测试结果/english_speech_debate_review_test_bundle'
ln -s '../../../../test_bundles/english_speech_debate_review_test_bundle_20260702_143055.zip' '批阅技能与素材/04-视频与动作/英语演讲与辩论模联/测试结果/english_speech_debate_review_test_bundle.zip'
```

Expected: 两个测试包入口可访问，`test_bundles/` 原目录未移动。

---

### Task 5: 整理音频与口语素材

**Files:**
- Move: `音乐作业批阅/` -> `批阅技能与素材/05-音频与口语/音乐表演批阅/`
- Move: `外语音频发音批阅-native模型版/` -> `批阅技能与素材/05-音频与口语/外语发音批阅/技能历史版本/`
- Move: `外语音频发音批阅-native模型版.zip` -> `批阅技能与素材/05-音频与口语/外语发音批阅/交付包/`

**Interfaces:**
- Consumes: Task 4 已移动的南京职业技术学校项目。
- Produces: 音乐、外语发音、低碳配音三个项目入口。

- [ ] **Step 1: 移动音频素材和独立外语发音技能**

Run:

```bash
mkdir -p \
  '批阅技能与素材/05-音频与口语/音乐表演批阅' \
  '批阅技能与素材/05-音频与口语/外语发音批阅/'{技能入口,技能历史版本,交付包} \
  '批阅技能与素材/05-音频与口语/低碳生活AI配音/'{技能入口,教师基准}
mv '音乐作业批阅' '批阅技能与素材/05-音频与口语/音乐表演批阅/原始素材'
mv '外语音频发音批阅-native模型版' '批阅技能与素材/05-音频与口语/外语发音批阅/技能历史版本/'
mv '外语音频发音批阅-native模型版.zip' '批阅技能与素材/05-音频与口语/外语发音批阅/交付包/'
```

Expected: 三个源路径已迁移，目标存在。

- [ ] **Step 2: 创建两个正式音频技能入口和一个独立技能入口**

Run:

```bash
mkdir -p '批阅技能与素材/05-音频与口语/音乐表演批阅/技能入口'
ln -s '../../../../.qoder/skills/grade-music-performance' '批阅技能与素材/05-音频与口语/音乐表演批阅/技能入口/grade-music-performance'
ln -s '../../../../.qoder/skills/grade-low-carbon-ai-voiceover' '批阅技能与素材/05-音频与口语/低碳生活AI配音/技能入口/grade-low-carbon-ai-voiceover'
ln -s '../技能历史版本/外语音频发音批阅-native模型版' '批阅技能与素材/05-音频与口语/外语发音批阅/技能入口/外语音频发音批阅-native模型版'
```

Expected: 三个入口均可访问对应 `SKILL.md`。

- [ ] **Step 3: 为低碳配音建立南京课程资料交叉入口**

Run:

```bash
ln -s '../../../04-视频与动作/南京职业技术学校-AI音视频作业/3【PDF】 使用AI工具天谱乐_副本.pdf' '批阅技能与素材/05-音频与口语/低碳生活AI配音/教师基准/南京职校-天谱乐课程资料.pdf'
```

Expected: 链接目标存在；南京课程资料不复制。

---

### Task 6: 整理文字作业、试卷和其他课程文档

**Files:**
- Move: `通信原理-单元测试1/`、`通信原理-单元测试2/`、`通信原理-单元测试3/` -> `批阅技能与素材/06-文字作业与试卷/通信原理单元测试/`
- Move: `skill_test_results/` -> `批阅技能与素材/06-文字作业与试卷/通信原理单元测试/测试结果/`
- Move: `测试题2.docx`、`图片1.png` -> `批阅技能与素材/06-文字作业与试卷/通信原理单元测试/历史版本/根目录重复文件/`
- Move: `湖南工学院-离散数学-技能批阅测试/`、`湖南工学院-离散数学-技能批阅测试.zip`、`离散数学批阅文档.docx` -> `批阅技能与素材/06-文字作业与试卷/离散数学证明题批阅/`
- Move: `日语日记批阅/` -> `批阅技能与素材/06-文字作业与试卷/日语日记批阅/`
- Move: `批阅文档/` -> `批阅技能与素材/06-文字作业与试卷/综合批阅文档/`
- Move: `安徽中医药高等专科学校-中医药学/`、`中医诊断学作业一.docx` -> `批阅技能与素材/06-文字作业与试卷/中医诊断学/`
- Move: `古代汉语/` -> `批阅技能与素材/06-文字作业与试卷/古代汉语/`
- Move: `document/` -> `批阅技能与素材/06-文字作业与试卷/其他课程文档素材/`
- Move: `题目含图完整版-3.docx` -> `批阅技能与素材/06-文字作业与试卷/大学物理题库（技能待补）/教师基准/`

**Interfaces:**
- Consumes: Task 1 分类骨架、正式文档类技能和已确认的 DOCX 内容识别结果。
- Produces: 八个正式文档类技能入口及五组“技能待补”课程素材。

- [ ] **Step 1: 移动通信原理、离散数学和日语项目**

Run:

```bash
mkdir -p \
  '批阅技能与素材/06-文字作业与试卷/通信原理单元测试/'{技能入口,测试结果,历史版本/根目录重复文件} \
  '批阅技能与素材/06-文字作业与试卷/离散数学证明题批阅/'{技能入口,教师基准,交付包,历史版本,测试结果} \
  '批阅技能与素材/06-文字作业与试卷/日语日记批阅/'{技能入口,原始素材}
mv '通信原理-单元测试1' '批阅技能与素材/06-文字作业与试卷/通信原理单元测试/单元测试1'
mv '通信原理-单元测试2' '批阅技能与素材/06-文字作业与试卷/通信原理单元测试/单元测试2'
mv '通信原理-单元测试3' '批阅技能与素材/06-文字作业与试卷/通信原理单元测试/单元测试3'
mv 'skill_test_results' '批阅技能与素材/06-文字作业与试卷/通信原理单元测试/测试结果/'
mv '测试题2.docx' '批阅技能与素材/06-文字作业与试卷/通信原理单元测试/历史版本/根目录重复文件/'
mv '图片1.png' '批阅技能与素材/06-文字作业与试卷/通信原理单元测试/历史版本/根目录重复文件/'
mv '湖南工学院-离散数学-技能批阅测试' '批阅技能与素材/06-文字作业与试卷/离散数学证明题批阅/原始素材'
mv '湖南工学院-离散数学-技能批阅测试.zip' '批阅技能与素材/06-文字作业与试卷/离散数学证明题批阅/交付包/'
mv '离散数学批阅文档.docx' '批阅技能与素材/06-文字作业与试卷/离散数学证明题批阅/教师基准/'
mv '日语日记批阅' '批阅技能与素材/06-文字作业与试卷/日语日记批阅/原始素材/'
```

Expected: `测试题2.docx` 与新 `单元测试1/测试题2.docx` 的 SHA-256 仍相同；`图片1.png` 与新 `单元测试1/测试1-1.png` 的 SHA-256 仍相同。

- [ ] **Step 2: 移动法律诊所、中医、古代汉语、其他课程和大学物理资料**

Run:

```bash
mkdir -p \
  '批阅技能与素材/06-文字作业与试卷/法律诊所/'{技能入口,原始素材} \
  '批阅技能与素材/06-文字作业与试卷/中医诊断学/'{教师基准,原始素材,测试结果} \
  '批阅技能与素材/06-文字作业与试卷/古代汉语' \
  '批阅技能与素材/06-文字作业与试卷/其他课程文档素材' \
  '批阅技能与素材/06-文字作业与试卷/大学物理题库（技能待补）/教师基准' \
  '批阅技能与素材/06-文字作业与试卷/大学英语写作翻译/'{技能入口,交付包}
mv '批阅文档' '批阅技能与素材/06-文字作业与试卷/综合批阅文档'
ln -s '../../综合批阅文档/法律诊所' '批阅技能与素材/06-文字作业与试卷/法律诊所/原始素材/法律诊所'
mv '安徽中医药高等专科学校-中医药学' '批阅技能与素材/06-文字作业与试卷/中医诊断学/原始素材/'
mv '中医诊断学作业一.docx' '批阅技能与素材/06-文字作业与试卷/中医诊断学/教师基准/'
mv '古代汉语' '批阅技能与素材/06-文字作业与试卷/古代汉语/原始素材'
mv 'document' '批阅技能与素材/06-文字作业与试卷/其他课程文档素材/原始素材'
mv '题目含图完整版-3.docx' '批阅技能与素材/06-文字作业与试卷/大学物理题库（技能待补）/教师基准/'
```

`题目含图完整版-3.docx` 已通过 `python-docx` 确认是大学物理题库，放入已识别但无专用技能的项目，不放入未知目录。

Expected: 所有列出的源路径都能在目标分类中找到；没有文件被覆盖。

- [ ] **Step 3: 创建八个正式文档类技能入口**

Run:

```bash
ln -s '../../../../.qoder/skills/grade-communication-principles' '批阅技能与素材/06-文字作业与试卷/通信原理单元测试/技能入口/grade-communication-principles'
ln -s '../../../../.qoder/skills/grade-communication-principles-test-1' '批阅技能与素材/06-文字作业与试卷/通信原理单元测试/技能入口/grade-communication-principles-test-1'
ln -s '../../../../.qoder/skills/grade-communication-principles-test-2' '批阅技能与素材/06-文字作业与试卷/通信原理单元测试/技能入口/grade-communication-principles-test-2'
ln -s '../../../../.qoder/skills/grade-communication-principles-test-3' '批阅技能与素材/06-文字作业与试卷/通信原理单元测试/技能入口/grade-communication-principles-test-3'
ln -s '../../../../.qoder/skills/grade-discrete-math-proof-reasoning' '批阅技能与素材/06-文字作业与试卷/离散数学证明题批阅/技能入口/grade-discrete-math-proof-reasoning'
ln -s '../../../../.qoder/skills/grade-japanese-diary-portfolio' '批阅技能与素材/06-文字作业与试卷/日语日记批阅/技能入口/grade-japanese-diary-portfolio'
ln -s '../../../../.qoder/skills/grade-college-english-writing-translation' '批阅技能与素材/06-文字作业与试卷/大学英语写作翻译/技能入口/grade-college-english-writing-translation'
ln -s '../../../../.qoder/skills/grade-legal-clinic-negotiation' '批阅技能与素材/06-文字作业与试卷/法律诊所/技能入口/grade-legal-clinic-negotiation'
```

Expected: 八个相对符号链接目标都包含 `SKILL.md`。

- [ ] **Step 4: 建立运行输出和测试包交叉入口**

Run:

```bash
ln -s '../../../../test_bundles/grade-discrete-math-proof-reasoning' '批阅技能与素材/06-文字作业与试卷/离散数学证明题批阅/测试结果/grade-discrete-math-proof-reasoning'
ln -s '../../../../output/college_english_skill_delivery' '批阅技能与素材/06-文字作业与试卷/大学英语写作翻译/交付包/college_english_skill_delivery'
ln -s '../../../../output/doc' '批阅技能与素材/06-文字作业与试卷/中医诊断学/测试结果/output-doc'
mkdir -p '批阅技能与素材/02-图片识别与PPT/水生生物学藻类易混种辨认/测试结果'
ln -s '../../../../output/doc/水生生物学藻类图片辨认测试材料.docx' '批阅技能与素材/02-图片识别与PPT/水生生物学藻类易混种辨认/测试结果/output-doc-藻类测试材料.docx'
```

Expected: `output/` 和 `test_bundles/` 仍在根目录，所有交叉入口无断链。

---

### Task 7: 整理通用技能、生成总索引和迁移清单

**Files:**
- Move: `publish_assets/` -> `批阅技能与素材/07-通用技能与工具/自定义批阅技能生成器/交付包/`
- Link: `.agents/skills/create-custom-homework-review-skill` -> 分类项目的 `技能入口/`
- Modify: `批阅技能与素材/README.md`
- Modify: `批阅技能与素材/整理清单.tsv`

**Interfaces:**
- Consumes: Tasks 2–6 的实际目标路径和完成状态。
- Produces: 面向用户的唯一总入口和可回退迁移记录。

- [ ] **Step 1: 移动自定义技能发布包并建立技能入口**

Run:

```bash
mkdir -p '批阅技能与素材/07-通用技能与工具/自定义批阅技能生成器/'{技能入口,交付包}
mv 'publish_assets' '批阅技能与素材/07-通用技能与工具/自定义批阅技能生成器/交付包/'
ln -s '../../../../.agents/skills/create-custom-homework-review-skill' '批阅技能与素材/07-通用技能与工具/自定义批阅技能生成器/技能入口/create-custom-homework-review-skill'
```

Expected: 技能入口和发布 ZIP 均可访问；`.agents/skills` 原路径未移动。

- [ ] **Step 2: 使用 apply_patch 编写总索引**

使用 `apply_patch` 创建 `README.md`。文档必须包含七类用途说明、20 个正式技能的完整映射表、外语发音与自定义技能两个独立入口、实验报告/燃烧学/中医/古代汉语/大学物理的“技能待补”状态、`output/` 与 `test_bundles/` 保留说明，以及燃烧学和舞蹈旧路径兼容链接说明。

正式技能映射表必须逐项列出：

```text
grade-action-video-comparison
grade-aquatic-algae-confusable-species
grade-college-english-writing-translation
grade-communication-principles
grade-communication-principles-test-1
grade-communication-principles-test-2
grade-communication-principles-test-3
grade-digital-logic-four-questions
grade-discrete-math-proof-reasoning
grade-english-debate-mun
grade-english-speech-presentation
grade-hailuo-bijian-eco-dubbing-subtitles
grade-japanese-diary-portfolio
grade-jimeng-image-to-video-heavy-equipment
grade-jimeng-text-to-video-homework
grade-legal-clinic-negotiation
grade-low-carbon-ai-voiceover
grade-music-performance
grade-surgical-gown-glove-video
grade-waveform-homework
```

Expected: 20 个正式 Qoder 技能名称在 README 中各出现一次；外语发音和自定义技能作为独立入口单列。

- [ ] **Step 3: 完成迁移清单**

使用 `apply_patch` 为 Tasks 3–7 的每个移动和链接追加 TSV 记录。对运行目录链接使用 `链接`，对素材目录使用 `移动`，对兼容入口使用 `兼容链接`。

Expected: 所有实际执行操作均有一行记录，状态均为 `完成`；未执行的候选项不得写成完成。

---

### Task 8: 全量核验和清理本次临时文件

**Files:**
- Verify: `批阅技能与素材/README.md`
- Verify: `批阅技能与素材/整理清单.tsv`
- Remove only agent-created temp: `tmp/docs/root-docx-inspection/`

**Interfaces:**
- Consumes: Tasks 1–7 的最终目录。
- Produces: 无断链、技能数量不变、迁移记录完整的分类结果。

- [ ] **Step 1: 核对正式技能数量未变**

Run:

```bash
find .qoder/skills -mindepth 2 -maxdepth 2 -type f -name SKILL.md | sort > /tmp/homework-review-skills-after.txt
diff -u /tmp/homework-review-skills-before.txt /tmp/homework-review-skills-after.txt
test "$(wc -l < /tmp/homework-review-skills-after.txt | tr -d ' ')" = "20"
```

Expected: `diff` 无输出，数量为 `20`。

- [ ] **Step 2: 检查所有分类符号链接**

Run:

```bash
find '批阅技能与素材' -type l -print0 | while IFS= read -r -d '' link; do
  test -e "$link" || printf 'BROKEN\t%s\n' "$link"
done
```

Expected: 无 `BROKEN` 输出。

- [ ] **Step 3: 检查关键兼容路径和分类目录**

Run:

```bash
test -d '燃烧学-西安交通大学-作业批阅/作业批阅智能体-燃烧学'
test -f '舞蹈动作批阅/测试输入-作业要求/标准视频/16.阻力带的旁吸腿练习.mp4'
test -f '批阅技能与素材/04-视频与动作/皖南医科大学-外科手术学/1.穿手术衣-视频批阅/老师操作视频.mp4'
test -f '批阅技能与素材/02-图片识别与PPT/水生生物学藻类易混种辨认/水生生物学-浮游植物易混种总结.pptx'
```

Expected: 四项检查全部通过。

- [ ] **Step 4: 检查根目录剩余素材并更新待确认清单**

Run:

```bash
find . -mindepth 1 -maxdepth 1 \
  \( -type f -o -type d -o -type l \) \
  -not -name '批阅技能与素材' \
  -not -name '.qoder' -not -name '.agents' -not -name '.tmp' \
  -not -name 'tmp' -not -name 'output' -not -name 'test_bundles' \
  -not -name 'test' -not -name 'utils' -not -name 'configs' \
  -not -name 'docs' -not -name '__pycache__' \
  -not -name '*.py' -not -name '*.mjs' -not -name '*.md' \
  -not -name '.env' -not -name '.env.example' -not -name '.DS_Store' \
  -print | sort
```

Expected: 只允许输出两个已记录的兼容符号链接；其他输出必须写入 `99-待确认/README.md` 后再结束任务。

- [ ] **Step 5: 清理本次只读识别产生的临时文件**

Run:

```bash
rm -rf 'tmp/docs/root-docx-inspection'
```

Expected: 只删除本次创建的检查目录，不删除其他 `tmp/` 内容。

- [ ] **Step 6: 最终 Git 边界检查**

Run:

```bash
git status --short
git diff --check
```

Expected: 不存在由本任务造成的代码修改；大体积媒体未被暂存，现有用户改动保持不变。
