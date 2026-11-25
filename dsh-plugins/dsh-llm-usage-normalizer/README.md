# @local/dsh-llm-usage-normalizer

把 LLM 网关返回的**字符串型 token 计数**归一化成整数，避免 DSH 会话投影校验失败、
导致历史无法加载。

## 它修的是什么问题

公司 `llm-service` 网关（Spring Boot / Jackson）把 usage 里的 token 数序列化成字符串：

```json
{"usage":{"prompt_tokens":"16","completion_tokens":"13","total_tokens":"18"}}
```

pi-ai 只对减法做隐式数值转换，加法没有：

```js
input  = Math.max(0, promptTokens - cacheRead - cacheWrite)  // 减法 → 数字 ✓
output = completion_tokens || 0                              // 透传 → 字符串 ✗
total  = input + output + cacheRead + cacheWrite             // 加法 → "2666"+"13"+"0"+"0"
```

于是 `totalTokens` 成为拼接出来的垃圾值 `"26661300"`；`dsh-token-meter` 在累加
`outputTokens` 时同样用加法（`totals - previous + next`），字符串一路滚雪球，
最终状态违反 `z.number().int().nonnegative()`：

```
failed to project session "session-…": invalid_type expected number received string
path ["outputTokens"]
```

后果是该会话的历史**再也打不开**，并且每次用该网关的模型都会再产生一条坏记录。

诊断链路（可复现）：

| 环节 | 代码 | 结果 |
|---|---|---|
| 网关 | `POST /api/openai/v1/chat/completions` | `"completion_tokens":"13"` |
| pi-ai | `@earendil-works/pi-ai` `parseChunkUsage` | `output` 保持字符串 |
| 适配器 | `dsh-llm-pi-ai` `mapUsage` | `outputTokens: "13"` |
| 投影 | `dsh-token-meter` `usage-projection.js` | 字符串累加 → 抛错 |

## 它怎么修

`llm/stream` 是 DSH 为中间件提供的 waterfall 扩展点：

```js
streamWithRegistration(options, prepared) {
  return this.ctx.waterfall(this, 'llm/stream', options, () => this.adapterStream(options, prepared))
}
```

本插件以 `{ global: true, prepend: true }` 注册监听器，在最外层包住分片流，在 usage
分片离开适配器时：

1. 把 `inputTokens` / `outputTokens` / `totalTokens` / `cacheReadTokens` /
   `cacheWriteTokens` / `reasoningTokens` 里的数字字符串转成非负安全整数；
2. 若 `totalTokens` 原本是字符串（说明是拼接产物），按 pi-ai 的公式复算
   `input + output + cacheRead + cacheWrite`；拿不到 input/output 时删掉这个可选字段；
3. 其余分片逐位、原引用透传。

因为归一化发生在分片进入 agent loop **之前**，所以写进会话日志的也是干净数字 ——
既修复投影失败，也不再产生新坏数据。对本来就返回数字的提供方（DeepSeek 官方等）
完全无副作用（数字 usage 分片原引用透传）。

## 安装与卸载

```bash
# 安装（profile 级别，影响该 profile 的全部会话）
#   通过 plugin_manager 工具的 install_bundle，target 传本目录的绝对路径
# 停用：plugin_manager set_plugin，target 为 llm-usage-normalizer
# 卸载：plugin_manager remove_bundle，target 为 @local/dsh-llm-usage-normalizer
```

## 自测

`index.js` 的 `apply(ctx)` 用一个假 ctx 捕获监听器，再把假分片流喂进去即可验证：

```bash
node --check index.js          # 语法
node /tmp/selftest.mjs         # 8 项行为断言（见仓库历史）
```

## 长期修复

根因在网关侧：`completion_tokens` 应返回 JSON number 而不是字符串。本插件是客户端
侧的防御，网关修好后可以直接卸载。
