# CLAUDE SKILLS

**Generated:** 2026-03-04

## OVERVIEW

Claude Code自动化技能系统。根据实训任务文档自动生成训练配置、评价标准、封面图、背景图。

---

## STRUCTURE

```
.claude/skills/
├── training-config-setup/          # 基础配置+封面图生成
├── training-rubric-generator/      # 评价标准生成
├── training-script-generator/      # 训练剧本配置
├── training-dialogue-simulator/    # 对话流程模拟
├── training-background-generator/  # 阶段背景图生成
├── training-auto-login/            # 账号表登录+过滑块+登录态缓存
├── training-deploy-and-test/       # 部署+自动测试
├── homework-answer-generator/      # 作业答案生成
└── doubao_skill_runner.py          # Doubao API调用基类
```

---

## WHERE TO LOOK

| 任务 | Skill | 触发词 | 输出 |
|------|-------|--------|------|
| 生成基础配置 | `training-config-setup` | "基础配置"、"封面图" | 基础配置.json + 封面图 |
| 生成评价标准 | `training-rubric-generator` | "评价标准"、"评分标准" | 评价标准.json/.md |
| 生成训练剧本 | `training-script-generator` | "训练剧本"、"实训配置" | 训练剧本配置.md |
| 模拟对话流程 | `training-dialogue-simulator` | "对话流程"、"模拟对话" | 对话流程模拟.md |
| 生成背景图 | `training-background-generator` | "背景图"、"阶段图片" | backgrounds/*.png |
| 平台登录 | `training-auto-login` | "登录"、"账号过期" | AUTHORIZATION/COOKIE/COURSE_ID |
| 一键部署测试 | `training-deploy-and-test` | "部署测试"、"导入平台" | 平台任务+测试报告 |

---

## CONVENTIONS

### 能力训练统一配置
生成、修改或导入普通能力训练、Pro、英文口语配置前，读取根目录 `AGENTS.md`「能力训练模型与数字人（统一规则）」：模型统一为 `doubao-seed-2.0-pro`；默认组合当前平台形象、声音创建本任务新数字人；只有用户明确要求“新建一个数字人形象”或自定义形象时才自定义人物图片。生成阶段只选资源，实际创建在已授权的导入阶段进行。

### 平台登录与账号（部署类技能前置）

任何需要登录 Polymas / 智慧树教学中心的技能（`training-deploy-and-test`、`training-config-setup` 等）在执行前按此顺序处理账号：

1. 用户显式给了账号密码 → 直接用
2. 用户给了 Chrome profile → 按根目录 `AGENTS.md`「Chrome Cookie」读取
3. 都没有 → 用 `.claude/skills/training-auto-login`，账号取自根目录 `智能体课程配置账号情况.xlsx`（`--school "学校名"` 自动匹配，支持全角/半角括号差异）

不要反问用户账号，也不要求用户手动登录。凭证：`.env` 的 `AUTHORIZATION`/`COOKIE`（最近一次登录）与 `training-auto-login/sessions/accounts/<教工号>.json`（按账号）；其他 agent 用 `auto_login.py --export-headers <教工号>` 离线取头，或 `new_context(storage_state=...)` 复用浏览器登录态。登录态缓存在 `training-auto-login/sessions/accounts/<账号>.json`，72 小时内直接复用；滑块（网易易盾拼图）由 `scripts/yidun_slider.py` 自动破解。

```bash
cd .claude/skills/training-auto-login/scripts
python3 auto_login.py --list-accounts 天津        # 查账号表
python3 auto_login.py --school "天津大学"          # 登录并回填 .env
```

### Skill调用方式
```
@路径/实训任务文档.md [指令]
```

### 一键全量生成
```
@化工原理/实训任务.md 生成基础配置、评价标准、训练剧本和对话流程
```
自动执行顺序：
1. config-setup → 基础配置+封面图
2. rubric-generator → 评价标准
3. script-generator → 训练剧本
4. dialogue-simulator → 对话流程
5. background-generator → 阶段背景图（如要求）

### 输出目录结构
```
课程文件夹/
├── 实训任务文档.md
└── 任务名称/                      # 自动生成
    ├── 基础配置.json
    ├── 封面图提示词.txt
    ├── 封面图.png
    ├── 评价标准.json
    ├── 评价标准.md
    ├── 训练剧本配置.md
    ├── 对话流程模拟.md
    └── backgrounds/
        ├── stage_1_xxx.png
        └── generation_record.json
```

### LangGPT框架
所有提示词使用标准LangGPT结构：
- Role / Profile / Rules / Workflow / Constraints / Context / Examples

---

## ANTI-PATTERNS

| 禁止 | 正确做法 |
|------|----------|
| 手动复制到平台 | 使用training-deploy-and-test自动导入 |
| 跳过对话示例 | 文档中包含对话示例可生成更精确的剧本 |
| 覆盖已调优配置 | 手动修改后标记`# 手动调优`避免被覆盖 |

---

## COMMANDS

```bash
# Skills通过Claude Code @引用自动调用
# 无需直接运行，但调试时可执行：

cd .claude/skills/training-config-setup
python config_generator.py

cd .claude/skills/training-rubric-generator
# 阅读SKILL.md了解详细配置
```

---

## NOTES

1. **环境变量**: `.claude/skills/.env`配置`ARK_API_KEY`
2. **封面图**: 16:9比例(2560×1440)，Doubao Seedream生成
3. **背景图**: 通过 `training-background-generator` 读取根目录 `secrets.json` 的 `providers.image` 主配置；模型与尺寸以该文件为准
4. **版本管理**: 各Skill有独立CHANGELOG.md
5. **详细文档**: 每个Skill目录下有SKILL.md完整技术文档
