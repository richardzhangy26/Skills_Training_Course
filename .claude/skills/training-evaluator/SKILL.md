---
name: training-evaluator
description: 对能力训练智能体的教学对话做批量 LLM 评测，输入教师文档 + 对话日志（单文件或目录），输出 5 维度 × 21 子维度的 JSON 报告并渲染 ASCII 汇总表。触发场景：用户要求"评测/评分/打分"一份或一批对话日志；用户提供教师文档路径 + 对话日志路径并要评估智能体表现；用户希望对比多档位（good/medium/bad）学生的对话质量；用户要跑评测稳定性实验（多次跑同一对话取均值）。关键词：评测、评分、打分、evaluation、教学质量、对话评估、目标达成度、流程遵循度、交互体验性、幻觉与边界、教学策略、一票否决、批量评估。
---

# Training Evaluator

## Purpose

对能力训练类智能体（Polymas 平台）的对话日志做自动化 LLM 评测。基于 `skill_training_evaluation/` 仓库内核，封装为单命令入口：

- 输入两个路径（教师文档 + 对话日志），可为文件或目录
- 支持多档位（good/medium/bad）+ 多次重复评测
- 并发调用 LLM（默认 4）
- 评测完成后直接打印 ASCII 汇总表

## When to Use

当用户说以下话时应当触发此 skill：

- "帮我评测一下这份对话" / "给这些对话打分" / "evaluate this dialogue"
- "跑一下 `<路径>` 的评测" / "批量评测某课程的所有对话"
- "对比 good/medium 档位的表现"
- "重跑 N 次看评分稳定性"
- 出现 `*_dialogue.json` / `*_dialogue.txt` + 教师文档 `.md` / `.docx` 的组合

## Quick Start

统一通过 `scripts/run.py` 调用。两个路径**必须同为文件**或**同为目录**（不支持混合）。

### 单文件评测

```bash
python <skill>/scripts/run.py \
    --teacher '<教师文档 .md/.docx>' \
    --dialogue '<对话日志 .json/.txt>'
```

### 批量目录评测（并发 4）

```bash
python <skill>/scripts/run.py \
    --teacher '<教师文档目录>' \
    --dialogue '<对话日志目录>' \
    --concurrency 4
```

### 多次重复评测（观测稳定性）

```bash
python <skill>/scripts/run.py \
    --teacher '<...>' \
    --dialogue '<...>' \
    --runs 3 \
    --concurrency 4
```

## Directory Matching (目录模式)

批量模式下目录结构必须是：

```
<教师文档目录>/
    任务名A.md       ← 或 .docx
    任务名B.md
    ...

<对话日志目录>/
    任务名A/<任意嵌套>/*_dialogue.json    ← 按第一级子目录名匹配教师文档
    任务名A/good/task_xxx_dialogue.json
    任务名B/对话流程模拟_good/good/task_xxx_dialogue.txt
    ...
```

核心规则：
- 递归搜索 `dialogue` 目录下所有 `*_dialogue.{json,txt}`
- 用**第一级子目录名**作为任务名去 teacher 目录里找同名 `.md`/`.docx`/`.txt`
- 第一级之后的所有嵌套目录拼成 `label`（标识档位/运行批次）

## Output Files

每次评测产生 2 个文件，落在**对话日志同目录**：

| 文件 | 内容 |
|---|---|
| `<前缀>_evaluation.json`（或 `_evaluation_run{i}.json`） | 结构化评测报告：总分、5 维度、21 子维度、问题引用、改进建议 |
| `<前缀>_evaluation.log` | main.py 子进程 stdout（LLM 调用详情） |

## ASCII Summary Table

脚本跑完自动打印，也可单独调：

```bash
python <skill>/scripts/ascii_report.py <report.json ...>
python <skill>/scripts/ascii_report.py <含若干评测报告的目录>
```

输出样式：

```
==============================================================================
任务                  档位/run      总分     等级          目标    流程    交互    幻觉    教学
==============================================================================
低碳钢压缩试验        good          94.0     优秀          20/20  20/20  14/20  20/20  20/20
低碳钢压缩试验        medium        96.0     优秀          18/20  20/20  18/20  20/20  20/20
------------------------------------------------------------------------------
梁弯曲正应力测定      good          86.0    一票否决       10/20⚠ 20/20  16/20  20/20  20/20
梁弯曲正应力测定      medium        96.0     优秀          20/20  20/20  16/20  20/20  20/20
==============================================================================

### ⚠ 一票否决
  ▸ 梁弯曲/good: 目标达成度得分10.0分，低于12分阈值
### 🐛 子维度解析/评估失败
  ▸ 压缩/good → 交互体验性/解析失败: JSON 解析失败: Expecting ',' delimiter ...
```

多次运行时额外输出"稳定性"段（N≥2 的对话显示均值/最低/最高/极差）。

## Arguments

| 参数 | 说明 | 默认 |
|---|---|---|
| `--teacher` | 教师文档单文件 或 课程目录 | 必填 |
| `--dialogue` | 对话日志单文件 或 课程目录 | 必填 |
| `--runs N` | 每个对话重复评测 N 次（产出 `_run1.json`..`_runN.json`） | 1 |
| `--concurrency K` | 并发子进程数（每次调用会串行 21 次 LLM，所以 K 越大越耗内存） | 4 |
| `--eval-dir` | `skill_training_evaluation` 目录路径（一般自动解析） | `/Users/zhangyichi/工作/能力训练/skill_training_evaluation` |
| `--no-report` | 跑完不打印 ASCII 汇总表 | False |

## Execution Notes

1. **评测内核依赖** — skill 复用 `skill_training_evaluation/main.py`；若移动了该目录需传 `--eval-dir` 或设 `TRAINING_EVAL_DIR` 环境变量
2. **.env 配置** — `main.py` 自动读取 `skill_training_evaluation/.env`（需包含 `LLM_API_KEY` / `LLM_API_URL` / `LLM_MODEL`）
3. **单评测耗时** — 一个对话评测 = 21 次 LLM 调用 × 10~60s = 约 5~15 分钟
4. **一票否决机制** — `目标达成度 < 12` 分会触发，即使其他维度全满也判"否决"
5. **解析保底** — 底层 `evaluator.py` 已对 LLM JSON 解析失败加了保底：不会让 `full_score=0` 污染维度总分；解析失败的子维度 `rating=解析失败`

## Decision Tree

```
用户要评测对话？
├─ 单个对话 + 单个文档          → run.py 单文件模式
├─ 整课程批量评测               → run.py 目录模式 --concurrency 4
├─ 跑多次看分数稳定性            → run.py 目录/单文件 + --runs N
└─ 已有 evaluation.json 要重新看报告 → ascii_report.py 直接渲染
```

## Resources

- `scripts/run.py` — launcher，解析输入 + 并发起 main.py 子进程 + 调用 ascii_report
- `scripts/ascii_report.py` — ASCII 汇总表渲染，可单独 CLI 使用
- `references/architecture.md` — 评测架构/prompts.json 结构/维度元数据速查
