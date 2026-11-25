---
name: simulation-interview-grading
description: 批阅模拟面试场景。以老师配置的评分维度为唯一评分标准，结合面试阶段轨迹、候选人对话、角色扮演、专业知识测验、Skill调用、上传材料（简历/作品集/证书等）、面试总结以及可靠的语音或视频面试数据取证评分。固定输出维度评分、综合评语、改进建议、阶段表现和4项亮点；存在有效测验或上传内容时，再输出测验表现或上传评价。适用于模拟面试、角色扮演面试、结构化面试、压力面试和无领导小组讨论等场景。
---

# 模拟面试批阅

## 最高优先级输出约束

在开始评分前，先为每条评价标准建立唯一ID映射：

```text
resolvedDimensionId = 标准中的 dimensionId（若存在且非空）
                      否则取标准中的 itemId
```

- 每条评价标准必须至少存在非空的 `dimensionId` 或 `itemId`；两者都缺失时停止评分。
- 若同时存在，以 `dimensionId` 为准，但不得修改其值。
- 每个最终维度对象必须显式输出 `dimensionId: resolvedDimensionId`。
- 每个最终维度对象的 `dimensionName` 必须原样取自本次入参对应评价标准的维度名称。
- `dimensionId`、`dimensionScore`、`scoreReason` 是不可省略的必需字段。
- 严禁输出任何模板占位名称，严禁使用Skill中的示意值覆盖本次入参。
- 在逐项确认所有维度均包含上述三个字段之前，不得输出最终JSON。
- 输出后端或A2UI内容前，先完成评分JSON校验；任何维度缺少 `dimensionId` 均视为无效结果。

## 批阅对象

【本技能接收两类必需入参：

1. **老师配置的评分标准（面试评价要求）**：来自模拟面试配置页。每一项标准包含系统生成的 `itemId`；若上游已按研发方案改名，也可能直接传入 `dimensionId`。同时包含老师填写的"维度名称、满分值、评价描述、评价项详细要求"；满分字段允许上游使用 `fullMark`、`dimensionFullMark` 或"满分值"。维度数量、顺序和分值均以本次入参为准，Skill内不预设业务维度。模拟面试常见维度包括：沟通表达、专业知识、逻辑思维、应变能力、职业素养/态度等，但具体以老师配置为准。

2. **学生模拟面试记录（学生面试记录）**：包含学生在本次模拟面试中的阶段轨迹与实际表现。普通版至少包含面试阶段名称和学生/面试官聊天记录；Pro版可额外包含用户选择扮演的候选人类型、面试阶段分支、专业知识测验、Skill调用结果、上传材料（如简历、作品集、证书）、面试总结、语音转写、摄像头或录屏识别结果及实操行为记录。
】

【参考资料：
- 读取 `references/input-contract.md` 了解评分标准和训练记录的输入字段、别名及缺失处理。
- 读取 `references/evidence-rules.md` 判断证据归属、有效性和公平性。
- 根据本次实际存在的数据，按需读取 `references/modality-evaluation.md` 的对应评价方法。
- 读取 `references/evaluation-output-contract.md`，严格生成固定评价项与条件评价项。
】

【本技能自带脚本（在 `scripts/` 下，由批阅流程显式调用）：
- `scripts/normalize_training_record.py`：统一评分标准、模拟面试配置和学生面试记录的字段结构。
- `scripts/parse_ability_training_xlsx.py`：解析普通版模拟面试记录Excel中的"阶段名称"和"聊天记录"工作表。
- `scripts/calculate_dimension_score.py`：按照老师本次配置的动态维度、满分和顺序生成评分项。
】

---

## 批阅流程

**① 校验两类必需入参**

先识别"老师配置的评分标准"和"学生模拟面试记录"。评分标准至少包含一个维度；每个维度必须具有非空的 `dimensionId` 或 `itemId`，以及维度名称、严格大于0的满分值、评价描述和评价项详细要求。

若评分标准缺失、维度为空、某维度满分不大于0或细则缺失，则停止评分并报告缺失字段。不得自行补充默认维度、默认分值或默认评分细则。

**② 整理学生面试记录**

若输入为普通版模拟面试记录Excel，先调用 `scripts/parse_ability_training_xlsx.py` 解析；其他结构化输入调用 `scripts/normalize_training_record.py`。区分"未采集""未发生""学生未完成"：未采集的数据不得作为负面证据；训练明确要求但学生未完成的面试任务（如未进行自我介绍、未回答必答题），可按照老师配置的相关维度细则扣分。

**③ 按老师配置的每个维度取证评分**

