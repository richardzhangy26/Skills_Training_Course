# 专家团三轮迭代交付记录

## 用户规则

验收使用“用户怎么问／专家应该怎么做／最后得到什么”的原文描述。首次基线后最多三轮修复和复测；仅修改授权专家 Agent.md 与 Skill，助教提示词须先协商；检索和课程能力优先复用两份来源 Excel 中已有能力。

## 交付入口

- `iterate_expert_team.py`：发现目标、初始化固定验收、真实测试采集、语义评价入账、修改范围检查、部署回读与接续状态。
- `team_acceptance/START_HERE.md`：交给下一 Agent 的入口及可复制任务描述。
- `team_acceptance/ITERATION_RUNBOOK.md`：每步命令、完成条件与阻断状态。
- `team_acceptance/examples/clinical-reasoning-acceptance.md` 与 criteria JSON：用户原文及五条准则映射；未生成诊疗指南或运行临床专家测试。
- `polymas_v5/docs/atomic-skill-catalog.md/.json`：20 个工作表、793 条来源能力记录、158 个不同名称候选；功能点不等于独立线上 Skill。目录有缺失 NID 和版本，需上线前核对。
- `dist/expert-team-iteration-20260907.zip`：33 个文件，包含可独立启动的 Python 入口、文档和目录，不含凭证、运行状态或真实对话。

## 本次验证

2026-09-07 全量：数据法学项目 tests ＋原子目录定向 tests，显式使用当前 bundled DOCX renderer，**288 passed，31.86s，无跳过**。

新三轮协议定向 27 项覆盖三轮上限、正常通过路径、来源伪造、旧消息复用、未来时间、签名/合同篡改、发布范围越界、重启不重复发送等。原子目录 16 项覆盖 XLSX 原始 XML 解析、合并来源、字段缺失、职责冲突、同源输出和 CLI；来源 1031 非空行、5071 原始单元格独立对账一致。

compileall、git diff --check、ZIP 完整性、解压后独立 CLI 单 JSON 输出、文档相对链接均通过。原子目录独立审查与三轮协议限定复审均无未解决 Critical/Important。

## 实际能力边界

当前脚本把迭代过程做成可由外层 Agent 接续的确定性协议，未内置模型 API 或未经核验的平台发布接口。语义诊断、源码编辑和发布由具有相应工具与授权的外层 Agent 完成。

专家正文可通过真实 PDS 回读比对全文、绑定版本和保护快照。通用 Skill 发布后源码回读尚未实测，Skill 内容变更停在 `SKILL_CONTENT_READBACK_UNVERIFIED`；不能仅凭版本号签发通过。

最近一次用当前 env 做只读发现返回 `AUTH_REQUIRED`，没有执行本轮线上编辑、发布或临床测试。上一阶段教师测试已证明发送/SSE终态/history回读，但不代表本轮自动发布已联调。

修改保留在隔离 worktree 的 `codex/polymas-expert-e2e`，未提交或推送；来源 Excel 及用户已有未跟踪素材未修改。
