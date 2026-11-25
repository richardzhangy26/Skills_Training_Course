#!/usr/bin/env node
/**
 * polymas-proxy 离线自测
 *
 * 起一个「假上游」复刻 llm-service 网关的全部已知毛病，再把反代指向它，
 * 逐项断言反代是否把响应/请求改写正确。**不需要真网关、不需要 API key**。
 *
 *   node selftest.mjs
 *
 * 退出码 0 = 全部通过。
 */

import http from 'node:http'
import net from 'node:net'
import { spawn } from 'node:child_process'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'

const HERE = dirname(fileURLToPath(import.meta.url))
const PROXY = join(HERE, 'polymas-proxy.mjs')

const results = []
const check = (label, ok, detail = '') => {
  results.push({ label, ok, detail })
  console.log(`${ok ? '✓' : '✗'} ${label}${ok || !detail ? '' : `\n    ${detail}`}`)
}

const freePort = () => new Promise((resolve) => {
  const probe = net.createServer()
  probe.listen(0, '127.0.0.1', () => {
    const { port } = probe.address()
    probe.close(() => resolve(port))
  })
})

/** 假上游：模仿网关的毛病，并记录收到的请求体 */
function startFakeGateway() {
  let lastRequest = null
  const server = http.createServer((req, res) => {
    const chunks = []
    req.on('data', (c) => chunks.push(c))
    req.on('end', () => {
      const body = Buffer.concat(chunks)
      let parsed
      try { parsed = JSON.parse(body.toString('utf8')) } catch { parsed = null }
      lastRequest = { url: req.url, body: parsed, raw: body.toString('utf8'), headers: req.headers }

      if (parsed?.stream === true) {
        // 毛病 1：内容放在 message 而不是 delta
        // 毛病 2：usage 是字符串
        // 毛病 3：不发 data: [DONE]
        res.writeHead(200, { 'content-type': 'text/event-stream;charset=UTF-8' })
        res.write('data:{"id":"chatcmpl-fake","choices":[{"index":0,"message":{"role":"assistant","content":"PONG"}}]}\n\n')
        res.write('data:{"id":"chatcmpl-fake","choices":[{"index":0,"message":{"content":""},"finish_reason":"stop"}],"usage":{"prompt_tokens":"7","completion_tokens":"3","total_tokens":"10"}}\n\n')
        res.end()
        return
      }
      // 非流式：message 本来就对，但 usage 仍是字符串
      res.writeHead(200, { 'content-type': 'application/json' })
      res.end(JSON.stringify({
        id: 'chatcmpl-fake',
        choices: [{ index: 0, message: { role: 'assistant', content: 'PONG' }, finish_reason: 'stop' }],
        usage: { prompt_tokens: '7', completion_tokens: '3', total_tokens: '10' },
      }))
    })
  })
  return new Promise((resolve) => server.listen(0, '127.0.0.1', () => resolve({ server, port: server.address().port, last: () => lastRequest })))
}

const waitHealthy = async (port, timeoutMs = 8000) => {
  const deadline = Date.now() + timeoutMs
  while (Date.now() < deadline) {
    try {
      const res = await fetch(`http://127.0.0.1:${port}/healthz`)
      if (res.ok) return true
    } catch { /* 还没起来 */ }
    await new Promise((r) => setTimeout(r, 150))
  }
  return false
}

const post = async (port, payload) => {
  const res = await fetch(`http://127.0.0.1:${port}/v1/chat/completions`, {
    method: 'POST',
    headers: { 'content-type': 'application/json', authorization: 'Bearer test-key' },
    body: JSON.stringify(payload),
  })
  return { status: res.status, text: await res.text(), contentType: res.headers.get('content-type') || '' }
}

const MAX_INT = 2147483647

