#!/bin/bash
# PostToolUse Hook: 当写入/修改训练剧本配置.md 时，自动运行 vts 纯净跳转验证

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | python3 -c "
import json, sys
d = json.load(sys.stdin)
print(d.get('tool_input', {}).get('file_path', ''))
" 2>/dev/null)

if [[ "$FILE_PATH" == *"训练剧本配置.md" ]]; then
    PROJECT_ROOT="/Users/zhangyichi/工作/能力训练"
    python3 "$PROJECT_ROOT/.claude/tools/validate_script_purity.py" "$FILE_PATH"
fi
