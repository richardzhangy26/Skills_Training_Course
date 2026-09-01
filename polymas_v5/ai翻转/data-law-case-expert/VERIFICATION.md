# 数据法学案例库专家｜验证记录

验证日期：2026-09-01

工作分支：`codex/data-law-case-expert`

## 本地已验证范围

- 上游材料：`案例拆分文档/00_案例索引.docx` 加 77 份单案例 DOCX。
- 导入结果：10 个场景、77 个唯一案例 ID，场景计数为 `12+7+5+3+4+3+3+3+35+2`。
- 详细材料：拆分 Word 的详细案情进入标准 `basic_facts`；争议焦点、法律条文、处理结果和法律分析按材料实际存在情况写入。
- 审查队列：`DLCL-0023`、`DLCL-0024` 与 `DLCL-0034` 的处理结果属于假设性表述，未写入正式 outcome。
- 学生端：固定模板 HTML 含 77 个案例；搜索、场景筛选、类型筛选和案例详情可用。
- 教师端：新增、修改、撤下、永久删除、版本冲突、历史 ID 不复用、整库回滚和确认绑定均有自动化测试。
- 安全边界：敏感内容递归扫描、AI 草稿隔离、官方证据状态校验、批内查重、并发发布锁、回滚事务 intent、公开 HTML 审计信息隔离和 ZIP 白名单均有自动化测试。

## 自动化验证

```text
python -m unittest discover -s ai翻转/data-law-case-expert/tests -p 'test_*.py'
55 tests passed
```

两个 Skill 分别通过：

```text
quick_validate.py data-law-case-query      → Skill is valid!
quick_validate.py data-law-case-maintenance → Skill is valid!
```

数据审计结果：

```text
case_files=77
case_ids_unique=true
fact_detail_fields=0
analysis_detail_fields=0
html_case_markers=77
knowledge_lines=77
html_has_actor_reference=false
```

## 视觉与交互 QA

- 桌面视口：1440×900。
- 移动视口：390×844，无横向溢出。
- 搜索“检察机关向人社”命中 1/77 个案例，并显示拆分文档中的详细案情。
- 儿童短视频案例可展示 345 字基本案情和 687 字处理结果。
- 两轮浏览器检查均无 JavaScript 控制台错误或警告。

## ZIP 验证

| 文件 | SHA-256 | 结构 |
|---|---|---|
| `data-law-case-query-1.0.0.zip` | `c1cfe1cba46cbbaecd76962ec8b862c51dc6bc5729ab76ed42249a892289d103` | 单根目录；4 个文件 |
| `data-law-case-maintenance-1.0.0.zip` | `cda4a5a92d15bbf59dd364f90828be039942979127b0455b3c3e9a59145bffa8` | 单根目录；13 个文件 |

打包器拒绝符号链接、未知文件后缀、本机绝对路径、私钥、JWT 和带值的 Authorization/Cookie 模式；ZIP 不包含测试、缓存、隐藏文件或本地源文档。

## 尚未验证的线上能力

- 未上传两个 Skill，未创建或绑定线上专家，未发送测试消息。
- 本地能力清单没有现有平台 Skill 的版本字段；PDS 当前版本尚未核对。
- `polymas-teacher-knowledge-distillation` 是否能更新当前专家实际挂载的知识库尚未联调。
- 资源上传成功、知识写入成功、专家回读成功和回滚后回读成功仍需分别验证。
- 当前知识包状态为 `artifact_ready_knowledge_pending` / `not_verified`，不能报告“专家知识已在线更新”。
