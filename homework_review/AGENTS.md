# HOMEWORK REVIEW

**Generated:** 2026-03-04

## OVERVIEW

AI作业批改工具。自动化上传学生作业文件，调用智能体进行批改并获取评分结果。

---

## STRUCTURE

```
homework_review/
├── homework_reviewer_v2.py    # 推荐入口（v2轮询模式）
├── homework_reviewer.py       # 旧版（同步模式）
├── report_generator.py        # PDF/JSON报告生成
├── utils/                     # 工具模块
│   ├── generate_report.py     # 报告生成器
│   ├── excel_summary.py       # Excel汇总
│   └── generate_report_exam.py # 试卷报告
└── test/                      # 测试用例
```

---

## WHERE TO LOOK

| 任务 | 文件 | 说明 |
|------|------|------|
| 批改作业 | `homework_reviewer_v2.py` | 上传→analysis.json→轮询completed |
| 生成报告 | `report_generator.py` | JSON/PDF格式报告 |
| 旧版兼容 | `homework_reviewer.py` | 同步模式（不推荐） |

---

## CONVENTIONS

### 环境变量
```bash
# 平台认证（同主项目）
AUTHORIZATION=eyJ0eXAiOiJKV1Q...
COOKIE=xxx

# 智能体实例ID（从平台URL获取）
INSTANCE_NID=xxx
```

### 输入路径格式
- **文件夹**: `/path/to/folder` → 扫描所有支持格式
- **单文件**: `/path/to/file.pdf`
- **多路径**: `/path/file1.png,/path/folder`（逗号分隔）

### 输出结构
```
输入文件夹/
└── review_results/
    ├── result_[filename].json   # 批改结果
    └── summary.xlsx             # 汇总表（批量时）
```

---

## ANTI-PATTERNS

| 禁止 | 正确做法 |
|------|----------|
| 使用旧版`homework_reviewer.py` | 改用`v2.py`（支持轮询状态） |
| 直接操作analysis.json | 通过API上传让后端处理 |
| 忽略`completed`状态 | v2版会自动轮询到完成 |

---

## COMMANDS

```bash
cd homework_review

# 推荐：v2轮询模式
python homework_reviewer_v2.py
# 提示输入路径 → 自动识别类型 → 轮询批改状态

# 旧版（不等待异步结果）
python homework_reviewer.py
```

---

## NOTES

1. **支持格式**: PDF、DOC、DOCX、PNG、JPG、JPEG、GIF
2. **智能体类型自动识别**: 题卷/语言写作/论文报告
3. **报告格式**: JSON（详细，推荐）或 PDF（美观）
4. **并发限制**: 默认单线程，避免API限流
