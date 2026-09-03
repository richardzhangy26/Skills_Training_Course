# 数据法学案例库专家 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在本地构建可部署到 Polymas V5 的案例库专家原型，把现有 77 个案例拆成独立结构化记录，生成固定模板 HTML，并提供学生问答与教师补库两个职责隔离的 Skill。

**Architecture:** `case-library/data/` 是唯一主数据；提取器只负责把 Word 表格转换为候选记录，发布器在校验通过后同时生成学生 HTML 和专家知识包。一个 `Agent.md` 路由两个领域 Skill：`data-law-case-query` 只读，`data-law-case-maintenance` 负责教师确认、版本化发布和失败状态；平台上传与知识蒸馏仅写为待真实联调的适配边界。

**Tech Stack:** Python 3 标准库、DOCX/XLSX OOXML、JSON Schema 风格校验、Jinja-free HTML 模板、原生 HTML/CSS/JavaScript、unittest。

**执行说明（2026-09-01）：** 工作区未提供 `pytest`，因此全部测试改用 Python 标准库 `unittest`，没有联网安装依赖。实现范围在计划基础上补齐了修改、撤下、永久删除、历史回滚、消费者版本指针一致性和候选指针失败补偿测试。PDS 当前版本核验因浏览器偏好尚未选择而保留为上线前阻断项。

## Global Constraints

- 所有开发交流、文档、测试说明和交付总结使用中文。
- 不覆盖 `ai翻转/` 中现有 DOCX、PNG 或其他用户文件。
- 不写入 Token、Cookie、Authorization、真实用户 ID 或线上凭证。
- 结构化案例数据是唯一真源；HTML 和知识包均为确定性生成物。
- 缺少争议焦点、裁判结果、案号或来源时写 `null` / `待补证`，不得模型补造。
- 发布、删除、知识写入和权限变化必须使用真实 `ask_user_question` 确认语义。
- 本阶段不上传 Skill、不绑定线上专家、不发送测试消息。
- 所有新 Python 行为遵循 RED → GREEN → REFACTOR。

---

### Task 1: 固化基线、目录边界与数据契约

**Files:**
- Create: `ai翻转/data-law-case-expert/tests/fixtures/skill-baseline.md`
- Create: `ai翻转/data-law-case-expert/data-law-case-maintenance/references/case-contract.md`
- Create: `ai翻转/data-law-case-expert/tests/test_contract.py`

**Interfaces:**
- Consumes: 两份源 DOCX 的表格/段落结构和已完成的无 Skill 基线回答。
- Produces: `validate_case(record: dict) -> list[str]` 所遵循的字段契约，以及后续测试统一使用的案例字段名。

- [ ] **Step 1: 写失败测试**

```python
def test_case_contract_rejects_fake_outcome():
    record = minimal_case(outcome="判处三年", outcome_evidence_status="missing")
    assert "outcome_requires_evidence" in validate_case(record)
```

- [ ] **Step 2: 运行测试并确认因 `validate_case` 尚不存在而失败**

Run: `python -m pytest -q ai翻转/data-law-case-expert/tests/test_contract.py`

Expected: FAIL，错误指向缺少契约实现，而不是测试语法错误。

- [ ] **Step 3: 写入最小契约实现和基线记录**

契约固定包含 `case_id/title/scene_id/record_type/jurisdiction/case_status/basic_facts/dispute_focus/legal_provisions/outcome_type/outcome/legal_analysis/sources/evidence_status/version`，并规定事实字段与证据状态的对应关系。

- [ ] **Step 4: 运行测试确认通过**

Run: `python -m pytest -q ai翻转/data-law-case-expert/tests/test_contract.py`

Expected: PASS。

### Task 2: 从 Word 确定性拆分 77 个案例

**Files:**
- Create: `ai翻转/data-law-case-expert/data-law-case-maintenance/scripts/library_core.py`
- Create: `ai翻转/data-law-case-expert/data-law-case-maintenance/scripts/extract_source_docx.py`
- Create: `ai翻转/data-law-case-expert/tests/test_extract_source_docx.py`
- Create: `ai翻转/data-law-case-expert/case-library/data/scenes.json`
- Create: `ai翻转/data-law-case-expert/case-library/data/cases/*.json`
- Create: `ai翻转/data-law-case-expert/case-library/data/manifest.json`

**Interfaces:**
- Consumes: `extract_source_docx.py SOURCE_DOCX --output-root CASE_LIBRARY`。
- Produces: 10 个场景、77 个 `DLCL-0001` 格式的独立案例 JSON 与一个 manifest。

- [ ] **Step 1: 写真实源文件测试**

