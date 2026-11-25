# llm-service 网关 OpenAI 兼容性问题报告

| 项 | 值 |
|---|---|
| 网关 | `http://llm-service.polymas.com/api/openai/v1` |
| 接口 | `POST /chat/completions` |
| 检测时间 | 2026-10-12 |
| 检测方式 | 直连网关（`Authorization: Bearer <key>`），不经过任何客户端 |
| 复现脚本 | [`llm-service-兼容性检测.py`](./llm-service-兼容性检测.py)（仅标准库，一条命令跑完） |

---

## 摘要

| # | 问题 | 严重度 | 命中率 |
|---|---|---|---|
| 1 | 流式响应把增量内容放在 `choices[].message`，而非 OpenAI 标准的 `choices[].delta` | **阻塞** | 15 / 15 个有响应的模型 |
| 2 | `usage` 里的 token 计数被序列化成 JSON **字符串**而非 number | 高 | 11 / 16 个模型 |
| 3 | 流结束没有 `data: [DONE]` 终止符 | 低 | 全部 |
| 4 | 低概率偶发 `HTTP 502` / 超时 | 低 | 32 次小请求中 1 次超时；较高并发/长请求时出现过 502 |
| 5 | 请求里超过 `2147483647` 的 JSON 整数被写成字符串，导致工具 schema 校验失败 | **阻塞**（Agent 场景） | 阈值精确：`2147483647` 通过、`2147483648` 失败 |

问题 1 会让**任何按 OpenAI 规范解析流式的客户端**（DSH、Cursor、Cline、LangChain、openai SDK…）
完全拿不到模型输出，表现为"空响应 / EMPTY_RESPONSE"，重试后整轮失败。
问题 2 会让客户端的 token 累加变成字符串拼接（`0 + "13"` → `"013"`），污染统计甚至破坏持久化数据。
问题 5 会让带工具定义的请求（几乎所有 Agent/IDE 客户端）直接失败，见下节。

---

## 问题 1：流式分片用 `message` 而不是 `delta`（阻塞）

### 复现

```bash
curl -N -s http://llm-service.polymas.com/api/openai/v1/chat/completions \
  -H "Authorization: Bearer $LLM_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"claude-opus-5","messages":[{"role":"user","content":"Reply with exactly one word: PONG"}],"max_tokens":32,"stream":true}'
```

### 实际收到（截取）

```
Content-Type: text/event-stream;charset=UTF-8

data:{"usage":{"prompt_tokens":"19","completion_tokens":"2","total_tokens":"21"},"id":"chatcmpl-…","object":"chat.completion.chunk","choices":[]}
data:{"id":"chatcmpl-…","object":"chat.completion.chunk","choices":[{"index":0,"message":{"role":"assistant","content":""}}]}
data:{"id":"chatcmpl-…","object":"chat.completion.chunk","choices":[{"index":0,"message":{"role":"assistant","content":""}}]}
data:{"id":"chatcmpl-…","object":"chat.completion.chunk","choices":[{"index":0,"message":{"role":"assistant","content":"PONG"}}]}
data:{"usage":{"prompt_tokens":"19","completion_tokens":"21","total_tokens":"40"},"id":"chatcmpl-…","object":"chat.completion.chunk","choices":[{"index":0,"message":{"role":"assistant","content":""},"finish_reason":"stop"}]}
```

### 期望（OpenAI `ChatCompletionChunk` 契约）

```
data:{"id":"chatcmpl-…","object":"chat.completion.chunk","choices":[{"index":0,"delta":{"role":"assistant","content":""}}]}
data:{"id":"chatcmpl-…","object":"chat.completion.chunk","choices":[{"index":0,"delta":{"content":"PONG"}}]}
data:{"id":"chatcmpl-…","object":"chat.completion.chunk","choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}
data:{"id":"chatcmpl-…","object":"chat.completion.chunk","choices":[],"usage":{"prompt_tokens":19,"completion_tokens":21,"total_tokens":40}}
data: [DONE]
```

