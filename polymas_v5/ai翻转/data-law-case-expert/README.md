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

env 文件必须由 `--env-file` 显式传入，至少包含 `AUTHORIZATION` 与 `COOKIE`。凭证只进入内存请求头，不进入 stdout、checkpoint 或报告。CLI 的 stdout 始终恰好一个 JSON；诊断写 stderr。运行 checkpoint 位于 `.online-e2e-state/`，JSON/Markdown 报告位于 `reports/online-e2e/`，两者均被 gitignore。

只有所有 live 前置条件补证后，`dry-run` 才会把一次性确认令牌返回到 stdout。随后必须使用相同 `run_id` 和原令牌执行：

```bash
python -m online_e2e data-law-case-expert apply full \
  --run-id run-20260904-approved \
  --env-file /absolute/path/to/polymas.env \
  --confirmation-token '<dry-run stdout 中的令牌>'
```

`apply` 在 target 级文件锁内重新计算本地资产摘要、线上快照、隔离助教 NID、关系版本和请求计划摘要；内容、身份、关系或版本变化会使旧令牌失效。令牌和 nonce 均为一次性消费。成功只保留新专家配置，教师双案例 fixture 和知识变更必须清理并恢复。配置与知识分别执行 version/digest CAS；任一项检测到第三方并发变化时停止覆盖，报告 `ROLLBACK_FAILED` 与 `config_not_restored` 或 `knowledge_not_restored` 残留状态。

### Synthetic 固定回归

`SyntheticRegressionBackend` 只用于离线证明完整状态机，不是 live 平台或 CDP 录制。固定学生套件覆盖精确案例法条、详细讲解、同 conversation 连续追问、模糊候选、未知案例拒绝补造和学生写入拒绝；runner 独立检查 outcome、案例/法条/候选/拒绝证据，不信任 backend 自报 `passed=true`。教师套件生成两个明确标注 `FICTIONAL TEST CASES / NO REAL PII` 的 DOCX 案例，backend 实际解析 DOCX 并核对 run_id、两个 exact case ID 和 scene，通过结构化上传、确认、同步和按 ID 回读后清理；自然语言“成功”不能替代写入回执或回读。

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
