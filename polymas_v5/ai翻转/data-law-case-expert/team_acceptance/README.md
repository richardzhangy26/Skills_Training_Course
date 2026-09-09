# 专家团验收 CLI

需要“按功能标准最多修复3轮”时，从 [接手入口](START_HERE.md) 和 [迭代执行说明](ITERATION_RUNBOOK.md) 开始，使用 `iterate_expert_team.py`。该流程锁定标准并限制专家文件修改范围；当前编辑与发布仍由外层 Agent 使用实际平台能力执行，Skill 源码回读未验证时明确阻断。

对教师个人资源库中已配置好的 AI 助教专家团执行预检、测试对话、独立历史回读和确定性验收。无需先发布 PDS 配置。`run` 会向配置中的助教发送测试消息；测试内容限定为查询与讲解。`preflight` 和 `evaluate` 不发送消息。

在 `data-law-case-expert` 目录运行：

需要 Python 3.11 或更新版本及 `requests`。可直接使用根目录 `test_expert_team.py`，与下面的 `python -m team_acceptance` 等价。

```bash
python -m team_acceptance run --config team_acceptance/examples/data-law-team.json --env-file "$TEAM_ENV_FILE" --run-id teacher-team-001 --report-prefix "$TEAM_REPORT_PREFIX"
python -m team_acceptance preflight --config team_acceptance/examples/data-law-team.json --env-file "$TEAM_ENV_FILE" --report-prefix "$TEAM_REPORT_PREFIX"
python -m team_acceptance evaluate --config team_acceptance/examples/data-law-team.json --evidence "$TEAM_EVIDENCE_FILE" --report-prefix "$TEAM_REPORT_PREFIX"
```

独立 ZIP 解压后，在解压目录执行 `python -m pip install -r requirements.txt`，再运行上述命令。包中不含认证文件或本轮对话报告。

`TEAM_ENV_FILE` 等变量由操作者指定。预检只使用显式 `--env-file` 中的 `AUTHORIZATION`、`COOKIE`，不会读取默认 `.env` 或继承 shell 中的认证字段。可选 `POLYMAS_BASE_URL` 和 `POLYMAS_TIMEOUT_SECONDS` 交由共享 `RequestsTransport` 校验。离线 evaluate 不加载凭证。

stdout 始终输出单个 JSON。退出码：`0` 表示声明的对话断言全部通过；`1` 表示发现不符；`2` 表示输入、认证或报告 I/O 错误；`3` 表示证据未核验完整。报告每项状态只有 `pass`、`fail`、`unverified`。预检成功仍为 `unverified`，不能据此宣称真实对话完成。

## 自动运行

`run` 先验证当前教师对助教的访问权、专家启用关系和精确版本，再逐条向 `/ai-agent/assistant/v1/chat/stream` 发送用例。只有收到 `ALL_FINISHED` 并从 `/chatim/v1/robot/chat/history` 回读到同一回答标识、trace、方向、正文和 `DONE` 状态，才通过对话传输验收。请求中的专家 NID 还需与流中实际专家名称匹配，不能仅凭请求参数认定专家已执行。

该教师发送协议于 2026-09-05 经真实 API 发送和独立 history 回读验证。请求产生的回答标识可用于回读；服务器会重写 `msgId/msgKey`，因此脚本不以其作为请求与回答的关联键。服务端当前只持久化了回答，测试提问保存在本地报告，报告如实标注 `input_persisted: false`。

每轮运行默认保存到 `.online-e2e-state/team-acceptance/`，支持 `--state-dir` 覆盖；报告默认位于 `reports/team-acceptance/<run_id>.json/.md`。复用同一 `run_id` 和同一配置只返回已有结果，不重复发送。首次发送前持久保存待执行关联键与助教停写标记；超时、回读不匹配或进程退出后，后续同助教运行返回 `RECOVERY_REQUIRED`。需要人工按 trace/回答标识对账后再处理停写记录，本版本不做自动重试或跨进程续跑。

`run` 的报告标为 `captured-live-api`，并保留本次预检和实际对话。内容断言失败表示专家没有达到所配置的预期；脚本执行并拿到失败结果仍是一次有效验收。此入口不承担学生端、知识库写入/清理或专家发布验收。

## 配置

`schema_version` 为 `1`。`assistants` 支持多个助教，每个助教有精确 `name`、`nid` 与 `experts` 列表。专家声明 `name`、`nid`、`expected_version`，可用 `knowledge_bindings` 指定必须存在的知识库 NID。其他已有绑定不会被修改。示例使用法学测试助教与 v6 数据法学案例专家；这些业务标识仅存在于示例数据。

每个 `cases` 用例需要唯一 `id`、已声明的 `assistant_nid` 和 `expert_nid`、`read_only: true`、`prompt` 和 `assertions`。断言支持：