### 关键点：分批逻辑本身是对的，只差字段名

把各分片的 `message.content` 按顺序拼接，得到的正是完整句子：

```
"I" + "'ll check the we" + "ather in" + " Beijing for you."   →   "I'll check the weather in Beijing for you."
```

也就是说内容已经是**增量切片**，只是被放进了 `message`（非流式字段）而不是 `delta`。
**修复不需要改动分批/流式逻辑，只需把流式分片里的键名 `message` 改为 `delta`。**

### 工具调用同样受影响

Agent 场景必须能用工具，实测（`claude-opus-5` + `tools`）：

```
data:{…"choices":[{"index":0,"message":{"content":null,"tool_calls":[{"id":"toolu_bdrk_…","type":"function","function":{"name":"get_weather","arguments":""}}]}}]}
data:{…"choices":[{"index":0,"message":{"content":null,"tool_calls":[{"index":0,"function":{"arguments":"{\"city\": "}}]}}]}
data:{…"choices":[{"index":0,"message":{"content":null,"tool_calls":[{"index":0,"function":{"arguments":"\"Beij"}}]}}]}
```

`index`、增量 `arguments` 都是标准写法，同样只是键名应为 `delta`。
实测 4 个模型（`claude-opus-5` / `claude-opus-4-8` / `claude-sonnet-5` / `gpt-5.6-sol`）
工具调用分片 100% 使用 `message`。

**但工具调用能力本身是完好的，不需要改逻辑：** 非流式模式下，配置里的 **19/19 个模型全部**
返回完全标准的 `tool_calls`（正确的 `name` + 完整 JSON `arguments`）：

```
claude-opus-5            OK get_weather {"city":"Beijing"}
claude-sonnet-5          OK get_weather {"city":"Beijing"}
…（19/19 全通过，含 kimi-k3 / glm-5.2 / qwen3.8-max / grok-4 / Doubao-Seed-2.1-pro 等）
```

流式模式下 18/19 也把工具调用送出来了（结构标准，只是挂在 `message` 下）。
**结论：张冠李戴的只有流式分片的键名，工具调用的生成、分批、参数拼装都无需改动。**

### 下游实际表现（DSH 会话日志实录）

客户端读取 `delta`，因此看到的是"完成但无内容"的响应，被判为空响应并重试 5 次后失败：

```json
{"type":"assistant/attempt","data":{"turn":1,"step":1,"stream":[
  {"type":"chunk","chunk":{"type":"usage","usage":{"inputTokens":16050,"outputTokens":5,"totalTokens":16055}}},
  {"type":"chunk","chunk":{"type":"finish","reason":{"kind":"error","failure":{
      "message":"model \"claude-opus-5\" returned a completed response with no content",
      "code":"EMPTY_RESPONSE"}}}}
]}}
```

对应的重放状态里内容块为空：`"blocks": []`。

---

## 问题 2：`usage` 计数被序列化成字符串

### 实际 / 期望

```json
// 实际
{"usage":{"prompt_tokens":"19","completion_tokens":"21","total_tokens":"40"}}
// 期望
{"usage":{"prompt_tokens":19,"completion_tokens":21,"total_tokens":40}}
```

### 影响

1. **客户端数值累加退化为字符串拼接**：`0 + "13"` → `"013"`，
   再累加得到 `"131313131313"`；`total_tokens` 更是在上游就被拼成
   `"2666" + "13" + "0" + "0"` = `"26661300"` 这样的垃圾值。
2. **破坏持久化数据的类型契约**：客户端一旦把该值写入带类型校验的存储，
   后续读取即失败，历史记录直接打不开（本次已实际发生并造成 3 个会话不可读）。
3. 成本/用量统计全错。

### 命中情况（同一网关上按上游不同）

