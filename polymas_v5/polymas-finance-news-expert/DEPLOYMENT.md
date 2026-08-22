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
- 修改计划采用新任务验证、切换启用、停用旧任务的两阶段切换；任一步失败回滚到旧 `cron_job_id`/`plan_version`。
- 每次触发和发送前重新校验 `status`、课程权限、计划、`plan_version` 和 `target_session_id`。
- 个人会话无法唯一定位时停止；绝不降级到班级群。只有 `channel-message` 返回发送成功后才更新成功时间与历史。

## 真实联调验收

以下项目尚未验证，必须在有授权的 PDS 测试环境逐项完成：

- Skill 上传、专家保存和八项挂载是否均成功。
- 多课程候选是否通过 `ask_user_question` 选择；学生自己填写计划后是否确实需要确认。
- 订阅字段、稳定 `job_key`、Cron 两阶段切换、失败回滚和暂停/恢复/退订是否符合平台实际接口。
- 唯一个人会话的发送成功、失败重试，以及多候选时停止不群发。
- `ready`、无课程证据、无候选和互动新闻展开是否能在 PDS 中得到可追溯输出。

请勿在文档、平台备注、测试消息或日志中粘贴 Token、Cookie、Authorization、真实学生 ID 或会话 ID。
