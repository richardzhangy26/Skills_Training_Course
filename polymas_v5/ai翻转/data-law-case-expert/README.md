# 数据法学案例库专家

本目录是一个 Polymas V5 本地原型：以 77 个结构化案例为唯一主数据，生成离线 HTML 和专家知识包，并提供学生查询与教师维护两个职责隔离的 Skill。

## 教师个人助教专家团验收

已配置好的 AI 助教可通过 `test_expert_team.py` 或 `python -m team_acceptance run` 执行教师侧测试：读取配置、发送只读用例、判定 SSE 终态、独立回读历史并输出 Markdown/JSON 报告。无需重新发布专家。参数、示例配置、已验证协议及使用边界见 [专家团验收说明](team_acceptance/README.md)。该入口的真实对话结果与下文旧发布/回滚框架的 synthetic 结果分别报告。

2026-09-05 已实跑法学测试助教与数据法学案例专家两条用例：两条均完成发送和回读，业务断言一条通过、一条未通过。精确案例查询失败涉及知识源与检索依赖不可用，不能据此宣称专家全部功能验收通过。

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
  --output-root ai翻转/data-law-case-expert/case-library-bootstrap

python ai翻转/data-law-case-expert/data-law-case-maintenance/scripts/render_html.py \
  ai翻转/data-law-case-expert/case-library-bootstrap \
  ai翻转/data-law-case-expert/case-library-bootstrap/exports/数据法学案例库.html

python ai翻转/data-law-case-expert/data-law-case-maintenance/scripts/build_knowledge_pack.py \
  ai翻转/data-law-case-expert/case-library-bootstrap \
  ai翻转/data-law-case-expert/case-library-bootstrap/exports/案例专家知识包.jsonl
```

脚本成功时 stdout 只输出一个 JSON。它仅初始化空目录，拒绝覆盖已有 `case-library`；已有库的材料更新必须走变更预览、确认和版本发布。它要求 `00_案例索引.docx` 与 77 份单案例 Word 完整对应；详细案情写入标准字段，推测性处理结果进入 `review-queue.json`。77 条初始记录为“已发布＋证据待补证”。

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

## Online E2E 编排器

`online_e2e` 把只读预检、线上快照、期望配置差异、一次性确认、发布、固定回归和清理组织为同一状态机。PDS 专家公开 NID `x3PalTZaWr`、中药材助教 NID `FEpEJws9cS` 和未来教学 runtime 标识分别建模，不互相替代。期望配置从线上完整配置克隆，只替换 `expertMd.customContent`，并按线上已观察顺序保留五个已声明 Skill；未知、缺失或重复 Skill 会阻断。

当前可安全执行 live `dry-run`。它读取当前用户、助教列表、助教与专家关系、专家完整配置和知识绑定，生成快照与差异，但不会写平台。由于专用测试助教、权威知识库目标、知识内容级快照/恢复、可信学生 transport、保存模型转换、新会话、上传、发送和教师恢复接口尚未验证，当前目标会返回 `BLOCKED / DEPENDENCY_UNVERIFIED`，不会签发确认令牌。`apply` 也会在任何平台写入前以相同原因阻断。

在本目录执行：

```bash
python -m online_e2e data-law-case-expert dry-run full \
  --run-id run-20260904-readonly \
  --env-file /absolute/path/to/polymas.env
```

env 文件必须由 `--env-file` 显式传入，至少包含 `AUTHORIZATION` 与 `COOKIE`，并且必须来自能够精确看到目标 `assistant_nid` 的同一账号。浏览器 Chrome 当前账号与 env 凭证账号不同，或该账号没有目标助教关系时，会返回 `ASSISTANT_NOT_ACCESSIBLE`；应从正确账号重新取得 AUTHORIZATION/COOKIE，不能改用名称包含、相似名称或其他模糊匹配绕过。生产 transport 只接受 `https://cloudapi.polymas.com` origin，并在发送前复核最终 URL，拒绝 path 中的 scheme/netloc、反斜杠和控制字符，避免凭证被带到外域。凭证只进入内存请求头，不进入 stdout、checkpoint 或报告。CLI 的 stdout 始终恰好一个 JSON；`--help/-h` 也只输出单个 HELP JSON，诊断写 stderr。运行 checkpoint 位于 `.online-e2e-state/`，JSON/Markdown 报告位于 `reports/online-e2e/`，两者均被 gitignore 且使用共享的 0600 原子写实现。发布前的稳定 ClientError 也会生成 BLOCKED JSON/Markdown 报告；只有 store/report 自身不可用时才由 CLI 返回无报告路径的单 JSON `INTERNAL_ERROR`。

