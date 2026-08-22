# Final fix report

## 状态

`DONE_WITH_CONCERNS`：所有 final-review findings 中可本地解决的 Critical/Important/Minor 已修复；未执行真实 PDS、Cron 或消息投递。

## RED / GREEN

- 修复前财经目录：`66 passed`。
- normalizer 新行为测试首轮：`23 failed, 44 passed`；修复后全部通过。
- 专家状态机新测试首轮：`3 failed, 10 passed`；修复后全部通过。
- Skill/契约新测试首轮：`3 failed, 7 passed`；修复后全部通过。
- package 未知参数先观察到 stderr usage 失败，后改为 stdout JSON/非零退出并通过。
- 详细 RED 证据与定向命令见 `polymas_v5/polymas-finance-news-expert/VERIFICATION.md`。

## 修复摘要

- normalizer：课程及 citation 双字段绑定，输出白名单，拒绝项仅 `{candidate_index, reason}`，hostname allowlist 推导来源等级，私网/userinfo/未列入域名拒绝，规避式中英文投资措辞检测，URL 规范化，1 MiB/100 候选/10 citation/字符串/深度上限与受控 JSON 错误。
- 专家：同课计划切换与跨课程新 `job_key` 迁移分流，补齐旧任务暂停、恢复失败和 orphan 二阶补偿，加入 `delivery_key` 幂等账本、一期一条完整历史、互动读取范围校验和“综合财经”确认流程。
- 打包：argparse 错误 JSON-only；ZIP 测试扫描成员正文凭证模式，并与源文件哈希对照。

## 完成验证

- 财经目录全量：`93 passed in 3.75s`。
- `quick_validate.py`：`Skill is valid!`。
- 2 个脚本 + 3 个测试文件 `py_compile`：退出码 0。
- 确定性 ZIP SHA-256：`049af16f63b04978c76f82b8b24c2b607ec772b6928e469816adfa038c4d1003`。
- ZIP 白名单成员：5；每成员与源码哈希一致；正文凭证模式命中：0。
- `git diff --check`：退出码 0。
- 既有无关仓库基线：`107 passed, 12 failed`，12 项为清洁 worktree 缺失未跟踪课程夹具；本轮未重跑该无关基线。

## 独立 forward-test

一个独立只读子代理仅获取完成态 Skill + Expert 和三个压力场景，未提供预期答案；总结论为 `PASS（有非阻断 concerns）`。

- 多课程+无证据：强制选课/确认，返回 `skipped_no_course_evidence`，不发送。
- 旧 Cron 重放+发送成功记账失败：旧触发 `skipped_stale_trigger`；后者 `delivery_uncertain`，不自动重发。
- 恶意来源/投资建议/超大输入：来源、内容和资源门禁均拦截，不产生 `ready`。

## 提交

- `ed664ff` `fix: harden finance news expert final review`
- `2155429` `docs: record finance expert verification`
- 本报告位于后续独立文档提交。

## 关注点

- 真实 PDS 上的 Cron 补偿、`metadata.delivery_key`、消息回执、跨存储记账原子性与 uncertain 人工对账仍是上线前联调门禁。
- 静态投资禁语表已覆盖 findings 要求的中英文与空格/标点/零宽规避，但不能代替平台端更强的语义审核。