- `terminal_status`：允许的已完成终态，真实 SSE 使用 `ALL_FINISHED`。`ERROR`、`INTERRUPTED` 等不是完成状态。
- `contains_all`：正文必须包含所有字面片段。
- `contains_any`：正文至少包含一个字面片段。
- `forbidden`（兼容 `excludes`）：正文不能包含任何片段。
- 用例级 `required_evidence_fields`：需要证据 `prerequisites` 中相应字段为 `true`；缺少时内容断言为 `unverified`。

字面匹配不替代法律准确性或幻觉审查。示例不要求向用户展示内部案例 ID；验收通过仅表示已声明的确定性断言满足。

## 预检

依次读取 current-user 并校验 `school_teacher`，读取关系清单并精确匹配 V5 课程助教。每个助教只读取一次 full config 快照，从同一快照核对各专家唯一性、名称、启用状态及版本；再只读查询知识绑定。报告脱敏后保留快照与摘要，不记录真实用户身份。

使用已验证的只读 endpoint profile；绑定查询虽然采用 POST，但只调用 `/bind/list`。不使用旧 runner 的生产助教或重新发布条件。

## 归一化对话证据

输入为 `{"schema_version":1,"records":[...]}`。每条 record 包含以下字段：

```json
{
  "case_id": "example-query",
  "source": "live-api",
  "captured_at": "2026-09-05T10:00:00+08:00",
  "assistant_nid": "example-assistant",
  "expert_nid": "example-expert",
  "session_id": "",
  "isolation": "existing-test-assistant-conversation",
  "message_id": "example-answer-nid",
  "trace_id": "example-trace",
  "prompt": "配置中的原始提示词",
  "terminal_status": "ALL_FINISHED",
  "response": "最终 ANSWER 正文",
  "prerequisites": {"knowledge_retrieved": true},
  "send": {
    "confirmed": true,
    "source": "live-api",
    "assistant_nid": "example-assistant",
    "expert_nid": "example-expert",
    "session_id": "",
    "message_id": "example-answer-nid",
    "trace_id": "example-trace",
    "prompt": "配置中的原始提示词",
    "captured_request": {
      "assistant_nid": "example-assistant",
      "prompt": "配置中的原始提示词",
      "input_chat_nid": "example-input-nid",
      "answer_chat_nid": "example-answer-nid",
      "trace_id": "example-trace"
    }
  },
  "readback": {
    "confirmed": true,
    "source": "live-api",
    "kind": "history",
    "assistant_nid": "example-assistant",
    "expert_nid": "example-expert",
    "session_id": "",
    "message_id": "example-answer-nid",
    "trace_id": "example-trace",
    "terminal_status": "ALL_FINISHED",
    "response": "最终 ANSWER 正文",
    "messages": [{
      "role": "assistant",
      "assistant_nid": "example-assistant",
      "expert_nid": "example-expert",
      "session_id": "",
      "message_id": "example-answer-nid",
      "trace_id": "example-trace",
      "terminal_status": "ALL_FINISHED",
      "text": "最终 ANSWER 正文"
    }]
  }
}
```

`source` 仅允许 `live-ui`、`live-api`、`synthetic`，导入报告固定标记 `evidence_origin: imported`，不会独立认证文件来源。`synthetic` 不能通过在线证据项。任何现场采集器必须从真实请求和独立 history 生成证据；不得将预期回答写成已观察回答。

`message_id` 使用可回读的 `answerChatNid` / history `nid`，不要使用服务器可能重写的请求 `msgId`。发送、record、history 必须匹配助教、专家、回答标识、trace、最终正文和终态。`live-api` 允许只持久化回答，此时用已捕获请求的 prompt、inputChatNid、answerChatNid、trace 关联，报告 `input_persisted: false`。`live-ui` 还必须有同会话、同助教、同文本的 user history 消息。`confirmed: true` 单独不足以通过。

真实会话 API 尚无新会话隔离证据时，允许 `session_id: ""` 与明确的 `isolation` 字段，并将 `session_isolation` 单列为 `unverified`。不能用 trace、run ID 或随机值冒充平台 session ID。

## 注入接口与文件安全

`core.preflight(config, transport)` 接受共享 Transport 的 `request` 接口；`core.evaluate(config, evidence)` 无网络；`cli.main(argv, transport_factory=...)` 支持测试注入。线上发送适配器可独立实现并将返回证据交给 evaluate，禁止猜測 API。

stdout、JSON 和 Markdown 使用 `online_e2e.safety.sanitize_json`；保留业务 trace/session/message IDs，脱敏用户身份与凭证。报告采用共享 private atomic 写入，文件权限 `0600`、目标目录权限 `0700`。仅处理操作者显式指定的配置、证据和报告路径。

验证命令：`python -m pytest -q tests/test_team_acceptance.py tests/test_team_acceptance_cli.py tests/test_team_acceptance_live_chat.py`。测试使用标注的 synthetic 样本，不等同于真实平台验收；真实结果由 `run` 生成。
