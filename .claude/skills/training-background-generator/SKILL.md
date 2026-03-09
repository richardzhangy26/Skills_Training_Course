---
name: training-background-generator
description: "根据能力训练剧本配置文档，为每个训练阶段生成写实中国风的16:9背景图片。解析Markdown格式的剧本配置，提取每个阶段的描述和场景配置，使用Doubao Seedream模型生成对应的背景图并保存到任务配置目录。关键词:背景图生成、阶段背景、中国风、写实风格、16:9、训练剧本、场景图片、文生图"
allowed-tools: Read, Bash, Write
---

# 训练阶段背景图生成器

根据能力训练剧本配置文档，为每个训练阶段生成写实中国风的16:9背景图片，并自动保存到对应的任务配置目录。

## 使用时机

当用户需要为能力训练的各个阶段生成背景图片时使用此 skill，典型场景包括:
- 用户提供了训练剧本配置文档（Markdown格式），需要为每个阶段生成背景图
- 用户提到"生成阶段背景图"、"生成训练背景"、"为剧本生成图片"等关键词
- 用户需要批量生成多个阶段的场景背景图
- 用户提到 seedream、文生图、背景图相关词汇

## 工作流程

### 第一步: 读取剧本配置文档

1. 使用 Read 工具读取用户提供的训练剧本配置 Markdown 文件
2. 确认文档包含 `### 阶段N:` 或 `### 阶段N：` 格式的阶段标题

### 第二步: 调用脚本生成背景图

使用 Bash 工具运行 `scripts/generate_background.py`，该脚本会自动完成:
1. 解析所有训练阶段（阶段编号、名称、描述、场景配置）
2. 调用 Doubao 文本模型（LLM）理解阶段上下文，生成高质量文生图提示词
3. 调用 Doubao Seedream 文生图 API 生成 16:9 背景图
4. 下载并保存图片到 `backgrounds_{任务名字}/` 目录
5. 自动回填图片路径到剧本 Markdown 的 `**背景图**` 字段
6. 生成 `generation_record.json` 记录文件

**调用方式**:
```bash
cd /Users/zhangyichi/工作/能力训练
python .claude/skills/training-background-generator/scripts/generate_background.py <剧本配置.md路径>
```

**可选参数**:
```bash
# 指定输出目录
python ... <剧本配置.md> --output-dir ./my_backgrounds

# 跳过LLM生成提示词（直接硬拼，速度更快但质量略低）
python ... <剧本配置.md> --no-llm-prompt

# 自定义风格后缀
python ... <剧本配置.md> --style "中国写实人物风格，东方美学，16:9"

# 指定文生图模型（默认: doubao-seedream-3-0-t2i-250415）
python ... <剧本配置.md> --model doubao-seedream-3-0-t2i-250415

# 指定文本模型（用于生成提示词，默认从.env读取）
python ... <剧本配置.md> --text-model doubao-seed-1-6-251015
```

### 第三步: 向用户汇报结果

报告:
- 成功生成的图片数量和文件路径
- 每个阶段使用的提示词（便于后续调整）
- 保存目录的完整路径
- 如有失败，列出失败的阶段和错误原因

## 环境配置

脚本使用 `.claude/skills/.env` 中的以下变量:

| 变量 | 用途 | 备注 |
|------|------|------|
| `LLM_API_KEY` | Polymas API 密钥（文生图 + 文本模型） | 必需 |
| `LLM_API_URL` | Polymas API 基础URL | 默认 `https://llm-service.polymas.com/api/openai/v1` |
| `LLM_MODEL` | 文本模型（用于生成提示词） | 默认 `Doubao-1.5-pro-32k` |

如果 `LLM_API_KEY` 未配置，脚本会尝试使用 `ARK_API_KEY`（直连 Volcengine Ark）作为备选。

## 示例

### 示例输入

