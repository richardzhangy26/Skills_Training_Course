#!/bin/sh
set -eu
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if ! command -v python3 >/dev/null 2>&1; then
  printf '%s\n' '{"ok":false,"error":"未找到 Python 3.9+，请先安装 Python 3"}' >&2
  exit 127
fi
if ! python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 9) else 1)'; then
  printf '%s\n' '{"ok":false,"error":"Python 版本过低，需要 Python 3.9+"}' >&2
  exit 127
fi
exec python3 "$SCRIPT_DIR/app_publish.py" "$@"
