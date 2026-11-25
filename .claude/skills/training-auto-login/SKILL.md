---
name: training-auto-login
description: "智能体课程平台自动登录并自动进入课程。根据训练剧本文件路径识别学校和课程，查找省区账号，完成登录、课程检索、进入课程，并回填 AUTHORIZATION/COOKIE/COURSE_ID。关键词: 自动登录、课程检索、COURSE_ID、Polymas、智慧树"
allowed-tools: Read, Bash, Write
---

# 智能体课程平台自动登录

根据训练剧本配置文件路径自动识别学校和课程，查询对应省区账号密码，使用 Playwright 自动完成登录流程，进入目标课程，并更新项目根目录 `.env` 文件中的 `AUTHORIZATION`、`COOKIE`、`COURSE_ID`。

## 使用时机

- 需要登录智能体课程平台进行训练任务配置时
- 已有训练剧本配置文件，需要自动获取对应省区账号时
- 希望上传 Markdown 后自动进入对应课程时
- 需要快速切换不同省区账号时
- 手动登录繁琐或频繁需要重新登录时

## 使用方式

### 方式1: 通过文件路径自动识别并进入课程（推荐）

```bash
/auto-login @/Users/zhangyichi/工作/能力训练/skills_training_course/武夷学院-茶艺学实践/实训任务6/训练剧本配置.md
```

脚本会自动：
- 从路径识别学校，例如 `武夷学院`
- 从课程目录识别课程关键词，例如 `茶艺学实践`
- 自动生成多个课程搜索候选词，例如 `茶艺学 武夷学院`
- 登录后进入最匹配的课程，并写回 `COURSE_ID`

### 方式2: 文件路径 + 手动指定课程名

适用于目录名和平台课程名差异较大时：

```bash
/auto-login @/Users/zhangyichi/工作/能力训练/skills_training_course/武夷学院-茶艺学实践/实训任务6/训练剧本配置.md --course-name "茶艺学 武夷学院"
```

### 方式3: 直接指定省区

```bash
/auto-login --province "福建省区"
```

### 方式4: 直接指定账号密码

```bash
/auto-login --account JFFJ1001000000 --password Zhihuishu@000000
```

### 方式5: 强制退出旧会话并重新登录

适用于你明确想丢弃当前 cookie、重新选择省区或重新走登录流程时：

```bash
/auto-login @/Users/zhangyichi/工作/能力训练/skills_training_course/武夷学院-茶艺学实践/实训任务6/训练剧本配置.md --force-relogin
```

### 方式6: 保持浏览器开启（不自动关闭）

适用于你想手动控制浏览器关闭时机，脚本执行完成后浏览器保持打开：

```bash
/auto-login @/Users/zhangyichi/工作/能力训练/skills_training_course/武夷学院-茶艺学实践/实训任务6/训练剧本配置.md --keep-open
```

**说明**：
- 使用 `--keep-open` 后，脚本执行完成后**不会自动关闭浏览器**
- 终端会提示"按 Enter 键结束脚本"，但浏览器窗口保持打开
- 需**手动关闭浏览器窗口**才能彻底结束进程
- 适合需要继续人工操作浏览器或调试的场景

## Instructions

### 第一步：解析登录参数

根据用户输入确定登录账号和课程目标：

1. **如果提供文件路径**：提取 `skills_training_course` 下一级目录，识别学校名称、课程目录、课程关键词
2. **如果指定 `--province`**：直接使用该省区查询账号
3. **如果指定 `--account` 和 `--password`**：直接使用提供的凭据
4. **如果指定 `--course-name`**：优先使用该课程名做课程检索
5. **如果指定 `--force-relogin`**：忽略历史会话，直接重新登录
6. **如果指定 `--keep-open`**：脚本执行完成后保持浏览器开启，不自动关闭

### 第二步：查询账号信息

从根目录账号表 `智能体课程配置账号情况.xlsx` 中查询（本地 JSON 映射已废弃）：
- 学校 -> 省区映射
- 省区 -> 账号密码映射

当前路径解析兼容两类课程目录命名：
- `学校-课程`
- `课程-学校`

