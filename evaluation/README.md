# AI对话式教学训练质量评测工具

用于评测AI对话式教学训练质量的Python模块，支持规则评测与LLM混合评测。

## 功能特性

- **5大维度20子维度评测**
  - 目标达成度（20分）- 规则评测
  - 流程遵循度（20分）- 规则评测
  - 交互体验性（20分）- LLM评测
  - 幻觉与边界（20分）- LLM评测
  - 教学策略（20分）- LLM评测

- **多格式支持**
  - 教师文档：.docx, .md, .txt
  - 对话日志：.json, .txt

- **批量评测**：支持目录批量评测，并发执行

## 安装依赖

```bash
pip install python-docx pydantic python-dotenv httpx
```

## 环境变量配置

创建 `.env` 文件：

```bash
# 必需
EVAL_API_KEY=your-ark-api-key

# 可选（使用默认值）
EVAL_API_URL=https://ark.cn-beijing.volces.com/api/v3
EVAL_MODEL=doubao-1.5-pro-32k
EVAL_MAX_CONCURRENT=3
EVAL_TIMEOUT=60
```

## 使用方式

### 命令行使用

**单文件评测：**
```bash
python -m evaluation \
  --teacher-doc 教学设计.docx \
  --dialogue dialogue.json \
  --output report.json \
  --verbose
```

**批量评测：**
```bash
python -m evaluation \
  --teacher-doc 教学设计.docx \
  --dialogue-dir ./logs/ \
  --output-dir ./reports/ \
  --workers 3
```

**简写形式：**
```bash
python -m evaluation -t doc.docx -d log.json -v
python -m evaluation -t doc.docx -D ./logs/ -O ./reports/
```

### Python API使用

```python
import asyncio
from evaluation import (
    parse_teacher_doc,
    parse_dialogue,
    evaluate,
    load_config,
)

async def main():
    # 加载配置
    config = load_config()

    # 解析文档
    teacher_doc = parse_teacher_doc("教学设计.docx")
    dialogue_data = parse_dialogue("dialogue.json")

    # 执行评测
    report = await evaluate(teacher_doc, dialogue_data, config)

    # 查看结果
    print(f"总分: {report.total_score}")
    print(f"等级: {report.level}")
    for dim in report.dimensions:
        print(f"{dim.name}: {dim.score}/{dim.full_score}")
    print(f"总结: {report.summary}")

    # 保存报告
    from evaluation.utils import save_json_report
    save_json_report(report, "report.json")

if __name__ == "__main__":
    asyncio.run(main())
```

## 输出格式

### 单个评测报告

```json
{
  "task_id": "task_xxx",
  "total_score": 85,
  "level": "良好",
  "dimensions": [
    {"name": "目标达成度", "score": 18, "full_score": 20, "details": "..."},
    {"name": "流程遵循度", "score": 19, "full_score": 20, "details": "..."},
    {"name": "交互体验性", "score": 16, "full_score": 20, "details": "..."},
    {"name": "幻觉与边界", "score": 17, "full_score": 20, "details": "..."},
    {"name": "教学策略", "score": 15, "full_score": 20, "details": "..."}
  ],
  "summary": "整体表现良好，教学目标基本达成...",
  "evaluated_at": "2026-03-03T12:00:00",
  "dialogue_file": "dialogue.json"
}
```

### 批量评测报告

```json
{
  "batch_summary": {
    "total_files": 10,
    "success_count": 10,
    "failed_count": 0,
    "avg_score": 82.5,
    "score_distribution": {
      "优秀": 3,
      "良好": 5,
      "合格": 2,
      "不合格": 0
    }
  },
  "individual_reports": [...]
}
```

## 等级划分

| 总分 | 等级 |
|------|------|
| 90-100 | 优秀 |
| 80-89 | 良好 |
| 60-79 | 合格 |
| 0-59 | 不合格 |

## 文件结构

```
evaluation/
├── __init__.py          # 模块导出
├── __main__.py          # 命令行入口
├── cli.py               # 命令行接口
├── types.py             # 数据类型定义
├── config.py            # 配置管理
├── parsers.py           # 文件解析器
├── evaluator.py         # 核心评测协调器
├── rules_evaluator.py   # 规则评测模块
├── llm_evaluator.py     # LLM评测模块
├── prompts.py           # 提示词模板
└── utils.py             # 工具函数
```

## 评测逻辑说明

### 规则评测（目标达成度、流程遵循度）

- **知识点覆盖率**：通过关键词匹配计算对话中提及的知识点比例
- **环节完整性**：检查对话是否经历教师文档中定义的教学环节
- **顺序正确性**：检查教学环节是否按预定顺序进行

### LLM评测（交互体验性、幻觉与边界、教学策略）

使用大语言模型对以下维度进行评测：
- 人设语言风格、表达自然度、上下文衔接
- 事实正确性、逻辑自洽性、未知承认
- 启发式提问频率、正向激励机制、纠错引导路径

LLM评测需要配置API密钥，支持OpenAI兼容的API（如Doubao、DeepSeek）。
