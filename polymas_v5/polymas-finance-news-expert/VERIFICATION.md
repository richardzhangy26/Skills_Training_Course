# 财经新闻课程点评专家验证记录

## RED 基线

- 修复前财经目录基线：`python -m pytest -q polymas_v5/polymas-finance-news-expert/tests` → `66 passed`。
- normalizer 安全与资源上限测试先于实现写入：首次定向执行为 `23 failed, 44 passed`，失败包括混课引用、课程元数据回显、伪造来源等级、私网/userinfo、规避式投资措辞、URL dot-segment、超限和深层 JSON。
- 专家状态机测试先于文档实现写入：首次定向执行为 `3 failed, 10 passed`，失败是默认主题确认、跨课程迁移/二阶补偿、投递账本/完整历史。
- Skill/数据契约测试先于文档同步：首次定向执行为 `3 failed, 7 passed`。
- package CLI 未知参数测试先于实现：首次执行确认 argparse 向 stderr 输出 usage 并失败。
- 证据预检为 false 时的 citation 上限、以及历史示例域名均分别先观察到目标测试失败，再实现修复。

### 封板复审补充 RED

- 补充 normalizer 测试后首次定向执行：`8 failed, 70 passed`。失败精确覆盖 `NFKC`/提示词+动作词投资建议、全角 `buy now`、畸形 URL 混批、percent-encoded unreserved 和 hostname canonical source。实现后定向为 `78 passed`。
- 补充专家状态机测试后首次定向执行：`2 failed, 16 passed`。失败精确覆盖首次激活/改课迁移失败状态与投递原子性/`next_run_at`。实现后定向为 `18 passed`，加入 package 测试后为 `20 passed`。
- package `--help` JSON 和 ZIP 凭证反例首次定向执行：`2 failed`；其中 argparse 返回普通 help 文本，旧正则同时漏掉 `"token": "..."` 和 `Authorization: Bearer ...`。
- Skill/数据契约/部署文档补充测试首次定向执行：`4 failed`；同步后 Skill+专家测试为 `30 passed`。

## GREEN 与完成门禁

当前定向命令：

```bash
python -m pytest -q polymas_v5/polymas-finance-news-expert/tests/test_normalize_candidates.py
python -m pytest -q polymas_v5/polymas-finance-news-expert/tests/test_skill_package.py
python -m pytest -q polymas_v5/polymas-finance-news-expert/tests/test_expert_bundle.py
python -m pytest -q polymas_v5/polymas-finance-news-expert/tests
python /Users/zhangyichi/.codex/skills/.system/skill-creator/scripts/quick_validate.py polymas_v5/polymas-finance-news-expert/finance-news-course-commentary
python -m py_compile \
  polymas_v5/polymas-finance-news-expert/finance-news-course-commentary/scripts/normalize_candidates.py \
  polymas_v5/polymas-finance-news-expert/scripts/package_skill.py \
  polymas_v5/polymas-finance-news-expert/tests/test_normalize_candidates.py \
  polymas_v5/polymas-finance-news-expert/tests/test_skill_package.py \
  polymas_v5/polymas-finance-news-expert/tests/test_expert_bundle.py
git diff --check
```

本轮新鲜结果：

- 财经目录全量：`108 passed in 2.64s`。
- Skill 基础校验：`Skill is valid!`。
- 上述 5 个新增/修改 Python 文件 `py_compile` 退出码为 0。
- `git diff --check` 退出码为 0。

## 确定性 ZIP 与凭证扫描

- 实际上传包与独立第二次构建的 SHA-256 一致：`d04f8f7f45fa2d87f1b8df637e45f3a4fb20ccbeef1e32d3ac70f786e7e376d5`。
- ZIP 仅含 5 个排序后白名单成员：`SKILL.md`、`output_format/briefing.md`、`references/data-contract.md`、`references/source-policy.md`、`scripts/normalize_candidates.py`。
- 每个 ZIP 成员的 SHA-256 都与当前源文件一致。
- 逐成员 UTF-8 正文扫描 Authorization/Cookie/Token/API key 赋值模式和 JWT 模式：`credential_pattern_hits: 0`。正则反例已证明能命中 `"token": "secretvalue123"` 和 `Authorization: Bearer ...`。

