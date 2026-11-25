# polymas-gateway-kit

让 **Claude Code / pi agent / DeepSeek Harness (DSH)** 能真正用上公司 llm-service 网关
（`claude-opus-5`、`gpt-5.6-sol`、`kimi-k3` …）的一套「客户端侧适配层」+ 接入文档。

> 网关目前有几处不符合 OpenAI 契约 / 会破坏数据的地方，导致按规范实现的客户端要么
> **读不到任何输出**，要么**工具定义被上游拒绝**。修复在网关侧（见
> [`docs/gateway-report.md`](docs/gateway-report.md)，带完整复现与精确阈值），
> 本包是在那之前的本地补丁 —— 网关修好后可以直接卸载。

---

## 30 秒了解它在补什么

| 网关行为 | 后果 | 本包的处理 |
|---|---|---|
| 流式分片把增量内容放在 `choices[].message`（标准是 `delta`） | 客户端读到空响应，整轮失败 | 改名为 `delta` |
| `usage` 里的 token 计数是字符串 `"19"` | 客户端累加变字符串拼接，污染持久化数据 | 转成数字 |
| 流结束不发 `data: [DONE]` | 部分客户端等到超时 | 补上 |
| 请求里超过 `2³¹−1` 的 JSON 整数被写成字符串 | 工具 schema 校验失败（`JSON schema is invalid`）→ Agent 用不了 | 删除/钳制越界数值约束 |
| 上游不认 `role: "developer"` | 阿里百炼等报 `developer is not one of [...]` | 归一成 `system` |

外加一件事：**Claude Code 讲 Anthropic 协议，而网关只有 OpenAI 端点**，
所以它还需要 CC Switch 自带的本地代理做协议转换 —— 文档在
[`clients/cc-switch.md`](clients/cc-switch.md)。

---

## 快速开始

```bash
# 1) 装反代（零依赖，只要有 Node ≥ 18；不需要 API key）
./install.sh

# 2) 验证：不碰真网关，起个假上游复刻网关的毛病，逐项断言改写
node proxy/selftest.mjs          # 期望 13 项全过

# 3) 把客户端指过来（任选）
clients/pi-setup.sh --key sk-xxxx --default claude-opus-5   # pi
#   Claude Code → clients/cc-switch.md
#   DSH         → clients/dsh.md
```

装完反代的地址是 `http://127.0.0.1:8787/v1`，客户端拿它当 baseURL。

---

## 目录

```
install.sh / uninstall.sh     一键安装（macOS launchd / Linux systemd）、卸载
config.env.example            端口、上游、安装目录、日志路径（可选）
proxy/
  polymas-proxy.mjs           反代本体（零依赖，仅 Node 标准库）
  selftest.mjs                离线自测：假上游 + 13 项断言，不需要真网关
launchd/                       macOS launchd 模板
clients/
  pi-setup.sh                 写 ~/.pi/agent/models.json（幂等、自动备份、可 --dry-run）
  cc-switch.md                CC Switch 里 Claude Code / pi 两个 app 的填法
  dsh.md                      DSH provider 片段
docs/
  gateway-report.md           给网关维护方的问题报告（可直接转发）
  gateway-check.py            网关兼容性检测脚本，退出码 0 = 网关已修好
  model-capability.md         模型能力对照表：哪些模型「带工具」可用（实测）
```

---

## 验证与排错

**反代有没有坏**（离线，不依赖网关）：

```bash
node proxy/selftest.mjs
```

**网关还坏不坏**（需要 key；决定这层反代还要不要）：

```bash
LLM_API_KEY=sk-xxxx python3 docs/gateway-check.py
# 退出码 0  → 网关已修复，可以 ./uninstall.sh 并让客户端直连
# 退出码 1  → 仍有问题，反代继续用
```

**看反代日志**：

```bash
tail -f ~/Library/Logs/polymas-proxy.log     # macOS（Linux 见 systemd 或 config.env 的日志路径）
# ✎ 请求体净化: claude-opus-5 schema 59 处 + developer→system 1 条   ← 说明改写在生效
```

**排查上游报的 schema 错**：把请求体落盘来比对（平时别开）：

```bash
POLYMAS_PROXY_DUMP_DIR=/tmp/polymas-dumps POLYMAS_PROXY_PORT=8799 \
  node proxy/polymas-proxy.mjs
```

**CC Switch 侧的请求记录**：

```bash
sqlite3 ~/.cc-switch/cc-switch.db \
 "select datetime(created_at,'unixepoch','localtime') t, model, status_code, substr(coalesce(error_message,''),1,80)
  from proxy_request_logs order by created_at desc limit 10"
```

常见报错对照表见 [`clients/cc-switch.md`](clients/cc-switch.md) 末尾。

---

## 安全说明

- 反代**不保存、不需要任何密钥**：鉴权头由客户端原样透传，`install.sh` 里没有 key。
- 密钥只出现在**客户端配置**里（CC Switch 的 provider、`~/.pi/agent/models.json`、DSH 凭据库）。
  `pi-setup.sh` 会把 key 写进 `models.json`（和 pi 官方示例一致），注意该文件别提交进 git。
- 反代默认只监听 `127.0.0.1`。
- 反代只在**确有需要时**才改写请求体（数值越界 / `developer` 角色）；
  其余情况逐字节透传，未触发时 `messages`/`tools`/`max_tokens` 完全不变。

## 局限

- 这是**客户端侧补救**，不是修复；根因在网关（`docs/gateway-report.md`，已附精确阈值证据）。
- 依赖一个常驻进程。它挂了 → 指向它的客户端不可用（其他 provider 不受影响）。
- 请求侧只处理**数值约束关键字**与 `developer` 角色，不动 `default`/`const`/`enum` 等数据位置。
- `contextWindow` 默认按 256K 给：网关真实上限未经确认，别盲目填 1M。
- `gpt-5.6-sol` 的上游不允许「工具 + `reasoning_effort`」共存，因此
  `pi-setup.sh` 把它标为非推理模型。
- **有些模型能力上就不支持 Agent 场景**：`gpt-6-sol` / `gpt-6.1-sol` 在 Chat Completions 上
  不接受 function tools（上游要求走 Responses API，而网关没有该端点）。
  逐模型实测见 [`docs/model-capability.md`](docs/model-capability.md)。
  这类缺口反代补不了 —— 反代只改表示层，不改模型能力。

## 卸载

```bash
./uninstall.sh            # 停服务、删注册
./uninstall.sh --purge    # 连安装目录一起删
```

别忘了把客户端里的 baseURL 改回去（`uninstall.sh` 结尾会再提醒一次）。