```python
def test_extracts_ten_scenes_and_seventy_seven_cases(tmp_path):
    result = extract_summary(SOURCE_DOCX, tmp_path)
    assert result.scene_count == 10
    assert result.case_count == 77
    assert result.scene_case_counts == [12, 7, 5, 3, 4, 3, 3, 3, 35, 2]
```

- [ ] **Step 2: 运行测试确认提取器缺失导致失败**

Run: `python -m pytest -q ai翻转/data-law-case-expert/tests/test_extract_source_docx.py`

Expected: FAIL，缺少模块或函数。

- [ ] **Step 3: 实现 OOXML 表格读取、编号清理、稳定 ID 和缺失字段策略**

仅使用 Python 标准库读取 `word/document.xml`；第一张表读取场景，后十张表逐行读取案例。标题去除行首序号，所有推断类型写入 `classification_review_required=true`。

- [ ] **Step 4: 运行提取测试并生成初始数据**

Run: `python -m pytest -q ai翻转/data-law-case-expert/tests/test_extract_source_docx.py`

Expected: PASS，精确验证 10/77 和各场景计数。

### Task 3: 合并 4 个展开案例而不重复计数

**Files:**
- Modify: `ai翻转/data-law-case-expert/data-law-case-maintenance/scripts/extract_source_docx.py`
- Create: `ai翻转/data-law-case-expert/tests/test_merge_expanded_docx.py`
- Create: `ai翻转/data-law-case-expert/case-library/data/review-queue.json`

**Interfaces:**
- Consumes: `merge_expanded_document(expanded_docx, cases) -> MergeReport`。
- Produces: 精确标题匹配的字段补充、未匹配候选和冲突审查队列；总案例数保持 77，除非教师另行确认新增。

- [ ] **Step 1: 写失败测试**

```python
def test_expanded_cases_enrich_without_increasing_case_count(tmp_path):
    report = merge_expanded_document(EXPANDED_DOCX, extracted_cases())
    assert report.total_after_merge == 77
    assert report.matched_count >= 1
    assert all(item.status != "published" for item in report.inferred_fields)
```

- [ ] **Step 2: 运行测试确认合并器缺失导致失败**

Run: `python -m pytest -q ai翻转/data-law-case-expert/tests/test_merge_expanded_docx.py`

Expected: FAIL。

- [ ] **Step 3: 实现标题归一化、段落字段识别和待确认差异报告**

展开文档中的“案例事实/具体案情、争议焦点、涉及法律条文、法院判决或处理结果、法律问题分析”映射到契约字段；任何推测性结果进入审查队列，不覆盖已核验事实。

- [ ] **Step 4: 运行测试确认通过**

Run: `python -m pytest -q ai翻转/data-law-case-expert/tests/test_merge_expanded_docx.py`

Expected: PASS。

### Task 4: 固定模板生成离线 HTML

**Files:**
- Create: `ai翻转/data-law-case-expert/data-law-case-maintenance/scripts/render_html.py`
- Create: `ai翻转/data-law-case-expert/data-law-case-maintenance/scripts/templates/case-library.html`
- Create: `ai翻转/data-law-case-expert/tests/test_render_html.py`
- Create: `ai翻转/data-law-case-expert/case-library/exports/数据法学案例库.html`

**Interfaces:**
- Consumes: `render_library(library_root, output_html, version)`。
- Produces: 单文件、无网络依赖、内嵌发布数据的响应式 HTML。

- [ ] **Step 1: 写失败测试**

```python
def test_rendered_html_contains_all_scenes_and_cases(tmp_path):
    html = render_fixture_library(tmp_path)
    assert html.count('data-case-id="DLCL-') == 77
    assert '就业、劳动管理与跨境 HR 数据场景' in html
    assert 'type="search"' in html
    assert '待补证' in html
```

- [ ] **Step 2: 运行测试确认渲染器缺失导致失败**

Run: `python -m pytest -q ai翻转/data-law-case-expert/tests/test_render_html.py`

Expected: FAIL。

- [ ] **Step 3: 实现固定模板、内嵌安全 JSON、搜索筛选和案例详情**

视觉方向采用“法律档案室”：深靛蓝、纸张白、朱砂强调色、细网格纹理；使用系统可用中文衬线与无衬线字体回退，不访问外部 CDN。JavaScript 只读取内嵌 JSON，不允许任意 HTML 注入。

- [ ] **Step 4: 运行测试并浏览器检查桌面/移动布局**

Run: `python -m pytest -q ai翻转/data-law-case-expert/tests/test_render_html.py`

Expected: PASS；浏览器无控制台错误，搜索、场景筛选和详情切换有效。

