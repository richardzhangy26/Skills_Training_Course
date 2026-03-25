---
name: training-deploy-and-test
description: "端到端自动化流程：根据训练剧本Markdown生成背景图、导入Polymas平台、使用优秀学生和中等学生两个档位自动进行对话测试并生成日志。关键词:一键部署、自动测试、对话测试、剧本导入、背景图生成、端到端、Pipeline、优秀学生、中等学生、自动化测试"
allowed-tools: Read, Bash, Write
---

# 训练部署与自动测试 Pipeline

端到端自动化：从训练剧本 Markdown 开始，自动创建训练任务 → 生成背景图 → 导入平台 → 双档位对话测试，一步完成。

## 使用时机

当用户需要将训练剧本一键部署到平台并进行自动化测试时使用此 skill，典型场景包括:
- 用户提供了训练剧本配置 Markdown，需要"直接导入并测试"
- 用户提到"一键部署"、"自动测试"、"导入并测试"、"部署并测试"等关键词
- 用户希望对已有剧本执行完整的 Pipeline（背景图 + 导入 + 对话测试）
- 用户要求使用不同学生档位进行自动化对话测试
- 用户需要创建新的训练任务（之前需要手动在平台创建）

## 前置条件

### 必须的环境变量（在项目根目录 `.env` 中配置）

| 变量 | 说明 | 获取方式 |
|------|------|----------|
| `AUTHORIZATION` | Polymas Bearer Token | 浏览器 DevTools → Network → runCard 请求的 Authorization 头 |
| `COOKIE` | 浏览器 Cookie | 同上，Cookie 头 |
| `COURSE_ID` | 课程 ID | 从平台 URL 或课程配置中获取（创建新任务时需要） |

### 可选的环境变量

| 变量 | 说明 | 获取方式 |
|------|------|----------|
| `TASK_ID` | 训练任务 ID | URL 中 trainTaskId 后面的字符串（使用现有任务时） |

### LLM 配置（二选一）

**方式1: Doubao POST API（默认）**
```
MODEL_TYPE=doubao_post
LLM_API_KEY=sk-xxx
LLM_MODEL=Doubao-1.5-pro-32k
LLM_API_URL=http://llm-service.polymas.com/api/openai/v1/chat/completions
LLM_SERVICE_CODE=SI_Ability
```

**方式2: Doubao SDK**
```
MODEL_TYPE=doubao_sdk
ARK_API_KEY=ak-xxx
DOUBAO_MODEL=doubao-seed-1-6-251015
```

### 封面图生成需要额外配置（用于创建新任务时）
```
ARK_API_KEY=ak-xxx  # 用于调用 Doubao Seedream 模型生成封面图
```

## 工作流程

### 第一步: 确认输入文件和任务 ID

1. 使用 Read 工具读取用户提供的训练剧本配置 Markdown 文件
2. 确认是否已配置 `TASK_ID` 或需要创建新任务
3. 如需创建新任务，确认 `COURSE_ID` 已配置

### 第二步: 执行 Pipeline

使用 Bash 工具运行 `scripts/run_pipeline.py`，该脚本会自动按顺序执行四个步骤:

**调用方式**:
```bash
cd /Users/zhangyichi/工作/能力训练
python .claude/skills/training-deploy-and-test/scripts/run_pipeline.py <剧本配置.md路径>
```

**完整参数**:
```bash
python .claude/skills/training-deploy-and-test/scripts/run_pipeline.py <剧本配置.md> \
  --create-task                # 强制创建新任务（即使 TASK_ID 已存在） \
  --create-only                # 仅创建任务，不执行后续步骤 \
  --course-id <课程ID>         # 创建新任务时需要（也可从 COURSE_ID 环境变量读取） \
  --task-id <任务ID>           # 使用现有任务（也可从 TASK_ID 环境变量读取） \
  --profiles good,medium       # 可选，默认 good,medium \
  --skip-bg                    # 可选，跳过背景图生成 \
  --skip-import                # 可选，跳过平台导入 \
  --skip-test                  # 可选，跳过自动测试 \
  --delete-existing            # 可选，删除现有节点后重新导入 \
  --with-rubric                # 可选，导入后配置评价标准（独立步骤） \
  --rubric-path <路径>         # 可选，指定评价标准文件路径 \
  --publish                    # 可选，所有配置完成后发布任务（独立步骤）
```

