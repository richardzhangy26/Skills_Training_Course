#!/bin/bash
# Claude Code 开发工具合集
# 用法: source .claude/tools/dev-tools.sh

PROJECT_ROOT="/Users/zhangyichi/工作/能力训练"

# ============================================================================
# 训练剧本纯净跳转验证工具 (vts)
# ============================================================================

alias vts='python "$PROJECT_ROOT/.claude/tools/validate_script_purity.py"'
alias vts-all='python "$PROJECT_ROOT/.claude/tools/validate_script_purity.py" --batch ./skills_training_course'
alias vts-git='python "$PROJECT_ROOT/.claude/tools/validate_script_purity.py" --check-git'

# ============================================================================
# 智能体课程平台自动登录工具 (auto-login)
# ============================================================================

AUTO_LOGIN_SCRIPT="$PROJECT_ROOT/.claude/skills/training-auto-login/scripts/auto_login.py"

# 主命令
auto-login() {
    if [ $# -eq 0 ]; then
        echo "用法: auto-login <训练剧本配置.md路径> [选项]"
        echo "       auto-login --province <省区名>"
        echo "       auto-login --account <账号> --password <密码>"
        echo ""
        echo "选项:"
        echo "  --course-name <名称>   手动指定课程名称"
        echo "  --keep-open            登录完成后保持浏览器开启"
        echo "  --force-relogin        强制重新登录（忽略历史会话）"
        echo "  --headless             无头模式（不显示浏览器窗口）"
        echo ""
        echo "示例:"
        echo "  auto-login @/path/to/训练剧本配置.md"
        echo "  auto-login @/path/to/训练剧本配置.md --keep-open"
        echo "  auto-login --province \"北京省区\""
        return 0
    fi

    python "$AUTO_LOGIN_SCRIPT" "$@"
}

# 快捷命令：登录并保持浏览器开启
auto-login-open() {
    if [ $# -eq 0 ]; then
        echo "用法: auto-login-open <训练剧本配置.md路径>"
        return 1
    fi
    auto-login "$@" --keep-open
}

# 快捷命令：使用特定省区登录
auto-login-province() {
    if [ $# -eq 0 ]; then
        echo "用法: auto-login-province <省区名>"
        echo ""
        echo "可用省区:"
        echo "  北京省区、福建省区、天津省区、河北省区、"
        echo "  河南省区、山东省区、贵州省区、云南省区、"
        echo "  湖南省区、湖北省区、陕西省区、..."
        return 1
    fi
    auto-login --province "$1"
}

# 快捷命令：强制重新登录
auto-login-fresh() {
    if [ $# -eq 0 ]; then
        echo "用法: auto-login-fresh <训练剧本配置.md路径>"
        return 1
    fi
    auto-login "$@" --force-relogin --keep-open
}

# 显示帮助信息
auto-login-help() {
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║           智能体课程平台自动登录 CLI 工具                     ║"
    echo "╠══════════════════════════════════════════════════════════════╣"
    echo "║                                                              ║"
    echo "║  主命令:                                                     ║"
    echo "║    auto-login <配置文件.md> [选项]                          ║"
    echo "║                                                              ║"
    echo "║  快捷命令:                                                   ║"
    echo "║    auto-login-open <配置文件.md>      # 保持浏览器开启       ║"
    echo "║    auto-login-province <省区名>       # 指定省区登录         ║"
    echo "║    auto-login-fresh <配置文件.md>     # 强制重新登录         ║"
    echo "║    auto-login-help                    # 显示帮助             ║"
    echo "║                                                              ║"
    echo "║  选项:                                                       ║"
    echo "║    --keep-open          登录后保持浏览器开启                 ║"
    echo "║    --force-relogin      强制重新登录                         ║"
    echo "║    --course-name <名>   手动指定课程名                       ║"
    echo "║    --headless           无头模式                             ║"
    echo "║                                                              ║"
    echo "║  示例:                                                       ║"
    echo "║    auto-login @/path/to/训练剧本配置.md                      ║"
    echo "║    auto-login-open @/path/to/训练剧本配置.md                 ║"
    echo "║    auto-login-province \"北京省区\"                           ║"
    echo "║                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
}

# ============================================================================
# 帮助信息
# ============================================================================

dev-tools-help() {
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║              Claude Code 开发工具合集                        ║"
    echo "╠══════════════════════════════════════════════════════════════╣"
    echo "║                                                              ║"
    echo "║  剧本验证工具 (vts):                                         ║"
    echo "║    vts <文件>              # 验证单个剧本文件                ║"
    echo "║    vts-all                 # 验证所有训练剧本                ║"
    echo "║    vts-git                 # 验证 git 暂存区的文件           ║"
    echo "║                                                              ║"
    echo "║  自动登录工具 (auto-login):                                  ║"
    echo "║    auto-login <文件.md>    # 自动登录并进入课程              ║"
    echo "║    auto-login-open <文件>  # 登录并保持浏览器开启            ║"
    echo "║    auto-login-province <p> # 指定省区登录                    ║"
    echo "║    auto-login-fresh <文件> # 强制重新登录                    ║"
    echo "║    auto-login-help         # 显示登录工具详细帮助            ║"
    echo "║                                                              ║"
    echo "║  其他:                                                       ║"
    echo "║    dev-tools-help          # 显示此帮助信息                  ║"
    echo "║                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
}

# ============================================================================
# 初始化提示
# ============================================================================

echo "✅ Claude Code 开发工具已加载"
echo ""
echo "可用命令:"
echo "  vts, vts-all, vts-git           # 剧本验证工具"
echo "  auto-login, auto-login-open     # 自动登录工具"
echo "  auto-login-province, auto-login-fresh"
echo "  dev-tools-help                  # 显示帮助"
echo ""
