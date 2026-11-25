#!/usr/bin/env bash
#
# 把 polymas 网关接进 pi agent（~/.pi/agent/models.json + settings.json）
#
#   ./pi-setup.sh --key sk-xxxx
#   ./pi-setup.sh --key sk-xxxx --base-url http://127.0.0.1:8788/v1 --default claude-opus-5
#   ./pi-setup.sh --key sk-xxxx --dry-run
#
# 要点：
#   · baseUrl 必须指向 polymas-proxy，不能直连网关
#     —— 网关的流式分片用 message 而非 delta，pi(pi-ai) 会读不到内容而报空响应。
#   · maxTokens 一定要设小（默认 32000）。pi 会把请求的 max_tokens 钳成
#     min(maxTokens, contextWindow − 提示词占用)；若填成 1e7 之类的值，
#     实际会发出接近 contextWindow 的天量 max_tokens，被上游以 400/500 拒绝。
#   · contextWindow 默认 262144（256K）。网关真实上限未经确认，别盲目填 1M。
#
set -euo pipefail

KEY=""
BASE_URL="${POLYMAS_PROXY_URL:-http://127.0.0.1:8787/v1}"
PROVIDER="${POLYMAS_PROVIDER_NAME:-polymas}"
CONTEXT_WINDOW="${POLYMAS_CONTEXT_WINDOW:-262144}"
MAX_TOKENS="${POLYMAS_MAX_TOKENS:-32000}"
MODELS="claude-opus-5,claude-sonnet-5,claude-opus-4-8,gpt-5.6-sol"
DEFAULT_MODEL=""
PI_DIR="${PI_CONFIG_DIR:-$HOME/.pi/agent}"
DRY_RUN=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --key)            KEY="$2"; shift 2 ;;
    --base-url)       BASE_URL="$2"; shift 2 ;;
    --provider)       PROVIDER="$2"; shift 2 ;;
    --models)         MODELS="$2"; shift 2 ;;
    --default)        DEFAULT_MODEL="$2"; shift 2 ;;
    --context-window) CONTEXT_WINDOW="$2"; shift 2 ;;
    --max-tokens)     MAX_TOKENS="$2"; shift 2 ;;
    --pi-dir)         PI_DIR="$2"; shift 2 ;;
    --dry-run)        DRY_RUN=1; shift ;;
    -h|--help)        sed -n '2,15p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "未知参数: $1（--help 看用法）" >&2; exit 2 ;;
  esac
done

[[ -n "$KEY" ]] || { echo "--key 必填（网关的 LLM_API_KEY）" >&2; exit 2; }
command -v node >/dev/null 2>&1 || { echo "需要 node（用于安全合并 JSON）" >&2; exit 1; }
[[ -d "$PI_DIR" ]] || { echo "找不到 pi 配置目录 $PI_DIR —— 先跑一次 pi 让它初始化" >&2; exit 1; }

echo "将写入："
echo "  provider      : $PROVIDER"
echo "  baseUrl       : $BASE_URL"
echo "  contextWindow : $CONTEXT_WINDOW"
echo "  maxTokens     : $MAX_TOKENS"
echo "  models        : $MODELS"
[[ -n "$DEFAULT_MODEL" ]] && echo "  设为默认      : $PROVIDER / $DEFAULT_MODEL"
[[ "$DRY_RUN" == "1" ]] && { echo; echo "（--dry-run，未写入）"; exit 0; }

KEY="$KEY" BASE_URL="$BASE_URL" PROVIDER="$PROVIDER" CONTEXT_WINDOW="$CONTEXT_WINDOW" \
MAX_TOKENS="$MAX_TOKENS" MODELS="$MODELS" DEFAULT_MODEL="$DEFAULT_MODEL" PI_DIR="$PI_DIR" \
node <<'EOF'
const fs = require('node:fs')
const path = require('node:path')
const dir = process.env.PI_DIR
const modelsPath = path.join(dir, 'models.json')
const settingsPath = path.join(dir, 'settings.json')
const provider = process.env.PROVIDER
const ids = process.env.MODELS.split(',').map((s) => s.trim()).filter(Boolean)

const stamp = new Date().toISOString().replace(/[:.]/g, '-')
const readJson = (p, fallback) => { try { return JSON.parse(fs.readFileSync(p, 'utf8')) } catch { return fallback } }
const backup = (p) => { if (fs.existsSync(p)) fs.copyFileSync(p, `${p}.bak-${stamp}`) }

// ---- models.json ----
const models = readJson(modelsPath, { providers: {} })
models.providers ??= {}
models.providers[provider] = {
  baseUrl: process.env.BASE_URL,
  api: 'openai-completions',
  apiKey: process.env.KEY,
  models: ids.map((id) => ({
    id,
    name: id,
    reasoning: id !== 'gpt-5.6-sol', // gpt-5.6-sol 的上游不允许「工具 + reasoning_effort」共存
    input: ['text'],
    contextWindow: Number(process.env.CONTEXT_WINDOW),
    maxTokens: Number(process.env.MAX_TOKENS),
  })),
}
backup(modelsPath)
fs.writeFileSync(modelsPath, JSON.stringify(models, null, 2) + '\n')
console.log(`  ✓ 已写入 ${modelsPath}（providers: ${Object.keys(models.providers).join(', ')}）`)

// ---- settings.json（可选设默认） ----
if (process.env.DEFAULT_MODEL) {
  const settings = readJson(settingsPath, {})
  settings.defaultProvider = provider
  settings.defaultModel = process.env.DEFAULT_MODEL
  backup(settingsPath)
  fs.writeFileSync(settingsPath, JSON.stringify(settings, null, 2) + '\n')
  console.log(`  ✓ 已写入 ${settingsPath}（默认 ${provider} / ${process.env.DEFAULT_MODEL}）`)
}
EOF

echo
echo "验证："
echo "  pi -p --provider $PROVIDER --model ${DEFAULT_MODEL:-claude-opus-5} 'reply with exactly: PONG'"
echo "  pi -p 'reply with exactly: PONG'        # 若设了默认，可省略参数"
