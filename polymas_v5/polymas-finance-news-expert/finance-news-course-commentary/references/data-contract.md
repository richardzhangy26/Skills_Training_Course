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
  "candidates": []
}
```

`course` 必须含可识别的课程名称。每个 `candidates` 元素必须包含：

| 字段 | 约束 |
|---|---|
| `title` | 新闻标题，非空字符串 |
| `url` | 可公开访问的 `http` 或 `https` URL |
| `source` | 来源名称 |
| `published_at` | 带时区的 ISO8601 发布时间 |
| `fact_summary` | 与来源可核对的事实摘要 |
| `theory_analysis` | 基于课程依据的学习分析，不含投资建议 |
| `discussion_question` | 供学生讨论的开放问题，不引导交易 |
| `theory_citations` | 非空数组，每项见下表 |

每条 `theory_citations` 必须同时包含非空的 `course_name`、`knowledge_point`、`resource_title`、`excerpt`。其中 `course_name` 必须等于所选课程；缺失、跨课程或不可核验都视为无课程证据。

`retrieved_at` 是简报运行上下文中必须保留的、带时区的 ISO8601 检索时间。它不属于 normalizer 的输入或输出字段，应由调用方在调用公开网检索时记录，并在展示模板中传入；不得以新闻发布时间替代。

## normalizer 调用与输出

```bash
python3 scripts/normalize_candidates.py \
  --input candidates.json \
  --since 2026-08-22T00:00:00+08:00 \
  --until 2026-08-22T23:59:59+08:00 \
  --edition-date 2026-08-22 \
  --max-items 3
```

stdout 只输出一个 JSON 对象；成功对象包含 `status`、`edition_id`、`course`、`items`、`rejected`。`items` 是可以展示的候选，每项保留输入字段、`source_level` 与 `item_id`；`rejected` 记录未采用候选及原因。

| `status` | 含义与后续动作 |
|---|---|
| `ready` | 使用 `items` 生成简报 |
| `no_eligible_candidates` | 如实报告本期没有合格公开候选 |
| `skipped_no_course_evidence` | 不生成通用点评，说明未取得所选课程的充分证据 |

`edition_id` 为 `FYYYYMMDD`。每个入选条目的 `item_id` 由排名后的位置确定，格式为 `FYYYYMMDD-01`、`FYYYYMMDD-02`、`FYYYYMMDD-03`；同一输入、时间窗、日期和上限必须得到相同 ID。不得自行改写 normalizer 的排序、去重或拒绝原因。

normalizer 不负责拒绝三级来源：调用方必须先按来源策略过滤候选，且不得把三级来源传入 normalizer 作为可展示候选。normalizer 返回的 `source_level` 仅是通过前置来源门禁后，供确定性优先排序使用的字段。

若前置课程证据查询为空，调用方直接使用 `skipped_no_course_evidence`，不将空 `candidates` 交给 normalizer。空 `candidates` 的 `no_eligible_candidates` 只表示已具备前置课程证据，但在时间窗和来源门禁后没有可处理新闻。

## 与订阅工作流的边界

订阅记录由专家维护。一份订阅只绑定一名学生和一门课程，其稳定任务键为 `finance-news:{schoolId}:{userId}:{courseId}`，不得包含会话 ID。`target_session_id` 是投递前重新校验的目标，不是任务键的一部分。Skill 不创建或保存上述记录，也不使用真实学生 ID、会话 ID、Cookie 或 Token。

## 展示映射

`items` 的 `fact_summary` 映射到新闻事实；`theory_citations` 映射到课程依据；`theory_analysis` 映射到理论分析；`discussion_question` 映射到讨论问题。不得在任何映射中删除来源 URL、发布时间或课程原文摘录。
