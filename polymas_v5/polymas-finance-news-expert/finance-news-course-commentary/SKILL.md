---
name: finance-news-course-commentary
description: Use when a student wants a recent public finance-news briefing tied to one selected course, with verifiable course evidence and no investment advice.
---

# 财经新闻课程点评

## 技能说明

将公开财经新闻转成一门已选课程的学习简报。核心原则是：新闻事实、课程依据、理论分析和讨论问题必须分栏；没有该课程可核验的证据，就不生成通用财经点评。所有路径都调用 normalizer，由它生成唯一的状态与状态来源；本 Skill 不管理订阅、定时任务或消息投递。

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

1. `[DETERMINE] 学生教学计划/学习资源`：读取已确认的单一课程、其教学计划和学习资源，提取可用于关联的课程名、知识点和原文摘录，并设置顶层布尔值 `course_evidence_available`。无论该值为真或假，都记录带时区的 `retrieved_at` 并构造 normalizer 输入；不得由调用方直接构造 `skipped_no_course_evidence`。
2. `[CALL] 平台通用工具公开网检索`：在 `course_evidence_available: true` 时，按课程主题和用户指定时间窗召回公开新闻，记录标题、URL、来源、发布时间、事实摘要和 `retrieved_at`；不使用付费墙内容或登录态。`source_tier` 只是调用方断言；normalizer 必须用内部 hostname allowlist 独立推导等级，调用方不能提升来源等级。输出 `source` 由 hostname allowlist 映射为固定机构名，不采信输入 `source`；不得传入 `source_level`。若为 false，不生成点评候选，但仍将空候选数组交给 normalizer。
3. `[CALL] 知识检索助手课程证据`：为每条候选检索同一门课程的 `course_id`、`course_name`、`knowledge_point`、`resource_title` 和 `excerpt`，并组装为 `theory_citations`。每条 citation 的 `course_id/course_name` 都必须同时等于所选课程；混合课程数组整条拒绝。只有取得完整且同课程的 citations 后，才能生成 `theory_analysis` 和 `discussion_question`。
4. `[BUILD] normalize_candidates.py`：按数据契约对候选进行强制校验与排序。它使用内部 hostname allowlist 推导 `source_level` 和 canonical source label，要求声明的 `source_tier` 与推导结果一致，强制拒绝三级、未列入、私网或 userinfo 来源。投资建议扫描先做 Unicode `NFKC`、casefold 并删除零宽/空白/标点，再检查直接禁语及提示词与动作词组合。`rejected` 只包含 `candidate_index` 和 `reason`。
5. `[BUILD] briefing`：将通过的条目按展示模板输出，保留来源 URL、发布时间、课程依据、理论分析和讨论问题；每期至多三条。

## 暂停确认规则

- 课程缺失或多个课程都可能匹配时，暂停等待学生选择，不自动选择。
- 需要改变订阅、推送时间、目标会话、发送范围或权限时，停止并交回专家；由专家按平台确认规则处理。
- 公开页面要求登录、验证码、付费或反爬验证时，停止使用该页面，改找可公开访问的独立来源；不得绕过。
- 仅剩无课程证据候选时，等待 normalizer 返回 `skipped_no_course_evidence`，不以常识补齐理论分析。

## 执行流程强制约束

- 一份简报只对应学生已选的一门课程；每条理论引用的 `course_id` 和 `course_name` 必须都与该课程一致。
- 严格执行“学生教学计划/学习资源 → 平台通用工具公开网检索 → 知识检索助手课程证据 → normalize_candidates.py → briefing”的顺序。`theory_analysis` 和 `discussion_question` 只能在 citations 完整后、normalizer 前生成。
- 公开来源按官方优先策略排序；其他公开页面只可帮助发现线索，不能在无独立可靠来源时支撑事实结论。normalizer 强制拒绝三级来源，返回 `untrusted_source`；调用方不得把脚本拒绝职责仅托付给提示词或人工判断。
- 平台通用工具返回候选后、normalizer 前，编排方必须按 `source-policy.md` 赋必填 `source_tier`；`source_level` 是 normalizer 输出，不能作为调用方输入。
- 所有路径都调用 normalizer：`course_evidence_available: false` 时返回 `skipped_no_course_evidence` / `precheck`；候选全部缺失或跨课程证据时返回同一状态 / `candidate_filter`；其他结果的状态来源为 `normalizer`。
- 不创建 Cron、不调用 channel-message、不保存订阅；也不更新发送历史或 `last_success_at`。
- 不输出投资建议、交易指令、目标价、收益承诺或投资组合建议。财经内容仅用于课程学习，不构成投资建议。
- 脚本 stdout 必须保持单个 JSON；脚本错误只能转述其 JSON `error`，不得伪造成功状态。
