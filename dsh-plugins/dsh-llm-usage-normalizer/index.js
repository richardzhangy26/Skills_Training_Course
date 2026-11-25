/**
 * llm-usage-normalizer —— 把 LLM 网关返回的字符串型 token 计数归一化成整数。
 *
 * 为什么需要它
 * ------------
 * 公司的 llm-service 网关（Spring Boot / Jackson）把 usage 里的 token 数序列化成了
 * JSON 字符串：
 *
 *     {"usage":{"prompt_tokens":"16","completion_tokens":"13","total_tokens":"18"}}
 *
 * pi-ai 只对减法做了隐式数值转换，加法没有：
 *
 *     input  = Math.max(0, promptTokens - cacheRead - cacheWrite)   // 减法 -> 数字 ✓
 *     output = completion_tokens || 0                               // 原样透传 -> 字符串 ✗
 *     total  = input + output + cacheRead + cacheWrite              // 加法 -> "2666"+"13"+"0"+"0"
 *
 * 于是 totalTokens 变成拼接出来的垃圾值 "26661300"；harness 的 token-meter 投影在
 * 累加 outputTokens 时又是加法（`totals - previous + next`），字符串一路滚雪球，
 * 最终投影状态违反 `z.number().int().nonnegative()`，抛：
 *
 *     failed to project session "…": invalid_type expected number received string
 *     path ["outputTokens"]
 *
 * 结果是该会话的历史再也打不开。
 *
 * 怎么修
 * ------
 * `llm/stream` 是 DSH 提供给中间件的 waterfall 扩展点（触发点是
 * `this.ctx.waterfall(this, 'llm/stream', options, () => adapterStream(...))`）。
 * 本插件在最外层包住分片流，在 usage 分片离开适配器的那一刻把数字字符串转回整数，
 * 并按 pi-ai 的公式把被拼接坏的 totalTokens 重新算出来。
 *
 * 归一化发生在分片进入 agent loop 之前，所以**写进会话日志的也是干净的数字**，
 * 既修好了已有的投影失败，也不会再产生新的坏数据。
 *
 * 只改动"看起来是数字的字符串"；任何本来就是数字、或格式无法识别的值都原样保留，
 * 因此对正常提供方（DeepSeek 官方等）完全无副作用。
 */

/** harness `TokenUsage` 里的计数字段；只有这些会被归一化。 */
const COUNT_KEYS = [
  'inputTokens',
  'outputTokens',
  'totalTokens',
  'cacheReadTokens',
  'cacheWriteTokens',
  'reasoningTokens',
]

/** 十进制数字文本（网关给的是整数字符串，小数也容忍）。 */
const NUMERIC_TEXT = /^-?\d+(?:\.\d+)?$/

/**
 * 把一个计数字段折算成合法的非负安全整数。
 * @param value - usage 里的原始值。
 * @returns 折算后的整数；无法折算时返回 `undefined`（表示"不要动它"）。
 */
function toCount(value) {
  if (typeof value === 'number') {
    if (Number.isInteger(value) && Number.isSafeInteger(value) && value >= 0) return value
    if (!Number.isFinite(value)) return undefined
    const truncated = Math.max(0, Math.trunc(value))
    return Number.isSafeInteger(truncated) ? truncated : 0
  }
  if (typeof value !== 'string') return undefined
  const text = value.trim()
  if (!NUMERIC_TEXT.test(text)) return undefined
  const parsed = Number(text)
  if (!Number.isFinite(parsed)) return undefined
  const count = Math.max(0, Math.trunc(parsed))
  return Number.isSafeInteger(count) ? count : 0
}

/**
 * 归一化一个 usage 对象。
 * @param usage - 适配器产出的 usage。
 * @returns 归一化后的对象；无需改动时返回原对象（保持引用不变）。
 */
function normalizeUsage(usage) {
  let changed = false
  let totalWasText = false
  const normalized = { ...usage }

  for (const key of COUNT_KEYS) {
    if (!Object.prototype.hasOwnProperty.call(normalized, key)) continue
    const current = normalized[key]
    const count = toCount(current)
    if (count === undefined || count === current) continue
    if (key === 'totalTokens') totalWasText = true
    normalized[key] = count
    changed = true
  }

  // 网关的 totalTokens 是字符串拼接的产物，转成数字也仍是垃圾值，必须复算。
  if (totalWasText) {
    const input = toCount(normalized.inputTokens)
    const output = toCount(normalized.outputTokens)
    if (input !== undefined && output !== undefined) {
      const cacheRead = toCount(normalized.cacheReadTokens) ?? 0
      const cacheWrite = toCount(normalized.cacheWriteTokens) ?? 0
      const total = input + output + cacheRead + cacheWrite
      if (normalized.totalTokens !== total) {
        normalized.totalTokens = total
        changed = true
      }
    } else {
      // 拿不到 input/output 就无法复算；totalTokens 在 TokenUsage 里是可选的，
      // 宁可省略一个坏值，也不要留下会让投影校验失败的数字。
      delete normalized.totalTokens
      changed = true
    }
  }

  return changed ? normalized : usage
}

/**
 * 逐分片透传，只在 usage 分片处归一化。
 * @param stream - 下游适配器的分片流。
 * @returns 归一化后的分片流。
 */
async function* normalizeStream(stream) {
  for await (const chunk of stream) {
    if (chunk === null || typeof chunk !== 'object' || chunk.type !== 'usage' || chunk.usage == null) {
      yield chunk
      continue
    }
    const usage = normalizeUsage(chunk.usage)
    yield usage === chunk.usage ? chunk : { ...chunk, usage }
  }
}

/**
 * 挂上 `llm/stream` waterfall。
 *
 * `prepend` 让本包装在其它监听器之外，后续消费者看到的一定是干净的数字；
 * `global` 使它不受上下文过滤器影响——这是纯粹的格式修复，与作用域无关。
 * @param ctx - 插件上下文，监听器随插件卸载一起销毁。
 */
export function apply(ctx) {
  ctx.on(
    'llm/stream',
    (_options, next) => normalizeStream(next()),
    { global: true, prepend: true },
  )
}
