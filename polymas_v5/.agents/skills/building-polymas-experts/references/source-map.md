# 资料地图

按任务读，不要整份预加载。路径相对 `polymas_v5/` 仓库根。

## 每次必读

| 任务 | 入口 | 读到什么停 |
|---|---|---|
| 分层、模板、红线 | `AGENTS.md` | 专家创建流程 + Agent.md 模板 + Skill 契约 |
| 原子候选 | `docs/atomic-skill-catalog.json` | 命中条目的 `name` / `source_refs` / `nid` / `version` / `classification` / `verification_flags` |
| 目录说明 | `docs/atomic-skill-catalog.md` | 文首规则 + 检索类/课程类索引 + conflicts |
| 顾问需求 | `ai翻转/顾问创建专家素材采集模板.md` | 「问→做→得到」、材料、真实问题 |

JSON 是目录权威数据；Markdown 是渲染视图。

## 表里没有再打开 xlsx

目录 `sources[].sha256` 与当前 xlsx 不一致时，以 xlsx 该行原文为准，并在选型表注明「目录指纹过期，已回源」。

| 文件 | 何时打开 |
|---|---|
| `技能  - 专家整理.xlsx` | 专家规划、技能中文名、功能点、提测状态 |
| `技能一览表.xlsx` | V5 技能、生产映射、Agent 与 Skill 列表 |
| `技能一览表-V5技能.csv` | 只要 V5 切片、且 CSV 已覆盖该名称 |

重建目录（仅目录过期且需要批量检索时）：

```bash
python scripts/build_atomic_skill_catalog.py
```

不要为了「刷新线上状态」去跑它。本流程不把 PDS/SkillHub 当权威源。

## 平台 Skill 写法

需要写新平台 Skill，或核对官方 Skill 目录约定时，读 `Polymas Skill V5参考手册.md` 的结构与调用章节。不要把手册里的技能名抄进选型表；选型表只收 xlsx/目录里出现的名称。

## 样例 — 按模式读一份

| 模式 | 读这些 | 抽取 |
|---|---|---|
| 零新 Skill | `湖南师范大学-大学体育/大学体育资料检索专家/挂载与使用说明.md`、`Agent-完整配置.md` | 只复用「知识检索」；来源约束写在 Agent.md |
| 领域数据合同 | `ai翻转/data-law-case-expert/Agent.md` | 只读/维护拆 Skill；发布、上传、回读分状态 |
| 领域规划 + 已有检索 | `北京师范大学-分子生物学/Helix学术检索专家/PDS字段.md`、`挂载与使用说明.md` | 新建的是规划/核验，不是再写通用检索器 |
| 领域内容 + 内置调度 | `polymas-finance-news-expert/EXPERT_CONFIG.md` | 领域 Skill 与 `cron` / `ask_user_question` 分工 |
| 专家团设计 | `polymas-student-profile-expert-skills/EXPERT_GROUP_ASSEMBLY.md`、`SINGLE_EXPERT_CONFIG.md` | 专家数 ≠ Skill 数；交接和最终答复责任 |

样例规则不可提升为通用规则。财经「不选课点评」与 `AGENTS.md` 课程点评证据要求是不同产品边界，须 grilling 选定，不可静默混用。

## 内置工具

`ask_user_question`、`cron`、文件工具不是可挂载 Skill。它们写进 Agent.md 工作流，不写进挂载清单。
