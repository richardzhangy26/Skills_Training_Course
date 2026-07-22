# training-pro-script-generator 设计文档

**日期**: 2026-07-22
**状态**: 已确认（方案 B）

## 目标

新建 Claude Code skill `training-pro-script-generator`，将教师输入文档转化为"能力训练 Pro"格式的完整训练配置 Markdown。

Pro 版与普通能力训练的差异：
- 无连线机制，阶段跳转写在剧本提示词的【阶段结束判定】中
- 多角色：全局成员（AI 角色）需预先配置，每个成员可绑定多个技能（含 `<skill_instruction>` 指令）
- 一张阶段卡片内多个角色共同参与，平台规划器按剧本提示词拆解 subtask 调度各角色

## 职责边界

- **只生成 Markdown 配置文件**，不注入平台、不生成评价标准、不生成图片（封面/背景/头像仅输出文字描述）
- 注入平台由独立程序负责（`@成员名` 由注入程序在成员创建后转换为真实 nid）

## 目录结构

```
.claude/skills/training-pro-script-generator/
├── SKILL.md                      # 触发时机 + 工作流程 + 完整生成规则
└── references/
    └── example_guoshu_qitiao.md  # 平台真实任务反推的成品范例（few-shot）
```

## SKILL.md 内容

1. **frontmatter**: name / description（含触发关键词：能力训练 Pro、Pro 剧本、Pro 配置、多角色卡片等）/ allowed-tools: Read, Grep, Glob, Write
2. **与现有 skill 的区分**：`training-script-generator(-v2)`、`training-prompt-expert` 面向普通版（单角色/连线跳转），本 skill 面向 Pro 版（多角色 + 成员技能 + 提示词内跳转）
3. **工作流程**：
   1. Read 教师文档（用户 @ 的路径）
   2. Read `references/example_guoshu_qitiao.md` 作为格式范例
   3. 按核心生成规则输出完整配置
   4. 按"关键约束"清单自检（人工 checklist，无校验脚本）
   5. 写出文件
4. **核心生成规则**：用户提供的提示词**原样照搬**（5 维度阶段结构、@成员名 引用规则、阶段跳转规则、成员技能 `<skill_instruction>` 结构、16 条关键约束），仅将 `{teacherDoc}` 占位符改为"读取用户提供的文档"

## 范例制作

- 用 `.env` 凭证调用 4 个 Pro API（`steps/list`、`tasks/detail`、`skills/list`、`global-roles/list`，参数注意 `global-roles` 用 `trainTaskId`）拉取任务 `PROuNODZ41RAJttrEuzs`（果蔬气调与新型保鲜技术）真实配置
- 反推整理为符合输出格式的 Markdown 范例，`@成员名` 恢复为成员名格式（不含 nid）
- 凭证失效则先运行 `training-auto-login` skill 回填

## 输出约定

- 生成的配置写到教师文档同目录，命名 `<能力名称>-Pro配置.md`

## 不做的事

- 不生成评价标准（Pro 版不需要）
- 不调用 Doubao API 生成内容（Claude 直接生成）
- 不写格式校验脚本（用户确认现有提示词效果已验证，照搬即可）
