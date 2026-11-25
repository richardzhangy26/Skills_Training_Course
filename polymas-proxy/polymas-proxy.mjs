#!/usr/bin/env node
/**
 * polymas-proxy —— 把 llm-service 网关的非标准流式响应改写成 OpenAI 标准。
 *
 * 为什么需要它
 * ------------
 * 网关（Spring）在 SSE 流式分片里把增量内容放在 `choices[].message`，
 * 而 OpenAI 标准是 `choices[].delta`；token 计数还被序列化成 JSON 字符串。
 * 按规范解析的客户端（DSH / pi-ai、Cursor、openai SDK…）因此拿不到任何模型输出，
 * 表现为"完成但无内容"→ EMPTY_RESPONSE。
 *
 * 本服务只做三件事，其余一律原样透传：
 *   1. 流式分片：`choices[].message` → `choices[].delta`（仅在请求 stream=true 时）
 *   2. `usage` 里的字符串数字 → 真数字（流式与非流式都做）
 *   3. 流结束时补上缺失的 `data: [DONE]`
 *
 * 非流式响应的 `choices[].message` 本身就是正确的，绝不改写。
 *
 * 用法
 * ----
 *   node polymas-proxy.mjs
 *   POLYMAS_PROXY_PORT=8787 POLYMAS_PROXY_DEBUG=1 node polymas-proxy.mjs
 *
 * 然后把 DSH 的 provider baseURL 指向 http://127.0.0.1:8787/v1/
 * 健康检查：curl http://127.0.0.1:8787/healthz
 *
 * 零依赖（仅 Node 标准库）。鉴权头原样透传，服务本身不保存任何密钥。
 */

import http from 'node:http'
import { mkdirSync, writeFileSync } from 'node:fs'
import { join } from 'node:path'

const PORT = Number(process.env.POLYMAS_PROXY_PORT || 8787)
const HOSTNAME = process.env.POLYMAS_PROXY_HOST || '127.0.0.1'
/** 上游根：请求 /v1/xxx 会转发到 <UPSTREAM>/v1/xxx */
const UPSTREAM = (process.env.POLYMAS_PROXY_UPSTREAM || 'http://llm-service.polymas.com/api/openai').replace(/\/+$/, '')
const DEBUG = process.env.POLYMAS_PROXY_DEBUG === '1'
/** 调试用：设置后把每个请求体原样落盘到该目录（排查上游 schema 校验问题） */
const DUMP_DIR = process.env.POLYMAS_PROXY_DUMP_DIR || ''

/**
 * 网关把 JSON 整数按 32 位解析：|n| > 2147483647 的值会被序列化成字符串，
 * 导致下游 schema 校验报 "'9007199254740991' is not of type 'number'"。
 * 实测阈值：2147483647 通过，2147483648 就失败。
 */
const MAX_INT = Number(process.env.POLYMAS_PROXY_MAX_INT || 2147483647)
/** 这些关键字的值必须是数字，超界会导致上游校验失败。 */
const NUMERIC_CONSTRAINT_KEYS = new Set([
  'maximum', 'minimum', 'exclusiveMaximum', 'exclusiveMinimum', 'multipleOf',
  'maxLength', 'minLength', 'maxItems', 'minItems',
  'maxProperties', 'minProperties', 'maxContains', 'minContains',
])

/** usage 里可能出现的计数字段（OpenAI 用 *_tokens，Anthropic 风格也一并兼容） */
const COUNT_KEYS = [
  'prompt_tokens', 'completion_tokens', 'total_tokens',
  'input_tokens', 'output_tokens',
  'cache_read_input_tokens', 'cache_creation_input_tokens',
  'reasoning_tokens', 'cached_tokens',
]

/** 逐字节转发的请求头里需要丢弃的（长度会变，且不可复用） */
const DROP_REQ_HEADERS = new Set(['host', 'content-length', 'connection', 'accept-encoding'])
/** 响应头里需要丢弃的（正文已被改写，长度/编码不再成立） */
const DROP_RES_HEADERS = new Set(['content-length', 'content-encoding', 'transfer-encoding', 'connection'])

const log = (...args) => console.log(new Date().toISOString(), ...args)
const debug = (...args) => { if (DEBUG) log(...args) }

