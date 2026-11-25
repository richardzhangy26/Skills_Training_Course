#!/usr/bin/env bash
#
# polymas-proxy 一键安装
#
#   ./install.sh                        # 用默认值安装并启动
#   ./install.sh --port 8788            # 换端口
#   ./install.sh --upstream http://other-gateway/api/openai
#   ./install.sh --no-service           # 只落地文件，不注册常驻服务
#
# 安装脚本**不需要 API key** —— 反代只做格式改写，鉴权头由客户端原样透传。
# 配置也可写在 config.env（见 config.env.example），命令行参数优先。
#
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ---------- 默认值（可被 config.env / 命令行覆盖） ----------
PORT="${POLYMAS_PROXY_PORT:-8787}"
HOST="${POLYMAS_PROXY_HOST:-127.0.0.1}"
UPSTREAM="${POLYMAS_PROXY_UPSTREAM:-http://llm-service.polymas.com/api/openai}"
INSTALL_DIR="${POLYMAS_PROXY_DIR:-$HOME/.polymas-proxy}"
LABEL="${POLYMAS_PROXY_LABEL:-com.polymas.proxy}"
LOG="${POLYMAS_PROXY_LOG:-$HOME/Library/Logs/polymas-proxy.log}"
NO_SERVICE=0

# ---------- 读 config.env（如果存在） ----------
if [[ -f "$HERE/config.env" ]]; then
  # shellcheck disable=SC1091
  set -a; . "$HERE/config.env"; set +a
  PORT="${POLYMAS_PROXY_PORT:-$PORT}"
  HOST="${POLYMAS_PROXY_HOST:-$HOST}"
  UPSTREAM="${POLYMAS_PROXY_UPSTREAM:-$UPSTREAM}"
  INSTALL_DIR="${POLYMAS_PROXY_DIR:-$INSTALL_DIR}"
  LABEL="${POLYMAS_PROXY_LABEL:-$LABEL}"
  LOG="${POLYMAS_PROXY_LOG:-$LOG}"
fi

# ---------- 命令行参数 ----------
while [[ $# -gt 0 ]]; do
  case "$1" in
    --port)      PORT="$2"; shift 2 ;;
    --host)      HOST="$2"; shift 2 ;;
    --upstream)  UPSTREAM="$2"; shift 2 ;;
    --dir)       INSTALL_DIR="$2"; shift 2 ;;
    --label)     LABEL="$2"; shift 2 ;;
    --log)       LOG="$2"; shift 2 ;;
    --no-service) NO_SERVICE=1; shift ;;
    -h|--help)   sed -n '2,14p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "未知参数: $1（用 --help 看用法）" >&2; exit 2 ;;
  esac
done

say()  { printf '\033[1m%s\033[0m\n' "$*"; }
ok()   { printf '  \033[32m✓\033[0m %s\n' "$*"; }
warn() { printf '  \033[33m!\033[0m %s\n' "$*"; }
die()  { printf '\033[31m✗ %s\033[0m\n' "$*" >&2; exit 1; }

# ---------- 前置检查 ----------
say "① 检查环境"
command -v node >/dev/null 2>&1 || die "没找到 node。装一个 Node ≥ 18（反代零依赖，只要有 node）。"
NODE_BIN="$(command -v node)"
NODE_MAJOR="$(node -p 'process.versions.node.split(".")[0]')"
NODE_VERSION="$(node -v)"
[[ "$NODE_MAJOR" -ge 18 ]] || die "Node 版本太低（$NODE_VERSION），反代用了内建 fetch，需要 ≥ 18。"
ok "node $NODE_VERSION  ($NODE_BIN)"
ok "安装目录 $INSTALL_DIR"
ok "上游 $UPSTREAM"
ok "监听 $HOST:$PORT"

# ---------- 落地文件 ----------
say "② 安装反代"
mkdir -p "$INSTALL_DIR"
cp "$HERE/proxy/polymas-proxy.mjs" "$INSTALL_DIR/polymas-proxy.mjs"
ok "已写入 $INSTALL_DIR/polymas-proxy.mjs"

# 端口占用检查（本服务自己占着则视为可覆盖）
if command -v lsof >/dev/null 2>&1; then
  if lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
    warn "端口 $PORT 已被占用（可能是旧实例）；会先停掉同名服务再启动"
  fi
fi

if [[ "$NO_SERVICE" == "1" ]]; then
  say "③ 跳过常驻服务注册（--no-service）"
  echo "  手动启动：POLYMAS_PROXY_PORT=$PORT POLYMAS_PROXY_UPSTREAM=$UPSTREAM node $INSTALL_DIR/polymas-proxy.mjs"