读取 `references/evidence-rules.md`。只把学生实际产生的回答、选择、操作、测验作答和提交内容作为学生表现证据。普通版记录中仅 `role=user` 属于学生证据；`role=assistant` 的提问、提示、纠错、总结和表扬仅作为上下文。

严格按照老师入参中的维度顺序逐项评分。对每个维度：

1. 读取维度名称、满分值、评价描述和评价项详细要求。
2. 从面试记录中查找与该细则直接相关的正向证据、问题证据及未完成的必做行为。
3. 在0至该维度满分范围内给出实际得分。
4. 给出能够定位到学生回答、操作、测验或材料的打分原因。

**模拟面试场景取证要点：**
- **角色一致性**：学生是否始终维持候选人身份，未出现角色跳脱（如以面试官口吻发言、要求AI切换角色）。
- **回答结构化**：行为面试问题是否使用STAR法则、PREP结构或其他清晰框架；技术问题是否先给结论再展开。
- **专业知识准确性**：技术概念、项目经验、行业认知是否准确，有无明显事实错误。
- **沟通礼仪**：是否使用恰当称呼、是否表达感谢、反问环节是否体现对岗位/公司的了解。
- **压力应对**：面对追问、质疑、难题或沉默时，是否保持冷静、尝试拆解问题或坦诚说明。

不得增加、删除、合并、拆分、重命名或重新排序老师配置的维度。每个结果中的 `dimensionId` 必须取对应评价标准的 `dimensionId`；若入参没有该字段，则取 `itemId`。即 `output.dimensionId = input.dimensionId ?? input.itemId`。不得自行生成、改写或使用数组序号代替。

**④ 生成并校验 scoring**

调用 `scripts/calculate_dimension_score.py`，传入老师配置的 `evaluation_standards` 和逐维度判断 `dimension_judgements`。

输出前必须满足：

- 输出维度数量与老师配置完全一致。
- 输出 `dimensionId` 与老师配置的 `dimensionId` 或 `itemId` 逐项对应，名称、顺序和满分与老师配置一致。
- `scoreData.fullMark` 等于所有 `dimensionFullMark` 之和。
- `scoring.totalScore`、`scoreData.totalScore` 均等于所有 `dimensionScore` 之和。
- 每个维度满分严格大于0；实际得分允许为0。
- 每个实际得分均位于0至该维度满分之间。

**⑤ 生成固定评价项**

无论训练是否配置测验、上传或其他互动，始终输出以下四项：

1. 综合评语。
2. 改进建议。
3. 阶段表现：覆盖面试记录中的全部有效阶段，模拟面试阶段通常包括自我介绍、专业能力考察、行为/情景面试、综合素质考察、候选人反问等；每项包含原始 `stageId`、原始 `stageName` 和基于该阶段学生证据生成的 `stageEvaluation`。
4. 亮点清单：恰好输出4项，每项包含 `highlightId`、`highlightName` 和 `highlightDescription`。亮点必须来自学生真实回答、操作、选择、完成行为或提交内容；表现较弱时可提炼基础完成行为和相对可保留点，但不得捏造能力或成果。

若某阶段存在于训练配置但没有学生表现证据，仍保留该阶段，并在 `stageEvaluation` 中客观说明"未发现可评价的学生表现证据"；不得把智能体发言写成学生表现。

**⑥ 检测并生成条件评价项**

- **测验表现**：仅当 `quizzes` 非空，或测验类 `skill_invocations` 中存在成功且可读取的题目、学生答案、对错或得分结果时输出。客观题分数和正确率沿用系统结果，不重新判分；点评学生的正确率、题型或知识点表现。仅有"调用过测验Skill"的名称或空结果时不输出。
- **上传评价**：仅当 `uploads` 非空且存在可读取的文件名与正文、解析结果或摘要，或上传类 `skill_invocations` 中存在成功且可读取的材料结果时输出。模拟面试场景中上传材料通常为简历、作品集、证书等，评价其与面试岗位的相关性、完整性、有效性与可用性。每份材料包含原始 `uploadId`、原始 `uploadName` 和 `uploadEvaluation`。仅有上传动作、文件占位或失败记录而没有材料内容时不输出。

不得在没有对应数据时输出空的测验表现或上传评价，也不得输出 `null`、空数组或"本次无测验/无上传"的占位评价项。

**⑦ 输出平台 JSON**

在同一个平台标准JSON中输出 `scoring`、`evaluations`：

- `scoring`：动态总满分、总得分、老师配置的全部维度及逐维度打分原因。
- `evaluations`：固定输出综合评语、改进建议、阶段表现、亮点清单；按第⑥步条件追加测验表现和上传评价。