/**
 * usage 数值归一：把 "19" 之类的字符串转成 19。
 * @returns 是否发生了改动
 */
function coerceUsage(usage) {
  if (usage === null || typeof usage !== 'object') return false
  let changed = false
  for (const key of COUNT_KEYS) {
    const value = usage[key]
    if (typeof value === 'string' && /^-?\d+(?:\.\d+)?$/.test(value.trim())) {
      const parsed = Number(value.trim())
      if (Number.isFinite(parsed)) {
        usage[key] = Math.max(0, Math.trunc(parsed))
        changed = true
      }
    }
  }
  // 有些上游把明细放在嵌套对象里
  for (const nested of ['prompt_tokens_details', 'completion_tokens_details']) {
    if (coerceUsage(usage[nested])) changed = true
  }
  return changed
}

/**
 * 改写一个 SSE 分片 / 非流式响应对象。
 * @param obj - 已解析的响应对象
 * @param streaming - 请求是否为 stream=true
 * @returns 是否发生了改动
 */
function fixObject(obj, streaming) {
  if (obj === null || typeof obj !== 'object') return false
  let changed = false

  if (coerceUsage(obj.usage)) changed = true

  if (streaming && Array.isArray(obj.choices)) {
    for (const choice of obj.choices) {
      if (choice === null || typeof choice !== 'object') continue
      // 只在缺 delta 时补，绝不覆盖已有的标准字段
      if ('message' in choice && !('delta' in choice)) {
        choice.delta = choice.message
        delete choice.message
        changed = true
      }
    }
  }
  return changed
}

/** 处理一行 SSE：仅 data: 行会被改写 */
function fixSseLine(line, streaming) {
  if (!line.startsWith('data:')) return line
  const payload = line.slice(5).trim()
  if (payload === '' || payload === '[DONE]') return line
  let obj
  try {
    obj = JSON.parse(payload)
  } catch {
    return line // 非 JSON（保活、注释等）原样透传
  }
  return fixObject(obj, streaming) ? 'data: ' + JSON.stringify(obj) : line
}

/**
 * 把上游 SSE 流转成标准 SSE 流。
 * 逐行处理、逐行下发，保持流式（不缓冲整段响应）。
 */
async function* transformSse(readable, streaming) {
  const decoder = new TextDecoder()
  let buffer = ''
  let sawDone = false

  const handleLine = (line) => fixSseLine(line.endsWith('\r') ? line.slice(0, -1) : line, streaming)

  for await (const chunk of readable) {
    buffer += decoder.decode(chunk, { stream: true })
    let index
    while ((index = buffer.indexOf('\n')) >= 0) {
      const line = buffer.slice(0, index)
      buffer = buffer.slice(index + 1)
      const out = handleLine(line)
      if (out.includes('[DONE]')) sawDone = true
      yield out + '\n'
    }
  }
  if (buffer.length > 0) {
    const out = handleLine(buffer)
    if (out.includes('[DONE]')) sawDone = true
    yield out + '\n'
  }
  if (!sawDone) yield 'data: [DONE]\n\n' // 网关不发终止符，客户端需要它
}

/**
 * 净化一个 JSON Schema 子树：把越界的数值约束收拾到网关能无损表示的范围。
 * 只动数值约束关键字，不碰 default / const / enum / examples 这些数据位置。
 * @returns 改写处数
 */
function sanitizeSchema(node, toolName, stats) {
  if (node === null || typeof node !== 'object') return 0
  let changed = 0

  if (Array.isArray(node)) {
    for (const item of node) changed += sanitizeSchema(item, toolName, stats)
    return changed
  }

  for (const [key, value] of Object.entries(node)) {
    if (NUMERIC_CONSTRAINT_KEYS.has(key) && typeof value === 'number' && Number.isInteger(value)
        && Math.abs(value) > MAX_INT) {
      if (Math.abs(value) === Number.MAX_SAFE_INTEGER) {
        // ±MAX_SAFE_INTEGER 语义上就是"无上限/无下限"，删掉最忠实
        delete node[key]
        stats.push(`${toolName}.${key}=±MAX_SAFE_INTEGER→删除`)
      } else {
        node[key] = value > 0 ? MAX_INT : -MAX_INT
        stats.push(`${toolName}.${key}=${value}→${node[key]}`)
      }
      changed += 1
      continue
    }
    changed += sanitizeSchema(value, toolName, stats)
  }
  return changed
}

