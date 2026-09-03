# 案例库更新状态机

## 发布链路

1. `[CALL]` 读取教师上传文件，按独立案情边界拆分候选案例。
2. `[FILTER]` 校验敏感信息、字段缺失、来源和证据状态。
3. `[FILTER]` 与当前版本按标题和事实特征查重，生成新增、疑似重复、冲突和场景未决项。
4. `[BUILD]` 生成批量变更预览；正常新增可批量接受，异常项逐项处理。
5. `[CONFIRM]` 调用 `ask_user_question` 展示变更内容与明确动作选项，并真正等待；内部保留该预览的 `change_set_id`。
6. `[CALL]` 使用已确认变更、`base_version`、当前会话 nonce 和同一 `change_set_id` 创建不可变候选版本；脚本重算哈希、检查一次性消费账本，在候选目录中完成数据、HTML 和知识包一致性校验。
7. `[CALL]` 原子切换 `current.json` 版本指针；旧版本保留用于回滚。
8. `[CALL]` 调用平台资源上传与知识蒸馏能力。
9. `[FILTER]` 使用案例 ID 回读新知识；只有查询到同版本内容才把知识同步标为成功。

## 状态定义

| 状态 | 含义 | 可否告知“专家已更新” |
|---|---|---|
| `needs_resolution` | 存在重复、冲突、场景或证据异常 | 否 |
| `preview_ready` | 预览已就绪，等待教师确认 | 否 |
| `awaiting_confirmation` | 尚未收到真实确认工具结果 | 否 |
| `version_conflict` | 当前版本已变化，需重新预览 | 否 |
| `artifact_ready_knowledge_pending` | 新数据、HTML、知识包已生成，知识库尚未回读验证 | 否 |
| `knowledge_verified` | 平台写入与按案例 ID 回读均成功 | 是 |
| `knowledge_state_unknown` | 上传超时或回执不确定 | 否，旧知识版本继续服务 |
| `confirmation_already_used` | 发布或回滚确认已被消费 | 否，重新预览和确认 |
| `candidate_release_invalid` | 候选数据、场景、HTML 或知识包不一致 | 否，删除候选并保留旧版本 |

## 回滚

回滚只切换到已存在且校验通过的不可变版本。回滚同样属于写操作，必须调用 `ask_user_question` 明确确认。指针切换后重新上传对应知识包并回读；回读前状态仍为 `artifact_ready_knowledge_pending`。

本地执行先使用 `rollback_release.py <library_root> <target_version> --actor-reference <actor_reference>` 获取 from→to 预览和 `rollback_confirmation_id`。上游 `ask_user_question` 确认后，再追加 `--confirmed --confirmation-rollback-id <rollback_confirmation_id>`。目标版本数据、HTML、知识包和内容摘要都会参与绑定；缺失或改变时停止。

## 并发

变更集携带 `base_version`。发布前发现当前版本不同即返回 `version_conflict`，展示新旧差异并重新确认；后提交者不能覆盖先发布者。
