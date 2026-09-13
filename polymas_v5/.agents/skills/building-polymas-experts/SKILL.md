---
name: building-polymas-experts
description: Use when designing or revising a Polymas V5 expert, choosing official atomic skills from 技能一览表 / 专家整理 / atomic-skill-catalog, judging a domain Skill gap, planning an expert group, or preparing Agent.md. Use when tempted to invent a retrieval or knowledge-base Skill, guess skill names or versions, skip grilling on mount or boundary decisions, or treat local tests as online success.
---

# Building Polymas Experts

把「做一个专家」做成有来源的能力组合、有确认的设计决策、有证据的交付状态。

本 Skill 约束工程师侧 Agent（Grok / Claude / Codex）。它不上传到 PDS，不替代平台专家，也不替代官方原子 Skill。

**REQUIRED SUB-SKILL:** `grilling`。工程师决策走 grilling；平台师生确认写进 Agent.md 的 `ask_user_question`。两层不混用。

权威流程与 Agent.md 模板只读 `AGENTS.md`，这里不复制。

## 锁定决策

| 项 | 值 |
|---|---|
| 专家团 | 可做选型、角色、交接设计；完整验收先覆盖单专家 |
| 源码位置 | 本目录。不要复制到个人 skills 后再分叉修改 |
| 宿主验收 | 当前宿主测通即可，未测宿主标未验证 |
| 选型权威源 | `技能一览表.xlsx`、`技能  - 专家整理.xlsx`、`docs/atomic-skill-catalog.json`。xlsx 有的即可挂载进设计；不把 PDS/SkillHub 在线核验当交付阻断 |
| 官方冲突 | 缩小路径或报告冲突后停止该项。兼容副本是单独方案，须确认维护人、更新方式和验收成本 |

## 何时用 / 不用

用：新建或改专家、选挂载、判断要不要新平台 Skill、写 Agent.md / 开场白 / 联调清单、规划专家团。

不用：师生运行时问答、只改某个已有平台 Skill 的脚本、未获授权的上传/绑定/发消息。

## 三层

| 层 | 产物 | 确认 |
|---|---|---|
| 本 Skill | 选型表、决策记录、验收说明 | grilling |
| 平台 `Agent.md` | 身份、路由、红线 | 运行时 `ask_user_question` |
| 平台领域 Skill | 仅领域缺口 | 按平台契约 |

专家价值可以来自路由和来源约束。大学体育只挂「知识检索」、零新 Skill，就是完成。

## 工作流

每步有完成条件。未完成不得进入依赖它的步骤。事实自己查；决策才 grilling。

### 1. 定范围

读用户材料、已有 `Agent.md` / 挂载说明、`AGENTS.md`。

完成：写清本次是讨论、生成本地产物，还是另有上传授权。默认只到本地产物。

### 2. 整理需求

按 `ai翻转/顾问创建专家素材采集模板.md` 抽出：使用者、1–3 个「问→做→得到」、真实问题、材料来源、是否写入、验收任务。

完成：文件能回答的都已回答。缺业务取舍则进入 grilling，不编造用途。

读 `references/source-map.md`。

### 3. 查原子能力

按 `references/capability-selection.md` 检索目录和两份 xlsx。先检索类、课程读写类、文件解析类。

完成：一张选型表，每行含：需求点、候选名称（表中原文）、来源文件/工作表/行、角色范围、读写、冲突标记、nid/version（空就留空）。

表里没有的名称不许写入选型表。

### 4. grilling 边界

读 `references/engineer-decisions.md`。加载 grilling，问完当前 frontier 后真正等待。

当前宿主有 `ask_user_question` 就用它投递当轮问题；否则输出 grilling 格式并停止本轮。禁止写「请确认」后继续。

完成：本轮问题都有工程师原话。推荐答案 ≠ 已采纳。

### 5. 判定领域缺口

仅当已确认的输出合同无法由选型表中的原子能力完成时，才提案新平台 Skill。

下列情况保持复用，不新建：表里已有同职责检索/知识库能力；官方技能临时失败或版本空缺；权限描述冲突；想要的只是换提示词或改路由。

冲突按锁定决策处理：缩小到表中只读或单一功能点，或报告冲突并撤下该候选。

完成：书面结论为「零新 Skill」或「缺口 + 理由 + 对应需求点」。专家团只出设计，不把团执行引擎当本步交付。

### 6. 编排交付包

按 `references/acceptance.md` 产出。`AGENTS.md` 的模板变量名一字不改，例如 `${agent_name}`。

挂载顺序只用于配置管理，不是每轮调用顺序。运行时路由单独写：何种意图调用谁、何时 `ask_user_question`、失败如何交付。

完成：acceptance 清单每一项都有对应文件或段落。

### 7. 条件式新建平台 Skill

仅步骤 5 确认缺口且用户授权本地实现后才写平台 Skill。先无 Skill 基线，再最小实现。结构遵循 `AGENTS.md` 的 Skill 目录与契约。

本 Skill 自身不是平台 Skill，不要套 `scripts/base/`。

## 示例

需求：「帮《大学体育》做资料检索专家，找老师发的视频和课件。」

正确：选型表命中「知识检索」/`external-knowledge-search` → grilling 确认只定位资料、不训练计划 → 零新 Skill → Agent.md 把课程资料默认路由到该原子能力。

错误：新建 `pe-video-search`；把工作空间检索当视频入口；版本空缺时写成 `v1.0.0`；PDS 没打开就说「线上已核验」。

## 红旗 — 停下回到对应步骤

- 还没查表就开始写新检索/知识库 Skill
- 选型表出现表中不存在的技能名，或把空 nid/version 补成猜测值
- 普通文本「请确认」之后继续编排
- 把 grilling 写进平台 Agent.md，或把 `ask_user_question` 当工程师访谈
- 官方冲突时直接克隆兼容副本
- 本地对话跑通就写「已上线 / 知识已更新 / 消息已读」

| 借口 | 现实 |
|---|---|
| 表有点旧，先写一个更快 | 选型权威源就是 xlsx；缺失则记缺口，不发明原子 |
| 官方检索这次失败了 | 失败不是新建理由；记依赖问题 |
| 我已经在回复里问过了 | 未等待的确认不算确认 |
| 专家团更完整 | 完整验收先交单专家 |

未测宿主、未做的上传和联调，在交付里写成未验证，不省略。
