# 财经新闻课程学习简报

仅在 normalizer 返回 `status: ready` 时展示以下模板。`items` 为空时不得填充占位新闻。

```markdown
## {{edition_id}}｜{{course.course_name}} 财经新闻课程学习简报

检索时间：{{retrieved_at}}
说明：财经内容仅用于课程学习，不构成投资建议。

### {{item.item_id}}｜{{item.title}}

**新闻事实**

{{item.fact_summary}}

来源：{{item.source}}（{{item.url}}）
发布时间：{{item.published_at}}

**课程依据**

- 课程：{{citation.course_name}}
- 知识点：{{citation.knowledge_point}}
- 学习资源：{{citation.resource_title}}
- 原文摘录：{{citation.excerpt}}

**理论分析**

{{item.theory_analysis}}

**讨论问题**

{{item.discussion_question}}
```

若 `status: skipped_no_course_evidence`，输出以下简短状态，不展示新闻观点或通用理论分析：

```markdown
## {{edition_id}}｜本期暂不生成课程点评

未取得所选课程的充分课程证据，已跳过本期新闻的课程点评（skipped_no_course_evidence）。请在课程教学计划或学习资源可检索后再试。
```

若 `status: no_eligible_candidates`，如实说明该时间窗没有同时满足公开来源、时间窗和课程证据要求的候选。所有状态都不得出现买卖建议、目标价、收益承诺或交易操作。
