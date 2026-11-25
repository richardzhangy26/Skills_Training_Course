#!/usr/bin/env bash
# 体检 polymas 网关：逐个探活 pi 里已配置的 polymas 模型，标出「无可用渠道」的型号。
# 用法:  ./check-models.sh                                    探活 models.json 里 polymas 的全部模型
#        ./check-models.sh claude-opus-5-5 gpt-6-astra ...    只探指定型号
set -uo pipefail

AGENT_DIR="${PI_AGENT_DIR:-$HOME/.pi/agent}"
PROXY="${POLYMAS_PROXY:-http://127.0.0.1:8787/v1}"
[ -f "$AGENT_DIR/models.json" ] || { echo "找不到 $AGENT_DIR/models.json"; exit 1; }

PKEY=$(python3 -c "import json;print(json.load(open('$AGENT_DIR/models.json'))['providers']['polymas']['apiKey'])" 2>/dev/null)
[ -n "${PKEY:-}" ] || { echo "models.json 里没有 polymas.apiKey"; exit 1; }

probe() {
  local model="$1" body resp reason
  body=$(printf '{"model":"%s","messages":[{"role":"user","content":"hi"}],"max_tokens":4,"stream":false}' "$model")
  resp=$(curl -s -m 45 -X POST "$PROXY/chat/completions" \
    -H "Authorization: Bearer $PKEY" -H 'Content-Type: application/json' -d "$body")
  if printf '%s' "$resp" | grep -q '"usage"'; then
    printf '  \033[32mOK  \033[0m %s\n' "$model"
  elif printf '%s' "$resp" | grep -q 'No available channel'; then
    reason=$(printf '%s' "$resp" | grep -o 'No available channel[^\\"]*' | head -1)
    printf '  \033[31mDEAD\033[0m %s  <- %s\n' "$model" "$reason"
  else
    printf '  \033[33mERR \033[0m %s  <- %s\n' "$model" "$(printf '%s' "$resp" | head -c 160)"
  fi
}

if [ "$#" -gt 0 ]; then
  echo "网关: $PROXY  |  指定型号: $#"
  for m in "$@"; do probe "$m"; done
else
  echo "网关: $PROXY  |  来源: $AGENT_DIR/models.json (polymas)"
  python3 -c "
import json
d=json.load(open('$AGENT_DIR/models.json'))
for m in d['providers']['polymas']['models']: print(m['id'])
" | while IFS= read -r m; do
    [ -n "$m" ] && probe "$m"
  done
fi