else
  say "③ 注册常驻服务"
  if [[ "$(uname -s)" == "Darwin" ]]; then
    mkdir -p "$(dirname "$LOG")" "$HOME/Library/LaunchAgents"
    PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
    sed -e "s|__LABEL__|$LABEL|g" \
        -e "s|__NODE__|$NODE_BIN|g" \
        -e "s|__SCRIPT__|$INSTALL_DIR/polymas-proxy.mjs|g" \
        -e "s|__PORT__|$PORT|g" \
        -e "s|__HOST__|$HOST|g" \
        -e "s|__UPSTREAM__|$UPSTREAM|g" \
        -e "s|__LOG__|$LOG|g" \
        "$HERE/launchd/com.polymas.proxy.plist.template" > "$PLIST"
    ok "已生成 $PLIST"
    launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
    sleep 1
    for attempt in 1 2 3; do
      if launchctl bootstrap "gui/$(id -u)" "$PLIST" 2>/dev/null; then break; fi
      warn "bootstrap 第 $attempt 次失败（多为 bootout 竞态），重试…"
      sleep 2
    done
    launchctl list | grep -q "$LABEL" || die "服务未注册成功。看 $LOG.err 或手动跑一次 node $INSTALL_DIR/polymas-proxy.mjs"
    ok "服务已注册：$LABEL"
  elif command -v systemctl >/dev/null 2>&1; then
    UNIT="$HOME/.config/systemd/user/$LABEL.service"
    mkdir -p "$(dirname "$UNIT")" "$(dirname "$LOG")"
    cat > "$UNIT" <<EOF
[Unit]
Description=polymas-proxy (llm-service 网关格式适配层)
After=network.target

[Service]
ExecStart=$NODE_BIN $INSTALL_DIR/polymas-proxy.mjs
Environment=POLYMAS_PROXY_PORT=$PORT
Environment=POLYMAS_PROXY_HOST=$HOST
Environment=POLYMAS_PROXY_UPSTREAM=$UPSTREAM
Restart=always
RestartSec=2
StandardOutput=append:$LOG
StandardError=append:$LOG.err

[Install]
WantedBy=default.target
EOF
    systemctl --user daemon-reload
    systemctl --user enable --now "$LABEL.service"
    ok "systemd 用户服务已启用：$LABEL"
  else
    warn "既不是 macOS 也没有 systemctl；请自行常驻。手动启动："
    echo "    POLYMAS_PROXY_PORT=$PORT POLYMAS_PROXY_UPSTREAM=$UPSTREAM node $INSTALL_DIR/polymas-proxy.mjs"
  fi
fi

# ---------- 健康检查 ----------
say "④ 健康检查"
HEALTH=""
for _ in $(seq 1 20); do
  HEALTH="$(curl -fsS -m 2 "http://$HOST:$PORT/healthz" 2>/dev/null || true)"
  [[ -n "$HEALTH" ]] && break
  sleep 0.5
done
if [[ -n "$HEALTH" ]]; then
  ok "存活：$HEALTH"
else
  die "健康检查失败。看日志：tail -50 ${LOG}.err ；或前台跑一次 node $INSTALL_DIR/polymas-proxy.mjs"
fi

# ---------- 离线自测（不碰真网关） ----------
say "⑤ 离线自测（假上游，验证 5 项改写）"
if node "$HERE/proxy/selftest.mjs" >/dev/null 2>&1; then
  ok "13 项断言通过"
else
  warn "自测未全通过：node $HERE/proxy/selftest.mjs 看详情"
fi

# ---------- 下一步 ----------
cat <<EOF

$(say "安装完成")
反代地址（客户端用它当 baseURL）：  http://$HOST:$PORT/v1

接下来把客户端指过来，任选：
  · Claude Code（经 CC Switch）  →  见 clients/cc-switch.md
  · pi agent                     →  ./clients/pi-setup.sh --key <你的 LLM_API_KEY>
  · DeepSeek Harness (DSH)       →  见 clients/dsh.md

先验证网关本身有没有问题（可选但推荐）：
  LLM_API_KEY=<你的 key> python3 docs/gateway-check.py
  退出码 0 = 网关已修好，反代可以卸掉；非 0 = 反代仍然必要（问题见 docs/gateway-report.md）

查看日志 / 卸载：
  tail -f ${LOG}
  ./uninstall.sh
EOF