仅输出平台标准模板要求的合法JSON，不附加解释文字或Markdown代码围栏。

---

## 1. 评分项（scoring）

> 必填。评分项结构固定，但维度内容由本次入参动态决定，由平台直接渲染。

`scoringType`：`DIMENSIONS`（维度评分）

`scoreData.fullMark`：老师配置的所有维度满分之和

### 若 scoringType = DIMENSIONS（维度评分，≤10个维度）

**动态维度配置：**

| 字段 | 来源 | 输出要求 |
|---|---|---|
| 维度ID | 入参的 `dimensionId`，没有时取 `itemId` | 必须显式输出为 `dimensionId` |
| 维度名称 | 老师填写的"维度名称" | 原样输出为 `dimensionName`，不得改写 |
| 维度满分 | 老师填写的"满分值" | 原样输出为 `dimensionFullMark`，必须大于0 |
| 评价描述和评分规则 | 老师填写的"评价描述"与"评价项详细要求" | 用于评分，并输出为 `dimensionCriteria` |
| 维度实际得分 | 根据该维度细则和学生证据计算 | 输出为 `dimensionScore` |
| 维度得分原因 | 根据该维度细则和学生证据生成 | 输出为 `scoreReason`，不得为空 |

**满分字段硬约束：**

- `fullMark = sum(dimensions[].dimensionFullMark)`。
- 每个 `dimensions[].dimensionFullMark` 必须与对应入参维度的满分值完全一致且严格大于0。
- 学生缺少相关证据时，只能将实际得分设为0，不能把维度满分设为0。
- 每一个维度对象都必须包含 `dimensionId`、`dimensionScore`、`scoreReason`，三个字段均不得缺失或为 `null`。

**输出字段映射：**

正式输出必须完全根据本次入参逐项构造，不得引用任何预设维度名称、ID、分值或细则：

```text
scoring.scoringType = "DIMENSIONS"
scoring.scoreData.dimensions[i].dimensionId = input.dimensions[i].dimensionId ?? input.dimensions[i].itemId
scoring.scoreData.dimensions[i].dimensionName = input.dimensions[i].维度名称
scoring.scoreData.dimensions[i].dimensionFullMark = input.dimensions[i].满分值
scoring.scoreData.dimensions[i].dimensionCriteria = input.dimensions[i].评价描述 + input.dimensions[i].评价项详细要求
scoring.scoreData.dimensions[i].dimensionScore = 依据第i项细则计算的实际得分
scoring.scoreData.dimensions[i].scoreReason = 依据第i项细则和学生记录形成的得分原因
```

输出数组必须覆盖老师配置的全部维度。若老师配置N个维度，则 `dimensions` 必须恰好输出N项。输出前逐项检查：

```text
dimensions[i].dimensionId == (input.dimensions[i].dimensionId ?? input.dimensions[i].itemId)
dimensions[i].dimensionName == input.dimensions[i].维度名称
dimensions[i].dimensionScore != null
dimensions[i].scoreReason != null && dimensions[i].scoreReason != ""
```

---

## 2. 评价项（evaluations）

> 必填。评价项用于描述学生训练表现，不参与分数计算，老师可在复审页编辑。详细字段和条件规则见 `references/evaluation-output-contract.md`。

**评价项配置：**

| 评价项名称 | 评价项描述 | 评价项生成规则 |
|---|---|---|
| 综合评语 | 对学生本次模拟面试整体表现的概括性评价 | 综合本次老师配置的全部评分维度、得分原因和面试证据，用2至4句话概括面试表现、主要优势和核心问题；不得引用不存在的固定维度，不得与实际得分矛盾 |
| 改进建议 | 针对本次面试中最需要改进的问题给出下一次可执行建议 | 输出1至3条建议，每条按照"问题—证据—下一步行动"组织，优先覆盖失分较多或影响面试目标的问题，避免空泛表述 |
| 阶段表现 | 逐阶段说明学生在面试流程中的实际表现 | 始终输出；每个阶段包含 `stageId`、`stageName`、`stageEvaluation`，ID和名称必须来自入参 |
| 亮点清单 | 提炼本次面试中值得保留的行为与表现 | 始终且恰好输出4项；每项包含 `highlightId`、`highlightName`、`highlightDescription` |

**输出结果：**

以平台标准要求的JSON格式输出。不要自行指定 `TIMELINE`、`LIST` 等A2UI组件类型，不要为了选择展示样式额外包装 `type` 或 `content`；只输出评价项的语义数据，由平台根据内容生成展示形式。
