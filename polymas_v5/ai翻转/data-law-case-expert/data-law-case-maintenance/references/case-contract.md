# 案例主数据契约

本文件是案例结构的唯一权威定义。HTML、专家知识包、教师变更预览和版本快照均由该结构派生。

## 案例字段

| 字段 | 类型 | 规则 |
|---|---|---|
| `case_id` | string | 不可变标识，格式 `DLCL-0001` |
| `title` | string | 用户可见名称，可随版本修订 |
| `scene_id` | string | 一个主场景，格式 `scene-01` |
| `record_type` | string | `judicial_case`、`administrative_enforcement`、`regulatory_event`、`compliance_event`、`security_incident`、`pending_dispute`、`research_material` 或 `unclassified` |
| `jurisdiction` | string | 案件或事件的主要法域；未知时为 `待确认` |
| `case_status` | string | 发布状态：`草稿`、`待确认`、`已发布`、`已撤下` |
| `basic_facts` | string/null | 来源材料明确记载的基本案情 |
| `dispute_focus` | string/null | 材料未提供时为 `null` |
| `legal_provisions` | array | 每项含 `citation_text`、`source_url`、`evidence_status` |
| `outcome_type` | string | `judgment`、`administrative_action`、`settlement`、`event_progress`、`not_applicable`、`unknown` |
| `outcome` | string/null | 材料未提供或不适用时为 `null` |
| `outcome_evidence_status` | string | `verified`、`source_material`、`missing` |
| `legal_analysis` | string/null | 原材料分析或经教师确认的教学分析 |
| `analysis_origin` | string | `source_material`、`teacher_confirmed`、`ai_draft` |
| `sources` | array | 来源名称、URL、发布时间、检索时间和来源层级 |
| `evidence_status` | string | `待补证`、`材料已核对`、`官方来源已核验` |
| `classification_review_required` | boolean | 类型或场景由规则推断时为 `true` |
| `version` | integer | 案例级版本，从 1 开始递增 |

## 事实边界

- `outcome_evidence_status=missing` 时，`outcome` 必须为 `null`。
- 境外案件中的中国法条属于比较法教学映射，不表示中国法实际支配该境外案件。
- `ai_draft` 只能进入教师审查队列；教师确认前不进入学生已发布视图。
- 发布状态与证据状态彼此独立；学生只读取 `case_status=已发布`，同时显示 `evidence_status`。课程材料可在“已发布＋待补证”状态下用于教学，但必须显著提示证据边界。
- `source_material` 处理结果至少绑定一条材料来源；`verified`/“官方来源已核验”必须绑定官方 URL。
- 法条需分别记录案件当时依据和当前有效性核验状态；未联网核验时显示“待核验”。
- 一个案例只保存一份主记录；跨场景关系使用标签或关联案例表达，不复制案例。

## 场景字段

场景记录至少包含 `scene_id`、`order`、`name`、`slug`、`description` 和 `case_count`。首版以源文档的 10 个场景为分类基线。