/**
 * 净化请求体里的工具定义。网关按 32 位整数解析 JSON，超界值会变成字符串，
 * 导致上游报 "JSON schema is invalid"（实测阈值 2147483647）。
 * @returns { body, changed, stats } —— changed 为 false 时调用方应沿用原始 Buffer
 */
function sanitizeTools(body, stats) {
  if (!Array.isArray(body.tools)) return 0
  let changed = 0
  for (const tool of body.tools) {
    if (tool === null || typeof tool !== 'object') continue
    const name = tool.function?.name ?? tool.name ?? '(匿名工具)'
    if (tool.function?.parameters) changed += sanitizeSchema(tool.function.parameters, name, stats)
    if (tool.input_schema) changed += sanitizeSchema(tool.input_schema, name, stats)
  }
  return changed
}

/**
 * 把 `role: "developer"` 归一成 `"system"`。
 * OpenAI 新规范用 developer 取代 system，但不少 OpenAI 兼容上游（如阿里百炼/DashScope）
 * 只认 system，会直接报 `developer is not one of [...]`。两者语义相同，改写无副作用。
 * @returns 改写处数
 */
function normalizeRoles(body) {
  if (!Array.isArray(body.messages)) return 0
  let changed = 0
  for (const message of body.messages) {
    if (message !== null && typeof message === 'object' && message.role === 'developer') {
      message.role = 'system'
      changed += 1
    }
  }
  return changed
}

/** 上游单请求上限约 4.5MB，留出余量 */
const MAX_BODY_BYTES = Number(process.env.POLYMAS_PROXY_MAX_BODY_BYTES || 4300000)

/**
 * 请求体超限时，从最早的图片开始替换成文字占位，直到低于上限（最近的图片优先保留）。
 * 只处理 OpenAI chat 格式的 image_url 块。
 * @returns 替换的图片数
 */
function dropOldImages(body) {
  if (!Array.isArray(body.messages)) return 0
  const refs = []
  for (const message of body.messages) {
    if (!Array.isArray(message?.content)) continue
    message.content.forEach((part, index) => {
      if (part?.type === 'image_url') refs.push({ content: message.content, index })
    })
  }
  let size = Buffer.byteLength(JSON.stringify(body), 'utf8')
  let dropped = 0
  for (const { content, index } of refs) {
    if (size <= MAX_BODY_BYTES) break
    const before = Buffer.byteLength(JSON.stringify(content[index]), 'utf8')
    content[index] = { type: 'text', text: '[图片已省略：请求体超过上游 4.5MB 上限]' }
    size -= before - Buffer.byteLength(JSON.stringify(content[index]), 'utf8')
    dropped += 1
  }
  return dropped
}

/** 读取请求体 */
function readBody(req) {
  return new Promise((resolve, reject) => {
    const parts = []
    req.on('data', (c) => parts.push(c))
    req.on('end', () => resolve(Buffer.concat(parts)))
    req.on('error', reject)
  })
}