### 第三步：执行自动登录

运行 Playwright 脚本完成以下流程：

1. 启动浏览器前检查历史会话：
   - 如果历史会话省区和目标省区一致，优先复用
   - 如果不一致，自动清理旧会话并重新登录
   - 如果显式传入 `--force-relogin`，无条件清理旧会话
2. 启动浏览器，优先使用系统 Chrome
3. 访问平台首页：`https://hike-teaching-center.polymas.com/tch-hike/agent-course-hike/ai-course-center`
4. 等待课程中心状态稳定，判断是已登录还是需跳转智慧树登录页
5. 选择机构：**Polymas实验室**
6. 输入教工号和密码
7. 勾选"我已阅读并同意用户协议"
8. 点击"立即登录"
9. 检测易盾滑块验证码（自动破解）：
   - 内置 `scripts/yidun_slider.py`，自动定位缺口 + 生成拟人轨迹拖动，默认最多 4 次
   - 通过 `api/v3/check` 返回的 `result` 判定，不依赖 DOM 猜测
   - 自动破解 4 次仍失败时，才转人工：用户在弹出的浏览器窗口中手动完成滑块
   - 脚本会在等待窗口内继续检测是否已登录
10. 登录成功后提取凭证
11. 进入课程中心并根据候选课程名检索目标课程
12. 点击匹配课程卡片
13. 从新页面 URL 提取 `COURSE_ID`
14. 更新 `.env` 文件
15. 根据 `--keep-open` 参数决定行为：
    - **默认（无 `--keep-open`）**：终端提示"按 Enter 键关闭浏览器"，等待用户确认后关闭浏览器
    - **有 `--keep-open`**：终端提示"按 Enter 键结束脚本"，但浏览器保持开启，需手动关闭浏览器窗口

### 第四步：更新环境变量

登录成功后，自动提取并更新以下环境变量到项目根目录 `.env` 文件：

```bash
AUTHORIZATION=eyJ0eXAiOiJKV1Q...  # 优先从 localStorage/sessionStorage 提取，必要时从 cookie 提取
COOKIE=hike-polymas-identity=1;...  # 浏览器 cookies
COURSE_ID=BJDw9WvWNguMrq5gYdRO      # 进入课程后的 URL 中提取
```

### 第五步：保存会话状态

保存以下文件到 `sessions/` 目录：
- `storage_state.json`: Playwright storage state（包含 cookies 和 localStorage）

这样下次运行时会优先复用已登录会话，减少重复登录成本。

## 学校→省区映射

当前支持的映射关系示例：

| 学校 | 省区 |
|------|------|
| 武夷学院、厦门大学 | 福建省区 |
| 天津科技大学、天津中德 | 天津省区 |
| 贵州大学 | 贵州省区 |
| 临沂大学 | 山东省区 |
| 华北理工 | 河北省区 |
| 湖南中医药大学 | 湖南省区 |
| 云南农业大学 | 云南省区 |
| 佳木斯大学 | 黑龙江省区 |
| 河北师范大学 | 河北省区 |

**注意**：如果学校不在映射表中，会提示用户手动选择省区或直接输入账号密码。

## 账号与映射数据源

数据文件：
- `/Users/zhangyichi/工作/能力训练/智能体课程配置账号情况.xlsx`（唯一账号来源）

内容包含两部分：
- `mappings`: 学校 -> 省区
- `province_accounts`: 省区 -> 账号密码

## 示例

### 示例1：通过文件路径自动登录并进入课程

```bash
/auto-login @/Users/zhangyichi/工作/能力训练/skills_training_course/天津中德-工程图学智能体实训任务-典型零件图识读（传动轴）/训练剧本配置.md
```

**执行流程**：
1. 从路径提取学校名称："天津中德"
2. 匹配省区："天津省区"
3. 从课程目录提取课程关键词："工程图学"
4. 查询账号：`JFTJ1001000000 / Zhihuishu@000000`
5. 启动浏览器并自动填充登录
6. 如遇滑块，由用户在浏览器中协助完成
7. 登录后自动搜索目标课程并点击进入
8. 将 `AUTHORIZATION`、`COOKIE`、`COURSE_ID` 写入 `.env`

