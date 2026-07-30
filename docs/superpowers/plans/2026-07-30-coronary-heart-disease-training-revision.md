# 冠心病中西医结合诊疗能力训练修改 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 安全、可回滚地定点修改普通能力训练任务 `gbxP2ro08oh4L66KpaVQ`，落实 7 月 24 日教师意见，并用三病例回归验证修改结果。

**Architecture:** 复用 `create_task_from_markdown.py` 的鉴权、步骤查询和完整步骤编辑载荷，新建本任务专用更新器。更新器先读取任务配置、27 个节点、28 条流程边和 5 个评分项并落盘备份，再以真实 Step ID 和更新前节点名双重校验构建补丁；默认仅预演，只有显式 `--apply` 才写平台。内容修改采用纯函数生成，远程写入通过可注入网关隔离，便于测试。

**Tech Stack:** Python 3、requests、pytest、Pillow、Polymas 普通能力训练 API。

## Global Constraints

- 目标任务 ID 固定为 `gbxP2ro08oh4L66KpaVQ`，不得接受其他任务 ID。
- 必须以线上真实 Step ID 为主键，节点名为写入前置校验；禁止按 API 返回顺序 `zip()`。
- 默认 dry-run；仅显式 `--apply` 允许远程写入。
- 写入前必须备份基础配置、全部步骤、全部流程边和全部评分项，备份不得包含 Authorization、Cookie 或其他请求头。
- 不整体导入 `训练剧本配置_三选一路由版.md`，不改动路由结构。
- 步骤编辑保留位置、数字人、音色、头像、知识库和既有资源，只修改设计明确列出的字段。
- 任务名精确改为“冠心病的中西医结合诊疗模拟训练”。
- 三个治疗节点统一命名为“中西医结合治疗方案”。
- 评价标准总分固定为 100，五项分值固定为 `10 / 20 / 20 / 20 / 30`。
- 平台生成的“（AI生成）”标签不在本次脚本中处理。

---

### Task 1: 定点更新安全内核

**Files:**
- Create: `skill_training_build/update_coronary_heart_disease_task.py`
- Create: `tests/test_update_coronary_heart_disease_task.py`
- Create: `tests/fixtures/coronary_heart_disease/live_snapshot_sanitized.json`

**Interfaces:**
- Consumes: `create_task_from_markdown.load_env_config()`、`get_headers()`、`ability_train_url()`、`build_edit_script_step_payload()`。
- Produces: `AbilityTrainGateway`、`export_task_snapshot()`、`write_backup()`、`build_update_plan()`、`execute_update_plan()`。

- [ ] **Step 1: 写失败测试，证明默认预演不产生平台写入**

```python
def test_default_run_is_dry_run_and_performs_no_platform_mutation(tmp_path):
    gateway = FakeGateway(load_fixture_snapshot())
    report = run_coronary_update(gateway, backup_dir=tmp_path)
    assert report["dry_run"] is True
    assert gateway.mutations == []
```

- [ ] **Step 2: 运行测试并确认 RED**

Run: `pytest -q tests/test_update_coronary_heart_disease_task.py::test_default_run_is_dry_run_and_performs_no_platform_mutation`

Expected: 因目标模块或函数尚不存在而失败。

- [ ] **Step 3: 写失败测试，证明错序列表仍按 Step ID 匹配**

```python
def test_plan_matches_by_step_id_not_api_order():
    snapshot = load_fixture_snapshot()
    snapshot["steps"].reverse()
    plan = build_update_plan(snapshot)
    assert [item["stepId"] for item in plan["steps"]] == EXPECTED_TARGET_STEP_IDS
```

- [ ] **Step 4: 写失败测试，证明节点名漂移会在写入前中止**

```python
def test_mismatched_expected_name_aborts_before_mutation(tmp_path):
    snapshot = load_fixture_snapshot()
    target = next(s for s in snapshot["steps"] if s["stepId"] == CASE1_INFO_STEP_ID)
    target["stepDetailDTO"]["stepName"] = "已被他人改名"
    gateway = FakeGateway(snapshot)
    with pytest.raises(PreflightError, match=CASE1_INFO_STEP_ID):
        run_coronary_update(gateway, backup_dir=tmp_path, apply=True)
    assert gateway.mutations == []
```

- [ ] **Step 5: 写最小安全内核**

实现只接受固定任务 ID 的网关、四类查询、JSON 备份、Step ID 映射、名称校验、默认 dry-run 和 `--apply` 开关。`write_backup()` 必须在任何网关写方法之前完成。

- [ ] **Step 6: 运行安全内核测试并确认 GREEN**

Run: `pytest -q tests/test_update_coronary_heart_disease_task.py -k 'dry_run or api_order or mismatched_expected_name or backup'`

