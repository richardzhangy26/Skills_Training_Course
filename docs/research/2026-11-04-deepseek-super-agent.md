# DeepSeek Super Agent 调研

日期：2026-11-04。调研范围：定位 2026 年 10 月底公开、被称作 DeepSeek Super Agent 的代码仓库，并用其 README、编号文档、源码，以及 DeepSeek Harness 团队同日发布的设计长文，回答它是什么、机制是什么、文档写了哪些用法、能否用到本仓库。没有运行原型，没有改本仓库业务代码，没有把二手博客的机制描述当成证据。

## 结论先行

2026-11-04 被广泛叫做 DeepSeek Super Agent 的代码项目，规范名称是 `dsh-superagent`，仓库是 [deepseek-ai/dsh-superagent-prototype](https://github.com/deepseek-ai/dsh-superagent-prototype)。它由 deepseek-ai 组织发布，作者栏为 DeepSeek Harness Team，MIT 许可证，版权归 DeepSeek Harness Team；README 同时写明它只是研究原型，不是 DeepSeek 正式产品。[README](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/README.md)、[package.json](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/package.json)、[LICENSE](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/LICENSE)

它不是新模型，也不是可订阅的聊天产品。它是 DeepSeek Harness 的一个 bundle：盯住一个 github.com 仓库，可选再听飞书；被允许的人提出请求后，它开工单，在独立的 Harness Session 和目录里做，再回到原对话，例如提一个 Pull Request。[README](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/README.md)、[docs/006](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/docs/006-deployment.md)

同日的微信长文《Super-agent 设计探索：迈向更自主的 Agent 系统》讲的是内部架构思路，开篇写明不是对 DeepSeek Harness 现有产品功能的介绍。原型 README 写明公开代码经过改写，与内部版本和该文都不相同，文中有些设计是未来方向、原型里没有。[微信原文](https://mp.weixin.qq.com/s/zoS7GlReWPhfCjENGxXCdg)、[README](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/README.md)

原型自己实现的是来源、工单、授权和派工；模型来回调用工具的循环交给 DeepSeek Harness 的 Session。权限由代码里的允许名单、准入表和 Mandate 执行，提示词改不了这些门禁。默认是只记录、不执行主动任务的 `observe`。[docs/001](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/docs/001-domain.md)、[docs/002](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/docs/002-authorization.md)、[docs/004](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/docs/004-prompts.md)、[src/index.ts](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/src/index.ts)

执行器以操作者的操作系统用户、`danger-full-access` 运行。文档写明账号包装脚本不是安全边界，worker 仍可按绝对路径执行程序并读取家目录。[docs/006](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/docs/006-deployment.md)

对本仓库：它可以作为制作侧、只盯一个 GitHub 仓库的编码助手来评估，主动接单应先停在 `observe`；允许名单上的人一旦 `@` 它，仍然会执行并改代码。它不适合替换学员面对的阶段模型 `doubao-seed-2.0-pro`，也不是对话评测器或 Polymas 导入器。后半句是对照本仓库规则后的结论，模型规则见 [Agents.md](../../Agents.md)。

仓库创建于 2026-10-31，本次打开的仓库页内嵌数据为 17575 star、1902 fork。热度的一手证据是这个时间差，不是博客里的星标时间线。[仓库页](https://github.com/deepseek-ai/dsh-superagent-prototype)

## 它是什么（含消歧）

### 判定的规范项目

| 项 | 事实 |
| --- | --- |
| 规范名称 | 包名和文档标题是 `dsh-superagent`；仓库名是 `dsh-superagent-prototype`；描述是 “Towards a More Autonomous Agent System” |
| 仓库 | https://github.com/deepseek-ai/dsh-superagent-prototype |
| 当前提交 | `8c32a9dc5d72c033816c6a8110b37f40cf94fba4`，作者 DeepSeek Harness Team `<team@dsh.dev>`，作者日期 2026-10-31 20:05 +0800，说明为 “feat: add the dsh-superagent research prototype”。克隆时 `main` 只有这一次提交，没有 tag、没有 release |
| 版本 | `0.1.0`，`private: true` |
| 许可证 | MIT，Copyright (c) 2026 DeepSeek Harness Team |
| 维护者 | GitHub 组织 `deepseek-ai`。作者字段是 DeepSeek Harness Team，不是一篇署名到个人的论文 |
| 语言与运行时 | TypeScript。Node.js `^22.19.0 \|\| >=24`，pnpm 11.7.0。必须作为 DeepSeek Harness bundle 运行，`engines.dsh` 为 `^0.2.1-alpha.2`；部署文档安装的公开版本是 `@deepseek-ai/dsh@0.2.1-rc.3`，并写明其他版本也必须落在 `engines.dsh` 范围内 |
| 模型 | 不绑定某一个模型 ID。使用该 Harness profile 的默认模型，除非 Eval 或 Execution 设置里另写 `{ provider, model, reasoningEffort? }` |

上表来自本次克隆的提交、[package.json](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/package.json)、[LICENSE](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/LICENSE) 和 [docs/006](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/docs/006-deployment.md)。2026-11-04 打开仓库 HTML 时，页内 JSON 为 `createdAt` 2026-10-31T09:32:46Z、`stargazerCount` 17575、`forksCount` 1902、`watcherCount` 118。[仓库页](https://github.com/deepseek-ai/dsh-superagent-prototype)

为什么判定就是现在说的那个项目：组织是 deepseek-ai；README 用 Super-agent 设计文的英文标题指代自己所对应的设计；创建到本次读取大约四天，星标已经过万。同名社区仓库的 star 在本次检索时是个位数到十位数，且 README 自己声明不是官方实现。社区仓库只用于消歧，见下一小节。

一句话：它是一个常驻的、面向单个 GitHub 仓库的主动编码代理框架，用来在少打扰人的前提下，把被授权的请求做成可审查的代码结果。它不解决模型训练、不提供 Polymas 或任何教学平台的对话运行时，也不声称是生产级软件。[README](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/README.md)、[docs/000](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/docs/000-philosophy.md)

明确不覆盖的范围，以文档原文为准：只支持 github.com，不支持 GitHub Enterprise Server；飞书是可关闭的可选来源，bundle 里默认 `disabled: true`；一个部署对应一个仓库；主动任务在默认的 `observe` 下只记录“本来会接”，并不执行。[docs/006](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/docs/006-deployment.md)、[cordis.patch.yml](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/cordis.patch.yml)、[docs/002](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/docs/002-authorization.md)

### 设计长文，不要和原型混写

2026-10-31 20:29，微信公众号文章《Super-agent 设计探索：迈向更自主的 Agent 系统》署名为原创、DeepSeek 产品部、DeepSeek Harness 团队。正文第一句是：这是面向工程实践的架构思路探讨，并非对 DeepSeek Harness 现有产品功能的介绍。[微信原文](https://mp.weixin.qq.com/s/zoS7GlReWPhfCjENGxXCdg)

该文把 Super-agent 定义成一种能跨会话保持上下文、同时推进多项复杂任务且互不干扰的连续实体，并列出四个特征：连续、高效、主动、持久。它提出五个模块：Router/Worker 双层、事件驱动、面向人的交互、计算/状态/环境分离、外部 Watchdog。文中写，团队观察一个人通常只能同时跟进 3 到 5 个活跃 Session；单任务上限取决于模型，多任务上限取决于人的注意力。这些是文章里的观察和设计主张，不是原型 README 的产品承诺。[微信原文](https://mp.weixin.qq.com/s/zoS7GlReWPhfCjENGxXCdg)

文章第 7 节的数字只描述合成实验：约 300 条消息、其中约 20 条工作请求，编码被换成只消耗时间的工具，每种方案跑 5 次；作者写明测的是调度与协作，不是单任务执行能力。文中给出的 Super-agent 任务完成时间是 p50 12.4 分钟、p95 15.7 分钟。实验脚本、模型和原始数据不在原型仓库里，本次不能复核计算过程，只能引用文章自述。[微信原文](https://mp.weixin.qq.com/s/zoS7GlReWPhfCjENGxXCdg)

文章还写了几件原型文档和源码里没有对应实现的事，读的时候不能倒灌进原型：云端无状态计算与端侧 daemon、BYOM、外部 Watchdog Session 用模型判断 worker 是否跑偏、Router 水平分片、投机执行时先在后台改代码再决定是否交付。本次在原型的 markdown 与 TypeScript 里检索 `Watchdog` / `watchdog`，没有这套控制回路；`cordis.patch.yml` 把调度、目标、工作流留在了 worker/router preset 之外。[微信原文](https://mp.weixin.qq.com/s/zoS7GlReWPhfCjENGxXCdg)、[cordis.patch.yml](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/cordis.patch.yml)

文章第 4.1 节写：异步 ReAct 的 `start()` / `stop()` 已经在 DeepSeek Harness 里实现，但尚未默认开启。这是文章对 Harness 的陈述。原型没有重新实现这个循环，只是在自己的 preset 里把前台 shell 和 job 等待限制为 5 秒。[微信原文](https://mp.weixin.qq.com/s/zoS7GlReWPhfCjENGxXCdg)、[cordis.patch.yml](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/cordis.patch.yml)

英文标题页 [Exploring Super-agent Design](https://x.com/DeepSeekHarness/article/2116857257245987236) 能打开，账号显示为 DeepSeek Harness，标题与 README 所引英文标题一致。本次页面正文长度为 0，没有抽出英文正文，因此不引用其段落。中文事实以微信原文为准。

### 容易混淆的项目

- [deepseek-ai/deepseek-harness](https://github.com/deepseek-ai/deepseek-harness)：Super-agent 所插入的运行时，口号是 “Everything is a Plugin”。2026-11-04 仓库页星标 271594。产品页 [deepseek.com/en/harness](https://www.deepseek.com/en/harness/) 写它处于 public preview、开源、插件可组合；本次页面正文检索不到 Super-agent、superagent 或 dsh-superagent。它不是 Super Agent 本身。
- [LofiSu/deepseek-super-agent](https://github.com/LofiSu/deepseek-super-agent)：社区独立实现，README 写明受公开文章和原型启发，不依赖 DeepSeek Harness、Cordis 或 `@deepseek-ai/dsh*`。
- [vicfei/dsh-super-agent](https://github.com/vicfei/dsh-super-agent)：社区项目，README 写明不隶属于 DeepSeek，把准入控制接到任意 CLI 编码代理上，不需要 DSH。
- [thefullgc/opensuperagent](https://github.com/thefullgc/opensuperagent)：社区落地，自带 `opensuperagent serve` 和另一套 Router/Worker，不是 `dsh-superagent` bundle。
- [yingpengma/cc-super-agent](https://github.com/yingpengma/cc-super-agent)：面向 Claude Code 的 Router–Worker 实验，不是 DeepSeek Harness 插件。
- [Check-mj/dsh-superagent-windows](https://github.com/Check-mj/dsh-superagent-windows)：README 写明是上游原型的非官方 Windows 适配，并打算补上游没有的 Watchdog 和 Router 分片。不能用它的额外功能描述上游。
- [sakisakisa-design/SuperDeepSeek](https://github.com/sakisakisa-design/SuperDeepSeek)：本地 OpenAI/Anthropic 兼容网关，名字相近，不是这个代理系统。

## 一手来源清单

本次实际读过的页面和文件：

- 仓库提交 [8c32a9dc5d72](https://github.com/deepseek-ai/dsh-superagent-prototype/commit/8c32a9dc5d72c033816c6a8110b37f40cf94fba4)：2026-11-04 浅克隆，`git log` 只有这一次提交。
- [README.md](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/README.md)、[SETUP.md](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/SETUP.md)、[LICENSE](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/LICENSE)、[package.json](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/package.json)、[examples/profile.cordis.patch.yml](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/examples/profile.cordis.patch.yml)。
- 编号文档 [000](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/docs/000-philosophy.md) 至 [008](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/docs/008-cookbook.md) 全文。008 后半是扩展 Source 的示例代码，机制结论没有依赖那段示例实现。
- 源码：`src/index.ts`、`src/core/engine.ts` 头部与 `receive`/`evaluateDue`、`src/core/evals.ts` 的 `REQUEUES`、`src/core/memory.ts`、`src/policy.ts` 的默认 schema、`src/limits.ts`、`src/app/tools/main.ts`、`src/app/tools/executor.ts`、`src/app/role-models.ts`、`src/app/retry-health.ts`、`src/executor/dsh.ts` 的 `BACKGROUND_LIMIT_MS`、`cordis.patch.yml`、`prompts/orchestrator.md`、`prompts/worker.md`、`prompts/admission.md`。
- 设计长文全文：[mp.weixin.qq.com/s/zoS7GlReWPhfCjENGxXCdg](https://mp.weixin.qq.com/s/zoS7GlReWPhfCjENGxXCdg)。这个 URL 先出现在社区仓库 README 中，打开后的标题、日期和“DeepSeek Harness 团队”署名与原型 README 所引文章一致，因此把它当作该文原文。
- Harness 产品页 [https://www.deepseek.com/en/harness/](https://www.deepseek.com/en/harness/) 与仓库页 [deepseek-ai/deepseek-harness](https://github.com/deepseek-ai/deepseek-harness)。没有通读 Harness 源码，所以下文不描述 Harness 内部的 agent loop 实现。
- 本仓库只读了 [Agents.md](../../Agents.md)、[skill_training_build/AGENTS.md](../../skill_training_build/AGENTS.md)、[skill_training_pro/AGENTS.md](../../skill_training_pro/AGENTS.md)、[evaluation/AGENTS.md](../../evaluation/AGENTS.md)、[.claude/skills/AGENTS.md](../../.claude/skills/AGENTS.md)、[docs/agents/issue-tracker.md](../agents/issue-tracker.md)。

二手博客只用来发现仓库 URL 和微信原文链接。博客中的星标时间线、安全审计和“已实测跑通 PR”都没有回源，下面不采用。

## 原理

下面只写原型文档和本次读到的源码。设计长文里多出来的模块已在上一节隔开。

### 循环：不是一个大 ReAct，而是领域状态机加两个 Harness Session

插件入口 `apply` 注入 Harness 的 `agents`、`sessionController`、`llm`、`tools`、`subprocess` 等服务，再构造 `Runtime`。领域规则不在这个入口里。[src/index.ts](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/src/index.ts)

工作从 Source 进入。Source 记住读位置，丢掉机器人自己的消息和监听范围之外的事件，把剩下的变成不可变 Trigger。Trigger 属于 Thread。同一 Thread 同时最多一次 Eval。人的后续消息如果已经落到某张工单，就扇出给那张工单，不再评估；其余 Trigger 进入 Eval。Eval 接受后才创建 Ticket 和 Mandate，Assignment 把工单交给 Executor，结果经 Channel 回到来源。[docs/001](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/docs/001-domain.md)

`Engine` 是唯一改写 Trigger、Thread、Decision、Ticket、Assignment 的入口。每个命令在一次仓库事务里完成；对外副作用先入队，提交后再做。`evaluateDue` 在未暂停时启动到期的 Eval、处理超时，并唤醒暂停期间收到人的消息的已结束工单。[src/core/engine.ts](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/src/core/engine.ts)、[docs/007](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/docs/007-architecture.md)

代码和提示词里的两个角色是 `orchestrator`（主 Session）和 `worker`（每张工单一个 Executor Session，目录名按工单短名）。主 Session 只做路由和对外回复；worker 读原始材料、判断范围、实现和验证。主 Session 的提示词写明不要补实现计划。[docs/001](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/docs/001-domain.md)、[prompts/orchestrator.md](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/prompts/orchestrator.md)、[prompts/worker.md](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/prompts/worker.md)

模型回合本身不在本仓库。preset 注释写的是：worker 基于 Harness 的 `standard`，前台命令超过 5 秒就转成后台 job；worker 的 subagent 使用 `standard`，那一层要 60 秒才转后台。主 Session 没有 subagent、没有网页工具、文件工具关闭写和编辑，也没有 persona，因为它的提示词是完整的。[cordis.patch.yml](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/cordis.patch.yml)

本次没有读 Harness 的 loop 源码。推断：主 Session 和 worker 的“想一步、调一个工具、再想一步”发生在被注入的 `@deepseek-ai/dsh-agent` 里，本仓库只规定 preset、工具和何时往 Session 里投消息。依据只是 `package.json` 的 peerDependency 和上面的 preset，不是 Harness 源码引用。

### 工具协议

工具参数用 zod 的 strict object。主 Session 有 14 个应用工具：`orchestrator_read`、`orchestrator_route`、`orchestrator_ticket_retry`、`orchestrator_ticket_request_status`、`orchestrator_ticket_note`、`orchestrator_trigger_requeue`、`orchestrator_eval`、`orchestrator_eval_read`、`orchestrator_eval_decide`、`orchestrator_reply`、`orchestrator_thread_unsubscribe`、`orchestrator_settings_save`、`orchestrator_policy_sync`、`orchestrator_prompts_save`。`orchestrator_route` 一次 1 到 20 条决定，单条失败不影响其他条。[docs/007](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/docs/007-architecture.md)、[src/app/tools/main.ts](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/src/app/tools/main.ts)

Executor 有 6 个应用工具：`orchestrator_read`、`orchestrator_ack`、`orchestrator_thread_unrelated`、`orchestrator_thread_follow`、`orchestrator_trigger_handback`、`orchestrator_report`。报告状态只能是 `progress`、`ready`、`blocked`、`failed`、`dropped`。工单结束后再调用会直接抛错。没有一个工具能让 Executor 自己宣布“人要求停止”；停止只由 Eval 或面板命令产生。[src/app/tools/executor.ts](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/src/app/tools/executor.ts)、[docs/002](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/docs/002-authorization.md)

读工具是分页资源，不是把整个仓库塞进上下文。默认一页文本 4000 个 UTF-16 码元，最多 8000；列表默认 20 条，最多 50。评估窗口是 Thread 前 5 条再加触发点两侧各 5 条。架构文档写，主 Session 另外还有 Harness 的 `skill`、`bash`、`read`、`read_image`、`job_output`、`job_list`、`job_kill`；不读代码只是提示词约束，不是工具层禁止。[docs/007](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/docs/007-architecture.md)

worker preset 挂载的 Harness 工具是 shell、文件读写、文件搜索、job、skill、压缩、subagent、todo，以及只搜索不抓取的 web 工具（`fetch: false`）。明确留出的包括向人提问、展示 UI、plan mode、插件管理、调度、goals、workflows 和 fork 式 subagent。[cordis.patch.yml](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/cordis.patch.yml)

主 Session 有一个代码守卫：命令位置上的 `sleep`、超过 30 秒的 shell `timeoutMs`、超过 5 秒的 `job_output` 等待会被拒绝。注释写明原因是阻塞会耽误新的候选。[src/app/sessions.ts](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/src/app/sessions.ts)

### 记忆和上下文

`src/core/memory.ts` 的 `MemoryRepositories` 是测试用的内存仓库，不是对话记忆。[src/core/memory.ts](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/src/core/memory.ts)

持久状态是 `<stateDir>/orchestrator.sqlite` 里的 trigger、disposition、thread、ticket、decision、effect、outbox 和 kv。文档写明目前没有删除旧记录，这些表和每次设置版本会一直增长。Session 翻页用的文本缓存在重启后丢失。[docs/007](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/docs/007-architecture.md)

模型侧的上下文是 Harness Session 自己的事件，加上 preset 里的 `@deepseek-ai/dsh-compaction-basic` 和工具结果裁剪（阈值 8192 字符，保留头 4096、尾 1024）。长内容不内联时，卡片带 `chars` 和 `orchestrator_read` 指针。这是原型的分页读法。设计长文把类似想法叫作 Inline & Spill 和链式召回；原型文档没有使用这两个名字，不能把文章里的多跳检索图说成已经在这个提交里实现。[cordis.patch.yml](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/cordis.patch.yml)、[docs/007](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/docs/007-architecture.md)、[微信原文](https://mp.weixin.qq.com/s/zoS7GlReWPhfCjENGxXCdg)

提示词每次模型请求都重新装配，最后一节是当前 Policy。改提示词不重启、不取消 Session。Executor 还会读 Harness 的 coding prompt 和目标仓库的 `AGENTS.md`；主 Session 不读仓库 `AGENTS.md`。[docs/004](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/docs/004-prompts.md)

### 规划和多代理

没有名为 planner 的组件。主 Session 被要求不做技术决定，路由笔记最多 30 个词。worker 在工单目录里自己选做法并验证。preset 把 plan mode 留在外面。因此“规划”只是 worker 提示词里的步骤，不是一个可切换的计划模式。[docs/004](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/docs/004-prompts.md)、[prompts/worker.md](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/prompts/worker.md)、[cordis.patch.yml](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/cordis.patch.yml)

多代理限于：一个常驻主 Session，加每张工单一个 worker Session。worker 还可以再开 Harness `standard` subagent，工单结束时这些工具被拿走。同层 worker 不直接对话；主 Session 可以用最多 100 词的 `orchestrator_ticket_note` 转述事实，且注明不授予权限。订阅是多对多，但上下文订阅不恢复已结束工单，也不提高授权强度。[docs/003](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/docs/003-execution.md)、[docs/004](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/docs/004-prompts.md)

并发槽默认 `maxWorkers` 为 3，合法范围 1 到 16。人的消息或状态请求可以多用一个槽，避免新工单把人挡在外面。准备命令最长 10 分钟；没有准备命令时，worker 从空目录开始。[src/policy.ts](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/src/policy.ts)、[src/limits.ts](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/src/limits.ts)、[docs/003](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/docs/003-execution.md)

### 权限和安全边界

两层 Eval。程序层的 gate 看发件人、是否点名代理、准入表和机器人名单，得出 `explicit`、`inferred` 或不准入。语义层只在需要时由主 Session 调用 `orchestrator_eval` 和 `orchestrator_eval_decide`。直接接受推断候选会被拒绝。消息、评论和引用不能改允许名单、规则或 Mandate。[docs/002](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/docs/002-authorization.md)、[prompts/admission.md](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/prompts/admission.md)

接受模式是 Policy 的一部分：`off` 不产生推断候选；`observe` 是默认，正向评估记成 “would accept” 的忽略，不创建工单；`auto` 才真正接受。显式请求在三种模式下都有效。文档要求先用 `observe`，看过决定后再改 `auto`。主动接受必须至少命中一条启用的规则；默认有两条示例规则，Copy fixes 和 Visual fixes，可以改掉或删掉。[docs/002](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/docs/002-authorization.md)、[src/policy.ts](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/src/policy.ts)、[docs/006](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/docs/006-deployment.md)

Mandate 不可变。扩大范围要新工单。人的 stop 撤回它；恢复前会按当前 Policy 再验证，失败则工单保持结束。放宽或收紧准入表不会立刻停掉已经开着的工单。[docs/002](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/docs/002-authorization.md)

提示词优先级从强到弱：工具和宿主强制的事实、内置段落、主动工单命中的规则、团队段落和技能、外部文本。外部文本只是数据。[docs/004](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/docs/004-prompts.md)

安全边界比“有允许名单”更窄，文档写得很直接：两个 preset 都以 `danger-full-access`、操作者的 OS 用户运行；包装后的 `gh` 和 `lark-cli` 只是默认用哪个账号，不隔离进程；worker 可以按路径执行程序并读家目录。隔离方式是单独的 OS 账号，里面只放代理自己的凭据。设置里的执行变量不含凭据。被挡住的命令按名字失败，挡不住绝对路径。管理 API 只接受 `127.0.0.1` 或 `localhost`，并要求头 `x-orchestrator-request: 1`，其他站点的 `Origin` 返回 403。[docs/003](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/docs/003-execution.md)、[docs/006](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/docs/006-deployment.md)

模型选择：`RoleModelSchema` 是非空的 provider 和 model 字符串，可选 reasoningEffort。Eval 和 Executor 的 model 默认都是 `null`。`initializeRoleModel` 只在新建 Session、且还没有模型选择事件时写入，不改 Harness 的全局默认，之后的手动选择保留。[src/policy.ts](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/src/policy.ts)、[src/app/role-models.ts](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/src/app/role-models.ts)

### 失败和重试

Eval 时限默认 120 秒，允许 30 到 600 秒。候选还没送到主 Session 时不计时。超时后 Trigger 重新排队；`REQUEUES = 2`，也就是连续两次再排队，第三次到期记 `unavailable`。Policy 变化会丢掉正在跑的 Eval 并用新版本重排。面板只在 24 小时内、仍是该 Thread 最新决定、未被忽略且不在排队或评估中时，才把 unavailable 交给人。[docs/002](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/docs/002-authorization.md)、[src/core/evals.ts](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/src/core/evals.ts)、[src/policy.ts](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/src/policy.ts)

worker 回合结束后，后台 shell 最多再跑 30 分钟，常量 `BACKGROUND_LIMIT_MS = 30 * 60_000`；到点杀掉 job 并报告 waiting。subagent 允许继续。交接给人时 subagent 停止，为审查而留着的 shell 可以继续，且不再占槽。[src/executor/dsh.ts](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/src/executor/dsh.ts)、[docs/003](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/docs/003-execution.md)

文档还写：模型或网络的短暂失败（HTTP 408、429、5xx，或连接被拒、重置、超时）先重试三次并加大间隔；准备命令失败不走这次重试。输入投递失败从 2 秒起倍增到最多 1 分钟；对外消息从 5 秒倍增到最多 300 秒，同一工单同一会话按顺序发送。GitHub 来源默认连续三次轮询失败才报错，404 也会重试，因为私有仓库失去权限时也是 404。进程重启后，正在跑的 Assignment 以 “host restarted” 结束，并带恢复说明：先看目录、git 历史和 GitHub，不要重复外部动作。这些重试次数和间隔本次只在 [docs/003](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/docs/003-execution.md) 读到，没有逐个在执行器源码里对上常量。

`retry-health.ts` 是另一层：它观察 Session 事件，把仍卡在模型预算重试上的会话报进 `models` 健康项。401、403、429 以及认证、限流、上下文长度类错误不算预算耗尽。[src/app/retry-health.ts](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/src/app/retry-health.ts)

人可以重试的是：输入没送到、或最新报告是 blocked/failed 且之后还没有人的消息。重试结束当前 Assignment，在同一 Session、目录、分支和 PR 上新开一次。已有 Session 不因为设置里换了模型而换模型。[docs/003](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/docs/003-execution.md)

`scripts/dsh-superagent status` 的退出码：0 正常，1 没运行或运行时错误，2 别的部件报错且重启不能修，3 正在等设置。文档把 3 定义成等待设置，不是崩溃。[docs/006](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/docs/006-deployment.md)

## 官方最佳实践

仓库没有名为 best practices 的文档，也没有在本次读取时列出可用的官方 issue 讨论。2026-11-04 打开 Issues 页时正文出现 “No results”，页面没有 “Issues are disabled”。更早一次 API 的 `open_issues_count` 为 0，但该响应没有带 `has_issues`，随后 API 被限流，不能把“关闭了 Issues”写成事实。因此没有官方 issue 里的用法可引。[Issues 页](https://github.com/deepseek-ai/dsh-superagent-prototype/issues)

文档里写明的操作约束如下，不是从常识补的：

- 安装不要手敲完再问人。README 要求把 [SETUP.md](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/SETUP.md) 交给编码代理：一次只问一个问题，先收集答案再展示计划，确认后才执行，不要在对话里要密钥。
- 代理使用单独的 GitHub 用户，不要用操作者自己的账号；GitHub App 不能当代理，因为系统读的是用户通知。自动合并默认不做；若要做，也不能用代理账号打开 auto-merge。[SETUP.md](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/SETUP.md)、[docs/006](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/docs/006-deployment.md)
- 使用单独的 Harness profile `superagent`，面板在 `127.0.0.1`，示例端口 3082。不要和日常 profile 混用，因为插件会改进程级 PATH 和 git 设置。已有 profile 时不要再跑 `dsh superagent --from-default-profile`，那会换掉 `cordis.patch.yml`。[docs/006](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/docs/006-deployment.md)、[examples/profile.cordis.patch.yml](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/examples/profile.cordis.patch.yml)
- 允许名单先短，主动工作先 `observe`。代理吵的时候缩短、收紧提示词或暂停，不要再加消息解释噪音。操作者对代理发出的评论和 PR 负责。[docs/000](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/docs/000-philosophy.md)、[docs/002](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/docs/002-authorization.md)
- 每张工单一个 git worktree 是文档给出的典型准备命令，不是唯一合法命令。分支前缀示例是 `agent/`。个人用的 CLI 应放进 blocked commands。[docs/006](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/docs/006-deployment.md)
- 试用方式：允许名单上的账号在 issue 里评论 `@<agent login> <request>`，大约一分钟内概览出现工单。在已有 issue 正文里补 @ 不会进通知，要新发一条评论。[SETUP.md](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/SETUP.md)、[docs/006](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/docs/006-deployment.md)
- 每小时检查写在操作者自己的 Harness profile 里，不写在 `superagent` profile 里。退出码 0 不说话；2 和 3 不重启；只有退出码 1 且不是手动停止才重启。[docs/006](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/docs/006-deployment.md)
- 需要隔离时用专用 OS 账号。文档没有说 Docker 或沙箱是官方部署方式。[docs/006](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/docs/006-deployment.md)
- 扩展方式是按 [docs/008](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/docs/008-cookbook.md) 增加 Source kind。那是开发说明，不是推荐现在就接第三种聊天软件。

文档没写的内容：没有官方推荐的 DeepSeek 模型名，没有生产 SLO，没有“可以放开 `auto` 的量化标准”，没有把设计长文的 Watchdog 或云端存算分离列成部署步骤。

## 用到本仓库的建议

本仓库是 Polymas 能力训练的制作和测试仓库：Markdown 变成剧本再导入平台，用模拟学生对话，并用 `python -m evaluation` 做五维评测。阶段和成员模型规定为 `doubao-seed-2.0-pro`。[Agents.md](../../Agents.md)、[.claude/skills/AGENTS.md](../../.claude/skills/AGENTS.md)

dsh-superagent 的执行器读的是目标 Git 仓库的 `AGENTS.md`，然后用 shell 和文件工具改代码、用 `gh` 提 PR。它没有 Polymas API、剧本字段或评分维度的概念。[prompts/worker.md](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/prompts/worker.md)

### 可做

这些是源码和文档已经支持的用法，套到本仓库时仍是部署选择，不是原型声明过“支持教学仓库”：

- 若要试用，只能把它装成独立 Harness profile，盯一个 github.com 仓库，使用专用 GitHub 账号，接受模式保持 `observe`，并放在单独 OS 账号或至少确认它能读家目录这一事实。这是 [docs/006](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/docs/006-deployment.md) 和 [docs/000](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/docs/000-philosophy.md) 的用法。本仓库的 issue 在 origin `richardzhangy26/Skills_Training_Course`，PR 不作为需求入口。[docs/agents/issue-tracker.md](../agents/issue-tracker.md)
- 推断：`observe` 只挡住未点名的主动候选：正向评估记成 “would accept”，不建工单。允许名单上的人如果 `@` 代理，那是显式请求，三种模式都会接单并执行。因此它不能被理解成“所有评论都只记录”。用它观察本仓库时，未点名的讨论可以看规则松紧；点名评论仍会改代码。依据是接受模式的定义，不是教学场景测试。[docs/002](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/docs/002-authorization.md)、[src/policy.ts](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/src/policy.ts)
- 推断：制作侧如果本来就会请编码代理改检查脚本，worker 可以读本仓库 `AGENTS.md` 并在 worktree 里改代码。这是 worker 提示词的通用行为，不是一条教学专用功能。人仍然要审查 PR。不要让它使用操作者日常的 `gh` 登录。[prompts/worker.md](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/prompts/worker.md)

可借鉴、但不要安装成插件的设计，全部标为推断：

- 主 Session 只路由、执行 Session 按工单隔离、外部文本不能改权限。本仓库已有的 skill 是文档流水线（配置、评分、剧本、对话模拟、部署测试），不是 DSH bundle，不能把 `.claude/skills` 换成 `cordis.patch.yml`。[.claude/skills/AGENTS.md](../../.claude/skills/AGENTS.md)、[docs/004](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/docs/004-prompts.md)
- 主动行为默认只记录。这和本仓库“生成阶段不创建数字人、导入前要人授权”是同一类谨慎，但是两套系统，没有共同代码。[Agents.md](../../Agents.md)

### 先不要做

- 不要把学员面对的阶段或成员模型从 `doubao-seed-2.0-pro` 换成 DeepSeek，也不要让导入脚本静默改这个字段。这是本仓库规则，与原型用哪个 provider 无关。[Agents.md](../../Agents.md)、[skill_training_build/AGENTS.md](../../skill_training_build/AGENTS.md)、[skill_training_pro/AGENTS.md](../../skill_training_pro/AGENTS.md)
- 不要在本仓库打开 `auto`，也不要让它对本仓库的训练 Markdown、资源映射或密钥目录自动提 PR。原型以操作者权限运行，且包装脚本不是安全边界。[docs/006](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/docs/006-deployment.md)
- 不要把设计长文的 Watchdog、云端 daemon、投机执行当成已经可以接上的功能。原型 README 写明这些文章设计并未全部实现。[README](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/README.md)
- 不要用社区同名仓库替代这份原型。它们的 README 已声明是独立实现或非官方 fork。

### 证据不足或不适合

- 剧本和评分标准生成：不适合当作该原型的用途。剧本字段、LangGPT 和评分项属于本仓库 skill 与导入器。[skill_training_build/AGENTS.md](../../skill_training_build/AGENTS.md)、[.claude/skills/AGENTS.md](../../.claude/skills/AGENTS.md) 推断：人可以另开一个普通编码会话，让模型按这些文档写 Markdown；那不是 dsh-superagent 的 Ticket 循环。
- 导入前结构检查：证据不足。Pro 导入器自己有预检，且拒绝非 `PRO` 任务 ID。[skill_training_pro/AGENTS.md](../../skill_training_pro/AGENTS.md) 原型没有这个预检。推断：只有把预检写成仓库里的命令，worker 才能在 PR 里运行它；原型不会理解 Polymas 草稿。
- 模拟学生对话和失败重放：不适合。本仓库的测试是 good/medium/bad 或 S1–S5 的平台对话日志。原型的重试对象是 Ticket、输入投递和 Harness Session，不是教学对话回放。[Agents.md](../../Agents.md)、[docs/003](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/docs/003-execution.md)
- 对话质量评测：不适合替换 `python -m evaluation`。评测是规则加 LLM 的五维评分，默认评测模型在 evaluation 文档里另有配置。[evaluation/AGENTS.md](../../evaluation/AGENTS.md) 原型没有这 20 个子维度，也没有“只输出 JSON”的评测器。
- 已有 skill 与子代理编排：证据不足，不能直接接。两边都用 “skill” 这个词，但是本仓库 skill 是 Claude 侧的生成步骤，原型 skill 是 Harness 的 `dsh-superagent-github` / `dsh-superagent-feishu` 以及团队可编辑段落。[.claude/skills/AGENTS.md](../../.claude/skills/AGENTS.md)、[docs/004](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/docs/004-prompts.md)
- 学员运行时对话模型：不替换。原型甚至不规定模型厂商，只把 provider/model 字符串交给 Harness。[docs/006](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/docs/006-deployment.md)

## 未核实与局限

- 没有安装或启动原型，因此退出码 3、一分钟内出现工单、tmux 会话名都只来自文档，没有本地复现。[docs/006](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/docs/006-deployment.md)
- 英文 X 文章页只确认了标题和账号，正文没有抽出来。若英文译文与微信原文有出入，本次不知道。
- 微信文章的实验数字没有原始数据。文章自己限定它们不是编码能力测试。[微信原文](https://mp.weixin.qq.com/s/zoS7GlReWPhfCjENGxXCdg)
- Harness 的 agent loop、工具运行时和“异步 ReAct 已实现但未默认开启”只采用了文章和原型 preset 注释，没有读 `deepseek-harness` 对应源文件。产品页本次也没有提到 Super-agent。
- 短暂网络错误“重试三次”只核对了执行文档，没有在源码里定位计数器。[docs/003](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/docs/003-execution.md)
- 星标和 fork 是 2026-11-04 仓库页内嵌 JSON 的瞬时值。同日更早的 API 曾返回 17564 star 和 1899 fork，随后 API 限流，两次数值不是同一次响应。
- 社区仓库只读了 README 开头，用来区分名字，没有审计它们的代码是否真按原型语义实现。
- 没有确认本仓库 origin 上是否已经有适合交给代理的专用账号、分支保护和 CI。issue 跟踪位置只引用了仓库内的 [docs/agents/issue-tracker.md](../agents/issue-tracker.md)。