Pipeline 内部执行顺序:

#### Step 0: 创建训练任务（可选）
- 当未提供 `--task-id` 或指定 `--create-task` 时自动执行
- 解析 Markdown 中的 `## 基础配置` 区域，获取任务名称、描述、背景图
- 使用 Doubao API 生成 16:9 封面图（如果未指定背景图或生成失败，使用平台默认封面）
- 调用平台 API 创建训练任务（仅基础配置，不含评价标准和发布）
- ✅ 自动将 `TASK_ID` 写入项目根目录 `.env` 文件
- ❌ 此步骤失败会中止 Pipeline

#### Step 1: 生成阶段背景图
- 参考skill `@.claude/skills/training-background-generator`
- 调用 `training-background-generator` 的 `generate_background.py`
- 为每个训练阶段生成 16:9 背景图
- 自动回填图片路径到 Markdown 的 `**背景图**` 字段
- ⚠️ 此步骤失败不会中止 Pipeline（背景图非必需）

#### Step 2: 导入训练剧本到平台
- 调用 `skill_training_build/create_task_from_markdown.py`
- 解析 Markdown → 创建脚本节点 → 自动连接流程
- 上传背景图到平台
- ❌ 此步骤失败会中止 Pipeline

#### Step 3: 配置评价标准（`--with-rubric`）
- 独立步骤，在剧本导入完成后执行
- 自动发现同目录或父目录下的 `评价标准.md` 文件
- 可通过 `--rubric-path` 指定评价标准文件路径
- 使用已有 `--task-id` 时也能执行（不依赖 Step 0）
- ⚠️ 此步骤失败不会中止 Pipeline

#### Step 4: 发布任务（`--publish`）
- 独立步骤，在所有配置（剧本+评价标准）完成后执行
- 调用 PUBLISH_URL 发布任务，确保发布的任务是完整的
- ⚠️ 此步骤失败不会中止 Pipeline（打印警告）

#### Step 5: 自动对话测试
- 使用 `WorkflowTester` 类（来自 `auto_script_train.py`）
- 默认使用「优秀学生」(good) 和「中等学生」(medium) 两个档位
- 每个档位独立运行完整的对话流程
- 对话日志保存到 `log/` 目录

### 第三步: 向用户汇报结果

汇报以下信息:
1. 每个步骤的执行状态（成功/失败）
2. 新创建任务的信息（如果创建了任务）
3. 背景图生成结果（数量、路径）
4. 平台导入结果
5. 每个档位的对话测试结果
6. 日志文件位置

## Markdown 格式要求

训练剧本配置 Markdown 必须在文件开头包含基础配置区域：

```markdown
## 基础配置

- **任务名称**: 离心泵汽蚀故障紧急诊断
- **任务描述**: 通过模拟真实的工业现场故障场景，培养学员快速诊断离心泵汽蚀问题的能力
- **背景图**: backgrounds/stage_1_cover.png

---

## 阶段配置

### 阶段1: 故障发现
...
```

**字段说明**:
- `任务名称`: 训练任务的显示名称（必填）
- `任务描述`: 任务的简短描述，会显示在课程列表中（必填）
- `背景图`: 任务封面图路径，可以是相对路径（可选，留空则自动生成或使用第一阶段背景图）

## 常用场景示例

### 场景 1: 仅创建新任务（不部署）
```bash
python .claude/skills/training-deploy-and-test/scripts/run_pipeline.py 训练剧本配置.md \
  --create-only \
  --course-id xxx
```
→ 创建任务后 TASK_ID 自动写入 .env，程序退出

### 场景 2: 创建新任务并完整部署
```bash
python .claude/skills/training-deploy-and-test/scripts/run_pipeline.py 训练剧本配置.md \
  --create-task \
  --course-id xxx
```
→ 成功后自动继续执行背景图生成 → 导入 → 测试