### Task 5: 生成专家知识包和本地查询能力

**Files:**
- Create: `ai翻转/data-law-case-expert/data-law-case-maintenance/scripts/build_knowledge_pack.py`
- Create: `ai翻转/data-law-case-expert/data-law-case-query/scripts/search_cases.py`
- Create: `ai翻转/data-law-case-expert/data-law-case-query/references/retrieval-contract.md`
- Create: `ai翻转/data-law-case-expert/data-law-case-query/output_format/student-answer.md`
- Create: `ai翻转/data-law-case-expert/tests/test_search_and_knowledge_pack.py`
- Create: `ai翻转/data-law-case-expert/case-library/exports/案例专家知识包.jsonl`

**Interfaces:**
- Consumes: `build_knowledge_pack(cases) -> JSONL`；`search_cases(query, cases, limit=5)`。
- Produces: 每案例一个可追踪知识块，以及标题/场景/法条/案情的确定性候选检索。

- [ ] **Step 1: 写失败测试**

```python
def test_ambiguous_query_returns_candidates_not_one_guess():
    matches = search_cases("招聘案", library_cases(), limit=5)
    assert len(matches) > 1
    assert all(match["case_id"].startswith("DLCL-") for match in matches)
```

- [ ] **Step 2: 运行测试确认模块缺失导致失败**

Run: `python -m pytest -q ai翻转/data-law-case-expert/tests/test_search_and_knowledge_pack.py`

Expected: FAIL。

- [ ] **Step 3: 实现知识块序列化和候选排序**

检索只返回候选和证据字段，不生成法律结论；学生回答由 Skill 根据已检索字段构建，并显式区分案例事实、法条、教学分析和材料不足。

- [ ] **Step 4: 运行测试确认通过**

Run: `python -m pytest -q ai翻转/data-law-case-expert/tests/test_search_and_knowledge_pack.py`

Expected: PASS。

### Task 6: 实现教师补库的预览、确认和版本发布

**Files:**
- Create: `ai翻转/data-law-case-expert/data-law-case-maintenance/scripts/prepare_update.py`
- Create: `ai翻转/data-law-case-expert/data-law-case-maintenance/scripts/publish_update.py`
- Create: `ai翻转/data-law-case-expert/data-law-case-maintenance/references/update-state-machine.md`
- Create: `ai翻转/data-law-case-expert/data-law-case-maintenance/output_format/change-preview.md`
- Create: `ai翻转/data-law-case-expert/tests/test_update_pipeline.py`

**Interfaces:**
- Consumes: `prepare_update(candidate_records, base_version) -> ChangeSet`；`publish_update(change_set, confirmed, library_root) -> PublishResult`。
- Produces: 重复/冲突/场景歧义预览；确认后原子生成新数据快照、HTML、知识包和 manifest。

- [ ] **Step 1: 写失败测试**

```python
def test_publish_rejects_unconfirmed_and_stale_changes(tmp_path):
    change = prepare_fixture_change(base_version=1)
    assert publish_update(change, confirmed=False, library_root=tmp_path)["status"] == "awaiting_confirmation"
    assert publish_update(change, confirmed=True, library_root=stale_v2(tmp_path))["status"] == "version_conflict"
```

- [ ] **Step 2: 运行测试确认发布模块缺失导致失败**

Run: `python -m pytest -q ai翻转/data-law-case-expert/tests/test_update_pipeline.py`

Expected: FAIL。

- [ ] **Step 3: 实现暂存、差异、确认门、版本校验和回滚保留**

脚本 stdout 成功时只输出单个 JSON；失败时输出 `{"error":"可转述错误"}`。HTML 成功而知识同步未验证时返回 `artifact_ready_knowledge_pending`，绝不返回 `published`。

- [ ] **Step 4: 运行测试确认通过**

Run: `python -m pytest -q ai翻转/data-law-case-expert/tests/test_update_pipeline.py`

Expected: PASS。

### Task 7: 编写并验证两个 Polymas Skill

**Files:**
- Create: `ai翻转/data-law-case-expert/data-law-case-query/SKILL.md`
- Create: `ai翻转/data-law-case-expert/data-law-case-maintenance/SKILL.md`
- Create: `ai翻转/data-law-case-expert/tests/test_skill_contracts.py`

**Interfaces:**
- Consumes: RED 基线、检索契约、更新状态机和输出模板。
- Produces: 可独立校验、职责不重叠的两个 Skill。

- [ ] **Step 1: 把基线缺陷编码为失败断言**

