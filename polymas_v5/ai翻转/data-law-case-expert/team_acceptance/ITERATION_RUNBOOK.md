# 专家团三轮迭代执行说明

此文交给具备文件编辑、终端执行和 Polymas 平台工具的 Agent。用户只需提供目标助教 ID、本地 `.env` 路径与功能验收原文；Agent 负责发现专家团、准备源码和用例，随后按脚本状态推进。源码无法从平台导出、权限不足或发布能力不完整时，返回真实阻断及缺少的材料。

当前已实现：教师侧真实测试与历史回读、固定验收及最多三轮修复状态、文件修改范围核对、专家正文/绑定版本实时回读、来源可追溯的原子 Skill 目录。脚本不内置某家模型 API；外层 Agent 负责语义评价和修改内容。当前还没有经实测的通用 Skill 发布与源码回读适配器，Skill 内容变更会停在 `SKILL_CONTENT_READBACK_UNVERIFIED`，不能宣称已完成全自动 Skill 发布闭环。

## 固定规则

1. 第0轮只建立测试基线，之后最多3轮修复及对应复测；第3轮仍未满足全部标准，结束为 `ITERATION_LIMIT_REACHED`。
2. 用户的“怎么问／怎么做／得到什么”是验收真源。逐条拆成稳定 criterion ID，保存原文引用；任务初始化后不得删减要求、放宽断言或替换用例来取得通过。
3. 修改范围仅限明确列入 scope 的专家 `Agent.md` 与 Skill。AI 助教的 Soul/Leader/Plan 等提示词需要另行与用户协商。项目 `AGENTS.md` 是开发规则，不是线上专家正文，不通过本流程改动。
4. 检索与课程能力先查原子目录，再去 PDS/SkillHub 核对精确名称、NID、版本、角色、依赖及权限。已有能力报错时先查配置、权限和缺失依赖，不因失败就再造一套同职责技能。
5. 自动发送只针对已授权的教师个人助教测试；查询文字不等于底层零写入证明。涉及资源写入、临床患者真实信息或其他副作用的用例，按实际数据和动作另行确定权限边界。
6. 评价者必须引用真实测试报告中的消息 ID 和回答原文。通过需要每条机器断言与每条语义准则均通过；没有足够证据使用 `unverified`，不猜测。

## 0. 发现专家团与准备素材

在脚本包根目录执行：

```bash
python iterate_expert_team.py discover --assistant-id "$ASSISTANT_ID" --env-file "$TEAM_ENV_FILE"
```

命令只读获取已启用专家的名称、NID和绑定版本。输出的 `cases` 为空，表示仍需外层 Agent 根据用户原文设计用例，不能把空用例当作通过。

保留实际需要测试的专家，形成 `team-config.json`。按照 [教师侧验收说明](README.md) 添加只读用例和断言。多轮功能用连续用例覆盖，保持同一案例的上下文；当前协议复用个人助教现有私聊，不声称创建了全新隔离会话。默认测试只能证明本次上下文中的表现，不等同于泛化评测。

把专家及 Skill 源码复制到一个独立源码目录；不要把整个仓库作为源码目录。源文件必须来自实际可编辑的专家/Skill，保留原版本备份和平台标识；没有源码时先获取，不能凭描述重写原 Skill。避免复制 env、缓存或无关教学材料。

查 [原子 Skill 目录](reference/atomic-skill-catalog.md)，使用对应 JSON 条目 ID 写入复用判断。源码目录外保存状态目录。准备 `scope.json`，下列路径按实际导出的文件替换：

```json
{
  "source_root": "/absolute/path/to/isolated-expert-source",
  "resources": [
    {"kind": "expert_agent_md", "expert_nid": "实际专家NID", "path": "expert/Agent.md"},
    {"kind": "expert_skill", "expert_nid": "实际专家NID", "path": "skills/actual-skill"},
    {"kind": "assistant_prompt", "path": "assistant/LeaderAgent.md"}
  ]
}
```

最后一项仅用于检测和暂停协商，不授予修改权限。未声明的文件、路径逃逸、符号链接和计划外文件变化会阻断。

目录来源更新时，用打包附带的 `scripts/build_atomic_skill_catalog.py` 重新解析两份原表并生成新的 Markdown/JSON。已经初始化的任务保留原目录快照，避免同一条目在迭代中改变含义；新任务使用更新后的目录。

```bash
python scripts/build_atomic_skill_catalog.py "$EXPERT_WORKBOOK" "$SKILL_WORKBOOK" --output-dir team_acceptance/reference
```

## 1. 初始化固定验收

把用户原文保存为 `acceptance.md`，语义准则保存为 `criteria.json`。参考 [原文示例](examples/clinical-reasoning-acceptance.md) 与 [准则示例](examples/clinical-reasoning-criteria.json)。示例仅展示格式，当前未配置或测试妇产科专家。

```bash
python iterate_expert_team.py init --session "$ITERATION_DIR" \
  --config team-config.json --acceptance acceptance.md --criteria criteria.json \
  --scope scope.json --catalog team_acceptance/reference/atomic-skill-catalog.json \
  --env-file "$TEAM_ENV_FILE"
```

初始化会读取当前平台专家正文、绑定版本和助教提示词摘要，锁定验收原文、用例、准则、范围与目录快照。每次接手先执行：

```bash
python iterate_expert_team.py status --session "$ITERATION_DIR"
```

