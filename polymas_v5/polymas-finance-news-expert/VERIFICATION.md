# 财经新闻推送专家验证记录

## 本次调整

- `ask_user_question` 与 `cron` 明确改为 AI 助教内置工具，不在 Skill 区挂载。
- 移除消息发送 Skill；Cron 唤醒后的 Agent 最终回复直接显示在创建任务的当前专家对话中。
- Skill 区只保留 `finance-news-commentary` 与 `平台通用工具 0.0.4`。
- 删除自建会话绑定、消息投递账本和本地订阅状态机；定时任务状态以平台内置 Cron 的 `list/get/state` 回执为准。
- 继续保持无课程模式、稳定任务键和计划切换回滚约束。

## 参考依据

问卷调查 MVP 的可用编排确认：

- `ask_user_question` 和 `cron` 位于内置工具区，不属于专业 Skill；
- Cron 操作使用 `list/create/get/state/pause/resume/delete/run` 并显式传当前 `agent-id`；
- 创建后必须回读任务 ID、状态和下一次执行时间。

财经专家在此基础上进一步使用内置 Cron 的当前对话回推能力，因此不再挂载或调用消息发送 Skill。

## RED 基线

新增目标合同测试后，旧版本出现 3 个预期失败：

1. Skill 挂载区仍含 Cron 与消息 Skill；
2. Agent.md 没有内置 Cron 的完整命令和当前对话最终回复契约；
3. 订阅仍包含会话绑定和消息投递字段。

这些失败证明测试覆盖了本次实际问题，而不是只验证新文案存在。

## 验证命令

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

- 财经专家目录：`161 passed in 7.91s`。
- Skill 校验：`Skill is valid!`。
- 五个 Python 文件编译退出码为 0，`git diff --check` 退出码为 0。
- 上传包 SHA-256：`f7842c7ad233c709c0c11eaf332afe6067b5171cb27dc6412b23b3f836d316a7`。

## 覆盖范围

- 专业 Skill 挂载列表不含 Cron 或消息能力。
- 内置 Cron 八类命令均显式传当前 agent-id。
- 创建前按稳定任务键精确 `cron list`，已有等价任务不重复创建。
- `cron create` 后必须 `get/state` 回读，工具未确认成功时不报告已订阅。
- 修改计划采用暂停旧任务、创建并验证候选、恢复候选、删除旧任务的切换顺序；失败时恢复旧任务或保持双方暂停。
- 定时任务正文携带任务键、计划版本、agent-id、主题和工作流要求；旧任务触发返回 `skipped_stale_trigger`。
- Cron 最终回复直接显示在当前专家对话中，不查询其他会话或调用消息 Skill。
- 暂停、恢复、退订和立即试运行使用内置 Cron 并回读真实状态。

## 独立 Forward-test

独立只读代理没有读取测试或本验证记录，模拟以下三种场景并给出 `PASS`，未发现 Critical 或 Important：

1. 学生已给出“每日 08:00、综合财经、上海”时，只展示规范化计划并做最终确认；确认后使用内置 `cron list/create/get/state`。
2. 完全相同的重复订阅精确复用现有任务，不调用 `cron create`。
3. 修改为 19:00 且候选校验失败时，删除候选并恢复旧任务；清理失败时保持新旧暂停，不虚报修改成功。

三个场景均未调用消息发送 Skill或会话检索，最终回执或简报直接出现在当前专家对话中。该结果仍属于配置级模拟，不是 PDS 真实 Cron 联调。

## 线上联调边界

本地测试只能验证 Agent.md、Skill、脚本、ZIP 和工具调用合同。本次未在 PDS 保存专家，未创建真实 Cron，也未验证定时到期后的当前对话回复。上线前必须用测试学生真实执行 `cron create/get/state/run`，并等待一次真实到期触发。