### 示例2：手动指定课程名

```bash
/auto-login @/Users/zhangyichi/工作/能力训练/skills_training_course/武夷学院-茶艺学实践/实训任务6/训练剧本配置.md --course-name "茶艺学 武夷学院"
```

**执行流程**：
1. 路径仍用于识别学校和省区
2. 课程检索时优先使用 `茶艺学 武夷学院`
3. 适合目录名和平台课程名不一致时使用

### 示例3：直接指定省区

```bash
/auto-login --province "贵州省区"
```

### 示例4：直接指定账号

```bash
/auto-login --account JFFJ1001000000 --password Zhihuishu@000000
```

## 注意事项

1. **验证码处理**：当前平台使用网易易盾滑块，脚本会自动破解（详见 `scripts/yidun_slider.py`），单次通过率约 60-80%，通常 1-2 次内通过；4 次仍失败再转人工。
2. **换省区自动重登**：脚本会读取历史会话中的身份信息；如果当前保存的是福建省区，而本次目标是贵州省区，会先自动清理旧会话再登录新账号。
3. **同省区强制重登**：如果你想在同一个省区也重新走一遍登录流程，可以显式加 `--force-relogin`。
4. **课程匹配策略**：脚本会优先使用“课程关键词 + 学校”组合去搜课；如果目录名和平台课程名差异太大，建议显式传 `--course-name`。
5. **会话有效期**：登录后的会话状态可能有时效性，如遇到 401/403 错误，需要重新运行登录。
6. **浏览器依赖**：需要安装 Playwright 和 Chromium：
   ```bash
   pip install playwright
   playwright install chromium
   ```
7. **.env 文件更新**：脚本会直接修改项目根目录 `.env` 文件，请确保文件可写。
8. **浏览器保持开启**：脚本执行完成后浏览器窗口会保持开启，方便用户继续操作；在终端中按 Enter 键才会关闭浏览器并退出脚本（自动化环境会自动跳过等待）。
9. **安全提示**：密码以明文形式临时使用，不会保存在脚本或生成的文件中。

## 错误处理

| 错误场景 | 处理策略 |
|---------|---------|
| 学校无法识别 | 提示用户手动选择省区或输入账号 |
| 账号未找到 | 提示检查映射文件和账号配置 |
| 登录失败（密码错误） | 提示检查密码，提供重试 |
| 验证码 4 次未通过 | 自动转人工拖动，或重新运行脚本（换一张图重试） |
| 课程搜索结果不准 | 使用 `--course-name` 显式指定平台课程名 |
| COURSE_ID 未提取到 | 检查是否成功进入课程页面 |
| 想切换省区但仍复用旧 cookie | 重新运行脚本，脚本会自动检测省区不一致并清理旧会话；必要时加 `--force-relogin` |
| 网络超时 | 重新运行并检查当前网络状态 |

## 凭证存放位置与跨 Agent 复用

登录成功后凭证落在三处：

| 位置 | 内容 | 用途 | 是否入 git |
|------|------|------|-----------|
| `能力训练/.env` | `AUTHORIZATION` / `COOKIE` / `COURSE_ID` | HTTP 调用（requests 带 `Authorization` + `Cookie` 头） | 否（`.gitignore`） |
| `sessions/accounts/<教工号>.json` | Playwright storage_state：约 28 个 cookie + localStorage | 浏览器自动化直接复用（无登录、无滑块） | 否（`sessions/.gitignore`） |
| `sessions/accounts/<教工号>.meta.json` | account / school / province / real_name / saved_at | 判断是否可复用 | 否 |

注意：`.env` 只保存**最后一次**登录的账号；按账号隔离的凭证在 `sessions/accounts/<教工号>.json`，互不覆盖。

其他 agent 复用的三种方式：

```bash
# 1) 离线导出请求头（不启动浏览器）
python3 auto_login.py --export-headers CUPB000000     # JSON: {"Authorization": "...", "Cookie": "..."}

# 2) 导出 shell 变量
eval "$(python3 auto_login.py --export-env CUPB000000)"

# 3) 查看/清理
python3 auto_login.py --list-sessions
python3 auto_login.py --forget-session CUPB000000
```

