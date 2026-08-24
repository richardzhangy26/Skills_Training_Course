# 财经新闻学习简报

只读取 normalizer 输出。仅在 `status: ready` 时展示条目；`items` 为空时不填充占位新闻。

```markdown
## {{edition_id}}｜财经新闻学习简报

检索时间：{{retrieved_at}}
状态来源：{{status_origin}}
说明：内容仅用于财经学习，不构成投资建议。

### {{item.item_id}}｜{{item.title}}

**新闻事实**

{{item.fact_summary}}

来源：{{item.source}}（{{item.url}}）
发布时间：{{item.published_at}}

**财经知识分析**

{{item.theory_analysis}}

**互动问题**

{{item.discussion_question}}
```

若 `status: no_eligible_candidates`：

```markdown
## {{edition_id}}｜本期没有合格候选

检索时间：{{retrieved_at}}
状态来源：{{status_origin}}
当前时间窗没有同时满足公开来源、时效和安全要求的财经新闻候选。
```

所有状态都不得出现买卖建议、目标价、收益承诺、仓位或交易操作。