| 返回字符串（需修，11 个） | 返回 number（正常，4 个） |
|---|---|
| `claude-opus-5`、`claude-opus-4-8`、`claude-sonnet-5`、`gpt-5.6-sol`、`gpt-5.5`、`gpt-5.4`、`kimi-k3`、`glm-5.2`、`qwen3.8-max`、`gemini-3.1-pro-preview`、`gemini-3.0` | `deepseek-v4-pro`、`deepseek-v4.1-flash`、`Doubao-Seed-2.1-pro`、`Doubao-Seed-2.0-Code` |

> `grok-4` 本轮返回 502 未取到样本；首轮实测同为字符串，一并修即可。

### 修复建议

排查该路径上的序列化：若使用的是 Jackson 且字段类型为 `String`（或经过 `String.valueOf(...)` /
手工拼装 JSON），请改为数值类型输出。注意**非流式**响应有同样问题，需一并修复。

---

## 问题 3：缺少 `data: [DONE]`

SSE 流在最后一个分片后直接结束，没有 OpenAI 标准的 `data: [DONE]` 终止符。
依赖该标记判断结束的客户端可能等待到超时。共 9 个 `data:` 分片，最后一个即上面的 finish 分片。

---

## 问题 4：低概率偶发 502 / 超时

- 32 次小请求（`max_tokens:16`、8 并发）探测：31 成功、1 次超时（`gpt-5.5`）、**0 次 502**。
- 在更高并发 + 较长上下文（16 模型并发跑流式 + 工具调用）时，观察到随机
  `HTTP 502 Bad Gateway`，命中过 `claude-opus-5`、`claude-sonnet-5`、`gpt-5.4`、`grok-4`，
  重试即可通过。

属低概率偶发，不影响上述结论，但建议关注上游超时与重试策略。

---

## 问题 5：超过 `2147483647` 的 JSON 整数被写成字符串（Agent 场景阻塞）

与问题 2 同源：**网关把数字序列化成字符串**。区别是这次发生在**请求**方向，受害字段在工具定义里。

### 复现（阈值为 2³¹−1，非常干净）

```bash
for N in 2147483647 2147483648; do
curl -s http://llm-service.polymas.com/api/openai/v1/chat/completions \
  -H "Authorization: Bearer $LLM_API_KEY" -H "Content-Type: application/json" \
  -d "{\"model\":\"gpt-5.6-sol\",\"max_tokens\":8,\"messages\":[{\"role\":\"user\",\"content\":\"hi\"}],
       \"tools\":[{\"type\":\"function\",\"function\":{\"name\":\"f\",\"description\":\"d\",
       \"parameters\":{\"type\":\"object\",\"properties\":{\"n\":{\"type\":\"integer\",\"maximum\":$N}}}}}]}"
done
```

实测：

| `maximum` | 结果 |
|---|---|
| `100` | 200 通过 |
| `2147483647`（`Integer.MAX_VALUE`） | 200 通过 |
| `2147483648` | 500 `Invalid schema for function 'f': '2147483648' is not of type 'number'` |
| `9007199254740991` | 500 同上（值是 `Number.MAX_SAFE_INTEGER`） |

注意错误信息里数字被**加了引号** —— 说明网关把它当字符串发给了上游。

### 影响面（已实际发生）

Claude Code（本地工具集）发出的 131 个工具定义里有 **59 处** `"maximum": 9007199254740991`
（以及 4 处 `minimum: -9007199254740991`），全部是 JS 生态表示"无上下限"的惯用写法。经本网关后：

```
claude-opus-5 → 500
  InvokeModelWithResponseStream: ... ValidationException:
  tool.custom.input_schema: JSON schema is invalid. It must match JSON Schema draft 2020-12
```

结果是 **Claude Code 无法通过本网关使用 `claude-opus-5`**（`claude-sonnet-5` 走另一条上游、
校验较松则可以通过）。所有发工具定义的 Agent/IDE 客户端都可能踩到。

