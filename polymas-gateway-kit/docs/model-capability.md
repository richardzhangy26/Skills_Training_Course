# 模型能力对照表（llm-service 网关，实测）

Agent 客户端（DSH / pi / Claude Code）**每次请求都会带工具定义**，所以「带工具能不能用」
才是这类客户端的关键指标。下表是逐模型实测结果（2026-10，经本地反代）。

| 模型 | 带工具（Agent 场景） | 纯文本 | 说明 |
|---|:---:|:---:|---|
| `claude-opus-5` | ✅ | ✅ | |
| `claude-sonnet-5` | ✅ | ✅ | |
| `claude-opus-4-8` | ✅ | ✅ | |
| `gpt-5.6-sol` | ⚠️ | ✅ | 该上游**不允许「工具 + `reasoning_effort`」共存**。客户端把它声明为**非推理模型**即可正常使用（pi 的 `pi-setup.sh` 已默认这样做） |
| `gpt-6-sol` | ❌ | ✅ | 见下方专节 |
| `gpt-6.1-sol` | ❌ | ✅ | 同上 |
| `gpt-5.5` | ✅ | ✅ | |
| `gpt-5.4` | ✅ | ✅ | |
| `gemini-3.1-pro-preview` | ✅ | ✅ | |
| `gemini-3.0` | ✅ | ✅ | |
| `deepseek-v4-pro` | ✅ | ✅ | 需把 `role:"developer"` 归一成 `system`（反代已处理） |
| `deepseek-v4.1-flash` | ✅ | ✅ | 同上 |
| `kimi-k3` | ✅ | ✅ | |
| `kimi-k2.6` | ✅ | ✅ | |
| `glm-5.2` | ✅ | ✅ | |
| `glm-5-3-260814` | ✅ | ✅ | |
| `qwen3.8-max` | ✅ | ✅ | `developer` 角色问题（反代已处理） |
| `qwen3.7-max` | ✅ | ✅ | 同上 |
| `grok-4` | ✅ | ✅ | |
| `Doubao-Seed-2.1-pro` | ✅ | ✅ | `developer` 角色问题（反代已处理） |
| `Doubao-Seed-2.0-Code` | ✅ | ✅ | 同上 |

> 表格里的 ❌/⚠️ 都是**上游能力限制**，不是配置错误、也不是反代的问题 ——
> 反代只改表示层（键名、数字类型、角色名），不改变模型能力。

---

## `gpt-6-sol` / `gpt-6.1-sol` 为什么用不了

**上游明确要求：带工具必须走 Responses API。**

```
Function tools with reasoning_effort are not supported for gpt-6-sol in /v1/chat/completions.
To use function tools, use /v1/responses or set reasoning_effort to 'none'.
```

实测（经反代，逐项排除）：

| 请求 | 结果 |
|---|---|
| 不带工具 | **200** ✅ |
| 带工具（不传 `reasoning_effort`） | 500 ❌ |
| 带工具 + `reasoning_effort=none`（错误里建议的） | 500 ❌ |
| 带工具 + `reasoning_effort=low` | 500 ❌ |
| 带工具 + 不传 `max_completion_tokens` | 500 ❌ |

两个关键点：

1. **错误里那句 "set reasoning_effort to 'none'" 是无效建议** —— 传 `none` 照样 500。
   真实条件是：该模型在 Chat Completions 上**根本不支持 function tools**。
2. **网关没有 `/v1/responses` 端点**：

   ```bash
   curl -s -o /dev/null -w '%{http_code}\n' -X POST \
     http://llm-service.polymas.com/api/openai/v1/responses \
     -H "Authorization: Bearer $LLM_API_KEY" -H 'Content-Type: application/json' \
     -d '{"model":"gpt-6-sol","input":"hi"}'      # → 404 NOT_FOUND
   ```

   所以上游指的那条路也走不通。

**顺带排除的干扰项**：这两个模型还**不接受 `max_tokens`**，只接受 `max_completion_tokens`
（否则报 `Unsupported parameter: 'max_tokens' ... Use 'max_completion_tokens' instead`）——
但改成正确参数后，带工具依然 500，可见与本条无关。

**结论**：在 DSH / pi / Claude Code 这类**必然发工具**的客户端里，这两个模型当前不可用。
要用它们只能：

- 走**纯文本/推理**调用（自己写脚本 curl，不带 `tools`）；
- 或者请网关方**开放 `/v1/responses`**（或放开该限制）。

**对照**：`gpt-5.6-sol` 是同一个「sol」家族但**带工具可用**（只要客户端不声明推理）；
别把两者混为一谈。
