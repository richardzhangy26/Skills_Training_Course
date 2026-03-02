# 环境配置快速切换指南

## 使用方法

### 1. 创建地区配置文件

为每个地区创建独立的配置文件：

```bash
# 方式一：使用工具创建模板
python switch_env.py
# 选择 'n' 创建新配置，输入地区名如: beijing

# 方式二：手动复制
cp .env.example .env.beijing
cp .env.example .env.shanghai
cp .env.example .env.guangzhou
```

### 2. 编辑地区配置

编辑每个 `.env.{地区}` 文件，填入对应地区的配置：

**示例：.env.beijing**
```ini
# REGION: beijing
AUTHORIZATION=eyJ0eXAiOiJKV1Q...  # 北京环境的 token
COOKIE=hike-polymas-identity=1;... # 北京环境的 cookie
TASK_ID=beijing_task_id_123

ARK_API_KEY=ak-beijing-xxx
DOUBAO_MODEL=doubao-seed-1-6-251015
```

**示例：.env.shanghai**
```ini
# REGION: shanghai
AUTHORIZATION=eyJ0eXAiOiJKV1Q...  # 上海环境的 token
COOKIE=hike-polymas-identity=1;... # 上海环境的 cookie
TASK_ID=shanghai_task_id_456

ARK_API_KEY=ak-shanghai-xxx
DOUBAO_MODEL=doubao-seed-1-6-251015
```

### 3. 快速切换环境

```bash
python switch_env.py
```

交互式界面会显示：
```
============================================================
🌍 环境配置切换工具
============================================================

当前环境: beijing

可用环境:
  1. beijing ← 当前
  2. shanghai
  3. guangzhou

操作选项:
  [数字] - 切换到对应环境
  [n/new] - 创建新地区配置
  [q/quit] - 退出

请选择: 
```

输入数字切换环境，例如输入 `2` 切换到上海环境。

### 4. 验证切换结果

```bash
head -n 1 .env
# 输出: # CURRENT: shanghai
```

或直接查看环境变量：
```bash
grep TASK_ID .env
```

## 文件结构

```
能力训练/
├── .env                    # 当前使用的环境（动态切换）
├── .env.backup            # 切换前的备份
├── .env.example           # 配置模板
├── .env.beijing           # 北京地区配置
├── .env.shanghai          # 上海地区配置
├── .env.guangzhou         # 广州地区配置
├── switch_env.py          # 切换工具
└── ENV_SWITCH_GUIDE.md   # 本文档
```

## 注意事项

1. **不要提交地区配置到 Git**：确保 `.gitignore` 已包含 `.env.*`
2. **备份机制**：每次切换会自动备份当前 `.env` 到 `.env.backup`
3. **配置隔离**：每个地区配置完全独立，互不影响
4. **命名规范**：地区名建议使用小写英文，如 `beijing`、`shanghai`

## 快捷命令（可选）

可以在 `~/.bashrc` 或 `~/.zshrc` 中添加别名：

```bash
# 添加到 shell 配置文件
alias envswitch='python /Users/zhangyichi/工作/能力训练/switch_env.py'

# 使用时直接输入
envswitch
```

## 高级用法：命令行参数（可扩展）

如需实现非交互式切换，可以修改 `switch_env.py` 支持命令行参数：

```bash
# 直接切换到指定环境
python switch_env.py beijing

# 查看当前环境
python switch_env.py --current
```

需求确认后我可以帮你实现这个功能。
