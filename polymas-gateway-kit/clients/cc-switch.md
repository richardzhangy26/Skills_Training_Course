# 把 polymas 网关接进 CC Switch（Claude Code / pi 两个 app）

> 前置：反代已跑起来（`../install.sh` 之后 `curl -s http://127.0.0.1:8787/healthz` 有返回）。

## 为什么 Claude Code 必须经过 CC Switch 的本地代理

Claude Code 讲 **Anthropic Messages 协议**（`/v1/messages`），而 llm-service 只有
**OpenAI 兼容**端点（`/api/anthropic/...`、`/v1/messages` 等路径实测全 404）。
CC Switch 4.x 自带的本地代理能做 **Anthropic ⇄ OpenAI** 转换（provider 的
`apiFormat` 支持 `openai_chat`），所以链路是三层：

```
Claude Code ──Anthropic──▶ CC Switch 本地代理 ──OpenAI──▶ polymas-proxy ──▶ 网关
                                (协议转换)                 (格式改写)
```

**两层都不可省**：CC Switch 负责协议；polymas-proxy 负责网关那三个毛病
（`message`/`delta`、字符串 usage、int32 越界），详见 `../docs/gateway-report.md`。

---

## A. Claude Code

在 CC Switch 里 **切到 Claude 这个 app**，添加/编辑一个自定义供应商：

| 字段 | 填什么 |
|---|---|
| 名称 | `Polymas 网关`（随意） |
| 官网链接 | `http://llm-service.polymas.com`（若必填） |
| API Key | 你的 `LLM_API_KEY`（`sk-…`） |
| 请求地址 | `http://127.0.0.1:8787/v1` ← **反代地址，不是网关地址** |
| 高级选项 → **上游格式** | **OpenAI Chat Completions（需开启路由）** |
| 完整 URL | 关 |

模型映射（4 档都填上网关里真实存在的 id）：

| 模型角色 | 实际请求模型 |
|---|---|
| Opus | `claude-opus-5` |
| Sonnet | `claude-sonnet-5` |
| Fable | `claude-opus-5` |
| Haiku | `claude-4.5-haiku` ← **别填 `claude-haiku-4-5`，网关没有这个 id（会 401）** |

然后：

1. **打开 Claude 的本地代理**（设置里那个开关）。不开的话 CC Switch 只会把
   `ANTHROPIC_BASE_URL` 原样指向反代，Claude Code 会拿 Anthropic 协议去撞 OpenAI 端点。
2. 切到该 provider 成为当前供应商。
3. 「声明支持 1M」这个勾**先别勾**：它只是客户端声明，网关真实上下文上限未确认。

### 验收

```bash
claude -p --model opus 'reply with exactly: PONG'     # 期望 PONG
claude -p '用 bash 执行 echo ok，然后只回复输出'        # 期望 ok（工具调用往返）
```

CC Switch 内部记录了每次请求，排错很有用：

```bash
sqlite3 ~/.cc-switch/cc-switch.db \
 "select datetime(created_at,'unixepoch','localtime') t, model, status_code, substr(coalesce(error_message,''),1,80)
  from proxy_request_logs order by created_at desc limit 10"
```

### 常见报错对照

| 报错 | 原因 | 处理 |
|---|---|---|
| `tool.custom.input_schema: JSON schema is invalid ... draft 2020-12` | 工具 schema 里有超过 2³¹−1 的整数，被网关写成字符串 | 确认 `baseURL` 指向反代（反代会删/钳这些值） |
| `developer is not one of ['system',...]` | 上游不认 `developer` 角色 | 同上，反代会归一成 `system` |
| `max_tokens: N > 128000` | 客户端把「上下文窗口 − 提示词」当成了 max_tokens | 该模型元数据里 maxTokens 调小（pi 见 B 节；Claude Code 见「1M」勾） |
| 401 `当前模型未配置代理` | 模型 id 在网关不存在 | 用 `curl -s <网关>/v1/models` 里的真实 id |

---

## B. pi

CC Switch 的 **Pi** 页面也能管 `~/.pi/agent/models.json`；也可以直接用脚本写：

```bash
../clients/pi-setup.sh --key sk-xxxx --default claude-opus-5
```

如果走 CC Switch 界面，字段对应关系：

| CC Switch 里的字段 | 值 | 说明 |
|---|---|---|
| baseUrl | `http://127.0.0.1:8787/v1` | 反代地址 |
| api | `openai-completions` | |
| apiKey | 你的 key | |
| 上下文长度 contextWindow | `262144` | **别填 400000/1M**，真实上限未确认 |
| 最大输出 maxTokens | `32000` | **千万别填 1e7**，见下 |

### 为什么 maxTokens 不能填大

pi 的 `clampMaxTokensToContext` 实际发出的是：

```js
max_tokens = min(model.maxTokens, model.contextWindow − 已用提示词 − 4096)
```

把 `maxTokens` 填成 `10000000`、`contextWindow` 填成 `400000` 时，实际发出的是
`400000 − 25379 ≈ 374621`，而上游对 `claude-sonnet-5` 的输出上限是 `128000` →
`500 ValidationException: max_tokens: 374621 > 128000`。

> CC Switch 会**跟随** `~/.pi/agent/models.json`（约 1 分钟内同步进它的库），
> 但反过来你在它界面里点保存也会把值写回文件 —— 两边别同时改。

### 验收

```bash
pi -p 'reply with exactly: PONG'                      # 走默认
pi -p --provider polymas --model kimi-k3 'reply with exactly: PONG'
```
