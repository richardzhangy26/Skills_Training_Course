---
name: training-deploy-and-test
description: "端到端自动化流程：根据训练剧本Markdown生成背景图、导入Polymas平台、使用优秀学生和中等学生两个档位自动进行对话测试并生成日志。关键词:一键部署、自动测试、对话测试、剧本导入、背景图生成、端到端、Pipeline、优秀学生、中等学生、自动化测试"
allowed-tools: Read, Bash, Write
---

# 训练部署与自动测试 Pipeline

端到端自动化：从训练剧本 Markdown 开始，自动生成背景图 → 导入平台 → 双档位对话测试，一步完成。

## 使用时机

当用户需要将训练剧本一键部署到平台并进行自动化测试时使用此 skill，典型场景包括:
- 用户提供了训练剧本配置 Markdown，需要"直接导入并测试"
- 用户提到"一键部署"、"自动测试"、"导入并测试"、"部署并测试"等关键词
- 用户希望对已有剧本执行完整的 Pipeline（背景图 + 导入 + 对话测试）
- 用户要求使用不同学生档位进行自动化对话测试

## 前置条件

### 必须的环境变量（在项目根目录 `.env` 中配置）

| 变量 | 说明 | 获取方式 |
|------|------|----------|
| `AUTHORIZATION` | Polymas Bearer Token | 浏览器 DevTools → Network → runCard 请求的 Authorization 头 |
| `COOKIE` | 浏览器 Cookie | 同上，Cookie 头 |
| `TASK_ID` | 训练任务 ID | URL 中 trainTaskId 后面的字符串 |

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

### 背景图生成需要额外配置（在 `.claude/skills/.env` 中）
```
LLM_API_KEY=sk-xxx
```

## 工作流程

### 第一步: 确认输入文件和任务 ID

1. 使用 Read 工具读取用户提供的训练剧本配置 Markdown 文件
2. 确认 `TASK_ID` 环境变量已配置，或从用户获取

### 第二步: 执行 Pipeline

使用 Bash 工具运行 `scripts/run_pipeline.py`，该脚本会自动按顺序执行三个步骤:

**调用方式**:
```bash
cd /Users/zhangyichi/工作/能力训练
python .claude/skills/training-deploy-and-test/scripts/run_pipeline.py <剧本配置.md路径>
```

**完整参数**:
```bash
python .claude/skills/training-deploy-and-test/scripts/run_pipeline.py <剧本配置.md> \
  --task-id <任务ID>           # 可选，默认从 TASK_ID 环境变量读取 \
  --profiles good,medium       # 可选，默认 good,medium \
  --skip-bg                    # 可选，跳过背景图生成 \
  --skip-import                # 可选，跳过平台导入 \
  --skip-test                  # 可选，跳过自动测试
```

Pipeline 内部执行顺序:

#### Step 1/3: 生成阶段背景图
- 参考skill `@.claude/skills/training-background-generator`
- 调用 `training-background-generator` 的 `generate_background.py`
- 为每个训练阶段生成 16:9 背景图
- 自动回填图片路径到 Markdown 的 `**背景图**` 字段
- ⚠️ 此步骤失败不会中止 Pipeline（背景图非必需）

#### Step 2/3: 导入训练剧本到平台
- 调用 `skill_training_build/create_task_from_markdown.py`
- 解析 Markdown → 创建脚本节点 → 自动连接流程
- 上传背景图到平台
- ❌ 此步骤失败会中止 Pipeline

#### Step 3/3: 自动对话测试
- 使用 `WorkflowTester` 类（来自 `auto_script_train.py`）
- 默认使用「优秀学生」(good) 和「中等学生」(medium) 两个档位
- 每个档位独立运行完整的对话流程
- 对话日志保存到 `log/` 目录

### 第三步: 向用户汇报结果

汇报以下信息:
1. 每个步骤的执行状态（成功/失败）
2. 背景图生成结果（数量、路径）
3. 平台导入结果
4. 每个档位的对话测试结果
5. 日志文件位置

## 常用场景示例

### 场景 1: 完整 Pipeline
```
用户: @离心泵汽蚀故障紧急诊断/训练剧本配置.md 请导入到平台并进行自动测试
```
→ 执行完整的三步 Pipeline

### 场景 2: 跳过背景图（已有背景图）
```bash
python .claude/skills/training-deploy-and-test/scripts/run_pipeline.py 训练剧本配置.md --skip-bg
```

### 场景 3: 只运行测试（已手动导入）
```bash
python .claude/skills/training-deploy-and-test/scripts/run_pipeline.py 训练剧本配置.md --skip-bg --skip-import
```

### 场景 4: 自定义测试档位
```bash
# 只测优秀学生
python ... 训练剧本配置.md --profiles good

# 测试所有档位
python ... 训练剧本配置.md --profiles good,medium,bad
```

## 输出目录结构

执行完整 Pipeline 后:
```
任务目录/
├── 训练剧本配置.md              ← 背景图路径已自动回填
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
| 背景图生成失败 | LLM_API_KEY 未配置 | 在 `.claude/skills/.env` 中配置 |
| 导入失败 | Markdown 格式不符 | 检查是否包含 `### 阶段N:` 格式的阶段标题 |
| 测试中 Doubao 无法调用 | API Key 错误或网络问题 | 检查 ARK_API_KEY 或 LLM_API_KEY |
| 对话测试无限循环 | 平台配置问题 | 脚本内置 80 轮安全上限，会自动退出 |