const server = http.createServer(async (req, res) => {
  const started = Date.now()

  // 健康检查（不转发上游）
  if (req.url === '/healthz') {
    res.writeHead(200, { 'content-type': 'application/json' })
    res.end(JSON.stringify({ ok: true, upstream: UPSTREAM, port: PORT }))
    return
  }

  const body = await readBody(req)

  // 判断是否流式：只看请求体里的 stream 字段
  let streaming = false
  let model = ''
  let parsedBody
  if (body.length > 0) {
    try {
      parsedBody = JSON.parse(body.toString('utf8'))
      streaming = parsedBody?.stream === true
      model = typeof parsedBody?.model === 'string' ? parsedBody.model : ''
    } catch {
      /* 非 JSON 请求体，按非流式处理 */
    }
  }

  // 调试转储：原样保存请求体，便于比对上游 schema 校验失败的具体字段
  if (DUMP_DIR && body.length > 0) {
    try {
      mkdirSync(DUMP_DIR, { recursive: true })
      const stamp = new Date().toISOString().replace(/[:.]/g, '-')
      writeFileSync(join(DUMP_DIR, `${stamp}-${streaming ? 'stream' : 'json'}.json`), body)
    } catch (error) {
      log(`转储失败: ${error?.message ?? error}`)
    }
  }

  // 净化工具 schema 里越界的数值约束（网关按 32 位整数解析，超界会变字符串）
  // 并把 developer 角色归一成 system（部分上游不认 developer）
  let outgoing = body
  if (parsedBody !== undefined) {
    const stats = []
    const fixed = sanitizeTools(parsedBody, stats)
    const roleFix = normalizeRoles(parsedBody)
    const imgDrop = body.length > MAX_BODY_BYTES ? dropOldImages(parsedBody) : 0
    if (fixed > 0 || roleFix > 0 || imgDrop > 0) {
      outgoing = Buffer.from(JSON.stringify(parsedBody), 'utf8')
      const parts = []
      if (fixed > 0) parts.push(`schema ${fixed} 处（${stats.slice(0, 2).join(', ')}${stats.length > 2 ? ', …' : ''}）`)
      if (roleFix > 0) parts.push(`developer→system ${roleFix} 条`)
      if (imgDrop > 0) parts.push(`丢弃旧图片 ${imgDrop} 张 (${body.length}→${outgoing.length} 字节)`)
      log(`✎ 请求体净化: ${model || req.url} ${parts.join(' + ')}`)
    }
  }

  const headers = {}
  for (const [key, value] of Object.entries(req.headers)) {
    if (DROP_REQ_HEADERS.has(key.toLowerCase())) continue
    headers[key] = value
  }
  headers['accept-encoding'] = 'identity' // 不压缩，便于改写正文

  const target = UPSTREAM + req.url
  let upstream
  try {
    upstream = await fetch(target, { method: req.method, headers, body: outgoing.length > 0 ? outgoing : undefined })
  } catch (error) {
    log(`✗ ${req.method} ${req.url} 上游不可达: ${error?.message ?? error}`)
    res.writeHead(502, { 'content-type': 'application/json' })
    res.end(JSON.stringify({ error: { message: `polymas-proxy: 上游不可达 (${error?.message ?? error})`, type: 'proxy_error' } }))
    return
  }

  const resHeaders = {}
  upstream.headers.forEach((value, key) => {
    if (DROP_RES_HEADERS.has(key.toLowerCase())) return
    resHeaders[key] = value
  })
  const isSse = (upstream.headers.get('content-type') || '').includes('text/event-stream')

  if (isSse) {
    res.writeHead(upstream.status, { ...resHeaders, 'content-type': 'text/event-stream;charset=UTF-8', 'cache-control': 'no-cache', connection: 'keep-alive' })
    if (!upstream.body) { res.end(); return }
    let lines = 0
    try {
      for await (const text of transformSse(upstream.body, streaming)) {
        res.write(text)
        lines += 1
      }
    } catch (error) {
      log(`✗ 流式中断: ${error?.message ?? error}`)
    }
    res.end()
    log(`✓ ${upstream.status} ${model || req.url} stream=${streaming} 行=${lines} ${Date.now() - started}ms`)
    return
  }

  // 非流式：整段读出，改 usage 数值后回写
  const raw = Buffer.from(await upstream.arrayBuffer())
  let out = raw
  try {
    const obj = JSON.parse(raw.toString('utf8'))
    if (fixObject(obj, false)) out = Buffer.from(JSON.stringify(obj), 'utf8')
  } catch {
    /* 非 JSON 原样返回 */
  }
  res.writeHead(upstream.status, { ...resHeaders, 'content-length': out.length })
  res.end(out)
  log(`✓ ${upstream.status} ${model || req.url} ${streaming ? 'stream' : 'json'} ${Date.now() - started}ms`)
})

server.listen(PORT, HOSTNAME, () => {
  log(`polymas-proxy 已启动: http://${HOSTNAME}:${PORT}/v1/  ->  ${UPSTREAM}`)
  log(`DSH provider baseURL 用: http://${HOSTNAME}:${PORT}/v1/`)
})

for (const signal of ['SIGINT', 'SIGTERM']) {
  process.on(signal, () => {
    log(`收到 ${signal}，关闭`)
    server.close(() => process.exit(0))
  })
}
