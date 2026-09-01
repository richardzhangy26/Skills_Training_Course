# 财经新闻推送专家部署说明

本版本采用“领域 Skill＋AI 助教内置工具”架构。当前仓库未执行真实专家保存、Cron 创建或定时回复。

## 上传包

```bash
python scripts/package_skill.py --output finance-news-commentary.zip
```

上传包根目录为 `finance-news-commentary/`，只包含 `SKILL.md`、`references/`、`output_format/` 和 `scripts/normalize_candidates.py`。

## PDS 配置

1. 定位“财经新闻推送专家”，昵称填写“财讯小信使”。
2. 上传 `finance-news-commentary.zip`。
3. 只挂载两项专业 Skill：

   1. `finance-news-commentary`
   2. `平台通用工具 0.0.4`

4. `ask_user_question` 是 AI 助教内置工具，`cron` 是 AI 助教内置工具，二者不作为 Skill 挂载。
5. 移除技能区中已挂载的定时任务或消息发送 Skill。
6. 粘贴 [EXPERT_CONFIG.md](EXPERT_CONFIG.md) 中的完整 Agent.md，保留 `${agent_name}`。

## 内置 Cron 操作

所有操作显式传当前专家 `agent-id`：

- `cron list --agent-id <当前专家>`
- `cron create --agent-id <当前专家>`
- `cron get <cron_job_id> --agent-id <当前专家>`
- `cron state <cron_job_id> --agent-id <当前专家>`
- `cron pause <cron_job_id> --agent-id <当前专家>`
- `cron resume <cron_job_id> --agent-id <当前专家>`
- `cron delete <cron_job_id> --agent-id <当前专家>`
- `cron run <cron_job_id> --agent-id <当前专家>`

稳定任务键为 `finance-news:{schoolId}:{userId}:{agentId}`，只保存在平台私有 Cron 元数据中，不进入外部检索、用户回复或执行日志。创建前执行 `cron list`，只按完整任务键和当前 agent-id 精确匹配；0 个时创建，1 个时复用或切换计划，多个时暂停全部精确匹配并返回 `duplicate_cron_conflict`。

任务正文严格保存：

```json
{
  "trigger_job_key": "finance-news:{schoolId}:{userId}:{agentId}",
  "trigger_plan_version": 1,
  "trigger_agent_id": "当前 agent-id",
  "topics": ["学生确认的主题"],
  "window_rule": "上次成功执行时间至本次执行时间",
  "workflow": "finance-news-current-expert"
}
```

内置 Cron 支持原生幂等键时同时传 `job_key`；不支持时在创建后立即再次 `cron list` 对账，只允许一个精确匹配任务继续启用。

## 当前专家对话回推

内置 Cron 到期后唤醒创建任务的当前专家。专家完成检索和点评后，将简报作为本轮 Cron 的最终回复直接返回；定时任务的最终回复直接显示在创建任务的当前专家对话中。

不调用任何消息发送 Skill，不执行会话查找或频道发送命令，也不维护额外的会话绑定、消息回执或投递账本。

## 计划切换与维护

- 修改计划：验证旧任务 → 暂停旧任务 → 创建并暂停候选 → `cron get/state` 校验 → 恢复候选 → 删除旧任务。旧任务删除失败时立即暂停候选并恢复旧任务；候选清理或旧任务恢复失败时保持双方暂停。
- 候选失败：删除候选并恢复旧任务；候选无法删除时保持新旧暂停并报告人工清理。
- 暂停、恢复、退订和立即试运行分别使用内置 `cron pause/resume/delete/run`，每次操作后都用 `cron get/state/list` 回读验证。
- 工具没有返回成功、任务 ID、状态或下一次执行时间时，不报告操作完成。
- 每次定时触发在生成前和最终回复前各执行一次 `cron list/get/state`，要求任务键只匹配一个启用任务，且运行时触发 ID、任务版本和 agent-id 均一致；失配返回 `skipped_stale_trigger`。

## 真实平台联调

- 技能区只存在两项专业 Skill，没有 Cron 或消息 Skill。
- `ask_user_question` 与 `cron` 显示为内置工具调用卡片。
- `cron create` 后可通过 `cron get/state` 查询到正确 agent-id、任务键、计划和下一次执行时间。
- `cron run` 和真实到期触发都会把最终简报显示在当前专家对话中。
- 重复订阅、修改计划、暂停、恢复和退订不会留下双任务。
- 定时触发能调用平台通用工具和 `finance-news-commentary`，并正确处理无候选和工具失败。

以上属于真实平台联调；本地 Markdown、脚本和测试通过不能替代 PDS 中的真实 Cron 启动与回复验证。
