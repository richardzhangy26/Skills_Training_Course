---
name: training-background-generator
description: 为能力训练剧本生成阶段背景图和任务封面，使用项目 secrets.json 的生图配置。此入口转向项目统一维护的背景图生成 Skill。
---

# 训练背景图生成入口

此目录保留为兼容入口。生成能力训练背景图时，先读取并遵循 [统一 Skill](../.claude/skills/training-background-generator/SKILL.md)，运行其 `scripts/generate_background.py`。

默认凭证文件为 `/Users/zhangyichi/工作/能力训练/secrets.json`，生图优先使用 `providers.image` 主配置。接口、模型、尺寸、备用服务选择和生成记录格式均以统一 Skill 为准。
