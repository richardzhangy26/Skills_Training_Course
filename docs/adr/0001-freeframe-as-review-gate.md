# 采用 FreeFrame 作为审查闸门，不 fork 源码

管线（narration-video-generation）产出的微课成片需要团队人工审查，结论回馈管线。经对 11 个开源候选调研（见 `agent_microcourse/流体力学/output/video_review_tool_research.md`），决定部署 FreeFrame（stable 分支，MIT）作为审查闸门，且**不 fork 其源码**：所有定制走官方 REST API + 外围脚本（推送分段清单、导出转换），关键帧并排对比做成独立的轻量页面而非改其前端。

理由：FreeFrame 是唯一内置按审查人审批状态流的候选，且上传/评论/审批/导出全 REST 化；fork Next.js+FastAPI 双栈的维护债远超收益。代价是接受其固定三值审批枚举、无邮件通知（一期）、MinIO 浏览器直连的内网拓扑约束。
