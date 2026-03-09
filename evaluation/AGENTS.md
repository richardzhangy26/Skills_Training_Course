# EVALUATION

**Generated:** 2026-03-04

## OVERVIEW

AI对话式教学训练质量评测模块。5大维度20子维度，规则+LLM混合评测。

---

## STRUCTURE

```
evaluation/
├── __init__.py           # 模块导出
├── __main__.py           # CLI入口
├── cli.py                # 命令行接口
├── types.py              # 数据类型(Pydantic)
├── config.py             # 配置管理
├── parsers.py            # 文档解析器
├── evaluator.py          # 核心评测协调器
├── rules_evaluator.py    # 规则评测
├── llm_evaluator.py      # LLM评测
├── prompts.py            # 评测提示词模板
└── utils.py              # 工具函数
```

---

## WHERE TO LOOK

| 任务 | 文件 | 说明 |
|------|------|------|
| CLI入口 | `__main__.py` / `cli.py` | 命令行参数解析 |
| 单文件评测 | `evaluator.py:evaluate()` | 主评测函数 |
| 规则评测 | `rules_evaluator.py` | 目标达成度/流程遵循度（关键词匹配） |
| LLM评测 | `llm_evaluator.py` | 交互体验性/幻觉与边界/教学策略 |
| 解析器 | `parsers.py` | docx/md/txt对话日志解析 |

---

## CONVENTIONS

### 5维度评分结构

| 维度 | 分数 | 评测方式 | 核心指标 |
|------|------|----------|----------|
| 目标达成度 | 20 | 规则 | 知识点覆盖率 |
| 流程遵循度 | 20 | 规则 | 环节完整性、顺序正确性 |
| 交互体验性 | 20 | LLM | 人设一致性、表达自然度 |
| 幻觉与边界 | 20 | LLM | 事实正确性、未知承认 |
| 教学策略 | 20 | LLM | 启发提问、纠错引导 |

### 环境变量
```bash
EVAL_API_KEY=your-ark-api-key          # 必需
EVAL_API_URL=https://ark.cn-beijing.volces.com/api/v3  # 默认
EVAL_MODEL=doubao-1.5-pro-32k          # 默认
EVAL_MAX_CONCURRENT=3                  # 并发数
EVAL_TIMEOUT=60                        # 超时秒数
```

### 输入格式
- **教师文档**: `.docx`, `.md`, `.txt`（教学设计/任务目标）
- **对话日志**: `.json`（推荐）或 `.txt`

---

## ANTI-PATTERNS

| 禁止 | 正确做法 |
|------|----------|
| 评测输出含非JSON内容 | LLM必须只输出JSON |
| 直接复制示例评分 | 示例仅供格式参考，独立评判 |
| 忽略`quote`字段 | 必须引用实际对话原文作为证据 |
| 超并发 | 默认3并发，避免API限流 |

---

## COMMANDS

```bash
# 单文件评测（详细输出）
python -m evaluation -t 教学设计.docx -d dialogue.json -v

# 批量评测（并发）
python -m evaluation -t doc.docx -D ./logs/ -O ./reports/ --workers 3

# Python API
python -c "
import asyncio
from evaluation import evaluate, parse_teacher_doc, parse_dialogue, load_config

async def main():
    config = load_config()
    teacher = parse_teacher_doc('doc.docx')
    dialogue = parse_dialogue('log.json')
    report = await evaluate(teacher, dialogue, config)
    print(f'总分: {report.total_score}')

asyncio.run(main())
"
```

---

## NOTES

1. **等级划分**: 90-100优秀/80-89良好/60-79合格/0-59不合格
2. **批量评测**: 自动生成`batch_report_[timestamp].json`汇总
3. **并发控制**: `EVAL_MAX_CONCURRENT`控制同时评测文件数
4. **提示词位置**: `../prompts/`目录含各子维度评测模板
