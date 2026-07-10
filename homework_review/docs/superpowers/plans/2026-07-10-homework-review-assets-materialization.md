# 批阅技能与素材实体化调整实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将当前分类目录及根目录中的全部 32 个符号链接转换为实体文件或实体目录，恢复实验报告和燃烧学根目录，并删除旧实验报告分类。

**Architecture:** 对每个链接先解析真实来源，复制到同级临时路径并用 `diff -qr` 或 `cmp` 验证，再原位替换链接。随后恢复原 03 分类中的两个实体素材目录、连续重编号分类、把 `技能入口` 改名为 `技能副本`，最后重写索引和迁移清单。

**Tech Stack:** macOS/zsh、`realpath`、`ditto`、`cp -p`、`diff`、`cmp`、SHA-256、Markdown、TSV。

## Global Constraints

- 不修改 `.qoder/skills` 和 `.agents/skills` 中的正式技能原件。
- 不删除课程素材；只删除本次整理生成的两个项目 README 和系统 `.DS_Store`。
- 不覆盖既有实体目标；临时复制验证成功后才能执行 `unlink`。
- `实验报告批阅智能体`和`燃烧学-西安交通大学-作业批阅`恢复为根目录实体目录。
- `舞蹈动作批阅`根目录改为实体副本。
- 最终分类连续编号为 `01` 至 `06`，另有 `99-待确认`。
- 最终分类目录和根目录均不得存在符号链接。
- 用户已有 `AGENTS.md`、`homework_reviewer_v2.py` 等未提交修改不在本任务范围内。

---

### Task 1: 建立链接和复制基线

**Files:**
- Read: `批阅技能与素材/`
- Read: `.qoder/skills/`
- Create temporary inventory: `/tmp/homework-review-links-before.txt`

**Interfaces:**
- Consumes: 当前 30 个分类链接和 2 个根目录链接。
- Produces: Task 2 用于逐项实体化的完整链接清单。

- [ ] **Step 1: 记录全部链接和正式技能基线**

Run:

```bash
find '批阅技能与素材' -type l -print | sort > /tmp/homework-review-catalog-links-before.txt
find . -mindepth 1 -maxdepth 1 -type l -print | sort > /tmp/homework-review-root-links-before.txt
cat /tmp/homework-review-catalog-links-before.txt /tmp/homework-review-root-links-before.txt > /tmp/homework-review-links-before.txt
test "$(wc -l < /tmp/homework-review-catalog-links-before.txt | tr -d ' ')" = '30'
test "$(wc -l < /tmp/homework-review-root-links-before.txt | tr -d ' ')" = '2'
find .qoder/skills -mindepth 2 -maxdepth 2 -type f -name SKILL.md | sort > /tmp/homework-review-skills-materialize-before.txt
test "$(wc -l < /tmp/homework-review-skills-materialize-before.txt | tr -d ' ')" = '20'
```

Expected: 分类链接 30 个、根目录链接 2 个、正式技能 20 个。

- [ ] **Step 2: 检查可用空间和复制源内部链接**

Run:

```bash
df -Pk . | awk 'NR==2 {exit !($4 > 1048576)}'
test "$(find .qoder/skills .agents/skills/create-custom-homework-review-skill output/doc output/college_english_skill_delivery test_bundles/grade-discrete-math-proof-reasoning test_bundles/english_speech_debate_review_test_bundle_20260702_143055 -type l | wc -l | tr -d ' ')" = '0'
```

Expected: 可用空间超过 1 GiB，所有主要复制源内部没有链接。

---

### Task 2: 把分类链接和舞蹈根目录链接转换为实体副本

**Files:**
- Replace: `批阅技能与素材/**` 下 30 个链接
- Replace: `舞蹈动作批阅`
- Preserve temporarily: `燃烧学-西安交通大学-作业批阅` 链接，留给 Task 3 原位恢复

**Interfaces:**
- Consumes: Task 1 的链接基线。
- Produces: 无链接的分类目录和根目录舞蹈实体副本。

- [ ] **Step 1: 定义并执行安全实体化函数**

Run:

```bash
materialize_link() {
  link="$1"
  test -L "$link"
  src=$(realpath "$link")
  tmp="${link}.materializing"
  test ! -e "$tmp"
  if test -d "$src"; then
    ditto "$src" "$tmp"
    diff -qr "$src" "$tmp" >/dev/null
  else
    cp -p "$src" "$tmp"
    cmp -s "$src" "$tmp"
  fi
  unlink "$link"
  mv "$tmp" "$link"
  test ! -L "$link"
}

while IFS= read -r link; do
  materialize_link "$link"
done < /tmp/homework-review-catalog-links-before.txt

materialize_link '舞蹈动作批阅'
```

