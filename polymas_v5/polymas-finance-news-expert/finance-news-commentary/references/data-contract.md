# 数据契约

本文件是 `finance-news-commentary` 的唯一字段契约。Skill 不接收课程、学生身份、会话或订阅字段。

## 输入

```json
{
  "retrieved_at": "2026-08-22T01:02:03+08:00",
  "candidates": []
}
```

| 字段 | 约束 |
|---|---|
| `retrieved_at` | 必填、带时区的 ISO8601 检索时间 |
| `candidates` | 必填数组，最多 100 条 |

每个候选必须包含：

| 字段 | 约束 |
|---|---|
| `title` | 新闻标题，非空字符串，最长 300 字符 |
| `url` | 可公开访问的 HTTP(S) URL，最长 4000 字符 |
| `source` | 输入追踪用；输出不采信该文字 |
| `source_tier` | 调用方来源等级断言 |
| `published_at` | 带时区的 ISO8601 发布时间 |
| `fact_summary` | 可由来源核对的事实摘要，最长 4000 字符 |
| `theory_analysis` | 明确标记的通用财经知识分析，最长 4000 字符 |
| `discussion_question` | 不引导交易的开放问题，最长 4000 字符 |

输入文件最大 1 MiB，JSON 最大深度 100、遍历节点最多 20000。超限或解析失败时 stdout 返回单个 `{"error":"..."}`，退出码非零。

## 来源与安全

`source_tier` 允许：

- `official`、`primary`、`regulator`、`government`、`exchange`、`company_announcement` → hostname 必须推导为一级来源；
- `authoritative_media`、`media` → hostname 必须推导为二级来源；
- `other` → 直接返回 `untrusted_source`。

`source_level` 和输出 `source` 由 normalizer 的单一 `SOURCE_REGISTRY` 按最长根域匹配生成。调用方不得传入或提升 `source_level`。

URL 会移除追踪参数、规范化 path 和默认端口。参数名经 NFKC、casefold 和重复 URL 解码后，只要包含 token、secret、credential、signature、authorization、password、cookie、JWT、access key、API key 或 session key 等敏感标记，整个候选返回 `sensitive_url_parameter`，且拒绝结果不回显原 URL。

所有输出字符串都执行投资建议扫描。明确交易命令、买卖建议、目标价、收益承诺、投资组合或仓位操作返回 `investment_advice_language`；教学或事实性术语不应因单纯出现“申购、持有、做多”等词而被误杀。

## normalizer 调用与输出

```bash
python3 scripts/normalize_candidates.py \
  --input candidates.json \
  --since 2026-08-22T00:00:00+08:00 \
  --until 2026-08-22T23:59:59+08:00 \
  --edition-date 2026-08-22 \
  --max-items 3
```

成功 stdout 字段：`status`、`status_origin`、`edition_id`、`retrieved_at`、`items`、`rejected`。

| `status` | 含义 |
|---|---|
| `ready` | `items` 含 1–3 条可展示新闻 |
| `no_eligible_candidates` | 时间窗内没有合格候选，不生成占位内容 |

`rejected` 每项严格为 `{candidate_index, reason}`。`edition_id` 为 `FYYYYMMDD`；`item_id` 为 `FYYYYMMDD-01` 至 `03`。一级来源优先于二级来源，再按发布时间、标题和 URL 确定性排序。

## 与订阅工作流的边界

订阅由专家维护。稳定任务键为 `finance-news:{schoolId}:{userId}:{agentId}`，不含课程或会话 ID。`target_session_id` 保存首次订阅时的当前专家个人会话；Skill 不创建、读取或修改这些字段。

## 展示映射

`fact_summary` 映射到新闻事实，`theory_analysis` 映射到财经知识分析，`discussion_question` 映射到互动问题。来源 URL、发布时间和检索时间必须保留。