```python
# Python 里直接复用浏览器登录态
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome")
    ctx = b.new_context(storage_state=".claude/skills/training-auto-login/sessions/accounts/CUPB000000.json")
    page = ctx.new_page()
    page.goto("https://hike-teaching-center.polymas.com/tch-hike/agent-course-hike/ai-course-center")
```

有效期：关键 cookie（`jt-cas` / `polymas-token` / `CASLOGC`）是会话级 cookie，服务端另有超时；
本技能默认按 72 小时判断复用，超时或服务端已失效时会自动重登并覆盖对应文件。

## 账号来源（账号表优先）

默认账号源：`/Users/zhangyichi/工作/能力训练/智能体课程配置账号情况.xlsx`（147 条有效账号）。

表格是多段式结构，解析规则：

| 位置 | 含义 |
|------|------|
| 主段（第 6 行起） | `对应省份 \| 教工号 \| 学校/机构 \| 机构(Polymas实验室) \| 默认密码 \| 手机号 \| 备注` |
| 表尾小段 | 演示账号、学生账号、再造课堂、评审账号（列序不同） |
| 识别规则 | B 列/第 2 列必须像账号 `^[A-Za-z0-9_-]{6,}$`；密码取 D/E 中第一个 `Zhihuishu@` 开头的值 |

按行解析出的字段：`province / province_key / account / name(学校或机构) / org / password / phone / note`。

**账号优先级**：

1. `--account` + `--password`（用户显式指定）
2. `--school` → 账号表（唯一来源，查不到直接报错并提示 `--list-accounts`）
3. `--province` → 账号表省区行 → 本地 JSON
4. 训练剧本路径推断学校 → 账号表 → 本地 JSON

账号表与本地 JSON 的密码并不一致（如 `JFTJ1001000000` 在账号表是 `Zhihuishu@000007`，JSON 里是 `Zhihuishu@000000`），**一律以账号表为准**。

**课程关键词提取**：目录名形如 `学校-课程名` 时，首段以 `大学/学院/学校/校区/分校` 结尾 → 判为学校，
其余部分作为课程关键词（例：`天津财经大学-理解当代中国英语演讲` → 学校 `天津财经大学`、关键词 `理解当代中国英语演讲`）。
只有首段不像学校名时才回落到原来的推断逻辑。

**学校名匹配**：`中国石油大学（北京）` 与 `中国石油大学(北京)`、空格差异、`大学/学院` 后缀差异都会归一化；顺序为 精确 → 归一化精确 → 省区精确 → 包含（取名字最长的）→ 去后缀再匹配。

```bash
cd .claude/skills/training-auto-login/scripts

# 查账号表
python3 auto_login.py --list-accounts            # 全部 147 条
python3 auto_login.py --list-accounts 天津        # 按省份/学校关键字过滤

# 用账号表登录（未指定 Chrome profile 时的默认动作）
python3 auto_login.py --school "中国石油大学（北京）"
python3 auto_login.py --school "北京化工大学"

# 换一份账号表
python3 auto_login.py --school "天津大学" --accounts-xlsx /path/to/另一份.xlsx
```

## 多账号登录态复用（会话缓存）

登录态按**账号**隔离存放，路径 `sessions/accounts/<账号>.json`，旁边一份 `<账号>.meta.json`
记录 account / school / province / real_name / saved_at。

运行时的判定顺序：

1. `sessions/accounts/<账号>.json` 存在、未超过 TTL、且 meta 里账号一致 → **直接复用**，不弹登录、不过滑块
2. 文件不存在 / 超过 TTL / 账号不匹配 → **新开干净的浏览器上下文**，用账号密码登录（自动破滑块），成功后落盘
3. 判定为"可复用"但打开后发现已失效（被踢/过期）→ 自动丢弃旧会话，新开网页重新登录
4. 登录成功以 **Cookie 是否落地**为准（`jt-cas` / `CASLOGC` / `polymas-token` / `AI-POLY-UINFO`），
   不依赖跳转是否成功——课程中心偶发 `ERR_CONNECTION_CLOSED` 也不影响拿到 AUTHORIZATION

