#!/usr/bin/env bash
#
# 卸载 polymas-proxy：停服务、删注册、可选删安装目录。
#
#   ./uninstall.sh                          # 停服务 + 删注册（保留安装目录与日志）
#   ./uninstall.sh --purge                  # 连安装目录一起删
#   ./uninstall.sh --port 8791 --label com.polymas.proxy.test --dir /tmp/xxx
#
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LABEL="${POLYMAS_PROXY_LABEL:-com.polymas.proxy}"
INSTALL_DIR="${POLYMAS_PROXY_DIR:-$HOME/.polymas-proxy}"
PORT="${POLYMAS_PROXY_PORT:-8787}"
PURGE=0

if [[ -f "$HERE/config.env" ]]; then
  # shellcheck disable=SC1091
  set -a; . "$HERE/config.env"; set +a
  LABEL="${POLYMAS_PROXY_LABEL:-$LABEL}"
  INSTALL_DIR="${POLYMAS_PROXY_DIR:-$INSTALL_DIR}"
  PORT="${POLYMAS_PROXY_PORT:-$PORT}"
fi

while [[ $# -gt 0 ]]; do
  case "$1" in
    --purge) PURGE=1; shift ;;
    --label) LABEL="$2"; shift 2 ;;
    --dir)   INSTALL_DIR="$2"; shift 2 ;;
    --port)  PORT="$2"; shift 2 ;;
    *) echo "未知参数: $1" >&2; exit 2 ;;
  esac
done

printf '\033[1m卸载 polymas-proxy\033[0m\n'
echo "  label=$LABEL  dir=$INSTALL_DIR  port=$PORT"

if [[ "$(uname -s)" == "Darwin" ]]; then
  PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
  launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
  rm -f "$PLIST"
  echo "  ✓ 已停止并移除 launchd 服务（$LABEL）"
elif command -v systemctl >/dev/null 2>&1; then
  systemctl --user disable --now "$LABEL.service" 2>/dev/null || true
  rm -f "$HOME/.config/systemd/user/$LABEL.service"
  systemctl --user daemon-reload 2>/dev/null || true
  echo "  ✓ 已停止并移除 systemd 用户服务（$LABEL）"
fi

# 兜底：只在「本实例配置的端口」上、且进程命令行确实指向本安装目录时，才结束它。
# 绝不做全局 pkill —— 同一台机器上可能有别人/别的端口实例，误杀会连带停掉。
if command -v lsof >/dev/null 2>&1; then
  for pid in $(lsof -nP -iTCP:"$PORT" -sTCP:LISTEN -t 2>/dev/null || true); do
    cmd="$(ps -o command= -p "$pid" 2>/dev/null || true)"
    case "$cmd" in
      *"$INSTALL_DIR"*)
        kill "$pid" 2>/dev/null && echo "  ✓ 已结束残留进程 $pid（端口 $PORT）" || true ;;
      *)
        echo "  ! 端口 $PORT 仍被其他进程占用（pid $pid），本脚本不动它：${cmd:0:70}" ;;
    esac
  done
fi

if [[ "$PURGE" == "1" ]]; then
  rm -rf "$INSTALL_DIR"
  echo "  ✓ 已删除安装目录 $INSTALL_DIR"
else
  echo "  · 安装目录保留：$INSTALL_DIR（要一并删除加 --purge）"
fi

cat <<'EOF'

注意：客户端里指向反代的 baseURL 需要自行改回，否则会连不上：
  · CC Switch  →  把该 provider 的上游格式改回 Anthropic，或删掉该 provider
  · pi         →  rm ~/.pi/agent/models.json 里对应 provider，或改 baseUrl
  · DSH        →  cordis.patch.yml 里 polymas.baseURL 改回网关直连
EOF