读取 `status`、`iteration` 和 `next_action` 后继续。不要重新初始化已有任务或手改状态文件。

## 2. 真实采集与语义评价

```bash
python iterate_expert_team.py run-test --session "$ITERATION_DIR" --env-file "$TEAM_ENV_FILE"
```

该命令使用固定用例和当前已核验版本执行测试，并保存本任务采集记录。只允许记录本任务真实采集的报告；不接受外部文件靠声明 `live-api` 获得通过，也不接受旧回答修改时间后复用。发送不确定时停止，保留回读标识，不重复提交。

正常采集结束会自动进入 `AWAITING_REVIEW`。`record-test --report ...` 仅用于恢复当前轮已签名捕获的同一份报告，不是导入任意外部结果的入口。本地可信边界包括脚本和私有状态目录；不要编辑签名文件或把状态密钥分享给其他服务。

评价 Agent 读取状态中的测试报告，对 `criteria.json` 每一项给出 `pass/fail/unverified`、理由与确切引用。对需要判断顺序的准则，引用多条消息并解释顺序；不要只引用最后一条“我遵循了流程”的自述。对“未执行某动作”不能仅凭回复自称认定，需要行为记录；无证据就写 `unverified`。

`review.json` 格式：

```json
{
  "criteria": [
    {
      "id": "固定criterion ID",
      "verdict": "fail",
      "reason": "描述实际行为如何未满足该条原始要求",
      "evidence": [
        {"case_id": "实际测试用例ID", "message_id": "实际回答标识", "quote": "报告中逐字存在的回答片段"}
      ]
    }
  ]
}
```

```bash
python iterate_expert_team.py record-review --session "$ITERATION_DIR" --review review.json
```

医学等专业正确性由适任评价者根据任务参考材料和权威依据审查，脚本只核查准则覆盖与引用真实性，不把关键词检查当作专业结论。

## 3. 诊断与修改

`NEEDS_REPAIR` 时，先定位提示词、领域 Skill、依赖、知识源或权限问题。修复计划写明具体文件、失败原因、拟改变的行为和已查目录条目。例如：

```json
{
  "files": ["expert/Agent.md"],
  "capability_type": "domain",
  "reason": "根据本轮证据补充专家逐步引导的顺序",
  "reuse_review": {
    "checked_entry_ids": ["目录中的真实entry ID"],
    "decision": "reuse_existing",
    "reason": "保留已有检索能力，本次只调整专家引导方式"
  }
}
```

`capability_type` 为 `domain/retrieval/course`；`decision` 为 `reuse_existing/extend_existing/new_domain_skill`。新领域 Skill 还需 `uncovered_behavior` 说明现有能力覆盖不到的领域逻辑。检索/课程类默认复用或扩展已有能力。目录引用证明查过来源，不代替线上版本与权限核验。

```bash
python iterate_expert_team.py propose-change --session "$ITERATION_DIR" --plan change-plan.json
```

得到 `AWAITING_EDITS` 后，外层 Agent 只编辑所列文件，运行对应脚本测试/Skill结构校验，保留修改前后差异。再执行：

```bash
python iterate_expert_team.py record-changes --session "$ITERATION_DIR"
```

涉及助教提示词会返回 `NEEDS_USER_AGREEMENT`；向用户展示具体差异与原因，等待协商。当前流程不会自动扩大范围。若用户明确同意新范围，保存新授权和旧任务记录后设计对应操作，不直接改状态绕过限制。

## 4. 发布、回读与复测

发布由外层 Agent 通过已获授权且已验证的平台接口或界面执行。发布前展示精确差异并遵循既有平台确认规则。禁止用工具描述、界面按钮名或自然语言“保存成功”代替真实写入与回读证据。

```bash
python iterate_expert_team.py verify-deployment --session "$ITERATION_DIR" --env-file "$TEAM_ENV_FILE"
```

只有本地专家正文与线上正文一致、助教实际绑定新版本、受保护提示词及计划外专家/Skill未变化时，才能进入下一轮 `AWAITING_TEST`。用例和验收保持固定，`runtime-config.json` 仅更新已回读的专家版本。发现计划外变化先停止，不覆盖其他人的修改。

当前 Skill 内容发布后的通用源码回读尚未联调，不能仅凭版本号解锁复测。遇到此限制记录：

```bash
python iterate_expert_team.py block --session "$ITERATION_DIR" --reason SKILL_CONTENT_READBACK_UNVERIFIED
```

`BLOCKED`、`NEEDS_USER_AGREEMENT` 和 `ITERATION_LIMIT_REACHED` 都不是通过；交付原始标准、已完成轮次、实际证据、修改差异及仍需解决的具体条件。当前未实现自动跨进程发布恢复；发送中断先按回读标识对账。

## 交付与可移植性

交付脚本包、原子目录、验收原文/用例、三轮记录和结果摘要。用户将同一包、状态目录与本地 env 路径交给下一 Agent，即可从 `status` 接续。不要把凭证粘贴进提示词、版本库或 ZIP；包不携带模型密钥、用户真实身份或前次对话。

外层 Agent 必须具备编辑文件、运行 Python、访问当前平台及执行所需部署动作的能力。只有 `agentId + env` 无法补足未提供的专业验收标准、不可导出的源码或平台缺失接口；本流程会准确列出这些阻断。