async function main() {
  const gateway = await startFakeGateway()
  const proxyPort = await freePort()
  const proxy = spawn(process.execPath, [PROXY], {
    env: { ...process.env, POLYMAS_PROXY_PORT: String(proxyPort), POLYMAS_PROXY_UPSTREAM: `http://127.0.0.1:${gateway.port}` },
    stdio: ['ignore', 'pipe', 'pipe'],
  })
  let proxyLog = ''
  proxy.stdout.on('data', (d) => { proxyLog += d })
  proxy.stderr.on('data', (d) => { proxyLog += d })

  const cleanup = () => { try { proxy.kill('SIGTERM') } catch {} ; try { gateway.server.close() } catch {} }
  try {
    if (!await waitHealthy(proxyPort)) throw new Error(`反代未在 8s 内就绪\n${proxyLog}`)
    console.log(`反代: 127.0.0.1:${proxyPort}  →  假上游: 127.0.0.1:${gateway.port}\n`)

    // ---------- 响应侧 ----------
    console.log('【响应侧】')
    const sse = await post(proxyPort, { model: 'claude-opus-5', stream: true, messages: [{ role: 'user', content: 'hi' }] })
    const dataLines = sse.text.split('\n').filter((l) => l.startsWith('data:'))
    const chunks = dataLines.map((l) => l.slice(5).trim()).filter((p) => p && p !== '[DONE]').map((p) => JSON.parse(p))
    check('流式分片用 delta 而不是 message',
      chunks.every((c) => (c.choices || []).every((ch) => !('message' in ch))) && chunks.some((c) => (c.choices || []).some((ch) => ch.delta)),
      JSON.stringify(chunks[0] || {}))
    check('流结束补上 data: [DONE]', sse.text.includes('[DONE]'))

    const usageChunk = chunks.find((c) => c.usage)
    const usage = usageChunk?.usage || {}
    check('usage 计数转成 number',
      ['prompt_tokens', 'completion_tokens', 'total_tokens'].every((k) => typeof usage[k] === 'number'),
      JSON.stringify(usage))

    const json = await post(proxyPort, { model: 'claude-opus-5', stream: false, messages: [{ role: 'user', content: 'hi' }] })
    const jsonBody = JSON.parse(json.text)
    check('非流式仍保留 message（不被误改）', !!jsonBody.choices?.[0]?.message && !jsonBody.choices?.[0]?.delta)
    check('非流式 usage 也转成 number', typeof jsonBody.usage?.prompt_tokens === 'number')

    // ---------- 请求侧 ----------
    console.log('\n【请求侧】')
    await post(proxyPort, {
      model: 'claude-opus-5',
      stream: false,
      messages: [
        { role: 'developer', content: 'system-ish' },
        { role: 'user', content: 'hi' },
      ],
      tools: [{
        type: 'function',
        function: {
          name: 'f',
          description: 'd',
          parameters: {
            type: 'object',
            properties: {
              n: { type: 'integer', minimum: -9007199254740991, maximum: 9007199254740991 },
              big: { type: 'integer', maximum: 5000000000 },
              ok: { type: 'integer', maximum: 100 },
            },
          },
        },
      }],
    })
    const received = gateway.last()
    const tool = received?.body?.tools?.[0]?.function?.parameters
    check('role: developer 归一成 system',
      received?.body?.messages?.[0]?.role === 'system',
      JSON.stringify(received?.body?.messages?.[0]))
    check('±MAX_SAFE_INTEGER 的数值约束被删除',
      tool?.properties?.n && !('maximum' in tool.properties.n) && !('minimum' in tool.properties.n),
      JSON.stringify(tool?.properties?.n))
    check(`其他越界整数被钳到 ±${MAX_INT}`,
      tool?.properties?.big?.maximum === MAX_INT,
      JSON.stringify(tool?.properties?.big))
    check('范围内的数值不动', tool?.properties?.ok?.maximum === 100, JSON.stringify(tool?.properties?.ok))
    check('请求体其余部分未被影响（工具名/参数结构完整）',
      received?.body?.tools?.[0]?.function?.name === 'f' && tool?.properties?.ok?.type === 'integer')

    // ---------- 透传 ----------
    console.log('\n【透传】')
    check('鉴权头原样转发给上游',
      received?.headers?.authorization === 'Bearer test-key',
      `上游收到 authorization=${received?.headers?.authorization}`)
    check('请求改为不压缩（便于改写正文）',
      received?.headers?.['accept-encoding'] === 'identity',
      `上游收到 accept-encoding=${received?.headers?.['accept-encoding']}`)
    const health = await fetch(`http://127.0.0.1:${proxyPort}/healthz`).then((r) => r.json())
    check('/healthz 可用且不转发上游', health.ok === true && health.upstream === `http://127.0.0.1:${gateway.port}`)
  } catch (error) {
    check('自测执行', false, String(error?.message ?? error))
  } finally {
    cleanup()
  }

  const failed = results.filter((r) => !r.ok)
  console.log(`\n${'='.repeat(60)}`)
  console.log(failed.length === 0
    ? `全部通过 ✅  (${results.length} 项)`
    : `${failed.length}/${results.length} 项失败 ❌`)
  console.log('='.repeat(60))
  process.exit(failed.length === 0 ? 0 : 1)
}

main()