### 修复建议

同一个修复点：**JSON 数字一律按数值类型序列化**，不要落到 `Integer`/字符串上。
若确实需要 32 位整数字段，请对超出范围的输入报错而不是静默转字符串。

### 客户端侧规避（已在我方本地反代实现，仅作参考）

- 值等于 `±Number.MAX_SAFE_INTEGER` 的数值约束 → 删除该关键字（语义上等于"无界"）
- 其他超过 `2147483647` 的 → 钳到上限
- 只处理数值约束关键字，不动 `default`/`const`/`enum` 等数据位置

---

## 附：非流式对照（正常）

```bash
curl -s http://llm-service.polymas.com/api/openai/v1/chat/completions \
  -H "Authorization: Bearer $LLM_API_KEY" -H "Content-Type: application/json" \
  -d '{"model":"claude-opus-5","messages":[{"role":"user","content":"Reply with exactly one word: PONG"}],"max_tokens":32}'
```

```json
{"choices":[{"index":0,"message":{"role":"assistant","content":"PONG"},"finish_reason":"stop"}],
 "usage":{"prompt_tokens":"19","completion_tokens":"21","total_tokens":"40"}}
```

说明：**非流式路径的内容字段是标准的**（`choices[].message` 在非流式下本就正确），
问题 1 只出在流式路径；问题 2 两条路径都有。

---

## 附：实测结果（16 个模型，单次完整运行，退出码 1）

```
网关: http://llm-service.polymas.com/api/openai/v1/chat/completions
模型: 16 个

【问题 1】流式字段：delta（标准） vs message（非标准）
model                          delta   message  文本           usage 类型
claude-opus-5                  False      True  'PONG'         字符串 ✗
claude-opus-4-8                False      True  'PONG'         字符串 ✗
claude-sonnet-5                False      True  'PONG'         字符串 ✗
gpt-5.6-sol                    False      True  'PONG'         字符串 ✗
gpt-5.5                        False      True  'PONG'         字符串 ✗
gpt-5.4                        False      True  'PONG'         字符串 ✗
deepseek-v4-pro                False      True  ''             number ✓
deepseek-v4.1-flash            False      True  'PONG'         number ✓
kimi-k3                        False      True  ''             字符串 ✗
glm-5.2                        False      True  'P'            字符串 ✗
qwen3.8-max                    False      True  'PONG'         字符串 ✗
gemini-3.1-pro-preview         False      True  ''             字符串 ✗
gemini-3.0                     False      True  ''             字符串 ✗
grok-4                             -         -  HTTP 502
Doubao-Seed-2.1-pro            False      True  'PONG'         number ✓
Doubao-Seed-2.0-Code           False      True  'PONG'         number ✓
```

- `delta` 列全为 `False` / `-`：**没有任何模型返回标准字段**。
- 表中"文本"为空的几行是**本探测的参数所致，非网关问题**：探测用 `max_tokens: 32`，
  而 `deepseek-v4-pro`、`glm-5.2`、`kimi-k3`、`gemini-3.x` 等推理型模型会把预算全部用在
  思考上（`completion_tokens` 正好等于 32，内容在 `reasoning_content`），`content` 因而为空；
  把 `max_tokens` 提到 512 后这些模型均正常返回 `PONG`。此项**无需网关方处理**。

---

## 附：修复后的验收方式

```bash
LLM_API_KEY=sk-xxx python3 llm-service-兼容性检测.py
```

- **退出码 0** = 问题 1、2 都已修复
- `delta` 列应为 `True`、`message` 列应为 `False`
- usage 类型应全部为 `number`
- 工具调用一节的 `delta_tool_calls` 应为 `True`

修好后**无需改动任何客户端**：DSH 及其他 OpenAI 兼容客户端即可直接使用本网关的
`claude-opus-5`、`gpt-5.6-sol` 等全部模型。
