---
name: training-background-generator
description: 根据能力训练剧本 Markdown 批量生成阶段背景图和任务封面，优先使用项目 secrets.json 配置的生图服务，保存图片并回填剧本路径。适用于生成训练背景图、阶段场景图片或任务封面。
allowed-tools: Read, Bash, Write
---

# 训练阶段背景图生成器

读取训练剧本，生成与阶段场景相符的写实宽屏背景图，保存到本地并回填 Markdown。

## 凭证与模型选择

默认读取 `/Users/zhangyichi/工作/能力训练/secrets.json`：

- 生图主配置使用 `providers.image` 的 `url`、`api_key`、`model`、`size`，即 Polymas 网关；当前为 `gpt-image-2`、`2560x1440`，实际以文件内容为准。同一网关还可用 `gpt-image-2.5-flare`、`gpt-image-2.5-sunburst`，需要时用 `--model` 指定。
- 备用配置为同组 `fallback_url`、`fallback_api_key`、`fallback_model`，即火山方舟 Seedream 5.0 Pro。调用时会关闭水印。
- 提示词生成使用 `providers.llm` 的 `url`、`api_key`、`model`。
- CLI 的 `--model`、`--size`、`--text-model` 可覆盖模型或尺寸。普通 `--model` 覆盖仍使用主端点。主服务某张图失败时，这张图自动改用备用服务重试一次；明确指定 `providers.image.fallback_model` 时，直接使用备用端点和 Key，不再回退。
- 默认文件不存在或未配置对应 provider 时，兼容 `.claude/skills/.env`、项目根 `.env` 中的 `BAILIAN_API_KEY`。旧生图模式为 DashScope 原生接口、`qwen-image-2.0-pro`、`1664x928`；旧文本模型读取 `BAILIAN_TEXT_MODEL`，缺省为 `qwen3.7-plus`。
- 显式指定的凭证文件不存在、JSON 损坏或生图配置不完整时直接报错，先修复配置。

凭证仅在运行时读取。只查看必要字段，文档、日志和生成台账均不复制 Key，也不输出整个 secrets 文件。

## 操作流程

1. 读取剧本，确认存在 `### 阶段N:` 或 `### 阶段N：` 标题；背景描述来自阶段描述、场景配置，也支持 Pro 的 `**卡片描述**`、`**背景图描述**`。
2. 使用下面的脚本生成图片，无需另外实现接口调用：

```bash
cd /Users/zhangyichi/工作/能力训练
python .claude/skills/training-background-generator/scripts/generate_background.py "<训练剧本配置.md路径>"
```

3. 检查 `generation_record.json` 的 `cover`、`success`、`failed`，确认本地图片和剧本路径已写入。逐项报告成功与失败；脚本退出不代表所有图片都成功。

脚本会根据阶段上下文生成约 100～200 字的中文场景提示词，并追加风格后缀；默认强调环境、光线、物体和氛围，避免把人物动作或对话直接当背景。提示词生成失败时使用场景描述拼接。需要特定人物或医学/工业细节时，应在场景描述中明确要求，并检查图片是否符合教学情境。

存在 `## 基础配置` 时，额外生成任务封面；否则只生成阶段图。接口兼容 OpenAI Images 的 URL / Base64 返回，以及 DashScope 原生图片 URL。

## 常用参数

```bash
# 使用人工写好的场景描述，跳过文本模型
python .claude/skills/training-background-generator/scripts/generate_background.py "<剧本.md>" --no-llm-prompt

# 明确覆盖尺寸和风格
python .claude/skills/training-background-generator/scripts/generate_background.py "<剧本.md>" --size 1920x1080 --style "写实摄影，自然光，16:9，不要文字或水印"

# 使用另一份同结构的凭证配置
python .claude/skills/training-background-generator/scripts/generate_background.py "<剧本.md>" --secrets-file "/path/to/secrets.json"
```

`--output-dir` / `-o` 指定输出父目录，实际写入其下的 `backgrounds_<剧本文件名>/`；未指定时写入剧本同级 `backgrounds/`。

## 输出与验收

- 阶段图片：`<剧本文件名>_stage_<编号>_<阶段名>.png`。
- 封面图片：`<任务名称>_cover.png`。
- 阶段路径回填至已有的 `**背景图**:` 字段；基础配置的背景图字段可自动添加。
- `generation_record.json` 保存主模型、备用模型、尺寸、提示词、时间、本地路径及成功/失败条目；每个成功条目的 `model` 是实际出图模型，走了备用时另记 `primary_error`。Base64 图片只存本地文件，台账中的 URL 为 `null`。
- 图片逐张生成，间隔 2 秒。主服务和备用都失败时记录两边的错误，继续其他阶段，最终按记录汇报失败原因。
- 本 Skill 完成于本地图片与路径回填；平台上传由后续导入流程处理。

依赖：`requests`、`python-dotenv`、`openai`。