只有所有 live 前置条件补证后，`dry-run` 才会把一次性确认令牌返回到 stdout。随后必须使用相同 `run_id` 和原令牌执行：

```bash
python -m online_e2e data-law-case-expert apply full \
  --run-id run-20260904-approved \
  --env-file /absolute/path/to/polymas.env \
  --confirmation-token '<dry-run stdout 中的令牌>'
```

`apply` 在 target 级文件锁内重新计算本地资产摘要、线上快照、隔离助教 NID、关系版本和请求计划摘要；确认签名单独绑定知识 version 与 content digest，同版本内容变化也会使旧令牌失效。令牌和 nonce 均为一次性消费。dry-run 与 apply 都精确查询本 run 的目标 `AUTO-{RUN_ID}-01/02`，目标集合和 baseline（包括显式空集合）进入计划摘要；任一目标已存在即 `FIXTURE_ID_COLLISION`，不签发令牌或发布。成功只保留新专家配置，教师双案例 fixture 和知识变更必须清理并恢复。清理同时要求已尝试教师写入、实际确认的 changeId，以及 backend 按 runId + changeId 返回的精确案例归属；当前减基线仅用于发现候选，不作为所有权证据。未开始教师写入时，只读检查原知识和案例状态；外部变化保留并报告残留。删除前 runner 与 backend 都校验知识 version+digest，删除后的知识回执必须与当前回读一致才可 restore；restore 后再次独立回读。配置与知识分别执行 CAS，第三方变化返回 `ROLLBACK_FAILED` 并保留残留状态。

首个可能写入前，target 锁内原子保存私有恢复快照与 `IN_FLIGHT` fence。若配置包含必须脱敏的字段，无法保存完整安全快照，则在写前阻断。进程崩溃后，同 target 的任何 dry-run/apply 都返回 `RECOVERY_REQUIRED` 和 `write_may_have_occurred`，不重建 baseline、不覆盖旧 checkpoint、不发起写请求。只有同进程正常清理或回滚且独立回读成功，才解除 fence；未确认写状态或 `ROLLBACK_FAILED` 保留。自动 rollback 只覆盖同进程捕获的异常，本批不实现跨进程自动 resume，崩溃需人工对账恢复。

DOCX 结构测试始终运行。视觉验收通过 `POLYMAS_QA_PYTHON` 和 `POLYMAS_DOCX_RENDERER` 显式注入 bundled Python 与 canonical renderer；未注入时仅跳过视觉测试，显式路径不存在则失败。取得当前工作区依赖路径后运行 `python -m pytest -q tests/test_online_e2e_plan.py`，不硬编码插件版本。

### Synthetic 固定回归

`SyntheticRegressionBackend` 只用于离线证明完整状态机，不是 live 平台或 CDP 录制。固定学生套件覆盖精确案例法条、详细讲解、同 conversation 连续追问、模糊候选、未知案例拒绝补造和学生写入拒绝；runner 独立检查 outcome、案例/法条/候选/拒绝证据，不信任 backend 自报 `passed=true`。详细讲解必须同时具有基本案情、争议焦点或分析、反思思考题三类结构化证据。教师套件生成两个明确标注 `FICTIONAL TEST CASES / NO REAL PII` 的 DOCX 案例，backend 实际解析 DOCX 并核对 run_id、两个 exact case ID 和 scene，通过结构化上传、确认、同步和按 ID 回读后清理；自然语言“成功”不能替代写入回执或独立回读。发布可能落地后的 None、非 Mapping、状态化读取异常或 TypeError 都会先做安全回读，再按 owned/before/other 分支回滚或报告残留。

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests/test_online_e2e_runner.py
```

### Codex Goal 示例

```text
在 data-law-case-expert 目录运行 online_e2e 的 data-law-case-expert dry-run full。
使用我明确提供的 --env-file；只做 API-first 只读预检、快照和差异。
若返回 blocker，列出 blocker 与报告路径并停止，不执行 apply、浏览器写入或平台写入。
```

API-first 是默认路径。只有为补齐尚未验证的协议事实时才使用 CDP bootstrap：先由用户在独立测试助教中完成一次受控操作，采集并脱敏 method、path、精确 payload 字段、响应字段和终止条件，再把证据固化为 endpoint profile 与回归测试。CDP 不读取无关登录态，不把清空记忆或 `run_id` 冒充新会话，也不在未获得最终确认时保存或发送。详细证据边界见 [线上联调说明](docs/online-e2e-live-integration.md)。