## 独立 forward-test（final review）

执行方：独立只读子代理；未向它提供审查 findings 或预期答案，未修改文件、未联网、未调用线上工具。总结论：`PASS（有非阻断 concerns）`。

1. **多课程 + 无证据**：先用 `ask_user_question` 让学生选课并确认计划；所选课程无可核验证据时，normalizer 返回 `skipped_no_course_evidence/precheck`、`items: []`，不调用 `channel-message`。关注点：订阅创建与“当期证据缺失而跳过”是两个状态，交付时必须区分。
2. **旧 Cron 重放 + 发送成功后记账失败**：旧触发返回 `skipped_stale_trigger`且不发送；新触发中消息已成功但账本/历史写入失败时保持 `pending/uncertain`，返回 `delivery_uncertain`，不更新成功时间，不自动重发。关注点：跨存储“原子记账”和人工对账/解除 uncertain 仍需在真实平台接口上验证。
3. **恶意来源/投资措辞/超大输入**：带 userinfo 的私网 URL 不能自报 official；空格、标点和大小写规避的中英文投资措辞被拒绝；超过 1 MiB、101 条候选、11 条 citation 和深层 JSON 均返回受控错误/拒绝，不产生 `ready`。关注点：静态短语表可处理已覆盖的规避形式，但不能代替平台端更强的语义审核。

## 独立 forward-test（封板复审）

执行方：新的独立只读子代理；只获取完成态 Skill/Expert 和压力场景，明确禁止读取 findings/tests/预期答案，未修改文件、未联网、未调用线上工具。总结论：`PASS（有 concerns）`。

1. **相同 `delivery_key` 并发**：有持久化原子能力时只有一个执行器取得 `pending` 所有权并发送；另一个返回 `delivery_uncertain` 或 `skipped_duplicate`。无原子能力/消息幂等键时，两个均返回 `delivery_atomicity_unavailable`并不发送。关注点：真实平台如何持久禁用自动发送和统一错误响应仍需联调。
2. **畸形 URL 混批**：`https://[bad` 候选级返回 `invalid_url`，合法人民银行候选正常进入 `ready`，输出 canonical source、`source_level: 1` 和稳定 ID；整批 stdout 为单 JSON/退出 0，且拒绝项不泄漏原 URL。
3. **六种投资措辞**：“建议持有该股票”、“建议做多该品种”、“维持增持评级”、`overweight this stock`、`buy now`、“买 入”均被拒绝；全部拒绝后为 `no_eligible_candidates/normalizer`，`rejected` 仅含索引与 `investment_advice_language`。
4. **全新订阅失败**：创建失败删草稿或保留 `paused/null/activation_error`；校验、启用或回读失败均暂停并删除候选；删除失败则 `paused+recovery_required+orphaned_cron_job_ids`，不进入 active。关注点：平台上的暂停失败/状态补偿写入失败和用户可见响应仍需联调。
5. **改课迁移二阶失败**：旧 Cron 停用或旧订阅退订写入失败时，暂停新任务、恢复旧 active、新订阅 `paused+migration_error` 并清理；恢复/清理再失败则双方 paused+recovery+orphans 并停止。关注点：跨订阅/Cron/清理的耐久原子性仍取决于平台能力。

## 与本目录无关的仓库基线

既有仓库基线记录为 `107 passed, 12 failed`；12 项失败来自清洁 worktree 缺少主工作区未跟踪的课程夹具/素材，与财经专家目录修改无关。本轮未重跑该缺失夹具的全仓命令，只将其作为历史基线记录；本轮完成门禁以上述财经目录 `108 passed` 为当前证据。

## 线上联调边界

本轮未上传 Skill、未保存 PDS 专家、未创建真实 Cron、未发送消息。真实平台的 `pending_activation` 持久化、Cron 补偿、原子 `create-if-absent`/消息幂等键、回执记账、`next_run_at` 回读和不确定状态对账仍是上线前联调门禁，不宣称已完成线上验证。
