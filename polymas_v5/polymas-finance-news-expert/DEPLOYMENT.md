# 财经新闻推送专家部署说明

本文件说明本地交付物的部署步骤。当前仓库未保存 PDS 凭证，也未执行真实专家保存、Cron 创建或消息发送。

## 上传包

```bash
python scripts/package_skill.py --output finance-news-commentary.zip
```

上传包根目录必须为 `finance-news-commentary/`，只含 `SKILL.md`、`references/`、`output_format/` 和 `scripts/normalize_candidates.py`。

## PDS 配置

1. 定位“财经新闻推送专家”，昵称填写“财讯小信使”。
2. 上传 `finance-news-commentary.zip`，核验 Skill 名为 `finance-news-commentary`。
3. 按顺序挂载四项能力：

   1. `finance-news-commentary`
   2. `平台通用工具 0.0.4`
   3. `cron 0.0.1`
   4. `channel-message 0.0.1`

4. 粘贴 [EXPERT_CONFIG.md](EXPERT_CONFIG.md) 中的完整 Agent.md，保留 `${agent_name}`。
5. 保存前确认专家无需选择课程，未挂载学生班课、教学计划、学习资源或知识检索能力。

## 首次订阅

- 读取运行时学生、当前专家和当前会话，不询问内部 ID。
- 当前会话验证为同一学生、当前专家的个人会话后直接绑定；不查询或改绑到其他会话。
- `ask_user_question` 只收集频率、星期、时间、IANA 时区和财经主题，并取得最终确认。
- 稳定键为 `finance-news:{schoolId}:{userId}:{agentId}`；重复订阅不创建第二个 Cron。
- Cron 所有操作显式传当前 `--agent-id`。

## 投递门禁

- Cron 触发必须携带 Cron ID、任务键、版本和 agent-id；发送前重读订阅并逐项比对。
- 已绑定会话必须仍属于同一学生、当前专家且为个人会话；无效时停止，不搜索替代会话，不发送到班级群。
- `delivery_key={job_key}:{plan_version}:{edition_id}` 必须使用原子 `create-if-absent`/唯一约束或消息原生幂等键。
- 无原子能力时暂停 Cron并持久化 `disabled_atomicity`，不得降级发送。
- 消息成功、账本与完整 edition 历史均耐久写入后，才更新 `last_success_at`。
- 所有退出分支回读真实 `next_run_at`；回读失败记录 `schedule_state_error`。

## 真实联调验收

- 首次订阅不触发任何课程查询，只出现主题与计划问题。
- 当前运行时会话自动绑定，消息只回到当前专家个人会话。
- 同一学生/专家重复订阅、计划修改、暂停、恢复和退订符合幂等与回滚规则。
- stale trigger 不发送；并发相同 `delivery_key` 只发送一次。
- `ready`、`no_eligible_candidates`、消息失败、记账不确定和互动展开均返回真实状态。
- 输出分开呈现新闻事实、财经知识分析和互动问题，且不包含投资建议。

以上均属于真实平台联调项目；本地测试通过不能替代 PDS 中的真实 Cron 和消息送达验证。

请勿在文档、平台备注、测试消息或日志中粘贴 Token、Cookie、Authorization、真实学生 ID 或会话 ID。