Expected: 全部通过，0 failure。

### Task 2: 教师意见内容补丁

**Files:**
- Modify: `skill_training_build/update_coronary_heart_disease_task.py`
- Modify: `tests/test_update_coronary_heart_disease_task.py`

**Interfaces:**
- Consumes: Task 1 的 Step ID 定点计划。
- Produces: `build_target_configuration()`、`build_target_step()`、`build_target_score_items()`。

- [ ] **Step 1: 写病例一失败测试**

断言目标内容同时满足：

```python
assert "西医与中医初步考虑什么诊断？" in case1_info_prompt
assert "干湿性啰音" in case1_exam_prompt
assert "患者需要做哪些辅助检查" in case1_aux_prompt
assert "CK-MB 18 U/L" in case1_aux_prologue
assert "肌钙蛋白I 0.02 ng/mL" in case1_aux_prologue
assert "分析合理" in case1_aux_prologue
assert "中医治则、主方、具体药物组成" in case1_treatment_prompt
assert "西医治疗原则、具体药物" in case1_treatment_prompt
assert case1_treatment_name == "中西医结合治疗方案"
assert "接下来" in case1_exam_prologue
```

- [ ] **Step 2: 写病例二失败测试**

断言信息补充节点不再规划辅助检查，开场含“下面进入信息补充”；辅助检查节点先问检查项目；诊断节点将“中医病名、证型、辨证依据”设为三个不可跳过的独立必答项；反馈不得包含“锁定不稳定型心绞痛”等替学生下结论的句子。

- [ ] **Step 3: 写病例三失败测试**

断言所有学生可见检查数值带单位；完整体检仍位于第一次问题前；硝酸甘油题干和参考答案与教师原文一致；治疗节点分别强制中医三项和西医两项。

- [ ] **Step 4: 写总结节点失败测试**

三个总结节点均必须先包含“标准答案”，再包含“总分：__/100”“问诊与危险信息采集”“体格检查与辅助检查”“西医诊断及依据”“中医病名、证型与辨证依据”“中西医结合治疗方案”和“扣分原因”；不得以单独的“优秀／良好／需改进”作为最终输出。

- [ ] **Step 5: 实现最小内容补丁**

以当前线上步骤深拷贝为基础，仅修改 `stepName`、`prologue`、`llmPrompt`；每条文本替换记录预期出现次数，数量不符即抛出 `PreflightError`。对防泄题、独立必答和总结格式使用带唯一标记的强制覆盖块，明确其优先级高于旧示例。

- [ ] **Step 6: 运行内容测试并确认 GREEN**

Run: `pytest -q tests/test_update_coronary_heart_disease_task.py -k 'case1 or case2 or case3 or summary'`

Expected: 全部通过，0 failure。

### Task 3: 基础配置与三病例评价标准

**Files:**
- Modify: `skill_training_build/update_coronary_heart_disease_task.py`
- Modify: `tests/test_update_coronary_heart_disease_task.py`

**Interfaces:**
- Consumes: 线上 `queryConfiguration` 和 `queryScoreItemList` 返回。
- Produces: 完整 `editConfiguration`、`editScoreItem` 载荷；保持原 itemId。

- [ ] **Step 1: 通过浏览器 Network 或前端保存动作核实两个编辑请求体**

记录 `editConfiguration` 和 `editScoreItem` 的实际字段，不猜测接口协议；若无法核实，基础配置和评分改用平台 UI 保存，步骤仍由脚本更新。

- [ ] **Step 2: 写失败测试**

```python
def test_score_plan_is_branch_aware_and_totals_100():
    items = build_target_score_items(load_fixture_snapshot()["scoreItems"])
    assert [item["score"] for item in items] == [10, 20, 20, 20, 30]
    assert sum(item["score"] for item in items) == 100
    assert all("按当前进入的病例" in item["requireDetail"] for item in items)
```

- [ ] **Step 3: 实现基础配置和评分载荷**

基础配置只改变任务名；五个评分项改为：

1. 问诊与危险信息采集 10 分。
2. 体格检查与辅助检查 20 分。
3. 西医诊断及依据 20 分。
4. 中医病名、证型与辨证依据 20 分。
5. 中西医结合治疗方案 30 分。

每项要求根据当前病例选择稳定型心绞痛、痰湿内阻不稳定型心绞痛或气虚血瘀急性心肌梗死的标准答案，并明确记录扣分原因。

- [ ] **Step 4: 运行评分测试并确认 GREEN**

Run: `pytest -q tests/test_update_coronary_heart_disease_task.py -k 'configuration or score'`

Expected: 全部通过，0 failure。

### Task 4: 病例三复合检查报告图

