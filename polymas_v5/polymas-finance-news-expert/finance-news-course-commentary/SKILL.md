---
name: finance-news-course-commentary
description: Use when a student wants a recent public finance-news briefing tied to one selected course, with verifiable course evidence and no investment advice.
---

# 财经新闻课程点评

## 技能说明

将公开财经新闻转成一门已选课程的学习简报。核心原则是：新闻事实、课程依据、理论分析和讨论问题必须分栏；没有该课程可核验的证据，就不生成通用财经点评。本 Skill 只生成和校验简报，不管理订阅、定时任务或消息投递。

## 触发/不触发

触发：学生已选定一门本人可访问的课程，且需要把近期公开财经新闻用于课程学习、复盘或讨论。

不触发：

- 选课、创建或修改订阅、暂停/恢复/退订、创建 Cron、发送消息，交由专家编排和内置工具处理。
- 用户要求买入、卖出、目标价、收益承诺、投资组合或交易操作。
- 没有明确课程，或无法取得课程知识点/学习资源证据。

若课程未唯一确定，暂停并要求调用方通过 `ask_user_question` 让学生选择；不得猜测课程，也不得跨课程复用证据。

## 项目结构

```text
finance-news-course-commentary/
├── SKILL.md
├── references/
│   ├── data-contract.md
│   └── source-policy.md
├── output_format/
│   └── briefing.md
└── scripts/
    └── normalize_candidates.py
```

数据字段、状态和 normalizer CLI 以 `references/data-contract.md` 为唯一契约；来源筛选以 `references/source-policy.md` 为准；用户可见输出使用 `output_format/briefing.md`。

## 执行流程

1. `[DETERMINE] 学生教学计划/学习资源`：读取已确认的单一课程、其教学计划和学习资源，提取可用于关联的课程名、知识点和原文摘录。前置课程证据查询为空时，直接输出 `skipped_no_course_evidence`，不进入公开网检索或 normalizer；这与“有新闻候选但均缺证据”的 normalizer 状态分开处理。课程证据可用但单条候选不足时，只保留有证据的候选。
2. `[CALL] 平台通用工具公开网检索`：按课程主题和用户指定时间窗召回公开新闻；先依据三级来源策略选取候选，记录标题、URL、来源、发布时间和事实摘要，不使用付费墙内容或登录态。
3. `[CALL] 知识检索助手课程证据`：为每条候选检索同一门课程的 `course_name`、`knowledge_point`、`resource_title` 和 `excerpt`。找不到完整证据的候选不得补写为通用理论点评。
4. `[BUILD] normalize_candidates.py`：按数据契约运行 normalizer，校验时间窗、URL、来源优先级、重复新闻、课程证据与投资建议边界；仅使用其 JSON 输出中的 `items`。
5. `[BUILD] briefing`：将通过的条目按展示模板输出，保留来源 URL、发布时间、课程依据、理论分析和讨论问题；每期至多三条。

## 暂停确认规则

- 课程缺失或多个课程都可能匹配时，暂停等待学生选择，不自动选择。
- 需要改变订阅、推送时间、目标会话、发送范围或权限时，停止并交回专家；由专家按平台确认规则处理。
- 公开页面要求登录、验证码、付费或反爬验证时，停止使用该页面，改找可公开访问的独立来源；不得绕过。
- 仅剩无课程证据候选时，输出 `skipped_no_course_evidence`，不以常识补齐理论分析。

## 执行流程强制约束

- 一份简报只对应学生已选的一门课程；理论引用中的 `course_name` 必须与该课程一致。
- 严格执行“学生教学计划/学习资源 → 平台通用工具公开网检索 → 知识检索助手课程证据 → normalize_candidates.py → briefing”的顺序。
- 公开来源按官方优先策略排序；其他公开页面只可帮助发现线索，不能在无独立可靠来源时支撑事实结论。不得把三级来源传入 normalizer 作为可展示候选；normalizer 的来源等级只用于已通过来源策略候选的确定性排序。
- 不创建 Cron、不调用 channel-message、不保存订阅；也不更新发送历史或 `last_success_at`。
- 不输出投资建议、交易指令、目标价、收益承诺或投资组合建议。财经内容仅用于课程学习，不构成投资建议。
- 脚本 stdout 必须保持单个 JSON；脚本错误只能转述其 JSON `error`，不得伪造成功状态。
