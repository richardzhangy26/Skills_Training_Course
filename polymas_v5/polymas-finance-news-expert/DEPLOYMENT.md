# 财经新闻推送专家部署说明

本文件仅说明可执行的上线步骤；当前仓库没有保存 PDS 凭证，未执行任何真实平台写入、Cron 创建或 `channel-message` 发送。

## 上传包

在本目录执行：

```bash
python scripts/package_skill.py --output finance-news-course-commentary.zip
```

生成的 `finance-news-course-commentary.zip` 根目录为 `finance-news-course-commentary/`，可作为 Skill 上传包。包内只含运行所需的 `SKILL.md`、`references/`、`output_format/` 和 `scripts/normalize_candidates.py`；不含测试、缓存、隐藏文件、Token、Cookie 或任何凭证。

## PDS 配置步骤

1. 新建或定位专家，名称填写“财经新闻推送专家”，昵称填写“财讯小信使”，描述采用 [EXPERT_CONFIG.md](EXPERT_CONFIG.md) 的基本信息。
2. 上传 `finance-news-course-commentary.zip`，核验 Skill 名为 `finance-news-course-commentary`。
3. 按以下挂载顺序添加能力：

   1. `finance-news-course-commentary`
   2. `平台通用工具 0.0.4`
   3. `知识检索助手 1.0.1`
   4. `学生班课查询 1.0.1`
   5. `学生教学计划查询 1.0.0`
   6. `学生学习资源助手 1.0.0`
   7. `cron 0.0.1`
   8. `channel-message 0.0.1`

4. 将 [EXPERT_CONFIG.md](EXPERT_CONFIG.md) 中“完整 Agent.md”代码块原样粘贴到 PDS Agent.md 模板对应位置，保留 `${agent_name}` 变量格式。
5. 保存前检查：学生选课、计划填写和所有写操作都经 `ask_user_question`；领域 Skill 不承担 Cron 和 `channel-message` 职责；不含 Token、Cookie 或学生真实身份数据。

## Cron 与投递操作清单

- 查询或创建 Cron 时显式带当前 `--agent-id`，并先以 `job_key` 查询现有任务。
- 修改计划严格采用：暂停已验证旧任务 → 创建初始暂停的候选任务 → 校验候选 → 写订阅新 ID/version → 启用候选 → 删除旧任务。只有新订阅写入+候选启用成功后才删除旧任务。
- 候选创建失败：恢复旧任务，订阅保持旧 ID/version。候选创建成功但校验失败：先删除候选；删除成功后恢复旧订阅/旧任务；删除失败则新旧均保持暂停、记录 `orphaned_candidate`、订阅status=paused、停止投递。候选校验成功但写订阅新ID/version失败：执行同一删除候选与恢复/暂停补偿矩阵。
- 旧任务暂停失败时不创建候选，状态保持不变。恢复旧任务或旧订阅失败时，新旧任务均暂停，写入 `status=paused`、`recovery_required=true` 和新旧 orphan ID，停止自动投递。
- 课程变更不使用同 `job_key` 切换：先创建、校验、写入并启用新课程的新 `job_key`，再停旧 Cron，最后将旧订阅标为退订并写入 `superseded_by_job_key`。新候选任一步失败都删除或暂停新候选，旧订阅继续活动。
- 每个 Cron 定时触发正文必须带 `trigger_cron_job_id`、`trigger_job_key`、`trigger_plan_version`、`trigger_agent_id`。发送前重读 subscription，逐一比对当前 Cron ID、任务键、版本和专家 agent-id；任一失配返回 `skipped_stale_trigger`，不调用 `channel-message`、不更新成功历史。
- 个人会话无法唯一定位时停止；绝不降级到班级群。只有 `channel-message` 返回发送成功后才更新成功时间与历史。
- 发送前以 `delivery_key={job_key}:{plan_version}:{edition_id}` 查幂等账本：`sent` 返回 `skipped_duplicate`，`pending/uncertain` 返回 `delivery_uncertain` 且不自动重发。只有先持久化 pending 后才发送；发送成功但账本记账失败仍是不可自动重试的不确定状态。
- 成功记账后，每期在 `finance_news/{schoolId}/{userId}/briefing_history.jsonl` 只写一条 edition，包含 `job_key`、完整课程对象、会话、回执和完整 `items` 数组。

## 真实联调验收

以下项目尚未验证，必须在有授权的 PDS 测试环境逐项完成：

- Skill 上传、专家保存和八项挂载是否均成功。
- 多课程候选是否通过 `ask_user_question` 选择；学生自己填写计划后是否确实需要确认。
- 订阅字段、稳定 `job_key`、Cron 两阶段切换、候选启用失败、候选删除失败、旧任务删除失败、回滚和暂停/恢复/退订是否符合平台实际接口。
- 候选创建失败是否恢复旧任务且订阅仍为旧 ID/version；候选创建成功但校验失败、候选校验成功但写订阅新ID/version失败时，是否按“删除成功恢复旧订阅/旧任务，删除失败双方暂停并记录 `orphaned_candidate`”执行。
- 课程变更是否生成新 `job_key`，且只在新订阅启用后停旧 Cron/写 `superseded_by_job_key`；测试恢复失败时的 `recovery_required=true` 双暂停门禁。
- stale trigger（Cron ID、任务键、版本或 agent-id 失配）是否返回 `skipped_stale_trigger`，且没有任何 `channel-message` 调用或成功历史更新。
- 唯一个人会话的发送成功、失败重试，以及多候选时停止不群发。
- `delivery_key` 的重复、pending/uncertain 和成功发送但记账失败分支；核对 `skipped_duplicate`、`delivery_uncertain` 且无二次发送，以及 `briefing_history.jsonl` 一期一记录的完整字段。
- `ready`、无课程证据、无候选和互动新闻展开是否能在 PDS 中得到可追溯输出。

请勿在文档、平台备注、测试消息或日志中粘贴 Token、Cookie、Authorization、真实学生 ID 或会话 ID。