Expected: 分类目录链接数量为 0；根目录只剩燃烧学一个链接。

- [ ] **Step 2: 验证实体化结果类型和技能副本数量**

Run:

```bash
test "$(find '批阅技能与素材' -type l | wc -l | tr -d ' ')" = '0'
test "$(find . -mindepth 1 -maxdepth 1 -type l | wc -l | tr -d ' ')" = '1'
test -d '舞蹈动作批阅'
test ! -L '舞蹈动作批阅'
test "$(find '批阅技能与素材' -path '*/技能入口/*/SKILL.md' -type f | wc -l | tr -d ' ')" = '22'
```

Expected: 20 个正式技能副本，加上外语发音和自定义技能，共 22 个实体 `SKILL.md`。

---

### Task 3: 恢复实验报告根目录并连续重编号

**Files:**
- Move: `批阅技能与素材/03-实验报告与综合文档/实验报告批阅智能体` -> `实验报告批阅智能体`
- Move: `批阅技能与素材/03-实验报告与综合文档/燃烧学-西安交通大学-作业批阅` -> `燃烧学-西安交通大学-作业批阅`
- Rename: `04-视频与动作` -> `03-视频与动作`
- Rename: `05-音频与口语` -> `04-音频与口语`
- Rename: `06-文字作业与试卷` -> `05-文字作业与试卷`
- Rename: `07-通用技能与工具` -> `06-通用技能与工具`
- Rename: all `技能入口` -> `技能副本`

**Interfaces:**
- Consumes: Task 2 的无链接分类目录。
- Produces: 根目录实体素材和连续编号分类。

- [ ] **Step 1: 删除仅由整理过程生成的两个项目 README**

使用 `apply_patch` 删除：

```text
批阅技能与素材/03-实验报告与综合文档/实验报告批阅智能体/README.md
批阅技能与素材/03-实验报告与综合文档/燃烧学-西安交通大学-作业批阅/README.md
```

Expected: 只删除这两个说明文件，其他素材文件数量不变。

- [ ] **Step 2: 恢复两个根目录实体素材目录**

Run:

```bash
test -L '燃烧学-西安交通大学-作业批阅'
unlink '燃烧学-西安交通大学-作业批阅'
mv '批阅技能与素材/03-实验报告与综合文档/燃烧学-西安交通大学-作业批阅' .
mv '批阅技能与素材/03-实验报告与综合文档/实验报告批阅智能体' .
test -d '燃烧学-西安交通大学-作业批阅'
test ! -L '燃烧学-西安交通大学-作业批阅'
test -d '实验报告批阅智能体'
```

Expected: 两个根目录均为实体目录，根目录链接数量为 0。

- [ ] **Step 3: 删除空旧分类并重编号**

Run:

```bash
rm -f '批阅技能与素材/03-实验报告与综合文档/.DS_Store'
rmdir '批阅技能与素材/03-实验报告与综合文档'
mv '批阅技能与素材/04-视频与动作' '批阅技能与素材/03-视频与动作'
mv '批阅技能与素材/05-音频与口语' '批阅技能与素材/04-音频与口语'
mv '批阅技能与素材/06-文字作业与试卷' '批阅技能与素材/05-文字作业与试卷'
mv '批阅技能与素材/07-通用技能与工具' '批阅技能与素材/06-通用技能与工具'
```

Expected: 分类目录为 01、02、03、04、05、06、99，旧实验报告分类不存在。

- [ ] **Step 4: 把所有技能目录改名为技能副本**

Run:

```bash
find '批阅技能与素材' -depth -type d -name '技能入口' -print0 | while IFS= read -r -d '' dir; do
  parent=$(dirname "$dir")
  test ! -e "$parent/技能副本"
  mv "$dir" "$parent/技能副本"
done
test "$(find '批阅技能与素材' -type d -name '技能入口' | wc -l | tr -d ' ')" = '0'
test "$(find '批阅技能与素材' -path '*/技能副本/*/SKILL.md' -type f | wc -l | tr -d ' ')" = '22'
```

Expected: 22 个实体技能副本均位于 `技能副本/`。

---

### Task 4: 更新总索引和迁移清单

**Files:**
- Modify: `批阅技能与素材/README.md`
- Modify: `批阅技能与素材/整理清单.tsv`

**Interfaces:**
- Consumes: Task 3 的最终目录路径。
- Produces: 不再描述链接实现的当前索引和可核验清单。

- [ ] **Step 1: 使用 apply_patch 更新 README**

README 必须明确写出以下当前状态：

