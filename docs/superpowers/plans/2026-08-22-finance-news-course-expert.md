# 财经新闻课程点评专家实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use subagent-driven-development or executing-plans task-by-task. Every production script follows test-driven-development.

**Goal:** 交付可上传的 `finance-news-course-commentary` Polymas Skill ZIP，以及可直接配置到既有“财经新闻推送专家”的专家配置、订阅/Cron/互动工作流和部署验收说明。

**Architecture:** 现有专家作为唯一可见入口；平台通用工具负责公开网新闻召回，知识检索助手和学生课程能力负责课程证据，新增 Skill 负责确定性清洗、去重、课程证据门禁、教学点评契约与输出。学生首次调用时自行选择一门课程及推送计划，Cron 负责个人任务，channel-message 只向唯一学生会话投递。

**Tech Stack:** Markdown Skill 契约、Python 3 标准库、pytest、zipfile、Polymas PDS 专家配置。

## Global Constraints

- 不硬编码课程；一份订阅只绑定学生选择的一门可访问课程。
- 学生必须通过 `ask_user_question` 选择课程、频率、星期、时间、时区、财经主题并确认订阅。
- 默认财经主题为综合财经，但具体计划由学生填写；每期最多 3 条。
- 不使用外部 API Key、登录 Cookie、付费账户、实时行情或绕过付费墙。
- 新闻事实、课程依据、理论分析、讨论问题必须分栏；无课程证据的新闻不得生成课程点评。
- 任务键固定为 `finance-news:{schoolId}:{userId}:{courseId}`；不得包含会话 ID。
- 个人会话无法唯一定位时停止，不降级到班级群。
- 只有 channel-message 返回成功后才更新 `last_success_at` 和发送历史。
- 所有 Cron 操作显式传 `--agent-id`；重复订阅不得创建第二个活动任务。
- 发送前重新校验订阅状态、任务版本、课程、目标会话和触发任务身份。
- 财经内容仅用于课程学习，不构成投资建议。

---

### Task 1: 确定性候选清洗与版本化简报脚本

**Files:**
- Create: `polymas_v5/polymas-finance-news-expert/finance-news-course-commentary/scripts/normalize_candidates.py`
- Create: `polymas_v5/polymas-finance-news-expert/tests/test_normalize_candidates.py`

**Interfaces:**
- CLI: `python3 scripts/normalize_candidates.py --input <json> --since <ISO8601> --until <ISO8601> --edition-date YYYY-MM-DD --max-items 3`
- 输入 JSON 顶层为 `{"course": {...}, "candidates": [...]}`。
- 候选必含 `title,url,source,published_at,fact_summary,theory_analysis,discussion_question,theory_citations`。
- `theory_citations` 每项必含 `course_name,knowledge_point,resource_title,excerpt`。
- stdout 只输出单个 JSON；错误输出 `{"error":"..."}`，退出码非 0。
- 输出含 `status,edition_id,course,items,rejected`；`item_id` 格式 `FYYYYMMDD-01`。

- [ ] **Step 1:** 先写测试，覆盖追踪参数 URL 规范化、重复 URL、相似标题聚类、时间窗、无效 URL、来源层级、缺课程证据、最多三条、稳定 item ID、投资建议禁语和 JSON-only CLI。
- [ ] **Step 2:** 运行 `python -m pytest -q polymas_v5/polymas-finance-news-expert/tests/test_normalize_candidates.py`，确认因脚本不存在而失败。
- [ ] **Step 3:** 用 Python 标准库实现最小代码；不发网络请求，不读取环境凭证。
- [ ] **Step 4:** 运行定向测试并确认通过。
- [ ] **Step 5:** 提交 `feat: add finance news candidate normalizer`。

### Task 2: 创建 Polymas 领域 Skill 包