常用命令：

```bash
# 首次：新开网页登录并缓存
python3 auto_login.py --school 天津大学

# 第二次：命中缓存（约 6-10s，无滑块）
python3 auto_login.py --school 天津大学

# 查看所有缓存账号及其有效期
python3 auto_login.py --list-sessions

# 强制重新登录 / 不复用
python3 auto_login.py --school 天津大学 --force-relogin
python3 auto_login.py --school 天津大学 --no-reuse-session

# 自定义有效期（默认 72 小时，0 = 不按时间过期）
python3 auto_login.py --school 天津大学 --session-ttl 24

# 删除某账号缓存
python3 auto_login.py --forget-session TJU000000
```

账号来源：只有账号表一个来源。`--account/--password` 直传 > `--school` > `--province` > 剧本路径推断学校。

新增学校账号只需在 `智能体课程配置账号情况.xlsx` 主段加一行：

```
对应省份 | 教工号 | 学校/机构 | 机构名称 | 默认密码 | 手机号 | 备注
天津     | TJU000000 | 天津大学 | Polymas实验室 | Zhihuishu@000000 | 14950000005 |
```

不用改代码，`--list-accounts 天津` 能查到即生效。

## 验证码破解原理（yidun_slider.py）

- 结构：`.yidun_bg-img`（480x240 原图，页面 400x200）与 `.yidun_jigsaw`（拼图条，与背景左上对齐）→ y 已知，只解 x。
- 缺口定位：三路投票 `edge`（轮廓相关）/ `fog`（缺口=低对比+去饱和+趋中灰）/ `content`（masked CCOEFF），两路接近取均值，全分歧时信 edge。
- 关键坑：手柄行程 ≠ 拼图行程，实测 `piece_left = knob_dx - 18px`（死区），先标定死区再补足，否则恒定偏 18px 必挂。
- 轨迹：加速段 → 巡航抖动 → 减速 → 过冲回拉，40~80 个点，0.8~1.5s，y 抖动 ±1px，走 CDP 真实事件（isTrusted=true）。
- 判定：读 `c.dun.163.com/api/v3/check` 的 `result` 字段。

## Version History

- v1.8 (2026-11-10)：新增 `--export-headers` / `--export-env`，可在不启动浏览器的情况下把某账号的 AUTHORIZATION/COOKIE 交给其他 agent 复用；补充凭证存放位置说明
- v1.7 (2026-11-10)：账号来源改为根目录《智能体课程配置账号情况.xlsx》优先（新增 `--list-accounts` / `--accounts-xlsx`），学校名归一化匹配，JSON 映射降级为兜底
- v1.6 (2026-11-09)：按账号缓存登录态（`sessions/accounts/<账号>.json`），命中即复用、未命中/过期自动新开网页登录；新增 `--school` / `--list-sessions` / `--forget-session` / `--no-reuse-session` / `--session-ttl`；登录判定改为 Cookie 落地优先，课程中心网络抖动自动重试降级
- v1.5 (2026-11-09)：内置易盾滑块自动破解；登录页滑块不再需要人工介入

- v1.4 (2026-03-14)：新增 `--keep-open` 参数，支持脚本执行完成后保持浏览器开启，由用户手动控制关闭时机
- v1.3 (2026-03-14)：浏览器执行完成后保持开启（终端交互需按 Enter 关闭）；改进课程关键词提取逻辑，正确处理 "郑州大学-医学遗传学" 等带连字符目录名
- v1.2 (2026-03-13)：新增跨省区自动清理旧会话并重登、`--force-relogin` 强制重登支持
- v1.1 (2026-03-13)：新增课程自动检索与进入、`COURSE_ID` 自动回填、路径课程名解析、`--course-name` 支持、系统 Chrome 优先启动、会话复用
- v1.0 (2026-03-13)：初始版本，支持学校自动识别、省区账号查询、Playwright 自动登录、`.env` 自动更新