```text
分类目录中的技能、教师基准、学生样例、测试结果和交付包均为实体文件或实体目录。
正式技能原件保留在 .qoder/skills，分类目录中的技能为快照副本。
分类为 01波形图、02图片、03视频、04音频、05文字、06通用、99待确认。
实验报告批阅智能体与燃烧学素材位于项目根目录，不属于本分类目录。
output 和 test_bundles 保留原位，匹配内容已复制进具体项目。
```

删除旧 README 中的实验报告分类、兼容入口和链接说明；把所有 `技能入口` 表述改为 `技能副本`。

Expected: README 中 20 个正式技能名称各出现一次，当前实现说明只使用“实体副本”。

- [ ] **Step 2: 机械更新迁移清单路径和动作**

按以下精确规则更新 `整理清单.tsv`：

```text
04-视频与动作 -> 03-视频与动作
05-音频与口语 -> 04-音频与口语
06-文字作业与试卷 -> 05-文字作业与试卷
07-通用技能与工具 -> 06-通用技能与工具
技能入口 -> 技能副本
动作“链接”或“兼容链接” -> “复制”
```

将实验报告、燃烧学和 doc_test 三行的目标改为根目录真实路径，动作改为 `恢复`；删除原燃烧学兼容链接的重复行。

Expected: TSV 每行 5 列，所有目标路径存在，不包含动作 `链接` 或 `兼容链接`。

---

### Task 5: 全量验收

**Files:**
- Verify: `批阅技能与素材/`
- Verify: `.qoder/skills/`
- Verify: root material directories

**Interfaces:**
- Consumes: Tasks 1–4 的最终结果。
- Produces: 零链接、连续编号、实体副本完整的验收证据。

- [ ] **Step 1: 验证零链接和连续分类**

Run:

```bash
test "$(find '批阅技能与素材' -type l | wc -l | tr -d ' ')" = '0'
test "$(find . -mindepth 1 -maxdepth 1 -type l | wc -l | tr -d ' ')" = '0'
test ! -e '批阅技能与素材/03-实验报告与综合文档'
find '批阅技能与素材' -mindepth 1 -maxdepth 1 -type d -exec basename {} \; | sort > /tmp/homework-review-final-categories.txt
printf '01-波形图与数字逻辑\n02-图片识别与PPT\n03-视频与动作\n04-音频与口语\n05-文字作业与试卷\n06-通用技能与工具\n99-待确认\n' | diff -u - /tmp/homework-review-final-categories.txt
```

Expected: 两处链接数量均为 0，分类清单完全一致。

- [ ] **Step 2: 验证正式技能原件和实体副本**

Run:

```bash
find .qoder/skills -mindepth 2 -maxdepth 2 -type f -name SKILL.md | sort > /tmp/homework-review-skills-materialize-after.txt
diff -u /tmp/homework-review-skills-materialize-before.txt /tmp/homework-review-skills-materialize-after.txt
test "$(wc -l < /tmp/homework-review-skills-materialize-after.txt | tr -d ' ')" = '20'
test "$(find '批阅技能与素材' -path '*/技能副本/grade-*/SKILL.md' -type f | wc -l | tr -d ' ')" = '20'
test "$(find '批阅技能与素材' -path '*/技能副本/*/SKILL.md' -type f | wc -l | tr -d ' ')" = '22'
```

Expected: 正式技能原件仍为 20，实体正式技能副本为 20，包含独立技能后共 22。

- [ ] **Step 3: 验证根目录实体素材和清单目标**

Run:

```bash
for dir in '实验报告批阅智能体' '燃烧学-西安交通大学-作业批阅' '舞蹈动作批阅'; do
  test -d "$dir"
  test ! -L "$dir"
done
awk -F '\t' 'NF != 5 {print "BAD_TSV", NR, NF; bad=1} END {exit bad}' '批阅技能与素材/整理清单.tsv'
tail -n +2 '批阅技能与素材/整理清单.tsv' | while IFS=$'\t' read -r src dst action reason row_status; do
  test "$row_status" = '完成'
  test -e "$dst"
  test "$action" != '链接'
  test "$action" != '兼容链接'
done
```

Expected: 三个根目录均为实体目录，清单全部目标存在且无链接动作。

- [ ] **Step 4: 最终结构和 Git 边界检查**

Run:

```bash
git diff --check
git status --short -- .
du -sh '批阅技能与素材' '实验报告批阅智能体' '燃烧学-西安交通大学-作业批阅' '舞蹈动作批阅'
```

Expected: 无空白错误；大体积素材未被 Git 暂存；用户已有代码修改保持原状。
