# Online E2E 线上联调说明

本文记录截至 2026 年 9 月 4 日可直接证明的 Polymas 协议、仍缺失的证据和解除发布门禁的步骤。当前没有执行平台保存、发布、消息发送、上传、知识写入或解绑；synthetic 回归结果不能解释为 live 验证。

## 已验证的只读接口

以下接口已有真实只读响应或部署源码与真实响应的交叉核对，可用于 `dry-run`：

| 操作 | 方法与路径 | 当前用途 |
|---|---|---|
| 专家预览 | `GET /llmOps/agent/v1/preview` | 核对公开专家 NID、类型、名称和来源版本 |
| 专家完整配置 | `GET /llmOps/mdTemplate/v1/agentFullConfig` | 无损快照完整配置、正文、Skill 顺序和扩展字段 |
| 专家知识绑定列表 | `POST /llmOps/agent/knowledge/bind/list` | 读取绑定候选；不等于内容级快照 |
| 当前用户 | `POST /console/v1/get-current-user-detail` | 在内存核对可信主体和 `school_teacher` 角色 |
| 助教列表 | `POST /polymasApp/user/relation/new/agent/list` | 精确定位 `FEpEJws9cS` 中药材助教 |
| 助教与专家关系 | `GET /llmOps/mdTemplate/v1/agentFullConfig` | 核对助教绑定 `x3PalTZaWr` 专家及版本 |

`FEpEJws9cS` 是生产中药材助教 app NID，`x3PalTZaWr` 是数据法学案例专家 NID。它们不是同一标识。`runtime_agent_nid` 仍单独保留，不能用任一现有 NID 猜测填充。

## 已观察但不可用于当前写入的接口

部署源码显示 `POST /llmOps/application/saveAssistant` 固定 `isPublish=1`，因此保存即发布，没有可供本工具使用的独立草稿保存。源码也显示知识绑定和解绑接口。此次没有执行这些写操作，且 `saveAssistant` 的模型转换、basicInfo 白名单、精确成功回执与不确定写入回读仍未完整核验；默认 `SaveProfile` 必须保持 unverified。

## 当前阻断项

| blocker | 原因 | 解除条件 |
|---|---|---|
| `LIVE_TEST_DISABLED` | 目标配置显式 `live_test_enabled=false` | 用户批准测试范围后再改为 true |
| `TEST_ISOLATION_UNAVAILABLE` | `isolated_test_assistant_nid=null` 且 `isolated_test_assistant_name=null`，生产助教不能充当隔离测试助教 | 用户明确指定专用测试助教的 exact NID 与显示名，且 NID 不等于 `FEpEJws9cS`；核对其绑定同一专家版本 |
| `KNOWLEDGE_TARGET_AMBIGUOUS` | 专家有 14 个绑定，本地没有权威 `knowledge_base_nid` | 用户指定唯一知识库并核对 name/type/resourceCount 与内容来源 |
| `STUDENT_TRANSPORT_UNVERIFIED` | 当前终端是 `PC_TEACHER`；roleList 同时出现 student 不代表学生认证上下文 | 获取独立可信学生 transport 并验证权威角色 |
| `SAVE_ENDPOINT_UNVERIFIED` | 保存 payload 转换与写后回读未实证 | 在专用测试专家采集一次完整请求和回读 |
| `SESSION_ENDPOINT_UNVERIFIED` | 没有独立新会话 API；清空记忆只是分隔线 | 证明真正隔离 conversation/session 的创建和回读协议 |
| `UPLOAD_ENDPOINT_UNVERIFIED` | 上传 payload、文件字段和结构化回执未知 | 采集专用测试场景的精确上传契约 |
| `SEND_ENDPOINT_UNVERIFIED` | 发送 payload、SSE 业务终态和历史回读未知 | 证明发送终态、message/plan/trace ID 和历史回读 |
| `TEACHER_RESTORE_UNVERIFIED` | confirm/resume、HTML/知识同步、按 ID 回读与清理协议未知 | 证明每个结构化回执及 cleanup 回读 |
| `KNOWLEDGE_CONTENT_SNAPSHOT_UNVERIFIED` | bind/list 只给元数据，不提供全量内容恢复 | 证明内容级 snapshot、restore 和不可检索验证 |

## 如何补齐协议证据

1. 先由用户明确批准专用测试助教、专用知识库和测试专家；不得操作生产中药材助教或自动挑选 14 个绑定中的任一知识库。
2. 使用 CDP bootstrap 时，每次只观察一个用户明确执行的动作。记录脱敏后的 method、path、请求字段、文件字段、响应字段、SSE 终止条件及写后回读；Authorization、Cookie、userNid 和个人会话信息不落盘。
3. 为每个新观察先增加 synthetic/fixture 协议测试，再把对应 endpoint profile 标记 verified。不能凭 URL 命名、旧脚本或前端按钮文字猜 payload。
4. 证明知识内容全量 snapshot 与 restore、临时案例按 ID 清理以及清理后不可检索。同步回执必须返回本 run 写入后的 knowledge version+digest；恢复前和 backend 内再次 CAS，任一不匹配都保留外部版本并报告 `knowledge_not_restored`。
5. 证明 PDS 发布后的专家版本已被专用测试助教绑定；版本不一致只报告差异，不修改无关专家关系。
6. 重跑 live `dry-run`。只有所有 blocker 消失且快照/差异仍匹配时才可获得一次性令牌；再由用户明确批准同一 `run_id` 的 `apply`。

## 状态解释

- `PASSED`：仅当指定 environment 的完整计划、结构化回执、回读与清理全部通过。
- `BLOCKED`：尚未写入，或 dry-run 正在等待确认。当前 live 目标属于此状态。
- `ROLLED_BACK`：发布后测试失败，且本 run 的案例、知识和配置均已恢复并回读。
- `ROLLBACK_FAILED`：检测到外部并发变化或恢复无法核验；停止覆盖并列出残留状态。

报告中的 `environment` 必须是 `synthetic` 或 `live`。只有 live 报告能证明真实平台行为；本任务没有产生 live 全链路通过报告。
