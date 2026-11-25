# polymas-proxy

把 llm-service 网关的**非标准流式响应**改写成 OpenAI 标准，让 DSH（及任何兼容客户端）能真正用上
`claude-opus-5`、`gpt-5.6-sol` 等模型。

## 为什么需要

网关（Spring）有三处不符合 OpenAI 契约 / 会破坏数据，详见
[../llm-service-网关兼容性问题报告.md](../llm-service-网关兼容性问题报告.md)：

| 网关行为 | 标准 | 后果 |
|---|---|---|
| 流式分片把增量内容放在 `choices[].message` | `choices[].delta` | 客户端读不到任何输出 → `EMPTY_RESPONSE` |
| `usage` 里 token 计数是字符串 `"19"` | number `19` | 客户端累加退化成字符串拼接，污染持久化数据 |
| 流结束不发 `data: [DONE]` | 必须发 | 部分客户端等待到超时 |
| **请求里超过 `2147483647` 的 JSON 整数被写成字符串** | 保持 number | 工具 schema 校验失败（如 Claude Code 的 `maximum: 9007199254740991`）→ 上游报 `JSON schema is invalid` |

## 它做什么

四项改写，其余原样透传：

**响应侧**（三个）：

1. 请求 `stream: true` 时，把 SSE 分片里的 `choices[].message` 改名为 `choices[].delta`
   （内容本身就是增量切片，只差键名）；
2. `usage` 里的字符串数字转成真数字（流式与非流式都做）；
3. 流结束时补上缺失的 `data: [DONE]`。

**请求侧**（两个，仅在确有需要时改写）：

4. 工具定义里越界的数值约束：值等于 `±Number.MAX_SAFE_INTEGER` 的**删除**该关键字
   （语义上就是"无上限/无下限"），其他超过 `2147483647` 的**钳到上限**。
   只处理数值约束关键字（`maximum`/`minimum`/`exclusiveMinimum`/`minLength`/`maxItems` 等），
   **不碰** `default`/`const`/`enum`/`examples` 这些数据位置，也不碰 messages。
   实测：网关 `2147483647` 通过、`2147483648` 就报
   `'2147483648' is not of type 'number'`。
5. `role: "developer"` → `"system"`。OpenAI 新规范用 developer 取代 system，
   但阿里百炼/DashScope 等上游只认 system，会报
   `developer is not one of ['system','assistant','user','tool','function']`。两者语义相同，改写无副作用。

**非流式响应的 `choices[].message` 是正确的，绝不改写。** 鉴权头原样透传，本服务不保存任何密钥。

请求体只在第 4、5 项触发时才会重新序列化；否则逐字节透传（未触发时 `messages`/`tools`/`max_tokens` 完全不变）。

零依赖，仅 Node 标准库。

## 运行方式

已装成 launchd 常驻服务（登录自启、崩溃自动重启）：

```bash
# 状态
launchctl list | grep polymas
curl -s http://127.0.0.1:8787/healthz

# 日志
tail -f ~/Library/Logs/polymas-proxy.log
tail -f ~/Library/Logs/polymas-proxy.err.log

# 停止（本次登录内）
launchctl bootout gui/$(id -u)/com.polymas.proxy

# 启动
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.polymas.proxy.plist

# 彻底卸载（含自启）
launchctl bootout gui/$(id -u)/com.polymas.proxy
rm ~/Library/LaunchAgents/com.polymas.proxy.plist
```

手动前台运行（调试方便）：

```bash
POLYMAS_PROXY_DEBUG=1 node polymas-proxy.mjs
```

## 配置（环境变量）

| 变量 | 默认 | 说明 |
|---|---|---|
| `POLYMAS_PROXY_PORT` | `8787` | 监听端口 |
| `POLYMAS_PROXY_HOST` | `127.0.0.1` | 监听地址（只本机） |
| `POLYMAS_PROXY_UPSTREAM` | `http://llm-service.polymas.com/api/openai` | 上游根；请求 `/v1/xxx` 转发到 `<上游>/v1/xxx` |
| `POLYMAS_PROXY_MAX_INT` | `2147483647` | 工具 schema 里数值约束的安全上限（网关按 32 位整数解析） |
| `POLYMAS_PROXY_DUMP_DIR` | 关 | 设了就把每个**请求体**原样落盘到该目录；排查上游 schema 问题用，平时别开 |
| `POLYMAS_PROXY_DEBUG` | 关 | 打开后输出每行 SSE 的调试信息 |

## DSH 侧配置

`~/.dsh/profiles/desktop/cordis.patch.yml` 里 polymas provider 的 baseURL 指向本服务：

```yaml
      polymas:
        apiKeyEnv: POLYMAS_API_KEY
        api: openai-completions
        baseURL: http://127.0.0.1:8787/v1/     # 回退直连：https://llm-service.polymas.com/api/openai/v1/
```

配置是热加载的，改完下一个请求即生效，无需重启 DSH。

## 验证

```bash
K="<你的 LLM_API_KEY>"

# 流式：应看到 delta、数字 usage、末尾 [DONE]
curl -sN http://127.0.0.1:8787/v1/chat/completions \
  -H "Authorization: Bearer $K" -H "Content-Type: application/json" \
  -d '{"model":"claude-opus-5","messages":[{"role":"user","content":"say PONG"}],"max_tokens":64,"stream":true}' | head

# 非流式：message 保留、usage 为数字
curl -s http://127.0.0.1:8787/v1/chat/completions \
  -H "Authorization: Bearer $K" -H "Content-Type: application/json" \
  -d '{"model":"claude-opus-5","messages":[{"role":"user","content":"say PONG"}],"max_tokens":64}'
```

## 注意

这是**客户端侧补救**。根因在网关：把流式分片的 `message` 改成 `delta`、token 计数返回数字即可
（报告已备好，可直接转发）。网关修好后卸载本服务、把 baseURL 改回直连即可，无需其他改动。

本服务挂了时 polymas 路由会连接失败（其他 provider 不受影响）。