**Files:**
- Create: `skill_training_build/generate_coronary_case3_exam_report.py`
- Create: `tests/test_generate_coronary_case3_exam_report.py`
- Create: `skills_training_course/湖南中医药大学-冠心病的中西医结合诊疗/辅助检查图片/病例三_辅助检查报告.png`

**Interfaces:**
- Consumes: 教师确认的病例三检查结果。
- Produces: 16:9 PNG，供病例三辅助检查节点上传或作为节点背景。

- [ ] **Step 1: 写失败测试**

断言输出为 1920×1080 PNG，且生成函数的结构化数据包含 ECG、肌钙蛋白 I `12.6 ng/mL`、CK-MB `85 U/L`、四项血脂单位和冠脉造影“左前降支近段完全闭塞”。

- [ ] **Step 2: 运行并确认 RED**

Run: `pytest -q tests/test_generate_coronary_case3_exam_report.py`

Expected: 因生成模块不存在而失败。

- [ ] **Step 3: 使用 Pillow 生成精确文字版检查报告**

采用白底医疗报告卡片布局，不使用生成式模型绘制数字或文字；所有医学数值以代码常量渲染，避免文字幻觉。

- [ ] **Step 4: 运行测试并视觉检查**

Run: `pytest -q tests/test_generate_coronary_case3_exam_report.py && python skill_training_build/generate_coronary_case3_exam_report.py`

Expected: 测试通过并生成 1920×1080 PNG；人工查看无文字截断、无错误单位。

### Task 5: 预演、备份和线上写入

**Files:**
- Create at runtime: `skills_training_course/湖南中医药大学-冠心病的中西医结合诊疗/platform_backups/<timestamp>/snapshot.json`
- Create at runtime: `skills_training_course/湖南中医药大学-冠心病的中西医结合诊疗/platform_backups/<timestamp>/update_plan.json`

**Interfaces:**
- Consumes: Task 1–4 的更新器、内容计划和图片。
- Produces: 平台配置变更及本地审计证据。

- [ ] **Step 1: 运行完整测试**

Run: `pytest -q tests/test_update_coronary_heart_disease_task.py tests/test_generate_coronary_case3_exam_report.py tests/test_create_task_from_markdown_update_existing.py`

Expected: 0 failure。

- [ ] **Step 2: 运行 dry-run**

Run: `python skill_training_build/update_coronary_heart_disease_task.py`

Expected: 输出固定任务 ID、真实 Step ID、更新前后差异和备份路径；远端写入计数为 0。

- [ ] **Step 3: 人工复核 update_plan.json**

确认只包含任务名、19 个教师意见相关节点、5 个评分项；流程更新数为 0。

- [ ] **Step 4: 显式执行**

Run: `python skill_training_build/update_coronary_heart_disease_task.py --apply`

Expected: 基础配置、目标步骤、评分项逐项成功；任一失败立即停止。

- [ ] **Step 5: 通过平台 UI 上传病例三检查报告图**

将 `病例三_辅助检查报告.png` 绑定到病例三“辅助检查与解读”节点；若资源面板不能稳定呈现，则设置为该节点背景，文本结果仍保留完整单位。

### Task 6: 写后回查与三病例回归

**Files:**
- Create at runtime: `skills_training_course/湖南中医药大学-冠心病的中西医结合诊疗/platform_backups/<timestamp>/verification.json`
- Create at runtime: `skills_training_course/湖南中医药大学-冠心病的中西医结合诊疗/platform_backups/<timestamp>/case1-dialogue.json`
- Create at runtime: `skills_training_course/湖南中医药大学-冠心病的中西医结合诊疗/platform_backups/<timestamp>/case2-dialogue.json`
- Create at runtime: `skills_training_course/湖南中医药大学-冠心病的中西医结合诊疗/platform_backups/<timestamp>/case3-dialogue.json`

**Interfaces:**
- Consumes: 写入后的平台配置。
- Produces: 字段级回查和三个真实分支的对话证据。

- [ ] **Step 1: 重新读取四类配置**

按任务名、目标 Step ID、五项评分和 28 条原流程边生成字段级校验；流程边必须与备份一致。

- [ ] **Step 2: 运行病例一**

验证辅助检查先问后给、单位完整、治疗六项必答、总结先标准答案后数字评分。

- [ ] **Step 3: 运行病例二**

验证患者不朗读跳转词、年轻医生说“下面进入信息补充”、体格检查先于辅助检查、中医三项缺一不得跳过。

- [ ] **Step 4: 运行病例三**

验证完整体检先于问题、图片可见、单位完整、硝酸甘油题与参考答案一致、治疗五项必答。

- [ ] **Step 5: 形成验收结论**

只在字段回查、图片检查和三病例对话证据均满足设计清单后宣布完成；如发现模型仍自问自答，依据日志中的具体节点继续做最小提示词补丁，不覆盖其他节点。
