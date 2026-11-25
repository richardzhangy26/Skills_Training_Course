# SKILL TRAINING BUILD

**Generated:** 2026-03-04

## OVERVIEW

Markdown → 平台任务构建工具。将结构化Markdown剧本自动转换为Polymas平台的训练任务节点和流程。

---

## STRUCTURE

```
skill_training_build/
├── create_task_from_markdown.py   # 核心构建脚本
├── create_score_items_from_rubric.py  # 从评价标准生成分数项
├── split_scenario_script*.py      # 场景分割工具
├── task_example.md                # Markdown格式模板
└── test/                          # 测试用例
```

---

## WHERE TO LOOK

| 任务 | 文件 | 说明 |
|------|------|------|
| 构建任务 | `create_task_from_markdown.py` | 解析Markdown → 创建API节点 → 连接流程 |
| 生成评分项 | `create_score_items_from_rubric.py` | 从评价标准JSON生成分数配置 |
| 参考格式 | `task_example.md` | Markdown剧本字段定义示例 |

---

## CONVENTIONS

### Markdown剧本字段

```markdown
### 阶段N: 阶段名称
**虚拟训练官名字**: 张老师              # → trainerName
**模型**: doubao-seed-2.0-pro            # → modelId，按当前平台模型接口核实映射
**数字人**:                            # → customDigitalHuman，创建前留空
**数字人名称**: 张老师                   # → digitalHumanName
**声音**: [当前平台声音资源ID]             # → agentId，配套声音参数一并核实
**形象**: [当前平台形象资源ID]             # → avatarNid
**互动轮次**: 3                         # → 该阶段对话轮数
**开场白**: "欢迎来到..."                # → 阶段开始AI发言
**提示词**: [LangGPT格式系统提示词]      # → system prompt
```

### 流程构建规则
- 自动识别平台的**开始节点**和**结束节点**
- 按阶段顺序连接: Start → Step1 → Step2 → ... → End
- 连线条件默认使用下一个阶段名称

### 模型与数字人导入
- 遵循根目录 `AGENTS.md`「能力训练模型与数字人（统一规则）」。业务阶段显式指定 `doubao-seed-2.0-pro`，不能依赖脚本中的旧模型兜底。
- 从当前平台接口选择声音、形象后，调用 `create_task_from_markdown.py` 的 `create_custom_digital_human` 创建本任务数字人；该函数使用 `ai-profile/digital_human/custom/addAndSyncResource`。仅在已获授权的导入阶段执行。
- `resolve_step_digital_human` 会查找历史同名或相同组合，不能仅凭字段留空认定它必然新建。导入流程须先创建新组合并显式绑定返回 ID，或先调整实现以满足新建规则；同一任务角色和断点续跑使用本任务创建记录。
- 英文口语也必须显式配置本任务新建的数字人，不依赖部署器的既有 `Assistant` 兜底。只有用户明确要求“新建一个数字人形象”或自定义形象时才上传人物图片。
- 验收须回读业务阶段的模型以及 `customDigitalHuman`、`avatarNid`、`agentId`、配套声音参数，并与本任务创建记录对照。

### 环境变量
```bash
AUTHORIZATION=eyJ0eXAiOiJKV1Q...  # JWT Token
COOKIE=xxx                         # 完整Cookie字符串
TASK_ID=xxx                        # 目标训练任务ID
```

---

## ANTI-PATTERNS

| 禁止 | 正确做法 |
|------|----------|
| 手动复制粘贴到平台 | 使用脚本批量创建节点和连线 |
| 在平台直接修改后不同步 | 修改Markdown源文件后重新构建 |
| 跳过阶段编号 | 严格使用"阶段1:"、"阶段2:"格式 |

---

## COMMANDS

```bash
# 交互式运行（推荐）
python create_task_from_markdown.py
# 提示输入: Markdown文件路径、TaskID

# 带参数运行
python create_task_from_markdown.py <markdown_path> <task_id>

# 从评价标准生成分数项
python create_score_items_from_rubric.py
```

---

## NOTES

1. **节点ID持久化**: 首次创建后，节点ID会回写到Markdown文件底部注释
2. **幂等执行**: 已存在的节点会被识别，不会重复创建
3. **语音配置**: 按角色从当前平台声音接口选取资源，并与平台已有形象组合新建数字人
4. **模型选择**: 统一使用 `doubao-seed-2.0-pro`
