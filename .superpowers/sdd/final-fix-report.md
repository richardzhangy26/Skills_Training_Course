# Final fix report

## 状态

`DONE_WITH_CONCERNS`：所有 final-review findings 中可本地解决的 Critical/Important/Minor 已修复；未执行真实 PDS、Cron 或消息投递。

## RED / GREEN

- 修复前财经目录：`66 passed`。
- normalizer 新行为测试首轮：`23 failed, 44 passed`；修复后全部通过。
- 专家状态机新测试首轮：`3 failed, 10 passed`；修复后全部通过。
- Skill/契约新测试首轮：`3 failed, 7 passed`；修复后全部通过。
- package 未知参数先观察到 stderr usage 失败，后改为 stdout JSON/非零退出并通过。
- 封板复审 normalizer 新测试：`8 failed, 70 passed` → `78 passed`；专家状态机：`2 failed, 16 passed` → `18 passed`。
- package `--help`/ZIP 凭证反例首轮 `2 failed`；Skill/契约/部署同步首轮 `4 failed`，实现后全部通过。
- 详细 RED 证据与定向命令见 `polymas_v5/polymas-finance-news-expert/VERIFICATION.md`。

## 修复摘要

- normalizer：在原有双字段课程绑定、输出白名单、hostname 信任和资源上限上，新增 Unicode `NFKC`+提示词/动作词投资建议门禁、候选级畸形 URL 隔离、percent-encoded unreserved 规范化和 hostname canonical source label。
- 专家：新增全新订阅/改课迁移 `pending_activation` 状态及失败补偿；`delivery_key` 必须使用原子 `create-if-absent`/唯一约束或消息原生幂等键，无能力返回 `delivery_atomicity_unavailable` 并停发；每次触发回读 `next_run_at`。
- 打包：argparse 错误及 `--help` 均 JSON-only；ZIP 正文扫描新增 JSON token 与 Bearer 反例，并与源文件哈希对照。

## 完成验证

- 财经目录全量：`108 passed in 2.64s`。
- `quick_validate.py`：`Skill is valid!`。
- 2 个脚本 + 3 个测试文件 `py_compile`：退出码 0。
- 确定性 ZIP SHA-256：`d04f8f7f45fa2d87f1b8df637e45f3a4fb20ccbeef1e32d3ac70f786e7e376d5`。
- ZIP 白名单成员：5；每成员与源码哈希一致；正文凭证模式命中：0。
- `git diff --check`：退出码 0。
- 既有无关仓库基线：`107 passed, 12 failed`，12 项为清洁 worktree 缺失未跟踪课程夹具；本轮未重跑该无关基线。

## 独立 forward-test

一个独立只读子代理仅获取完成态 Skill + Expert 和三个压力场景，未提供预期答案；总结论为 `PASS（有非阻断 concerns）`。

- 多课程+无证据：强制选课/确认，返回 `skipped_no_course_evidence`，不发送。
- 旧 Cron 重放+发送成功记账失败：旧触发 `skipped_stale_trigger`；后者 `delivery_uncertain`，不自动重发。
- 恶意来源/投资建议/超大输入：来源、内容和资源门禁均拦截，不产生 `ready`。

封板复审后另一个独立只读子代理评估并发触发、畸形 URL 混批、六种投资措辞、全新订阅和改课二阶失败，结论为 `PASS（有 concerns）`。原子锁仅允许一个执行器发送，无原子能力时完全停发；畸形 URL 不影响合法同批；六种措辞全部拒绝且不回显；激活/迁移失败不留 active 无任务或双发状态。

## 提交

- `ed664ff` `fix: harden finance news expert final review`
- `2155429` `docs: record finance expert verification`
- `c03981d` `docs: add final finance fix report`
- `75bd57a` `fix: close finance expert seal review gaps`
- 本轮验证记录/报告更新位于后续独立文档提交。

## 关注点

- 真实 PDS 上的 `pending_activation`、Cron 补偿、原子 create-if-absent/消息幂等键、无原子能力的持久停发、回执记账与 uncertain 对账仍是上线前联调门禁。
- 静态投资禁语表已覆盖 findings 要求的中英文与空格/标点/零宽规避，但不能代替平台端更强的语义审核。
