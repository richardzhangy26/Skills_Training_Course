# PROJECT KNOWLEDGE BASE

**Generated:** 2026-03-04

## OVERVIEW

AI教育平台自动化测试系统（能力训练工作流测试）。模拟学生-AI对话，测试对话式教学任务质量。

---

## WHERE TO LOOK

| 任务 | 入口文件 | 说明 |
|------|----------|------|
| 平台登录 / 账号 | `.claude/skills/training-auto-login/scripts/auto_login.py` | 账号表 `智能体课程配置账号情况.xlsx` 取账号，自动过滑块、缓存登录态 |
| 读平台 Cookie | 本文件「Chrome Cookie」 | 用户给 Chrome profile 名，用 `browser_cookie3` 解密 SQLite |
| 运行工作流测试 | `auto_script_train.py` | 3档学生：good/medium/bad |
| 并发压力测试 | `auto_script_train_5characters.py` | 5角色并行 |
| 语音训练测试 | `auto_audio_train.py` | WebSocket+TTS实时 |
| 从Markdown构建任务 | `skill_training_build/create_task_from_markdown.py` | 自动生成节点+流程 |
| 导入能力训练 Pro | `skill_training_pro/deploy_pro_from_markdown.py` | Pro任务、成员、技能、卡片、评分项 |
| 作业批改 | `homework_review/homework_reviewer_v2.py` | 上传→解析→评分 |
| 对话质量评测 | `python -m evaluation` | 5维度规则+LLM混合评测 |
| 查看API基类 | `workflow_tester_base.py` | 所有脚本继承自此 |

---

## CONVENTIONS

### 环境配置
- **脚本环境**: 按需使用 `.env`文件（从`.env.example`复制）；服务凭证优先按下节读取 `secrets.json`
- **认证**: 用户只给 Chrome profile 名时，按下方「Chrome Cookie」自己解密读取；`.env` 的 `AUTHORIZATION`/`COOKIE` 只作过期兜底
- **LLM后端**: `MODEL_TYPE`选择 `doubao_sdk`/`doubao_post`/`deepseek_sdk`

### 能力训练模型与数字人（统一规则）

- **模型**：普通能力训练、能力训练 Pro、英文口语的阶段和成员模型统一使用 `doubao-seed-2.0-pro`，模板必须显式填写。旧文档、环境默认值或脚本兜底不作为模型选择依据；平台若使用不同显示名称或模型 ID，先从当前模型接口核实对应关系，不得静默换用其他模型。图片、TTS、视频等专用服务仍按各自配置选择模型。
- **默认新建数字人**：先通过当前账号的平台形象、声音接口选择匹配角色的 `avatarNid`、`voiceNid` 及对应声音参数，再组合创建本任务的新数字人，保存并回读新返回的 `customNid` / `customDigitalHuman`。已有数字人同名或组合相同，也不直接复用其 ID。
- **形象自定义门槛**：只有用户明确说“新建一个数字人形象”或明确要求自定义形象时，才生成、上传或注册自定义人物图片；“创建数字人”默认仅指组合平台已有形象和声音，不授权自定义形象或克隆声音。没有合适的平台资源时记录缺口，不自动转为自定义。
- **同一角色与断点续跑**：同一任务内同一角色跨阶段沿用本次新建的数字人；重试先从本任务创建记录恢复 ID，避免重复创建。其他任务或历史资源不作为默认复用对象。
- **生成与执行边界**：剧本生成阶段只读选资源，普通剧本的 `数字人` 字段留空、Pro 的 `数字人组合ID` 写 `运行时解析`；实际创建放在已获授权的导入阶段。导入前检查脚本是否会自动复用历史数字人；若会，先调整调用流程或实现，不能将自动复用的结果当作新建完成。导入后回读全部业务阶段/成员的模型、数字人 ID、形象和声音绑定。

### 共享服务凭证（secrets.json）

调用图片生成、OSS、TTS、数字人、视频或文本模型时，Agent 可直接在本机读取 `/Users/zhangyichi/工作/能力训练/secrets.json`（本仓库根目录），按 `providers` 下的对应服务获取接口、模型和凭证，无需再向用户索取已有 Key。

| 能力 | JSON 路径 |
|------|-----------|
| 生图 | `providers.image`：主配置 `url`、`api_key`、`model`、`size` 为 Polymas 网关（`gpt-image-2` 等）；备用 `fallback_url`、`fallback_api_key`、`fallback_model` 为火山方舟 Seedream 5.0 Pro |
| OSS | `providers.oss`：访问密钥、endpoint、bucket、prefix、public_base_url |
| TTS | `providers.tts`：`url`、`api_key`、`model`、`voice` |
| 数字人 | `providers.digital_human`：接口、模型、签名密钥及默认人像/音频策略 |
| 视频 | `providers.video`；合成为 `providers.video_compose` |
| 文本模型 / PPT 元素解析 | `providers.llm` / `providers.pptx_element` |

