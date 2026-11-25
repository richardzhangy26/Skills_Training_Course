# 能力训练通用批阅 Skill

## 文件结构

```text
ability-training-evaluator/
├── SKILL.md
├── README.md
├── references/
│   ├── input-contract.md
│   ├── evidence-rules.md
│   ├── evaluation-output-contract.md
│   └── modality-evaluation.md
└── scripts/
    ├── normalize_training_record.py
    ├── parse_docx_inputs.py
    ├── parse_ability_training_xlsx.py
    └── calculate_dimension_score.py
```

## 两类必需入参

1. 老师在能力训练配置页填写的评分标准，包括系统生成的评价项 `itemId`（或上游已改名的 `dimensionId`）、维度名称、满分值、评价描述和评价项详细要求。
2. 学生能力训练记录，包括对话、阶段、角色选择、测验、Skill调用、上传材料、最终成果及实际采集到的多模态记录。

平台测试时，老师评价标准放入“作业要求”，学生训练记录放入“学生提交”。两类输入都可以是平台能够读取的正文、结构化数据或附件，包括PDF、TXT、Word、Excel等，且不要求格式一致。正式版每次都从本次老师评价标准动态提取维度，不保留演示版固定维度。

## 平台约定

- Skill不预设评分维度、维度数量、维度名称或固定总分。
- 输出维度必须与老师本次配置逐项一致，并按 `output.dimensionId = input.dimensionId ?? input.itemId` 映射ID。
- 每个维度结果必须包含 `dimensionId`、`dimensionScore` 和 `scoreReason`。
- 总满分等于老师配置的所有维度满分之和。
- 不生成默认维度；始终使用本次“作业要求”中解析出的评分标准。
- 固定输出5个必评模块：维度评分、综合评语、改进建议、阶段表现、亮点清单。其中维度评分位于 `scoring`，其余4项位于 `evaluations`。
- 阶段表现被渲染为时间线时，每个节点必须包含非空 `time`；没有真实时间戳时使用“阶段1”“第2阶段”等顺序标签。
- 测验表现和上传表现为2个选评模块：仅在对应测验Skill或上传Skill成功产生非空、可评价入参或结果时追加；只有Skill名称、空入参、失败记录或不可读文件时不输出整个板块。
- 因维度评分不在 `evaluations` 中，报告业务模块总数为5至7个，`evaluations` 的合法数量仍为4至6项。
- 禁止生成 `cards: []`；所有LIST评价项至少包含1张卡片。
- 不声明A2UI组件类型，由平台根据语义数据生成展示形式。

## 证据约定

普通版记录支持“阶段名称”和“聊天记录”两张工作表，学生证据来自 `role=user`。Pro版可增加角色选择、分支、测验、上传、Skill调用和多模态数据。智能体的提示、总结和表扬仅作为上下文，不能直接计入学生表现。