**Files:**
- Create: `polymas_v5/polymas-finance-news-expert/finance-news-course-commentary/SKILL.md`
- Create: `polymas_v5/polymas-finance-news-expert/finance-news-course-commentary/references/data-contract.md`
- Create: `polymas_v5/polymas-finance-news-expert/finance-news-course-commentary/references/source-policy.md`
- Create: `polymas_v5/polymas-finance-news-expert/finance-news-course-commentary/output_format/briefing.md`
- Create: `polymas_v5/polymas-finance-news-expert/tests/test_skill_package.py`

**Interfaces:**
- Skill 名固定 `finance-news-course-commentary`，description 以 `Use when` 开头。
- 必需章节：技能说明、触发/不触发、项目结构、执行流程、暂停确认规则、执行流程强制约束。
- 调用顺序：学生教学计划/学习资源 → 平台通用工具公开网检索 → 知识检索助手课程证据 → normalizer → briefing。
- 公开来源采用三级策略：监管/政府/交易所/公司公告；权威财经媒体；其他公开页面仅作线索。
- 课程证据不足时减少条数；全部不足输出 `skipped_no_course_evidence`。
- Skill 不创建 Cron、不调用 channel-message、不保存订阅。

- [ ] **Step 1:** 先写包结构和契约测试并确认因文件缺失而失败。
- [ ] **Step 2:** 写最小 `SKILL.md`、数据合同、来源策略和展示模板。
- [ ] **Step 3:** 运行包测试及 `quick_validate.py`。
- [ ] **Step 4:** 用独立代理完成真实场景 forward-test，修正已观察到的流程偏差。
- [ ] **Step 5:** 提交 `feat: add finance news course commentary skill`。

### Task 3: 专家配置、订阅工作流与可上传 ZIP

**Files:**
- Create: `polymas_v5/polymas-finance-news-expert/EXPERT_CONFIG.md`
- Create: `polymas_v5/polymas-finance-news-expert/DEPLOYMENT.md`
- Create: `polymas_v5/polymas-finance-news-expert/scripts/package_skill.py`
- Create: `polymas_v5/polymas-finance-news-expert/tests/test_expert_bundle.py`
- Create: `polymas_v5/polymas-finance-news-expert/finance-news-course-commentary.zip`

**Interfaces:**
- 保留专家名“财经新闻推送专家”和昵称“财讯小信使”，补齐描述和完整 Agent.md。
- 精确挂载：新领域 Skill、平台通用工具 0.0.4、知识检索助手 1.0.1、学生班课查询 1.0.1、学生教学计划查询 1.0.0、学生学习资源助手 1.0.0、cron 0.0.1、channel-message 0.0.1。
- 首次订阅、定时生成/投递、展开某条新闻、修改课程/计划、暂停/恢复/退订分别有明确路由。
- 订阅记录包含 `status,course,topics,schedule,timezone,consent_at,job_key,plan_version,cron_job_id,target_session_id,last_success_at,next_run_at`。
- 打包脚本只收录 Skill 目录内必要文件，排序固定，排除隐藏文件、缓存、测试和凭证。

- [ ] **Step 1:** 先写专家字段、工作流、技能清单、Cron/会话安全和 ZIP 内容测试，确认失败。
- [ ] **Step 2:** 写专家配置和部署说明；不得在测试或文档中写真实身份 ID、Token、Cookie。
- [ ] **Step 3:** 实现确定性 ZIP 打包并生成上传包。
- [ ] **Step 4:** 运行全部财经专家测试、quick validator、ZIP 内容检查和 `git diff --check`。
- [ ] **Step 5:** 提交 `feat: package finance news course expert`。

### Task 4: 全分支审查与平台联调准备

**Files:**
- Review all files under `polymas_v5/polymas-finance-news-expert/`.

- [ ] **Step 1:** 独立审查规格符合度、代码质量、隐私、投资建议边界、Cron 竞态与错投风险。
- [ ] **Step 2:** 修复全部 Critical/Important 问题并重新审查。
- [ ] **Step 3:** 重跑财经专家全部测试并记录仓库既有 12 项基线失败。
- [ ] **Step 4:** 保持线上 PDS 不变；上传、绑定和保存前向用户进行动作时确认。
