# 财经新闻推送专家验证记录

## 本次调整

- `ask_user_question` 与 `cron` 使用 AI 助教内置工具，不在 Skill 区挂载。
- 移除消息发送 Skill；Cron 最终回复直接显示在创建任务的当前专家对话中。
- Skill 区只保留 `finance-news-commentary` 与 `平台通用工具 0.0.4`。
- 不维护会话 ID、投递账本、学生稳定键、触发 schema 或自建订阅状态机。
- 定时任务使用名称 `财经新闻推送` 和内置 Cron 返回的 `cron_job_id` 管理。

## 参考依据

问卷调查 MVP 将 `ask_user_question`、`cron`、时间等能力放在内置工具区，并使用 `cron list/create/get/state/pause/resume/delete/run` 管理任务。本专家复用这一模式，同时利用内置 Cron 的当前对话最终回复能力，因此不需要消息发送 Skill。

## RED 基线

新增目标合同测试后，旧版本出现 3 个预期失败：

1. Skill 挂载区仍含 Cron 与消息 Skill；
2. Agent.md 没有内置 Cron 的完整命令和当前对话最终回复契约；
3. 订阅仍包含会话绑定和消息投递字段。

在用户要求进一步简化后，新的合同测试又确认旧稿仍残留学生稳定键、触发 schema 和过度对账规则；随后将它们移除。

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

- 财经专家目录：`161 passed in 11.36s`。
- Skill 校验：`Skill is valid!`。
- 五个 Python 文件编译退出码为 0，`git diff --check` 退出码为 0。
- 上传包 SHA-256：`12878d64963d051539e5e1e07908827ac87f4569f0dc8d5a3823766e4c280c38`。

## 覆盖范围

- 专业 Skill 挂载列表不含 Cron 或消息能力。
- 内置 Cron 八类命令均显式传当前 agent-id。
- 创建前按当前专家作用域和任务名称查找；已有同名同计划任务时复用。
- `cron create` 后用返回的任务 ID 执行 `get/state`；工具未确认成功时不报告已订阅。
- 修改计划采用暂停旧任务、创建并验证新任务、删除旧任务；候选失败时删除候选并恢复旧任务。
- Cron 最终回复直接显示在当前专家对话中，不查询其他会话或调用消息 Skill。
- 暂停、恢复、退订和立即试运行使用内置 Cron 并回读真实状态。

## 独立 Forward-test

独立只读代理模拟首次订阅、重复同名订阅、改期候选校验失败三种场景。核心流程符合简化要求：仅使用当前专家作用域、任务名称和 Cron 返回的任务 ID；不调用消息 Skill或会话检索；改期失败删除候选并恢复旧任务。

代理指出两处残留：首次订阅仍读取 `schoolId/userId`，联调清单仍提到任务键和 stale trigger。两处均已删除，避免无谓依赖和验收口径冲突。

## 最终独立审查

独立只读审查对范围 `c8d995c..84f56a3` 给出 `READY`，未发现 Critical 或 Important。审查复跑结果为 `161 passed`、`Skill is valid!`、`git diff --check` 通过；ZIP 为 5 个白名单成员，均与源码逐字节一致。

## 线上联调边界

本地测试只能验证 Agent.md、Skill、脚本、ZIP 和工具调用合同。本次未在 PDS 保存专家，未创建真实 Cron，也未验证定时到期后的当前对话回复。上线前必须用测试学生真实执行 `cron create/get/state/run`，并等待一次真实到期触发。
