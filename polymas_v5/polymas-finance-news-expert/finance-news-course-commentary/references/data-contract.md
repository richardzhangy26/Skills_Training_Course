# 数据契约

本文件是 `finance-news-course-commentary` 的唯一字段契约。调用方在进入本 Skill 前已经确定一名学生和一门可访问课程；Skill 本身不持久化这些身份信息。

## 输入

normalizer 的输入为一个 JSON 对象：

```json
{
  "course": {
    "course_id": "课程标识",
    "course_name": "课程名称"
  },
  "retrieved_at": "2026-08-22T01:02:03+08:00",
  "course_evidence_available": true,
  "candidates": []
}
```

顶层字段均为 normalizer 输入：

| 字段 | 约束 |
|---|---|
| `course` | 必须同时含非空 `course_id` 和 `course_name`；输出只输出 `course_id` 和 `course_name`，其他课程元数据不回显 |
| `retrieved_at` | 必填，带时区的 ISO8601 检索时间；必须在公开网检索开始时记录，不能用新闻发布时间替代 |
| `course_evidence_available` | 必填布尔值；仅当学生教学计划/学习资源能提供所选课程的可核验知识点和摘录时为 `true` |
| `candidates` | 数组；即使 `course_evidence_available` 为 `false` 也必须提供（通常为空数组） |

`course` 必须精确提供 `course_id` 和 `course_name`。每个 `candidates` 元素必须包含：

| 字段 | 约束 |
|---|---|
| `title` | 新闻标题，非空字符串 |
| `url` | 可公开访问的 `http` 或 `https` URL |
| `source` | 调用方的来源名称仅供输入追踪；normalizer 忽略输入 `source`，输出 hostname 映射的 canonical source label |
| `source_tier` | 必填；`source_tier` 只是调用方断言，normalizer 必须与 hostname 推导等级比对 |
| `published_at` | 带时区的 ISO8601 发布时间 |
| `fact_summary` | 与来源可核对的事实摘要 |
| `theory_analysis` | 基于已取得课程依据的学习分析，不含投资建议；只能在 citations 完整后、normalizer 前生成 |
| `discussion_question` | 供学生讨论的开放问题，不引导交易；只能在 citations 完整后、normalizer 前生成 |
| `theory_citations` | 非空数组，每项见下表 |

每条 `theory_citations` 必须同时包含非空的 `course_id`、`course_name`、`knowledge_point`、`resource_title`、`excerpt`。数组中每一条 citation 的 `course_id` 与 `course_name` 都必须等于所选课程；任一条混入其他课程即整个候选 `course_mismatch`，按无课程证据处理。

## 资源上限

- 输入文件最大 1 MiB，`candidates` 最多 100 条，每条 `theory_citations` 最多 10 条。
- `title`/`source` 最长 300 字符；`fact_summary`/`theory_analysis`/`discussion_question` 各最长 4000 字符；`excerpt` 最长 2000 字符。
- 超限、过深 JSON、解码、`RecursionError` 或 `MemoryError` 均返回单一 stdout JSON 错误且非零退出；字符串扫描使用有界迭代遍历。

### `source_tier` 枚举与断言

`source_tier` 只是调用方断言。normalizer 不依据它授信，而是用 hostname allowlist 推导实际等级并要求两者一致：

| `source_tier` 允许值 | hostname 必须推导为 | 含义 |
|---|---:|---|
| `official`、`primary`、`regulator`、`government`、`exchange`、`company_announcement` | 1 | 官方/一级来源 |
| `authoritative_media`、`media` | 2 | 权威财经媒体/二级来源 |
| `other` | 不适用 | 三级公开线索；不查 hostname 一致性，直接 `untrusted_source` |

`source_level` 是输出，不是调用方输入。调用方不得以 `source_level` 替代 `source_tier`，也不得根据来源名称自行写入输出等级。

输出 `source` 同样不信任输入文字；它由命中的 allowlist 根域映射为 canonical source label。例如 `news.cn` 始终输出“新华网”，即使输入 `source` 声称“中国人民银行”也不回显该伪造名称。

hostname 的 `source_level` 和 canonical source label 只维护在单一 `SOURCE_REGISTRY` 中，子域名同时匹配多个根域时使用最长/最具体的注册项。`source_tier == other` 时无论 hostname 是否命中 registry，都优先返回 `untrusted_source`，不返回 `source_tier_mismatch`。

