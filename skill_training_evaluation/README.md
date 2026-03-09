# 智能体评估工具

使用 LLM 对教学智能体的对话质量进行评测。

## 文件结构

```
skill_training_evaluation/
├── main.py          # 主入口
├── evaluator.py     # LLM 评测核心逻辑
├── config.py        # 维度配置（从 prompts.json 动态读取）
├── types_def.py     # 数据类定义
├── file_parsers.py  # 文件解析器
├── utils.py         # LLM 工具函数
├── txt_converter.py # TXT 对话记录解析
├── prompts.json     # 提示词模板（核心配置）
└── .env             # 环境变量配置
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

创建 `.env` 文件：

```bash
LLM_API_KEY=your-api-key
LLM_API_URL=https://api.example.com/v1/chat/completions
LLM_MODEL=gpt-4o
```

### 3. 配置提示词

编辑 `prompts.json`，按以下格式配置各维度的提示词：

```json
{
  "目标达成度": {
    "知识点覆盖率": "提示词模板，支持 ${teacherDoc} 和 ${dialogueText} 占位符...",
    "能力覆盖率": "..."
  },
  "流程遵循度": {
    "环节准入条件": "...",
    "环节内部顺序": "..."
  }
}
```

### 4. 运行评测

```bash
# 交互式运行
python main.py

# 命令行参数
python main.py \
  --teacher-doc 教师文档.md \
  --dialogue-record 对话记录.txt \
  --output report.json
```

## 评测维度

维度配置从 `prompts.json` 动态读取。默认支持以下维度：

| 维度 | 权重 | 说明 |
|------|------|------|
| 目标达成度 | 20% | 一票否决项，低于阈值直接不合格 |
| 流程遵循度 | 20% | 环节流转和顺序检查 |
| 交互体验性 | 20% | 语言风格和自然度 |
| 幻觉与边界 | 20% | 事实正确性和安全边界 |
| 教学策略 | 20% | 加分项，教学技巧评估 |

## 输出格式

评估报告 JSON 示例：

```json
{
  "task_id": "任务ID",
  "total_score": 85.5,
  "final_level": "良好",
  "pass_criteria_met": true,
  "dimensions": [...],
  "issues": ["关键问题列表"],
  "suggestions": ["优化建议"],
  "evaluated_at": "2026-01-14T00:00:00"
}
```

## 等级标准

| 总分 | 等级 |
|------|------|
| >= 90 | 优秀 |
| 75-89 | 良好 |
| 60-74 | 合格 |
| < 60 | 不合格 |
| 一票否决 | 目标达成度低于阈值 |