```
@skills_training_course/化工原理-武夷学院/离心泵汽蚀故障紧急诊断/训练剧本配置.md
请为这个剧本的每个阶段生成背景图
```

### 解析结果示例

| 阶段 | 名称 | 场景描述 |
|------|------|---------|
| 1 | 开场与现象认知 | 化工厂车间，B区设备间，泵旁有监控屏幕 |
| 2 | 根因分析 | 李主任办公室或泵房，手里拿着运行记录本 |
| 3 | 应急处理与决策 | 泵房和控制室，李主任在旁边指挥 |
| 4 | 知识整合与总结 | 会议室或办公室，墙上贴着维护记录 |

### 输出文件结构

```
离心泵汽蚀故障紧急诊断/
├── 训练剧本配置.md              ← 背景图路径已自动回填
├── backgrounds/
│   ├── stage_1_开场与现象认知.png
│   ├── stage_2_根因分析.png
│   ├── stage_3_应急处理与决策.png
│   ├── stage_4_知识整合与总结.png
│   └── generation_record.json   ← 生成记录（URL、提示词、时间戳）
```

## 提示词设计指南

脚本使用 LLM 自动生成提示词，以下是不同场景类型的参考风格:

### 工业/工厂场景
- 强调工业设备的细节和真实感
- 包含安全标识、管道、仪表等元素
- 使用工业照明（荧光灯、应急灯）
- 中国工业现场风格

### 办公/会议场景
- 现代中式办公环境
- 包含白板、投影、文件资料等
- 自然光与室内照明结合

### 实验室/教学场景
- 精密仪器和实验设备
- 干净整洁的实验台
- 专业的实验室照明

## 注意事项

1. **16:9比例**: 图片尺寸固定为 512x288（符合 Polymas API 豆包模型的建议值）
2. **风格一致性**: 同一任务的所有阶段背景图应保持视觉风格一致
3. **API限流**: 每次图片生成之间有2秒间隔，避免触发限流
4. **URL时效性**: 生成的图片 URL 有时效性，脚本会自动下载到本地保存
5. **回填字段**: 剧本 Markdown 中需要有 `**背景图**:` 字段才能自动回填路径

## 错误处理

1. **LLM_API_KEY未配置**: 尝试切换到 ARK_API_KEY，否则提示用户配置
2. **某阶段提示词生成失败**: 自动使用硬拼方式 (fallback)，继续处理其他阶段
3. **图片生成失败**: 记录失败阶段，继续生成其他阶段，最终汇总报告
4. **未找到背景图字段**: 正常完成生成，提示用户手动添加 `**背景图**:` 字段

## 脚本工具

### scripts/generate_background.py

独立的 CLI 脚本，可直接运行批量生成阶段背景图。

#### 依赖安装

```bash
pip install requests python-dotenv openai
```

#### 环境变量

在 `.claude/skills/.env` 中配置:
```bash
LLM_API_KEY=sk-xxx          # Polymas API Key（必需）
LLM_API_URL=https://llm-service.polymas.com/api/openai/v1  # 可选，有默认值
LLM_MODEL=Doubao-1.5-pro-32k  # 可选，用于生成提示词
```

#### 参数说明

| 参数 | 缩写 | 默认值 | 说明 |
|------|------|--------|------|
| `markdown_file` | — | *必需* | 训练剧本配置 Markdown 文件路径 |
| `--output-dir` | `-o` | 剧本同级 `backgrounds/` | 输出目录 |
| `--model` | `-m` | `doubao-seedream-3-0-t2i-250415` | 文生图模型名称 |
| `--size` | `-s` | `512x288` | 图片尺寸（16:9，范围256-768） |
| `--style` | — | 写实中国风 | 风格描述后缀，附加到每个阶段提示词末尾 |
| `--text-model` | — | 从.env读取 | 文本模型，用于智能生成提示词 |
| `--no-llm-prompt` | — | `false` | 跳过LLM生成，直接硬拼提示词 |
