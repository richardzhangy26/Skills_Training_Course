# 财经新闻课程点评专家验证记录

## RED 基线

- 修复前财经目录基线：`python -m pytest -q polymas_v5/polymas-finance-news-expert/tests` → `66 passed`。
- normalizer 安全与资源上限测试先于实现写入：首次定向执行为 `23 failed, 44 passed`，失败包括混课引用、课程元数据回显、伪造来源等级、私网/userinfo、规避式投资措辞、URL dot-segment、超限和深层 JSON。
- 专家状态机测试先于文档实现写入：首次定向执行为 `3 failed, 10 passed`，失败是默认主题确认、跨课程迁移/二阶补偿、投递账本/完整历史。
- Skill/数据契约测试先于文档同步：首次定向执行为 `3 failed, 7 passed`。
- package CLI 未知参数测试先于实现：首次执行确认 argparse 向 stderr 输出 usage 并失败。
- 证据预检为 false 时的 citation 上限、以及历史示例域名均分别先观察到目标测试失败，再实现修复。

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

- 财经目录全量：`93 passed in 3.75s`。
- Skill 基础校验：`Skill is valid!`。
- 上述 5 个新增/修改 Python 文件 `py_compile` 退出码为 0。
- `git diff --check` 退出码为 0。

## 确定性 ZIP 与凭证扫描

- 实际上传包与独立第二次构建的 SHA-256 一致：`049af16f63b04978c76f82b8b24c2b607ec772b6928e469816adfa038c4d1003`。
- ZIP 仅含 5 个排序后白名单成员：`SKILL.md`、`output_format/briefing.md`、`references/data-contract.md`、`references/source-policy.md`、`scripts/normalize_candidates.py`。
- 每个 ZIP 成员的 SHA-256 都与当前源文件一致。
- 逐成员 UTF-8 正文扫描 Authorization/Cookie/Token/API key 赋值模式和 JWT 模式：`credential_pattern_hits: 0`。

## 独立 forward-test

执行方：独立只读子代理；未向它提供审查 findings 或预期答案，未修改文件、未联网、未调用线上工具。总结论：`PASS（有非阻断 concerns）`。

1. **多课程 + 无证据**：先用 `ask_user_question` 让学生选课并确认计划；所选课程无可核验证据时，normalizer 返回 `skipped_no_course_evidence/precheck`、`items: []`，不调用 `channel-message`。关注点：订阅创建与“当期证据缺失而跳过”是两个状态，交付时必须区分。
2. **旧 Cron 重放 + 发送成功后记账失败**：旧触发返回 `skipped_stale_trigger`且不发送；新触发中消息已成功但账本/历史写入失败时保持 `pending/uncertain`，返回 `delivery_uncertain`，不更新成功时间，不自动重发。关注点：跨存储“原子记账”和人工对账/解除 uncertain 仍需在真实平台接口上验证。
3. **恶意来源/投资措辞/超大输入**：带 userinfo 的私网 URL 不能自报 official；空格、标点和大小写规避的中英文投资措辞被拒绝；超过 1 MiB、101 条候选、11 条 citation 和深层 JSON 均返回受控错误/拒绝，不产生 `ready`。关注点：静态短语表可处理已覆盖的规避形式，但不能代替平台端更强的语义审核。

## 与本目录无关的仓库基线

既有仓库基线记录为 `107 passed, 12 failed`；12 项失败来自清洁 worktree 缺少主工作区未跟踪的课程夹具/素材，与财经专家目录修改无关。本轮未重跑该缺失夹具的全仓命令，只将其作为历史基线记录；本轮完成门禁以上述财经目录 `93 passed` 为当前证据。

## 线上联调边界

本轮未上传 Skill、未保存 PDS 专家、未创建真实 Cron、未发送消息。真实平台的订阅持久化、Cron 补偿、幂等元数据传递、消息回执、跨存储记账和不确定状态对账仍是上线前联调门禁，不宣称已完成线上验证。