URL path 会将 percent-encoded unreserved 字符（如 `%7E`）还原为字面值，reserved 字符（如 `%2F`）保持编码并规范化十六进制大写。

URL 查询参数名 casefold 后若为 `token`、`access_token`、`authorization`、`api_key`、`apikey`、`secret`、`password`、`passwd`、`cookie`、`session`、`sessionid`、`jwt`、`credential`、`signature`、`sig` 或 `x-api-key`，整个候选返回 `sensitive_url_parameter`。不得通过删除参数后放行，`rejected` 不回显 URL 或参数值。

投资建议检测对所有将输出的字符串和键值执行 Unicode `NFKC` + casefold，删除零宽、空白和标点后，匹配直接禁语及“建议/推荐/应该/可考虑/维持/评级/看多看空”等提示词与“持有/增持/减持/做多/做空/申购/赎回/认购/持仓/入离场/仓位/配置/调换仓/满空仓/buy/sell/hold/long/short/subscribe/redeem/position/portfolio allocation”等动作词组合。“增持评级”、`overweight` 等直接禁语不需额外提示词即拒绝。

`retrieved_at` 属于 normalizer 的输入或输出字段：它作为顶层必填输入，经 ISO8601 解析并规范化后回传到输出。调用方在公开网检索开始时写入该值；展示模板只读取 normalizer 输出中的 `retrieved_at`。

## normalizer 调用与输出

```bash
python3 scripts/normalize_candidates.py \
  --input candidates.json \
  --since 2026-08-22T00:00:00+08:00 \
  --until 2026-08-22T23:59:59+08:00 \
  --edition-date 2026-08-22 \
  --max-items 3
```

stdout 只输出一个 JSON 对象；成功对象包含 `status`、`status_origin`、`edition_id`、`course`、`retrieved_at`、`course_evidence_available`、`items`、`rejected`。`items` 是可以展示的候选，每项保留允许字段、`source_level` 与 `item_id`。`rejected` 每项严格为 `{candidate_index, reason}`，不回显标题、URL 或正文。

| `status` | 含义与后续动作 |
|---|---|
| `ready` | `status_origin: normalizer`；使用 `items` 生成简报 |
| `no_eligible_candidates` | `status_origin: normalizer`；如实报告本期没有合格公开候选 |
| `skipped_no_course_evidence` | 不生成通用点评；见下列唯一状态来源 |

| 条件 | `status` | `status_origin` |
|---|---|---|
| `course_evidence_available: false` | `skipped_no_course_evidence` | `precheck` |
| 所有候选均因 `missing_course_evidence` 或 `course_mismatch` 被拒绝 | `skipped_no_course_evidence` | `candidate_filter` |
| 其他路径 | 由 normalizer 正常判定 | `normalizer` |

所有路径都必须调用 normalizer。调用方不得直接构造状态或 `status_origin`；前置证据不可用时，仍传入 `course_evidence_available: false` 及 `candidates` 数组，由 normalizer 返回 `precheck`。

`edition_id` 为 `FYYYYMMDD`。每个入选条目的 `item_id` 由排名后的位置确定，格式为 `FYYYYMMDD-01`、`FYYYYMMDD-02`、`FYYYYMMDD-03`；同一输入、时间窗、日期和上限必须得到相同 ID。不得自行改写 normalizer 的排序、去重或拒绝原因。

normalizer 强制拒绝三级来源：`source_tier == other` 的候选在 hostname registry 判定前即进入 `rejected`，原因固定为 `untrusted_source`，不生成 `source_level`也不得出现在 `items`。其余通过候选中，一级来源优先于二级来源，再由发布时间、标题和 URL 作确定性排序。

## 与订阅工作流的边界

订阅记录由专家维护。一份订阅只绑定一名学生和一门课程，其稳定任务键为 `finance-news:{schoolId}:{userId}:{courseId}`，不得包含会话 ID。`target_session_id` 是投递前重新校验的目标，不是任务键的一部分。Skill 不创建或保存上述记录，也不使用真实学生 ID、会话 ID、Cookie 或 Token。

## 展示映射

`items` 的 `fact_summary` 映射到新闻事实；`theory_citations` 映射到课程依据；`theory_analysis` 映射到理论分析；`discussion_question` 映射到讨论问题。不得在任何映射中删除来源 URL、发布时间或课程原文摘录。