### 场景 3: 使用现有任务部署（向后兼容）
```bash
python .claude/skills/training-deploy-and-test/scripts/run_pipeline.py 训练剧本配置.md \
  --task-id abc123
```

### 场景 4: 从环境变量读取配置（最简洁）
```bash
export COURSE_ID=xxx
# export TASK_ID=abc123  # 可选，如果不设置则自动创建新任务
python .claude/skills/training-deploy-and-test/scripts/run_pipeline.py 训练剧本配置.md
```

### 场景 5: 跳过背景图（已有背景图）
```bash
python .claude/skills/training-deploy-and-test/scripts/run_pipeline.py 训练剧本配置.md --skip-bg
```

### 场景 6: 只运行测试（已手动导入）
```bash
python .claude/skills/training-deploy-and-test/scripts/run_pipeline.py 训练剧本配置.md --skip-bg --skip-import
```

### 场景 7: 自定义测试档位
```bash
# 只测优秀学生
python ... 训练剧本配置.md --profiles good

# 测试所有档位
python ... 训练剧本配置.md --profiles good,medium,bad
```

### 场景 8: 创建任务时配置评价标准并发布
```bash
# 创建任务、配置评价标准（自动发现）并发布
python .claude/skills/training-deploy-and-test/scripts/run_pipeline.py 训练剧本配置.md \
  --create-task \
  --course-id xxx \
  --with-rubric \
  --publish

# 指定评价标准文件路径
python .claude/skills/training-deploy-and-test/scripts/run_pipeline.py 训练剧本配置.md \
  --create-task \
  --course-id xxx \
  --with-rubric \
  --rubric-path /path/to/评价标准.md \
  --publish

# 仅创建任务并发布（不生成背景图、不测试）
python .claude/skills/training-deploy-and-test/scripts/run_pipeline.py 训练剧本配置.md \
  --create-only \
  --course-id xxx \
  --with-rubric \
  --publish
```

## 输出目录结构

执行完整 Pipeline 后:
```
任务目录/
├── 训练剧本配置.md              ← 背景图路径已自动回填
├── covers/                       ← Step 0 生成（任务封面图）
│   └── task_cover.png
├── backgrounds/                  ← Step 1 生成
│   ├── stage_1_xxx.png
│   ├── stage_2_xxx.png
│   └── generation_record.json
└── (平台上的训练任务已更新)       ← Step 2 导入

log/
└── [context_path]/
    ├── good/                     ← Step 3 优秀学生测试
    │   ├── task_xxx_runcard.txt
    │   ├── task_xxx_dialogue.txt
    │   └── task_xxx_dialogue.json
    └── medium/                   ← Step 3 中等学生测试
        ├── task_xxx_runcard.txt
        ├── task_xxx_dialogue.txt
        └── task_xxx_dialogue.json
```

## 故障排除

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 401/403 错误 | Token 过期 | 重新从浏览器 DevTools 获取 AUTHORIZATION 和 COOKIE |
| 缺少基础配置字段 | Markdown 格式不符 | 确保 Markdown 开头包含 `## 基础配置` 区域 |
| 封面图生成失败 | ARK_API_KEY 未配置 | 在 `.env` 中配置 ARK_API_KEY，或忽略（会使用默认封面） |
| 背景图生成失败 | LLM_API_KEY 未配置 | 在 `.claude/skills/.env` 中配置 |
| 导入失败 | Markdown 格式不符 | 检查是否包含 `### 阶段N:` 格式的阶段标题 |
| 测试中 Doubao 无法调用 | API Key 错误或网络问题 | 检查 ARK_API_KEY 或 LLM_API_KEY |
| 对话测试无限循环 | 平台配置问题 | 脚本内置 80 轮安全上限，会自动退出 |
| COURSE_ID 未配置 | 创建任务时缺少课程ID | 通过 `--course-id` 参数或 `COURSE_ID` 环境变量提供 |