```python
def test_maintenance_skill_requires_real_confirmation():
    text = MAINTENANCE_SKILL.read_text(encoding="utf-8")
    assert "[CONFIRM]" in text
    assert "ask_user_question" in text
    assert "真正等待" in text
```

- [ ] **Step 2: 运行测试确认 Skill 尚不存在而失败**

Run: `python -m pytest -q ai翻转/data-law-case-expert/tests/test_skill_contracts.py`

Expected: FAIL。

- [ ] **Step 3: 编写查询 Skill，运行应用场景复测并记录结果**

查询 Skill 固定“定位案例 → 多候选点选 → 检索字段 → 构建回答 → 一次追问”，材料缺失时返回真实缺口。

- [ ] **Step 4: 编写维护 Skill，运行应用场景复测并记录结果**

维护 Skill 固定“读取 → 拆分 → 查重 → 场景判断 → 差异预览 → `[CONFIRM]` → 发布 → 回读验证”，任何部分成功都返回真实状态。

- [ ] **Step 5: 分别运行 quick_validate 和 Skill 契约测试**

Run: `python /Users/zhangyichi/.codex/skills/.system/skill-creator/scripts/quick_validate.py <skill_dir>`

Expected: 两个 Skill 均返回验证通过。

### Task 8: 生成专家 Agent.md、配置包和推荐问题

**Files:**
- Create: `ai翻转/data-law-case-expert/Agent.md`
- Create: `ai翻转/data-law-case-expert/EXPERT_CONFIG.md`
- Create: `ai翻转/data-law-case-expert/README.md`
- Create: `ai翻转/data-law-case-expert/tests/test_expert_config.py`

**Interfaces:**
- Consumes: 两个 Skill 的精确名称、平台已有能力和未验证边界。
- Produces: 可直接粘贴到 PDS 的 Agent.md、字段内容、挂载顺序、开场白、推荐问题和真实联调清单。

- [ ] **Step 1: 写失败测试**

```python
def test_agent_routes_student_and_teacher_without_role_spoofing():
    text = AGENT_MD.read_text(encoding="utf-8")
    assert "data-law-case-query" in text
    assert "data-law-case-maintenance" in text
    assert "不能仅凭用户自称教师" in text
```

- [ ] **Step 2: 运行测试确认配置缺失导致失败**

Run: `python -m pytest -q ai翻转/data-law-case-expert/tests/test_expert_config.py`

Expected: FAIL。

- [ ] **Step 3: 按 PDS 模板编写完整 Agent.md 和配置包**

挂载列表将平台现有 Skill 版本标为“需在 PDS 当前页面核对”，不从历史表格猜版本；线上动作保持未验证状态。

- [ ] **Step 4: 运行测试确认通过**

Run: `python -m pytest -q ai翻转/data-law-case-expert/tests/test_expert_config.py`

Expected: PASS。

### Task 9: 打包、视觉 QA 与最终验证

**Files:**
- Create: `ai翻转/data-law-case-expert/scripts/package_skills.py`
- Create: `ai翻转/data-law-case-expert/tests/test_packages.py`
- Create: `ai翻转/data-law-case-expert/dist/*.zip`
- Create: `ai翻转/data-law-case-expert/VERIFICATION.md`

**Interfaces:**
- Consumes: 两个 Skill 目录、案例库数据、HTML 和专家配置。
- Produces: 无隐藏文件、缓存、测试、凭证和本地绝对路径的两个 Skill ZIP，以及验证记录。

- [ ] **Step 1: 写失败测试验证 ZIP 根目录、必需文件和敏感内容扫描**

```python
def test_skill_archives_have_one_root_and_no_secrets():
    for archive in build_archives(tmp_path):
        names = zip_names(archive)
        assert len({name.split('/')[0] for name in names}) == 1
        assert not any('__pycache__' in name or name.endswith('.pyc') for name in names)
```

- [ ] **Step 2: 运行测试确认打包器缺失导致失败**

Run: `python -m pytest -q ai翻转/data-law-case-expert/tests/test_packages.py`

Expected: FAIL。

- [ ] **Step 3: 实现确定性 ZIP 打包，打开 HTML 做桌面和移动视觉检查**

HTML 使用本地浏览器打开；检查 10 个场景、77 个案例、搜索、筛选、详情、长文本换行、键盘焦点和窄屏布局。

- [ ] **Step 4: 执行完整验证**

Run: `python -m pytest -q ai翻转/data-law-case-expert/tests`

Run: `git diff --check -- polymas_v5/ai翻转/data-law-case-expert polymas_v5/docs/superpowers/plans/2026-08-31-data-law-case-expert.md`

Expected: 所有定向测试通过，diff check 无输出；两个 ZIP 可解压且目录结构正确。
