# 能力训练 Pro trainV2 WebSocket 协议

完整 REST 与 WebSocket 文档见 [ability-training-pro-api.md](ability-training-pro-api.md)。

## 连接

```text
wss://cloudapi.polymas.com/ai-platform/ws/trainV2
  ?taskId=${TASK_ID}
  &userId=${USER_NID}
  &sessionId=${SESSION_ID}
```

握手使用当前登录态的 `Cookie`，测试脚本同时携带 `Authorization`。不要保存 `Sec-WebSocket-Key` 或完整请求头。

## 客户端事件

```json
{"event":"scriptStart"}
{"event":"stepStart","payload":{"stepId":"${STEP_ID}"}}
{"event":"userTextInput","payload":{"text":"学生回答"}}
{"event":"continueCurrentStep"}
{"event":"heartBeat","payload":{}}
```

## 服务端事件

```text
connected
nextStep
selectRoleStart
selectRoleEnd
botAnswerStart
botAnswer
botAnswerEnd
audioStart
audioEnd
heartbeatAck
stepEnd
scriptEnd
error
```

处理顺序：

1. 连接后立即发送 `scriptStart`。
2. 收到 `nextStep.nextStepId` 后发送 `stepStart`。
3. `selectRoleEnd.roleNid == "user"` 时发送 `userTextInput`，再发送一次 `continueCurrentStep`。
4. 其他角色等待 `botAnswerEnd`，记录完整 `payload.content`，再发送一次 `continueCurrentStep`。
5. 每 30 秒发送应用层 `heartBeat`。
6. `stepEnd` 仅标记当前步骤结束，`scriptEnd` 才表示任务完成。

`roleNid="system"` 是主理人/教练点评，应单独标记，不要作为普通角色对话。
