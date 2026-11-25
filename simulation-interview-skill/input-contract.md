# 输入约定

## 必需输入一：老师配置的评分标准

评分标准来自模拟面试配置页，在平台消息中通常作为"面试评价要求"传入。至少包含一个评分维度，每个维度包含：

| 字段来源 | 规范字段 | 约束 |
|---|---|---|
| 系统生成的评价项ID | `dimensionId` 或 `itemId` | 至少一个非空且唯一；结果统一输出为 `dimensionId` |
| 维度名称 | `name` | 非空，并在本次评分标准内可区分 |
| 满分值 | `full` | 数值且严格大于0 |
| 评价描述 | `description` | 非空，用于说明该维度评价什么 |
| 评价项详细要求 | `detailed_requirements` | 非空，作为取证和评分细则 |

推荐结构：

```json
{
  "evaluation_standards": {
    "dimensions": [
      {
        "itemId": "criterion-uuid",
        "name": "维度名称",
        "full": 20,
        "description": "该维度评价范围",
        "detailed_requirements": "具体得分、扣分和证据要求"
      }
    ]
  }
}
```

兼容别名：

- 评分标准：`evaluation_standards`、`evaluation_standard`、`scoring_standard`、`rubric`。
- 维度数组：`dimensions`、`scoring_dimensions`、`criteria`。
- 评价项ID：优先读取 `dimensionId`、`dimension_id`；不存在时读取 `itemId`、`item_id`。
- 维度满分：`full`、`full_score`、`full_mark`、`dimensionFullMark`、`score`、`分值`、`满分值`。
- 评价描述：`description`、`evaluation_description`、`评价描述`。
- 详细要求：`detailed_requirements`、`requirements`、`scoring_rule`、`评价项详细要求`。

平台可能以Markdown形式传入"面试评价要求"，例如：

```markdown
### 1. 沟通表达（满分：10分）
评价描述
- itemId：abc123
- 详细要求：评价细则
```

先按上述字段提取结构。ID由业务系统随评价标准一同传入，可能使用 `itemId`，也可能已由上游改名为 `dimensionId`。模型不得根据维度名称或数组序号自行生成。批阅输出时执行：`output.dimensionId = input.dimensionId ?? input.itemId`。

总满分默认由各维度满分求和。如果入参另有总满分，该值必须与维度满分之和一致，否则停止评分并报告配置不一致。

## 必需输入二：学生模拟面试记录

学生模拟面试记录在平台消息中通常作为"学生面试记录"传入。

### 普通版Excel记录

普通版记录包含两个工作表：

| 工作表 | 字段 | 含义 |
|---|---|---|
| 阶段名称 | `script_step_id` | 阶段ID |
| 阶段名称 | `step_name` | 阶段名称 |
| 聊天记录 | `step_Id` | 当前消息所属阶段ID |
| 聊天记录 | `role` | `user`表示学生，`assistant`表示智能体 |
| 聊天记录 | `content` | 对话正文 |

工作表不包含时间戳、显式阶段完成状态或评分结果。只能依据消息顺序还原对话，不得编造时间；出现某阶段消息只说明进入过该阶段，不自动证明阶段目标高质量完成。

### 结构化训练记录

可包含：

- `stage_runs`：阶段进入、退出、完成、跳过和重试记录。
- `dialogues`：学生与智能体的对话。
- `quizzes`：题目、学生答案、参考答案、得分和知识点。
- `interactions`：选择、搜索、工具调用、表单和白板等行为。
- `uploads`：学生上传材料及解析结果。
- `media`：语音、摄像头、录屏或实操识别结果。
- `final_outputs`：总结、方案、报告、反思等最终产出。

阶段信息至少应能解析出阶段ID和阶段名称。兼容 `stageId`、`stage_id`、`script_step_id`、`step_Id` 作为阶段ID，兼容 `stageName`、`stage_name`、`step_name` 作为阶段名称。阶段表现输出必须沿用这些原始值，不得另造ID或改写名称。

### Pro版扩展

- `selected_role` 或 `role_selections`：学生选择扮演的角色及发生阶段。
- `skill_invocations`：被唤起的Skill名称、类型、输入、输出、状态和所属阶段。
- 测验Skill结果写入 `quizzes`。
- 上传Skill结果写入 `uploads`，并提供可读取的文件正文或解析内容。
- 搜索、知识库、白板、点评等结果写入 `interactions`。
- 摄像头、录屏、语音和实操识别结果写入 `media`。

用于条件评价项时：测验记录应提供可回传的测验ID与名称，上传记录应提供可回传的上传ID与文件名。兼容 `quizId`、`quiz_id`、`id` 作为测验ID，兼容 `uploadId`、`upload_id`、`fileId`、`file_id`、`id` 作为上传ID。输出时沿用原值，不根据名称生成新ID。

## 可选输入

- `training`：模拟面试名称、角色、阶段、任务目标和完成条件。
- `teacher_supplement`：教师对本次发布作业的补充要求。

## 缺失与异常处理

- 评分标准缺失：停止评分，不启用默认维度。
- `dimensionId` 和 `itemId` 同时缺失：停止评分，不生成临时ID，也不使用维度名称代替。
- 其他维度字段缺失或满分不大于0：停止评分并指出具体维度和字段。
- 总满分与维度满分之和不一致：停止评分，不擅自修改老师配置。
- 未采集：系统没有提供该类学生数据，不得推断为表现不佳。
- 未发生：训练设计中没有该环节，不得因此扣分。
- 未完成：训练明确要求学生完成但记录显示未完成，可以依据对应维度细则扣分。
- 仅检测到Skill名称但没有成功结果或可读取内容：不视为存在可评价的测验或上传数据，不输出对应条件评价项。
