# 财经新闻推送专家验证记录

## 本次行为变更

- 移除课程查询、课程选择、教学计划、学习资源和课程知识证据。
- 首次订阅默认绑定当前运行时的本专家个人会话，不搜索其他会话。
- 稳定任务键改为 `finance-news:{schoolId}:{userId}:{agentId}`。
- 输出改为“新闻事实＋财经知识分析＋互动问题”。
- Skill 更名为 `finance-news-commentary`，上传包更名为 `finance-news-commentary.zip`。

## RED 基线

- 隔离 worktree 创建后，旧目录基线为 `187 passed`，Skill 校验通过。
- 新增“无课程＋当前专家会话”专家合同测试后，旧版本因仍挂载 `学生班课查询`、教学计划、学习资源和知识检索能力而失败。
- 新增 general normalizer 输入测试后，旧脚本返回 `input.course_evidence_available must be a boolean`，证明其仍强制依赖课程字段。
- 独立只读基线代理模拟“每天 8 点推送到当前专家且拒绝选课”时，旧工作流会先访问课程并因没有 `courseId` 停止；旧 `job_key`、领域 Skill、Cron 和历史均依赖课程。

## GREEN 验证命令

```bash
python -m pytest -q polymas_v5/polymas-finance-news-expert/tests
python /Users/zhangyichi/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  polymas_v5/polymas-finance-news-expert/finance-news-commentary
python -m py_compile \
  polymas_v5/polymas-finance-news-expert/finance-news-commentary/scripts/normalize_candidates.py \
  polymas_v5/polymas-finance-news-expert/scripts/package_skill.py \
  polymas_v5/polymas-finance-news-expert/tests/test_normalize_candidates.py \
  polymas_v5/polymas-finance-news-expert/tests/test_skill_package.py \
  polymas_v5/polymas-finance-news-expert/tests/test_expert_bundle.py
git diff --check
```

当前本地结果：

- 财经专家目录：`158 passed`。
- Skill 校验：`Skill is valid!`。
- 五个 Python 文件 `py_compile` 退出码为 0。
- `git diff --check` 退出码为 0。

## ZIP 验证

- 上传包：`finance-news-commentary.zip`。
- SHA-256：`cdb9cce120ace3a045a501c5475f4db90ec6a335cd2853d0d32e95c458613a89`。
- 独立重建两次与交付包 SHA-256 相同。
- ZIP 仅含 5 个白名单成员，根目录为 `finance-news-commentary/`。
- 每个成员与当前源码逐字节一致，凭证扫描无命中。

## 新模式覆盖

- 同一只读代理在更新后复跑相同首次订阅场景并给出 `PASS`：只补问时区并进行最终确认，未访问课程、未搜索其他会话；`job_key`、当前会话绑定、Cron 和投递门禁均符合新模式。
- 首次订阅不访问或选择课程，只询问财经主题、频率、星期、时间和时区。
- 当前运行时会话经身份与专家归属校验后直接绑定；不查询、改绑或降级到其他会话/班级群。
- 同一学生/专家只允许一个活动订阅，重复请求不创建第二个 Cron。
- 计划切换保留暂停旧任务、创建暂停候选、校验、启用、清理和二阶失败双暂停门禁。
- stale trigger、原子 `delivery_key`、不确定回执、成功后记账与 `next_run_at` finalizer 仍有自动化合同测试。
- normalizer 保留来源可信度、URL 安全、去重、资源上限和投资建议检测，不再接收或输出课程字段。

## 线上联调边界

本次没有保存 PDS 专家、上传 Skill、创建真实 Cron 或发送真实消息。当前会话运行时字段、Cron 原子能力、`channel-message` 会话归属校验、真实送达和回执记账仍需在获授权的测试学生环境联调。