以文件当前内容为准，接口、模型与 Key 必须使用同一服务配置；只读取当前任务需要的字段。凭证仅在运行时使用，文档和日志只记录路径、字段名及非敏感配置，不复制 Key、不输出整个文件，`secrets.json` 不入库。该文件用于服务调用，不替代下方的平台登录 Cookie。

能力训练背景图统一使用 `.claude/skills/training-background-generator/scripts/generate_background.py`，默认优先采用 `providers.image` 的 Polymas 主配置；主服务失败时自动改用同组 `fallback_*` 的 Seedream 5.0 Pro，并在生成记录中写明每张图的实际模型与主服务错误。明确指定备用模型时直接走备用端点和 Key。

### 平台登录与账号来源（账号表优先）

登录智慧树 / Polymas 教学中心时，账号来源统一走根目录的 `智能体课程配置账号情况.xlsx`（147 条有效账号）。

- **默认行为**：用户没有指定 Chrome profile、也没有直接给账号密码时，一律用账号表里的账号登录，不反问、不让用户手动登录。
- **账号表结构**：多段式表格。主段列为 `对应省份 | 教工号 | 学校/机构 | 机构(Polymas实验室) | 默认密码 | 手机号 | 备注`；表尾另有 `演示账号`、`学生账号`、`再造课堂`、`评审账号` 几个小段，列序不同，解析时按"教工号形态 + 密码以 Zhihuishu@ 开头"识别。
- **账号优先级**：`--account/--password`（用户显式指定） > `--school` > `--province`（省区行） > 训练剧本路径推断学校。**账号表是唯一来源**，原来的 `data/school_province_map.json` 已废弃删除；表里查不到的学校会自动降级到该省区的省区账号。
- **课程关键词**：目录名 `学校-课程名` 时，首段以 `大学/学院/学校` 结尾即视为学校，其余为课程关键词（如 `天津财经大学-理解当代中国英语演讲`），用于平台课程检索。
- **学校名匹配**：全角/半角括号、空格、`中国石油大学（北京）` vs `中国石油大学(北京)` 视为同一学校；先精确、再归一化精确、再包含匹配，最后去掉"大学/学院/学校"后缀再试。
- **登录态复用**：每个账号的登录态缓存在 `.claude/skills/training-auto-login/sessions/accounts/<账号>.json`，未过期（默认 72h）直接复用，不弹登录、不过滑块；缺失或过期才新开网页用账号密码登录。滑块由 `scripts/yidun_slider.py` 自动破解。
- **凭证位置**：`能力训练/.env`（AUTHORIZATION / COOKIE / COURSE_ID，仅最后一次登录的账号）；`.claude/skills/training-auto-login/sessions/accounts/<教工号>.json`（按账号隔离的 Playwright storage_state）。两者都已 gitignore。
- **跨 Agent 复用**：不启动浏览器也能拿凭证 —— `python3 auto_login.py --export-headers <教工号>`（JSON 头）或 `--export-env <教工号>`（shell 变量）；需要浏览器时直接 `new_context(storage_state=".../<教工号>.json")`，进去就是已登录状态。
- **推荐入口**：`python3 .claude/skills/training-auto-login/scripts/auto_login.py --school "学校名"`，成功后 `.env` 的 `AUTHORIZATION`/`COOKIE` 自动回填，再执行部署/配置类技能。

```bash
cd .claude/skills/training-auto-login/scripts
python3 auto_login.py --list-accounts 北京          # 查账号表：省份/学校/教工号/密码
python3 auto_login.py --school "中国石油大学（北京）"  # 登录并缓存登录态
python3 auto_login.py --list-sessions              # 看已有登录态及有效期
```

### Chrome Cookie

登录态从本机已登录的 Chrome 现场读取。用户只需给出 profile 名（`Default` / `0` / `1` / `2`）。

1. 配置目录：`~/Library/Application Support/Google/Chrome/`
   - `Default` 或 `0` → `Default/Cookies`
   - `1` → `Profile 1/Cookies`
   - `2` → `Profile 2/Cookies`
2. 真源是该路径下的 SQLite 文件 `Cookies`（macOS 加密，走钥匙串）。Cookie 不在明文 txt 里。
3. 用 `browser_cookie3` 解密读取：

```python
# python3 -m pip install browser_cookie3
import browser_cookie3
cj = browser_cookie3.chrome(
    cookie_file="/Users/zhangyichi/Library/Application Support/Google/Chrome/Profile 1/Cookies"
)
```

4. 按目标站点筛 `cookie.domain`（去掉前导 `.` 后 `endswith` 目标域名）。
5. 拼 `Cookie` header 再调 API。该 profile 须已在 Chrome 里登录目标站点。

完成标准：筛出的 cookie 能打通目标 API（不再 401）。仓库 `.env` 里的 `AUTHORIZATION`/`COOKIE` 已对 `cloudapi.polymas.com` 返回 401，不当真源。

Polymas（`polymas.com`，登录 cookie 名 `ai-poly`）的账号对照与 `--chrome-profile`：`homework_review/AGENTS.md`。

### 学生画像
- **3档**: good(优秀) / medium(需引导) / bad(跑题)
- **5档**: S1(沉默) / S2(配合) / S3(完美主义) / S4(捣乱) / S5(创新)
- 自定义: `student_profiles.custom.json`覆盖默认值

