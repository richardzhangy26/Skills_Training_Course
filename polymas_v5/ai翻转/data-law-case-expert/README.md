# 数据法学案例库专家

本目录是一个 Polymas V5 本地原型：以 77 个结构化案例为唯一主数据，生成离线 HTML 和专家知识包，并提供学生查询与教师维护两个职责隔离的 Skill。

## 目录

```text
data-law-case-expert/
├── Agent.md
├── EXPERT_CONFIG.md
├── data-law-case-query/
├── data-law-case-maintenance/
├── case-library/
│   ├── data/
│   └── exports/
├── tests/
└── dist/
```

## 从教师拆分文档生成初始案例库

在 `polymas_v5/` 目录执行：

```bash
python ai翻转/data-law-case-expert/data-law-case-maintenance/scripts/import_split_documents.py \
  ai翻转/案例拆分文档 \
  --output-root ai翻转/data-law-case-expert/case-library

python ai翻转/data-law-case-expert/data-law-case-maintenance/scripts/render_html.py \
  ai翻转/data-law-case-expert/case-library \
  ai翻转/data-law-case-expert/case-library/exports/数据法学案例库.html

python ai翻转/data-law-case-expert/data-law-case-maintenance/scripts/build_knowledge_pack.py \
  ai翻转/data-law-case-expert/case-library \
  ai翻转/data-law-case-expert/case-library/exports/案例专家知识包.jsonl
```

脚本成功时 stdout 只输出一个 JSON。它要求 `00_案例索引.docx` 与 77 份单案例 Word 完整对应；详细案情写入标准字段，推测性处理结果进入 `review-queue.json`。拆分材料仍缺少完整官方来源和部分案号，所以 77 条记录默认标记为“待补证”。

原 `案例提炼汇总.docx` 与 `AI时代一体化数字营销与法律回望.docx` 的兼容提取器仍保留，用于复核迁移差异，不再作为首选主数据入口。

## 运行测试

```bash
python3 -m unittest discover -s ai翻转/data-law-case-expert/tests -p 'test_*.py'
```

## 状态边界

- 本地结构化数据、HTML 和知识包可以生成和回滚。
- 教师变更管道支持新增、修改、撤下、永久删除和历史版本回滚；永久删除仍在旧版本和删除审计中可追踪。
- 平台资源上传、知识写入和专家回读尚未联调。
- `artifact_ready_knowledge_pending` 不是发布成功；只有 `knowledge_verified` 表示专家能够检索新版本。
- 未经用户明确授权，本目录不会上传 Skill、创建线上专家或发送测试消息。
