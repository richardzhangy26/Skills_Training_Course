---
name: finance-news-commentary
description: Use when a student asks for recent public finance news, a general finance explanation, or a discussion prompt without selecting a course.
---

# 财经新闻通用点评

## 技能说明

将公开财经新闻转成通用学习简报。新闻事实、财经知识分析和讨论问题分栏呈现；所有候选都先经过 normalizer。Skill 只负责新闻清洗与点评，不管理订阅、Cron 或消息投递。

## 触发/不触发

触发：学生需要近期公开财经新闻、通用财经知识解释或互动讨论，且不绑定课程。

不触发：选课、课程查询、订阅维护、Cron、发送消息、实时行情、估值、交易建议或投资组合操作。

## 项目结构

```text
finance-news-commentary/
├── SKILL.md
├── references/
│   ├── data-contract.md
│   └── source-policy.md
├── output_format/
│   └── briefing.md
└── scripts/
    └── normalize_candidates.py
```

数据字段与状态以 `references/data-contract.md` 为唯一契约；来源筛选以 `references/source-policy.md` 为准；用户可见格式使用 `output_format/briefing.md`。

## 执行流程

1. `[DETERMINE] 时间窗与主题`：读取学生已确认的财经主题、上次成功时间和本次执行时间；记录带时区的 `retrieved_at`。
2. `[CALL] 平台通用工具公开网检索`：按主题和时间窗召回公开新闻，记录标题、URL、来源、发布时间和事实摘要；优先官方来源，不使用付费墙或登录态。
3. `[FILTER] 事实核对`：同一事件聚类去重；来源冲突时保留可核验事实并标记不确定性，事实无法确认的候选不进入点评。
4. `[BUILD] 通用财经分析`：为候选生成简短 `theory_analysis` 和 `discussion_question`。分析只使用通用财经概念，明确标记为分析，不伪装成新闻事实；不确定时缩小结论或放弃候选。
5. `[BUILD] normalize_candidates.py`：强制校验来源、URL、时间窗、字段长度、投资建议禁语、排序、去重和最多三条限制。`rejected` 只含 `candidate_index` 与 `reason`，不回显原文或敏感 URL。
6. `[BUILD] briefing`：只展示 normalizer 返回的 `ready` 条目；无合格候选时如实输出 `no_eligible_candidates`。

## 暂停确认规则

- 页面要求登录、验证码、付费或反爬验证时，停止使用该页面并改找公开来源。
- 需要改变订阅、推送时间、目标会话或发送范围时，停止并交回专家编排。
- 事实来源冲突且无法确认时，不生成确定性结论。

## 执行流程强制约束

- 无需课程、课程 ID、课程资源或课程证据；不得调用课程相关 Skill。
- 严格执行“公开网检索 → 事实核对与去重 → 通用财经分析 → normalizer → briefing”。
- `source_tier` 是调用方断言；`source_level` 与 canonical source label 只能由 normalizer 的 `SOURCE_REGISTRY` 推导。
- URL 含凭证类查询参数时整个候选返回 `sensitive_url_parameter`，不通过删参后放行。
- 不创建 Cron、不调用 `channel-message`、不保存订阅，也不更新发送历史或 `last_success_at`。
- 不输出投资建议、交易指令、目标价、收益承诺或投资组合建议。内容仅用于财经学习，不构成投资建议。
- 脚本 stdout 始终为单个 JSON；错误只能转述其 JSON `error`，不得伪造成功状态。