### 日志规范
```
log/[context]/[profile]/
├── task_[ID]_[ts]_runcard.txt    # API请求响应
├── task_[ID]_[ts]_dialogue.txt   # 对话记录（人可读）
└── task_[ID]_[ts]_dialogue.json  # JSON导出（用于回放）
```

### API调用顺序（强制）
```python
query_script_step_list(task_id)  # 1. 获取步骤列表
run_card(task_id, step_id)       # 2. 初始化步骤
chat(user_answer)                # 3. 循环对话
# 若返回 needSkipStep=true → 自动调用run_card进入下一步
```

---

## ANTI-PATTERNS

| 禁止 | 正确做法 |
|------|----------|
| 硬编码`TASK_ID` | 使用`.env`环境变量 |
| 向用户要 DevTools 粘贴的 JWT，或复用仓库 `.env` 里的 `AUTHORIZATION`/`COOKIE` | 用户给 Chrome profile 名后，按「Chrome Cookie」用 `browser_cookie3` 现场解密 |
| 使用英文TTS(`en-US-GuyNeural`)播报中文 | 改用`zh-CN-XiaoxiaoNeural` |
| LLM评测输出非JSON内容 | 强制JSON-only，禁止额外文本 |
| 评测时直接复制示例值 | 示例仅供格式参考，必须独立评判 |
| 省略`run_card`直接`chat` | 必须按顺序初始化 |
| 对话超过50字（AI学生） | 限制回答在50字内，确认/选择题直接答"是"/"1" |
| 主观判断状态转换 | 必须用封闭式确认问题（"明白了吗？"→"是"） |

---

## COMMANDS

```bash
# 对话评测
python -m evaluation -t doc.docx -d log.json -v
python -m evaluation -t doc.docx -D ./logs/ -O ./reports/ --workers 3
```

---

## NOTES

1. **半交互模式快捷键**: Enter=AI生成, `continue`=全自动, `continue N`=自动到N轮后暂停
2. **回放模式**: 编辑`dialogue.txt/json`后重新运行，自动匹配相似问题复用答案
3. **并发测试**: 5角色脚本输入`1,3,5`可同时跑S1/S3/S5
4. **Skills工作流**: 引用文档`@路径/任务.md` → 自动生成基础配置/评价标准/剧本/对话流程
5. **评测维度**: 目标达成度/流程遵循度(规则) + 交互体验性/幻觉与边界/教学策略(LLM)

---

## CHILD AGENTS.md

- [skill_training_build/AGENTS.md](./skill_training_build/AGENTS.md) - Markdown→平台构建
- [skill_training_pro/AGENTS.md](./skill_training_pro/AGENTS.md) - 能力训练 Pro 导入与回查
- [homework_review/AGENTS.md](./homework_review/AGENTS.md) - 作业批改
- [agent_microcourse/AGENTS.md](./agent_microcourse/AGENTS.md) - 智能体微课（旁白微课视频生产，独立 repo `agent-microcourse`）
- [polymas_v5/AGENTS.md](./polymas_v5/AGENTS.md) - 专家智能体搭建（独立 repo）
- [skills_training_course/AGENTS.md](./skills_training_course/AGENTS.md) - 能力训练课程资料与交付物
- [HTML/AGENTS.md](./HTML/AGENTS.md) - 互动网页与视觉小说类项目
- [evaluation/AGENTS.md](./evaluation/AGENTS.md) - 对话质量评测
- [.claude/skills/AGENTS.md](./.claude/skills/AGENTS.md) - Claude Code技能系统
- [docs/agents/workspace-map.md](./docs/agents/workspace-map.md) - 各项目 skill / agent / AGENTS.md 总览（`python3 scripts/workspace_inventory.py` 生成清单）

`polymas_v5` 已独立为 https://github.com/richardzhangy26/polymas_v5 ，本仓库不再跟踪该目录。

---

## Agent skills

### Issue tracker

Issue 跟踪在 GitHub（origin 仓库 `richardzhangy26/Skills_Training_Course`）。详见 `docs/agents/issue-tracker.md`。

### Triage labels

使用默认的五个 triage 标签（needs-triage / needs-info / ready-for-agent / ready-for-human / wontfix）。详见 `docs/agents/triage-labels.md`。

### Domain docs

单上下文布局：根目录 `CONTEXT.md` + `docs/adr/`。详见 `docs/agents/domain.md`。

### 企业微信任务与资料归档

用户要求整理私聊分派、记录待办或归档课程附件时，先读 [企业微信任务记录与资料归档](docs/agents/wecom-task-intake.md)。新归档目录与待办标题按 `学校名-课程名` 命名，学校在前、课程在后：能力训练进入 `skills_training_course/`，专家智能体资料进入 `polymas_v5/`，作业批阅进入 `homework_review/`。原件、DDL 依据和 SHA-256 写入任务台账；优先复用已有学校-课程目录，已有制作项目保留原路径。企业微信待办与截止字段须保存后分别回读确认。
