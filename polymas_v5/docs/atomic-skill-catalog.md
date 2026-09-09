# Polymas 原子 Skill 复用目录

本目录由 atomic-skill-catalog.json 渲染；JSON 是权威数据。表格记录不等同于当前线上可用。

先查目录中的检索类、课程读写类及既有功能点，再核对 PDS/SkillHub 的精确名称、NID、版本与角色权限。已有技能临时失败不能作为新建同职责技能的理由。

一条记录对应一条来源表格行；功能点并不等于独立可挂载 Skill。同一行可能列出多个 Skill。空白 NID/版本保持 null，候选占位名不当作真实技能；跨行仅承接 Excel 显式合并单元格。原始日期序号、状态和错别字保持原样。

关键词分类与职责差异是选型提示，属于推断；并不授予读写权限。线上状态、提测状态与测试结论均为原表历史快照。专家配置、问题、日志等非能力行保留在来源上下文，不计入能力条目。

## 来源覆盖

| 文件 | 工作表 | 能力记录 | 上下文记录 | 非空行 |
| --- | --- | ---: | ---: | ---: |
| 技能  - 专家整理.xlsx | 技能(学生测) | 19 | 6 | 25 |
| 技能  - 专家整理.xlsx | 技能(教师测) | 29 | 2 | 31 |
| 技能  - 专家整理.xlsx | 技能(公共) | 2 | 1 | 3 |
| 技能  - 专家整理.xlsx | 技能 | 176 | 1 | 177 |
| 技能  - 专家整理.xlsx | 专家 | 40 | 10 | 50 |
| 技能  - 专家整理.xlsx | 专家推荐列表 | 0 | 15 | 15 |
| 技能  - 专家整理.xlsx | 技能推荐列表 | 31 | 1 | 32 |
| 技能  - 专家整理.xlsx | 应用广场数据整理 | 62 | 15 | 77 |
| 技能  - 专家整理.xlsx | 技能2 | 45 | 1 | 46 |
| 技能  - 专家整理.xlsx | 技能推荐列表2 | 12 | 1 | 13 |
| 技能  - 专家整理.xlsx | 业务-专家 | 61 | 20 | 81 |
| 技能  - 专家整理.xlsx | 模版推荐 | 21 | 12 | 33 |
| 技能一览表.xlsx | 技能一览 | 28 | 16 | 44 |
| 技能一览表.xlsx | 推广问题修复 | 0 | 12 | 12 |
| 技能一览表.xlsx | V5技能 | 33 | 1 | 34 |
| 技能一览表.xlsx | V5技能列表 | 28 | 27 | 55 |
| 技能一览表.xlsx | Agent与Skill列表 | 92 | 1 | 93 |
| 技能一览表.xlsx | 生产智能体-技能映射 | 23 | 1 | 24 |
| 技能一览表.xlsx | SKILL开发方向划分 | 91 | 40 | 131 |
| 技能一览表.xlsx | SKILL开发日报 | 0 | 55 | 55 |

共 793 条来源能力记录，158 个按原文提取的不同技能名称。名称数包含历史独立功能名与推荐模板候选，不等于线上 Skill 数量。

## 检索类优先复用索引

按名称合并展示；引用指向原始记录，挂载前仍需核对各功能点、来源差异和权限。

| 名称 | 代表功能 / 描述 | 写入候选（推断） | 来源条目 |
| --- | --- | --- | --- |
| DeepRag | 见原表 | 未从文本识别 | [entry-28f389935077437f6a60](#entry-28f389935077437f6a60) |
| adaptive-empathy | 研究生自适应共情响应子技能。处理所有非事实查询、非危机类的用户输入，通过情绪强度评估和求助明确度判断，动态选择深度倾听、共情+轻引导、靶向疏导三种响应模式。支持4维压力模型（科研焦虑/人际困扰/发展迷茫/毕业恐慌）识别与标签输出。适用于研究生情绪倾诉、科研压力、导生关系困扰、毕业焦虑等场景。 | 未从文本识别 | [entry-ec75e36238ea8b812c87](#entry-ec75e36238ea8b812c87) |
| anysearch-skill | 见原表 | 未从文本识别 | [entry-bad24347f333b177ff92](#entry-bad24347f333b177ff92) |
| counseling-guide | 心理中心指引子技能。处理用户关于预约方式、咨询地点、咨询师信息、咨询流程、开放时间、费用等事实性问题。通过RAG检索知识库结构化数据，返回信息卡片，标注信息时效性。适用于查询校心理中心服务信息、预约入口、咨询师排班等场景。 | 未从文本识别 | [entry-d6852b78f32472ba90ad](#entry-d6852b78f32472ba90ad) |
| creation_router | 创作分发 | 未从文本识别 | [entry-4bea4df5b0879cc35a6f](#entry-4bea4df5b0879cc35a6f) |
| creator_tool | 创作基础工具包 | 未从文本识别 | [entry-30381f9733da27122fe8](#entry-30381f9733da27122fe8) |
| deep-search | deep/联网/检索 | 未从文本识别 | [entry-1e77dbb876cee6dbbffb](#entry-1e77dbb876cee6dbbffb)、[entry-cb1ff64eabad55f98c81](#entry-cb1ff64eabad55f98c81) |
| external-knowledge-search | deep/联网/wiki检索 | 未从文本识别 | [entry-b8658e2a3dd473f51019](#entry-b8658e2a3dd473f51019)、[entry-1603ba0e239b72099cdc](#entry-1603ba0e239b72099cdc)、[entry-28dbe1452b6556df1f6d](#entry-28dbe1452b6556df1f6d) |
| literature-review | 系统文献检索、证据综合与研究空白识别 | 未从文本识别 | [entry-93ae63dcf46af427433f](#entry-93ae63dcf46af427433f) |
| meeting-skill | meeting | 有 | [entry-aa132a749470a97dcc3b](#entry-aa132a749470a97dcc3b)、[entry-5fafffd2fe12e7fca657](#entry-5fafffd2fe12e7fca657) |
| openalex-database | 学术论文、作者、机构、主题与引用关系检索 | 未从文本识别 | [entry-a4b373d48eebef9ba225](#entry-a4b373d48eebef9ba225) |
| perplexity-search | 检索最新竞赛、活动、奖学金、科研机会与公开信息 | 未从文本识别 | [entry-203ff94c5a881b504172](#entry-203ff94c5a881b504172) |
| planning-with-files | 将复杂学习或研究任务拆成计划、发现与进度记录 | 未从文本识别 | [entry-c21805b2b9906e5824b8](#entry-c21805b2b9906e5824b8) |
| polymas-capability-search-install | 能力广场搜索/安装能力 | 有 | [entry-b3549915d233ed6f6a49](#entry-b3549915d233ed6f6a49) |
| polymas-course-list-skills | 查询课程列表信息，包括当前学期课程、归档课程和共享课列表，共享课仅返回state==3的课程 | 未从文本识别 | [entry-e74272f5b613edde7c66](#entry-e74272f5b613edde7c66) |
| polymas-course-obe-skills | course_obe | 未从文本识别 | [entry-d82f416b8359bc0e4e10](#entry-d82f416b8359bc0e4e10)、[entry-5d140bbd72c4af643731](#entry-5d140bbd72c4af643731) |
| polymas-course-overview-skills | course_overview | 未从文本识别 | [entry-1d1a3c8a1223dc5415f1](#entry-1d1a3c8a1223dc5415f1)、[entry-e90a4e798e2230e4e5df](#entry-e90a4e798e2230e4e5df)、[entry-9c9b7d783e3d68db8610](#entry-9c9b7d783e3d68db8610) |
| polymas-get-student-course-homework | homework_query | 有 | [entry-2d273457ae6cd3fea8a3](#entry-2d273457ae6cd3fea8a3)、[entry-62c0ed2ff4ec34771eb6](#entry-62c0ed2ff4ec34771eb6)、[entry-447e243f6d05a82c7efe](#entry-447e243f6d05a82c7efe)（共 7 条，完整记录见下文） |
| polymas-online-search | 联网搜索 | 未从文本识别 | [entry-1ecf6761f76eb78a0593](#entry-1ecf6761f76eb78a0593) |
| polymas-query-teaching-unit | query_teaching_unit | 未从文本识别 | [entry-5dfbe45583f61c71cdf5](#entry-5dfbe45583f61c71cdf5)、[entry-d57900b6d24674b26614](#entry-d57900b6d24674b26614)、[entry-ab5a9bafb488dda05e13](#entry-ab5a9bafb488dda05e13)（共 6 条，完整记录见下文） |
| polymas-skill-online-search-install | 联网搜索/安装SKILL | 有 | [entry-d6cc6458807d8ba6e07b](#entry-d6cc6458807d8ba6e07b) |
| polymas-student-agent-teaching-skill | 智能体教学查询 | 未从文本识别 | [entry-a29eda470e6d365db743](#entry-a29eda470e6d365db743) |
| polymas-student-basic-skills | course_search | 未从文本识别 | [entry-291b9c4c3bf194e37188](#entry-291b9c4c3bf194e37188)、[entry-2eab479050c64de785eb](#entry-2eab479050c64de785eb)、[entry-bb2d1b6aad0aa80717bc](#entry-bb2d1b6aad0aa80717bc)（共 6 条，完整记录见下文） |
| polymas-student-class-search | 学生班级查询 | 未从文本识别 | [entry-7cda31772e815bf813e9](#entry-7cda31772e815bf813e9) |
| polymas-student-classroom-report-skills | 课堂报告查询 | 未从文本识别 | [entry-46d3c7f1c15ca3e10b86](#entry-46d3c7f1c15ca3e10b86) |
| polymas-student-course-search | 学生课程查询 | 未从文本识别 | [entry-3f948f433dd3842beb9d](#entry-3f948f433dd3842beb9d) |
| polymas-student-discussion-skills | 讨论情况查询 | 未从文本识别 | [entry-6d2c98efad60757d062a](#entry-6d2c98efad60757d062a) |
| polymas-student-exam-skills | 考试查询与结果 | 未从文本识别 | [entry-c2b9b3b176d7625e4ef7](#entry-c2b9b3b176d7625e4ef7) |
| polymas-student-homework-search | 学生作业查询 | 未从文本识别 | [entry-e9a5686af70c108c67c2](#entry-e9a5686af70c108c67c2) |
| polymas-student-practice-skills | 训练查询与反馈 | 未从文本识别 | [entry-e7d5c022c5b9eb79cfe5](#entry-e7d5c022c5b9eb79cfe5) |
| polymas-student-score-skills | 本人课程成绩查询 | 未从文本识别 | [entry-7a2fce10d4d32014f5de](#entry-7a2fce10d4d32014f5de) |
| polymas-student-study-resource | 学习资源查询 | 有 | [entry-2c58b383a97b3c4bab38](#entry-2c58b383a97b3c4bab38) |
| polymas-student-teaching-plan | 教学计划查询 | 未从文本识别 | [entry-2b36ccd802a6c36b67ea](#entry-2b36ccd802a6c36b67ea) |
| polymas-student-todo-notification-skills | 待办与通知查询 | 未从文本识别 | [entry-2b5ec8ea5c57059bbd9a](#entry-2b5ec8ea5c57059bbd9a) |
| polymas-teacher-activity-skills | notice_search | 有 | [entry-e7844c4a7ef1c242b930](#entry-e7844c4a7ef1c242b930)、[entry-d01f9fc82ceddc762d28](#entry-d01f9fc82ceddc762d28) |
| polymas-teacher-class-group-skills | group_plan_query | 有 | [entry-bf500ff19b644ba7b2b4](#entry-bf500ff19b644ba7b2b4)、[entry-48fa3f6d141978413d3d](#entry-48fa3f6d141978413d3d)、[entry-429380e074b69d66b445](#entry-429380e074b69d66b445)（共 4 条，完整记录见下文） |
| polymas-teacher-class-search | 教师管理班级查询 | 未从文本识别 | [entry-1a6f619987b2f4c013da](#entry-1a6f619987b2f4c013da) |
| polymas-teacher-class-skills | class_search | 有 | [entry-176e584129d00c432e07](#entry-176e584129d00c432e07)、[entry-f2a27b48a34b0ae5a197](#entry-f2a27b48a34b0ae5a197)、[entry-e29e614ce446eafa1b67](#entry-e29e614ce446eafa1b67)（共 6 条，完整记录见下文） |
| polymas-teacher-class-student-skills | student_query | 有 | [entry-2eb7976dd287f83ff112](#entry-2eb7976dd287f83ff112)、[entry-2a8343b34677fca1c00b](#entry-2a8343b34677fca1c00b)、[entry-923a0b1192574be3e753](#entry-923a0b1192574be3e753)（共 4 条，完整记录见下文） |
| polymas-teacher-classroom-report-skills | core_data_analysis | 未从文本识别 | [entry-189c84a9c97299162388](#entry-189c84a9c97299162388)、[entry-d3c15d09a82b5448a7df](#entry-d3c15d09a82b5448a7df)、[entry-4d92f5c8341f551167d0](#entry-4d92f5c8341f551167d0)（共 6 条，完整记录见下文） |
| polymas-teacher-course-search | 教师课程查询 | 未从文本识别 | [entry-629a84e97afc1cd1b558](#entry-629a84e97afc1cd1b558) |
| polymas-teacher-course-skills | course_search | 有 | [entry-ce23d0bacf246c868138](#entry-ce23d0bacf246c868138)、[entry-7403b63f751c757b83ac](#entry-7403b63f751c757b83ac)、[entry-72d3a6b803e27a71c68c](#entry-72d3a6b803e27a71c68c)（共 4 条，完整记录见下文） |
| polymas-teacher-exam-skills | exam_search | 有 | [entry-f1cd1d60a4a82e9e7657](#entry-f1cd1d60a4a82e9e7657)、[entry-06cab54aaa8cff1796fd](#entry-06cab54aaa8cff1796fd)、[entry-dce90b0424ed4e6ea404](#entry-dce90b0424ed4e6ea404)（共 7 条，完整记录见下文） |
| polymas-teacher-homework-chat-query | 教师查询/分析作业下互动交流内容 | 未从文本识别 | [entry-a4be5a7b9ca61fb2fbe8](#entry-a4be5a7b9ca61fb2fbe8) |
| polymas-teacher-homework-detail-skills | 1. 查询作业学情分析情况<br>2.查询作业详情<br>3.获取考试学情分析<br>4.获取某次考试详情信息<br>5.获取课程下作业及考试列表 | 未从文本识别 | [entry-effbcffcdccae08f5253](#entry-effbcffcdccae08f5253) |
| polymas-teacher-homework-search | 教师作业查询 | 未从文本识别 | [entry-961a6cde40d971f2837d](#entry-961a6cde40d971f2837d) |
| polymas-teacher-homework-skills | homework_search | 有 | [entry-f0638be9079d85c517c6](#entry-f0638be9079d85c517c6)、[entry-ae6879721d3c8ee58983](#entry-ae6879721d3c8ee58983)、[entry-7308380659854dc9b39e](#entry-7308380659854dc9b39e)（共 14 条，完整记录见下文） |
| polymas-teacher-knowledge-graph | knowledge_graph | 未从文本识别 | [entry-47ca9f18666ade3cbae1](#entry-47ca9f18666ade3cbae1)、[entry-07a031f2cb8aff1a3219](#entry-07a031f2cb8aff1a3219)、[entry-f0b52d37bc2fdba5e856](#entry-f0b52d37bc2fdba5e856) |
| polymas-teacher-knowledge-search | 教师搜索知识库 | 未从文本识别 | [entry-f6a9e1df46bf01feda49](#entry-f6a9e1df46bf01feda49) |
| polymas-teacher-questionbank-skills | 查询教师的题库资源与题目信息，包括课程题库和个人题库分类、题目详情（题干、题型、选项、答案）等数据 | 有 | [entry-328901ad8b318be1ae67](#entry-328901ad8b318be1ae67)、[entry-63cb98651f01c7852b02](#entry-63cb98651f01c7852b02)、[entry-1343af9310575fe6b603](#entry-1343af9310575fe6b603)（共 5 条，完整记录见下文） |
| polymas-teacher-questions-query | question_search | 未从文本识别 | [entry-bcea28594dfc2a45589f](#entry-bcea28594dfc2a45589f)、[entry-f720324a512b1f10f24c](#entry-f720324a512b1f10f24c)、[entry-ec15f22cf47dcd0abdf6](#entry-ec15f22cf47dcd0abdf6)（共 4 条，完整记录见下文） |
| polymas-teacher-resource-file-search | 教师搜索资源库文件 | 有 | [entry-4cb249404d18846cdfd1](#entry-4cb249404d18846cdfd1) |
| polymas-teacher-resource-skills | knowledge_search | 有 | [entry-29049897aa6d25de116d](#entry-29049897aa6d25de116d)、[entry-7e94c7090002a395a0da](#entry-7e94c7090002a395a0da)、[entry-84cdc61c50a5c915c206](#entry-84cdc61c50a5c915c206)（共 11 条，完整记录见下文） |
| polymas-teacher-score-skills | score_grade_query | 有 | [entry-9f7966ff74921ebccf12](#entry-9f7966ff74921ebccf12)、[entry-f877074a695241719b2b](#entry-f877074a695241719b2b)、[entry-7500281ae97b69f77785](#entry-7500281ae97b69f77785)（共 13 条，完整记录见下文） |
| polymas-teacher-teaching-observation-skills | learning_progress | 未从文本识别 | [entry-226e511f0cade0f0b4a8](#entry-226e511f0cade0f0b4a8)、[entry-4116439b6730fc4d9738](#entry-4116439b6730fc4d9738)、[entry-3fde8e6588e3345ec83a](#entry-3fde8e6588e3345ec83a)（共 15 条，完整记录见下文） |
| polymas-teacher-teaching-plan | teaching_plan_query | 未从文本识别 | [entry-fa67f202946a1b226ca7](#entry-fa67f202946a1b226ca7)、[entry-4d5dd3b1fd7165880575](#entry-4d5dd3b1fd7165880575) |
| polymas-teacher-work-calendar | teaching_schedule_query | 未从文本识别 | [entry-a81099ab3d8a8b29cb7b](#entry-a81099ab3d8a8b29cb7b)、[entry-9e1b91cbe6b67df05741](#entry-9e1b91cbe6b67df05741)、[entry-828520b42dc96c5ee0b8](#entry-828520b42dc96c5ee0b8)（共 4 条，完整记录见下文） |
| polymas-teaching-unit-query | 教学单元查询 | 未从文本识别 | [entry-72e4a15b641984d06b9b](#entry-72e4a15b641984d06b9b) |
| polymas-tool-skills | online_search | 有 | [entry-5708fa4debd3e5454042](#entry-5708fa4debd3e5454042)、[entry-ccd09c00a7ab2f8d8c1e](#entry-ccd09c00a7ab2f8d8c1e)、[entry-04fb1b0ff74ff392a4df](#entry-04fb1b0ff74ff392a4df)（共 8 条，完整记录见下文） |
| polymas-user-detail-query | 用户详情查询 | 未从文本识别 | [entry-5701713791fe21c6b269](#entry-5701713791fe21c6b269) |
| research-assistant | 科研学术助手，集成科研资讯追踪、文献深度解析、选题辅助、论文写作支持、学术规范与诚信五大模块。当用户涉及论文搜索/推荐、文献阅读/解析、选题建议/评估、论文润色/参考文献检查、学术规范/AI使用边界等科研场景时使用此Skill。通过两级意图识别自动路由到对应模块 | 未从文本识别 | [entry-da1dc3e0e7938aeab9cd](#entry-da1dc3e0e7938aeab9cd) |
| research-lookup | 查询最新论文、研究发现、技术资料与统计信息 | 未从文本识别 | [entry-39edb9d43822b66b5b8b](#entry-39edb9d43822b66b5b8b) |
| resource-understanding | 结构化+文件理解 | 未从文本识别 | [entry-8897c08fd44d8b71c2dd](#entry-8897c08fd44d8b71c2dd) |
| schedule-meeting | 会议日程管理 | 有 | [entry-f1b9f3e95c6cce589082](#entry-f1b9f3e95c6cce589082)、[entry-14ef7da87b85332c3036](#entry-14ef7da87b85332c3036)、[entry-29c0c39e42420695b844](#entry-29c0c39e42420695b844)（共 4 条，完整记录见下文） |
| scientific-brainstorming | 研究选题、跨学科连接与研究空白构思 | 未从文本识别 | [entry-a9021dc5f2ded172a883](#entry-a9021dc5f2ded172a883) |
| scientific-critical-thinking | 研究方法、统计有效性与证据质量评估 | 未从文本识别 | [entry-89a662b5f9e54b8cb26c](#entry-89a662b5f9e54b8cb26c) |
| tcm_creative_design | story_search | 未从文本识别 | [entry-a6cce461553087dc1269](#entry-a6cce461553087dc1269)、[entry-a8303af697d8139d14d4](#entry-a8303af697d8139d14d4)、[entry-58549c2ed3373d9cc7fc](#entry-58549c2ed3373d9cc7fc) |
## 课程读写类优先复用索引

按名称合并展示；引用指向原始记录，挂载前仍需核对各功能点、来源差异和权限。

| 名称 | 代表功能 / 描述 | 写入候选（推断） | 来源条目 |
| --- | --- | --- | --- |
| aigc-teaching-material | 教学AIGC生成 | 未从文本识别 | [entry-329699efebd43720932f](#entry-329699efebd43720932f)、[entry-721972c5c3de8edac21b](#entry-721972c5c3de8edac21b)、[entry-dbb1e66cd2f8fb5bd346](#entry-dbb1e66cd2f8fb5bd346)（共 4 条，完整记录见下文） |
| courseware | 见原表 | 未从文本识别 | [entry-613d2714f26278896fb3](#entry-613d2714f26278896fb3) |
| digital_lesson_html | 数字课堂 | 未从文本识别 | [entry-28b91bd8ac559e5f5cf2](#entry-28b91bd8ac559e5f5cf2) |
| job_resume_match | 见原表 | 未从文本识别 | [entry-583713ce4c7af2f1ecf0](#entry-583713ce4c7af2f1ecf0) |
| lesson-prep | §3 #50 <br>1.是否和课堂设计相关？<br>课堂设计用于把互动测验编排进课堂流程。<br>课堂设计编排能力暂未开发-需求还未评审<br>2.备课流程已梳理-原子化流程与算法协作<br>生成教案-生成课件-生成的案例<br>添加资源<br>生成自定义投票-生成头脑风暴-生成随堂测验<br><br> | 未从文本识别 | [entry-3cb728719d19289a54ec](#entry-3cb728719d19289a54ec)、[entry-3994647697addb203b3e](#entry-3994647697addb203b3e) |
| lesson_plan | 见原表 | 未从文本识别 | [entry-42ce99d8d1a3e6660ca7](#entry-42ce99d8d1a3e6660ca7) |
| polymas-course-comprehensive-skills | 教师按课程、班级查看指定学生的学情分析报告，包括作业完成情况、成绩趋势、学习活跃度等数据 | 未从文本识别 | [entry-334c5eef14c662b784c4](#entry-334c5eef14c662b784c4) |
| polymas-course-list-skills | 查询课程列表信息，包括当前学期课程、归档课程和共享课列表，共享课仅返回state==3的课程 | 未从文本识别 | [entry-93925541ad541303a7bd](#entry-93925541ad541303a7bd)、[entry-e74272f5b613edde7c66](#entry-e74272f5b613edde7c66) |
| polymas-course-obe-skills | course_obe | 有 | [entry-d82f416b8359bc0e4e10](#entry-d82f416b8359bc0e4e10)、[entry-da0f5a3c58d24c22469b](#entry-da0f5a3c58d24c22469b)、[entry-bedb2d1e4313945bdf81](#entry-bedb2d1e4313945bdf81)（共 8 条，完整记录见下文） |
| polymas-course-overview-skills | course_overview | 未从文本识别 | [entry-1d1a3c8a1223dc5415f1](#entry-1d1a3c8a1223dc5415f1)、[entry-ff84628095063131da17](#entry-ff84628095063131da17)、[entry-e90a4e798e2230e4e5df](#entry-e90a4e798e2230e4e5df)（共 5 条，完整记录见下文） |
| polymas-get-student-course-homework | homework_query | 有 | [entry-2d273457ae6cd3fea8a3](#entry-2d273457ae6cd3fea8a3)、[entry-da9fd0fb71d9a18575f5](#entry-da9fd0fb71d9a18575f5)、[entry-5ed3591cfa646a007931](#entry-5ed3591cfa646a007931)（共 14 条，完整记录见下文） |
| polymas-query-teaching-unit | query_teaching_unit | 未从文本识别 | [entry-5dfbe45583f61c71cdf5](#entry-5dfbe45583f61c71cdf5)、[entry-430c84c7f12d3d2e2274](#entry-430c84c7f12d3d2e2274)、[entry-d57900b6d24674b26614](#entry-d57900b6d24674b26614)（共 7 条，完整记录见下文） |
| polymas-student-agent-teaching-skill | 智能体教学查询 | 未从文本识别 | [entry-a29eda470e6d365db743](#entry-a29eda470e6d365db743) |
| polymas-student-basic-skills | course_search | 未从文本识别 | [entry-291b9c4c3bf194e37188](#entry-291b9c4c3bf194e37188)、[entry-2eab479050c64de785eb](#entry-2eab479050c64de785eb)、[entry-75f18129b549805ee989](#entry-75f18129b549805ee989)（共 10 条，完整记录见下文） |
| polymas-student-class-search | 学生班级查询 | 未从文本识别 | [entry-7cda31772e815bf813e9](#entry-7cda31772e815bf813e9) |
| polymas-student-classroom-report-skills | 课堂报告查询 | 未从文本识别 | [entry-46d3c7f1c15ca3e10b86](#entry-46d3c7f1c15ca3e10b86) |
| polymas-student-course-search | 学生课程查询 | 未从文本识别 | [entry-3f948f433dd3842beb9d](#entry-3f948f433dd3842beb9d) |
| polymas-student-custom-study-skills | 创建学习目标并启动学习 | 有 | [entry-7abef0a7ac0faee9db8c](#entry-7abef0a7ac0faee9db8c) |
| polymas-student-discussion-skills | 讨论情况查询 | 有 | [entry-6d2c98efad60757d062a](#entry-6d2c98efad60757d062a)、[entry-a355d51fad1dda5bd281](#entry-a355d51fad1dda5bd281)、[entry-59a1ee58d7f6e0cd1828](#entry-59a1ee58d7f6e0cd1828) |
| polymas-student-exam-skills | 考试查询与结果 | 未从文本识别 | [entry-c2b9b3b176d7625e4ef7](#entry-c2b9b3b176d7625e4ef7) |
| polymas-student-homework-search | 学生作业查询 | 未从文本识别 | [entry-e9a5686af70c108c67c2](#entry-e9a5686af70c108c67c2) |
| polymas-student-practice-skills | 训练查询与反馈 | 未从文本识别 | [entry-e7d5c022c5b9eb79cfe5](#entry-e7d5c022c5b9eb79cfe5)、[entry-b37aa55337017181e5b6](#entry-b37aa55337017181e5b6)、[entry-955f72f6720675edfd4d](#entry-955f72f6720675edfd4d) |
| polymas-student-score-skills | 本人课程成绩查询 | 未从文本识别 | [entry-7a2fce10d4d32014f5de](#entry-7a2fce10d4d32014f5de) |
| polymas-student-study-resource | 学习资源查询 | 有 | [entry-2c58b383a97b3c4bab38](#entry-2c58b383a97b3c4bab38)、[entry-0c79aa5964ec7eb48d9c](#entry-0c79aa5964ec7eb48d9c) |
| polymas-student-teaching-plan | 教学计划查询 | 未从文本识别 | [entry-2b36ccd802a6c36b67ea](#entry-2b36ccd802a6c36b67ea) |
| polymas-student-todo-notification-skills | 待办与通知查询 | 未从文本识别 | [entry-2b5ec8ea5c57059bbd9a](#entry-2b5ec8ea5c57059bbd9a) |
| polymas-teacher-activity-skills | notice_publish | 有 | [entry-693fdddd0dfd19904a90](#entry-693fdddd0dfd19904a90)、[entry-e7844c4a7ef1c242b930](#entry-e7844c4a7ef1c242b930)、[entry-4d9a16451cfcf6508ce9](#entry-4d9a16451cfcf6508ce9)（共 19 条，完整记录见下文） |
| polymas-teacher-agent-create | agent_create_api | 有 | [entry-90297062033dcc2ab930](#entry-90297062033dcc2ab930)、[entry-65f2a253322044110da1](#entry-65f2a253322044110da1)、[entry-938b6a67492b434419fb](#entry-938b6a67492b434419fb)（共 6 条，完整记录见下文） |
| polymas-teacher-agent-teaching-gen | agent_class_generate | 有 | [entry-27167b3989d720aa6b7b](#entry-27167b3989d720aa6b7b)、[entry-96b506799a28db39a982](#entry-96b506799a28db39a982)、[entry-f2bf57fce37cb3b6e72c](#entry-f2bf57fce37cb3b6e72c)（共 9 条，完整记录见下文） |
| polymas-teacher-analogy-skills | concept-analogy | 未从文本识别 | [entry-fa247d550010faa5d903](#entry-fa247d550010faa5d903)、[entry-4ae85d9069ffb725a0ab](#entry-4ae85d9069ffb725a0ab)、[entry-38b73e2d119a3585e791](#entry-38b73e2d119a3585e791)（共 5 条，完整记录见下文） |
| polymas-teacher-case-skills | case-generation | 未从文本识别 | [entry-ae0ba7955860c90b282d](#entry-ae0ba7955860c90b282d)、[entry-7b32777a58453e6c8900](#entry-7b32777a58453e6c8900)、[entry-26e6bd3d651a9ae89b3a](#entry-26e6bd3d651a9ae89b3a)（共 5 条，完整记录见下文） |
| polymas-teacher-class-group-assistant | class_group_message | 有 | [entry-3123c3c021270d08f2de](#entry-3123c3c021270d08f2de)、[entry-edc6617466eb630b450d](#entry-edc6617466eb630b450d)、[entry-b7f139727a646dda898f](#entry-b7f139727a646dda898f)（共 8 条，完整记录见下文） |
| polymas-teacher-class-group-skills | group_plan_query | 有 | [entry-bf500ff19b644ba7b2b4](#entry-bf500ff19b644ba7b2b4)、[entry-a3816b977fa53a7ab136](#entry-a3816b977fa53a7ab136)、[entry-3b93f344aa3aa78064b9](#entry-3b93f344aa3aa78064b9)（共 10 条，完整记录见下文） |
| polymas-teacher-class-search | 教师管理班级查询 | 未从文本识别 | [entry-1a6f619987b2f4c013da](#entry-1a6f619987b2f4c013da) |
| polymas-teacher-class-skills | class_create | 有 | [entry-f3f919a1d1c3d801b8cb](#entry-f3f919a1d1c3d801b8cb)、[entry-176e584129d00c432e07](#entry-176e584129d00c432e07)、[entry-7a2e9390d8f33deb5546](#entry-7a2e9390d8f33deb5546)（共 14 条，完整记录见下文） |
| polymas-teacher-class-student-skills | student_query | 有 | [entry-2eb7976dd287f83ff112](#entry-2eb7976dd287f83ff112)、[entry-93f6bc547b8299121797](#entry-93f6bc547b8299121797)、[entry-61fd4d4629cbf620e6a9](#entry-61fd4d4629cbf620e6a9)（共 14 条，完整记录见下文） |
| polymas-teacher-classroom-replay-management | 见原表 | 未从文本识别 | [entry-0c56b7ffab1dc0e4e623](#entry-0c56b7ffab1dc0e4e623) |
| polymas-teacher-classroom-report-skills | core_data_analysis | 未从文本识别 | [entry-189c84a9c97299162388](#entry-189c84a9c97299162388)、[entry-d3c15d09a82b5448a7df](#entry-d3c15d09a82b5448a7df)、[entry-4d92f5c8341f551167d0](#entry-4d92f5c8341f551167d0)（共 12 条，完整记录见下文） |
| polymas-teacher-content-creation | 根据教学需求，智能生成教案、复习提纲、课堂讲稿、PPT等备课材料的提示词，并调用内容生成引擎完成创作 | 未从文本识别 | [entry-ebe9170b61c6a142aeaf](#entry-ebe9170b61c6a142aeaf)、[entry-cc40133891e1fb2bf5f2](#entry-cc40133891e1fb2bf5f2)、[entry-815de93694418af77fc5](#entry-815de93694418af77fc5) |
| polymas-teacher-course-search | 教师课程查询 | 未从文本识别 | [entry-629a84e97afc1cd1b558](#entry-629a84e97afc1cd1b558) |
| polymas-teacher-course-skills | course_create | 有 | [entry-a90d516105f5e8eaae57](#entry-a90d516105f5e8eaae57)、[entry-ce23d0bacf246c868138](#entry-ce23d0bacf246c868138)、[entry-87617bbae8233ec1cea0](#entry-87617bbae8233ec1cea0)（共 11 条，完整记录见下文） |
| polymas-teacher-exam-skills | exam_search | 有 | [entry-f1cd1d60a4a82e9e7657](#entry-f1cd1d60a4a82e9e7657)、[entry-dca01e4a86b389fbf882](#entry-dca01e4a86b389fbf882)、[entry-d6e7cc695c9eb3e82280](#entry-d6e7cc695c9eb3e82280)（共 27 条，完整记录见下文） |
| polymas-teacher-file-import-questions | file_import_questions | 有 | [entry-a5c7909392d645004140](#entry-a5c7909392d645004140)、[entry-8386e42f0e8bb1bee868](#entry-8386e42f0e8bb1bee868)、[entry-f01374c3bc091e293f31](#entry-f01374c3bc091e293f31)（共 7 条，完整记录见下文） |
| polymas-teacher-homework-analysis | 教师分析作业完成情况 | 未从文本识别 | [entry-46694fafc48b3af5fabd](#entry-46694fafc48b3af5fabd) |
| polymas-teacher-homework-chat-query | 教师查询/分析作业下互动交流内容 | 未从文本识别 | [entry-a4be5a7b9ca61fb2fbe8](#entry-a4be5a7b9ca61fb2fbe8) |
| polymas-teacher-homework-detail-skills | exam_homework_detail | 有 | [entry-f83e21c59ffc638e6975](#entry-f83e21c59ffc638e6975)、[entry-f57057e3d437d10ac84d](#entry-f57057e3d437d10ac84d)、[entry-9cbb59b4f5add52caeb9](#entry-9cbb59b4f5add52caeb9)（共 16 条，完整记录见下文） |
| polymas-teacher-homework-hit-back | 教师打回作业 | 有 | [entry-bf5177a1cc205f5beabd](#entry-bf5177a1cc205f5beabd) |
| polymas-teacher-homework-search | 教师作业查询 | 未从文本识别 | [entry-961a6cde40d971f2837d](#entry-961a6cde40d971f2837d) |
| polymas-teacher-homework-skills | homework_search | 有 | [entry-f0638be9079d85c517c6](#entry-f0638be9079d85c517c6)、[entry-3b10a9837a33174f6a45](#entry-3b10a9837a33174f6a45)、[entry-651e0464c95a6fde0591](#entry-651e0464c95a6fde0591)（共 41 条，完整记录见下文） |
| polymas-teacher-homework-urge | 教师催交作业 | 有 | [entry-7d429f6a62a82d9c8b9d](#entry-7d429f6a62a82d9c8b9d) |
| polymas-teacher-knowledge-distillation | knowledge_distillation | 有 | [entry-355b16e4fd76481787ac](#entry-355b16e4fd76481787ac)、[entry-ec36229d9713bff5f38b](#entry-ec36229d9713bff5f38b)、[entry-7bd42adfe1e1ae08bfbc](#entry-7bd42adfe1e1ae08bfbc)（共 4 条，完整记录见下文） |
| polymas-teacher-knowledge-graph | knowledge_graph | 未从文本识别 | [entry-47ca9f18666ade3cbae1](#entry-47ca9f18666ade3cbae1)、[entry-800e06251af1cdd3b3b1](#entry-800e06251af1cdd3b3b1)、[entry-07a031f2cb8aff1a3219](#entry-07a031f2cb8aff1a3219)（共 5 条，完整记录见下文） |
| polymas-teacher-knowledge-search | 教师搜索知识库 | 未从文本识别 | [entry-f6a9e1df46bf01feda49](#entry-f6a9e1df46bf01feda49) |
| polymas-teacher-learning-analytics-skills | student_learning_view | 有 | [entry-eb1bad41db0f578e8138](#entry-eb1bad41db0f578e8138)、[entry-8bc4582c2394fd92cbbf](#entry-8bc4582c2394fd92cbbf)、[entry-9ccd79ab10959f00756f](#entry-9ccd79ab10959f00756f)（共 6 条，完整记录见下文） |
| polymas-teacher-lession-analysis | lession_analysis | 未从文本识别 | [entry-85edeca98d49dad781a5](#entry-85edeca98d49dad781a5)、[entry-1ea9c56aeec5254f8ce0](#entry-1ea9c56aeec5254f8ce0)、[entry-02906e57e8c7723cf11b](#entry-02906e57e8c7723cf11b)（共 10 条，完整记录见下文） |
| polymas-teacher-lesson-design | 根据教师提供的课程主题与教学要求，生成结构化课堂教学流程方案，支持多轮迭代与细化 | 未从文本识别 | [entry-e889a1e7035ccfbc58e1](#entry-e889a1e7035ccfbc58e1)、[entry-b96442a90e0cb7b42512](#entry-b96442a90e0cb7b42512)、[entry-54db0b301994266051f4](#entry-54db0b301994266051f4) |
| polymas-teacher-preparation-management | preparation_management | 有 | [entry-7c249410d361a2dcbc68](#entry-7c249410d361a2dcbc68)、[entry-8e2dcbfbb6c575ec4738](#entry-8e2dcbfbb6c575ec4738)、[entry-e9ccaa7e84fd320ce8e4](#entry-e9ccaa7e84fd320ce8e4) |
| polymas-teacher-problem-skills | problem_generate | 未从文本识别 | [entry-57ed3a3a4667fab8f357](#entry-57ed3a3a4667fab8f357)、[entry-519cbd617c2f7d926bf6](#entry-519cbd617c2f7d926bf6)、[entry-6354ce6f82202ecfbb31](#entry-6354ce6f82202ecfbb31)（共 8 条，完整记录见下文） |
| polymas-teacher-questionbank-skills | 查询教师的题库资源与题目信息，包括课程题库和个人题库分类、题目详情（题干、题型、选项、答案）等数据 | 有 | [entry-cada0c57279b1790104a](#entry-cada0c57279b1790104a)、[entry-328901ad8b318be1ae67](#entry-328901ad8b318be1ae67)、[entry-63cb98651f01c7852b02](#entry-63cb98651f01c7852b02)（共 10 条，完整记录见下文） |
| polymas-teacher-questions-query | question_search | 有 | [entry-bcea28594dfc2a45589f](#entry-bcea28594dfc2a45589f)、[entry-e6f9f9b1d491876f0e38](#entry-e6f9f9b1d491876f0e38)、[entry-f720324a512b1f10f24c](#entry-f720324a512b1f10f24c)（共 8 条，完整记录见下文） |
| polymas-teacher-resource-file-search | 教师搜索资源库文件 | 有 | [entry-4cb249404d18846cdfd1](#entry-4cb249404d18846cdfd1) |
| polymas-teacher-resource-skills | knowledge_search | 有 | [entry-29049897aa6d25de116d](#entry-29049897aa6d25de116d)、[entry-7e94c7090002a395a0da](#entry-7e94c7090002a395a0da)、[entry-84cdc61c50a5c915c206](#entry-84cdc61c50a5c915c206)（共 21 条，完整记录见下文） |
| polymas-teacher-save-to-skills | 文件<br>保存至工作空间<br>保存至xxx资源库<br>保存至备课<br> | 未从文本识别 | [entry-01a47265f27e5dfc7cac](#entry-01a47265f27e5dfc7cac) |
| polymas-teacher-score-skills | score_grade_query | 有 | [entry-9f7966ff74921ebccf12](#entry-9f7966ff74921ebccf12)、[entry-84039e8202917df8dead](#entry-84039e8202917df8dead)、[entry-f877074a695241719b2b](#entry-f877074a695241719b2b)（共 22 条，完整记录见下文） |
| polymas-teacher-study-resource | 见原表 | 未从文本识别 | [entry-cedf52e57fa825e49f8d](#entry-cedf52e57fa825e49f8d) |
| polymas-teacher-teaching-observation-skills | learning_progress | 未从文本识别 | [entry-226e511f0cade0f0b4a8](#entry-226e511f0cade0f0b4a8)、[entry-4116439b6730fc4d9738](#entry-4116439b6730fc4d9738)、[entry-3fde8e6588e3345ec83a](#entry-3fde8e6588e3345ec83a)（共 21 条，完整记录见下文） |
| polymas-teacher-teaching-plan | teaching_plan_query | 未从文本识别 | [entry-fa67f202946a1b226ca7](#entry-fa67f202946a1b226ca7)、[entry-b0d6920c39d613bed65d](#entry-b0d6920c39d613bed65d)、[entry-892e2bed131dbbdd35a3](#entry-892e2bed131dbbdd35a3)（共 7 条，完整记录见下文） |
| polymas-teacher-work-calendar | teaching_schedule_query | 未从文本识别 | [entry-a81099ab3d8a8b29cb7b](#entry-a81099ab3d8a8b29cb7b)、[entry-0527f12846fd7ef11f39](#entry-0527f12846fd7ef11f39)、[entry-9e1b91cbe6b67df05741](#entry-9e1b91cbe6b67df05741)（共 6 条，完整记录见下文） |
| polymas-teaching-unit-query | 教学单元查询 | 未从文本识别 | [entry-72e4a15b641984d06b9b](#entry-72e4a15b641984d06b9b) |
| question_generate | 见原表 | 未从文本识别 | [entry-e13c4ffb9234b2d0d993](#entry-e13c4ffb9234b2d0d993) |
| teaching_image | 见原表 | 未从文本识别 | [entry-583713ce4c7af2f1ecf0](#entry-583713ce4c7af2f1ecf0) |
| teaching_video | 见原表 | 未从文本识别 | [entry-e13c4ffb9234b2d0d993](#entry-e13c4ffb9234b2d0d993) |

## 待核对的名称与职责差异

- **polymas-teacher-resource-skills**：scope_conflict_needs_check；待核对。同名记录同时出现只读约束与写入能力描述；可能为版本、功能点或角色差异，须核对平台。
  [entry-29049897aa6d25de116d](#entry-29049897aa6d25de116d)、[entry-7e94c7090002a395a0da](#entry-7e94c7090002a395a0da)、[entry-440a8859566fce64a33b](#entry-440a8859566fce64a33b)、[entry-47d19e1b6ab874837264](#entry-47d19e1b6ab874837264)、[entry-62602ba16460cafbcd81](#entry-62602ba16460cafbcd81)、[entry-84cdc61c50a5c915c206](#entry-84cdc61c50a5c915c206)、[entry-3084c11d63493bbf0289](#entry-3084c11d63493bbf0289)、[entry-4958f95d48f08bbd7ad6](#entry-4958f95d48f08bbd7ad6)、[entry-c11b9ad4118da4364d3d](#entry-c11b9ad4118da4364d3d)、[entry-f788df50ce55c95b9bc9](#entry-f788df50ce55c95b9bc9)
- **polymas-tool-skills**：scope_conflict_needs_check；待核对。同名记录同时出现只读约束与写入能力描述；可能为版本、功能点或角色差异，须核对平台。
  [entry-5708fa4debd3e5454042](#entry-5708fa4debd3e5454042)、[entry-04fb1b0ff74ff392a4df](#entry-04fb1b0ff74ff392a4df)、[entry-00dd1a66aedec0399d81](#entry-00dd1a66aedec0399d81)、[entry-ccd09c00a7ab2f8d8c1e](#entry-ccd09c00a7ab2f8d8c1e)、[entry-c0e744feef6f5b5e95e7](#entry-c0e744feef6f5b5e95e7)、[entry-72a7d2b6a22b21a36237](#entry-72a7d2b6a22b21a36237)、[entry-4b28395248f511f1eaf2](#entry-4b28395248f511f1eaf2)、[entry-7f74fe33fa0154218004](#entry-7f74fe33fa0154218004)

## 全部能力来源记录

<a id="entry-1c51b1f5a89c70bcdf9b"></a>
### entry-1c51b1f5a89c70bcdf9b · 课程待办任务查询

技能  - 专家整理.xlsx / 技能(学生测) / 第 2 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B2 | 场景标签 | 首页/待办（内置） |
| D2 | 技能中文名 | 课程待办任务查询 |
| E2 | 功能点序号 | 1 |
| G2 | 功能点（中文） | 1、查询教学平台课程待办作业考试（包含各类型的作业考试），以及完成进度<br><br>2、筛选和搜索作业考试<br><br>作业/考试类型：自定义作业、选题作业、知识点作业、小组作业、智能辅导作业、自定义考试、选题考试、随机组卷考试 |
| H2 | 描述 | 查询当前学生未完成作业考试 |
| M2 | 使用场景 | 内置 |
| N2 | 未命名列 N | 标准技能 |

<a id="entry-6bedb8877c2ff704c9af"></a>
### entry-6bedb8877c2ff704c9af · 1、进入课中，参与老师发布的多种互动，如签到、投票、头脑风暴、点名、随堂测验、分组讨论、答疑等互动<br>2、查看老师播放的课件、截图等

技能  - 专家整理.xlsx / 技能(学生测) / 第 3 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B3 | 场景标签 | 课堂学习 |
| G3 | 功能点（中文） | 1、进入课中，参与老师发布的多种互动，如签到、投票、头脑风暴、点名、随堂测验、分组讨论、答疑等互动<br>2、查看老师播放的课件、截图等 |
| H3 | 描述 | 学生进入课中可以查看老师发布的互动，参与各种互动，并实时查看自己或他人的互动记录数据 |

<a id="entry-578fb2c3189f44d9048e"></a>
### entry-578fb2c3189f44d9048e · 1、开课推送<br>2、作业截止时间提醒<br>3、开始考试提醒<br>4、考试截止时间提醒<br>5、作业打回提醒

技能  - 专家整理.xlsx / 技能(学生测) / 第 4 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B4 | 场景标签 | 推送 |
| G4 | 功能点（中文） | 1、开课推送<br>2、作业截止时间提醒<br>3、开始考试提醒<br>4、考试截止时间提醒<br>5、作业打回提醒 |
| N4 | 未命名列 N | 实现方式待定 |

<a id="entry-d64a0549250db9587020"></a>
### entry-d64a0549250db9587020 · 课程查询

技能  - 专家整理.xlsx / 技能(学生测) / 第 5 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B5 | 场景标签 | 我的课程（内置） |
| D5 | 技能中文名 | 课程查询 |
| G5 | 功能点（中文） | 1、查询课程（查询我学的课、我管的课（助教），包含各课程类型课程、课程数量、按学期查询、按课程名称查询）<br> |
| H5 | 描述 | 按需查询课程信息、加入课程 |
| M5 | 使用场景 | 内置 |
| N5 | 未命名列 N | 标准技能 |

<a id="entry-40229c962470dc786abb"></a>
### entry-40229c962470dc786abb · 2、加入课程：加入校内课（Ai智课+智能体课）和共享课

技能  - 专家整理.xlsx / 技能(学生测) / 第 6 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| G6 | 功能点（中文） | 2、加入课程：加入校内课（Ai智课+智能体课）和共享课 |
| M6 | 使用场景 | 内置 |
| B（合并继承自 B5；B5:B6） | 原值见锚点 | 我的课程（内置） |

<a id="entry-5bfce7bd4b2e6506df7a"></a>
### entry-5bfce7bd4b2e6506df7a · 学习资源（标准+跳转）<br>1、学习已发布的资源（必学和选学）<br>2、统计总学习进度，已完成和未完成资源<br>3、按老师发布的模式学习（普通模式、闯关模式、复习模式）<br>4、资源是否可下载

技能  - 专家整理.xlsx / 技能(学生测) / 第 7 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B7 | 场景标签 | 课程学习 |
| G7 | 功能点（中文） | 学习资源（标准+跳转）<br>1、学习已发布的资源（必学和选学）<br>2、统计总学习进度，已完成和未完成资源<br>3、按老师发布的模式学习（普通模式、闯关模式、复习模式）<br>4、资源是否可下载 |
| H7 | 描述 | 查询课程中资源的学习情况及进度、必学资源数量、是否可下载 |
| M7 | 使用场景 | 内置 |
| N7 | 未命名列 N | 功能 跳转 |
| O7 | 未命名列 O | 不是推出资源，学习卡片点击卡片跳转到学习资源模块 |

<a id="entry-d2956a9a1c25317b4a0f"></a>
### entry-d2956a9a1c25317b4a0f · 课堂回放<br>1、查询课程中已发布的回放（包含同步课堂回放+屏幕录制回放）

技能  - 专家整理.xlsx / 技能(学生测) / 第 8 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| G8 | 功能点（中文） | 课堂回放<br>1、查询课程中已发布的回放（包含同步课堂回放+屏幕录制回放） |
| H8 | 描述 | 查询课程中老师发布的课堂回放 |
| N8 | 未命名列 N | 合并 |
| O8 | 未命名列 O | 资源检索中 |
| B（合并继承自 B7；B7:B10） | 原值见锚点 | 课程学习 |

<a id="entry-46ea10b1010d9199fd5a"></a>
### entry-46ea10b1010d9199fd5a · 知识体系<br>1、查询课程知识图谱、问题图谱、能力图谱（包含知识点、课程问题、主能力与子能力）

技能  - 专家整理.xlsx / 技能(学生测) / 第 9 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| G9 | 功能点（中文） | 知识体系<br>1、查询课程知识图谱、问题图谱、能力图谱（包含知识点、课程问题、主能力与子能力） |
| H9 | 描述 | 查看课程知识图谱、问题图谱、能力图谱及对应知识点 |
| M9 | 使用场景 | 内置 |
| N9 | 未命名列 N | 标准 |
| B（合并继承自 B7；B7:B10） | 原值见锚点 | 课程学习 |

<a id="entry-a136a53c166dfe0f0571"></a>
### entry-a136a53c166dfe0f0571 · 训练题库<br>1、查询课程下已开放的训练题目<br>2、支持按模式训练题目，随机练习、精准练习、模拟考试<br>3、支持整合错题、收藏题目<br>4、统计题目完成率

技能  - 专家整理.xlsx / 技能(学生测) / 第 10 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| G10 | 功能点（中文） | 训练题库<br>1、查询课程下已开放的训练题目<br>2、支持按模式训练题目，随机练习、精准练习、模拟考试<br>3、支持整合错题、收藏题目<br>4、统计题目完成率 |
| H10 | 描述 | 课程题目刷题练习，支持随机练习、精准练习、模拟考试，查询错题 |
| O10 | 未命名列 O | 去练习 + 自动出题 做备考Agent |
| B（合并继承自 B7；B7:B10） | 原值见锚点 | 课程学习 |

<a id="entry-c4bacc6666372e0ffff8"></a>
### entry-c4bacc6666372e0ffff8 · 作业<br>1、查询作业（包含各种作业类型）按作业名称、作业状态查询<br>2、查询作业成绩、打回、重做等信息

技能  - 专家整理.xlsx / 技能(学生测) / 第 11 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B11 | 场景标签 | 课程任务 |
| G11 | 功能点（中文） | 作业<br>1、查询作业（包含各种作业类型）按作业名称、作业状态查询<br>2、查询作业成绩、打回、重做等信息 |
| H11 | 描述 | 按作业类型、作业名称、状态等查询作业 |
| M11 | 使用场景 | 内置 |
| N11 | 未命名列 N | 标准 |

<a id="entry-af498f53a04cadfd03e5"></a>
### entry-af498f53a04cadfd03e5 · 提交作业

技能  - 专家整理.xlsx / 技能(学生测) / 第 12 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| G12 | 功能点（中文） | 提交作业 |
| M12 | 使用场景 | 内置 |
| N12 | 未命名列 N | 标准 |
| B（合并继承自 B11；B11:B14） | 原值见锚点 | 课程任务 |

<a id="entry-e4afd25dfa2c04398811"></a>
### entry-e4afd25dfa2c04398811 · 考试<br>1、查询考试（包含各种考试类型）按考试名称、考试状态查询<br>2、查询考试成绩、补考等信息

技能  - 专家整理.xlsx / 技能(学生测) / 第 13 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| G13 | 功能点（中文） | 考试<br>1、查询考试（包含各种考试类型）按考试名称、考试状态查询<br>2、查询考试成绩、补考等信息 |
| H13 | 描述 | 按考试名称、状态等查询考试及补考 |
| N13 | 未命名列 N | 功能 跳转 |
| B（合并继承自 B11；B11:B14） | 原值见锚点 | 课程任务 |

<a id="entry-bb2f1a87033bc4930234"></a>
### entry-bb2f1a87033bc4930234 · 讨论<br>1、查询已发布的话题讨论（本课程老师和学生）支持筛选状态、更新时间、搜索等查询<br>2、支持发布提问

技能  - 专家整理.xlsx / 技能(学生测) / 第 14 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| G14 | 功能点（中文） | 讨论<br>1、查询已发布的话题讨论（本课程老师和学生）支持筛选状态、更新时间、搜索等查询<br>2、支持发布提问 |
| H14 | 描述 | 按需查询讨论话题及信息、发布提问 |
| B（合并继承自 B11；B11:B14） | 原值见锚点 | 课程任务 |

<a id="entry-b3d14b8b8d420a512129"></a>
### entry-b3d14b8b8d420a512129 · 1.查询阶梯完成状态/完成进度<br>2.查询课程下当前学期阶梯数量<br>3.查询学生当前学期的数据统计<br>4.查询学伴等级<br>5.查询学生某个阶梯的批阅消息

技能  - 专家整理.xlsx / 技能(学生测) / 第 15 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B15 | 场景标签 | 能力阶梯 |
| G15 | 功能点（中文） | 1.查询阶梯完成状态/完成进度<br>2.查询课程下当前学期阶梯数量<br>3.查询学生当前学期的数据统计<br>4.查询学伴等级<br>5.查询学生某个阶梯的批阅消息 |

<a id="entry-48619e5500d46c5043bc"></a>
### entry-48619e5500d46c5043bc · 1.查询智能体授课完成状态<br>2.查询合集完成进度

技能  - 专家整理.xlsx / 技能(学生测) / 第 16 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B16 | 场景标签 | 智能体教学 |
| G16 | 功能点（中文） | 1.查询智能体授课完成状态<br>2.查询合集完成进度 |

<a id="entry-22113ed484ad832111b1"></a>
### entry-22113ed484ad832111b1 · 1、查询已发布的学习路径（包含路径名称、路径开放时间、路径状态、路径介绍等）<br>2、支持切换路径学习<br>3、查询学习进度和节点得分<br>3、查询节点任务状态<br>4、查看个人多维学情分析，包括学习成长曲线、个人成绩、学习进度、班级排名、节点成绩对比等

技能  - 专家整理.xlsx / 技能(学生测) / 第 17 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B17 | 场景标签 | AI翻转 |
| G17 | 功能点（中文） | 1、查询已发布的学习路径（包含路径名称、路径开放时间、路径状态、路径介绍等）<br>2、支持切换路径学习<br>3、查询学习进度和节点得分<br>3、查询节点任务状态<br>4、查看个人多维学情分析，包括学习成长曲线、个人成绩、学习进度、班级排名、节点成绩对比等 |
| H17 | 描述 | 按需查询学习路径、学习进度、各节点得分、学情分析等内容 |

<a id="entry-5f51d3ab0ad55d32a617"></a>
### entry-5f51d3ab0ad55d32a617 · 1、查询所在小组，加入新发布的小组<br>2、查询小组内作业信息，包括作业作答时间、组内成员、作业成绩等；作为组长提交小组作业，组员参与组内互评或组间互评

技能  - 专家整理.xlsx / 技能(学生测) / 第 18 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B18 | 场景标签 | 小组学习 |
| G18 | 功能点（中文） | 1、查询所在小组，加入新发布的小组<br>2、查询小组内作业信息，包括作业作答时间、组内成员、作业成绩等；作为组长提交小组作业，组员参与组内互评或组间互评 |
| H18 | 描述 | 作为组长或组员加入小组，提交作业，参与组内互评、组间互评 |

<a id="entry-800a05bf872dfe7f5d74"></a>
### entry-800a05bf872dfe7f5d74 · 1、收录作业、考试、训练题库中做错的题目，支持按照题干关键词、题目类型、错因、是否掌握等筛选题目，AI解析错题错因，也可自动绑定错因<br>2、选择错题进行训练、做对会提高掌握度，多次做对题目自动变为已掌握<br>3、支持查看训练历史记录，再次练习<br>4、支持错题生成学习材料，如音频、题目、文档、知识闪卡等

技能  - 专家整理.xlsx / 技能(学生测) / 第 19 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B19 | 场景标签 | 学习助手（单独智能体） |
| G19 | 功能点（中文） | 1、收录作业、考试、训练题库中做错的题目，支持按照题干关键词、题目类型、错因、是否掌握等筛选题目，AI解析错题错因，也可自动绑定错因<br>2、选择错题进行训练、做对会提高掌握度，多次做对题目自动变为已掌握<br>3、支持查看训练历史记录，再次练习<br>4、支持错题生成学习材料，如音频、题目、文档、知识闪卡等 |
| H19 | 描述 | 学生可以对收录错题进行学习和训练，通过音频、文档、题目、知识闪卡等学习巩固知识点，多次训练题目提高掌握度，消灭错题 |

<a id="entry-92b4555ddf7b903c7b8a"></a>
### entry-92b4555ddf7b903c7b8a · 1、根据学习期望和偏好设置生成学习计划、学习计划支持编辑、删除<br>2、可查看不同状态的学习计划（进行中、已完成）<br>3、根据关键词、排序搜索学习计划<br>4、支持查看学习计划的学习进度

技能  - 专家整理.xlsx / 技能(学生测) / 第 20 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B20 | 场景标签 | 自定义学习（单独智能体） |
| G20 | 功能点（中文） | 1、根据学习期望和偏好设置生成学习计划、学习计划支持编辑、删除<br>2、可查看不同状态的学习计划（进行中、已完成）<br>3、根据关键词、排序搜索学习计划<br>4、支持查看学习计划的学习进度 |
| H20 | 描述 | 支持学生自主学习计划的创建与学习进度的追踪 |

<a id="entry-adc1cabb45b56976e3a1"></a>
### entry-adc1cabb45b56976e3a1 · 1、查询课程（查询我教的课、我学的课，包含各课程类型及是否教务课程、课程数量、按学期查询、按课程名称查询、查询哪些课程归档了等）

技能  - 专家整理.xlsx / 技能(教师测) / 第 2 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B2 | 场景标签 | 我的课程 |
| G2 | 功能点（中文） | 1、查询课程（查询我教的课、我学的课，包含各课程类型及是否教务课程、课程数量、按学期查询、按课程名称查询、查询哪些课程归档了等）<br> |
| H2 | 描述 | 按需查询课程信息、创建课程 |
| M2 | 未命名列 M | 内置 |
| N2 | 未命名列 N | 标准 |

<a id="entry-9ee26aa831ff3783cbdd"></a>
### entry-9ee26aa831ff3783cbdd · 2、创建课程

技能  - 专家整理.xlsx / 技能(教师测) / 第 3 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| G3 | 功能点（中文） | 2、创建课程 |
| M3 | 未命名列 M | 内置 |
| N3 | 未命名列 N | 标准 |
| B（合并继承自 B2；B2:B4） | 原值见锚点 | 我的课程 |

<a id="entry-b63e5b9e2b3a4519e44c"></a>
### entry-b63e5b9e2b3a4519e44c · 3、加入课程,

技能  - 专家整理.xlsx / 技能(教师测) / 第 4 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| G4 | 功能点（中文） | 3、加入课程, |
| B（合并继承自 B2；B2:B4） | 原值见锚点 | 我的课程 |

<a id="entry-9cd72f866c70d5e13b52"></a>
### entry-9cd72f866c70d5e13b52 · 课程管理

技能  - 专家整理.xlsx / 技能(教师测) / 第 5 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B5 | 场景标签 | 课程管理 |
| D5 | 技能中文名 | 课程管理 |
| G5 | 功能点（中文） | 1、修改/完善/编辑课程基础信息、包括名称、<br>2、查询、添加、移除教师团队、变更课程负责人、设置团队老师为管理员<br>3、查询、添加、删除班级、学生增减维护、筛选查询、群聊管理<br>4、小组方案创建、编辑、删除 |
| H5 | 描述 | 协助老师完善课程信息、课程团队、课程班级、分组管理 |
| M5 | 未命名列 M | 两部分<br>1、查询相关<br>2、管理相关 |

<a id="entry-904b21c6062594abc27b"></a>
### entry-904b21c6062594abc27b · 教学活动专员

技能  - 专家整理.xlsx / 技能(教师测) / 第 6 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B6 | 场景标签 | 教学活动 |
| D6 | 技能中文名 | 教学活动专员 |
| G6 | 功能点（中文） | 1、查询对应课程不同类型活动列表、数量、关联班级、活动截止时间等<br>2、创建、编辑、删除不同类型活动<br>3、可查询发布和未发布的作业、考试、通知；已发布的话题讨论<br>4、查看授课后生成的课堂报告，以及课堂中发布的考勤学生参与情况<br>5、汇聚最新的教学动态 |
| H6 | 描述 | 教师查看课程下的各类教学活动（作业、考试、讨论、通知、课堂报告），支持创建、编辑、删除活动，配置活动参数和关联班级 |

<a id="entry-4a46b0515056b8aaa0bc"></a>
### entry-4a46b0515056b8aaa0bc · 1、发布作业（各种类型）<br>2、查看学生作业提交情况<br>3、对作业进行催交、批阅、打回<br>4、修改作业内容、延长作业时间<br>5、审核学生作业重做申请<br>6、发布学生作业成绩<br>7、导出作业附件、批注附件、学生作业、学生成绩、作业分析<br>8、作业内容编辑、测评题目绑定、学生答题收集、作答数据统计分析<br>9、AI批阅、手动批阅、公布成绩和答案

技能  - 专家整理.xlsx / 技能(教师测) / 第 7 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B7 | 场景标签 | 作业 |
| G7 | 功能点（中文） | 1、发布作业（各种类型）<br>2、查看学生作业提交情况<br>3、对作业进行催交、批阅、打回<br>4、修改作业内容、延长作业时间<br>5、审核学生作业重做申请<br>6、发布学生作业成绩<br>7、导出作业附件、批注附件、学生作业、学生成绩、作业分析<br>8、作业内容编辑、测评题目绑定、学生答题收集、作答数据统计分析<br>9、AI批阅、手动批阅、公布成绩和答案 |
| H7 | 描述 | 教师发布和管理课程作业，跟踪学生提交情况，支持催缴、批阅、打回、成绩发布和数据导出；作业可批量下发至班级，自动汇总学生答题数据，教师仅查看本班作业信息，发布前审核拦截未完善作业 |

<a id="entry-e059f38a1321f46eb3aa"></a>
### entry-e059f38a1321f46eb3aa · 1、发布考试（各种类型），考试防作弊设置<br>2、查看学生考试情况，实时进行考试监考<br>3、对考试进行催缴、批阅、打回<br>4、修改考试内容、延长考试时间<br>5、发布学生考试成绩<br>6、查看考试学情分析<br>7、针对已结束考试创建补考<br>8、公布试卷和答案<br>9、导出考试附件、批注附件、学生试卷、学生成绩、试题存档

技能  - 专家整理.xlsx / 技能(教师测) / 第 8 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B8 | 场景标签 | 考试 |
| G8 | 功能点（中文） | 1、发布考试（各种类型），考试防作弊设置<br>2、查看学生考试情况，实时进行考试监考<br>3、对考试进行催缴、批阅、打回<br>4、修改考试内容、延长考试时间<br>5、发布学生考试成绩<br>6、查看考试学情分析<br>7、针对已结束考试创建补考<br>8、公布试卷和答案<br>9、导出考试附件、批注附件、学生试卷、学生成绩、试题存档 |
| H8 | 描述 | 教师创建和管理课程考试，配置试卷、考试时间和防作弊规则，支持客观题自动判分和主观题AI/手动批阅，考试数据独立隔离，支持教师手动调整成绩 |

<a id="entry-a7a1c0a43d4f7499e797"></a>
### entry-a7a1c0a43d4f7499e797 · 1、查询话题讨论及参与班级等信息<br>2、创建话题讨论关联班级设定发布<br>3、话题讨论操作，设置为精华、围观等<br>4、删除话题讨论

技能  - 专家整理.xlsx / 技能(教师测) / 第 9 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B9 | 场景标签 | 话题讨论 |
| G9 | 功能点（中文） | 1、查询话题讨论及参与班级等信息<br>2、创建话题讨论关联班级设定发布<br>3、话题讨论操作，设置为精华、围观等<br>4、删除话题讨论 |
| H9 | 描述 | 话题讨论管理，信息查询，创建和删除操作 |

<a id="entry-a99be544ccc0aa277cb3"></a>
### entry-a99be544ccc0aa277cb3 · 1、查询各种状态的通知及设定的参与班级、已读人数等信息<br>2、创建通知关联班级设定发布

技能  - 专家整理.xlsx / 技能(教师测) / 第 10 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B10 | 场景标签 | 通知 |
| G10 | 功能点（中文） | 1、查询各种状态的通知及设定的参与班级、已读人数等信息<br>2、创建通知关联班级设定发布 |

<a id="entry-6ee49c4594d26218d638"></a>
### entry-6ee49c4594d26218d638 · 备课@余洲

技能  - 专家整理.xlsx / 技能(教师测) / 第 11 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B11 | 场景标签 | 备课 |
| D11 | 技能中文名 | 备课@余洲 |
| G11 | 功能点（中文） | 1、查询对应课程的备课信息<br>2、创建、编辑、删除备课方案<br>3、备课添加教学设计（课件、教案、德育案例，自主上传）<br>4、添加、编辑、删除各种工具如：头脑风暴、随堂测试、投票等。（签到、随机点名、抢答、课堂答疑、课堂评价、HTML网页目前开发中）<br>5、复制备课方案 |
| H11 | 描述 | 创建和管理备课方案，添加教学设计资源（课件、教案、德育案例）和课堂互动工具（头脑风暴、随堂测试、投票等），可复用模板快速生成备课方案 |

<a id="entry-1354e69321949ce6ec31"></a>
### entry-1354e69321949ce6ec31 · 1、配置学期时间<br>2、查询本学期/某一天/星期X，我的排课信息、会议、作业截止、考试、AI提醒等，也希望支持按时间范围和类型筛选<br>3、创建、编辑某个课程的课堂日程（单个、周期性日程支持周次配置）<br>4、删除某个课程的课堂日程（单个、周期性日程）

技能  - 专家整理.xlsx / 技能(教师测) / 第 12 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B12 | 场景标签 | 教学日历 |
| G12 | 功能点（中文） | 1、配置学期时间<br>2、查询本学期/某一天/星期X，我的排课信息、会议、作业截止、考试、AI提醒等，也希望支持按时间范围和类型筛选<br>3、创建、编辑某个课程的课堂日程（单个、周期性日程支持周次配置）<br>4、删除某个课程的课堂日程（单个、周期性日程） |
| H12 | 描述 | 支持老师配置学期时间，查询管理自己的课堂日程， |

<a id="entry-12241262aa0ed97f9281"></a>
### entry-12241262aa0ed97f9281 · 成绩管理

技能  - 专家整理.xlsx / 技能(教师测) / 第 13 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B13 | 场景标签 | 成绩管理 |
| D13 | 技能中文名 | 成绩管理 |
| G13 | 功能点（中文） | 1、一键切换不同班级查看该班成绩<br>2、导出班级所有考勤成绩、平时成绩、作业成绩、考试成绩数据<br>3、支持搜索具体学生查看学生的各维度成绩<br>4、考勤成绩支持添加线下考勤 / 下载考勤数据 / 高级导出 / 出勤率；考勤数据支持老师手动修改签到状态<br>5、平时成绩支持下载 / 高级导出 / ；统计学习进度+互动次数+课堂互动总分<br>6、作业成绩支持添加线下作业 / 下载 / 高级导出；根据权重设置计算学生的作业平均（加权）成绩<br>7、考试成绩支持添加线下考试 / 下载 / 高级导出；根据权重设置计算学生的考试平均（加权）成绩<br>8、成绩加权设置，支持自定义设置各维度成绩的权重，也支持添加自定义考核项<br>9、支持快速复制权重设置到其他教学班<br>10、总成绩支持进行成绩归档操作/下载总成绩<br>11、可设置是否允许学生查看总成绩<br>12、总成绩分布图表可视化展示<br>13、支持老师手动修改学生的最终总成绩 |
| H13 | 描述 | 教师录入和管理学生成绩，按权重自动核算综合成绩，支持成绩导出和修改审计；系统可按权重自动核算综合成绩，成绩数据修改操作全部记录日志，上课教师只可编辑本班成绩 |

<a id="entry-fea90bb734fb6f663bf8"></a>
### entry-fea90bb734fb6f663bf8 · 1、学习模式一键切换（普通/闯关/复习）<br>2、支持资源的引用、上传、编辑、下载、发布到班级<br>3、支持查询具体班级下已发布的学习资源和课程下所有已上传引用的学习资源<br>4、支持新建资源分组、从共享资源库和资源库引用资源；支持添加链接形式的资源<br>5、支持根据资源名称搜索已添加的资源<br>6、可批量发布、取消发布、删除学习资源<br>7、资源支持定时自动发布

技能  - 专家整理.xlsx / 技能(教师测) / 第 14 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B14 | 场景标签 | 学习资源 |
| G14 | 功能点（中文） | 1、学习模式一键切换（普通/闯关/复习）<br>2、支持资源的引用、上传、编辑、下载、发布到班级<br>3、支持查询具体班级下已发布的学习资源和课程下所有已上传引用的学习资源<br>4、支持新建资源分组、从共享资源库和资源库引用资源；支持添加链接形式的资源<br>5、支持根据资源名称搜索已添加的资源<br>6、可批量发布、取消发布、删除学习资源<br>7、资源支持定时自动发布 |
| H14 | 描述 | 学习资源管理，教师管理课程学习资源的一站式模块，覆盖资源的上传、引用、编辑、发布全生命周期。系统提供普通、闯关、复习三种学习模式，教师可按教学需要一键切换，适配不同教学场景。 |
| M14 | 未命名列 M | 检索+跳转 |

<a id="entry-ec113ce4ef03fde49a53"></a>
### entry-ec113ce4ef03fde49a53 · 1、多格式资料上传、文件自动解析<br>2、知识库文件删除<br>3、知识块添加、编辑、删除<br>4、课代表问答使用AI知识库内容

技能  - 专家整理.xlsx / 技能(教师测) / 第 15 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B15 | 场景标签 | AI/课程知识库 |
| G15 | 功能点（中文） | 1、多格式资料上传、文件自动解析<br>2、知识库文件删除<br>3、知识块添加、编辑、删除<br>4、课代表问答使用AI知识库内容 |
| H15 | 描述 | 知识库文件、知识块内容搜索、上传文件解析等功能 |

<a id="entry-e11149f135dd8f86e328"></a>
### entry-e11149f135dd8f86e328 · 资源管理

技能  - 专家整理.xlsx / 技能(教师测) / 第 16 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B16 | 场景标签 | 资源库 |
| D16 | 技能中文名 | 资源管理 |
| G16 | 功能点（中文） | 1、三大资源库（个人资源库、团队资源库、课程资源库）数据隔离支持不同资源库之间的资源复制、移动操作<br>2、资源库支持创建作业模板、考试模板、上传课件、上传文件、新建文件夹、能力实训模板、智能体教学模板、知识图谱、智能体、智能辅导（指定机构）、备课、数字人<br>3、资源库中的资源模板支持添加至学习资源、发布到教学活动<br>4、个人资源库（教师私有）：<br>  1.1 资源上传/添加（本地+引用）<br>  1.2 自定义分类管理（13 个分类）<br>  1.3 文件夹管理（新建/重命名/删除）<br>  1.4 资源搜索<br>  1.5 资源操作（预览/编辑/引用/下载/复制/删除）<br>  1.6 回收站（移入+还原+永久删除）<br>  1.7 资源卡片（标题/累计发布次数/分类标签）<br>  1.8 视图切换（网格/列表）<br>  1.9 批量操作<br>  1.10我的知识库管理<br>  1.11支持引用翻转课资源和共享课资源<br>5、团队资源库（教研室团队共享）：<br>  2.1 团队切换 + 成员数展示<br>  2.2 团队资源上传/引用/共享<br>  2.3 13 个分类管理<br>  2.4 资源搜索/编辑/删除<br>  2.5 资源共享<br>  2.6 批量操作（批量发布/删除）<br>6、课程资源库（课程维度）<br>  1.1课程团队老师共享<br>  1.2课堂回放文件夹单独自动存放教学生成的课堂录像 |
| H16 | 描述 | 教师在 AI 教学中心管理教学资源的一站式模块，按资源归属提供个人资源库、团队资源库、课程资源库三大资源库。三大资源库共享统一的资源操作能力（添加、新建文件夹、搜索、视图切换、批量选择、引用、下载、删除/回收站），但各自有独立的分类体系与权限管理。 |

<a id="entry-a41ced4d95b47b88772b"></a>
### entry-a41ced4d95b47b88772b · 题库试卷库管理

技能  - 专家整理.xlsx / 技能(教师测) / 第 17 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B17 | 场景标签 | 题库试卷库 |
| D17 | 技能中文名 | 题库试卷库管理 |
| G17 | 功能点（中文） | 1、支持两种维度的题库管理：课程题库&amp;我的题库，两者之间题目支持互相复制和移动<br>2、新增试题支持5种方式（AI出题、手动新增、智能导入、word导入、excal导入）<br>3、题目支持已文件夹形式管理，文件夹支持创建、编辑、移动、删除<br>4、试题列表支持题型/难度/知识点/标签/来源等多维筛选 + 关键字搜索 + 翻页<br>5、试题单条操作（预览/编辑/复制/移动/添加到/删除）<br>6、试题预览详细信息，支持查看题目的来源、属性、位置、以及应用到的试卷和修改记录<br>7、试题支持批量多选题目的 word 导出、excel 导出、设置标签、预览、添加到、移动到、删除<br>8、题目工具集：试题查重/开启试题防护/标签管理<br>9、题库支持17种题型<br>10、支持两种维度的试卷库管理：课程试卷库&amp;我的试卷库，两者之间的试卷支持互相复制和移动<br>11、试卷库支持创建试卷、自动/手动组卷、配置题型分布、自定义组卷策略<br>12、试卷库中的试卷可根据试卷关键词进行搜索<br>13、试卷库中的试卷支持查看、编辑、下载、发布到作业和考试、重命名、复制、移动、删除<br>14、随机组卷的试卷支持查看样卷、删除样卷、修改出题规则<br>15、回收站统一 30 天管控：到期自动清理，可手工恢复、永久删除 |
| H17 | 描述 | 教师在 AI 教学中心管理课程试题与试卷的一站式模块，由题库、试卷库、回收站三大区域组成。题库与试卷库均提供"课程级 + 个人级"双维度，支持题目与试卷在双维度间复制、移动，实现资源沉淀与跨课程复用。 |

<a id="entry-951928d6a4a66a6f8a06"></a>
### entry-951928d6a4a66a6f8a06 · AI 出题

技能  - 专家整理.xlsx / 技能(教师测) / 第 18 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B18 | 场景标签 | AI 出题 |
| D18 | 技能中文名 | AI 出题 |
| G18 | 功能点（中文） | 1、按题目名称 / 出题要求 / 参考资料 / 学科名称 / 考核目标生成单选 / 多选 / 填空题生成指定数量题目、支持保存到题库 |
| H18 | 描述 | 可以按照要求生成指定数量题目并保存到题库使用 |

<a id="entry-dfdab737d85b9396c0b9"></a>
### entry-dfdab737d85b9396c0b9 · 1、支持一键导入训练题，选择题库中题目一键导入、编辑和移除题目<br>2、记录答题数据，分析学生知识点掌握情况<br>3、支持查看学生易错题目、学生完成度、易错知识点和学生的答题详情<br>4、支持设置训练题库按照比例开放还是按照属性开放<br>5、刷题开放配置（教师）：开启/关闭开关，关闭后学生端不显示题目<br>6、题目查看与管理（教师）：题型/数量/明细，单题切换版本/编辑/删除/详情<br>7、支持 13 种题型筛选预览、可按照难易度筛选、关键字筛选

技能  - 专家整理.xlsx / 技能(教师测) / 第 19 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B19 | 场景标签 | 训练题库 |
| G19 | 功能点（中文） | 1、支持一键导入训练题，选择题库中题目一键导入、编辑和移除题目<br>2、记录答题数据，分析学生知识点掌握情况<br>3、支持查看学生易错题目、学生完成度、易错知识点和学生的答题详情<br>4、支持设置训练题库按照比例开放还是按照属性开放<br>5、刷题开放配置（教师）：开启/关闭开关，关闭后学生端不显示题目<br>6、题目查看与管理（教师）：题型/数量/明细，单题切换版本/编辑/删除/详情<br>7、支持 13 种题型筛选预览、可按照难易度筛选、关键字筛选 |
| H19 | 描述 | 训练题库是 AI 教学中心面向"学生自主刷题训练"的场景化模块，由教师配置开放规则、学生在 PC 与 H5 双端练习与模考。以"题库开放 → 刷题练习 → 错题/收藏沉淀 → 学习统计"为主链路。 |

<a id="entry-ada254cce4eb3879e418"></a>
### entry-ada254cce4eb3879e418 · 1、支持查看课程下老师管理班级的学情数据（综合评价、学习进度、教学活动完成率、总成绩、学生排行榜、学期趋势、知识点掌握度）<br>2、支持一键提醒预警学生<br>3、统计学习进度、课堂互动、话题讨论、作业、考试、智能体问答使用情况<br>4、支持查看课程下老师管理班级的教学数据（综合评价、班级数、入课学生数、课程活动数、老师学生进入课程次数）<br>5、统计教学资源（学习资源总数、题库题目总数、教学活动数、知识图谱数、智能体数）<br>6、教学运行概况统计（作业、考试、课堂互动、话题讨论的发布次数和参与率）<br>7、课程图谱统计<br>8、AI知识库上传资源和知识切片数量统计<br>9、智能体创建和使用次数统计<br>10、AI应用场景和次数统计

技能  - 专家整理.xlsx / 技能(教师测) / 第 20 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B20 | 场景标签 | 教学观测 |
| G20 | 功能点（中文） | 1、支持查看课程下老师管理班级的学情数据（综合评价、学习进度、教学活动完成率、总成绩、学生排行榜、学期趋势、知识点掌握度）<br>2、支持一键提醒预警学生<br>3、统计学习进度、课堂互动、话题讨论、作业、考试、智能体问答使用情况<br>4、支持查看课程下老师管理班级的教学数据（综合评价、班级数、入课学生数、课程活动数、老师学生进入课程次数）<br>5、统计教学资源（学习资源总数、题库题目总数、教学活动数、知识图谱数、智能体数）<br>6、教学运行概况统计（作业、考试、课堂互动、话题讨论的发布次数和参与率）<br>7、课程图谱统计<br>8、AI知识库上传资源和知识切片数量统计<br>9、智能体创建和使用次数统计<br>10、AI应用场景和次数统计 |
| H20 | 描述 | 教师对课程与班级教学全过程进行"观测与决策"的数据看板模块，从学生学情、教学运行、资源建设、AI 应用四个视角提供统计视图，帮助教师及时掌握教学状态、发现风险并干预。 |

<a id="entry-1a076ae9458f0edaf37e"></a>
### entry-1a076ae9458f0edaf37e · 课堂互动

技能  - 专家整理.xlsx / 技能(教师测) / 第 21 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B21 | 场景标签 | 课堂互动 |
| D21 | 技能中文名 | 课堂互动 |
| G21 | 功能点（中文） | 1、开启课堂，包括教室授课和直播授课<br>2、发起互动：签到、投票、点名、抢答、答疑、头脑风暴、随堂测验、分组讨论等互动<br>3、查询学生信息，参与互动情况<br>4、播放课件 |
| H21 | 描述 | 各类互动工具参与情况实时查询，学生作答数据实时同步展示，分值自动累计，所有互动记录可课后查询核对 |

<a id="entry-e183d9a584fa141e7161"></a>
### entry-e183d9a584fa141e7161 · 1、直播回放观看<br>2、课堂教学数据自动汇总、教学报告预览<br>3、课堂回放同步到学习资源、发布给学生查看<br>4、查看回放申请审批

技能  - 专家整理.xlsx / 技能(教师测) / 第 22 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B22 | 场景标签 | 课堂报告/回放 |
| G22 | 功能点（中文） | 1、直播回放观看<br>2、课堂教学数据自动汇总、教学报告预览<br>3、课堂回放同步到学习资源、发布给学生查看<br>4、查看回放申请审批 |
| H22 | 描述 | 可以查看生成的课堂回放，按需要将回放同步至学习资源或发布给学生查看，查询学生信息，包括互动参与情况、在线时长、得分情况等 |

<a id="entry-e7aab2c1c59e64515e24"></a>
### entry-e7aab2c1c59e64515e24 · 知识图谱

技能  - 专家整理.xlsx / 技能(教师测) / 第 23 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B23 | 场景标签 | 知识图谱 |
| D23 | 技能中文名 | 知识图谱 |
| G23 | 功能点（中文） | 1、手动创建支持图谱或根据文件生成知识图谱<br>2、支持编辑、删除知识图谱<br>3、可以按树状、环状、网状展示知识图谱 |
| H23 | 描述 | 可以查看、新增、编辑、删除知识图谱，支持在知识点挂载资源，查看知识点数 |

<a id="entry-f8d059a34cd5abfb3c25"></a>
### entry-f8d059a34cd5abfb3c25 · 创建教学计划<br>讲-配置

技能  - 专家整理.xlsx / 技能(教师测) / 第 24 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B24 | 场景标签 | AI翻转 |
| D24 | 技能中文名 | 创建教学计划<br>讲-配置 |
| G24 | 功能点（中文） | 1、创建讲组成教学计划<br>2、基础信息配置:名称,学时,课堂目标,课堂概述的配置<br>3、任务配置:添加各种类型的作业，考试，训练题库，资源学习、智能体教学、话题讨论、链接任务<br>4、闯关配置：配置学习方式（自由学习，顺序闯关，全域浏览），完成条件，开始时间的配置 |
| H24 | 描述 | 可以按要求，生成教学计划和作业、考试、训练题库、资源学习、智能体教学、话题讨论等任务配置 |

<a id="entry-a7f5f6a179e03c8827ef"></a>
### entry-a7f5f6a179e03c8827ef · 1、分组方案学期概览<br>2、创建分组方案，支持自由分组、随机分组、指定分组<br>3、小组成员查看、调整，包括更换组长、调整组员等<br>4、分组下新建、编辑、删除、发布小组作业<br>5、作业数据统计、查询作业

技能  - 专家整理.xlsx / 技能(教师测) / 第 25 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B25 | 场景标签 | 小组教学 |
| G25 | 功能点（中文） | 1、分组方案学期概览<br>2、创建分组方案，支持自由分组、随机分组、指定分组<br>3、小组成员查看、调整，包括更换组长、调整组员等<br>4、分组下新建、编辑、删除、发布小组作业<br>5、作业数据统计、查询作业 |
| H25 | 描述 | 按学期展示分组方案，统计学生数、分组数、作业数，可以查询方案、小组作业等；支持新建、编辑、删除小组方案、小组作业 |

<a id="entry-2913b71455d5af34b40e"></a>
### entry-2913b71455d5af34b40e · 1、可以上传文件解析生成对应的教学计划<br>2、查询、编辑、删除教学计划，包括教学计划单元，知识点等<br>3、统计展示教学计划关联的作业、考试

技能  - 专家整理.xlsx / 技能(教师测) / 第 26 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B26 | 场景标签 | 教学计划 |
| G26 | 功能点（中文） | 1、可以上传文件解析生成对应的教学计划<br>2、查询、编辑、删除教学计划，包括教学计划单元，知识点等<br>3、统计展示教学计划关联的作业、考试 |
| H26 | 描述 | 老师可以上传文件生成教学计划，生成后支持编辑、删除操作，并可查看和统计教学计划关联的作业和考试 |

<a id="entry-daf9ca6d2929733511f5"></a>
### entry-daf9ca6d2929733511f5 · 1、录入毕业要求、录入课程目标（支持手动输入、AI识别）、编辑、删除<br>2、设置/修改课程目标与毕业要求对应关系<br>3、设置/修改考核方式（教学活动权重为1还是课程目标权重为1）设置单项教学活动权重<br>4、修改课程目标占比<br>5、配置课程目标设置达成度构成添加教学活动（课堂考勤、学习资源、作业、考试、添加自定义）<br>6、题目权重分配<br>7、T+1查看达成度分析<br>8、导出报告

技能  - 专家整理.xlsx / 技能(教师测) / 第 27 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B27 | 场景标签 | OBE管理 |
| G27 | 功能点（中文） | 1、录入毕业要求、录入课程目标（支持手动输入、AI识别）、编辑、删除<br>2、设置/修改课程目标与毕业要求对应关系<br>3、设置/修改考核方式（教学活动权重为1还是课程目标权重为1）设置单项教学活动权重<br>4、修改课程目标占比<br>5、配置课程目标设置达成度构成添加教学活动（课堂考勤、学习资源、作业、考试、添加自定义）<br>6、题目权重分配<br>7、T+1查看达成度分析<br>8、导出报告 |
| H27 | 描述 | OBE（成果导向教育）管理模块，教师按"毕业要求 → 课程目标 → 考核方式 → 达成度分析"主线配置课程的成果导向教学体系，支撑专业认证与持续改进 |

<a id="entry-bcebec08d2070c4d5ae0"></a>
### entry-bcebec08d2070c4d5ae0 · 1、有多种通用的AI工具，如AI阅读、AI批阅智能体、深度写作、PPT生成、文生图、教学视频生成，灵活使用以提高工作效率<br>2、支持自定义工具

技能  - 专家整理.xlsx / 技能(教师测) / 第 28 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B28 | 场景标签 | 课程工具箱 |
| G28 | 功能点（中文） | 1、有多种通用的AI工具，如AI阅读、AI批阅智能体、深度写作、PPT生成、文生图、教学视频生成，灵活使用以提高工作效率<br>2、支持自定义工具 |
| H28 | 描述 | 支持AI阅读、AI批阅智能体、深度写作、PPT生成、文生图、教学视频生成等多种工具能力使用，也支持自定义生成工具 |

<a id="entry-6f4ca7a7f8e63dfc1672"></a>
### entry-6f4ca7a7f8e63dfc1672 · 1.创建智能体教学单课堂（不要创建合集了，20号版本会去掉创建合集的入口）<br>2.发布智能体教学单课堂<br>3.查询单课堂/合集发布状态<br>4.查询已发布单课堂/合集的学生列表/学生完成情况<br>5.单课堂和合集的复制/删除/添加到资源库<br>6.查询课程在当前学期，智能体授课的学习人次、累计授课时长、累计互动次数

技能  - 专家整理.xlsx / 技能(教师测) / 第 29 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B29 | 场景标签 | 智能体教学 |
| G29 | 功能点（中文） | 1.创建智能体教学单课堂（不要创建合集了，20号版本会去掉创建合集的入口）<br>2.发布智能体教学单课堂<br>3.查询单课堂/合集发布状态<br>4.查询已发布单课堂/合集的学生列表/学生完成情况<br>5.单课堂和合集的复制/删除/添加到资源库<br>6.查询课程在当前学期，智能体授课的学习人次、累计授课时长、累计互动次数 |

<a id="entry-95e40f970bd562108997"></a>
### entry-95e40f970bd562108997 · 1.查询阶梯：发布状态<br>2.查询已发布阶梯的学生完成情况（整体）<br>3.查询阶梯下具体任务的完成人数/达成度<br>4.查询目标达成度<br>5.查询阶梯下某个学生完成情况<br>6.发布/删除/添加到/复制<br>7.查询当前学期能力全景图的统计数据

技能  - 专家整理.xlsx / 技能(教师测) / 第 30 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B30 | 场景标签 | 能力阶梯 |
| G30 | 功能点（中文） | 1.查询阶梯：发布状态<br>2.查询已发布阶梯的学生完成情况（整体）<br>3.查询阶梯下具体任务的完成人数/达成度<br>4.查询目标达成度<br>5.查询阶梯下某个学生完成情况<br>6.发布/删除/添加到/复制<br>7.查询当前学期能力全景图的统计数据 |

<a id="entry-ce0673c2afea2a164abe"></a>
### entry-ce0673c2afea2a164abe · 课程待办任务查询

技能  - 专家整理.xlsx / 技能(公共) / 第 2 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B2 | 场景标签 | 首页/待办 |
| D2 | 技能中文名 | 课程待办任务查询 |
| E2 | 功能点序号 | 1 |
| G2 | 功能点（中文） | 查询教学平台课程待办任务，以及完成进度 |
| H2 | 描述 | 查询当前学生的任务、筛选、搜索与课程通知 |

<a id="entry-095ef2796db86189c506"></a>
### entry-095ef2796db86189c506 · 1、学习模式一键切换（普通/闯关/复习）<br>2、支持资源的引用、上传、编辑、下载、发布到班级<br>3、支持查询具体班级下已发布的学习资源和课程下所有已上传引用的学习资源<br>4、支持新建资源分组、从共享资源库和资源库引用资源；支持添加链接形式的资源<br>5、支持根据资源名称搜索已添加的资源<br>6、可批量发布、取消发布、删除学习资源<br>7、资源支持定时自动发布<br>8、学生端仅支持查看学习资源，显示必学资源学习进度

技能  - 专家整理.xlsx / 技能(公共) / 第 3 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B3 | 场景标签 | 学习资源 |
| G3 | 功能点（中文） | 1、学习模式一键切换（普通/闯关/复习）<br>2、支持资源的引用、上传、编辑、下载、发布到班级<br>3、支持查询具体班级下已发布的学习资源和课程下所有已上传引用的学习资源<br>4、支持新建资源分组、从共享资源库和资源库引用资源；支持添加链接形式的资源<br>5、支持根据资源名称搜索已添加的资源<br>6、可批量发布、取消发布、删除学习资源<br>7、资源支持定时自动发布<br>8、学生端仅支持查看学习资源，显示必学资源学习进度 |
| H3 | 描述 | 学习资源管理，教师管理课程学习资源的一站式模块，覆盖资源的上传、引用、编辑、发布全生命周期。系统提供普通、闯关、复习三种学习模式，教师可按教学需要一键切换，适配不同教学场景。<br><br>学生端仅支持查看学习资源，显示必学资源学习进度 |

<a id="entry-aa132a749470a97dcc3b"></a>
### entry-aa132a749470a97dcc3b · meeting-skill

技能  - 专家整理.xlsx / 技能 / 第 3 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A3 | 类型 | 业务 |
| B3 | 场景标签 | 会议管理 |
| C3 | 技能名称 | meeting-skill |
| D3 | 技能中文名 | 会议管理技能 |
| E3 | 功能点序号 | 1 |
| F3 | 功能点（英文） | meeting |
| G3 | 功能点（中文） | 会议管理 |
| H3 | 描述 | 会议全流程：创建会议、查询会议列表（Markdown展示）、取消会议、查询会议纪要/总结 |

<a id="entry-f964f68515af765f5869"></a>
### entry-f964f68515af765f5869 · meeting-skill

技能  - 专家整理.xlsx / 技能 / 第 4 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| E4 | 功能点序号 | 2 |
| F4 | 功能点（英文） | errors |
| G4 | 功能点（中文） | 错误处理规范 |
| H4 | 描述 | 会议技能错误处理规范：脚本输出约定、错误码含义与回复模板 |
| D（合并继承自 D3；D3:D4） | 原值见锚点 | 会议管理技能 |
| C（合并继承自 C3；C3:C4） | 原值见锚点 | meeting-skill |
| B（合并继承自 B3；B3:B4） | 原值见锚点 | 会议管理 |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-33b3abf5e876783e63fc"></a>
### entry-33b3abf5e876783e63fc · polymas-agent-readme

技能  - 专家整理.xlsx / 技能 / 第 5 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B5 | 场景标签 | 平台帮助/导航 |
| C5 | 技能名称 | polymas-agent-readme |
| D5 | 技能中文名 | 平台智能体帮助手册 |
| E5 | 功能点序号 | 1 |
| F5 | 功能点（英文） | platform-help |
| G5 | 功能点（中文） | 平台功能帮助 |
| H5 | 描述 | 展示平台8大模块、34项核心能力及典型问法；引导用户用自然语言描述需求，不执行业务操作 |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-d82f416b8359bc0e4e10"></a>
### entry-d82f416b8359bc0e4e10 · polymas-course-obe-skills

技能  - 专家整理.xlsx / 技能 / 第 6 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B6 | 场景标签 | OBE/达成度 |
| C6 | 技能名称 | polymas-course-obe-skills |
| D6 | 技能中文名 | 课程OBE技能 |
| E6 | 功能点序号 | 1 |
| F6 | 功能点（英文） | course_obe |
| G6 | 功能点（中文） | OBE达成度查询 |
| H6 | 描述 | 查询课程OBE达成度，包括课程整体平均达成度、各课程目标平均达成度及各班级达成度 |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-da0f5a3c58d24c22469b"></a>
### entry-da0f5a3c58d24c22469b · polymas-course-obe-skills

技能  - 专家整理.xlsx / 技能 / 第 7 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B7 | 场景标签 | OBE/识别 |
| E7 | 功能点序号 | 2 |
| F7 | 功能点（英文） | obe_file_analysis |
| G7 | 功能点（中文） | OBE文件识别 |
| H7 | 描述 | 上传教学大纲文件，AI识别毕业目标和毕业要求 |
| D（合并继承自 D6；D6:D8） | 原值见锚点 | 课程OBE技能 |
| C（合并继承自 C6；C6:C8） | 原值见锚点 | polymas-course-obe-skills |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-bedb2d1e4313945bdf81"></a>
### entry-bedb2d1e4313945bdf81 · polymas-course-obe-skills

技能  - 专家整理.xlsx / 技能 / 第 8 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B8 | 场景标签 | OBE/保存 |
| E8 | 功能点序号 | 3 |
| F8 | 功能点（英文） | obe_save |
| G8 | 功能点（中文） | OBE目标保存 |
| H8 | 描述 | 保存毕业要求和保存毕业目标（权重之和必须为100） |
| D（合并继承自 D6；D6:D8） | 原值见锚点 | 课程OBE技能 |
| C（合并继承自 C6；C6:C8） | 原值见锚点 | polymas-course-obe-skills |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-1d1a3c8a1223dc5415f1"></a>
### entry-1d1a3c8a1223dc5415f1 · polymas-course-overview-skills

技能  - 专家整理.xlsx / 技能 / 第 9 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B9 | 场景标签 | 课程查询/概况 |
| C9 | 技能名称 | polymas-course-overview-skills |
| D9 | 技能中文名 | 课程概况查询技能 |
| E9 | 功能点序号 | 1 |
| F9 | 功能点（英文） | course_overview |
| G9 | 功能点（中文） | 课程概况查询 |
| H9 | 描述 | 查询课程概况信息，包括教学计划状态、单元/章节数量、课代表对话次数、AI知识库资源数量及教学活动列表 |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-03b2cab6867bb4e6e3c4"></a>
### entry-03b2cab6867bb4e6e3c4 · polymas-page-navigation

技能  - 专家整理.xlsx / 技能 / 第 10 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B10 | 场景标签 | 平台导航 |
| C10 | 技能名称 | polymas-page-navigation |
| D10 | 技能中文名 | 页面导航指引技能 |
| E10 | 功能点序号 | 1 |
| F10 | 功能点（英文） | page_navigation |
| G10 | 功能点（中文） | 页面导航指引 |
| H10 | 描述 | 页面导航指引：用户想做某操作但需在页面完成时，返回对应页面链接+一句话操作指引 |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-5dfbe45583f61c71cdf5"></a>
### entry-5dfbe45583f61c71cdf5 · polymas-query-teaching-unit

技能  - 专家整理.xlsx / 技能 / 第 11 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B11 | 场景标签 | 教学计划/查询 |
| C11 | 技能名称 | polymas-query-teaching-unit |
| D11 | 技能中文名 | 教学单元查询技能 |
| E11 | 功能点序号 | 1 |
| F11 | 功能点（英文） | query_teaching_unit |
| G11 | 功能点（中文） | 教学单元查询 |
| H11 | 描述 | 查询指定课程的教学单元、主题、知识点及知识点关系的层级结构；仅可查当前用户有权访问的课程 |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-693fdddd0dfd19904a90"></a>
### entry-693fdddd0dfd19904a90 · polymas-teacher-activity-skills

技能  - 专家整理.xlsx / 技能 / 第 12 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B12 | 场景标签 | 教学活动/通知 |
| C12 | 技能名称 | polymas-teacher-activity-skills |
| D12 | 技能中文名 | 教师教学活动技能 |
| E12 | 功能点序号 | 1 |
| F12 | 功能点（英文） | notice_publish |
| G12 | 功能点（中文） | 通知发布 |
| H12 | 描述 | 教师向课程下班级或全部学生发布一条通知，支持指定标题、内容、附件以及目标班级 |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-e7844c4a7ef1c242b930"></a>
### entry-e7844c4a7ef1c242b930 · polymas-teacher-activity-skills

技能  - 专家整理.xlsx / 技能 / 第 13 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| E13 | 功能点序号 | 2 |
| F13 | 功能点（英文） | notice_search |
| G13 | 功能点（中文） | 通知查看 |
| H13 | 描述 | 教师查看课程下已发布的通知列表，支持关键词搜索、分页浏览与通知详情查看（已读/未读人员） |
| D（合并继承自 D12；D12:D17） | 原值见锚点 | 教师教学活动技能 |
| C（合并继承自 C12；C12:C17） | 原值见锚点 | polymas-teacher-activity-skills |
| B（合并继承自 B12；B12:B14） | 原值见锚点 | 教学活动/通知 |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-4d9a16451cfcf6508ce9"></a>
### entry-4d9a16451cfcf6508ce9 · polymas-teacher-activity-skills

技能  - 专家整理.xlsx / 技能 / 第 14 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| E14 | 功能点序号 | 3 |
| F14 | 功能点（英文） | notice_analysis |
| G14 | 功能点（中文） | 通知分析 |
| H14 | 描述 | 教师分析最近通知整体情况：数量、内容关键词聚合、发布频次、阅读情况统计等 |
| D（合并继承自 D12；D12:D17） | 原值见锚点 | 教师教学活动技能 |
| C（合并继承自 C12；C12:C17） | 原值见锚点 | polymas-teacher-activity-skills |
| B（合并继承自 B12；B12:B14） | 原值见锚点 | 教学活动/通知 |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-37a716f13fb3bcb5c882"></a>
### entry-37a716f13fb3bcb5c882 · polymas-teacher-activity-skills

技能  - 专家整理.xlsx / 技能 / 第 15 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B15 | 场景标签 | 教学活动/讨论 |
| E15 | 功能点序号 | 4 |
| F15 | 功能点（英文） | topic_publish |
| G15 | 功能点（中文） | 话题讨论发布 |
| H15 | 描述 | 教师在课程下班级发布话题讨论，支持指定内容、附件、班级范围与回复策略 |
| D（合并继承自 D12；D12:D17） | 原值见锚点 | 教师教学活动技能 |
| C（合并继承自 C12；C12:C17） | 原值见锚点 | polymas-teacher-activity-skills |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-d01f9fc82ceddc762d28"></a>
### entry-d01f9fc82ceddc762d28 · polymas-teacher-activity-skills

技能  - 专家整理.xlsx / 技能 / 第 16 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| E16 | 功能点序号 | 5 |
| F16 | 功能点（英文） | topic_search |
| G16 | 功能点（中文） | 话题讨论查看 |
| H16 | 描述 | 教师查看课程下话题讨论列表，支持关键词搜索、分页浏览 |
| B（合并继承自 B15；B15:B17） | 原值见锚点 | 教学活动/讨论 |
| D（合并继承自 D12；D12:D17） | 原值见锚点 | 教师教学活动技能 |
| C（合并继承自 C12；C12:C17） | 原值见锚点 | polymas-teacher-activity-skills |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-ac781d217b31173b76b2"></a>
### entry-ac781d217b31173b76b2 · polymas-teacher-activity-skills

技能  - 专家整理.xlsx / 技能 / 第 17 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| E17 | 功能点序号 | 6 |
| F17 | 功能点（英文） | topic_analysis |
| G17 | 功能点（中文） | 话题讨论分析 |
| H17 | 描述 | 教师分析讨论区学生关注热点：话题数量、关键词聚合、回复内容分析等 |
| B（合并继承自 B15；B15:B17） | 原值见锚点 | 教学活动/讨论 |
| D（合并继承自 D12；D12:D17） | 原值见锚点 | 教师教学活动技能 |
| C（合并继承自 C12；C12:C17） | 原值见锚点 | polymas-teacher-activity-skills |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-90297062033dcc2ab930"></a>
### entry-90297062033dcc2ab930 · polymas-teacher-agent-create

技能  - 专家整理.xlsx / 技能 / 第 18 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B18 | 场景标签 | 智能体教学/创建 |
| C18 | 技能名称 | polymas-teacher-agent-create |
| D18 | 技能中文名 | 课堂智能体创建技能 |
| E18 | 功能点序号 | 1 |
| F18 | 功能点（英文） | agent_create_api |
| G18 | 功能点（中文） | 课堂智能体创建 |
| H18 | 描述 | 创建课堂智能体：所有接口的参数定义与调用示例 |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-27167b3989d720aa6b7b"></a>
### entry-27167b3989d720aa6b7b · polymas-teacher-agent-teaching-gen

技能  - 专家整理.xlsx / 技能 / 第 19 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B19 | 场景标签 | 智能体教学/生成 |
| C19 | 技能名称 | polymas-teacher-agent-teaching-gen |
| D19 | 技能中文名 | 智能体教学生成技能 |
| E19 | 功能点序号 | 1 |
| F19 | 功能点（英文） | agent_class_generate |
| G19 | 功能点（中文） | 智能体课堂生成 |
| H19 | 描述 | 生成单个智能体课堂：抽取信息 → 定位课程/学期 → 匹配数字人 → 创建课堂 → 发布活动 → 轮询生成状态 |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-96b506799a28db39a982"></a>
### entry-96b506799a28db39a982 · polymas-teacher-agent-teaching-gen

技能  - 专家整理.xlsx / 技能 / 第 20 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| E20 | 功能点序号 | 2 |
| F20 | 功能点（英文） | agent_collection_generate |
| G20 | 功能点（中文） | 智能体课堂合集生成 |
| H20 | 描述 | 生成智能体课堂合集：创建合集 → 轮询大纲 → 编辑大纲触发稿件 → 轮询稿件 → AI生成课堂 → 展示结果 |
| D（合并继承自 D19；D19:D20） | 原值见锚点 | 智能体教学生成技能 |
| C（合并继承自 C19；C19:C20） | 原值见锚点 | polymas-teacher-agent-teaching-gen |
| B（合并继承自 B19；B19:B20） | 原值见锚点 | 智能体教学/生成 |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-fa247d550010faa5d903"></a>
### entry-fa247d550010faa5d903 · polymas-teacher-analogy-skills

技能  - 专家整理.xlsx / 技能 / 第 21 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B21 | 场景标签 | 教学辅助/概念解释 |
| C21 | 技能名称 | polymas-teacher-analogy-skills |
| D21 | 技能中文名 | 教师概念类比技能 |
| E21 | 功能点序号 | 1 |
| F21 | 功能点（英文） | concept-analogy |
| G21 | 功能点（中文） | 概念类比 |
| H21 | 描述 | 将抽象概念转化为类比、生活化例子或反例；支持自定义解释风格与目标听众群体 |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-ae0ba7955860c90b282d"></a>
### entry-ae0ba7955860c90b282d · polymas-teacher-case-skills

技能  - 专家整理.xlsx / 技能 / 第 22 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B22 | 场景标签 | 教学辅助/案例 |
| C22 | 技能名称 | polymas-teacher-case-skills |
| D22 | 技能中文名 | 教师案例生成技能 |
| E22 | 功能点序号 | 1 |
| F22 | 功能点（英文） | case-generation |
| G22 | 功能点（中文） | 教学案例生成 |
| H22 | 描述 | 根据课程内容与教学需求生成教学案例；支持商业案例、生活化案例、行业案例等类型 |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-3123c3c021270d08f2de"></a>
### entry-3123c3c021270d08f2de · polymas-teacher-class-group-assistant

技能  - 专家整理.xlsx / 技能 / 第 23 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B23 | 场景标签 | 班级群/消息 |
| C23 | 技能名称 | polymas-teacher-class-group-assistant |
| D23 | 技能中文名 | 班级群综合管理技能 |
| E23 | 功能点序号 | 1 |
| F23 | 功能点（英文） | class_group_message |
| G23 | 功能点（中文） | 班级群消息发送 |
| H23 | 描述 | 向班级群发送消息通知 |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-edc6617466eb630b450d"></a>
### entry-edc6617466eb630b450d · polymas-teacher-class-group-assistant

技能  - 专家整理.xlsx / 技能 / 第 24 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B24 | 场景标签 | 班级群/公告 |
| E24 | 功能点序号 | 2 |
| F24 | 功能点（英文） | class_group_announcement |
| G24 | 功能点（中文） | 班级群公告发布 |
| H24 | 描述 | 向班级群发布群公告 |
| D（合并继承自 D23；D23:D25） | 原值见锚点 | 班级群综合管理技能 |
| C（合并继承自 C23；C23:C25） | 原值见锚点 | polymas-teacher-class-group-assistant |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-b7f139727a646dda898f"></a>
### entry-b7f139727a646dda898f · polymas-teacher-class-group-assistant

技能  - 专家整理.xlsx / 技能 / 第 25 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B25 | 场景标签 | 班级群/管理 |
| E25 | 功能点序号 | 3 |
| F25 | 功能点（英文） | class_group_management |
| G25 | 功能点（中文） | 班级群管理 |
| H25 | 描述 | 班级群管理：入群申请审批、全员禁言/解除禁言、成员管理（添加/移除成员） |
| D（合并继承自 D23；D23:D25） | 原值见锚点 | 班级群综合管理技能 |
| C（合并继承自 C23；C23:C25） | 原值见锚点 | polymas-teacher-class-group-assistant |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-bf500ff19b644ba7b2b4"></a>
### entry-bf500ff19b644ba7b2b4 · polymas-teacher-class-group-skills

技能  - 专家整理.xlsx / 技能 / 第 26 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B26 | 场景标签 | 班级管理/分组 |
| C26 | 技能名称 | polymas-teacher-class-group-skills |
| D26 | 技能中文名 | 班级分组管理技能 |
| E26 | 功能点序号 | 1 |
| F26 | 功能点（英文） | group_plan_query |
| G26 | 功能点（中文） | 分组方案查询 |
| H26 | 描述 | 查询课程下的分组方案列表、分组方案详情、组内学生名单及未进组学生 |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-a3816b977fa53a7ab136"></a>
### entry-a3816b977fa53a7ab136 · polymas-teacher-class-group-skills

技能  - 专家整理.xlsx / 技能 / 第 27 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| E27 | 功能点序号 | 2 |
| F27 | 功能点（英文） | group_plan_create |
| G27 | 功能点（中文） | 分组方案创建 |
| H27 | 描述 | 创建随机分组、自由分组或指定分组方案，支持跨班/不可跨班配置 |
| D（合并继承自 D26；D26:D29） | 原值见锚点 | 班级分组管理技能 |
| C（合并继承自 C26；C26:C29） | 原值见锚点 | polymas-teacher-class-group-skills |
| B（合并继承自 B26；B26:B29） | 原值见锚点 | 班级管理/分组 |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-3b93f344aa3aa78064b9"></a>
### entry-3b93f344aa3aa78064b9 · polymas-teacher-class-group-skills

技能  - 专家整理.xlsx / 技能 / 第 28 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| E28 | 功能点序号 | 3 |
| F28 | 功能点（英文） | group_plan_manage |
| G28 | 功能点（中文） | 分组方案管理 |
| H28 | 描述 | 编辑或删除已有的分组方案，支持修改方案名称和简介 |
| D（合并继承自 D26；D26:D29） | 原值见锚点 | 班级分组管理技能 |
| C（合并继承自 C26；C26:C29） | 原值见锚点 | polymas-teacher-class-group-skills |
| B（合并继承自 B26；B26:B29） | 原值见锚点 | 班级管理/分组 |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-cd012e08fc351c0b8320"></a>
### entry-cd012e08fc351c0b8320 · polymas-teacher-class-group-skills

技能  - 专家整理.xlsx / 技能 / 第 29 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| E29 | 功能点序号 | 4 |
| F29 | 功能点（英文） | group_member_manage |
| G29 | 功能点（中文） | 分组成员管理 |
| H29 | 描述 | 管理分组方案内的小组和成员：调组、小组改名、小组删除、查看组内学生 |
| D（合并继承自 D26；D26:D29） | 原值见锚点 | 班级分组管理技能 |
| C（合并继承自 C26；C26:C29） | 原值见锚点 | polymas-teacher-class-group-skills |
| B（合并继承自 B26；B26:B29） | 原值见锚点 | 班级管理/分组 |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-f3f919a1d1c3d801b8cb"></a>
### entry-f3f919a1d1c3d801b8cb · polymas-teacher-class-skills

技能  - 专家整理.xlsx / 技能 / 第 30 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B30 | 场景标签 | 班级管理 |
| C30 | 技能名称 | polymas-teacher-class-skills |
| D30 | 技能中文名 | 教师班级技能 |
| E30 | 功能点序号 | 1 |
| F30 | 功能点（英文） | class_create |
| G30 | 功能点（中文） | 班级创建 |
| H30 | 描述 | 教师在课程下创建班级，支持按课程名称定位课程、输入班级名称后完成创建，创建后可按需手动添加学生并支持循环添加 |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-176e584129d00c432e07"></a>
### entry-176e584129d00c432e07 · polymas-teacher-class-skills

技能  - 专家整理.xlsx / 技能 / 第 31 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| E31 | 功能点序号 | 2 |
| F31 | 功能点（英文） | class_search |
| G31 | 功能点（中文） | 班级查询 |
| H31 | 描述 | 查询教师管理的班级信息，包括班级列表、学生明细及条件筛选，支持按课程、班级名称、学生姓名或学号过滤 |
| D（合并继承自 D30；D30:D32） | 原值见锚点 | 教师班级技能 |
| C（合并继承自 C30；C30:C32） | 原值见锚点 | polymas-teacher-class-skills |
| B（合并继承自 B30；B30:B32） | 原值见锚点 | 班级管理 |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-7a2e9390d8f33deb5546"></a>
### entry-7a2e9390d8f33deb5546 · polymas-teacher-class-skills

技能  - 专家整理.xlsx / 技能 / 第 32 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| E32 | 功能点序号 | 3 |
| F32 | 功能点（英文） | class_student_template_upload |
| G32 | 功能点（中文） | 班级学生批量导入 |
| H32 | 描述 | 教师通过 Excel 模板批量导入班级及学生名单，支持模板下载、课程定位及上传结果展示 |
| D（合并继承自 D30；D30:D32） | 原值见锚点 | 教师班级技能 |
| C（合并继承自 C30；C30:C32） | 原值见锚点 | polymas-teacher-class-skills |
| B（合并继承自 B30；B30:B32） | 原值见锚点 | 班级管理 |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-2eb7976dd287f83ff112"></a>
### entry-2eb7976dd287f83ff112 · polymas-teacher-class-student-skills

技能  - 专家整理.xlsx / 技能 / 第 33 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B33 | 场景标签 | 班级管理/学生 |
| C33 | 技能名称 | polymas-teacher-class-student-skills |
| D33 | 技能中文名 | 班级学生管理技能 |
| E33 | 功能点序号 | 1 |
| F33 | 功能点（英文） | student_query |
| G33 | 功能点（中文） | 学生查询 |
| H33 | 描述 | 按入班状态查询课程/班级下的学生信息，支持已入班、待审核、待激活三种状态路由，返回学生名单、标签、院系等数据 |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-93f6bc547b8299121797"></a>
### entry-93f6bc547b8299121797 · polymas-teacher-class-student-skills

技能  - 专家整理.xlsx / 技能 / 第 34 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| E34 | 功能点序号 | 2 |
| F34 | 功能点（英文） | enrollment_audit |
| G34 | 功能点（中文） | 入班审核 |
| H34 | 描述 | 审核入班申请：支持查看待审核列表、批量同意全部申请、忽略指定申请（需二次确认） |
| D（合并继承自 D33；D33:D37） | 原值见锚点 | 班级学生管理技能 |
| C（合并继承自 C33；C33:C37） | 原值见锚点 | polymas-teacher-class-student-skills |
| B（合并继承自 B33；B33:B37） | 原值见锚点 | 班级管理/学生 |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-61fd4d4629cbf620e6a9"></a>
### entry-61fd4d4629cbf620e6a9 · polymas-teacher-class-student-skills

技能  - 专家整理.xlsx / 技能 / 第 35 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| E35 | 功能点序号 | 3 |
| F35 | 功能点（英文） | pending_student_manage |
| G35 | 功能点（中文） | 待激活学生管理 |
| H35 | 描述 | 待激活学生管理：查看待激活学生列表，支持删除待激活学生（需二次确认） |
| D（合并继承自 D33；D33:D37） | 原值见锚点 | 班级学生管理技能 |
| C（合并继承自 C33；C33:C37） | 原值见锚点 | polymas-teacher-class-student-skills |
| B（合并继承自 B33；B33:B37） | 原值见锚点 | 班级管理/学生 |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-98953077aebcaaf5870f"></a>
### entry-98953077aebcaaf5870f · polymas-teacher-class-student-skills

技能  - 专家整理.xlsx / 技能 / 第 36 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| E36 | 功能点序号 | 4 |
| F36 | 功能点（英文） | student_transfer |
| G36 | 功能点（中文） | 学生调班退班 |
| H36 | 描述 | 学生调班/退班：调整已入班学生的班级归属，支持调班（查当前班级→查目标班级→执行调班）和退班（需二次确认） |
| D（合并继承自 D33；D33:D37） | 原值见锚点 | 班级学生管理技能 |
| C（合并继承自 C33；C33:C37） | 原值见锚点 | polymas-teacher-class-student-skills |
| B（合并继承自 B33；B33:B37） | 原值见锚点 | 班级管理/学生 |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-f3d089b8c07cf9fafcd2"></a>
### entry-f3d089b8c07cf9fafcd2 · polymas-teacher-class-student-skills

技能  - 专家整理.xlsx / 技能 / 第 37 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| E37 | 功能点序号 | 5 |
| F37 | 功能点（英文） | student_tag |
| G37 | 功能点（中文） | 学生标签管理 |
| H37 | 描述 | 学生标签管理：给学生打/改/查/删标签，支持模糊匹配已有标签（避免重复创建）、自动创建新标签、批量操作 |
| D（合并继承自 D33；D33:D37） | 原值见锚点 | 班级学生管理技能 |
| C（合并继承自 C33；C33:C37） | 原值见锚点 | polymas-teacher-class-student-skills |
| B（合并继承自 B33；B33:B37） | 原值见锚点 | 班级管理/学生 |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-189c84a9c97299162388"></a>
### entry-189c84a9c97299162388 · polymas-teacher-classroom-report-skills

技能  - 专家整理.xlsx / 技能 / 第 38 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B38 | 场景标签 | 课堂报告/数据 |
| C38 | 技能名称 | polymas-teacher-classroom-report-skills |
| D38 | 技能中文名 | 课堂报告分析技能 |
| E38 | 功能点序号 | 1 |
| F38 | 功能点（英文） | core_data_analysis |
| G38 | 功能点（中文） | 课堂核心数据分析 |
| H38 | 描述 | 课堂核心数据分析：查询课堂基本数据统计与授课方式分布 |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-d3c15d09a82b5448a7df"></a>
### entry-d3c15d09a82b5448a7df · polymas-teacher-classroom-report-skills

技能  - 专家整理.xlsx / 技能 / 第 39 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B39 | 场景标签 | 课堂报告/回顾 |
| E39 | 功能点序号 | 2 |
| F39 | 功能点（英文） | course_review |
| G39 | 功能点（中文） | 课堂核心回顾 |
| H39 | 描述 | 课堂核心回顾：查询知识导图、知识点清单和课堂摘要 |
| D（合并继承自 D38；D38:D41） | 原值见锚点 | 课堂报告分析技能 |
| C（合并继承自 C38；C38:C41） | 原值见锚点 | polymas-teacher-classroom-report-skills |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-4d92f5c8341f551167d0"></a>
### entry-4d92f5c8341f551167d0 · polymas-teacher-classroom-report-skills

技能  - 专家整理.xlsx / 技能 / 第 40 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B40 | 场景标签 | 课堂报告/互动 |
| E40 | 功能点序号 | 3 |
| F40 | 功能点（英文） | interaction_analysis |
| G40 | 功能点（中文） | 随堂互动分析 |
| H40 | 描述 | 随堂互动数据分析：查询课堂随堂互动列表与随堂测验详情 |
| D（合并继承自 D38；D38:D41） | 原值见锚点 | 课堂报告分析技能 |
| C（合并继承自 C38；C38:C41） | 原值见锚点 | polymas-teacher-classroom-report-skills |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-882504a19076b7c50e13"></a>
### entry-882504a19076b7c50e13 · polymas-teacher-classroom-report-skills

技能  - 专家整理.xlsx / 技能 / 第 41 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B41 | 场景标签 | 课堂报告/人员 |
| E41 | 功能点序号 | 4 |
| F41 | 功能点（英文） | person_overview |
| G41 | 功能点（中文） | 人员概况分析 |
| H41 | 描述 | 人员概况分析：查询课堂学生的人员概况数据，包括学生名单、班级、课堂表现分、互动次数等 |
| D（合并继承自 D38；D38:D41） | 原值见锚点 | 课堂报告分析技能 |
| C（合并继承自 C38；C38:C41） | 原值见锚点 | polymas-teacher-classroom-report-skills |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-a90d516105f5e8eaae57"></a>
### entry-a90d516105f5e8eaae57 · polymas-teacher-course-skills

技能  - 专家整理.xlsx / 技能 / 第 42 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B42 | 场景标签 | 课程管理/创建 |
| C42 | 技能名称 | polymas-teacher-course-skills |
| D42 | 技能中文名 | 教师课程技能 |
| E42 | 功能点序号 | 1 |
| F42 | 功能点（英文） | course_create |
| G42 | 功能点（中文） | 课程创建 |
| H42 | 描述 | 老师创建课程，支持邀请码建课和AI智课建课两种方式 |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-ce23d0bacf246c868138"></a>
### entry-ce23d0bacf246c868138 · polymas-teacher-course-skills

技能  - 专家整理.xlsx / 技能 / 第 43 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B43 | 场景标签 | 课程管理/查询 |
| E43 | 功能点序号 | 2 |
| F43 | 功能点（英文） | course_search |
| G43 | 功能点（中文） | 课程查询 |
| H43 | 描述 | 查询教师指定学期的课程信息，支持按学期、课程名称筛选，包括课程基本信息、课程类型、关联班级及学生数量等数据 |
| D（合并继承自 D42；D42:D43） | 原值见锚点 | 教师课程技能 |
| C（合并继承自 C42；C42:C43） | 原值见锚点 | polymas-teacher-course-skills |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-f1cd1d60a4a82e9e7657"></a>
### entry-f1cd1d60a4a82e9e7657 · polymas-teacher-exam-skills

技能  - 专家整理.xlsx / 技能 / 第 44 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B44 | 场景标签 | 考试管理/查询 |
| C44 | 技能名称 | polymas-teacher-exam-skills |
| D44 | 技能中文名 | 教师考试技能 |
| E44 | 功能点序号 | 1 |
| F44 | 功能点（英文） | exam_search |
| G44 | 功能点（中文） | 考试查询 |
| H44 | 描述 | 查询教师在课程下的考试信息，包括考试详细信息、关联班级安排、考试开始/结束时间、防作弊配置及组卷信息等数据 |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-dca01e4a86b389fbf882"></a>
### entry-dca01e4a86b389fbf882 · polymas-teacher-exam-skills

技能  - 专家整理.xlsx / 技能 / 第 45 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B45 | 场景标签 | 考试管理/创建 |
| E45 | 功能点序号 | 2 |
| F45 | 功能点（英文） | exam_create |
| G45 | 功能点（中文） | 考试创建 |
| H45 | 描述 | 教师在课程下创建考试，支持自定义考试、选题考试两种类型，涵盖班级时间、防作弊、AI批阅、教学计划关联及题库选题完整流程 |
| D（合并继承自 D44；D44:D52） | 原值见锚点 | 教师考试技能 |
| C（合并继承自 C44；C44:C52） | 原值见锚点 | polymas-teacher-exam-skills |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-d6e7cc695c9eb3e82280"></a>
### entry-d6e7cc695c9eb3e82280 · polymas-teacher-exam-skills

技能  - 专家整理.xlsx / 技能 / 第 46 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B46 | 场景标签 | 考试管理/编辑 |
| E46 | 功能点序号 | 3 |
| F46 | 功能点（英文） | exam_edit |
| G46 | 功能点（中文） | 考试编辑 |
| H46 | 描述 | 教师在课程下编辑考试，支持修改考试标题、内容、时长、总分、关联班级及起止时间等完整信息 |
| D（合并继承自 D44；D44:D52） | 原值见锚点 | 教师考试技能 |
| C（合并继承自 C44；C44:C52） | 原值见锚点 | polymas-teacher-exam-skills |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-0d5b48121240b57ec346"></a>
### entry-0d5b48121240b57ec346 · polymas-teacher-exam-skills

技能  - 专家整理.xlsx / 技能 / 第 47 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B47 | 场景标签 | 考试管理/成绩 |
| E47 | 功能点序号 | 4 |
| F47 | 功能点（英文） | exam_score_publish |
| G47 | 功能点（中文） | 考试成绩发布 |
| H47 | 描述 | 教师批量发布考试成绩，支持选择课程、考试、学生后发布成绩，并在发布后提醒未批阅考试数量 |
| D（合并继承自 D44；D44:D52） | 原值见锚点 | 教师考试技能 |
| C（合并继承自 C44；C44:C52） | 原值见锚点 | polymas-teacher-exam-skills |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-33323093b8147c026efc"></a>
### entry-33323093b8147c026efc · polymas-teacher-exam-skills

技能  - 专家整理.xlsx / 技能 / 第 48 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B48 | 场景标签 | 考试管理/催交 |
| E48 | 功能点序号 | 5 |
| F48 | 功能点（英文） | exam_urge_all |
| G48 | 功能点（中文） | 考试全部催交 |
| H48 | 描述 | 对指定考试的全部未交学生执行催交操作 |
| D（合并继承自 D44；D44:D52） | 原值见锚点 | 教师考试技能 |
| C（合并继承自 C44；C44:C52） | 原值见锚点 | polymas-teacher-exam-skills |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-4e7a9bd5d8a8730556ba"></a>
### entry-4e7a9bd5d8a8730556ba · polymas-teacher-exam-skills

技能  - 专家整理.xlsx / 技能 / 第 49 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B49 | 场景标签 | 考试管理/打回 |
| E49 | 功能点序号 | 6 |
| F49 | 功能点（英文） | exam_hit_back_all |
| G49 | 功能点（中文） | 考试全部打回 |
| H49 | 描述 | 对指定考试的全部已交学生执行打回重做操作 |
| D（合并继承自 D44；D44:D52） | 原值见锚点 | 教师考试技能 |
| C（合并继承自 C44；C44:C52） | 原值见锚点 | polymas-teacher-exam-skills |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-06cab54aaa8cff1796fd"></a>
### entry-06cab54aaa8cff1796fd · polymas-teacher-exam-skills

技能  - 专家整理.xlsx / 技能 / 第 50 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B50 | 场景标签 | 考试管理/公布 |
| E50 | 功能点序号 | 7 |
| F50 | 功能点（英文） | exam_publish_answer |
| G50 | 功能点（中文） | 公布试卷及答案 |
| H50 | 描述 | 公布试卷及答案，先检查未批阅数，再查询班级列表并执行公布 |
| D（合并继承自 D44；D44:D52） | 原值见锚点 | 教师考试技能 |
| C（合并继承自 C44；C44:C52） | 原值见锚点 | polymas-teacher-exam-skills |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-3a52d4c0e9e51090cddf"></a>
### entry-3a52d4c0e9e51090cddf · polymas-teacher-exam-skills

技能  - 专家整理.xlsx / 技能 / 第 51 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B51 | 场景标签 | 考试管理/补考 |
| E51 | 功能点序号 | 8 |
| F51 | 功能点（英文） | exam_make_up |
| G51 | 功能点（中文） | 补考创建 |
| H51 | 描述 | 教师创建补考：从已有考试出发，校验补考资格、选择补考班级和学生，确认补考配置后创建补考 |
| D（合并继承自 D44；D44:D52） | 原值见锚点 | 教师考试技能 |
| C（合并继承自 C44；C44:C52） | 原值见锚点 | polymas-teacher-exam-skills |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-ff53452f03d5955176a7"></a>
### entry-ff53452f03d5955176a7 · polymas-teacher-exam-skills

技能  - 专家整理.xlsx / 技能 / 第 52 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B52 | 场景标签 | 考试管理/辅助 |
| E52 | 功能点序号 | 9 |
| F52 | 功能点（英文） | term_selection |
| G52 | 功能点（中文） | 学期选择 |
| H52 | 描述 | 学期选择可复用模板 — 在执行技能业务逻辑前确定全局学期编号，支持用户指定学期、当前学期自动探测、学期列表选择三种路径 |
| D（合并继承自 D44；D44:D52） | 原值见锚点 | 教师考试技能 |
| C（合并继承自 C44；C44:C52） | 原值见锚点 | polymas-teacher-exam-skills |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-a5c7909392d645004140"></a>
### entry-a5c7909392d645004140 · polymas-teacher-file-import-questions

技能  - 专家整理.xlsx / 技能 / 第 53 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B53 | 场景标签 | 出题/文件导题 |
| C53 | 技能名称 | polymas-teacher-file-import-questions |
| D53 | 技能中文名 | 教师文件导题技能 |
| E53 | 功能点序号 | 1 |
| F53 | 功能点（英文） | file_import_questions |
| G53 | 功能点（中文） | 文件导题 |
| H53 | 描述 | 教师文件导题技能：上传试卷文件（支持PDF、DOC、DOCX、PNG、JPG、JPEG、XLS、XLSX，单文件≤500MB），AI解析提取题目，逐题确认后导入题库 |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-291b9c4c3bf194e37188"></a>
### entry-291b9c4c3bf194e37188 · polymas-student-basic-skills

技能  - 专家整理.xlsx / 技能 / 第 54 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B54 | 场景标签 | 学生班课 |
| C54 | 技能名称 | polymas-student-basic-skills |
| D54 | 技能中文名 | 学生班课查询助手 |
| E54 | 功能点序号 | 1 |
| F54 | 功能点（英文） | course_search |
| G54 | 功能点（中文） | 课程查询 |
| H54 | 描述 | 学生基础技能：根据用户需求智能选择课程搜索和作业查询功能 |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-2eab479050c64de785eb"></a>
### entry-2eab479050c64de785eb · polymas-student-basic-skills

技能  - 专家整理.xlsx / 技能 / 第 55 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B55 | 场景标签 | 学生班课 |
| C55 | 技能名称 | polymas-student-basic-skills |
| D55 | 技能中文名 | 学生班课查询助手 |
| E55 | 功能点序号 | 2 |
| F55 | 功能点（英文） | homework_query |
| G55 | 功能点（中文） | 作业查询 |
| H55 | 描述 | 学生基础技能：根据用户需求智能选择课程搜索和作业查询功能 |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-2d273457ae6cd3fea8a3"></a>
### entry-2d273457ae6cd3fea8a3 · polymas-get-student-course-homework

技能  - 专家整理.xlsx / 技能 / 第 56 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B56 | 场景标签 | 学生作业 |
| C56 | 技能名称 | polymas-get-student-course-homework |
| D56 | 技能中文名 | 学生作业管理助手 |
| E56 | 功能点序号 | 1 |
| F56 | 功能点（英文） | homework_query |
| G56 | 功能点（中文） | 作业查询 |
| H56 | 描述 | 查询学生在课程下的所有作业信息，包括作业详细信息、作业关联班级信息、班级作业结束时间、完成率统计等数据。 |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-f83e21c59ffc638e6975"></a>
### entry-f83e21c59ffc638e6975 · polymas-teacher-homework-detail-skills

技能  - 专家整理.xlsx / 技能 / 第 57 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B57 | 场景标签 | 作业详情/考试 |
| C57 | 技能名称 | polymas-teacher-homework-detail-skills |
| D57 | 技能中文名 | 教师作业详情技能 |
| E57 | 功能点序号 | 1 |
| F57 | 功能点（英文） | exam_homework_detail |
| G57 | 功能点（中文） | 考试作业详情分析 |
| H57 | 描述 | 教师查看考试作业详情与学情分析，包括考试基本信息、成绩统计、分段人数及各班级对比数据 |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-f57057e3d437d10ac84d"></a>
### entry-f57057e3d437d10ac84d · polymas-teacher-homework-detail-skills

技能  - 专家整理.xlsx / 技能 / 第 58 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B58 | 场景标签 | 作业详情/作业 |
| E58 | 功能点序号 | 2 |
| F58 | 功能点（英文） | question_homework_detail |
| G58 | 功能点（中文） | 作业详情分析 |
| H58 | 描述 | 教师查看作业详情与学情分析，包括作业基本信息、成绩概览、高频错题诊断和预警学生名单 |
| D（合并继承自 D57；D57:D61） | 原值见锚点 | 教师作业详情技能 |
| C（合并继承自 C57；C57:C61） | 原值见锚点 | polymas-teacher-homework-detail-skills |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-9cbb59b4f5add52caeb9"></a>
### entry-9cbb59b4f5add52caeb9 · polymas-teacher-homework-detail-skills

技能  - 专家整理.xlsx / 技能 / 第 59 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B59 | 场景标签 | 作业详情/完成 |
| E59 | 功能点序号 | 3 |
| F59 | 功能点（英文） | exam_completion_detail |
| G59 | 功能点（中文） | 考试完成情况 |
| H59 | 描述 | 教师查看考试完成情况，包括提交/审核统计和各状态学生列表 |
| D（合并继承自 D57；D57:D61） | 原值见锚点 | 教师作业详情技能 |
| C（合并继承自 C57；C57:C61） | 原值见锚点 | polymas-teacher-homework-detail-skills |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-b730870d67573957d09f"></a>
### entry-b730870d67573957d09f · polymas-teacher-homework-detail-skills

技能  - 专家整理.xlsx / 技能 / 第 60 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B60 | 场景标签 | 作业详情/完成 |
| E60 | 功能点序号 | 4 |
| F60 | 功能点（英文） | homework_completion_detail |
| G60 | 功能点（中文） | 作业完成情况 |
| H60 | 描述 | 教师查看作业完成情况，包括批阅统计和各状态学生列表 |
| D（合并继承自 D57；D57:D61） | 原值见锚点 | 教师作业详情技能 |
| C（合并继承自 C57；C57:C61） | 原值见锚点 | polymas-teacher-homework-detail-skills |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-1353dafabc09ff99d344"></a>
### entry-1353dafabc09ff99d344 · polymas-teacher-homework-detail-skills

技能  - 专家整理.xlsx / 技能 / 第 61 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B61 | 场景标签 | 作业详情/题库 |
| E61 | 功能点序号 | 5 |
| F61 | 功能点（英文） | question_bank_detail |
| G61 | 功能点（中文） | 训练题库详情 |
| H61 | 描述 | 教师查看训练题库详情，包括题库摘要、完成率分布、易错知识点和学生答题详情 |
| D（合并继承自 D57；D57:D61） | 原值见锚点 | 教师作业详情技能 |
| C（合并继承自 C57；C57:C61） | 原值见锚点 | polymas-teacher-homework-detail-skills |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-f0638be9079d85c517c6"></a>
### entry-f0638be9079d85c517c6 · polymas-teacher-homework-skills

技能  - 专家整理.xlsx / 技能 / 第 62 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B62 | 场景标签 | 作业管理/查询 |
| C62 | 技能名称 | polymas-teacher-homework-skills |
| D62 | 技能中文名 | 教师作业技能 |
| E62 | 功能点序号 | 1 |
| F62 | 功能点（英文） | homework_search |
| G62 | 功能点（中文） | 作业查询 |
| H62 | 描述 | 查询教师在课程下的作业信息，包括作业详细信息、作业关联班级信息、班级作业结束时间、完成率统计等数据 |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-3b10a9837a33174f6a45"></a>
### entry-3b10a9837a33174f6a45 · polymas-teacher-homework-skills

技能  - 专家整理.xlsx / 技能 / 第 63 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B63 | 场景标签 | 作业管理/分析 |
| E63 | 功能点序号 | 2 |
| F63 | 功能点（英文） | homework_analysis |
| G63 | 功能点（中文） | 作业分析 |
| H63 | 描述 | 教师按课程、作业查看作业学情分析报告，包括成绩概览、高频错题、预警学生等数据 |
| D（合并继承自 D62；D62:D77） | 原值见锚点 | 教师作业技能 |
| C（合并继承自 C62；C62:C77） | 原值见锚点 | polymas-teacher-homework-skills |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-651e0464c95a6fde0591"></a>
### entry-651e0464c95a6fde0591 · polymas-teacher-homework-skills

技能  - 专家整理.xlsx / 技能 / 第 64 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B64 | 场景标签 | 作业管理/交流 |
| E64 | 功能点序号 | 3 |
| F64 | 功能点（英文） | homework_chat_query |
| G64 | 功能点（中文） | 作业交流查询 |
| H64 | 描述 | 教师查看作业下学生与教师的互动交流记录，支持分页展示和嵌套回复浏览 |
| D（合并继承自 D62；D62:D77） | 原值见锚点 | 教师作业技能 |
| C（合并继承自 C62；C62:C77） | 原值见锚点 | polymas-teacher-homework-skills |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-bfb6217987eb553ac75a"></a>
### entry-bfb6217987eb553ac75a · polymas-teacher-homework-skills

技能  - 专家整理.xlsx / 技能 / 第 65 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B65 | 场景标签 | 作业管理/催交 |
| E65 | 功能点序号 | 4 |
| F65 | 功能点（英文） | homework_urge |
| G65 | 功能点（中文） | 作业催交 |
| H65 | 描述 | 教师催促作业下未提交作业的学生，支持按课程、作业、学生等条件精确筛选待催交学生并批量发送催交通知 |
| D（合并继承自 D62；D62:D77） | 原值见锚点 | 教师作业技能 |
| C（合并继承自 C62；C62:C77） | 原值见锚点 | polymas-teacher-homework-skills |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-59c19bb3bdf15e989e67"></a>
### entry-59c19bb3bdf15e989e67 · polymas-teacher-homework-skills

技能  - 专家整理.xlsx / 技能 / 第 66 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B66 | 场景标签 | 作业管理/打回 |
| E66 | 功能点序号 | 5 |
| F66 | 功能点（英文） | homework_hit_back |
| G66 | 功能点（中文） | 作业打回 |
| H66 | 描述 | 教师按课程、作业、班级、学号等条件筛选已提交学生，批量打回学生作业 |
| D（合并继承自 D62；D62:D77） | 原值见锚点 | 教师作业技能 |
| C（合并继承自 C62；C62:C77） | 原值见锚点 | polymas-teacher-homework-skills |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-a428c5134e4240d08c5c"></a>
### entry-a428c5134e4240d08c5c · polymas-teacher-homework-skills

技能  - 专家整理.xlsx / 技能 / 第 67 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B67 | 场景标签 | 作业管理/创建 |
| E67 | 功能点序号 | 6 |
| F67 | 功能点（英文） | homework_create |
| G67 | 功能点（中文） | 作业创建 |
| H67 | 描述 | 教师在课程下创建作业，支持设置作业名称、描述、总分、关联班级及起止时间等完整信息 |
| D（合并继承自 D62；D62:D77） | 原值见锚点 | 教师作业技能 |
| C（合并继承自 C62；C62:C77） | 原值见锚点 | polymas-teacher-homework-skills |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-ae6879721d3c8ee58983"></a>
### entry-ae6879721d3c8ee58983 · polymas-teacher-homework-skills

技能  - 专家整理.xlsx / 技能 / 第 68 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B68 | 场景标签 | 作业管理/创建 |
| E68 | 功能点序号 | 7 |
| F68 | 功能点（英文） | homework_create_question |
| G68 | 功能点（中文） | 题库选题创建作业 |
| H68 | 描述 | 教师从题库选题创建作业，支持查询题目、选题保存、设置分数、发布完整流程。 |
| D（合并继承自 D62；D62:D77） | 原值见锚点 | 教师作业技能 |
| C（合并继承自 C62；C62:C77） | 原值见锚点 | polymas-teacher-homework-skills |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-fda73c525a207c04f586"></a>
### entry-fda73c525a207c04f586 · polymas-teacher-homework-skills

技能  - 专家整理.xlsx / 技能 / 第 69 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B69 | 场景标签 | 作业管理/发布 |
| E69 | 功能点序号 | 8 |
| F69 | 功能点（英文） | homework_publish |
| G69 | 功能点（中文） | 作业发布 |
| H69 | 描述 | 发布教师创建的作业到指定班级，使作业对学生可见。 |
| D（合并继承自 D62；D62:D77） | 原值见锚点 | 教师作业技能 |
| C（合并继承自 C62；C62:C77） | 原值见锚点 | polymas-teacher-homework-skills |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-acc04004cb5b12dfbf01"></a>
### entry-acc04004cb5b12dfbf01 · polymas-teacher-homework-skills

技能  - 专家整理.xlsx / 技能 / 第 70 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B70 | 场景标签 | 作业管理/编辑 |
| E70 | 功能点序号 | 9 |
| F70 | 功能点（英文） | homework_edit |
| G70 | 功能点（中文） | 作业编辑 |
| H70 | 描述 | 教师在课程下编辑作业，支持设置作业名称、描述、总分、关联班级及起止时间、提交规则等完整信息 |
| D（合并继承自 D62；D62:D77） | 原值见锚点 | 教师作业技能 |
| C（合并继承自 C62；C62:C77） | 原值见锚点 | polymas-teacher-homework-skills |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-374f7987d0885a715099"></a>
### entry-374f7987d0885a715099 · polymas-teacher-homework-skills

技能  - 专家整理.xlsx / 技能 / 第 71 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B71 | 场景标签 | 作业管理/成绩 |
| E71 | 功能点序号 | 10 |
| F71 | 功能点（英文） | homework_score_publish |
| G71 | 功能点（中文） | 作业成绩发布 |
| H71 | 描述 | 教师批量发布作业成绩，支持选择课程、作业、学生后发布成绩，并在发布后提醒未批阅作业数量 |
| D（合并继承自 D62；D62:D77） | 原值见锚点 | 教师作业技能 |
| C（合并继承自 C62；C62:C77） | 原值见锚点 | polymas-teacher-homework-skills |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-cd81223a0a8c7a7bc357"></a>
### entry-cd81223a0a8c7a7bc357 · polymas-teacher-homework-skills

技能  - 专家整理.xlsx / 技能 / 第 72 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B72 | 场景标签 | 作业管理/审批 |
| E72 | 功能点序号 | 11 |
| F72 | 功能点（英文） | homework_redo_approving |
| G72 | 功能点（中文） | 重做申请审批 |
| H72 | 描述 | 教师审批学生的重做申请，支持查看申请列表、批量通过或驳回重做申请 |
| D（合并继承自 D62；D62:D77） | 原值见锚点 | 教师作业技能 |
| C（合并继承自 C62；C62:C77） | 原值见锚点 | polymas-teacher-homework-skills |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-fdbba7cfa6878e8ebcf8"></a>
### entry-fdbba7cfa6878e8ebcf8 · polymas-teacher-homework-skills

技能  - 专家整理.xlsx / 技能 / 第 73 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B73 | 场景标签 | 作业管理/模版 |
| E73 | 功能点序号 | 12 |
| F73 | 功能点（英文） | homework_template_save |
| G73 | 功能点（中文） | 作业模版保存 |
| H73 | 描述 | 教师将已有作业保存为个人模版，便于下学期复用 |
| D（合并继承自 D62；D62:D77） | 原值见锚点 | 教师作业技能 |
| C（合并继承自 C62；C62:C77） | 原值见锚点 | polymas-teacher-homework-skills |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-65d5b6cf8ef4db87c158"></a>
### entry-65d5b6cf8ef4db87c158 · polymas-teacher-homework-skills

技能  - 专家整理.xlsx / 技能 / 第 74 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B74 | 场景标签 | 作业管理/模版 |
| E74 | 功能点序号 | 13 |
| F74 | 功能点（英文） | homework_template_use |
| G74 | 功能点（中文） | 作业模版使用 |
| H74 | 描述 | 教师使用已有模版创建作业并发布到指定班级 |
| D（合并继承自 D62；D62:D77） | 原值见锚点 | 教师作业技能 |
| C（合并继承自 C62；C62:C77） | 原值见锚点 | polymas-teacher-homework-skills |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-7308380659854dc9b39e"></a>
### entry-7308380659854dc9b39e · polymas-teacher-homework-skills

技能  - 专家整理.xlsx / 技能 / 第 75 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B75 | 场景标签 | 作业管理/辅助 |
| E75 | 功能点序号 | 14 |
| F75 | 功能点（英文） | current_term_query |
| G75 | 功能点（中文） | 当前学期查询 |
| H75 | 描述 | 查询指定课程当前学期信息，获取学期名称和学期代码。 |
| D（合并继承自 D62；D62:D77） | 原值见锚点 | 教师作业技能 |
| C（合并继承自 C62；C62:C77） | 原值见锚点 | polymas-teacher-homework-skills |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-046cbacd80d995de6b78"></a>
### entry-046cbacd80d995de6b78 · polymas-teacher-homework-skills

技能  - 专家整理.xlsx / 技能 / 第 76 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B76 | 场景标签 | 作业管理/辅助 |
| E76 | 功能点序号 | 15 |
| F76 | 功能点（英文） | term_selection |
| G76 | 功能点（中文） | 学期选择 |
| H76 | 描述 | 学期选择可复用模板 — 在执行技能业务逻辑前确定全局学期编号，支持用户指定学期、当前学期自动探测、学期列表选择三种路径 |
| D（合并继承自 D62；D62:D77） | 原值见锚点 | 教师作业技能 |
| C（合并继承自 C62；C62:C77） | 原值见锚点 | polymas-teacher-homework-skills |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-4b1b77e70243c9ec3ee7"></a>
### entry-4b1b77e70243c9ec3ee7 · polymas-teacher-homework-skills

技能  - 专家整理.xlsx / 技能 / 第 77 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B77 | 场景标签 | 作业管理/辅助 |
| E77 | 功能点序号 | 16 |
| F77 | 功能点（英文） | agent_selection_guide |
| G77 | 功能点（中文） | AI智能体选择指南 |
| H77 | 描述 | 作业创建时 AI 批阅/查重 Agent 的选择与配置说明，通过 agentList 接口按 sTag 区分智能体类型 |
| D（合并继承自 D62；D62:D77） | 原值见锚点 | 教师作业技能 |
| C（合并继承自 C62；C62:C77） | 原值见锚点 | polymas-teacher-homework-skills |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-355b16e4fd76481787ac"></a>
### entry-355b16e4fd76481787ac · polymas-teacher-knowledge-distillation

技能  - 专家整理.xlsx / 技能 / 第 78 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B78 | 场景标签 | 知识管理/蒸馏 |
| C78 | 技能名称 | polymas-teacher-knowledge-distillation |
| D78 | 技能中文名 | 个人知识蒸馏技能 |
| E78 | 功能点序号 | 1 |
| F78 | 功能点（英文） | knowledge_distillation |
| G78 | 功能点（中文） | 个人知识蒸馏 |
| H78 | 描述 | 个人知识蒸馏：对话中接收教师经验/规则文本，存入'我的知识库'供智能体对话引用 |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-47ca9f18666ade3cbae1"></a>
### entry-47ca9f18666ade3cbae1 · polymas-teacher-knowledge-graph

技能  - 专家整理.xlsx / 技能 / 第 79 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B79 | 场景标签 | 知识管理/图谱 |
| C79 | 技能名称 | polymas-teacher-knowledge-graph |
| D79 | 技能中文名 | 知识图谱查询技能 |
| E79 | 功能点序号 | 1 |
| F79 | 功能点（英文） | knowledge_graph |
| G79 | 功能点（中文） | 知识图谱查询 |
| H79 | 描述 | 知识图谱查询：查三谱（知识/问题/能力）结构与统计 |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-eb1bad41db0f578e8138"></a>
### entry-eb1bad41db0f578e8138 · polymas-teacher-learning-analytics-skills

技能  - 专家整理.xlsx / 技能 / 第 80 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B80 | 场景标签 | 学情分析/综合 |
| C80 | 技能名称 | polymas-teacher-learning-analytics-skills |
| D80 | 技能中文名 | 全平台学情分析技能 |
| E80 | 功能点序号 | 1 |
| F80 | 功能点（英文） | student_learning_view |
| G80 | 功能点（中文） | 学生综合学情视图 |
| H80 | 描述 | 将单个学生的作业完成率、考试成绩、课堂互动次数整合到一起，给出综合视图 |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-8bc4582c2394fd92cbbf"></a>
### entry-8bc4582c2394fd92cbbf · polymas-teacher-learning-analytics-skills

技能  - 专家整理.xlsx / 技能 / 第 81 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B81 | 场景标签 | 学情分析/综合 |
| E81 | 功能点序号 | 2 |
| F81 | 功能点（英文） | class_comparison |
| G81 | 功能点（中文） | 班级横向对比 |
| H81 | 描述 | 将多个班级的出勤、作业提交、成绩数据汇总到一张表里，进行横向对比 |
| D（合并继承自 D80；D80:D82） | 原值见锚点 | 全平台学情分析技能 |
| C（合并继承自 C80；C80:C82） | 原值见锚点 | polymas-teacher-learning-analytics-skills |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-9ccd79ab10959f00756f"></a>
### entry-9ccd79ab10959f00756f · polymas-teacher-learning-analytics-skills

技能  - 专家整理.xlsx / 技能 / 第 82 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B82 | 场景标签 | 学情分析/综合 |
| E82 | 功能点序号 | 3 |
| F82 | 功能点（英文） | semester_report |
| G82 | 功能点（中文） | 学期学情报告 |
| H82 | 描述 | 将作业、测验、讨论、出勤这几类数据都拉出来，整合成一份完整的学期学情报告 |
| D（合并继承自 D80；D80:D82） | 原值见锚点 | 全平台学情分析技能 |
| C（合并继承自 C80；C80:C82） | 原值见锚点 | polymas-teacher-learning-analytics-skills |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-85edeca98d49dad781a5"></a>
### entry-85edeca98d49dad781a5 · polymas-teacher-lession-analysis

技能  - 专家整理.xlsx / 技能 / 第 83 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B83 | 场景标签 | lession-analysis |
| C83 | 技能名称 | polymas-teacher-lession-analysis |
| D83 | 技能中文名 | 课堂表现分析技能 |
| E83 | 功能点序号 | 1 |
| F83 | 功能点（英文） | lession_analysis |
| G83 | 功能点（中文） | 课堂表现分析 |
| H83 | 描述 | 按课程、课堂查看学生课堂表现：成绩得分、互动参与、弹幕次数、在线时长；支持分页 |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-1ea9c56aeec5254f8ce0"></a>
### entry-1ea9c56aeec5254f8ce0 · polymas-teacher-lession-analysis

技能  - 专家整理.xlsx / 技能 / 第 84 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B84 | 场景标签 | 课堂分析 |
| E84 | 功能点序号 | 2 |
| F84 | 功能点（英文） | pause_confirmation_rules |
| G84 | 功能点（中文） | 暂停确认规则 |
| H84 | 描述 | 当 步骤返回结果数量超过阈值时，必须暂停执行，向用户展示候选列表并等待确认后再继续。 |
| D（合并继承自 D83；D83:D84） | 原值见锚点 | 课堂表现分析技能 |
| C（合并继承自 C83；C83:C84） | 原值见锚点 | polymas-teacher-lession-analysis |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-7c249410d361a2dcbc68"></a>
### entry-7c249410d361a2dcbc68 · polymas-teacher-preparation-management

技能  - 专家整理.xlsx / 技能 / 第 85 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B85 | 场景标签 | 备课管理 |
| C85 | 技能名称 | polymas-teacher-preparation-management |
| D85 | 技能中文名 | 备课管理技能 |
| E85 | 功能点序号 | 1 |
| F85 | 功能点（英文） | preparation_management |
| G85 | 功能点（中文） | 备课管理 |
| H85 | 描述 | 备课管理：新建/复制/删除/同步备课课次 |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-57ed3a3a4667fab8f357"></a>
### entry-57ed3a3a4667fab8f357 · polymas-teacher-problem-skills

技能  - 专家整理.xlsx / 技能 / 第 86 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B86 | 场景标签 | 出题/题库 |
| C86 | 技能名称 | polymas-teacher-problem-skills |
| D86 | 技能中文名 | 教师AI出题技能 |
| E86 | 功能点序号 | 1 |
| F86 | 功能点（英文） | problem_generate |
| G86 | 功能点（中文） | AI出题 |
| H86 | 描述 | 教师出题技能：根据知识点、难度、题型等要求，通过 AI 自动生成题目并保存到题库 |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-bcea28594dfc2a45589f"></a>
### entry-bcea28594dfc2a45589f · polymas-teacher-questions-query

技能  - 专家整理.xlsx / 技能 / 第 87 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C87 | 技能名称 | polymas-teacher-questions-query |
| D87 | 技能中文名 | 教师题库技能 |
| E87 | 功能点序号 | 1 |
| F87 | 功能点（英文） | question_search |
| G87 | 功能点（中文） | 题库资源查询 |
| H87 | 描述 | 查询教师的题库资源与题目信息，包括课程题库和个人题库分类、题目详情（题干、题型、选项、答案）等数据 |
| B（合并继承自 B86；B86:B88） | 原值见锚点 | 出题/题库 |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-e6f9f9b1d491876f0e38"></a>
### entry-e6f9f9b1d491876f0e38 · polymas-teacher-questions-query

技能  - 专家整理.xlsx / 技能 / 第 88 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| E88 | 功能点序号 | 2 |
| F88 | 功能点（英文） | question_excel_upload |
| G88 | 功能点（中文） | Excel批量导题 |
| H88 | 描述 | 通过Excel文件批量导入题目至题库，包括模板下载、上传文件、解析题目、导入题库的完整流程 |
| D（合并继承自 D87；D87:D88） | 原值见锚点 | 教师题库技能 |
| C（合并继承自 C87；C87:C88） | 原值见锚点 | polymas-teacher-questions-query |
| B（合并继承自 B86；B86:B88） | 原值见锚点 | 出题/题库 |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-f720324a512b1f10f24c"></a>
### entry-f720324a512b1f10f24c · polymas-teacher-questions-query

技能  - 专家整理.xlsx / 技能 / 第 89 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B89 | 场景标签 | 出题/题库查询 |
| C89 | 技能名称 | polymas-teacher-questions-query |
| D89 | 技能中文名 | 教师题库查询技能 |
| E89 | 功能点序号 | 1 |
| F89 | 功能点（英文） | questions_query |
| G89 | 功能点（中文） | 题库查询 |
| H89 | 描述 | 教师题库查询技能：查询题库题目数量、分布、具体题目，支持按题型/难度/知识点/标签/来源等多维度筛选 |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-29049897aa6d25de116d"></a>
### entry-29049897aa6d25de116d · polymas-teacher-resource-skills

技能  - 专家整理.xlsx / 技能 / 第 90 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B90 | 场景标签 | 资源管理/知识库 |
| C90 | 技能名称 | polymas-teacher-resource-skills |
| D90 | 技能中文名 | 教师资源技能 |
| E90 | 功能点序号 | 1 |
| F90 | 功能点（英文） | knowledge_search |
| G90 | 功能点（中文） | 知识库搜索 |
| H90 | 描述 | 仅用于查询/搜索教师知识库内容，包括标题、资源类型、资源封面、资源链接、资源预览图标、资源名称、资源摘要。不支持新增、编辑、删除、上传、下载等操作。 |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-7e94c7090002a395a0da"></a>
### entry-7e94c7090002a395a0da · polymas-teacher-resource-skills

技能  - 专家整理.xlsx / 技能 / 第 91 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B91 | 场景标签 | 资源管理/文件 |
| E91 | 功能点序号 | 2 |
| F91 | 功能点（英文） | resource_file_search |
| G91 | 功能点（中文） | 资源库文件搜索 |
| H91 | 描述 | 仅用于查询/搜索资源库中的教师文件，包括文件标题、文件后缀、文件大小、文件地址、创建/更新时间。不支持上传、删除、下载等操作。 |
| D（合并继承自 D90；D90:D96） | 原值见锚点 | 教师资源技能 |
| C（合并继承自 C90；C90:C96） | 原值见锚点 | polymas-teacher-resource-skills |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-84cdc61c50a5c915c206"></a>
### entry-84cdc61c50a5c915c206 · polymas-teacher-resource-skills

技能  - 专家整理.xlsx / 技能 / 第 92 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| E92 | 功能点序号 | 3 |
| F92 | 功能点（英文） | resource_file_upload |
| G92 | 功能点（中文） | 资源库文件上传 |
| H92 | 描述 | 将本地文件或URL文件上传至教师的课程资源库。当用户未指定课程时，自动搜索关联课程并由用户确认后再上传。 |
| B（合并继承自 B91；B91:B96） | 原值见锚点 | 资源管理/文件 |
| D（合并继承自 D90；D90:D96） | 原值见锚点 | 教师资源技能 |
| C（合并继承自 C90；C90:C96） | 原值见锚点 | polymas-teacher-resource-skills |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-e681d89ecfdce56a5eda"></a>
### entry-e681d89ecfdce56a5eda · polymas-teacher-resource-skills

技能  - 专家整理.xlsx / 技能 / 第 93 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| E93 | 功能点序号 | 4 |
| F93 | 功能点（英文） | file_location_finder |
| G93 | 功能点（中文） | 文件路径定位 |
| H93 | 描述 | 该技能，支持个人/团队/课程资源库三种类型。返回文件所在文件夹的完整路径链和路径字符串。 |
| B（合并继承自 B91；B91:B96） | 原值见锚点 | 资源管理/文件 |
| D（合并继承自 D90；D90:D96） | 原值见锚点 | 教师资源技能 |
| C（合并继承自 C90；C90:C96） | 原值见锚点 | polymas-teacher-resource-skills |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-32d255cd17e2d0934f75"></a>
### entry-32d255cd17e2d0934f75 · polymas-teacher-resource-skills

技能  - 专家整理.xlsx / 技能 / 第 94 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| E94 | 功能点序号 | 5 |
| F94 | 功能点（英文） | resource_file_search_with_folder |
| G94 | 功能点（中文） | 资源库文件搜索V2 |
| H94 | 描述 | 该技能，不支持文件的增删改操作。 |
| B（合并继承自 B91；B91:B96） | 原值见锚点 | 资源管理/文件 |
| D（合并继承自 D90；D90:D96） | 原值见锚点 | 教师资源技能 |
| C（合并继承自 C90；C90:C96） | 原值见锚点 | polymas-teacher-resource-skills |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-3084c11d63493bbf0289"></a>
### entry-3084c11d63493bbf0289 · polymas-teacher-resource-skills

技能  - 专家整理.xlsx / 技能 / 第 95 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| E95 | 功能点序号 | 6 |
| F95 | 功能点（英文） | resource_file_upload_with_folder |
| G95 | 功能点（中文） | 资源库文件上传V2 |
| H95 | 描述 | 该技能，支持本地文件路径和网络URL两种方式上传。此外，该技能提供了上传前的重名检测和自动处理机制。 |
| B（合并继承自 B91；B91:B96） | 原值见锚点 | 资源管理/文件 |
| D（合并继承自 D90；D90:D96） | 原值见锚点 | 教师资源技能 |
| C（合并继承自 C90；C90:C96） | 原值见锚点 | polymas-teacher-resource-skills |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-09d8c172f6be27a44647"></a>
### entry-09d8c172f6be27a44647 · polymas-teacher-resource-skills

技能  - 专家整理.xlsx / 技能 / 第 96 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| E96 | 功能点序号 | 7 |
| F96 | 功能点（英文） | search_file_in_all_libraries |
| G96 | 功能点（中文） | 跨库文件查找 |
| H96 | 描述 | 该工具支持在中同时进行递归文件查找，返回文件的完整路径和位置信息。 |
| B（合并继承自 B91；B91:B96） | 原值见锚点 | 资源管理/文件 |
| D（合并继承自 D90；D90:D96） | 原值见锚点 | 教师资源技能 |
| C（合并继承自 C90；C90:C96） | 原值见锚点 | polymas-teacher-resource-skills |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-9f7966ff74921ebccf12"></a>
### entry-9f7966ff74921ebccf12 · polymas-teacher-score-skills

技能  - 专家整理.xlsx / 技能 / 第 97 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B97 | 场景标签 | 成绩管理/查询 |
| C97 | 技能名称 | polymas-teacher-score-skills |
| D97 | 技能中文名 | 教师成绩技能 |
| E97 | 功能点序号 | 1 |
| F97 | 功能点（英文） | score_grade_query |
| G97 | 功能点（中文） | 多维成绩查询 |
| H97 | 描述 | 教师多维成绩查询：总成绩 / 考勤 / 平时 / 作业 / 考试 / 自定义考核项，支持个人与班级分布两种视角 |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-84039e8202917df8dead"></a>
### entry-84039e8202917df8dead · polymas-teacher-score-skills

技能  - 专家整理.xlsx / 技能 / 第 98 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B98 | 场景标签 | 成绩管理/配置 |
| E98 | 功能点序号 | 2 |
| F98 | 功能点（英文） | score_setting |
| G98 | 功能点（中文） | 成绩权重配置 |
| H98 | 描述 | 教师成绩加权设置（服务端持久化）：四项权重、缺勤扣分、互动计分、应用到其他班级、学生查看开关、最终成绩设置 |
| D（合并继承自 D97；D97:D104） | 原值见锚点 | 教师成绩技能 |
| C（合并继承自 C97；C97:C104） | 原值见锚点 | polymas-teacher-score-skills |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-f877074a695241719b2b"></a>
### entry-f877074a695241719b2b · polymas-teacher-score-skills

技能  - 专家整理.xlsx / 技能 / 第 99 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B99 | 场景标签 | 成绩管理/考勤 |
| E99 | 功能点序号 | 3 |
| F99 | 功能点（英文） | score_attendance |
| G99 | 功能点（中文） | 线下考勤管理 |
| H99 | 描述 | 教师线下考勤全生命周期：查询考勤列表、录入一次考勤、修改考勤（改为已签/未签）、删除本次考勤 |
| D（合并继承自 D97；D97:D104） | 原值见锚点 | 教师成绩技能 |
| C（合并继承自 C97；C97:C104） | 原值见锚点 | polymas-teacher-score-skills |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-7500281ae97b69f77785"></a>
### entry-7500281ae97b69f77785 · polymas-teacher-score-skills

技能  - 专家整理.xlsx / 技能 / 第 100 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B100 | 场景标签 | 成绩管理/录入 |
| E100 | 功能点序号 | 4 |
| F100 | 功能点（英文） | score_offline |
| G100 | 功能点（中文） | 线下成绩录入 |
| H100 | 描述 | 教师线下成绩（考试/作业）全生命周期：增/改/删、Excel 模板导入、导入结果查询 |
| I100 | 未命名列 I | 没有到应用广场 |
| D（合并继承自 D97；D97:D104） | 原值见锚点 | 教师成绩技能 |
| C（合并继承自 C97；C97:C104） | 原值见锚点 | polymas-teacher-score-skills |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-a9c4c1b945efa053a794"></a>
### entry-a9c4c1b945efa053a794 · polymas-teacher-score-skills

技能  - 专家整理.xlsx / 技能 / 第 101 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B101 | 场景标签 | 成绩管理/导出 |
| E101 | 功能点序号 | 5 |
| F101 | 功能点（英文） | score_export |
| G101 | 功能点（中文） | 成绩导出 |
| H101 | 描述 | 教师发起成绩异步导出 + 查询下载中心获取文件 URL |
| D（合并继承自 D97；D97:D104） | 原值见锚点 | 教师成绩技能 |
| C（合并继承自 C97；C97:C104） | 原值见锚点 | polymas-teacher-score-skills |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-a60871d3a197d6c39c7c"></a>
### entry-a60871d3a197d6c39c7c · polymas-teacher-score-skills

技能  - 专家整理.xlsx / 技能 / 第 102 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B102 | 场景标签 | 成绩管理/计算 |
| E102 | 功能点序号 | 6 |
| F102 | 功能点（英文） | score_calculation |
| G102 | 功能点（中文） | 成绩加权计算 |
| H102 | 描述 | 教师按自定义权重计算每个学生的汇总成绩，支持作业与考试成绩加权计算 |
| D（合并继承自 D97；D97:D104） | 原值见锚点 | 教师成绩技能 |
| C（合并继承自 C97；C97:C104） | 原值见锚点 | polymas-teacher-score-skills |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-8165dcc367be6af9eef9"></a>
### entry-8165dcc367be6af9eef9 · polymas-teacher-score-skills

技能  - 专家整理.xlsx / 技能 / 第 103 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B103 | 场景标签 | 成绩管理/查询 |
| E103 | 功能点序号 | 7 |
| F103 | 功能点（英文） | score_query |
| G103 | 功能点（中文） | 成绩明细查询 |
| H103 | 描述 | 教师查看班级下每个学生的成绩明细，支持作业成绩、考试成绩与汇总成绩查看 |
| D（合并继承自 D97；D97:D104） | 原值见锚点 | 教师成绩技能 |
| C（合并继承自 C97；C97:C104） | 原值见锚点 | polymas-teacher-score-skills |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-51ebf1a74107bdcd6a6b"></a>
### entry-51ebf1a74107bdcd6a6b · polymas-teacher-score-skills

技能  - 专家整理.xlsx / 技能 / 第 104 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B104 | 场景标签 | 成绩管理/汇总 |
| E104 | 功能点序号 | 8 |
| F104 | 功能点（英文） | score_summary |
| G104 | 功能点（中文） | 成绩汇总 |
| H104 | 描述 | 教师汇总课程下班级成绩：按班级维度展示作业成绩、考试成绩与汇总成绩 |
| D（合并继承自 D97；D97:D104） | 原值见锚点 | 教师成绩技能 |
| C（合并继承自 C97；C97:C104） | 原值见锚点 | polymas-teacher-score-skills |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-226e511f0cade0f0b4a8"></a>
### entry-226e511f0cade0f0b4a8 · polymas-teacher-teaching-observation-skills

技能  - 专家整理.xlsx / 技能 / 第 105 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B105 | 场景标签 | 教学观测/进度 |
| C105 | 技能名称 | polymas-teacher-teaching-observation-skills |
| D105 | 技能中文名 | 教师教学观测技能 |
| E105 | 功能点序号 | 1 |
| F105 | 功能点（英文） | learning_progress |
| G105 | 功能点（中文） | 学习进度查询 |
| H105 | 描述 | 查询学习进度：学习资源完成率、必学完成率分组分布 |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-4116439b6730fc4d9738"></a>
### entry-4116439b6730fc4d9738 · polymas-teacher-teaching-observation-skills

技能  - 专家整理.xlsx / 技能 / 第 106 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B106 | 场景标签 | 教学观测/排行 |
| E106 | 功能点序号 | 2 |
| F106 | 功能点（英文） | rankings |
| G106 | 功能点（中文） | 排行榜查询 |
| H106 | 描述 | 查询四大排行榜：学习完成率、作业平均分、考试平均分、互动参与率 Top5 |
| D（合并继承自 D105；D105:D117） | 原值见锚点 | 教师教学观测技能 |
| C（合并继承自 C105；C105:C117） | 原值见锚点 | polymas-teacher-teaching-observation-skills |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-3fde8e6588e3345ec83a"></a>
### entry-3fde8e6588e3345ec83a · polymas-teacher-teaching-observation-skills

技能  - 专家整理.xlsx / 技能 / 第 107 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B107 | 场景标签 | 教学观测/活动 |
| E107 | 功能点序号 | 3 |
| F107 | 功能点（英文） | activity |
| G107 | 功能点（中文） | 教学活动查询 |
| H107 | 描述 | 查询教学活动：互动参与、作业/考试完成、智能体教学、话题讨论、阶梯达成、能力训练等 |
| D（合并继承自 D105；D105:D117） | 原值见锚点 | 教师教学观测技能 |
| C（合并继承自 C105；C105:C117） | 原值见锚点 | polymas-teacher-teaching-observation-skills |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-8f1d17f8f9893f723f3f"></a>
### entry-8f1d17f8f9893f723f3f · polymas-teacher-teaching-observation-skills

技能  - 专家整理.xlsx / 技能 / 第 108 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B108 | 场景标签 | 教学观测/成绩 |
| E108 | 功能点序号 | 4 |
| F108 | 功能点（英文） | score |
| G108 | 功能点（中文） | 总成绩查询 |
| H108 | 描述 | 查询总成绩：总分平均、各考核权重与平均分、成绩等级分组 |
| D（合并继承自 D105；D105:D117） | 原值见锚点 | 教师教学观测技能 |
| C（合并继承自 C105；C105:C117） | 原值见锚点 | polymas-teacher-teaching-observation-skills |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-2a54ca6f048f0a2c7578"></a>
### entry-2a54ca6f048f0a2c7578 · polymas-teacher-teaching-observation-skills

技能  - 专家整理.xlsx / 技能 / 第 109 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B109 | 场景标签 | 教学观测/趋势 |
| E109 | 功能点序号 | 5 |
| F109 | 功能点（英文） | trend |
| G109 | 功能点（中文） | 学习趋势查询 |
| H109 | 描述 | 查询学习趋势：按周统计 AI 使用量与学习活动完成量 |
| D（合并继承自 D105；D105:D117） | 原值见锚点 | 教师教学观测技能 |
| C（合并继承自 C105；C105:C117） | 原值见锚点 | polymas-teacher-teaching-observation-skills |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-4dcac1fc89ccdebdd42f"></a>
### entry-4dcac1fc89ccdebdd42f · polymas-teacher-teaching-observation-skills

技能  - 专家整理.xlsx / 技能 / 第 110 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B110 | 场景标签 | 教学观测/知识点 |
| E110 | 功能点序号 | 6 |
| F110 | 功能点（英文） | knowledge |
| G110 | 功能点（中文） | 知识点情况查询 |
| H110 | 描述 | 查询知识点情况：AI概要、掌握度统计、较好/一般/薄弱知识点分类列表 |
| D（合并继承自 D105；D105:D117） | 原值见锚点 | 教师教学观测技能 |
| C（合并继承自 C105；C105:C117） | 原值见锚点 | polymas-teacher-teaching-observation-skills |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-e85c11b93dc76ce4a467"></a>
### entry-e85c11b93dc76ce4a467 · polymas-teacher-teaching-observation-skills

技能  - 专家整理.xlsx / 技能 / 第 111 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B111 | 场景标签 | 教学观测/预警 |
| E111 | 功能点序号 | 7 |
| F111 | 功能点（英文） | warning |
| G111 | 功能点（中文） | 学习预警查询 |
| H111 | 描述 | 查询学习预警：预警学生Top20列表及各类预警统计 |
| D（合并继承自 D105；D105:D117） | 原值见锚点 | 教师教学观测技能 |
| C（合并继承自 C105；C105:C117） | 原值见锚点 | polymas-teacher-teaching-observation-skills |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-d41def8c52b4a87305b6"></a>
### entry-d41def8c52b4a87305b6 · polymas-teacher-teaching-observation-skills

技能  - 专家整理.xlsx / 技能 / 第 112 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B112 | 场景标签 | 教学观测/进度详情 |
| E112 | 功能点序号 | 8 |
| F112 | 功能点（英文） | progress_detail |
| G112 | 功能点（中文） | 学习进度详情 |
| H112 | 描述 | 查询学习进度详情：资源统计、学习时长排行、学习数量排行、必学完成数分组 |
| D（合并继承自 D105；D105:D117） | 原值见锚点 | 教师教学观测技能 |
| C（合并继承自 C105；C105:C117） | 原值见锚点 | polymas-teacher-teaching-observation-skills |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-7c9525568a0d53bc0651"></a>
### entry-7c9525568a0d53bc0651 · polymas-teacher-teaching-observation-skills

技能  - 专家整理.xlsx / 技能 / 第 113 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B113 | 场景标签 | 教学观测/课堂互动 |
| E113 | 功能点序号 | 9 |
| F113 | 功能点（英文） | lesson_interaction |
| G113 | 功能点（中文） | 课堂互动查询 |
| H113 | 描述 | 查询课堂互动：签到/抢答/答疑/点名/讨论/随测/头脑风暴/投票等各类互动参与数据 |
| D（合并继承自 D105；D105:D117） | 原值见锚点 | 教师教学观测技能 |
| C（合并继承自 C105；C105:C117） | 原值见锚点 | polymas-teacher-teaching-observation-skills |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-da93b90b6951caed9c0e"></a>
### entry-da93b90b6951caed9c0e · polymas-teacher-teaching-observation-skills

技能  - 专家整理.xlsx / 技能 / 第 114 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B114 | 场景标签 | 教学观测/讨论 |
| E114 | 功能点序号 | 10 |
| F114 | 功能点（英文） | topic_discussion |
| G114 | 功能点（中文） | 话题讨论查询 |
| H114 | 描述 | 查询话题讨论：话题数、回复数、评论数、参与率、讨论词云 |
| D（合并继承自 D105；D105:D117） | 原值见锚点 | 教师教学观测技能 |
| C（合并继承自 C105；C105:C117） | 原值见锚点 | polymas-teacher-teaching-observation-skills |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-1d20c9b471b6595a4573"></a>
### entry-1d20c9b471b6595a4573 · polymas-teacher-teaching-observation-skills

技能  - 专家整理.xlsx / 技能 / 第 115 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B115 | 场景标签 | 教学观测/作业 |
| E115 | 功能点序号 | 11 |
| F115 | 功能点（英文） | homework |
| G115 | 功能点（中文） | 作业数据查询 |
| H115 | 描述 | 查询作业：作业完成率、人均完成数、作业明细列表 |
| D（合并继承自 D105；D105:D117） | 原值见锚点 | 教师教学观测技能 |
| C（合并继承自 C105；C105:C117） | 原值见锚点 | polymas-teacher-teaching-observation-skills |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-25b9953219584b5a9f0e"></a>
### entry-25b9953219584b5a9f0e · polymas-teacher-teaching-observation-skills

技能  - 专家整理.xlsx / 技能 / 第 116 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B116 | 场景标签 | 教学观测/考试 |
| E116 | 功能点序号 | 12 |
| F116 | 功能点（英文） | exam |
| G116 | 功能点（中文） | 考试数据查询 |
| H116 | 描述 | 查询考试：考试参与率、缺考人数、考试明细列表 |
| D（合并继承自 D105；D105:D117） | 原值见锚点 | 教师教学观测技能 |
| C（合并继承自 C105；C105:C117） | 原值见锚点 | polymas-teacher-teaching-observation-skills |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-474ac85a5b4ff1cd100e"></a>
### entry-474ac85a5b4ff1cd100e · polymas-teacher-teaching-observation-skills

技能  - 专家整理.xlsx / 技能 / 第 117 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B117 | 场景标签 | 教学观测/智能体 |
| E117 | 功能点序号 | 13 |
| F117 | 功能点（英文） | agent_qa |
| G117 | 功能点（中文） | 智能体问答查询 |
| H117 | 描述 | 查询智能体问答：累计解答数、AI课代表/课堂智能体数量、对话人次、问答词云 |
| D（合并继承自 D105；D105:D117） | 原值见锚点 | 教师教学观测技能 |
| C（合并继承自 C105；C105:C117） | 原值见锚点 | polymas-teacher-teaching-observation-skills |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-fa67f202946a1b226ca7"></a>
### entry-fa67f202946a1b226ca7 · polymas-teacher-teaching-plan

技能  - 专家整理.xlsx / 技能 / 第 118 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B118 | 场景标签 | 教学计划 |
| C118 | 技能名称 | polymas-teacher-teaching-plan |
| D118 | 技能中文名 | 教学计划技能 |
| E118 | 功能点序号 | 1 |
| F118 | 功能点（英文） | teaching_plan_query |
| G118 | 功能点（中文） | 教学计划查询编辑 |
| H118 | 描述 | 教学计划查询：查询单元/主题(小节)/知识点结构及关联的作业与考试活动 |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-a81099ab3d8a8b29cb7b"></a>
### entry-a81099ab3d8a8b29cb7b · polymas-teacher-work-calendar

技能  - 专家整理.xlsx / 技能 / 第 119 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B119 | 场景标签 | 日程/日历 |
| C119 | 技能名称 | polymas-teacher-work-calendar |
| D119 | 技能中文名 | 工作日历查询技能 |
| E119 | 功能点序号 | 1 |
| F119 | 功能点（英文） | teaching_schedule_query |
| G119 | 功能点（中文） | 教学日程查询 |
| H119 | 描述 | 工作日历查询：查教学日程（课程/会议/作业截止/考试/AI提醒） |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-5708fa4debd3e5454042"></a>
### entry-5708fa4debd3e5454042 · polymas-tool-skills

技能  - 专家整理.xlsx / 技能 / 第 120 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B120 | 场景标签 | 通用工具/搜索 |
| C120 | 技能名称 | polymas-tool-skills |
| D120 | 技能中文名 | 平台通用工具技能 |
| E120 | 功能点序号 | 1 |
| F120 | 功能点（英文） | online_search |
| G120 | 功能点（中文） | 联网搜索 |
| H120 | 描述 | 仅用于联网搜索互联网公开内容，返回标题、描述、URL、封面、平台名称、相似度、发布时间等信息。纯搜索，不做任何内容操作。 |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-ccd09c00a7ab2f8d8c1e"></a>
### entry-ccd09c00a7ab2f8d8c1e · polymas-tool-skills

技能  - 专家整理.xlsx / 技能 / 第 121 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B121 | 场景标签 | 通用工具/Skill |
| E121 | 功能点序号 | 2 |
| F121 | 功能点（英文） | skill_search_install |
| G121 | 功能点（中文） | Skill搜索安装 |
| H121 | 描述 | 联网搜索 Skill 市场并安装到平台。支持仅搜索（返回结果后追问安装意愿）和搜索即安装。默认 ClawHub（纯 API，零浏览器），也支持 ModelScope 和 SkillsMP。 |
| D（合并继承自 D120；D120:D125） | 原值见锚点 | 平台通用工具技能 |
| C（合并继承自 C120；C120:C125） | 原值见锚点 | polymas-tool-skills |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-04fb1b0ff74ff392a4df"></a>
### entry-04fb1b0ff74ff392a4df · polymas-tool-skills

技能  - 专家整理.xlsx / 技能 / 第 122 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B122 | 场景标签 | 通用工具/能力广场 |
| E122 | 功能点序号 | 3 |
| F122 | 功能点（英文） | capability_search |
| G122 | 功能点（中文） | 能力广场搜索 |
| H122 | 描述 | 仅用于查询/搜索技能广场的AI能力（技能SKILL、技能套件SKILL_SUITE、MCP工具MCP、探索卡片EXPLORE_CARD）。不支持上传、删除、下载等操作。 |
| D（合并继承自 D120；D120:D125） | 原值见锚点 | 平台通用工具技能 |
| C（合并继承自 C120；C120:C125） | 原值见锚点 | polymas-tool-skills |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-c0e744feef6f5b5e95e7"></a>
### entry-c0e744feef6f5b5e95e7 · polymas-tool-skills

技能  - 专家整理.xlsx / 技能 / 第 123 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B123 | 场景标签 | 通用工具/能力广场 |
| E123 | 功能点序号 | 4 |
| F123 | 功能点（英文） | capability_install |
| G123 | 功能点（中文） | 能力广场安装 |
| H123 | 描述 | 仅用于安装技能广场的AI能力（技能SKILL、技能套件SKILL_SUITE、MCP工具MCP、探索卡片EXPLORE_CARD）。安装所需参数缺失时，须先走能力搜索流程补全参数。 |
| D（合并继承自 D120；D120:D125） | 原值见锚点 | 平台通用工具技能 |
| C（合并继承自 C120；C120:C125） | 原值见锚点 | polymas-tool-skills |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-33f67b912344de6ad7f6"></a>
### entry-33f67b912344de6ad7f6 · polymas-tool-skills

技能  - 专家整理.xlsx / 技能 / 第 124 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B124 | 场景标签 | 通用工具/用户 |
| E124 | 功能点序号 | 5 |
| F124 | 功能点（英文） | user_detail |
| G124 | 功能点（中文） | 用户信息查询 |
| H124 | 描述 | 查询当前登录用户详情接口说明 |
| D（合并继承自 D120；D120:D125） | 原值见锚点 | 平台通用工具技能 |
| C（合并继承自 C120；C120:C125） | 原值见锚点 | polymas-tool-skills |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-72a7d2b6a22b21a36237"></a>
### entry-72a7d2b6a22b21a36237 · polymas-tool-skills

技能  - 专家整理.xlsx / 技能 / 第 125 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B125 | 场景标签 | 通用工具/文件 |
| E125 | 功能点序号 | 6 |
| F125 | 功能点（英文） | file_upload |
| G125 | 功能点（中文） | 文件上传 |
| H125 | 描述 | 将 polymas-* 类技能生成的本地文件上传到平台工作空间，上传成功后自动删除本地文件。 |
| D（合并继承自 D120；D120:D125） | 原值见锚点 | 平台通用工具技能 |
| C（合并继承自 C120；C120:C125） | 原值见锚点 | polymas-tool-skills |
| A（合并继承自 A3；A3:A125） | 原值见锚点 | 业务 |

<a id="entry-b8658e2a3dd473f51019"></a>
### entry-b8658e2a3dd473f51019 · external-knowledge-search

技能  - 专家整理.xlsx / 技能 / 第 126 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A126 | 类型 | 算法 |
| B126 | 场景标签 | deep/联网/wiki检索 |
| C126 | 技能名称 | external-knowledge-search |
| G126 | 功能点（中文） | deep/联网/wiki检索 |
| H126 | 描述 | 支持互联网联网检索与知识库检索并行执行。工作空间内部文档请使用workspace专属检索；需联网资料、知识库查询时优先路由本能力。⚡ 并行响应（5-30 秒），适用于知识库相关复杂问答场景。 |

<a id="entry-1e77dbb876cee6dbbffb"></a>
### entry-1e77dbb876cee6dbbffb · deep-search

技能  - 专家整理.xlsx / 技能 / 第 127 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B127 | 场景标签 | deep/联网/检索 |
| C127 | 技能名称 | deep-search |
| G127 | 功能点（中文） | deep/联网/检索 |
| H127 | 描述 | 三阶段完整流程：意图识别→深度检索→覆盖检查。解析用户输入生成检索意图，调用 deep_search.py 执行检索，再分析意图覆盖情况供用户交互调整。Use when the user provides a query that needs intent analysis, deep search, and coverage check. |
| A（合并继承自 A126；A126:A141） | 原值见锚点 | 算法 |

<a id="entry-8897c08fd44d8b71c2dd"></a>
### entry-8897c08fd44d8b71c2dd · resource-understanding

技能  - 专家整理.xlsx / 技能 / 第 128 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B128 | 场景标签 | 结构化/文件理解 |
| C128 | 技能名称 | resource-understanding |
| G128 | 功能点（中文） | 结构化+文件理解 |
| H128 | 描述 | Use this skill whenever you need to understand an arbitrary resource file (document, spreadsheet, PDF, image, audio, video, archive, code, or unknown type) end-to-end. Stage 1 (raw structuration) extracts the file's structured content/plain text; stage 2 (agent understanding — a concise summary plus an intent-aware answer) is ENABLED by default, so the skill returns both the structured content (rawStructureResult) and the summary/intent (resourceSummary + intentResult). Trigger this when the user gives you a file URL and asks "what is this", "summarize this", "find X in this file", "which chart/image shows Y", or otherwise wants a file's content extracted or read. Set taskType="writing" (default "qa") when the user wants to WRITE with the file as source material — the skill then locates and returns relevant verbatim fragments (writingResult) instead of answering. This is a self-contained port of the kb-resource-understanding-service; it calls an external structuration service directly and an LLM gateway for stage 2 — it does NOT require that service to be running. |
| A（合并继承自 A126；A126:A141） | 原值见锚点 | 算法 |

<a id="entry-4bea4df5b0879cc35a6f"></a>
### entry-4bea4df5b0879cc35a6f · creation_router

技能  - 专家整理.xlsx / 技能 / 第 129 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B129 | 场景标签 | 创作 |
| C129 | 技能名称 | creation_router |
| G129 | 功能点（中文） | 创作分发 |
| H129 | 描述 | 创作任务路由指南。负责判断信息完整性、请求Lead Agent 补充必要信息（检索结果或文件），并将完整的创作任务路由到下游 Skill。 |
| I129 | 未命名列 I | 不能放 |
| A（合并继承自 A126；A126:A141） | 原值见锚点 | 算法 |

<a id="entry-c4b3f6e2c36d73d68e87"></a>
### entry-c4b3f6e2c36d73d68e87 · creation_router_vip

技能  - 专家整理.xlsx / 技能 / 第 130 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C130 | 技能名称 | creation_router_vip |
| I130 | 未命名列 I | 不能放 |
| B（合并继承自 B129；B129:B139） | 原值见锚点 | 创作 |
| A（合并继承自 A126；A126:A141） | 原值见锚点 | 算法 |

<a id="entry-30381f9733da27122fe8"></a>
### entry-30381f9733da27122fe8 · creator_tool

技能  - 专家整理.xlsx / 技能 / 第 131 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C131 | 技能名称 | creator_tool |
| G131 | 功能点（中文） | 创作基础工具包 |
| H131 | 描述 | 创作基础工具集。包含：生图（LLM 润色 + OSS）、生视频（Qwen Happy Horse / Matplotlib + OSS）、图片校验（批量 URL 可达性检查）、获取知识库 ID、文件解析、检索结果清洗。 |
| I131 | 未命名列 I | 有两个 |
| B（合并继承自 B129；B129:B139） | 原值见锚点 | 创作 |
| A（合并继承自 A126；A126:A141） | 原值见锚点 | 算法 |

<a id="entry-ca0b939625166b1c405e"></a>
### entry-ca0b939625166b1c405e · creator_tool_vip

技能  - 专家整理.xlsx / 技能 / 第 132 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C132 | 技能名称 | creator_tool_vip |
| I132 | 未命名列 I | 不能放 |
| B（合并继承自 B129；B129:B139） | 原值见锚点 | 创作 |
| A（合并继承自 A126；A126:A141） | 原值见锚点 | 算法 |

<a id="entry-330e9e864d761f2fad0f"></a>
### entry-330e9e864d761f2fad0f · mintflow-markdown

技能  - 专家整理.xlsx / 技能 / 第 133 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C133 | 技能名称 | mintflow-markdown |
| G133 | 功能点（中文） | mardkwon文档生成 |
| H133 | 描述 | 把 JSON 大纲或纯文本主题生成为结构清晰的 Markdown 文档（技术文档 / 报告 / 博客 / 会议纪要 / PRD 等纯文本长文）。默认走"生成→给用户看草稿→按反馈修订→用户通过"的人工介入回环（HITL，分多次调用续接）；用户明确要"直接给结果、不用看"时才一次性生成。当用户要"写一篇文章 / 整理成文档 / 生成报告 / 把大纲扩写成正文"且输出是纯 Markdown（不需要 PPT、网页排版、数据分析）时使用。免安装直接跑 scripts/run.py,LLM 密钥由配置中心下发,无需手工配置。 |
| B（合并继承自 B129；B129:B139） | 原值见锚点 | 创作 |
| A（合并继承自 A126；A126:A141） | 原值见锚点 | 算法 |

<a id="entry-431312168a7e24545853"></a>
### entry-431312168a7e24545853 · mintflow-html

技能  - 专家整理.xlsx / 技能 / 第 134 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C134 | 技能名称 | mintflow-html |
| G134 | 功能点（中文） | html创作 |
| B（合并继承自 B129；B129:B139） | 原值见锚点 | 创作 |
| A（合并继承自 A126；A126:A141） | 原值见锚点 | 算法 |

<a id="entry-28b91bd8ac559e5f5cf2"></a>
### entry-28b91bd8ac559e5f5cf2 · digital_lesson_html

技能  - 专家整理.xlsx / 技能 / 第 135 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C135 | 技能名称 | digital_lesson_html |
| G135 | 功能点（中文） | 数字课堂 |
| I135 | 未命名列 I | 未上线 |
| B（合并继承自 B129；B129:B139） | 原值见锚点 | 创作 |
| A（合并继承自 A126；A126:A141） | 原值见锚点 | 算法 |

<a id="entry-3f98ca33c7bb3961ed63"></a>
### entry-3f98ca33c7bb3961ed63 · script-to-video

技能  - 专家整理.xlsx / 技能 / 第 136 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C136 | 技能名称 | script-to-video |
| G136 | 功能点（中文） | （纯 AI）讲稿 |
| I136 | 未命名列 I | 未上线 |
| B（合并继承自 B129；B129:B139） | 原值见锚点 | 创作 |
| A（合并继承自 A126；A126:A141） | 原值见锚点 | 算法 |

<a id="entry-f087b3de766e7a2913cc"></a>
### entry-f087b3de766e7a2913cc · pptx-video-native

技能  - 专家整理.xlsx / 技能 / 第 137 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C137 | 技能名称 | pptx-video-native |
| G137 | 功能点（中文） | pptx→雨馨治同动画规划的skill-自研 |
| I137 | 未命名列 I | 未上线 |
| B（合并继承自 B129；B129:B139） | 原值见锚点 | 创作 |
| A（合并继承自 A126；A126:A141） | 原值见锚点 | 算法 |

<a id="entry-2d6b12ff94566aaddbf8"></a>
### entry-2d6b12ff94566aaddbf8 · pptx-video-ai

技能  - 专家整理.xlsx / 技能 / 第 138 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C138 | 技能名称 | pptx-video-ai |
| G138 | 功能点（中文） | PPT → AI |
| I138 | 未命名列 I | 未上线 |
| B（合并继承自 B129；B129:B139） | 原值见锚点 | 创作 |
| A（合并继承自 A126；A126:A141） | 原值见锚点 | 算法 |

<a id="entry-d8d63dd2d7e223c0c2ed"></a>
### entry-d8d63dd2d7e223c0c2ed · power-html-ppt

技能  - 专家整理.xlsx / 技能 / 第 139 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C139 | 技能名称 | power-html-ppt |
| G139 | 功能点（中文） | PPT创作 |
| B（合并继承自 B129；B129:B139） | 原值见锚点 | 创作 |
| A（合并继承自 A126；A126:A141） | 原值见锚点 | 算法 |

<a id="entry-1c2700204ab9967c0816"></a>
### entry-1c2700204ab9967c0816 · lesson_prep

技能  - 专家整理.xlsx / 技能 / 第 140 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B140 | 场景标签 | 备课 |
| C140 | 技能名称 | lesson_prep |
| G140 | 功能点（中文） | 备课 |
| A（合并继承自 A126；A126:A141） | 原值见锚点 | 算法 |

<a id="entry-429ad72e7b30813fea01"></a>
### entry-429ad72e7b30813fea01 · generate-questions

技能  - 专家整理.xlsx / 技能 / 第 141 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B141 | 场景标签 | AI出题 |
| C141 | 技能名称 | generate-questions |
| G141 | 功能点（中文） | AI出题 |
| I141 | 未命名列 I | 不放 |
| A（合并继承自 A126；A126:A141） | 原值见锚点 | 算法 |

<a id="entry-da1dc3e0e7938aeab9cd"></a>
### entry-da1dc3e0e7938aeab9cd · research-assistant

技能  - 专家整理.xlsx / 技能 / 第 142 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A142 | 类型 | 交付-西南交大智能学伴 |
| B142 | 场景标签 | 科研学术 |
| C142 | 技能名称 | research-assistant |
| H142 | 描述 | 科研学术助手，集成科研资讯追踪、文献深度解析、选题辅助、论文写作支持、学术规范与诚信五大模块。当用户涉及论文搜索/推荐、文献阅读/解析、选题建议/评估、论文润色/参考文献检查、学术规范/AI使用边界等科研场景时使用此Skill。通过两级意图识别自动路由到对应模块 |
| I142 | 未命名列 I | 不放 |

<a id="entry-3834412d7a0e3736e3d4"></a>
### entry-3834412d7a0e3736e3d4 · psy-education

技能  - 专家整理.xlsx / 技能 / 第 143 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B143 | 场景标签 | 身心健康 |
| C143 | 技能名称 | psy-education |
| H143 | 描述 | 心理科普推送子技能。支持定时推送和情境触发两种模式：定时模式每周≥2次从知识库科普文章分类召回最新/最热文章；情境模式在共情疏导识别到压力标签后推荐强相关文章（≤1篇）。生成图文卡片（标题+摘要+阅读链接）。适用于定期心理健康科普、压力标签匹配的文章推荐等场景。 |
| A（合并继承自 A142；A142:A148） | 原值见锚点 | 交付-西南交大智能学伴 |
| I（合并继承自 I142；I142:I151） | 原值见锚点 | 不放 |

<a id="entry-6cd8b15e0cd0387fbc3c"></a>
### entry-6cd8b15e0cd0387fbc3c · crisis-alert

技能  - 专家整理.xlsx / 技能 / 第 144 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C144 | 技能名称 | crisis-alert |
| H144 | 描述 | 研究生心理危机预警子技能（5秒熔断机制）。当用户输入命中高危关键词或语义规则时立即触发，中断所有正常技能执行流，返回固定模板回复并触发后台告警。适用于自伤、自杀意念、极端绝望表达等心理危机场景。此技能输出不可被LLM改写。 |
| B（合并继承自 B143；B143:B146） | 原值见锚点 | 身心健康 |
| A（合并继承自 A142；A142:A148） | 原值见锚点 | 交付-西南交大智能学伴 |
| I（合并继承自 I142；I142:I151） | 原值见锚点 | 不放 |

<a id="entry-d6852b78f32472ba90ad"></a>
### entry-d6852b78f32472ba90ad · counseling-guide

技能  - 专家整理.xlsx / 技能 / 第 145 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C145 | 技能名称 | counseling-guide |
| H145 | 描述 | 心理中心指引子技能。处理用户关于预约方式、咨询地点、咨询师信息、咨询流程、开放时间、费用等事实性问题。通过RAG检索知识库结构化数据，返回信息卡片，标注信息时效性。适用于查询校心理中心服务信息、预约入口、咨询师排班等场景。 |
| B（合并继承自 B143；B143:B146） | 原值见锚点 | 身心健康 |
| A（合并继承自 A142；A142:A148） | 原值见锚点 | 交付-西南交大智能学伴 |
| I（合并继承自 I142；I142:I151） | 原值见锚点 | 不放 |

<a id="entry-ec75e36238ea8b812c87"></a>
### entry-ec75e36238ea8b812c87 · adaptive-empathy

技能  - 专家整理.xlsx / 技能 / 第 146 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C146 | 技能名称 | adaptive-empathy |
| H146 | 描述 | 研究生自适应共情响应子技能。处理所有非事实查询、非危机类的用户输入，通过情绪强度评估和求助明确度判断，动态选择深度倾听、共情+轻引导、靶向疏导三种响应模式。支持4维压力模型（科研焦虑/人际困扰/发展迷茫/毕业恐慌）识别与标签输出。适用于研究生情绪倾诉、科研压力、导生关系困扰、毕业焦虑等场景。 |
| B（合并继承自 B143；B143:B146） | 原值见锚点 | 身心健康 |
| A（合并继承自 A142；A142:A148） | 原值见锚点 | 交付-西南交大智能学伴 |
| I（合并继承自 I142；I142:I151） | 原值见锚点 | 不放 |

<a id="entry-833251b8bc3bd277aa8b"></a>
### entry-833251b8bc3bd277aa8b · competition-assistant

技能  - 专家整理.xlsx / 技能 / 第 147 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B147 | 场景标签 | 竞赛 |
| C147 | 技能名称 | competition-assistant |
| H147 | 描述 | 心理科普推送子技能。支持定时推送和情境触发两种模式：定时模式每周≥2次从知识库科普文章分类召回最新/最热文章；情境模式在共情疏导识别到压力标签后推荐强相关文章（≤1篇）。生成图文卡片（标题+摘要+阅读链接）。适用于定期心理健康科普、压力标签匹配的文章推荐等场景。 |
| A（合并继承自 A142；A142:A148） | 原值见锚点 | 交付-西南交大智能学伴 |
| I（合并继承自 I142；I142:I151） | 原值见锚点 | 不放 |

<a id="entry-a5f446edd451b08fec25"></a>
### entry-a5f446edd451b08fec25 · academic_planning

技能  - 专家整理.xlsx / 技能 / 第 148 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B148 | 场景标签 | 学业规划 |
| C148 | 技能名称 | academic_planning |
| H148 | 描述 | 学业规划主技能。统一入口，接收学生自然语言提问，执行语义意图识别（5大类：入学适应、学工事务、培养解析、进度跟踪、学位指引），支持多意图并行识别与分发，按意图动态裁剪学生档案，并行路由分发至对应子技能执行 |
| A（合并继承自 A142；A142:A148） | 原值见锚点 | 交付-西南交大智能学伴 |
| I（合并继承自 I142；I142:I151） | 原值见锚点 | 不放 |

<a id="entry-a6cce461553087dc1269"></a>
### entry-a6cce461553087dc1269 · tcm_creative_design

技能  - 专家整理.xlsx / 技能 / 第 149 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A149 | 类型 | 应用工程师 |
| B149 | 场景标签 | 典故检索 |
| C149 | 技能名称 | tcm_creative_design |
| D149 | 技能中文名 | 中医药文创专家 |
| E149 | 功能点序号 | 1 |
| F149 | 功能点（英文） | story_search |
| G149 | 功能点（中文） | 典故检索 |
| H149 | 描述 | 中医药文创全案专家。强制调用 db-search 检索知识库，提取中医药典故与纹样，并静默生成全系 HTML 网页。 |
| I（合并继承自 I142；I142:I151） | 原值见锚点 | 不放 |

<a id="entry-a8303af697d8139d14d4"></a>
### entry-a8303af697d8139d14d4 · tcm_creative_design

技能  - 专家整理.xlsx / 技能 / 第 150 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B150 | 场景标签 | 纹样提取 |
| E150 | 功能点序号 | 2 |
| F150 | 功能点（英文） | pattern_extract |
| G150 | 功能点（中文） | 纹样提取 |
| C（合并继承自 C149；C149:C151） | 原值见锚点 | tcm_creative_design |
| D（合并继承自 D149；D149:D151） | 原值见锚点 | 中医药文创专家 |
| A（合并继承自 A149；A149:A154） | 原值见锚点 | 应用工程师 |
| H（合并继承自 H149；H149:H151） | 原值见锚点 | 中医药文创全案专家。强制调用 db-search 检索知识库，提取中医药典故与纹样，并静默生成全系 HTML 网页。 |
| I（合并继承自 I142；I142:I151） | 原值见锚点 | 不放 |

<a id="entry-58549c2ed3373d9cc7fc"></a>
### entry-58549c2ed3373d9cc7fc · tcm_creative_design

技能  - 专家整理.xlsx / 技能 / 第 151 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B151 | 场景标签 | 网页生成 |
| E151 | 功能点序号 | 3 |
| F151 | 功能点（英文） | webpage_generate |
| G151 | 功能点（中文） | 网页生成 |
| C（合并继承自 C149；C149:C151） | 原值见锚点 | tcm_creative_design |
| D（合并继承自 D149；D149:D151） | 原值见锚点 | 中医药文创专家 |
| A（合并继承自 A149；A149:A154） | 原值见锚点 | 应用工程师 |
| H（合并继承自 H149；H149:H151） | 原值见锚点 | 中医药文创全案专家。强制调用 db-search 检索知识库，提取中医药典故与纹样，并静默生成全系 HTML 网页。 |
| I（合并继承自 I142；I142:I151） | 原值见锚点 | 不放 |

<a id="entry-1bf48e4373405fdba846"></a>
### entry-1bf48e4373405fdba846 · tcm_identifier_pro

技能  - 专家整理.xlsx / 技能 / 第 152 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B152 | 场景标签 | 药材鉴别 |
| C152 | 技能名称 | tcm_identifier_pro |
| D152 | 技能中文名 | 中药鉴别专家 |
| E152 | 功能点序号 | 1 |
| F152 | 功能点（英文） | herb_identify |
| G152 | 功能点（中文） | 药材鉴别 |
| H152 | 描述 | 智能中药全产业链鉴别专家，支持药材鉴别、活体病虫害识别与品相评估。 |
| A（合并继承自 A149；A149:A154） | 原值见锚点 | 应用工程师 |

<a id="entry-2f9a169f2498ffcf5bd7"></a>
### entry-2f9a169f2498ffcf5bd7 · tcm_identifier_pro

技能  - 专家整理.xlsx / 技能 / 第 153 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B153 | 场景标签 | 病虫害识别 |
| E153 | 功能点序号 | 2 |
| F153 | 功能点（英文） | pest_identify |
| G153 | 功能点（中文） | 病虫害识别 |
| D（合并继承自 D152；D152:D154） | 原值见锚点 | 中药鉴别专家 |
| C（合并继承自 C152；C152:C154） | 原值见锚点 | tcm_identifier_pro |
| A（合并继承自 A149；A149:A154） | 原值见锚点 | 应用工程师 |
| H（合并继承自 H152；H152:H154） | 原值见锚点 | 智能中药全产业链鉴别专家，支持药材鉴别、活体病虫害识别与品相评估。 |

<a id="entry-db7209ab6f734e8f6db9"></a>
### entry-db7209ab6f734e8f6db9 · tcm_identifier_pro

技能  - 专家整理.xlsx / 技能 / 第 154 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B154 | 场景标签 | 品相评估 |
| E154 | 功能点序号 | 3 |
| F154 | 功能点（英文） | quality_assess |
| G154 | 功能点（中文） | 品相评估 |
| D（合并继承自 D152；D152:D154） | 原值见锚点 | 中药鉴别专家 |
| C（合并继承自 C152；C152:C154） | 原值见锚点 | tcm_identifier_pro |
| A（合并继承自 A149；A149:A154） | 原值见锚点 | 应用工程师 |
| H（合并继承自 H152；H152:H154） | 原值见锚点 | 智能中药全产业链鉴别专家，支持药材鉴别、活体病虫害识别与品相评估。 |

<a id="entry-2fcdb509e34242c28495"></a>
### entry-2fcdb509e34242c28495 · pincaimao-interview-question

技能  - 专家整理.xlsx / 技能 / 第 155 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A155 | 类型 | 其他 |
| B155 | 场景标签 | 试题生成 |
| C155 | 技能名称 | pincaimao-interview-question |
| D155 | 技能中文名 | 面试出题大师 |
| E155 | 功能点序号 | 1 |
| F155 | 功能点（英文） | question_generate |
| G155 | 功能点（中文） | 试题生成 |
| H155 | 描述 | 聘才猫 - 面试出题大师 Use when calling Pincaimao Interview Question Master API to generate interview questions based on a job description and candidate resume. Requires PCM_INTERVIEW_QUESTIONS_KEY env var. |
| I155 | 未命名列 I | 放 |

<a id="entry-7f8e3a17d394761c7a90"></a>
### entry-7f8e3a17d394761c7a90 · pincaimao-interview-question

技能  - 专家整理.xlsx / 技能 / 第 156 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B156 | 场景标签 | 岗人匹配 |
| E156 | 功能点序号 | 2 |
| F156 | 功能点（英文） | job_resume_match |
| G156 | 功能点（中文） | 岗人匹配 |
| H156 | 描述 | 聘才猫 - 面试出题大师 Use when calling Pincaimao Interview Question Master API to generate interview questions based on a job description and candidate resume. Requires PCM_INTERVIEW_QUESTIONS_KEY env var. |
| I156 | 未命名列 I | 放 |
| C（合并继承自 C155；C155:C157） | 原值见锚点 | pincaimao-interview-question |
| D（合并继承自 D155；D155:D157） | 原值见锚点 | 面试出题大师 |
| A（合并继承自 A155；A155:A178） | 原值见锚点 | 其他 |

<a id="entry-031304615643020d52cf"></a>
### entry-031304615643020d52cf · pincaimao-interview-question

技能  - 专家整理.xlsx / 技能 / 第 157 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B157 | 场景标签 | 定制出题 |
| E157 | 功能点序号 | 3 |
| F157 | 功能点（英文） | custom_question |
| G157 | 功能点（中文） | 定制出题 |
| H157 | 描述 | 聘才猫 - 面试出题大师 Use when calling Pincaimao Interview Question Master API to generate interview questions based on a job description and candidate resume. Requires PCM_INTERVIEW_QUESTIONS_KEY env var. |
| I157 | 未命名列 I | 放 |
| C（合并继承自 C155；C155:C157） | 原值见锚点 | pincaimao-interview-question |
| D（合并继承自 D155；D155:D157） | 原值见锚点 | 面试出题大师 |
| A（合并继承自 A155；A155:A178） | 原值见锚点 | 其他 |

<a id="entry-445cb677fa7537821150"></a>
### entry-445cb677fa7537821150 · cyber-ppt

技能  - 专家整理.xlsx / 技能 / 第 158 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B158 | 场景标签 | PPT制作 |
| C158 | 技能名称 | cyber-ppt |
| D158 | 技能中文名 | cyber-ppt |
| E158 | 功能点序号 | 1 |
| F158 | 功能点（英文） | material_to_ppt |
| G158 | 功能点（中文） | 材料转PPT |
| H158 | 描述 | 当用户需要把 DOCX、PDF、TXT、XLSX、研究报告、业务材料或原始数据转成高密度、可编辑、咨询风格 PPTX 时使用；也适用于需要 SCR 论证、视觉风格探索、详细图表和渲染质检的 PPT。 |
| I158 | 未命名列 I | 放 |
| A（合并继承自 A155；A155:A178） | 原值见锚点 | 其他 |

<a id="entry-f847b1700b6c42c9807e"></a>
### entry-f847b1700b6c42c9807e · cyber-ppt

技能  - 专家整理.xlsx / 技能 / 第 159 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| E159 | 功能点序号 | 2 |
| F159 | 功能点（英文） | consulting_style |
| G159 | 功能点（中文） | 咨询风格PPT |
| H159 | 描述 | 当用户需要把 DOCX、PDF、TXT、XLSX、研究报告、业务材料或原始数据转成高密度、可编辑、咨询风格 PPTX 时使用；也适用于需要 SCR 论证、视觉风格探索、详细图表和渲染质检的 PPT。 |
| I159 | 未命名列 I | 放 |
| C（合并继承自 C158；C158:C159） | 原值见锚点 | cyber-ppt |
| D（合并继承自 D158；D158:D159） | 原值见锚点 | cyber-ppt |
| B（合并继承自 B158；B158:B159） | 原值见锚点 | PPT制作 |
| A（合并继承自 A155；A155:A178） | 原值见锚点 | 其他 |

<a id="entry-62f36fc5928885e87640"></a>
### entry-62f36fc5928885e87640 · rank

技能  - 专家整理.xlsx / 技能 / 第 160 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B160 | 场景标签 | 思维工具 |
| C160 | 技能名称 | rank |
| D160 | 技能中文名 | rank |
| E160 | 功能点序号 | 1 |
| F160 | 功能点（英文） | domain_rank |
| G160 | 功能点（中文） | 领域降秩 |
| H160 | 描述 | 给一个领域，找出背后真正撑着它的几根独立的力。十几个现象砍到不可再少的生成器——砍完能把现象一个个生回来，才算数。Use when user says '降秩', '找秩', '秩是什么', '这个领域靠什么撑着', '背后是什么', or wants to decompose any domain to its irreducible generators. |
| I160 | 未命名列 I | 放 |
| A（合并继承自 A155；A155:A178） | 原值见锚点 | 其他 |

<a id="entry-967ff476942316873a8e"></a>
### entry-967ff476942316873a8e · rank

技能  - 专家整理.xlsx / 技能 / 第 161 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| E161 | 功能点序号 | 2 |
| F161 | 功能点（英文） | essence_decompose |
| G161 | 功能点（中文） | 本质拆解 |
| H161 | 描述 | 给一个领域，找出背后真正撑着它的几根独立的力。十几个现象砍到不可再少的生成器——砍完能把现象一个个生回来，才算数。Use when user says '降秩', '找秩', '秩是什么', '这个领域靠什么撑着', '背后是什么', or wants to decompose any domain to its irreducible generators. |
| I161 | 未命名列 I | 放 |
| C（合并继承自 C160；C160:C161） | 原值见锚点 | rank |
| D（合并继承自 D160；D160:D161） | 原值见锚点 | rank |
| B（合并继承自 B160；B160:B161） | 原值见锚点 | 思维工具 |
| A（合并继承自 A155；A155:A178） | 原值见锚点 | 其他 |

<a id="entry-ea7c29de26920ea13275"></a>
### entry-ea7c29de26920ea13275 · book

技能  - 专家整理.xlsx / 技能 / 第 162 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B162 | 场景标签 | 阅读分析 |
| C162 | 技能名称 | book |
| D162 | 技能中文名 | book |
| E162 | 功能点序号 | 1 |
| F162 | 功能点（英文） | book_decompose |
| G162 | 功能点（中文） | 拆书分析 |
| H162 | 描述 | 拆一本书，以「问题」为轴心走一条线。五件事：作者在答什么问题（问题），这个问题之前各流派/社会共识怎么答（零点），作者带来什么独特洞见——公式/理论框架/模型/概念四选一——相对共识挪动了什么（位移/delta），落成哪句结论（落点），最后萃一个 takeaway 作为精神内核（行囊）。收尾画一张 ASCII 参考系图（千脑智能式）：各流派、旧共识、作者钉到同一张图的位置上，delta 是图上一段看得见的距离，再走两步做预测——看懂这本书在认知史里挪动了哪一步，还能拿它预测书外的新事。Use when user says '拆书', '拆这本', '分析这本书', '这本书在讲什么', '上帝之眼看这本书', '压缩一本书', 'book', or shares a book name wanting structural analysis. NOT FOR 章节摘要（用 Fabric extract_wisdom）、论文（用 -paper）、单一观点深钻（用 -think）、一个领域降秩（用 -rank）. |
| I162 | 未命名列 I | 放 |
| A（合并继承自 A155；A155:A178） | 原值见锚点 | 其他 |

<a id="entry-11b11fe2374737192228"></a>
### entry-11b11fe2374737192228 · book

技能  - 专家整理.xlsx / 技能 / 第 163 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| E163 | 功能点序号 | 2 |
| F163 | 功能点（英文） | cognitive_shift |
| G163 | 功能点（中文） | 认知位移 |
| H163 | 描述 | 拆一本书，以「问题」为轴心走一条线。五件事：作者在答什么问题（问题），这个问题之前各流派/社会共识怎么答（零点），作者带来什么独特洞见——公式/理论框架/模型/概念四选一——相对共识挪动了什么（位移/delta），落成哪句结论（落点），最后萃一个 takeaway 作为精神内核（行囊）。收尾画一张 ASCII 参考系图（千脑智能式）：各流派、旧共识、作者钉到同一张图的位置上，delta 是图上一段看得见的距离，再走两步做预测——看懂这本书在认知史里挪动了哪一步，还能拿它预测书外的新事。Use when user says '拆书', '拆这本', '分析这本书', '这本书在讲什么', '上帝之眼看这本书', '压缩一本书', 'book', or shares a book name wanting structural analysis. NOT FOR 章节摘要（用 Fabric extract_wisdom）、论文（用 -paper）、单一观点深钻（用 -think）、一个领域降秩（用 -rank）. |
| I163 | 未命名列 I | 放 |
| B（合并继承自 B162；B162:B164） | 原值见锚点 | 阅读分析 |
| C（合并继承自 C162；C162:C164） | 原值见锚点 | book |
| D（合并继承自 D162；D162:D164） | 原值见锚点 | book |
| A（合并继承自 A155；A155:A178） | 原值见锚点 | 其他 |

<a id="entry-be20ebe909f606fba3e6"></a>
### entry-be20ebe909f606fba3e6 · book

技能  - 专家整理.xlsx / 技能 / 第 164 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| E164 | 功能点序号 | 3 |
| F164 | 功能点（英文） | book_predict |
| G164 | 功能点（中文） | 书外预测 |
| H164 | 描述 | 拆一本书，以「问题」为轴心走一条线。五件事：作者在答什么问题（问题），这个问题之前各流派/社会共识怎么答（零点），作者带来什么独特洞见——公式/理论框架/模型/概念四选一——相对共识挪动了什么（位移/delta），落成哪句结论（落点），最后萃一个 takeaway 作为精神内核（行囊）。收尾画一张 ASCII 参考系图（千脑智能式）：各流派、旧共识、作者钉到同一张图的位置上，delta 是图上一段看得见的距离，再走两步做预测——看懂这本书在认知史里挪动了哪一步，还能拿它预测书外的新事。Use when user says '拆书', '拆这本', '分析这本书', '这本书在讲什么', '上帝之眼看这本书', '压缩一本书', 'book', or shares a book name wanting structural analysis. NOT FOR 章节摘要（用 Fabric extract_wisdom）、论文（用 -paper）、单一观点深钻（用 -think）、一个领域降秩（用 -rank）. |
| I164 | 未命名列 I | 放 |
| B（合并继承自 B162；B162:B164） | 原值见锚点 | 阅读分析 |
| C（合并继承自 C162；C162:C164） | 原值见锚点 | book |
| D（合并继承自 D162；D162:D164） | 原值见锚点 | book |
| A（合并继承自 A155；A155:A178） | 原值见锚点 | 其他 |

<a id="entry-bf3789608d65cf99bb15"></a>
### entry-bf3789608d65cf99bb15 · present

技能  - 专家整理.xlsx / 技能 / 第 165 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B165 | 场景标签 | 演示创作 |
| C165 | 技能名称 | present |
| D165 | 技能中文名 | present |
| E165 | 功能点序号 | 1 |
| F165 | 功能点（英文） | outline_present |
| G165 | 功能点（中文） | 大纲演讲化 |
| H165 | 描述 | 演讲铸造器（Outline-Faithful）。基于 orgmode/markdown outline 层级 1:1 视觉化呈现——色块大字、ultra-bold 错位，原文不动只做美化。三档主题色 black/red/yellow（默认 black 或按 filetags 推断），可用 -r/-b/-y 显式覆盖；可用 --cyber 走黑底绿字 cyber-hacker 风。使用时用户会说：'讲这个'、'present'、'做成演讲'、'呈现一下'、'铸成演示'、'做个 slides'、'标语流'、'宣言体'、'slogan'、'manifesto'、'按 outline 美化'。 |
| I165 | 未命名列 I | 放 |
| A（合并继承自 A155；A155:A178） | 原值见锚点 | 其他 |

<a id="entry-62a5bb313303e8c6bd7a"></a>
### entry-62a5bb313303e8c6bd7a · think

技能  - 专家整理.xlsx / 技能 / 第 166 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B166 | 场景标签 | 思维工具 |
| C166 | 技能名称 | think |
| D166 | 技能中文名 | think |
| E166 | 功能点序号 | 1 |
| F166 | 功能点（英文） | deep_drill |
| G166 | 功能点（中文） | 深度追问 |
| H166 | 描述 | 追本之箭——纵向深钻思维工具。给一个观点、现象或问题，像箭一样一路向下钻到不可再分的本质。Use when user says '想透', '追本', '本质是什么', '为什么会这样', '深挖', '钻到底', 'think deep', 'drill down', or wants to trace any idea/phenomenon vertically to its irreducible root. Also trigger when user provides a statement and wants depth analysis, not breadth survey. |
| I166 | 未命名列 I | 放 |
| A（合并继承自 A155；A155:A178） | 原值见锚点 | 其他 |

<a id="entry-ebf51aa99b71ac88cefa"></a>
### entry-ebf51aa99b71ac88cefa · think

技能  - 专家整理.xlsx / 技能 / 第 167 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| E167 | 功能点序号 | 2 |
| F167 | 功能点（英文） | essence_trace |
| G167 | 功能点（中文） | 本质挖掘 |
| H167 | 描述 | 追本之箭——纵向深钻思维工具。给一个观点、现象或问题，像箭一样一路向下钻到不可再分的本质。Use when user says '想透', '追本', '本质是什么', '为什么会这样', '深挖', '钻到底', 'think deep', 'drill down', or wants to trace any idea/phenomenon vertically to its irreducible root. Also trigger when user provides a statement and wants depth analysis, not breadth survey. |
| I167 | 未命名列 I | 放 |
| B（合并继承自 B166；B166:B167） | 原值见锚点 | 思维工具 |
| C（合并继承自 C166；C166:C167） | 原值见锚点 | think |
| D（合并继承自 D166；D166:D167） | 原值见锚点 | think |
| A（合并继承自 A155；A155:A178） | 原值见锚点 | 其他 |

<a id="entry-2fda441e350d39851589"></a>
### entry-2fda441e350d39851589 · word

技能  - 专家整理.xlsx / 技能 / 第 168 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B168 | 场景标签 | 语言学习 |
| C168 | 技能名称 | word |
| D168 | 技能中文名 | word |
| E168 | 功能点序号 | 1 |
| F168 | 功能点（英文） | word_mastery |
| G168 | 功能点（中文） | 单词深解 |
| H168 | 描述 | Deep-dive English word mastery tool. Deconstructs a single English word into core semantics and epiphany. Use when user asks to explain/master a specific English word. |
| I168 | 未命名列 I | 放 |
| A（合并继承自 A155；A155:A178） | 原值见锚点 | 其他 |

<a id="entry-7f8671773d0025e9b340"></a>
### entry-7f8671773d0025e9b340 · baoyu-infographic

技能  - 专家整理.xlsx / 技能 / 第 169 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B169 | 场景标签 | 信息可视化 |
| C169 | 技能名称 | baoyu-infographic |
| D169 | 技能中文名 | baoyu-infographic |
| E169 | 功能点序号 | 1 |
| F169 | 功能点（英文） | infographic_gen |
| G169 | 功能点（中文） | 信息图生成 |
| H169 | 描述 | Generate professional infographics with 21 layout types and 22 visual styles. Analyzes content, recommends layout×style combinations, and generates publication-ready infographics. Use when user asks to create "infographic", "信息图", "visual summary", "可视化", or "高密度信息大图". |
| I169 | 未命名列 I | 放 |
| A（合并继承自 A155；A155:A178） | 原值见锚点 | 其他 |

<a id="entry-e538a124f81fbc07dbda"></a>
### entry-e538a124f81fbc07dbda · explain-like-socrates

技能  - 专家整理.xlsx / 技能 / 第 170 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B170 | 场景标签 | 教学辅助 |
| C170 | 技能名称 | explain-like-socrates |
| D170 | 技能中文名 | explain-like-socrates |
| E170 | 功能点序号 | 1 |
| F170 | 功能点（英文） | socratic_dialogue |
| G170 | 功能点（中文） | 苏格拉底式讲解 |
| H170 | 描述 | Explains concepts using Socratic-style dialogue. Use when the user asks to explain, teach or help understand a concept like socrates. |
| I170 | 未命名列 I | 放 |
| A（合并继承自 A155；A155:A178） | 原值见锚点 | 其他 |

<a id="entry-9faf4d57d22a2ccc946f"></a>
### entry-9faf4d57d22a2ccc946f · math-intuition-builder

技能  - 专家整理.xlsx / 技能 / 第 171 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B171 | 场景标签 | 数学教学 |
| C171 | 技能名称 | math-intuition-builder |
| D171 | 技能中文名 | math-intuition-builder |
| E171 | 功能点序号 | 1 |
| F171 | 功能点（英文） | math_intuition |
| G171 | 功能点（中文） | 数学直觉构建 |
| H171 | 描述 | Develops mathematical understanding through examples, visualization, and analogy |
| I171 | 未命名列 I | 放 |
| A（合并继承自 A155；A155:A178） | 原值见锚点 | 其他 |

<a id="entry-4dda42d2139ee1719ccb"></a>
### entry-4dda42d2139ee1719ccb · ppt-master

技能  - 专家整理.xlsx / 技能 / 第 172 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B172 | 场景标签 | PPT制作 |
| C172 | 技能名称 | ppt-master |
| D172 | 技能中文名 | ppt-master |
| E172 | 功能点序号 | 1 |
| F172 | 功能点（英文） | doc_to_ppt/svg_generate |
| G172 | 功能点（中文） | 文档转PPT/SVG页面生成 |
| H172 | 描述 | AI-driven multi-format SVG content generation system. Converts source documents (PDF/DOCX/URL/Markdown) into high-quality SVG pages and exports to PPTX through multi-role collaboration. Use when user asks to "create PPT", "make presentation", "生成PPT", "做PPT", "制作演示文稿", or mentions "ppt-master". |
| I172 | 未命名列 I | 放 |
| A（合并继承自 A155；A155:A178） | 原值见锚点 | 其他 |

<a id="entry-e452ed74db551a09d8b4"></a>
### entry-e452ed74db551a09d8b4 · scientific-schematics

技能  - 专家整理.xlsx / 技能 / 第 173 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B173 | 场景标签 | 科研绘图 |
| C173 | 技能名称 | scientific-schematics |
| D173 | 技能中文名 | scientific-schematics |
| E173 | 功能点序号 | 1 |
| F173 | 功能点（英文） | sci_diagram |
| G173 | 功能点（中文） | 科研示意图 |
| H173 | 描述 | Create publication-quality scientific diagrams using Nano Banana 2 AI with smart iterative refinement. Uses Gemini 3.1 Pro Preview for quality review. Only regenerates if quality is below threshold for your document type. Specialized in neural network architectures, system diagrams, flowcharts, biological pathways, and complex scientific visualizations. |
| I173 | 未命名列 I | 放 |
| A（合并继承自 A155；A155:A178） | 原值见锚点 | 其他 |

<a id="entry-b9a782640533713e1961"></a>
### entry-b9a782640533713e1961 · statistical-analysis

技能  - 专家整理.xlsx / 技能 / 第 174 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B174 | 场景标签 | 数据分析 |
| C174 | 技能名称 | statistical-analysis |
| D174 | 技能中文名 | statistical-analysis |
| E174 | 功能点序号 | 1 |
| F174 | 功能点（英文） | descriptive_stats |
| G174 | 功能点（中文） | 描述统计 |
| H174 | 描述 | Apply statistical methods including descriptive stats, trend analysis, outlier detection, and hypothesis testing. Use when analyzing distributions, testing for significance, detecting anomalies, computing correlations, or interpreting statistical results. |
| I174 | 未命名列 I | 放 |
| A（合并继承自 A155；A155:A178） | 原值见锚点 | 其他 |

<a id="entry-def1e5caff7501c688e8"></a>
### entry-def1e5caff7501c688e8 · statistical-analysis

技能  - 专家整理.xlsx / 技能 / 第 175 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| E175 | 功能点序号 | 2 |
| F175 | 功能点（英文） | hypothesis_test |
| G175 | 功能点（中文） | 假设检验 |
| I175 | 未命名列 I | 放 |
| B（合并继承自 B174；B174:B176） | 原值见锚点 | 数据分析 |
| C（合并继承自 C174；C174:C176） | 原值见锚点 | statistical-analysis |
| D（合并继承自 D174；D174:D176） | 原值见锚点 | statistical-analysis |
| H（合并继承自 H174；H174:H176） | 原值见锚点 | Apply statistical methods including descriptive stats, trend analysis, outlier detection, and hypothesis testing. Use when analyzing distributions, testing for significance, detecting anomalies, computing correlations, or interpreting statistical results. |
| A（合并继承自 A155；A155:A178） | 原值见锚点 | 其他 |

<a id="entry-56daf1865a702c19f9b7"></a>
### entry-56daf1865a702c19f9b7 · statistical-analysis

技能  - 专家整理.xlsx / 技能 / 第 176 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| E176 | 功能点序号 | 3 |
| F176 | 功能点（英文） | outlier_detect |
| G176 | 功能点（中文） | 异常检测 |
| I176 | 未命名列 I | 放 |
| B（合并继承自 B174；B174:B176） | 原值见锚点 | 数据分析 |
| C（合并继承自 C174；C174:C176） | 原值见锚点 | statistical-analysis |
| D（合并继承自 D174；D174:D176） | 原值见锚点 | statistical-analysis |
| H（合并继承自 H174；H174:H176） | 原值见锚点 | Apply statistical methods including descriptive stats, trend analysis, outlier detection, and hypothesis testing. Use when analyzing distributions, testing for significance, detecting anomalies, computing correlations, or interpreting statistical results. |
| A（合并继承自 A155；A155:A178） | 原值见锚点 | 其他 |

<a id="entry-d9ad789cdf85ab4d4f37"></a>
### entry-d9ad789cdf85ab4d4f37 · find-skills

技能  - 专家整理.xlsx / 技能 / 第 177 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B177 | 场景标签 | 通用工具/Skill |
| C177 | 技能名称 | find-skills |
| D177 | 技能中文名 | find-skills |
| I177 | 未命名列 I | 放 |
| J177 | 未命名列 J | https://github.com/vercel-labs/skills/tree/main/skills/find-skills |
| A（合并继承自 A155；A155:A178） | 原值见锚点 | 其他 |

<a id="entry-6ae93ac075c6bfe59d48"></a>
### entry-6ae93ac075c6bfe59d48 · skill-creator

技能  - 专家整理.xlsx / 技能 / 第 178 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B178 | 场景标签 | 通用工具/Skill |
| C178 | 技能名称 | skill-creator |
| D178 | 技能中文名 | skill-creator |
| I178 | 未命名列 I | 放 |
| J178 | 未命名列 J | https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md |
| A（合并继承自 A155；A155:A178） | 原值见锚点 | 其他 |

<a id="entry-12c72804a2654c8327c4"></a>
### entry-12c72804a2654c8327c4 · polymas-agent-readme

技能  - 专家整理.xlsx / 专家 / 第 4 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B4 | 专家名称 | 基础工具 |
| C4 | 专家描述 | 展示平台8大模块、34项核心能力及典型问法；引导用户用自然语言描述需求，不执行业务操作;<br>页面导航指引：用户想做某操作但需在页面完成时，返回对应页面链接+一句话操作指引<br>仅用于联网搜索互联网公开内容，返回标题、描述、URL、封面、平台名称、相似度、发布时间等信息。纯搜索，不做任何内容操作。 |
| D4 | 附属技能 | polymas-agent-readme |
| A（合并继承自 A3；A3:A43） | 原值见锚点 | 业务 |

<a id="entry-105e741a0a283eed8e91"></a>
### entry-105e741a0a283eed8e91 · polymas-page-navigation

技能  - 专家整理.xlsx / 专家 / 第 5 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| D5 | 附属技能 | polymas-page-navigation |
| B（合并继承自 B4；B4:B6） | 原值见锚点 | 基础工具 |
| C（合并继承自 C4；C4:C6） | 原值见锚点 | 展示平台8大模块、34项核心能力及典型问法；引导用户用自然语言描述需求，不执行业务操作;<br>页面导航指引：用户想做某操作但需在页面完成时，返回对应页面链接+一句话操作指引<br>仅用于联网搜索互联网公开内容，返回标题、描述、URL、封面、平台名称、相似度、发布时间等信息。纯搜索，不做任何内容操作。 |
| A（合并继承自 A3；A3:A43） | 原值见锚点 | 业务 |

<a id="entry-d3871ed4c1c73c15c8cc"></a>
### entry-d3871ed4c1c73c15c8cc · polymas-tool-skills

技能  - 专家整理.xlsx / 专家 / 第 6 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| D6 | 附属技能 | polymas-tool-skills |
| B（合并继承自 B4；B4:B6） | 原值见锚点 | 基础工具 |
| C（合并继承自 C4；C4:C6） | 原值见锚点 | 展示平台8大模块、34项核心能力及典型问法；引导用户用自然语言描述需求，不执行业务操作;<br>页面导航指引：用户想做某操作但需在页面完成时，返回对应页面链接+一句话操作指引<br>仅用于联网搜索互联网公开内容，返回标题、描述、URL、封面、平台名称、相似度、发布时间等信息。纯搜索，不做任何内容操作。 |
| A（合并继承自 A3；A3:A43） | 原值见锚点 | 业务 |

<a id="entry-8512b0120cef57b4bd9e"></a>
### entry-8512b0120cef57b4bd9e · polymas-teacher-homework-skills

技能  - 专家整理.xlsx / 专家 / 第 7 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B7 | 专家名称 | 教学活动专员 |
| C7 | 专家描述 | 作业信息查询<br>教师端： 查询教师在课程下的作业信息，包括作业详细信息、作业关联班级信息、班级作业结束时间、完成率统计等数据。<br><br>学生端： 查询学生在课程下的所有作业信息，包括作业详细信息、作业关联班级信息、班级作业结束时间、完成率统计等数据。<br><br>考试信息查询<br>查询教师在课程下的考试信息，包括考试详细信息、关联班级安排、考试开始/结束时间、防作弊配置及组卷信息等数据。<br><br>考试/作业学情分析<br>教师查看考试或作业的详情与学情分析，包括基本信息、成绩统计、分段人数及各班级对比数据。<br><br>课程 OBE 达成度查询<br>查询课程 OBE 达成度，包括课程整体平均达成度、各课程目标平均达成度及各班级达成度。<br><br>教师多维成绩查询<br>支持查询总成绩、考勤、平时、作业、考试、自定义考核项等多维成绩数据，提供个人与班级分布两种视角。<br><br>通知发布<br>课程通知： 教师向课程下指定班级或全部学生发布通知，支持设置标题、内容、附件及目标班级。<br><br>班级群消息： 向班级群发送消息通知。<br><br>工作日历查询<br>查询教学日程，包括课程、会议、作业截止、考试、AI 提醒等日程安排。<br><br>课程分组查询<br>查询课程下的分组方案列表、分组方案详情、组内学生名单及未进组学生信息。<br><br>教师知识库查询<br>仅用于查询/搜索教师知识库内容，包括标题、资源类型、资源封面、资源链接、资源预览图标、资源名称、资源摘要。不支持新增、编辑、删除、上传、下载等操作。<br><br>学习进度查询<br>查询学习进度相关数据，包括学习资源完成率、必学完成率及按分组维度的完成率分布。 |
| D7 | 附属技能 | polymas-teacher-homework-skills |
| A（合并继承自 A3；A3:A43） | 原值见锚点 | 业务 |

<a id="entry-b1e65d1d28e144aea502"></a>
### entry-b1e65d1d28e144aea502 · polymas-teacher-exam-skills

技能  - 专家整理.xlsx / 专家 / 第 8 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| D8 | 附属技能 | polymas-teacher-exam-skills |
| A（合并继承自 A3；A3:A43） | 原值见锚点 | 业务 |
| B（合并继承自 B7；B7:B19） | 原值见锚点 | 教学活动专员 |
| C（合并继承自 C7；C7:C19） | 原值见锚点 | 作业信息查询<br>教师端： 查询教师在课程下的作业信息，包括作业详细信息、作业关联班级信息、班级作业结束时间、完成率统计等数据。<br><br>学生端： 查询学生在课程下的所有作业信息，包括作业详细信息、作业关联班级信息、班级作业结束时间、完成率统计等数据。<br><br>考试信息查询<br>查询教师在课程下的考试信息，包括考试详细信息、关联班级安排、考试开始/结束时间、防作弊配置及组卷信息等数据。<br><br>考试/作业学情分析<br>教师查看考试或作业的详情与学情分析，包括基本信息、成绩统计、分段人数及各班级对比数据。<br><br>课程 OBE 达成度查询<br>查询课程 OBE 达成度，包括课程整体平均达成度、各课程目标平均达成度及各班级达成度。<br><br>教师多维成绩查询<br>支持查询总成绩、考勤、平时、作业、考试、自定义考核项等多维成绩数据，提供个人与班级分布两种视角。<br><br>通知发布<br>课程通知： 教师向课程下指定班级或全部学生发布通知，支持设置标题、内容、附件及目标班级。<br><br>班级群消息： 向班级群发送消息通知。<br><br>工作日历查询<br>查询教学日程，包括课程、会议、作业截止、考试、AI 提醒等日程安排。<br><br>课程分组查询<br>查询课程下的分组方案列表、分组方案详情、组内学生名单及未进组学生信息。<br><br>教师知识库查询<br>仅用于查询/搜索教师知识库内容，包括标题、资源类型、资源封面、资源链接、资源预览图标、资源名称、资源摘要。不支持新增、编辑、删除、上传、下载等操作。<br><br>学习进度查询<br>查询学习进度相关数据，包括学习资源完成率、必学完成率及按分组维度的完成率分布。 |

<a id="entry-757507bfe1a36265b040"></a>
### entry-757507bfe1a36265b040 · polymas-course-obe-skills

技能  - 专家整理.xlsx / 专家 / 第 9 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| D9 | 附属技能 | polymas-course-obe-skills |
| A（合并继承自 A3；A3:A43） | 原值见锚点 | 业务 |
| B（合并继承自 B7；B7:B19） | 原值见锚点 | 教学活动专员 |
| C（合并继承自 C7；C7:C19） | 原值见锚点 | 作业信息查询<br>教师端： 查询教师在课程下的作业信息，包括作业详细信息、作业关联班级信息、班级作业结束时间、完成率统计等数据。<br><br>学生端： 查询学生在课程下的所有作业信息，包括作业详细信息、作业关联班级信息、班级作业结束时间、完成率统计等数据。<br><br>考试信息查询<br>查询教师在课程下的考试信息，包括考试详细信息、关联班级安排、考试开始/结束时间、防作弊配置及组卷信息等数据。<br><br>考试/作业学情分析<br>教师查看考试或作业的详情与学情分析，包括基本信息、成绩统计、分段人数及各班级对比数据。<br><br>课程 OBE 达成度查询<br>查询课程 OBE 达成度，包括课程整体平均达成度、各课程目标平均达成度及各班级达成度。<br><br>教师多维成绩查询<br>支持查询总成绩、考勤、平时、作业、考试、自定义考核项等多维成绩数据，提供个人与班级分布两种视角。<br><br>通知发布<br>课程通知： 教师向课程下指定班级或全部学生发布通知，支持设置标题、内容、附件及目标班级。<br><br>班级群消息： 向班级群发送消息通知。<br><br>工作日历查询<br>查询教学日程，包括课程、会议、作业截止、考试、AI 提醒等日程安排。<br><br>课程分组查询<br>查询课程下的分组方案列表、分组方案详情、组内学生名单及未进组学生信息。<br><br>教师知识库查询<br>仅用于查询/搜索教师知识库内容，包括标题、资源类型、资源封面、资源链接、资源预览图标、资源名称、资源摘要。不支持新增、编辑、删除、上传、下载等操作。<br><br>学习进度查询<br>查询学习进度相关数据，包括学习资源完成率、必学完成率及按分组维度的完成率分布。 |

<a id="entry-6a98dbb796e0549118cb"></a>
### entry-6a98dbb796e0549118cb · polymas-teacher-score-skills

技能  - 专家整理.xlsx / 专家 / 第 10 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| D10 | 附属技能 | polymas-teacher-score-skills |
| A（合并继承自 A3；A3:A43） | 原值见锚点 | 业务 |
| B（合并继承自 B7；B7:B19） | 原值见锚点 | 教学活动专员 |
| C（合并继承自 C7；C7:C19） | 原值见锚点 | 作业信息查询<br>教师端： 查询教师在课程下的作业信息，包括作业详细信息、作业关联班级信息、班级作业结束时间、完成率统计等数据。<br><br>学生端： 查询学生在课程下的所有作业信息，包括作业详细信息、作业关联班级信息、班级作业结束时间、完成率统计等数据。<br><br>考试信息查询<br>查询教师在课程下的考试信息，包括考试详细信息、关联班级安排、考试开始/结束时间、防作弊配置及组卷信息等数据。<br><br>考试/作业学情分析<br>教师查看考试或作业的详情与学情分析，包括基本信息、成绩统计、分段人数及各班级对比数据。<br><br>课程 OBE 达成度查询<br>查询课程 OBE 达成度，包括课程整体平均达成度、各课程目标平均达成度及各班级达成度。<br><br>教师多维成绩查询<br>支持查询总成绩、考勤、平时、作业、考试、自定义考核项等多维成绩数据，提供个人与班级分布两种视角。<br><br>通知发布<br>课程通知： 教师向课程下指定班级或全部学生发布通知，支持设置标题、内容、附件及目标班级。<br><br>班级群消息： 向班级群发送消息通知。<br><br>工作日历查询<br>查询教学日程，包括课程、会议、作业截止、考试、AI 提醒等日程安排。<br><br>课程分组查询<br>查询课程下的分组方案列表、分组方案详情、组内学生名单及未进组学生信息。<br><br>教师知识库查询<br>仅用于查询/搜索教师知识库内容，包括标题、资源类型、资源封面、资源链接、资源预览图标、资源名称、资源摘要。不支持新增、编辑、删除、上传、下载等操作。<br><br>学习进度查询<br>查询学习进度相关数据，包括学习资源完成率、必学完成率及按分组维度的完成率分布。 |

<a id="entry-53a706dca51954c522c5"></a>
### entry-53a706dca51954c522c5 · polymas-teacher-homework-detail-skills

技能  - 专家整理.xlsx / 专家 / 第 11 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| D11 | 附属技能 | polymas-teacher-homework-detail-skills |
| A（合并继承自 A3；A3:A43） | 原值见锚点 | 业务 |
| B（合并继承自 B7；B7:B19） | 原值见锚点 | 教学活动专员 |
| C（合并继承自 C7；C7:C19） | 原值见锚点 | 作业信息查询<br>教师端： 查询教师在课程下的作业信息，包括作业详细信息、作业关联班级信息、班级作业结束时间、完成率统计等数据。<br><br>学生端： 查询学生在课程下的所有作业信息，包括作业详细信息、作业关联班级信息、班级作业结束时间、完成率统计等数据。<br><br>考试信息查询<br>查询教师在课程下的考试信息，包括考试详细信息、关联班级安排、考试开始/结束时间、防作弊配置及组卷信息等数据。<br><br>考试/作业学情分析<br>教师查看考试或作业的详情与学情分析，包括基本信息、成绩统计、分段人数及各班级对比数据。<br><br>课程 OBE 达成度查询<br>查询课程 OBE 达成度，包括课程整体平均达成度、各课程目标平均达成度及各班级达成度。<br><br>教师多维成绩查询<br>支持查询总成绩、考勤、平时、作业、考试、自定义考核项等多维成绩数据，提供个人与班级分布两种视角。<br><br>通知发布<br>课程通知： 教师向课程下指定班级或全部学生发布通知，支持设置标题、内容、附件及目标班级。<br><br>班级群消息： 向班级群发送消息通知。<br><br>工作日历查询<br>查询教学日程，包括课程、会议、作业截止、考试、AI 提醒等日程安排。<br><br>课程分组查询<br>查询课程下的分组方案列表、分组方案详情、组内学生名单及未进组学生信息。<br><br>教师知识库查询<br>仅用于查询/搜索教师知识库内容，包括标题、资源类型、资源封面、资源链接、资源预览图标、资源名称、资源摘要。不支持新增、编辑、删除、上传、下载等操作。<br><br>学习进度查询<br>查询学习进度相关数据，包括学习资源完成率、必学完成率及按分组维度的完成率分布。 |

<a id="entry-475e8c6bb74875aef0ba"></a>
### entry-475e8c6bb74875aef0ba · polymas-teacher-exam-skills

技能  - 专家整理.xlsx / 专家 / 第 12 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| D12 | 附属技能 | polymas-teacher-exam-skills |
| A（合并继承自 A3；A3:A43） | 原值见锚点 | 业务 |
| B（合并继承自 B7；B7:B19） | 原值见锚点 | 教学活动专员 |
| C（合并继承自 C7；C7:C19） | 原值见锚点 | 作业信息查询<br>教师端： 查询教师在课程下的作业信息，包括作业详细信息、作业关联班级信息、班级作业结束时间、完成率统计等数据。<br><br>学生端： 查询学生在课程下的所有作业信息，包括作业详细信息、作业关联班级信息、班级作业结束时间、完成率统计等数据。<br><br>考试信息查询<br>查询教师在课程下的考试信息，包括考试详细信息、关联班级安排、考试开始/结束时间、防作弊配置及组卷信息等数据。<br><br>考试/作业学情分析<br>教师查看考试或作业的详情与学情分析，包括基本信息、成绩统计、分段人数及各班级对比数据。<br><br>课程 OBE 达成度查询<br>查询课程 OBE 达成度，包括课程整体平均达成度、各课程目标平均达成度及各班级达成度。<br><br>教师多维成绩查询<br>支持查询总成绩、考勤、平时、作业、考试、自定义考核项等多维成绩数据，提供个人与班级分布两种视角。<br><br>通知发布<br>课程通知： 教师向课程下指定班级或全部学生发布通知，支持设置标题、内容、附件及目标班级。<br><br>班级群消息： 向班级群发送消息通知。<br><br>工作日历查询<br>查询教学日程，包括课程、会议、作业截止、考试、AI 提醒等日程安排。<br><br>课程分组查询<br>查询课程下的分组方案列表、分组方案详情、组内学生名单及未进组学生信息。<br><br>教师知识库查询<br>仅用于查询/搜索教师知识库内容，包括标题、资源类型、资源封面、资源链接、资源预览图标、资源名称、资源摘要。不支持新增、编辑、删除、上传、下载等操作。<br><br>学习进度查询<br>查询学习进度相关数据，包括学习资源完成率、必学完成率及按分组维度的完成率分布。 |

<a id="entry-1c17a44a1418e8341da8"></a>
### entry-1c17a44a1418e8341da8 · polymas-teacher-activity-skills

技能  - 专家整理.xlsx / 专家 / 第 13 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| D13 | 附属技能 | polymas-teacher-activity-skills |
| A（合并继承自 A3；A3:A43） | 原值见锚点 | 业务 |
| B（合并继承自 B7；B7:B19） | 原值见锚点 | 教学活动专员 |
| C（合并继承自 C7；C7:C19） | 原值见锚点 | 作业信息查询<br>教师端： 查询教师在课程下的作业信息，包括作业详细信息、作业关联班级信息、班级作业结束时间、完成率统计等数据。<br><br>学生端： 查询学生在课程下的所有作业信息，包括作业详细信息、作业关联班级信息、班级作业结束时间、完成率统计等数据。<br><br>考试信息查询<br>查询教师在课程下的考试信息，包括考试详细信息、关联班级安排、考试开始/结束时间、防作弊配置及组卷信息等数据。<br><br>考试/作业学情分析<br>教师查看考试或作业的详情与学情分析，包括基本信息、成绩统计、分段人数及各班级对比数据。<br><br>课程 OBE 达成度查询<br>查询课程 OBE 达成度，包括课程整体平均达成度、各课程目标平均达成度及各班级达成度。<br><br>教师多维成绩查询<br>支持查询总成绩、考勤、平时、作业、考试、自定义考核项等多维成绩数据，提供个人与班级分布两种视角。<br><br>通知发布<br>课程通知： 教师向课程下指定班级或全部学生发布通知，支持设置标题、内容、附件及目标班级。<br><br>班级群消息： 向班级群发送消息通知。<br><br>工作日历查询<br>查询教学日程，包括课程、会议、作业截止、考试、AI 提醒等日程安排。<br><br>课程分组查询<br>查询课程下的分组方案列表、分组方案详情、组内学生名单及未进组学生信息。<br><br>教师知识库查询<br>仅用于查询/搜索教师知识库内容，包括标题、资源类型、资源封面、资源链接、资源预览图标、资源名称、资源摘要。不支持新增、编辑、删除、上传、下载等操作。<br><br>学习进度查询<br>查询学习进度相关数据，包括学习资源完成率、必学完成率及按分组维度的完成率分布。 |

<a id="entry-e0914371d368b57fc8a8"></a>
### entry-e0914371d368b57fc8a8 · polymas-teacher-class-group-assistant

技能  - 专家整理.xlsx / 专家 / 第 14 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| D14 | 附属技能 | polymas-teacher-class-group-assistant |
| A（合并继承自 A3；A3:A43） | 原值见锚点 | 业务 |
| B（合并继承自 B7；B7:B19） | 原值见锚点 | 教学活动专员 |
| C（合并继承自 C7；C7:C19） | 原值见锚点 | 作业信息查询<br>教师端： 查询教师在课程下的作业信息，包括作业详细信息、作业关联班级信息、班级作业结束时间、完成率统计等数据。<br><br>学生端： 查询学生在课程下的所有作业信息，包括作业详细信息、作业关联班级信息、班级作业结束时间、完成率统计等数据。<br><br>考试信息查询<br>查询教师在课程下的考试信息，包括考试详细信息、关联班级安排、考试开始/结束时间、防作弊配置及组卷信息等数据。<br><br>考试/作业学情分析<br>教师查看考试或作业的详情与学情分析，包括基本信息、成绩统计、分段人数及各班级对比数据。<br><br>课程 OBE 达成度查询<br>查询课程 OBE 达成度，包括课程整体平均达成度、各课程目标平均达成度及各班级达成度。<br><br>教师多维成绩查询<br>支持查询总成绩、考勤、平时、作业、考试、自定义考核项等多维成绩数据，提供个人与班级分布两种视角。<br><br>通知发布<br>课程通知： 教师向课程下指定班级或全部学生发布通知，支持设置标题、内容、附件及目标班级。<br><br>班级群消息： 向班级群发送消息通知。<br><br>工作日历查询<br>查询教学日程，包括课程、会议、作业截止、考试、AI 提醒等日程安排。<br><br>课程分组查询<br>查询课程下的分组方案列表、分组方案详情、组内学生名单及未进组学生信息。<br><br>教师知识库查询<br>仅用于查询/搜索教师知识库内容，包括标题、资源类型、资源封面、资源链接、资源预览图标、资源名称、资源摘要。不支持新增、编辑、删除、上传、下载等操作。<br><br>学习进度查询<br>查询学习进度相关数据，包括学习资源完成率、必学完成率及按分组维度的完成率分布。 |

<a id="entry-da9fd0fb71d9a18575f5"></a>
### entry-da9fd0fb71d9a18575f5 · polymas-get-student-course-homework

技能  - 专家整理.xlsx / 专家 / 第 15 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| D15 | 附属技能 | polymas-get-student-course-homework |
| A（合并继承自 A3；A3:A43） | 原值见锚点 | 业务 |
| B（合并继承自 B7；B7:B19） | 原值见锚点 | 教学活动专员 |
| C（合并继承自 C7；C7:C19） | 原值见锚点 | 作业信息查询<br>教师端： 查询教师在课程下的作业信息，包括作业详细信息、作业关联班级信息、班级作业结束时间、完成率统计等数据。<br><br>学生端： 查询学生在课程下的所有作业信息，包括作业详细信息、作业关联班级信息、班级作业结束时间、完成率统计等数据。<br><br>考试信息查询<br>查询教师在课程下的考试信息，包括考试详细信息、关联班级安排、考试开始/结束时间、防作弊配置及组卷信息等数据。<br><br>考试/作业学情分析<br>教师查看考试或作业的详情与学情分析，包括基本信息、成绩统计、分段人数及各班级对比数据。<br><br>课程 OBE 达成度查询<br>查询课程 OBE 达成度，包括课程整体平均达成度、各课程目标平均达成度及各班级达成度。<br><br>教师多维成绩查询<br>支持查询总成绩、考勤、平时、作业、考试、自定义考核项等多维成绩数据，提供个人与班级分布两种视角。<br><br>通知发布<br>课程通知： 教师向课程下指定班级或全部学生发布通知，支持设置标题、内容、附件及目标班级。<br><br>班级群消息： 向班级群发送消息通知。<br><br>工作日历查询<br>查询教学日程，包括课程、会议、作业截止、考试、AI 提醒等日程安排。<br><br>课程分组查询<br>查询课程下的分组方案列表、分组方案详情、组内学生名单及未进组学生信息。<br><br>教师知识库查询<br>仅用于查询/搜索教师知识库内容，包括标题、资源类型、资源封面、资源链接、资源预览图标、资源名称、资源摘要。不支持新增、编辑、删除、上传、下载等操作。<br><br>学习进度查询<br>查询学习进度相关数据，包括学习资源完成率、必学完成率及按分组维度的完成率分布。 |

<a id="entry-0527f12846fd7ef11f39"></a>
### entry-0527f12846fd7ef11f39 · polymas-teacher-work-calendar

技能  - 专家整理.xlsx / 专家 / 第 16 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| D16 | 附属技能 | polymas-teacher-work-calendar |
| A（合并继承自 A3；A3:A43） | 原值见锚点 | 业务 |
| B（合并继承自 B7；B7:B19） | 原值见锚点 | 教学活动专员 |
| C（合并继承自 C7；C7:C19） | 原值见锚点 | 作业信息查询<br>教师端： 查询教师在课程下的作业信息，包括作业详细信息、作业关联班级信息、班级作业结束时间、完成率统计等数据。<br><br>学生端： 查询学生在课程下的所有作业信息，包括作业详细信息、作业关联班级信息、班级作业结束时间、完成率统计等数据。<br><br>考试信息查询<br>查询教师在课程下的考试信息，包括考试详细信息、关联班级安排、考试开始/结束时间、防作弊配置及组卷信息等数据。<br><br>考试/作业学情分析<br>教师查看考试或作业的详情与学情分析，包括基本信息、成绩统计、分段人数及各班级对比数据。<br><br>课程 OBE 达成度查询<br>查询课程 OBE 达成度，包括课程整体平均达成度、各课程目标平均达成度及各班级达成度。<br><br>教师多维成绩查询<br>支持查询总成绩、考勤、平时、作业、考试、自定义考核项等多维成绩数据，提供个人与班级分布两种视角。<br><br>通知发布<br>课程通知： 教师向课程下指定班级或全部学生发布通知，支持设置标题、内容、附件及目标班级。<br><br>班级群消息： 向班级群发送消息通知。<br><br>工作日历查询<br>查询教学日程，包括课程、会议、作业截止、考试、AI 提醒等日程安排。<br><br>课程分组查询<br>查询课程下的分组方案列表、分组方案详情、组内学生名单及未进组学生信息。<br><br>教师知识库查询<br>仅用于查询/搜索教师知识库内容，包括标题、资源类型、资源封面、资源链接、资源预览图标、资源名称、资源摘要。不支持新增、编辑、删除、上传、下载等操作。<br><br>学习进度查询<br>查询学习进度相关数据，包括学习资源完成率、必学完成率及按分组维度的完成率分布。 |

<a id="entry-b3a6b832bd9a09e3b8f5"></a>
### entry-b3a6b832bd9a09e3b8f5 · polymas-teacher-class-group-skills

技能  - 专家整理.xlsx / 专家 / 第 17 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| D17 | 附属技能 | polymas-teacher-class-group-skills |
| A（合并继承自 A3；A3:A43） | 原值见锚点 | 业务 |
| B（合并继承自 B7；B7:B19） | 原值见锚点 | 教学活动专员 |
| C（合并继承自 C7；C7:C19） | 原值见锚点 | 作业信息查询<br>教师端： 查询教师在课程下的作业信息，包括作业详细信息、作业关联班级信息、班级作业结束时间、完成率统计等数据。<br><br>学生端： 查询学生在课程下的所有作业信息，包括作业详细信息、作业关联班级信息、班级作业结束时间、完成率统计等数据。<br><br>考试信息查询<br>查询教师在课程下的考试信息，包括考试详细信息、关联班级安排、考试开始/结束时间、防作弊配置及组卷信息等数据。<br><br>考试/作业学情分析<br>教师查看考试或作业的详情与学情分析，包括基本信息、成绩统计、分段人数及各班级对比数据。<br><br>课程 OBE 达成度查询<br>查询课程 OBE 达成度，包括课程整体平均达成度、各课程目标平均达成度及各班级达成度。<br><br>教师多维成绩查询<br>支持查询总成绩、考勤、平时、作业、考试、自定义考核项等多维成绩数据，提供个人与班级分布两种视角。<br><br>通知发布<br>课程通知： 教师向课程下指定班级或全部学生发布通知，支持设置标题、内容、附件及目标班级。<br><br>班级群消息： 向班级群发送消息通知。<br><br>工作日历查询<br>查询教学日程，包括课程、会议、作业截止、考试、AI 提醒等日程安排。<br><br>课程分组查询<br>查询课程下的分组方案列表、分组方案详情、组内学生名单及未进组学生信息。<br><br>教师知识库查询<br>仅用于查询/搜索教师知识库内容，包括标题、资源类型、资源封面、资源链接、资源预览图标、资源名称、资源摘要。不支持新增、编辑、删除、上传、下载等操作。<br><br>学习进度查询<br>查询学习进度相关数据，包括学习资源完成率、必学完成率及按分组维度的完成率分布。 |

<a id="entry-244d137c9b54f81507c6"></a>
### entry-244d137c9b54f81507c6 · polymas-teacher-resource-skills

技能  - 专家整理.xlsx / 专家 / 第 18 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| D18 | 附属技能 | polymas-teacher-resource-skills |
| A（合并继承自 A3；A3:A43） | 原值见锚点 | 业务 |
| B（合并继承自 B7；B7:B19） | 原值见锚点 | 教学活动专员 |
| C（合并继承自 C7；C7:C19） | 原值见锚点 | 作业信息查询<br>教师端： 查询教师在课程下的作业信息，包括作业详细信息、作业关联班级信息、班级作业结束时间、完成率统计等数据。<br><br>学生端： 查询学生在课程下的所有作业信息，包括作业详细信息、作业关联班级信息、班级作业结束时间、完成率统计等数据。<br><br>考试信息查询<br>查询教师在课程下的考试信息，包括考试详细信息、关联班级安排、考试开始/结束时间、防作弊配置及组卷信息等数据。<br><br>考试/作业学情分析<br>教师查看考试或作业的详情与学情分析，包括基本信息、成绩统计、分段人数及各班级对比数据。<br><br>课程 OBE 达成度查询<br>查询课程 OBE 达成度，包括课程整体平均达成度、各课程目标平均达成度及各班级达成度。<br><br>教师多维成绩查询<br>支持查询总成绩、考勤、平时、作业、考试、自定义考核项等多维成绩数据，提供个人与班级分布两种视角。<br><br>通知发布<br>课程通知： 教师向课程下指定班级或全部学生发布通知，支持设置标题、内容、附件及目标班级。<br><br>班级群消息： 向班级群发送消息通知。<br><br>工作日历查询<br>查询教学日程，包括课程、会议、作业截止、考试、AI 提醒等日程安排。<br><br>课程分组查询<br>查询课程下的分组方案列表、分组方案详情、组内学生名单及未进组学生信息。<br><br>教师知识库查询<br>仅用于查询/搜索教师知识库内容，包括标题、资源类型、资源封面、资源链接、资源预览图标、资源名称、资源摘要。不支持新增、编辑、删除、上传、下载等操作。<br><br>学习进度查询<br>查询学习进度相关数据，包括学习资源完成率、必学完成率及按分组维度的完成率分布。 |

<a id="entry-ace27f27cd5b62fa6b3c"></a>
### entry-ace27f27cd5b62fa6b3c · polymas-teacher-teaching-observation-skills

技能  - 专家整理.xlsx / 专家 / 第 19 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| D19 | 附属技能 | polymas-teacher-teaching-observation-skills |
| A（合并继承自 A3；A3:A43） | 原值见锚点 | 业务 |
| B（合并继承自 B7；B7:B19） | 原值见锚点 | 教学活动专员 |
| C（合并继承自 C7；C7:C19） | 原值见锚点 | 作业信息查询<br>教师端： 查询教师在课程下的作业信息，包括作业详细信息、作业关联班级信息、班级作业结束时间、完成率统计等数据。<br><br>学生端： 查询学生在课程下的所有作业信息，包括作业详细信息、作业关联班级信息、班级作业结束时间、完成率统计等数据。<br><br>考试信息查询<br>查询教师在课程下的考试信息，包括考试详细信息、关联班级安排、考试开始/结束时间、防作弊配置及组卷信息等数据。<br><br>考试/作业学情分析<br>教师查看考试或作业的详情与学情分析，包括基本信息、成绩统计、分段人数及各班级对比数据。<br><br>课程 OBE 达成度查询<br>查询课程 OBE 达成度，包括课程整体平均达成度、各课程目标平均达成度及各班级达成度。<br><br>教师多维成绩查询<br>支持查询总成绩、考勤、平时、作业、考试、自定义考核项等多维成绩数据，提供个人与班级分布两种视角。<br><br>通知发布<br>课程通知： 教师向课程下指定班级或全部学生发布通知，支持设置标题、内容、附件及目标班级。<br><br>班级群消息： 向班级群发送消息通知。<br><br>工作日历查询<br>查询教学日程，包括课程、会议、作业截止、考试、AI 提醒等日程安排。<br><br>课程分组查询<br>查询课程下的分组方案列表、分组方案详情、组内学生名单及未进组学生信息。<br><br>教师知识库查询<br>仅用于查询/搜索教师知识库内容，包括标题、资源类型、资源封面、资源链接、资源预览图标、资源名称、资源摘要。不支持新增、编辑、删除、上传、下载等操作。<br><br>学习进度查询<br>查询学习进度相关数据，包括学习资源完成率、必学完成率及按分组维度的完成率分布。 |

<a id="entry-155d6cec25e027511598"></a>
### entry-155d6cec25e027511598 · polymas-teacher-learning-analytics-skills

技能  - 专家整理.xlsx / 专家 / 第 20 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B20 | 专家名称 | 学情分析专员 |
| C20 | 专家描述 | 1. 学生学情分析报告查询<br>教师可按课程、班级查看指定学生的学情分析报告，包括作业完成情况、成绩趋势、学习活跃度等数据。<br><br>2. 学生综合学情视图<br>将单个学生的作业完成率、考试成绩、课堂互动次数整合展示，提供该学生的综合学情视图。<br><br>3. 学习进度查询<br>查询学习进度相关数据，包括学习资源完成率、必学完成率，以及按分组维度的完成率分布。<br><br>4. 课堂表现查询<br>按课程、课堂查看学生课堂表现，包括成绩得分、互动参与、弹幕次数、在线时长等；支持分页查询。<br><br>5. 课堂核心数据分析<br>查询课堂基本数据统计与授课方式分布等核心分析数据。<br><br>6. 统计分析<br>运用描述性统计、趋势分析、异常值检测、假设检验等统计方法，用于分析数据分布、检验显著性、识别异常、计算相关性并解读统计结果。适用于需要对学情、成绩、活跃度等数据进行量化分析的场景。 |
| D20 | 附属技能 | polymas-teacher-learning-analytics-skills |
| A（合并继承自 A3；A3:A43） | 原值见锚点 | 业务 |

<a id="entry-3580c0dd48872d89e125"></a>
### entry-3580c0dd48872d89e125 · polymas-teacher-teaching-observation-skills

技能  - 专家整理.xlsx / 专家 / 第 21 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| D21 | 附属技能 | polymas-teacher-teaching-observation-skills |
| B（合并继承自 B20；B20:B24） | 原值见锚点 | 学情分析专员 |
| A（合并继承自 A3；A3:A43） | 原值见锚点 | 业务 |
| C（合并继承自 C20；C20:C24） | 原值见锚点 | 1. 学生学情分析报告查询<br>教师可按课程、班级查看指定学生的学情分析报告，包括作业完成情况、成绩趋势、学习活跃度等数据。<br><br>2. 学生综合学情视图<br>将单个学生的作业完成率、考试成绩、课堂互动次数整合展示，提供该学生的综合学情视图。<br><br>3. 学习进度查询<br>查询学习进度相关数据，包括学习资源完成率、必学完成率，以及按分组维度的完成率分布。<br><br>4. 课堂表现查询<br>按课程、课堂查看学生课堂表现，包括成绩得分、互动参与、弹幕次数、在线时长等；支持分页查询。<br><br>5. 课堂核心数据分析<br>查询课堂基本数据统计与授课方式分布等核心分析数据。<br><br>6. 统计分析<br>运用描述性统计、趋势分析、异常值检测、假设检验等统计方法，用于分析数据分布、检验显著性、识别异常、计算相关性并解读统计结果。适用于需要对学情、成绩、活跃度等数据进行量化分析的场景。 |

<a id="entry-02906e57e8c7723cf11b"></a>
### entry-02906e57e8c7723cf11b · polymas-teacher-lession-analysis

技能  - 专家整理.xlsx / 专家 / 第 22 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| D22 | 附属技能 | polymas-teacher-lession-analysis |
| B（合并继承自 B20；B20:B24） | 原值见锚点 | 学情分析专员 |
| A（合并继承自 A3；A3:A43） | 原值见锚点 | 业务 |
| C（合并继承自 C20；C20:C24） | 原值见锚点 | 1. 学生学情分析报告查询<br>教师可按课程、班级查看指定学生的学情分析报告，包括作业完成情况、成绩趋势、学习活跃度等数据。<br><br>2. 学生综合学情视图<br>将单个学生的作业完成率、考试成绩、课堂互动次数整合展示，提供该学生的综合学情视图。<br><br>3. 学习进度查询<br>查询学习进度相关数据，包括学习资源完成率、必学完成率，以及按分组维度的完成率分布。<br><br>4. 课堂表现查询<br>按课程、课堂查看学生课堂表现，包括成绩得分、互动参与、弹幕次数、在线时长等；支持分页查询。<br><br>5. 课堂核心数据分析<br>查询课堂基本数据统计与授课方式分布等核心分析数据。<br><br>6. 统计分析<br>运用描述性统计、趋势分析、异常值检测、假设检验等统计方法，用于分析数据分布、检验显著性、识别异常、计算相关性并解读统计结果。适用于需要对学情、成绩、活跃度等数据进行量化分析的场景。 |

<a id="entry-b8d9a3c6fba31374c4a7"></a>
### entry-b8d9a3c6fba31374c4a7 · polymas-teacher-classroom-report-skills

技能  - 专家整理.xlsx / 专家 / 第 23 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| D23 | 附属技能 | polymas-teacher-classroom-report-skills |
| B（合并继承自 B20；B20:B24） | 原值见锚点 | 学情分析专员 |
| A（合并继承自 A3；A3:A43） | 原值见锚点 | 业务 |
| C（合并继承自 C20；C20:C24） | 原值见锚点 | 1. 学生学情分析报告查询<br>教师可按课程、班级查看指定学生的学情分析报告，包括作业完成情况、成绩趋势、学习活跃度等数据。<br><br>2. 学生综合学情视图<br>将单个学生的作业完成率、考试成绩、课堂互动次数整合展示，提供该学生的综合学情视图。<br><br>3. 学习进度查询<br>查询学习进度相关数据，包括学习资源完成率、必学完成率，以及按分组维度的完成率分布。<br><br>4. 课堂表现查询<br>按课程、课堂查看学生课堂表现，包括成绩得分、互动参与、弹幕次数、在线时长等；支持分页查询。<br><br>5. 课堂核心数据分析<br>查询课堂基本数据统计与授课方式分布等核心分析数据。<br><br>6. 统计分析<br>运用描述性统计、趋势分析、异常值检测、假设检验等统计方法，用于分析数据分布、检验显著性、识别异常、计算相关性并解读统计结果。适用于需要对学情、成绩、活跃度等数据进行量化分析的场景。 |

<a id="entry-1b9f743345e7884db178"></a>
### entry-1b9f743345e7884db178 · statistical-analysis

技能  - 专家整理.xlsx / 专家 / 第 24 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| D24 | 附属技能 | statistical-analysis |
| B（合并继承自 B20；B20:B24） | 原值见锚点 | 学情分析专员 |
| A（合并继承自 A3；A3:A43） | 原值见锚点 | 业务 |
| C（合并继承自 C20；C20:C24） | 原值见锚点 | 1. 学生学情分析报告查询<br>教师可按课程、班级查看指定学生的学情分析报告，包括作业完成情况、成绩趋势、学习活跃度等数据。<br><br>2. 学生综合学情视图<br>将单个学生的作业完成率、考试成绩、课堂互动次数整合展示，提供该学生的综合学情视图。<br><br>3. 学习进度查询<br>查询学习进度相关数据，包括学习资源完成率、必学完成率，以及按分组维度的完成率分布。<br><br>4. 课堂表现查询<br>按课程、课堂查看学生课堂表现，包括成绩得分、互动参与、弹幕次数、在线时长等；支持分页查询。<br><br>5. 课堂核心数据分析<br>查询课堂基本数据统计与授课方式分布等核心分析数据。<br><br>6. 统计分析<br>运用描述性统计、趋势分析、异常值检测、假设检验等统计方法，用于分析数据分布、检验显著性、识别异常、计算相关性并解读统计结果。适用于需要对学情、成绩、活跃度等数据进行量化分析的场景。 |

<a id="entry-b4b6401ab39e421190e8"></a>
### entry-b4b6401ab39e421190e8 · polymas-teacher-classroom-report-skills

技能  - 专家整理.xlsx / 专家 / 第 25 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B25 | 专家名称 | 课中智能体 |
| C25 | 专家描述 | 课堂核心数据分析：查询课堂基本数据统计与授课方式分布;<br>按课程、课堂查看学生课堂表现：成绩得分、互动参与、弹幕次数、在线时长；支持分页 |
| D25 | 附属技能 | polymas-teacher-classroom-report-skills |
| A（合并继承自 A3；A3:A43） | 原值见锚点 | 业务 |

<a id="entry-84dd097a0145f23980d9"></a>
### entry-84dd097a0145f23980d9 · polymas-teacher-lession-analysis

技能  - 专家整理.xlsx / 专家 / 第 26 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| D26 | 附属技能 | polymas-teacher-lession-analysis |
| B（合并继承自 B25；B25:B26） | 原值见锚点 | 课中智能体 |
| A（合并继承自 A3；A3:A43） | 原值见锚点 | 业务 |
| C（合并继承自 C25；C25:C26） | 原值见锚点 | 课堂核心数据分析：查询课堂基本数据统计与授课方式分布;<br>按课程、课堂查看学生课堂表现：成绩得分、互动参与、弹幕次数、在线时长；支持分页 |

<a id="entry-87617bbae8233ec1cea0"></a>
### entry-87617bbae8233ec1cea0 · polymas-teacher-course-skills

技能  - 专家整理.xlsx / 专家 / 第 27 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B27 | 专家名称 | 课程管理专员 |
| C27 | 专家描述 | 1. 课程创建<br>教师创建课程，支持邀请码建课和 AI 智课建课两种方式。<br><br>2. 课程列表查询<br>查询课程列表信息，包括当前学期课程、归档课程和共享课列表；其中共享课仅返回 state == 3 的课程。<br><br>3. 课程概况查询<br>查询课程概况信息，包括教学计划状态、单元/章节数量、课代表对话次数、AI 知识库资源数量及教学活动列表。<br><br>4. 课程知识结构查询<br>查询指定课程的教学单元、主题、知识点及知识点关系的层级结构；仅可查询当前用户有权访问的课程。<br><br>5. 教学计划查询<br>查询课程的教学单元、主题（小节）、知识点结构，以及关联的作业与考试活动。<br><br>6. 班级创建<br>教师在课程下创建班级，支持按课程名称定位课程、输入班级名称后完成创建；创建后可按需手动添加学生，并支持循环添加。<br><br>7. 学生入班信息查询<br>按入班状态查询课程/班级下的学生信息，支持已入班、待审核、待激活三种状态；返回学生名单、标签、院系等数据。<br><br>8. 课程分组查询<br>查询课程下的分组方案列表、分组方案详情、组内学生名单及未进组学生信息。<br><br>9. 学生基础技能<br>根据用户需求，智能选择并调用课程搜索、作业查询等相关功能。 |
| D27 | 附属技能 | polymas-teacher-course-skills |
| A（合并继承自 A3；A3:A43） | 原值见锚点 | 业务 |

<a id="entry-93925541ad541303a7bd"></a>
### entry-93925541ad541303a7bd · polymas-course-list-skills

技能  - 专家整理.xlsx / 专家 / 第 28 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| D28 | 附属技能 | polymas-course-list-skills |
| B（合并继承自 B27；B27:B35） | 原值见锚点 | 课程管理专员 |
| A（合并继承自 A3；A3:A43） | 原值见锚点 | 业务 |
| C（合并继承自 C27；C27:C35） | 原值见锚点 | 1. 课程创建<br>教师创建课程，支持邀请码建课和 AI 智课建课两种方式。<br><br>2. 课程列表查询<br>查询课程列表信息，包括当前学期课程、归档课程和共享课列表；其中共享课仅返回 state == 3 的课程。<br><br>3. 课程概况查询<br>查询课程概况信息，包括教学计划状态、单元/章节数量、课代表对话次数、AI 知识库资源数量及教学活动列表。<br><br>4. 课程知识结构查询<br>查询指定课程的教学单元、主题、知识点及知识点关系的层级结构；仅可查询当前用户有权访问的课程。<br><br>5. 教学计划查询<br>查询课程的教学单元、主题（小节）、知识点结构，以及关联的作业与考试活动。<br><br>6. 班级创建<br>教师在课程下创建班级，支持按课程名称定位课程、输入班级名称后完成创建；创建后可按需手动添加学生，并支持循环添加。<br><br>7. 学生入班信息查询<br>按入班状态查询课程/班级下的学生信息，支持已入班、待审核、待激活三种状态；返回学生名单、标签、院系等数据。<br><br>8. 课程分组查询<br>查询课程下的分组方案列表、分组方案详情、组内学生名单及未进组学生信息。<br><br>9. 学生基础技能<br>根据用户需求，智能选择并调用课程搜索、作业查询等相关功能。 |

<a id="entry-ff84628095063131da17"></a>
### entry-ff84628095063131da17 · polymas-course-overview-skills

技能  - 专家整理.xlsx / 专家 / 第 29 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| D29 | 附属技能 | polymas-course-overview-skills |
| B（合并继承自 B27；B27:B35） | 原值见锚点 | 课程管理专员 |
| A（合并继承自 A3；A3:A43） | 原值见锚点 | 业务 |
| C（合并继承自 C27；C27:C35） | 原值见锚点 | 1. 课程创建<br>教师创建课程，支持邀请码建课和 AI 智课建课两种方式。<br><br>2. 课程列表查询<br>查询课程列表信息，包括当前学期课程、归档课程和共享课列表；其中共享课仅返回 state == 3 的课程。<br><br>3. 课程概况查询<br>查询课程概况信息，包括教学计划状态、单元/章节数量、课代表对话次数、AI 知识库资源数量及教学活动列表。<br><br>4. 课程知识结构查询<br>查询指定课程的教学单元、主题、知识点及知识点关系的层级结构；仅可查询当前用户有权访问的课程。<br><br>5. 教学计划查询<br>查询课程的教学单元、主题（小节）、知识点结构，以及关联的作业与考试活动。<br><br>6. 班级创建<br>教师在课程下创建班级，支持按课程名称定位课程、输入班级名称后完成创建；创建后可按需手动添加学生，并支持循环添加。<br><br>7. 学生入班信息查询<br>按入班状态查询课程/班级下的学生信息，支持已入班、待审核、待激活三种状态；返回学生名单、标签、院系等数据。<br><br>8. 课程分组查询<br>查询课程下的分组方案列表、分组方案详情、组内学生名单及未进组学生信息。<br><br>9. 学生基础技能<br>根据用户需求，智能选择并调用课程搜索、作业查询等相关功能。 |

<a id="entry-430c84c7f12d3d2e2274"></a>
### entry-430c84c7f12d3d2e2274 · polymas-query-teaching-unit

技能  - 专家整理.xlsx / 专家 / 第 30 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| D30 | 附属技能 | polymas-query-teaching-unit |
| B（合并继承自 B27；B27:B35） | 原值见锚点 | 课程管理专员 |
| A（合并继承自 A3；A3:A43） | 原值见锚点 | 业务 |
| C（合并继承自 C27；C27:C35） | 原值见锚点 | 1. 课程创建<br>教师创建课程，支持邀请码建课和 AI 智课建课两种方式。<br><br>2. 课程列表查询<br>查询课程列表信息，包括当前学期课程、归档课程和共享课列表；其中共享课仅返回 state == 3 的课程。<br><br>3. 课程概况查询<br>查询课程概况信息，包括教学计划状态、单元/章节数量、课代表对话次数、AI 知识库资源数量及教学活动列表。<br><br>4. 课程知识结构查询<br>查询指定课程的教学单元、主题、知识点及知识点关系的层级结构；仅可查询当前用户有权访问的课程。<br><br>5. 教学计划查询<br>查询课程的教学单元、主题（小节）、知识点结构，以及关联的作业与考试活动。<br><br>6. 班级创建<br>教师在课程下创建班级，支持按课程名称定位课程、输入班级名称后完成创建；创建后可按需手动添加学生，并支持循环添加。<br><br>7. 学生入班信息查询<br>按入班状态查询课程/班级下的学生信息，支持已入班、待审核、待激活三种状态；返回学生名单、标签、院系等数据。<br><br>8. 课程分组查询<br>查询课程下的分组方案列表、分组方案详情、组内学生名单及未进组学生信息。<br><br>9. 学生基础技能<br>根据用户需求，智能选择并调用课程搜索、作业查询等相关功能。 |

<a id="entry-b0d6920c39d613bed65d"></a>
### entry-b0d6920c39d613bed65d · polymas-teacher-teaching-plan

技能  - 专家整理.xlsx / 专家 / 第 31 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| D31 | 附属技能 | polymas-teacher-teaching-plan |
| B（合并继承自 B27；B27:B35） | 原值见锚点 | 课程管理专员 |
| A（合并继承自 A3；A3:A43） | 原值见锚点 | 业务 |
| C（合并继承自 C27；C27:C35） | 原值见锚点 | 1. 课程创建<br>教师创建课程，支持邀请码建课和 AI 智课建课两种方式。<br><br>2. 课程列表查询<br>查询课程列表信息，包括当前学期课程、归档课程和共享课列表；其中共享课仅返回 state == 3 的课程。<br><br>3. 课程概况查询<br>查询课程概况信息，包括教学计划状态、单元/章节数量、课代表对话次数、AI 知识库资源数量及教学活动列表。<br><br>4. 课程知识结构查询<br>查询指定课程的教学单元、主题、知识点及知识点关系的层级结构；仅可查询当前用户有权访问的课程。<br><br>5. 教学计划查询<br>查询课程的教学单元、主题（小节）、知识点结构，以及关联的作业与考试活动。<br><br>6. 班级创建<br>教师在课程下创建班级，支持按课程名称定位课程、输入班级名称后完成创建；创建后可按需手动添加学生，并支持循环添加。<br><br>7. 学生入班信息查询<br>按入班状态查询课程/班级下的学生信息，支持已入班、待审核、待激活三种状态；返回学生名单、标签、院系等数据。<br><br>8. 课程分组查询<br>查询课程下的分组方案列表、分组方案详情、组内学生名单及未进组学生信息。<br><br>9. 学生基础技能<br>根据用户需求，智能选择并调用课程搜索、作业查询等相关功能。 |

<a id="entry-bbe8fb262a0d1be1a361"></a>
### entry-bbe8fb262a0d1be1a361 · polymas-teacher-class-skills

技能  - 专家整理.xlsx / 专家 / 第 32 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| D32 | 附属技能 | polymas-teacher-class-skills |
| B（合并继承自 B27；B27:B35） | 原值见锚点 | 课程管理专员 |
| A（合并继承自 A3；A3:A43） | 原值见锚点 | 业务 |
| C（合并继承自 C27；C27:C35） | 原值见锚点 | 1. 课程创建<br>教师创建课程，支持邀请码建课和 AI 智课建课两种方式。<br><br>2. 课程列表查询<br>查询课程列表信息，包括当前学期课程、归档课程和共享课列表；其中共享课仅返回 state == 3 的课程。<br><br>3. 课程概况查询<br>查询课程概况信息，包括教学计划状态、单元/章节数量、课代表对话次数、AI 知识库资源数量及教学活动列表。<br><br>4. 课程知识结构查询<br>查询指定课程的教学单元、主题、知识点及知识点关系的层级结构；仅可查询当前用户有权访问的课程。<br><br>5. 教学计划查询<br>查询课程的教学单元、主题（小节）、知识点结构，以及关联的作业与考试活动。<br><br>6. 班级创建<br>教师在课程下创建班级，支持按课程名称定位课程、输入班级名称后完成创建；创建后可按需手动添加学生，并支持循环添加。<br><br>7. 学生入班信息查询<br>按入班状态查询课程/班级下的学生信息，支持已入班、待审核、待激活三种状态；返回学生名单、标签、院系等数据。<br><br>8. 课程分组查询<br>查询课程下的分组方案列表、分组方案详情、组内学生名单及未进组学生信息。<br><br>9. 学生基础技能<br>根据用户需求，智能选择并调用课程搜索、作业查询等相关功能。 |

<a id="entry-88a1845c66bf092cffb3"></a>
### entry-88a1845c66bf092cffb3 · polymas-teacher-class-student-skills

技能  - 专家整理.xlsx / 专家 / 第 33 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| D33 | 附属技能 | polymas-teacher-class-student-skills |
| B（合并继承自 B27；B27:B35） | 原值见锚点 | 课程管理专员 |
| A（合并继承自 A3；A3:A43） | 原值见锚点 | 业务 |
| C（合并继承自 C27；C27:C35） | 原值见锚点 | 1. 课程创建<br>教师创建课程，支持邀请码建课和 AI 智课建课两种方式。<br><br>2. 课程列表查询<br>查询课程列表信息，包括当前学期课程、归档课程和共享课列表；其中共享课仅返回 state == 3 的课程。<br><br>3. 课程概况查询<br>查询课程概况信息，包括教学计划状态、单元/章节数量、课代表对话次数、AI 知识库资源数量及教学活动列表。<br><br>4. 课程知识结构查询<br>查询指定课程的教学单元、主题、知识点及知识点关系的层级结构；仅可查询当前用户有权访问的课程。<br><br>5. 教学计划查询<br>查询课程的教学单元、主题（小节）、知识点结构，以及关联的作业与考试活动。<br><br>6. 班级创建<br>教师在课程下创建班级，支持按课程名称定位课程、输入班级名称后完成创建；创建后可按需手动添加学生，并支持循环添加。<br><br>7. 学生入班信息查询<br>按入班状态查询课程/班级下的学生信息，支持已入班、待审核、待激活三种状态；返回学生名单、标签、院系等数据。<br><br>8. 课程分组查询<br>查询课程下的分组方案列表、分组方案详情、组内学生名单及未进组学生信息。<br><br>9. 学生基础技能<br>根据用户需求，智能选择并调用课程搜索、作业查询等相关功能。 |

<a id="entry-0c3c7ec0e09169e7c1be"></a>
### entry-0c3c7ec0e09169e7c1be · polymas-teacher-class-group-skills

技能  - 专家整理.xlsx / 专家 / 第 34 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| D34 | 附属技能 | polymas-teacher-class-group-skills |
| B（合并继承自 B27；B27:B35） | 原值见锚点 | 课程管理专员 |
| A（合并继承自 A3；A3:A43） | 原值见锚点 | 业务 |
| C（合并继承自 C27；C27:C35） | 原值见锚点 | 1. 课程创建<br>教师创建课程，支持邀请码建课和 AI 智课建课两种方式。<br><br>2. 课程列表查询<br>查询课程列表信息，包括当前学期课程、归档课程和共享课列表；其中共享课仅返回 state == 3 的课程。<br><br>3. 课程概况查询<br>查询课程概况信息，包括教学计划状态、单元/章节数量、课代表对话次数、AI 知识库资源数量及教学活动列表。<br><br>4. 课程知识结构查询<br>查询指定课程的教学单元、主题、知识点及知识点关系的层级结构；仅可查询当前用户有权访问的课程。<br><br>5. 教学计划查询<br>查询课程的教学单元、主题（小节）、知识点结构，以及关联的作业与考试活动。<br><br>6. 班级创建<br>教师在课程下创建班级，支持按课程名称定位课程、输入班级名称后完成创建；创建后可按需手动添加学生，并支持循环添加。<br><br>7. 学生入班信息查询<br>按入班状态查询课程/班级下的学生信息，支持已入班、待审核、待激活三种状态；返回学生名单、标签、院系等数据。<br><br>8. 课程分组查询<br>查询课程下的分组方案列表、分组方案详情、组内学生名单及未进组学生信息。<br><br>9. 学生基础技能<br>根据用户需求，智能选择并调用课程搜索、作业查询等相关功能。 |

<a id="entry-75f18129b549805ee989"></a>
### entry-75f18129b549805ee989 · polymas-student-basic-skills

技能  - 专家整理.xlsx / 专家 / 第 35 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| D35 | 附属技能 | polymas-student-basic-skills |
| B（合并继承自 B27；B27:B35） | 原值见锚点 | 课程管理专员 |
| A（合并继承自 A3；A3:A43） | 原值见锚点 | 业务 |
| C（合并继承自 C27；C27:C35） | 原值见锚点 | 1. 课程创建<br>教师创建课程，支持邀请码建课和 AI 智课建课两种方式。<br><br>2. 课程列表查询<br>查询课程列表信息，包括当前学期课程、归档课程和共享课列表；其中共享课仅返回 state == 3 的课程。<br><br>3. 课程概况查询<br>查询课程概况信息，包括教学计划状态、单元/章节数量、课代表对话次数、AI 知识库资源数量及教学活动列表。<br><br>4. 课程知识结构查询<br>查询指定课程的教学单元、主题、知识点及知识点关系的层级结构；仅可查询当前用户有权访问的课程。<br><br>5. 教学计划查询<br>查询课程的教学单元、主题（小节）、知识点结构，以及关联的作业与考试活动。<br><br>6. 班级创建<br>教师在课程下创建班级，支持按课程名称定位课程、输入班级名称后完成创建；创建后可按需手动添加学生，并支持循环添加。<br><br>7. 学生入班信息查询<br>按入班状态查询课程/班级下的学生信息，支持已入班、待审核、待激活三种状态；返回学生名单、标签、院系等数据。<br><br>8. 课程分组查询<br>查询课程下的分组方案列表、分组方案详情、组内学生名单及未进组学生信息。<br><br>9. 学生基础技能<br>根据用户需求，智能选择并调用课程搜索、作业查询等相关功能。 |

<a id="entry-65f2a253322044110da1"></a>
### entry-65f2a253322044110da1 · polymas-teacher-agent-create

技能  - 专家整理.xlsx / 专家 / 第 36 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B36 | 专家名称 | 智能体课程专员 |
| C36 | 专家描述 | 创建课堂智能体；<br>生成单个智能体课堂：抽取信息 → 定位课程/学期 → 匹配数字人 → 创建课堂 → 发布活动 → 轮询生成状态 |
| D36 | 附属技能 | polymas-teacher-agent-create |
| A（合并继承自 A3；A3:A43） | 原值见锚点 | 业务 |

<a id="entry-f2bf57fce37cb3b6e72c"></a>
### entry-f2bf57fce37cb3b6e72c · polymas-teacher-agent-teaching-gen

技能  - 专家整理.xlsx / 专家 / 第 37 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| D37 | 附属技能 | polymas-teacher-agent-teaching-gen |
| B（合并继承自 B36；B36:B37） | 原值见锚点 | 智能体课程专员 |
| A（合并继承自 A3；A3:A43） | 原值见锚点 | 业务 |
| C（合并继承自 C36；C36:C37） | 原值见锚点 | 创建课堂智能体；<br>生成单个智能体课堂：抽取信息 → 定位课程/学期 → 匹配数字人 → 创建课堂 → 发布活动 → 轮询生成状态 |

<a id="entry-d8d70355912582e06f5a"></a>
### entry-d8d70355912582e06f5a · polymas-teacher-resource-skills

技能  - 专家整理.xlsx / 专家 / 第 38 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B38 | 专家名称 | 资源管理专员 |
| C38 | 专家描述 | 1. 教师知识库查询<br>仅用于查询/搜索教师知识库内容，包括标题、资源类型、资源封面、资源链接、资源预览图标、资源名称、资源摘要。不支持新增、编辑、删除、上传、下载等操作。<br><br>2. 知识图谱查询<br>查询教学知识图谱中知识谱、问题谱、能力谱的结构与统计数据。<br><br>3. 教师题库查询<br>查询教师的题库资源与题目信息，包括课程题库和个人题库分类、题目详情（题干、题型、选项、答案）等数据；支持查询题目数量、分布及具体题目，可按题型、难度、知识点、标签、来源等多维度筛选。<br><br>4. 教师文件导题<br>上传试卷文件（支持 PDF、DOC、DOCX、PNG、JPG、JPEG、XLS、XLSX，单文件 ≤ 500MB），由 AI 解析提取题目，教师逐题确认后导入题库。<br><br>5. 教师 AI 出题<br>根据知识点、难度、题型等要求，通过 AI 自动生成题目并保存到题库。 |
| D38 | 附属技能 | polymas-teacher-resource-skills |
| A（合并继承自 A3；A3:A43） | 原值见锚点 | 业务 |

<a id="entry-cada0c57279b1790104a"></a>
### entry-cada0c57279b1790104a · polymas-teacher-questionbank-skills

技能  - 专家整理.xlsx / 专家 / 第 39 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| D39 | 附属技能 | polymas-teacher-questionbank-skills |
| B（合并继承自 B38；B38:B43） | 原值见锚点 | 资源管理专员 |
| A（合并继承自 A3；A3:A43） | 原值见锚点 | 业务 |
| C（合并继承自 C38；C38:C43） | 原值见锚点 | 1. 教师知识库查询<br>仅用于查询/搜索教师知识库内容，包括标题、资源类型、资源封面、资源链接、资源预览图标、资源名称、资源摘要。不支持新增、编辑、删除、上传、下载等操作。<br><br>2. 知识图谱查询<br>查询教学知识图谱中知识谱、问题谱、能力谱的结构与统计数据。<br><br>3. 教师题库查询<br>查询教师的题库资源与题目信息，包括课程题库和个人题库分类、题目详情（题干、题型、选项、答案）等数据；支持查询题目数量、分布及具体题目，可按题型、难度、知识点、标签、来源等多维度筛选。<br><br>4. 教师文件导题<br>上传试卷文件（支持 PDF、DOC、DOCX、PNG、JPG、JPEG、XLS、XLSX，单文件 ≤ 500MB），由 AI 解析提取题目，教师逐题确认后导入题库。<br><br>5. 教师 AI 出题<br>根据知识点、难度、题型等要求，通过 AI 自动生成题目并保存到题库。 |

<a id="entry-1492c83b0b7efccba1cd"></a>
### entry-1492c83b0b7efccba1cd · polymas-teacher-questions-query

技能  - 专家整理.xlsx / 专家 / 第 40 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| D40 | 附属技能 | polymas-teacher-questions-query |
| B（合并继承自 B38；B38:B43） | 原值见锚点 | 资源管理专员 |
| A（合并继承自 A3；A3:A43） | 原值见锚点 | 业务 |
| C（合并继承自 C38；C38:C43） | 原值见锚点 | 1. 教师知识库查询<br>仅用于查询/搜索教师知识库内容，包括标题、资源类型、资源封面、资源链接、资源预览图标、资源名称、资源摘要。不支持新增、编辑、删除、上传、下载等操作。<br><br>2. 知识图谱查询<br>查询教学知识图谱中知识谱、问题谱、能力谱的结构与统计数据。<br><br>3. 教师题库查询<br>查询教师的题库资源与题目信息，包括课程题库和个人题库分类、题目详情（题干、题型、选项、答案）等数据；支持查询题目数量、分布及具体题目，可按题型、难度、知识点、标签、来源等多维度筛选。<br><br>4. 教师文件导题<br>上传试卷文件（支持 PDF、DOC、DOCX、PNG、JPG、JPEG、XLS、XLSX，单文件 ≤ 500MB），由 AI 解析提取题目，教师逐题确认后导入题库。<br><br>5. 教师 AI 出题<br>根据知识点、难度、题型等要求，通过 AI 自动生成题目并保存到题库。 |

<a id="entry-8386e42f0e8bb1bee868"></a>
### entry-8386e42f0e8bb1bee868 · polymas-teacher-file-import-questions

技能  - 专家整理.xlsx / 专家 / 第 41 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| D41 | 附属技能 | polymas-teacher-file-import-questions |
| B（合并继承自 B38；B38:B43） | 原值见锚点 | 资源管理专员 |
| A（合并继承自 A3；A3:A43） | 原值见锚点 | 业务 |
| C（合并继承自 C38；C38:C43） | 原值见锚点 | 1. 教师知识库查询<br>仅用于查询/搜索教师知识库内容，包括标题、资源类型、资源封面、资源链接、资源预览图标、资源名称、资源摘要。不支持新增、编辑、删除、上传、下载等操作。<br><br>2. 知识图谱查询<br>查询教学知识图谱中知识谱、问题谱、能力谱的结构与统计数据。<br><br>3. 教师题库查询<br>查询教师的题库资源与题目信息，包括课程题库和个人题库分类、题目详情（题干、题型、选项、答案）等数据；支持查询题目数量、分布及具体题目，可按题型、难度、知识点、标签、来源等多维度筛选。<br><br>4. 教师文件导题<br>上传试卷文件（支持 PDF、DOC、DOCX、PNG、JPG、JPEG、XLS、XLSX，单文件 ≤ 500MB），由 AI 解析提取题目，教师逐题确认后导入题库。<br><br>5. 教师 AI 出题<br>根据知识点、难度、题型等要求，通过 AI 自动生成题目并保存到题库。 |

<a id="entry-519cbd617c2f7d926bf6"></a>
### entry-519cbd617c2f7d926bf6 · polymas-teacher-problem-skills

技能  - 专家整理.xlsx / 专家 / 第 42 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| D42 | 附属技能 | polymas-teacher-problem-skills |
| B（合并继承自 B38；B38:B43） | 原值见锚点 | 资源管理专员 |
| A（合并继承自 A3；A3:A43） | 原值见锚点 | 业务 |
| C（合并继承自 C38；C38:C43） | 原值见锚点 | 1. 教师知识库查询<br>仅用于查询/搜索教师知识库内容，包括标题、资源类型、资源封面、资源链接、资源预览图标、资源名称、资源摘要。不支持新增、编辑、删除、上传、下载等操作。<br><br>2. 知识图谱查询<br>查询教学知识图谱中知识谱、问题谱、能力谱的结构与统计数据。<br><br>3. 教师题库查询<br>查询教师的题库资源与题目信息，包括课程题库和个人题库分类、题目详情（题干、题型、选项、答案）等数据；支持查询题目数量、分布及具体题目，可按题型、难度、知识点、标签、来源等多维度筛选。<br><br>4. 教师文件导题<br>上传试卷文件（支持 PDF、DOC、DOCX、PNG、JPG、JPEG、XLS、XLSX，单文件 ≤ 500MB），由 AI 解析提取题目，教师逐题确认后导入题库。<br><br>5. 教师 AI 出题<br>根据知识点、难度、题型等要求，通过 AI 自动生成题目并保存到题库。 |

<a id="entry-800e06251af1cdd3b3b1"></a>
### entry-800e06251af1cdd3b3b1 · polymas-teacher-knowledge-graph

技能  - 专家整理.xlsx / 专家 / 第 43 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| D43 | 附属技能 | polymas-teacher-knowledge-graph |
| B（合并继承自 B38；B38:B43） | 原值见锚点 | 资源管理专员 |
| A（合并继承自 A3；A3:A43） | 原值见锚点 | 业务 |
| C（合并继承自 C38；C38:C43） | 原值见锚点 | 1. 教师知识库查询<br>仅用于查询/搜索教师知识库内容，包括标题、资源类型、资源封面、资源链接、资源预览图标、资源名称、资源摘要。不支持新增、编辑、删除、上传、下载等操作。<br><br>2. 知识图谱查询<br>查询教学知识图谱中知识谱、问题谱、能力谱的结构与统计数据。<br><br>3. 教师题库查询<br>查询教师的题库资源与题目信息，包括课程题库和个人题库分类、题目详情（题干、题型、选项、答案）等数据；支持查询题目数量、分布及具体题目，可按题型、难度、知识点、标签、来源等多维度筛选。<br><br>4. 教师文件导题<br>上传试卷文件（支持 PDF、DOC、DOCX、PNG、JPG、JPEG、XLS、XLSX，单文件 ≤ 500MB），由 AI 解析提取题目，教师逐题确认后导入题库。<br><br>5. 教师 AI 出题<br>根据知识点、难度、题型等要求，通过 AI 自动生成题目并保存到题库。 |

<a id="entry-9bf200ab38619f621e1f"></a>
### entry-9bf200ab38619f621e1f · pincaimao-interview-question

技能  - 专家整理.xlsx / 技能推荐列表 / 第 2 行

NID：zXdK3ZqIXy；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A2 | 类型 | 助教(随机4 - 5个) |
| B2 | 来源 | 第三方拉取 |
| C2 | 技能 | pincaimao-interview-question |
| D2 | 技能nid | zXdK3ZqIXy |
| E2 | 是否必须推送 | 否 |

<a id="entry-f2496c8fdf6555483e63"></a>
### entry-f2496c8fdf6555483e63 · cyber-ppt

技能  - 专家整理.xlsx / 技能推荐列表 / 第 3 行

NID：zz12345678；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C3 | 技能 | cyber-ppt |
| D3 | 技能nid | zz12345678 |
| E（合并继承自 E2；E2:E14） | 原值见锚点 | 否 |
| A（合并继承自 A2；A2:A15） | 原值见锚点 | 助教(随机4 - 5个) |
| B（合并继承自 B2；B2:B15） | 原值见锚点 | 第三方拉取 |

<a id="entry-31d48ecf1d4190595197"></a>
### entry-31d48ecf1d4190595197 · rank

技能  - 专家整理.xlsx / 技能推荐列表 / 第 4 行

NID：pROAU0vQvX；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C4 | 技能 | rank |
| D4 | 技能nid | pROAU0vQvX |
| E（合并继承自 E2；E2:E14） | 原值见锚点 | 否 |
| A（合并继承自 A2；A2:A15） | 原值见锚点 | 助教(随机4 - 5个) |
| B（合并继承自 B2；B2:B15） | 原值见锚点 | 第三方拉取 |

<a id="entry-98eb2876129d8780e23f"></a>
### entry-98eb2876129d8780e23f · book

技能  - 专家整理.xlsx / 技能推荐列表 / 第 5 行

NID：vHGv7DMv6T；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C5 | 技能 | book |
| D5 | 技能nid | vHGv7DMv6T |
| E（合并继承自 E2；E2:E14） | 原值见锚点 | 否 |
| A（合并继承自 A2；A2:A15） | 原值见锚点 | 助教(随机4 - 5个) |
| B（合并继承自 B2；B2:B15） | 原值见锚点 | 第三方拉取 |

<a id="entry-5d3215ee8c1b279c8f81"></a>
### entry-5d3215ee8c1b279c8f81 · present

技能  - 专家整理.xlsx / 技能推荐列表 / 第 6 行

NID：MLN4EBW4GR；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C6 | 技能 | present |
| D6 | 技能nid | MLN4EBW4GR |
| E（合并继承自 E2；E2:E14） | 原值见锚点 | 否 |
| A（合并继承自 A2；A2:A15） | 原值见锚点 | 助教(随机4 - 5个) |
| B（合并继承自 B2；B2:B15） | 原值见锚点 | 第三方拉取 |

<a id="entry-9fdf6ec08e3d7633bd99"></a>
### entry-9fdf6ec08e3d7633bd99 · think

技能  - 专家整理.xlsx / 技能推荐列表 / 第 7 行

NID：mxtNqLtCS7；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C7 | 技能 | think |
| D7 | 技能nid | mxtNqLtCS7 |
| E（合并继承自 E2；E2:E14） | 原值见锚点 | 否 |
| A（合并继承自 A2；A2:A15） | 原值见锚点 | 助教(随机4 - 5个) |
| B（合并继承自 B2；B2:B15） | 原值见锚点 | 第三方拉取 |

<a id="entry-104a7222c9241a5a9d14"></a>
### entry-104a7222c9241a5a9d14 · word

技能  - 专家整理.xlsx / 技能推荐列表 / 第 8 行

NID：Fph4Q3Ao19；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C8 | 技能 | word |
| D8 | 技能nid | Fph4Q3Ao19 |
| E（合并继承自 E2；E2:E14） | 原值见锚点 | 否 |
| A（合并继承自 A2；A2:A15） | 原值见锚点 | 助教(随机4 - 5个) |
| B（合并继承自 B2；B2:B15） | 原值见锚点 | 第三方拉取 |

<a id="entry-ba18c0fd8e2f09c34ad4"></a>
### entry-ba18c0fd8e2f09c34ad4 · baoyu-infographic

技能  - 专家整理.xlsx / 技能推荐列表 / 第 9 行

NID：umw5xMPtgY；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C9 | 技能 | baoyu-infographic |
| D9 | 技能nid | umw5xMPtgY |
| E（合并继承自 E2；E2:E14） | 原值见锚点 | 否 |
| A（合并继承自 A2；A2:A15） | 原值见锚点 | 助教(随机4 - 5个) |
| B（合并继承自 B2；B2:B15） | 原值见锚点 | 第三方拉取 |

<a id="entry-323ecee4f6059c291be5"></a>
### entry-323ecee4f6059c291be5 · explain-like-socrates

技能  - 专家整理.xlsx / 技能推荐列表 / 第 10 行

NID：SRpzIG2wNw；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C10 | 技能 | explain-like-socrates |
| D10 | 技能nid | SRpzIG2wNw |
| E（合并继承自 E2；E2:E14） | 原值见锚点 | 否 |
| A（合并继承自 A2；A2:A15） | 原值见锚点 | 助教(随机4 - 5个) |
| B（合并继承自 B2；B2:B15） | 原值见锚点 | 第三方拉取 |

<a id="entry-8b9b257a460fb387a463"></a>
### entry-8b9b257a460fb387a463 · math-intuition-builder

技能  - 专家整理.xlsx / 技能推荐列表 / 第 11 行

NID：2JDf8tyead；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C11 | 技能 | math-intuition-builder |
| D11 | 技能nid | 2JDf8tyead |
| E（合并继承自 E2；E2:E14） | 原值见锚点 | 否 |
| A（合并继承自 A2；A2:A15） | 原值见锚点 | 助教(随机4 - 5个) |
| B（合并继承自 B2；B2:B15） | 原值见锚点 | 第三方拉取 |

<a id="entry-0ce838f04aa7e5703caf"></a>
### entry-0ce838f04aa7e5703caf · ppt-master

技能  - 专家整理.xlsx / 技能推荐列表 / 第 12 行

NID：RzXg2eaopI；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C12 | 技能 | ppt-master |
| D12 | 技能nid | RzXg2eaopI |
| E（合并继承自 E2；E2:E14） | 原值见锚点 | 否 |
| A（合并继承自 A2；A2:A15） | 原值见锚点 | 助教(随机4 - 5个) |
| B（合并继承自 B2；B2:B15） | 原值见锚点 | 第三方拉取 |

<a id="entry-1d38f4479f6be6f0e692"></a>
### entry-1d38f4479f6be6f0e692 · scientific-schematics

技能  - 专家整理.xlsx / 技能推荐列表 / 第 13 行

NID：pi068ShZtT；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C13 | 技能 | scientific-schematics |
| D13 | 技能nid | pi068ShZtT |
| E（合并继承自 E2；E2:E14） | 原值见锚点 | 否 |
| A（合并继承自 A2；A2:A15） | 原值见锚点 | 助教(随机4 - 5个) |
| B（合并继承自 B2；B2:B15） | 原值见锚点 | 第三方拉取 |

<a id="entry-684dad8d626844bf3e89"></a>
### entry-684dad8d626844bf3e89 · statistical-analysis

技能  - 专家整理.xlsx / 技能推荐列表 / 第 14 行

NID：PQG3F99qxM；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C14 | 技能 | statistical-analysis |
| D14 | 技能nid | PQG3F99qxM |
| E（合并继承自 E2；E2:E14） | 原值见锚点 | 否 |
| A（合并继承自 A2；A2:A15） | 原值见锚点 | 助教(随机4 - 5个) |
| B（合并继承自 B2；B2:B15） | 原值见锚点 | 第三方拉取 |

<a id="entry-801ca406d440ff4487bc"></a>
### entry-801ca406d440ff4487bc · find-skills

技能  - 专家整理.xlsx / 技能推荐列表 / 第 15 行

NID：jwzVQMBIuj；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C15 | 技能 | find-skills |
| D15 | 技能nid | jwzVQMBIuj |
| E15 | 是否必须推送 | 必须 |
| A（合并继承自 A2；A2:A15） | 原值见锚点 | 助教(随机4 - 5个) |
| B（合并继承自 B2；B2:B15） | 原值见锚点 | 第三方拉取 |

<a id="entry-45a483eb8a01cc0e93f6"></a>
### entry-45a483eb8a01cc0e93f6 · pincaimao-interview-question

技能  - 专家整理.xlsx / 技能推荐列表 / 第 16 行

NID：zXdK3ZqIXy；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A16 | 类型 | 课代表 - 教师（3- 4）/学生推荐(3 - 4) |
| B16 | 来源 | 第三方拉取 |
| C16 | 技能 | pincaimao-interview-question |
| D16 | 技能nid | zXdK3ZqIXy |
| E16 | 是否必须推送 | 否 |

<a id="entry-8f9dc4f20ec4ab914299"></a>
### entry-8f9dc4f20ec4ab914299 · cyber-ppt

技能  - 专家整理.xlsx / 技能推荐列表 / 第 17 行

NID：zz12345678；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C17 | 技能 | cyber-ppt |
| D17 | 技能nid | zz12345678 |
| E（合并继承自 E16；E16:E28） | 原值见锚点 | 否 |
| A（合并继承自 A16；A16:A28） | 原值见锚点 | 课代表 - 教师（3- 4）/学生推荐(3 - 4) |
| B（合并继承自 B16；B16:B29） | 原值见锚点 | 第三方拉取 |

<a id="entry-54e531754d4b794cd6d3"></a>
### entry-54e531754d4b794cd6d3 · rank

技能  - 专家整理.xlsx / 技能推荐列表 / 第 18 行

NID：pROAU0vQvX；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C18 | 技能 | rank |
| D18 | 技能nid | pROAU0vQvX |
| E（合并继承自 E16；E16:E28） | 原值见锚点 | 否 |
| A（合并继承自 A16；A16:A28） | 原值见锚点 | 课代表 - 教师（3- 4）/学生推荐(3 - 4) |
| B（合并继承自 B16；B16:B29） | 原值见锚点 | 第三方拉取 |

<a id="entry-01dda353c459a49d1f63"></a>
### entry-01dda353c459a49d1f63 · book

技能  - 专家整理.xlsx / 技能推荐列表 / 第 19 行

NID：vHGv7DMv6T；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C19 | 技能 | book |
| D19 | 技能nid | vHGv7DMv6T |
| E（合并继承自 E16；E16:E28） | 原值见锚点 | 否 |
| A（合并继承自 A16；A16:A28） | 原值见锚点 | 课代表 - 教师（3- 4）/学生推荐(3 - 4) |
| B（合并继承自 B16；B16:B29） | 原值见锚点 | 第三方拉取 |

<a id="entry-d337e10674a77660929d"></a>
### entry-d337e10674a77660929d · present

技能  - 专家整理.xlsx / 技能推荐列表 / 第 20 行

NID：MLN4EBW4GR；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C20 | 技能 | present |
| D20 | 技能nid | MLN4EBW4GR |
| E（合并继承自 E16；E16:E28） | 原值见锚点 | 否 |
| A（合并继承自 A16；A16:A28） | 原值见锚点 | 课代表 - 教师（3- 4）/学生推荐(3 - 4) |
| B（合并继承自 B16；B16:B29） | 原值见锚点 | 第三方拉取 |

<a id="entry-a99c374c69c7dedf073b"></a>
### entry-a99c374c69c7dedf073b · think

技能  - 专家整理.xlsx / 技能推荐列表 / 第 21 行

NID：mxtNqLtCS7；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C21 | 技能 | think |
| D21 | 技能nid | mxtNqLtCS7 |
| E（合并继承自 E16；E16:E28） | 原值见锚点 | 否 |
| A（合并继承自 A16；A16:A28） | 原值见锚点 | 课代表 - 教师（3- 4）/学生推荐(3 - 4) |
| B（合并继承自 B16；B16:B29） | 原值见锚点 | 第三方拉取 |

<a id="entry-867113bcadef7cbd4bc4"></a>
### entry-867113bcadef7cbd4bc4 · word

技能  - 专家整理.xlsx / 技能推荐列表 / 第 22 行

NID：Fph4Q3Ao19；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C22 | 技能 | word |
| D22 | 技能nid | Fph4Q3Ao19 |
| E（合并继承自 E16；E16:E28） | 原值见锚点 | 否 |
| A（合并继承自 A16；A16:A28） | 原值见锚点 | 课代表 - 教师（3- 4）/学生推荐(3 - 4) |
| B（合并继承自 B16；B16:B29） | 原值见锚点 | 第三方拉取 |

<a id="entry-ba971320a2a1abf4e2dd"></a>
### entry-ba971320a2a1abf4e2dd · baoyu-infographic

技能  - 专家整理.xlsx / 技能推荐列表 / 第 23 行

NID：umw5xMPtgY；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C23 | 技能 | baoyu-infographic |
| D23 | 技能nid | umw5xMPtgY |
| E（合并继承自 E16；E16:E28） | 原值见锚点 | 否 |
| A（合并继承自 A16；A16:A28） | 原值见锚点 | 课代表 - 教师（3- 4）/学生推荐(3 - 4) |
| B（合并继承自 B16；B16:B29） | 原值见锚点 | 第三方拉取 |

<a id="entry-8414fbe6310940938491"></a>
### entry-8414fbe6310940938491 · explain-like-socrates

技能  - 专家整理.xlsx / 技能推荐列表 / 第 24 行

NID：SRpzIG2wNw；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C24 | 技能 | explain-like-socrates |
| D24 | 技能nid | SRpzIG2wNw |
| E（合并继承自 E16；E16:E28） | 原值见锚点 | 否 |
| A（合并继承自 A16；A16:A28） | 原值见锚点 | 课代表 - 教师（3- 4）/学生推荐(3 - 4) |
| B（合并继承自 B16；B16:B29） | 原值见锚点 | 第三方拉取 |

<a id="entry-9f8f11a04dcba656ba02"></a>
### entry-9f8f11a04dcba656ba02 · math-intuition-builder

技能  - 专家整理.xlsx / 技能推荐列表 / 第 25 行

NID：2JDf8tyead；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C25 | 技能 | math-intuition-builder |
| D25 | 技能nid | 2JDf8tyead |
| E（合并继承自 E16；E16:E28） | 原值见锚点 | 否 |
| A（合并继承自 A16；A16:A28） | 原值见锚点 | 课代表 - 教师（3- 4）/学生推荐(3 - 4) |
| B（合并继承自 B16；B16:B29） | 原值见锚点 | 第三方拉取 |

<a id="entry-dc2b7c48ee34efde7540"></a>
### entry-dc2b7c48ee34efde7540 · ppt-master

技能  - 专家整理.xlsx / 技能推荐列表 / 第 26 行

NID：RzXg2eaopI；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C26 | 技能 | ppt-master |
| D26 | 技能nid | RzXg2eaopI |
| E（合并继承自 E16；E16:E28） | 原值见锚点 | 否 |
| A（合并继承自 A16；A16:A28） | 原值见锚点 | 课代表 - 教师（3- 4）/学生推荐(3 - 4) |
| B（合并继承自 B16；B16:B29） | 原值见锚点 | 第三方拉取 |

<a id="entry-7850355d337ad04f7eaf"></a>
### entry-7850355d337ad04f7eaf · scientific-schematics

技能  - 专家整理.xlsx / 技能推荐列表 / 第 27 行

NID：pi068ShZtT；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C27 | 技能 | scientific-schematics |
| D27 | 技能nid | pi068ShZtT |
| E（合并继承自 E16；E16:E28） | 原值见锚点 | 否 |
| A（合并继承自 A16；A16:A28） | 原值见锚点 | 课代表 - 教师（3- 4）/学生推荐(3 - 4) |
| B（合并继承自 B16；B16:B29） | 原值见锚点 | 第三方拉取 |

<a id="entry-1e49b211083979ea2036"></a>
### entry-1e49b211083979ea2036 · statistical-analysis

技能  - 专家整理.xlsx / 技能推荐列表 / 第 28 行

NID：PQG3F99qxM；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C28 | 技能 | statistical-analysis |
| D28 | 技能nid | PQG3F99qxM |
| E（合并继承自 E16；E16:E28） | 原值见锚点 | 否 |
| A（合并继承自 A16；A16:A28） | 原值见锚点 | 课代表 - 教师（3- 4）/学生推荐(3 - 4) |
| B（合并继承自 B16；B16:B29） | 原值见锚点 | 第三方拉取 |

<a id="entry-b0bf2fcbb5f54791b7ce"></a>
### entry-b0bf2fcbb5f54791b7ce · find-skills

技能  - 专家整理.xlsx / 技能推荐列表 / 第 29 行

NID：jwzVQMBIuj；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A29 | 类型 | 教师技能 |
| C29 | 技能 | find-skills |
| D29 | 技能nid | jwzVQMBIuj |
| E29 | 是否必须推送 | 必须 |
| B（合并继承自 B16；B16:B29） | 原值见锚点 | 第三方拉取 |

<a id="entry-5ed3591cfa646a007931"></a>
### entry-5ed3591cfa646a007931 · polymas-get-student-course-homework

技能  - 专家整理.xlsx / 技能推荐列表 / 第 30 行

NID：y9azCkSHMg；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A30 | 类型 | 学生技能 |
| B30 | 来源 | 业务开发 |
| C30 | 技能 | polymas-get-student-course-homework  |
| D30 | 技能nid | y9azCkSHMg |
| E30 | 是否必须推送 | 必须 |

<a id="entry-aee5589421f3f4b19c03"></a>
### entry-aee5589421f3f4b19c03 · polymas-student-basic-skills

技能  - 专家整理.xlsx / 技能推荐列表 / 第 31 行

NID：P0oNhYY02C；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A31 | 类型 | 学生技能 |
| C31 | 技能 | polymas-student-basic-skills  |
| D31 | 技能nid | P0oNhYY02C |
| E31 | 是否必须推送 | 必须 |
| B（合并继承自 B30；B30:B31） | 原值见锚点 | 业务开发 |

<a id="entry-1603ba0e239b72099cdc"></a>
### entry-1603ba0e239b72099cdc · external-knowledge-search

技能  - 专家整理.xlsx / 技能推荐列表 / 第 32 行

NID：zRG4S1dhy4；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A32 | 类型 | 学生技能 |
| B32 | 来源 | 算法 |
| C32 | 技能 | external-knowledge-search |
| D32 | 技能nid | zRG4S1dhy4 |
| E32 | 是否必须推送 | 必须 |

<a id="entry-0582499515620a27e573"></a>
### entry-0582499515620a27e573 · meeting-skill

技能  - 专家整理.xlsx / 应用广场数据整理 / 第 2 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A2 | 类型 | 技能 |
| B2 | 来源 | 业务 |
| C2 | 名称 | meeting-skill |
| D2 | 中文名 | 会议管理技能 |

<a id="entry-9e1f905fc59169e1ea02"></a>
### entry-9e1f905fc59169e1ea02 · polymas-agent-readme

技能  - 专家整理.xlsx / 应用广场数据整理 / 第 3 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C3 | 名称 | polymas-agent-readme |
| D3 | 中文名 | 平台智能体帮助手册 |
| B（合并继承自 B2；B2:B36） | 原值见锚点 | 业务 |
| A（合并继承自 A2；A2:A63） | 原值见锚点 | 技能 |

<a id="entry-066ac1933693e3e79e08"></a>
### entry-066ac1933693e3e79e08 · polymas-course-obe-skills

技能  - 专家整理.xlsx / 应用广场数据整理 / 第 4 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C4 | 名称 | polymas-course-obe-skills |
| D4 | 中文名 | 课程OBE技能 |
| B（合并继承自 B2；B2:B36） | 原值见锚点 | 业务 |
| A（合并继承自 A2；A2:A63） | 原值见锚点 | 技能 |

<a id="entry-e90a4e798e2230e4e5df"></a>
### entry-e90a4e798e2230e4e5df · polymas-course-overview-skills

技能  - 专家整理.xlsx / 应用广场数据整理 / 第 5 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C5 | 名称 | polymas-course-overview-skills |
| D5 | 中文名 | 课程概况查询技能 |
| B（合并继承自 B2；B2:B36） | 原值见锚点 | 业务 |
| A（合并继承自 A2；A2:A63） | 原值见锚点 | 技能 |

<a id="entry-bfb9c923369ec05afee9"></a>
### entry-bfb9c923369ec05afee9 · polymas-page-navigation

技能  - 专家整理.xlsx / 应用广场数据整理 / 第 6 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C6 | 名称 | polymas-page-navigation |
| D6 | 中文名 | 页面导航指引技能 |
| B（合并继承自 B2；B2:B36） | 原值见锚点 | 业务 |
| A（合并继承自 A2；A2:A63） | 原值见锚点 | 技能 |

<a id="entry-d57900b6d24674b26614"></a>
### entry-d57900b6d24674b26614 · polymas-query-teaching-unit

技能  - 专家整理.xlsx / 应用广场数据整理 / 第 7 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C7 | 名称 | polymas-query-teaching-unit |
| D7 | 中文名 | 教学单元查询技能 |
| B（合并继承自 B2；B2:B36） | 原值见锚点 | 业务 |
| A（合并继承自 A2；A2:A63） | 原值见锚点 | 技能 |

<a id="entry-88f61952c4cc57e411a1"></a>
### entry-88f61952c4cc57e411a1 · polymas-teacher-activity-skills

技能  - 专家整理.xlsx / 应用广场数据整理 / 第 8 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C8 | 名称 | polymas-teacher-activity-skills |
| D8 | 中文名 | 教师教学活动技能 |
| B（合并继承自 B2；B2:B36） | 原值见锚点 | 业务 |
| A（合并继承自 A2；A2:A63） | 原值见锚点 | 技能 |

<a id="entry-938b6a67492b434419fb"></a>
### entry-938b6a67492b434419fb · polymas-teacher-agent-create

技能  - 专家整理.xlsx / 应用广场数据整理 / 第 9 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C9 | 名称 | polymas-teacher-agent-create |
| D9 | 中文名 | 课堂智能体创建技能 |
| B（合并继承自 B2；B2:B36） | 原值见锚点 | 业务 |
| A（合并继承自 A2；A2:A63） | 原值见锚点 | 技能 |

<a id="entry-7edc8051993f6a7363b4"></a>
### entry-7edc8051993f6a7363b4 · polymas-teacher-agent-teaching-gen

技能  - 专家整理.xlsx / 应用广场数据整理 / 第 10 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C10 | 名称 | polymas-teacher-agent-teaching-gen |
| D10 | 中文名 | 智能体教学生成技能 |
| B（合并继承自 B2；B2:B36） | 原值见锚点 | 业务 |
| A（合并继承自 A2；A2:A63） | 原值见锚点 | 技能 |

<a id="entry-4ae85d9069ffb725a0ab"></a>
### entry-4ae85d9069ffb725a0ab · polymas-teacher-analogy-skills

技能  - 专家整理.xlsx / 应用广场数据整理 / 第 11 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C11 | 名称 | polymas-teacher-analogy-skills |
| D11 | 中文名 | 教师概念类比技能 |
| B（合并继承自 B2；B2:B36） | 原值见锚点 | 业务 |
| A（合并继承自 A2；A2:A63） | 原值见锚点 | 技能 |

<a id="entry-7b32777a58453e6c8900"></a>
### entry-7b32777a58453e6c8900 · polymas-teacher-case-skills

技能  - 专家整理.xlsx / 应用广场数据整理 / 第 12 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C12 | 名称 | polymas-teacher-case-skills |
| D12 | 中文名 | 教师案例生成技能 |
| B（合并继承自 B2；B2:B36） | 原值见锚点 | 业务 |
| A（合并继承自 A2；A2:A63） | 原值见锚点 | 技能 |

<a id="entry-e54985884853c56ba476"></a>
### entry-e54985884853c56ba476 · polymas-teacher-class-group-assistant

技能  - 专家整理.xlsx / 应用广场数据整理 / 第 13 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C13 | 名称 | polymas-teacher-class-group-assistant |
| D13 | 中文名 | 班级群综合管理技能 |
| B（合并继承自 B2；B2:B36） | 原值见锚点 | 业务 |
| A（合并继承自 A2；A2:A63） | 原值见锚点 | 技能 |

<a id="entry-8a27084e8bc82042a783"></a>
### entry-8a27084e8bc82042a783 · polymas-teacher-class-group-skills

技能  - 专家整理.xlsx / 应用广场数据整理 / 第 14 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C14 | 名称 | polymas-teacher-class-group-skills |
| D14 | 中文名 | 班级分组管理技能 |
| B（合并继承自 B2；B2:B36） | 原值见锚点 | 业务 |
| A（合并继承自 A2；A2:A63） | 原值见锚点 | 技能 |

<a id="entry-4a09a85c30b1cf9514c4"></a>
### entry-4a09a85c30b1cf9514c4 · polymas-teacher-class-skills

技能  - 专家整理.xlsx / 应用广场数据整理 / 第 15 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C15 | 名称 | polymas-teacher-class-skills |
| D15 | 中文名 | 教师班级技能 |
| B（合并继承自 B2；B2:B36） | 原值见锚点 | 业务 |
| A（合并继承自 A2；A2:A63） | 原值见锚点 | 技能 |

<a id="entry-d3f4cf210378adc9b347"></a>
### entry-d3f4cf210378adc9b347 · polymas-teacher-class-student-skills

技能  - 专家整理.xlsx / 应用广场数据整理 / 第 16 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C16 | 名称 | polymas-teacher-class-student-skills |
| D16 | 中文名 | 班级学生管理技能 |
| B（合并继承自 B2；B2:B36） | 原值见锚点 | 业务 |
| A（合并继承自 A2；A2:A63） | 原值见锚点 | 技能 |

<a id="entry-ea38745b706f2fee3f16"></a>
### entry-ea38745b706f2fee3f16 · polymas-teacher-classroom-report-skills

技能  - 专家整理.xlsx / 应用广场数据整理 / 第 17 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C17 | 名称 | polymas-teacher-classroom-report-skills |
| D17 | 中文名 | 课堂报告分析技能 |
| B（合并继承自 B2；B2:B36） | 原值见锚点 | 业务 |
| A（合并继承自 A2；A2:A63） | 原值见锚点 | 技能 |

<a id="entry-d1c609cbdcc532472b6f"></a>
### entry-d1c609cbdcc532472b6f · polymas-teacher-course-skills

技能  - 专家整理.xlsx / 应用广场数据整理 / 第 18 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C18 | 名称 | polymas-teacher-course-skills |
| D18 | 中文名 | 教师课程技能 |
| B（合并继承自 B2；B2:B36） | 原值见锚点 | 业务 |
| A（合并继承自 A2；A2:A63） | 原值见锚点 | 技能 |

<a id="entry-d7aeeed4d712bf3f79b7"></a>
### entry-d7aeeed4d712bf3f79b7 · polymas-teacher-exam-skills

技能  - 专家整理.xlsx / 应用广场数据整理 / 第 19 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C19 | 名称 | polymas-teacher-exam-skills |
| D19 | 中文名 | 教师考试技能 |
| B（合并继承自 B2；B2:B36） | 原值见锚点 | 业务 |
| A（合并继承自 A2；A2:A63） | 原值见锚点 | 技能 |

<a id="entry-f01374c3bc091e293f31"></a>
### entry-f01374c3bc091e293f31 · polymas-teacher-file-import-questions

技能  - 专家整理.xlsx / 应用广场数据整理 / 第 20 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C20 | 名称 | polymas-teacher-file-import-questions |
| D20 | 中文名 | 教师文件导题技能 |
| B（合并继承自 B2；B2:B36） | 原值见锚点 | 业务 |
| A（合并继承自 A2；A2:A63） | 原值见锚点 | 技能 |

<a id="entry-bb2d1b6aad0aa80717bc"></a>
### entry-bb2d1b6aad0aa80717bc · polymas-student-basic-skills

技能  - 专家整理.xlsx / 应用广场数据整理 / 第 21 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C21 | 名称 | polymas-student-basic-skills |
| D21 | 中文名 | 学生班课查询助手 |
| B（合并继承自 B2；B2:B36） | 原值见锚点 | 业务 |
| A（合并继承自 A2；A2:A63） | 原值见锚点 | 技能 |

<a id="entry-534891f29cb274a9f2d3"></a>
### entry-534891f29cb274a9f2d3 · polymas-get-student-course-homework

技能  - 专家整理.xlsx / 应用广场数据整理 / 第 22 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C22 | 名称 | polymas-get-student-course-homework |
| D22 | 中文名 | 学生作业管理助手 |
| B（合并继承自 B2；B2:B36） | 原值见锚点 | 业务 |
| A（合并继承自 A2；A2:A63） | 原值见锚点 | 技能 |

<a id="entry-d98a5333e7b5e8424b64"></a>
### entry-d98a5333e7b5e8424b64 · polymas-teacher-homework-detail-skills

技能  - 专家整理.xlsx / 应用广场数据整理 / 第 23 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C23 | 名称 | polymas-teacher-homework-detail-skills |
| D23 | 中文名 | 教师作业详情技能 |
| B（合并继承自 B2；B2:B36） | 原值见锚点 | 业务 |
| A（合并继承自 A2；A2:A63） | 原值见锚点 | 技能 |

<a id="entry-3b9a9e83ab503552d6ff"></a>
### entry-3b9a9e83ab503552d6ff · polymas-teacher-homework-skills

技能  - 专家整理.xlsx / 应用广场数据整理 / 第 24 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C24 | 名称 | polymas-teacher-homework-skills |
| D24 | 中文名 | 教师作业技能 |
| B（合并继承自 B2；B2:B36） | 原值见锚点 | 业务 |
| A（合并继承自 A2；A2:A63） | 原值见锚点 | 技能 |

<a id="entry-ec36229d9713bff5f38b"></a>
### entry-ec36229d9713bff5f38b · polymas-teacher-knowledge-distillation

技能  - 专家整理.xlsx / 应用广场数据整理 / 第 25 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C25 | 名称 | polymas-teacher-knowledge-distillation |
| D25 | 中文名 | 个人知识蒸馏技能 |
| B（合并继承自 B2；B2:B36） | 原值见锚点 | 业务 |
| A（合并继承自 A2；A2:A63） | 原值见锚点 | 技能 |

<a id="entry-07a031f2cb8aff1a3219"></a>
### entry-07a031f2cb8aff1a3219 · polymas-teacher-knowledge-graph

技能  - 专家整理.xlsx / 应用广场数据整理 / 第 26 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C26 | 名称 | polymas-teacher-knowledge-graph |
| D26 | 中文名 | 知识图谱查询技能 |
| B（合并继承自 B2；B2:B36） | 原值见锚点 | 业务 |
| A（合并继承自 A2；A2:A63） | 原值见锚点 | 技能 |

<a id="entry-0dd381c75856576cf201"></a>
### entry-0dd381c75856576cf201 · polymas-teacher-lession-analysis

技能  - 专家整理.xlsx / 应用广场数据整理 / 第 27 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C27 | 名称 | polymas-teacher-lession-analysis |
| D27 | 中文名 | 课堂表现分析技能 |
| B（合并继承自 B2；B2:B36） | 原值见锚点 | 业务 |
| A（合并继承自 A2；A2:A63） | 原值见锚点 | 技能 |

<a id="entry-8e2dcbfbb6c575ec4738"></a>
### entry-8e2dcbfbb6c575ec4738 · polymas-teacher-preparation-management

技能  - 专家整理.xlsx / 应用广场数据整理 / 第 28 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C28 | 名称 | polymas-teacher-preparation-management |
| D28 | 中文名 | 备课管理技能 |
| B（合并继承自 B2；B2:B36） | 原值见锚点 | 业务 |
| A（合并继承自 A2；A2:A63） | 原值见锚点 | 技能 |

<a id="entry-6354ce6f82202ecfbb31"></a>
### entry-6354ce6f82202ecfbb31 · polymas-teacher-problem-skills

技能  - 专家整理.xlsx / 应用广场数据整理 / 第 29 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C29 | 名称 | polymas-teacher-problem-skills |
| D29 | 中文名 | 教师AI出题技能 |
| B（合并继承自 B2；B2:B36） | 原值见锚点 | 业务 |
| A（合并继承自 A2；A2:A63） | 原值见锚点 | 技能 |

<a id="entry-fb9f690daddcb1a4e71e"></a>
### entry-fb9f690daddcb1a4e71e · polymas-teacher-questions-query

技能  - 专家整理.xlsx / 应用广场数据整理 / 第 30 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C30 | 名称 | polymas-teacher-questions-query |
| D30 | 中文名 | 教师题库技能 |
| B（合并继承自 B2；B2:B36） | 原值见锚点 | 业务 |
| A（合并继承自 A2；A2:A63） | 原值见锚点 | 技能 |

<a id="entry-b0c1ccc2db89713978b0"></a>
### entry-b0c1ccc2db89713978b0 · polymas-teacher-resource-skills

技能  - 专家整理.xlsx / 应用广场数据整理 / 第 31 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C31 | 名称 | polymas-teacher-resource-skills |
| D31 | 中文名 | 教师资源技能 |
| B（合并继承自 B2；B2:B36） | 原值见锚点 | 业务 |
| A（合并继承自 A2；A2:A63） | 原值见锚点 | 技能 |

<a id="entry-b4023732f32c367b1367"></a>
### entry-b4023732f32c367b1367 · polymas-teacher-score-skills

技能  - 专家整理.xlsx / 应用广场数据整理 / 第 32 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C32 | 名称 | polymas-teacher-score-skills |
| D32 | 中文名 | 教师成绩技能 |
| B（合并继承自 B2；B2:B36） | 原值见锚点 | 业务 |
| A（合并继承自 A2；A2:A63） | 原值见锚点 | 技能 |

<a id="entry-c27968866bad1b86451b"></a>
### entry-c27968866bad1b86451b · polymas-teacher-teaching-observation-skills

技能  - 专家整理.xlsx / 应用广场数据整理 / 第 33 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C33 | 名称 | polymas-teacher-teaching-observation-skills |
| D33 | 中文名 | 教师教学观测技能 |
| B（合并继承自 B2；B2:B36） | 原值见锚点 | 业务 |
| A（合并继承自 A2；A2:A63） | 原值见锚点 | 技能 |

<a id="entry-892e2bed131dbbdd35a3"></a>
### entry-892e2bed131dbbdd35a3 · polymas-teacher-teaching-plan

技能  - 专家整理.xlsx / 应用广场数据整理 / 第 34 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C34 | 名称 | polymas-teacher-teaching-plan |
| D34 | 中文名 | 教学计划技能 |
| B（合并继承自 B2；B2:B36） | 原值见锚点 | 业务 |
| A（合并继承自 A2；A2:A63） | 原值见锚点 | 技能 |

<a id="entry-9e1b91cbe6b67df05741"></a>
### entry-9e1b91cbe6b67df05741 · polymas-teacher-work-calendar

技能  - 专家整理.xlsx / 应用广场数据整理 / 第 35 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C35 | 名称 | polymas-teacher-work-calendar |
| D35 | 中文名 | 工作日历查询技能 |
| B（合并继承自 B2；B2:B36） | 原值见锚点 | 业务 |
| A（合并继承自 A2；A2:A63） | 原值见锚点 | 技能 |

<a id="entry-cbcb0f6bbc52ba694aad"></a>
### entry-cbcb0f6bbc52ba694aad · polymas-tool-skills

技能  - 专家整理.xlsx / 应用广场数据整理 / 第 36 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C36 | 名称 | polymas-tool-skills |
| D36 | 中文名 | 平台通用工具技能 |
| B（合并继承自 B2；B2:B36） | 原值见锚点 | 业务 |
| A（合并继承自 A2；A2:A63） | 原值见锚点 | 技能 |

<a id="entry-28dbe1452b6556df1f6d"></a>
### entry-28dbe1452b6556df1f6d · external-knowledge-search

技能  - 专家整理.xlsx / 应用广场数据整理 / 第 37 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B37 | 来源 | 算法 |
| C37 | 名称 | external-knowledge-search |
| A（合并继承自 A2；A2:A63） | 原值见锚点 | 技能 |

<a id="entry-cb1ff64eabad55f98c81"></a>
### entry-cb1ff64eabad55f98c81 · deep-search

技能  - 专家整理.xlsx / 应用广场数据整理 / 第 38 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C38 | 名称 | deep-search |
| B（合并继承自 B37；B37:B45） | 原值见锚点 | 算法 |
| A（合并继承自 A2；A2:A63） | 原值见锚点 | 技能 |

<a id="entry-768f12a344d24facdb93"></a>
### entry-768f12a344d24facdb93 · resource-understanding

技能  - 专家整理.xlsx / 应用广场数据整理 / 第 39 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C39 | 名称 | resource-understanding |
| B（合并继承自 B37；B37:B45） | 原值见锚点 | 算法 |
| A（合并继承自 A2；A2:A63） | 原值见锚点 | 技能 |

<a id="entry-501952133a29284e72a8"></a>
### entry-501952133a29284e72a8 · creator_tool

技能  - 专家整理.xlsx / 应用广场数据整理 / 第 40 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C40 | 名称 | creator_tool |
| B（合并继承自 B37；B37:B45） | 原值见锚点 | 算法 |
| A（合并继承自 A2；A2:A63） | 原值见锚点 | 技能 |

<a id="entry-138bedf27fc5b3c5bd82"></a>
### entry-138bedf27fc5b3c5bd82 · mintflow-markdown

技能  - 专家整理.xlsx / 应用广场数据整理 / 第 41 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C41 | 名称 | mintflow-markdown |
| B（合并继承自 B37；B37:B45） | 原值见锚点 | 算法 |
| A（合并继承自 A2；A2:A63） | 原值见锚点 | 技能 |

<a id="entry-7d457306be4aa08bf6e1"></a>
### entry-7d457306be4aa08bf6e1 · mintflow-html

技能  - 专家整理.xlsx / 应用广场数据整理 / 第 42 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C42 | 名称 | mintflow-html |
| B（合并继承自 B37；B37:B45） | 原值见锚点 | 算法 |
| A（合并继承自 A2；A2:A63） | 原值见锚点 | 技能 |

<a id="entry-98052c54a05abb886b29"></a>
### entry-98052c54a05abb886b29 · power-html-ppt

技能  - 专家整理.xlsx / 应用广场数据整理 / 第 43 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C43 | 名称 | power-html-ppt |
| B（合并继承自 B37；B37:B45） | 原值见锚点 | 算法 |
| A（合并继承自 A2；A2:A63） | 原值见锚点 | 技能 |

<a id="entry-b9af5bb312d42513ef15"></a>
### entry-b9af5bb312d42513ef15 · lesson_prep

技能  - 专家整理.xlsx / 应用广场数据整理 / 第 44 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C44 | 名称 | lesson_prep |
| B（合并继承自 B37；B37:B45） | 原值见锚点 | 算法 |
| A（合并继承自 A2；A2:A63） | 原值见锚点 | 技能 |

<a id="entry-4b9962e7a4fab27212ff"></a>
### entry-4b9962e7a4fab27212ff · generate-questions

技能  - 专家整理.xlsx / 应用广场数据整理 / 第 45 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C45 | 名称 | generate-questions |
| B（合并继承自 B37；B37:B45） | 原值见锚点 | 算法 |
| A（合并继承自 A2；A2:A63） | 原值见锚点 | 技能 |

<a id="entry-9a7bd6b325a45d97f0f3"></a>
### entry-9a7bd6b325a45d97f0f3 · pincaimao-interview-question

技能  - 专家整理.xlsx / 应用广场数据整理 / 第 46 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B46 | 来源 | 其他 |
| C46 | 名称 | pincaimao-interview-question |
| D46 | 中文名 | 面试出题大师 |
| A（合并继承自 A2；A2:A63） | 原值见锚点 | 技能 |

<a id="entry-642fc5d78faa056deada"></a>
### entry-642fc5d78faa056deada · cyber-ppt

技能  - 专家整理.xlsx / 应用广场数据整理 / 第 47 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C47 | 名称 | cyber-ppt |
| D47 | 中文名 | cyber-ppt |
| A（合并继承自 A2；A2:A63） | 原值见锚点 | 技能 |
| B（合并继承自 B46；B46:B60） | 原值见锚点 | 其他 |

<a id="entry-587a1fdcb23781b5a0ef"></a>
### entry-587a1fdcb23781b5a0ef · rank

技能  - 专家整理.xlsx / 应用广场数据整理 / 第 48 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C48 | 名称 | rank |
| D48 | 中文名 | rank |
| A（合并继承自 A2；A2:A63） | 原值见锚点 | 技能 |
| B（合并继承自 B46；B46:B60） | 原值见锚点 | 其他 |

<a id="entry-30a97f5b7b0c67bd2e9e"></a>
### entry-30a97f5b7b0c67bd2e9e · book

技能  - 专家整理.xlsx / 应用广场数据整理 / 第 49 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C49 | 名称 | book |
| D49 | 中文名 | book |
| A（合并继承自 A2；A2:A63） | 原值见锚点 | 技能 |
| B（合并继承自 B46；B46:B60） | 原值见锚点 | 其他 |

<a id="entry-b8995551a33c33cc74b3"></a>
### entry-b8995551a33c33cc74b3 · present

技能  - 专家整理.xlsx / 应用广场数据整理 / 第 50 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C50 | 名称 | present |
| D50 | 中文名 | present |
| A（合并继承自 A2；A2:A63） | 原值见锚点 | 技能 |
| B（合并继承自 B46；B46:B60） | 原值见锚点 | 其他 |

<a id="entry-8901592cfb719224820e"></a>
### entry-8901592cfb719224820e · think

技能  - 专家整理.xlsx / 应用广场数据整理 / 第 51 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C51 | 名称 | think |
| D51 | 中文名 | think |
| A（合并继承自 A2；A2:A63） | 原值见锚点 | 技能 |
| B（合并继承自 B46；B46:B60） | 原值见锚点 | 其他 |

<a id="entry-6de24f4da40d80c60a71"></a>
### entry-6de24f4da40d80c60a71 · word

技能  - 专家整理.xlsx / 应用广场数据整理 / 第 52 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C52 | 名称 | word |
| D52 | 中文名 | word |
| A（合并继承自 A2；A2:A63） | 原值见锚点 | 技能 |
| B（合并继承自 B46；B46:B60） | 原值见锚点 | 其他 |

<a id="entry-9e19724b42a668746d24"></a>
### entry-9e19724b42a668746d24 · baoyu-infographic

技能  - 专家整理.xlsx / 应用广场数据整理 / 第 53 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C53 | 名称 | baoyu-infographic |
| D53 | 中文名 | baoyu-infographic |
| A（合并继承自 A2；A2:A63） | 原值见锚点 | 技能 |
| B（合并继承自 B46；B46:B60） | 原值见锚点 | 其他 |

<a id="entry-39252059db383dc00f79"></a>
### entry-39252059db383dc00f79 · explain-like-socrates

技能  - 专家整理.xlsx / 应用广场数据整理 / 第 54 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C54 | 名称 | explain-like-socrates |
| D54 | 中文名 | explain-like-socrates |
| A（合并继承自 A2；A2:A63） | 原值见锚点 | 技能 |
| B（合并继承自 B46；B46:B60） | 原值见锚点 | 其他 |

<a id="entry-55979e2d82a9d24b2bb1"></a>
### entry-55979e2d82a9d24b2bb1 · math-intuition-builder

技能  - 专家整理.xlsx / 应用广场数据整理 / 第 55 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C55 | 名称 | math-intuition-builder |
| D55 | 中文名 | math-intuition-builder |
| A（合并继承自 A2；A2:A63） | 原值见锚点 | 技能 |
| B（合并继承自 B46；B46:B60） | 原值见锚点 | 其他 |

<a id="entry-62f505bcde43f994d315"></a>
### entry-62f505bcde43f994d315 · ppt-master

技能  - 专家整理.xlsx / 应用广场数据整理 / 第 56 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C56 | 名称 | ppt-master |
| D56 | 中文名 | ppt-master |
| A（合并继承自 A2；A2:A63） | 原值见锚点 | 技能 |
| B（合并继承自 B46；B46:B60） | 原值见锚点 | 其他 |

<a id="entry-70a672ec053f499b1081"></a>
### entry-70a672ec053f499b1081 · scientific-schematics

技能  - 专家整理.xlsx / 应用广场数据整理 / 第 57 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C57 | 名称 | scientific-schematics |
| D57 | 中文名 | scientific-schematics |
| A（合并继承自 A2；A2:A63） | 原值见锚点 | 技能 |
| B（合并继承自 B46；B46:B60） | 原值见锚点 | 其他 |

<a id="entry-522bd8be1394cef0ed17"></a>
### entry-522bd8be1394cef0ed17 · statistical-analysis

技能  - 专家整理.xlsx / 应用广场数据整理 / 第 58 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C58 | 名称 | statistical-analysis |
| D58 | 中文名 | statistical-analysis |
| A（合并继承自 A2；A2:A63） | 原值见锚点 | 技能 |
| B（合并继承自 B46；B46:B60） | 原值见锚点 | 其他 |

<a id="entry-720e3482b4f240fb7303"></a>
### entry-720e3482b4f240fb7303 · find-skills

技能  - 专家整理.xlsx / 应用广场数据整理 / 第 59 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C59 | 名称 | find-skills |
| D59 | 中文名 | find-skills |
| A（合并继承自 A2；A2:A63） | 原值见锚点 | 技能 |
| B（合并继承自 B46；B46:B60） | 原值见锚点 | 其他 |

<a id="entry-5c454e31ed4c6c6eeaae"></a>
### entry-5c454e31ed4c6c6eeaae · skill-creator

技能  - 专家整理.xlsx / 应用广场数据整理 / 第 60 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C60 | 名称 | skill-creator |
| D60 | 中文名 | skill-creator |
| A（合并继承自 A2；A2:A63） | 原值见锚点 | 技能 |
| B（合并继承自 B46；B46:B60） | 原值见锚点 | 其他 |

<a id="entry-ef4f977b49c51f9e3466"></a>
### entry-ef4f977b49c51f9e3466 · grade-sentence-paraphrase100

技能  - 专家整理.xlsx / 应用广场数据整理 / 第 61 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B61 | 来源 | 批阅 |
| C61 | 名称 | grade-sentence-paraphrase100 |
| D61 | 中文名 | 08f1ZOXJwD |
| E61 | 未命名列 E | 这几个是从pds中找的 |
| A（合并继承自 A2；A2:A63） | 原值见锚点 | 技能 |

<a id="entry-2f5939f21bbca41912f2"></a>
### entry-2f5939f21bbca41912f2 · micro-lab1-morphology-grading

技能  - 专家整理.xlsx / 应用广场数据整理 / 第 62 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C62 | 名称 | micro-lab1-morphology-grading |
| D62 | 中文名 | Ha8JV29Ek9 |
| E62 | 未命名列 E | 这几个是从pds中找的 |
| A（合并继承自 A2；A2:A63） | 原值见锚点 | 技能 |
| B（合并继承自 B61；B61:B63） | 原值见锚点 | 批阅 |

<a id="entry-9559b6e45fa42a3085bf"></a>
### entry-9559b6e45fa42a3085bf · grade-java-web-assignment

技能  - 专家整理.xlsx / 应用广场数据整理 / 第 63 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C63 | 名称 | grade-java-web-assignment |
| D63 | 中文名 | e5xriHKYgH |
| E63 | 未命名列 E | 这几个是从pds中找的 |
| A（合并继承自 A2；A2:A63） | 原值见锚点 | 技能 |
| B（合并继承自 B61；B61:B63） | 原值见锚点 | 批阅 |

<a id="entry-36adfb703b43e6a94ae0"></a>
### entry-36adfb703b43e6a94ae0 · polymas-agent-readme

技能  - 专家整理.xlsx / 技能2 / 第 2 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A2 | 类型 | 业务 |
| B2 | 场景标签 | 平台帮助/导航 |
| C2 | 技能名称 | polymas-agent-readme |
| D2 | 技能中文名 | 平台智能体帮助手册 |
| E2 | 功能点序号 | 1 |
| F2 | 功能点（英文） | platform-help |
| G2 | 功能点（中文） | 平台功能帮助 |
| H2 | 描述 | 展示平台8大模块、34项核心能力及典型问法；引导用户用自然语言描述需求，不执行业务操作 |
| I2 | 负责人 | @赵洪恩 |

<a id="entry-5d82a98c964d5a66e89d"></a>
### entry-5d82a98c964d5a66e89d · polymas-page-navigation

技能  - 专家整理.xlsx / 技能2 / 第 3 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B3 | 场景标签 | 平台导航 |
| C3 | 技能名称 | polymas-page-navigation |
| D3 | 技能中文名 | 页面导航指引技能 |
| E3 | 功能点序号 | 1 |
| F3 | 功能点（英文） | page_navigation |
| G3 | 功能点（中文） | 页面导航指引 |
| H3 | 描述 | 页面导航指引：用户想做某操作但需在页面完成时，返回对应页面链接+一句话操作指引 |
| I3 | 负责人 | @赵洪恩 |
| A（合并继承自 A2；A2:A35） | 原值见锚点 | 业务 |

<a id="entry-d570a561ef40437cf7a2"></a>
### entry-d570a561ef40437cf7a2 · polymas-student-basic-skills

技能  - 专家整理.xlsx / 技能2 / 第 4 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B4 | 场景标签 | 学生班课 |
| C4 | 技能名称 | polymas-student-basic-skills |
| D4 | 技能中文名 | 学生班课查询助手 |
| E4 | 功能点序号 | 1 |
| F4 | 功能点（英文） | course_search |
| G4 | 功能点（中文） | 课程查询 |
| H4 | 描述 | 学生基础技能：根据用户需求智能选择课程搜索和作业查询功能 |
| I4 | 负责人 | @赵洪恩 |
| J4 | 提测状态 | 已提测 |
| K4 | 提测时间 | 46244 |
| L4 | 验证人 | @赵双玲 |
| A（合并继承自 A2；A2:A35） | 原值见锚点 | 业务 |

<a id="entry-f7a4ec17563d239b6c28"></a>
### entry-f7a4ec17563d239b6c28 · polymas-student-basic-skills

技能  - 专家整理.xlsx / 技能2 / 第 5 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C5 | 技能名称 | polymas-student-basic-skills |
| D5 | 技能中文名 | 学生班课查询助手 |
| E5 | 功能点序号 | 2 |
| F5 | 功能点（英文） | homework_query |
| G5 | 功能点（中文） | 作业查询 |
| H5 | 描述 | 学生基础技能：根据用户需求智能选择课程搜索和作业查询功能 |
| I5 | 负责人 | @赵洪恩 |
| J5 | 提测状态 | 已提测 |
| K5 | 提测时间 | 46244 |
| L5 | 验证人 | @赵双玲 |
| B（合并继承自 B4；B4:B5） | 原值见锚点 | 学生班课 |
| A（合并继承自 A2；A2:A35） | 原值见锚点 | 业务 |

<a id="entry-62c0ed2ff4ec34771eb6"></a>
### entry-62c0ed2ff4ec34771eb6 · polymas-get-student-course-homework

技能  - 专家整理.xlsx / 技能2 / 第 6 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B6 | 场景标签 | 学生作业 |
| C6 | 技能名称 | polymas-get-student-course-homework |
| D6 | 技能中文名 | 学生作业管理助手 |
| E6 | 功能点序号 | 1 |
| F6 | 功能点（英文） | homework_query |
| G6 | 功能点（中文） | 作业查询 |
| H6 | 描述 | 查询学生在课程下的所有作业信息，包括作业详细信息、作业关联班级信息、班级作业结束时间、完成率统计等数据。 |
| I6 | 负责人 | @赵洪恩 |
| J6 | 提测状态 | 已提测 |
| K6 | 提测时间 | 46244 |
| L6 | 验证人 | @赵双玲 |
| A（合并继承自 A2；A2:A35） | 原值见锚点 | 业务 |

<a id="entry-05cacd7add4ca64c2616"></a>
### entry-05cacd7add4ca64c2616 · find-skills

技能  - 专家整理.xlsx / 技能2 / 第 7 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B7 | 场景标签 | 通用工具/Skill |
| C7 | 技能名称 | find-skills |
| D7 | 技能中文名 | find-skills |
| I7 | 负责人 | @赵洪恩 |
| J7 | 提测状态 | 已提测 |
| K7 | 提测时间 | 46244 |
| L7 | 验证人 | @赵双玲 |
| A（合并继承自 A2；A2:A35） | 原值见锚点 | 业务 |

<a id="entry-5d649d40885777e51091"></a>
### entry-5d649d40885777e51091 · skill-creator

技能  - 专家整理.xlsx / 技能2 / 第 8 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C8 | 技能名称 | skill-creator |
| D8 | 技能中文名 | skill-creator |
| I8 | 负责人 | @赵洪恩 |
| J8 | 提测状态 | 已提测 |
| K8 | 提测时间 | 46244 |
| L8 | 验证人 | @赵双玲 |
| B（合并继承自 B7；B7:B8） | 原值见锚点 | 通用工具/Skill |
| A（合并继承自 A2；A2:A35） | 原值见锚点 | 业务 |

<a id="entry-2b36ccd802a6c36b67ea"></a>
### entry-2b36ccd802a6c36b67ea · polymas-student-teaching-plan

技能  - 专家整理.xlsx / 技能2 / 第 9 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B9 | 场景标签 | 教学计划/查询 |
| C9 | 技能名称 | polymas-student-teaching-plan |
| D9 | 技能中文名 | 教学计划查询（学生视角增强） |
| E9 | 功能点序号 | 1 |
| G9 | 功能点（中文） | 教学计划查询 |
| H9 | 描述 | 查询学生可见的课程教学计划、单元、主题、知识点和关联活动 |
| I9 | 负责人 | @朱希文 |
| J9 | 提测状态 | 已提测 |
| K9 | 提测时间 | 46241 |
| L9 | 验证人 | @赵双玲 |
| A（合并继承自 A2；A2:A35） | 原值见锚点 | 业务 |

<a id="entry-7a2fce10d4d32014f5de"></a>
### entry-7a2fce10d4d32014f5de · polymas-student-score-skills

技能  - 专家整理.xlsx / 技能2 / 第 10 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B10 | 场景标签 | 成绩管理/查询 |
| C10 | 技能名称 | polymas-student-score-skills |
| D10 | 技能中文名 | 成绩查询（学生视角增强） |
| E10 | 功能点序号 | 1 |
| G10 | 功能点（中文） | 本人课程成绩查询 |
| H10 | 描述 | 查询学生本人总成绩、分项和规则 |
| I10 | 负责人 | @朱希文 |
| J10 | 提测状态 | 已提测 |
| K10 | 提测时间 | 46241 |
| L10 | 验证人 | @赵双玲 |
| A（合并继承自 A2；A2:A35） | 原值见锚点 | 业务 |

<a id="entry-46d3c7f1c15ca3e10b86"></a>
### entry-46d3c7f1c15ca3e10b86 · polymas-student-classroom-report-skills

技能  - 专家整理.xlsx / 技能2 / 第 11 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B11 | 场景标签 | 课堂报告/数据 |
| C11 | 技能名称 | polymas-student-classroom-report-skills |
| D11 | 技能中文名 | 课堂报告查询（学生视角增强） |
| E11 | 功能点序号 | 1 |
| G11 | 功能点（中文） | 课堂报告查询 |
| H11 | 描述 | 查询学生可见的课堂报告和回放元数据 |
| I11 | 负责人 | @朱希文 |
| J11 | 提测状态 | 已提测 |
| K11 | 提测时间 | 46241 |
| L11 | 验证人 | @赵双玲 |
| A（合并继承自 A2；A2:A35） | 原值见锚点 | 业务 |

<a id="entry-a29eda470e6d365db743"></a>
### entry-a29eda470e6d365db743 · polymas-student-agent-teaching-skill

技能  - 专家整理.xlsx / 技能2 / 第 12 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B12 | 场景标签 | 智能体教学/查询 |
| C12 | 技能名称 | polymas-student-agent-teaching-skill |
| D12 | 技能中文名 | 智能体教学查询（学生视角增强） |
| E12 | 功能点序号 | 1 |
| G12 | 功能点（中文） | 智能体教学查询 |
| H12 | 描述 | 查询学生可见的智能体课堂、合集、开放状态和本人学习进度 |
| I12 | 负责人 | @朱希文 |
| J12 | 提测状态 | 已提测 |
| K12 | 提测时间 | 46242 |
| L12 | 验证人 | @赵双玲 |
| A（合并继承自 A2；A2:A35） | 原值见锚点 | 业务 |

<a id="entry-6d2c98efad60757d062a"></a>
### entry-6d2c98efad60757d062a · polymas-student-discussion-skills

技能  - 专家整理.xlsx / 技能2 / 第 13 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B13 | 场景标签 | 教学活动/讨论 |
| C13 | 技能名称 | polymas-student-discussion-skills |
| D13 | 技能中文名 | 讨论情况查询（学生视角增强） |
| E13 | 功能点序号 | 1 |
| G13 | 功能点（中文） | 讨论情况查询 |
| H13 | 描述 | 查询学生可见话题、筛选、详情和附件 |
| I13 | 负责人 | @赵洪恩 |
| J13 | 提测状态 | 已提测 |
| K13 | 提测时间 | 46242 |
| L13 | 验证人 | @赵双玲 |
| A（合并继承自 A2；A2:A35） | 原值见锚点 | 业务 |

<a id="entry-2b5ec8ea5c57059bbd9a"></a>
### entry-2b5ec8ea5c57059bbd9a · polymas-student-todo-notification-skills

技能  - 专家整理.xlsx / 技能2 / 第 14 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B14 | 场景标签 | 首页/待办 |
| C14 | 技能名称 | polymas-student-todo-notification-skills |
| D14 | 技能中文名 | 学生待办与课程通知查询 |
| E14 | 功能点序号 | 1 |
| G14 | 功能点（中文） | 待办与通知查询 |
| H14 | 描述 | 查询当前学生的任务、筛选、搜索与课程通知 |
| I14 | 负责人 | @朱希文 |
| J14 | 提测状态 | 已提测 |
| K14 | 提测时间 | 46242 |
| L14 | 验证人 | @赵双玲 |
| A（合并继承自 A2；A2:A35） | 原值见锚点 | 业务 |

<a id="entry-2c58b383a97b3c4bab38"></a>
### entry-2c58b383a97b3c4bab38 · polymas-student-study-resource

技能  - 专家整理.xlsx / 技能2 / 第 15 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B15 | 场景标签 | 学习资源/查询 |
| C15 | 技能名称 | polymas-student-study-resource |
| D15 | 技能中文名 | 学生学习资源查询 |
| E15 | 功能点序号 | 1 |
| G15 | 功能点（中文） | 学习资源查询 |
| H15 | 描述 | 查询已发布可见资源、要求、知识点、进度和解锁状态 |
| I15 | 负责人 | @朱希文 |
| J15 | 提测状态 | 已提测 |
| K15 | 提测时间 | 46244 |
| L15 | 验证人 | @赵双玲 |
| A（合并继承自 A2；A2:A35） | 原值见锚点 | 业务 |

<a id="entry-0c79aa5964ec7eb48d9c"></a>
### entry-0c79aa5964ec7eb48d9c · polymas-student-study-resource

技能  - 专家整理.xlsx / 技能2 / 第 16 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B16 | 场景标签 | 学习资源/下载 |
| C16 | 技能名称 | polymas-student-study-resource |
| D16 | 技能中文名 | 学生学习资源下载 |
| E16 | 功能点序号 | 1 |
| G16 | 功能点（中文） | 学习资源下载 |
| H16 | 描述 | 下载允许下载的学习资源，并校验权限与链接有效期 |
| I16 | 负责人 | @朱希文 |
| J16 | 提测状态 | 已提测 |
| K16 | 提测时间 | 46244 |
| L16 | 验证人 | @赵双玲 |
| A（合并继承自 A2；A2:A35） | 原值见锚点 | 业务 |

<a id="entry-447e243f6d05a82c7efe"></a>
### entry-447e243f6d05a82c7efe · polymas-get-student-course-homework

技能  - 专家整理.xlsx / 技能2 / 第 17 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B17 | 场景标签 | 学生作业 |
| C17 | 技能名称 | polymas-get-student-course-homework |
| D17 | 技能中文名 | 学生作业查询与反馈 |
| E17 | 功能点序号 | 1 |
| G17 | 功能点（中文） | 作业详情与反馈查询 |
| H17 | 描述 | 查询学生本人作业列表、详情、截止时间、状态、成绩、逐题反馈和批注附件 |
| I17 | 负责人 | @张康 |
| J17 | 提测状态 | 已提测 |
| K17 | 提测时间 | 46244 |
| L17 | 验证人 | @赵双玲 |
| A（合并继承自 A2；A2:A35） | 原值见锚点 | 业务 |

<a id="entry-08eafef29b3369838a50"></a>
### entry-08eafef29b3369838a50 · polymas-get-student-course-homework

技能  - 专家整理.xlsx / 技能2 / 第 18 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B18 | 场景标签 | 学生作业/提交 |
| C18 | 技能名称 | polymas-get-student-course-homework |
| D18 | 技能中文名 | 学生提交与修改作业 |
| E18 | 功能点序号 | 1 |
| G18 | 功能点（中文） | 作业提交与修改 |
| H18 | 描述 | 提交或修改自定义作业和小组作业 |
| I18 | 负责人 | @张康 |
| J18 | 提测状态 | - |
| A（合并继承自 A2；A2:A35） | 原值见锚点 | 业务 |

<a id="entry-71a80451266ed88d4a63"></a>
### entry-71a80451266ed88d4a63 · polymas-get-student-course-homework

技能  - 专家整理.xlsx / 技能2 / 第 19 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B19 | 场景标签 | 学生作业/互动 |
| C19 | 技能名称 | polymas-get-student-course-homework |
| D19 | 技能中文名 | 学生作业互动 |
| E19 | 功能点序号 | 1 |
| G19 | 功能点（中文） | 作业互动 |
| H19 | 描述 | 在作业下提问、回复并查询新回复 |
| I19 | 负责人 | @张康 |
| J19 | 提测状态 | 已提测 |
| K19 | 提测时间 | 46244 |
| L19 | 验证人 | @赵双玲 |
| A（合并继承自 A2；A2:A35） | 原值见锚点 | 业务 |

<a id="entry-9cb672d72bac339c1fce"></a>
### entry-9cb672d72bac339c1fce · polymas-get-student-course-homework

技能  - 专家整理.xlsx / 技能2 / 第 20 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B20 | 场景标签 | 学生作业/重做 |
| C20 | 技能名称 | polymas-get-student-course-homework |
| D20 | 技能中文名 | 学生重做申请 |
| E20 | 功能点序号 | 1 |
| G20 | 功能点（中文） | 重做申请 |
| H20 | 描述 | 提交作业重做申请并查询次数、截止时间和状态 |
| I20 | 负责人 | @张康 |
| J20 | 提测状态 | 已提测 |
| K20 | 提测时间 | 46244 |
| L20 | 验证人 | @赵双玲 |
| A（合并继承自 A2；A2:A35） | 原值见锚点 | 业务 |

<a id="entry-badecbb280955d2376d7"></a>
### entry-badecbb280955d2376d7 · polymas-get-student-course-homework

技能  - 专家整理.xlsx / 技能2 / 第 21 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B21 | 场景标签 | 学生作业/小组 |
| C21 | 技能名称 | polymas-get-student-course-homework |
| D21 | 技能中文名 | 学生小组学习与组队 |
| E21 | 功能点序号 | 1 |
| G21 | 功能点（中文） | 小组学习与组队 |
| H21 | 描述 | 查询课程小组、成员与空位，并申请加入可用小组 |
| I21 | 负责人 | @张康 |
| J21 | 提测状态 | 已提测 |
| K21 | 提测时间 | 46244 |
| L21 | 验证人 | @赵双玲 |
| A（合并继承自 A2；A2:A35） | 原值见锚点 | 业务 |

<a id="entry-babb093806bf16e33cc2"></a>
### entry-babb093806bf16e33cc2 · polymas-get-student-course-homework

技能  - 专家整理.xlsx / 技能2 / 第 22 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B22 | 场景标签 | 学生作业/互评 |
| C22 | 技能名称 | polymas-get-student-course-homework |
| D22 | 技能中文名 | 学生小组互评 |
| E22 | 功能点序号 | 1 |
| G22 | 功能点（中文） | 小组互评 |
| H22 | 描述 | 提交小组互评并查看本人可见结果 |
| I22 | 负责人 | @张康 |
| J22 | 提测状态 | 已提测 |
| K22 | 提测时间 | 46244 |
| L22 | 验证人 | @赵双玲 |
| A（合并继承自 A2；A2:A35） | 原值见锚点 | 业务 |

<a id="entry-c2b9b3b176d7625e4ef7"></a>
### entry-c2b9b3b176d7625e4ef7 · polymas-student-exam-skills

技能  - 专家整理.xlsx / 技能2 / 第 23 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B23 | 场景标签 | 考试/查询 |
| C23 | 技能名称 | polymas-student-exam-skills |
| D23 | 技能中文名 | 学生考试查询与结果 |
| E23 | 功能点序号 | 1 |
| G23 | 功能点（中文） | 考试查询与结果 |
| H23 | 描述 | 查询本人考试安排、规则(考试描述)、监考提醒、成绩和解析 |
| I23 | 负责人 | @朱希文 |
| J23 | 提测状态 | 已提测 |
| K23 | 提测时间 | 46244 |
| L23 | 验证人 | @赵双玲 |
| A（合并继承自 A2；A2:A35） | 原值见锚点 | 业务 |

<a id="entry-a355d51fad1dda5bd281"></a>
### entry-a355d51fad1dda5bd281 · polymas-student-discussion-skills

技能  - 专家整理.xlsx / 技能2 / 第 24 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B24 | 场景标签 | 问答讨论/参与 |
| C24 | 技能名称 | polymas-student-discussion-skills |
| D24 | 技能中文名 | 学生讨论参与与本人内容管理 |
| E24 | 功能点序号 | 1 |
| G24 | 功能点（中文） | 讨论参与与本人内容管理 |
| H24 | 描述 | 发布、围观、点赞、回答、回复或删除本人讨论内容 |
| I24 | 负责人 | @赵洪恩 |
| J24 | 提测状态 | 已提测 |
| K24 | 提测时间 | 46242 |
| L24 | 验证人 | @赵双玲 |
| A（合并继承自 A2；A2:A35） | 原值见锚点 | 业务 |

<a id="entry-50ccaee7123400624da2"></a>
### entry-50ccaee7123400624da2 · #82（待分配）

技能  - 专家整理.xlsx / 技能2 / 第 25 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B25 | 场景标签 | 群聊/查询 |
| C25 | 技能名称 | #82（待分配） |
| D25 | 技能中文名 | 学生群聊查询 |
| E25 | 功能点序号 | 1 |
| G25 | 功能点（中文） | 群聊查询 |
| H25 | 描述 | 查询学生可见的会话、公告、成员、消息历史和群文件 |
| I25 | 负责人 | @朱希文 |
| J25 | 提测状态 | - |
| A（合并继承自 A2；A2:A35） | 原值见锚点 | 业务 |

<a id="entry-a14e310920cc3b03bd4e"></a>
### entry-a14e310920cc3b03bd4e · #83（待分配）

技能  - 专家整理.xlsx / 技能2 / 第 26 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B26 | 场景标签 | 群聊/消息 |
| C26 | 技能名称 | #83（待分配） |
| D26 | 技能中文名 | 学生群消息发送与本人消息处理 |
| E26 | 功能点序号 | 1 |
| G26 | 功能点（中文） | 发送与处理本人消息 |
| H26 | 描述 | 发送、转发、引用、撤回或重新编辑本人消息 |
| I26 | 负责人 | @朱希文 |
| J26 | 提测状态 | - |
| A（合并继承自 A2；A2:A35） | 原值见锚点 | 业务 |

<a id="entry-02cc11aa54092fe4a61b"></a>
### entry-02cc11aa54092fe4a61b · #84（待分配）

技能  - 专家整理.xlsx / 技能2 / 第 27 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B27 | 场景标签 | 群聊/设置 |
| C27 | 技能名称 | #84（待分配） |
| D27 | 技能中文名 | 学生群聊个人设置 |
| E27 | 功能点序号 | 1 |
| G27 | 功能点（中文） | 群聊个人设置 |
| H27 | 描述 | 修改当前学生的群名片、置顶和免打扰设置 |
| I27 | 负责人 | @朱希文 |
| J27 | 提测状态 | - |
| A（合并继承自 A2；A2:A35） | 原值见锚点 | 业务 |

<a id="entry-0b396900252ec9b07f7e"></a>
### entry-0b396900252ec9b07f7e · #85（待分配）

技能  - 专家整理.xlsx / 技能2 / 第 28 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B28 | 场景标签 | 讨论与群聊/举报 |
| C28 | 技能名称 | #85（待分配） |
| D28 | 技能中文名 | 学生内容举报 |
| E28 | 功能点序号 | 1 |
| G28 | 功能点（中文） | 内容举报 |
| H28 | 描述 | 举报讨论区或群聊中的不当内容，并查询受理状态 |
| I28 | 负责人 | @朱希文 |
| J28 | 提测状态 | - |
| A（合并继承自 A2；A2:A35） | 原值见锚点 | 业务 |

<a id="entry-e7d5c022c5b9eb79cfe5"></a>
### entry-e7d5c022c5b9eb79cfe5 · polymas-student-practice-skills

技能  - 专家整理.xlsx / 技能2 / 第 29 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B29 | 场景标签 | 刷题训练/查询 |
| C29 | 技能名称 | polymas-student-practice-skills |
| D29 | 技能中文名 | 学生刷题训练查询与反馈 |
| E29 | 功能点序号 | 1 |
| G29 | 功能点（中文） | 训练查询与反馈 |
| H29 | 描述 | 查询本人练习历史、结果、错题、收藏 |
| I29 | 负责人 | @张康 |
| J29 | 提测状态 | 已提测 |
| K29 | 提测时间 | 46244 |
| L29 | 验证人 | @赵双玲 |
| A（合并继承自 A2；A2:A35） | 原值见锚点 | 业务 |

<a id="entry-b37aa55337017181e5b6"></a>
### entry-b37aa55337017181e5b6 · polymas-student-practice-skills

技能  - 专家整理.xlsx / 技能2 / 第 30 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B30 | 场景标签 | 刷题训练/发起 |
| C30 | 技能名称 | polymas-student-practice-skills |
| D30 | 技能中文名 | 学生刷题训练配置与发起 |
| E30 | 功能点序号 | 1 |
| G30 | 功能点（中文） | 训练配置与发起 |
| H30 | 描述 | 随机、精准、错题或收藏发起练习 |
| I30 | 负责人 | @张康 |
| J30 | 提测状态 | 已提测 |
| K30 | 提测时间 | 46244 |
| L30 | 验证人 | @赵双玲 |
| M30 | 未命名列 M | 精选练习没知识点没做 |
| A（合并继承自 A2；A2:A35） | 原值见锚点 | 业务 |

<a id="entry-955f72f6720675edfd4d"></a>
### entry-955f72f6720675edfd4d · polymas-student-practice-skills

技能  - 专家整理.xlsx / 技能2 / 第 31 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B31 | 场景标签 | 刷题训练/维护 |
| C31 | 技能名称 | polymas-student-practice-skills |
| D31 | 技能中文名 | 学生错题与收藏维护 |
| E31 | 功能点序号 | 1 |
| G31 | 功能点（中文） | 错题与收藏维护 |
| H31 | 描述 | 批量移除错题或收藏题 |
| I31 | 负责人 | @张康 |
| J31 | 提测状态 | 已提测 |
| K31 | 提测时间 | 46244 |
| L31 | 验证人 | @赵双玲 |
| A（合并继承自 A2；A2:A35） | 原值见锚点 | 业务 |

<a id="entry-59a1ee58d7f6e0cd1828"></a>
### entry-59a1ee58d7f6e0cd1828 · polymas-student-discussion-skills

技能  - 专家整理.xlsx / 技能2 / 第 32 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B32 | 场景标签 | 问答讨论/权限 |
| C32 | 技能名称 | polymas-student-discussion-skills |
| D32 | 技能中文名 | 学生讨论越权管理 |
| E32 | 功能点序号 | 1 |
| G32 | 功能点（中文） | 讨论越权管理 |
| H32 | 描述 | 学生端可见但权限未确认的删除他人内容、置顶回答能力 |
| I32 | 负责人 | @赵洪恩 |
| J32 | 提测状态 | 已提测 |
| K32 | 提测时间 | 46242 |
| L32 | 验证人 | @赵双玲 |
| A（合并继承自 A2；A2:A35） | 原值见锚点 | 业务 |

<a id="entry-5eceb98966d23a1d6a9d"></a>
### entry-5eceb98966d23a1d6a9d · CAND-S02

技能  - 专家整理.xlsx / 技能2 / 第 33 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B33 | 场景标签 | 群聊/权限 |
| C33 | 技能名称 | CAND-S02 |
| D33 | 技能中文名 | 学生删除群消息 |
| E33 | 功能点序号 | 1 |
| G33 | 功能点（中文） | 删除群消息 |
| H33 | 描述 | 学生端可见但删除语义和对象所有权未确认的群消息删除能力 |
| I33 | 负责人 | @朱希文 |
| J33 | 提测状态 | - |
| A（合并继承自 A2；A2:A35） | 原值见锚点 | 业务 |

<a id="entry-657a0a7a9918e4aa42f4"></a>
### entry-657a0a7a9918e4aa42f4 · CAND-S03

技能  - 专家整理.xlsx / 技能2 / 第 34 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B34 | 场景标签 | 群文件/权限 |
| C34 | 技能名称 | CAND-S03 |
| D34 | 技能中文名 | 学生群文件管理 |
| E34 | 功能点序号 | 1 |
| G34 | 功能点（中文） | 群文件管理 |
| H34 | 描述 | 学生端可见但上传、重命名和删除权限未确认的群文件管理能力 |
| I34 | 负责人 | @朱希文 |
| J34 | 提测状态 | - |
| A（合并继承自 A2；A2:A35） | 原值见锚点 | 业务 |

<a id="entry-7abef0a7ac0faee9db8c"></a>
### entry-7abef0a7ac0faee9db8c · polymas-student-custom-study-skills

技能  - 专家整理.xlsx / 技能2 / 第 35 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B35 | 场景标签 | 自定义学习 |
| C35 | 技能名称 | polymas-student-custom-study-skills |
| D35 | 技能中文名 | 自定义学习 |
| E35 | 功能点序号 | 1 |
| G35 | 功能点（中文） | 创建学习目标并启动学习 |
| H35 | 描述 | 学生主动创建一个学习目标，并围绕该目标发起学习 |
| I35 | 负责人 | @赵洪恩 |
| J35 | 提测状态 | 已提测 |
| K35 | 提测时间 | 46242 |
| L35 | 验证人 | @赵双玲 |
| A（合并继承自 A2；A2:A35） | 原值见锚点 | 业务 |

<a id="entry-01a47265f27e5dfc7cac"></a>
### entry-01a47265f27e5dfc7cac · polymas-teacher-save-to-skills

技能  - 专家整理.xlsx / 技能2 / 第 36 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A36 | 类型 | 教师端-内置 |
| B36 | 场景标签 | 保存至 |
| C36 | 技能名称 | polymas-teacher-save-to-skills |
| D36 | 技能中文名 | 文件管存助手 |
| G36 | 功能点（中文） | 文件<br>保存至工作空间<br>保存至xxx资源库<br>保存至备课<br> |
| H36 | 描述 | 保存至 技能； 比如对话里讲 把这个文件保存到工作空间、保存到个人资源库、保存到xxx课程资源库、保存到备课 |
| I36 | 负责人 | @赵洪恩 |
| J36 | 提测状态 | 已提测 |
| K36 | 提测时间 | 46242 |
| L36 | 验证人 | @赵双玲 |

<a id="entry-93ae63dcf46af427433f"></a>
### entry-93ae63dcf46af427433f · literature-review

技能  - 专家整理.xlsx / 技能2 / 第 37 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A37 | 类型 | 其他 |
| B37 | 场景标签 | 科研/文献综述 |
| C37 | 技能名称 | literature-review |
| D37 | 技能中文名 | 系统文献综述 |
| E37 | 功能点序号 | 1 |
| G37 | 功能点（中文） | 系统文献检索、证据综合与研究空白识别 |
| H37 | 描述 | Conduct comprehensive, systematic literature reviews using multiple academic databases (PubMed, arXiv, bioRxiv, Semantic Scholar, etc.). This skill should be used when conducting systematic literature reviews, meta-analyses, research synthesis, or comprehensive literature searches across biomedical, scientific, and technical domains. Creates professionally formatted markdown documents and PDFs with verified citations in multiple citation styles (APA, Nature, Vancouver, etc.). |
| I37 | 负责人 | https://www.skills.sh/davila7/claude-code-templates/literature-review |

<a id="entry-89a662b5f9e54b8cb26c"></a>
### entry-89a662b5f9e54b8cb26c · scientific-critical-thinking

技能  - 专家整理.xlsx / 技能2 / 第 38 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B38 | 场景标签 | 科研/证据评估 |
| C38 | 技能名称 | scientific-critical-thinking |
| D38 | 技能中文名 | 科研批判性思维 |
| E38 | 功能点序号 | 1 |
| G38 | 功能点（中文） | 研究方法、统计有效性与证据质量评估 |
| H38 | 描述 | Evaluate research rigor. Assess methodology, experimental design, statistical validity, biases, confounding, evidence quality (GRADE, Cochrane ROB), for critical analysis of scientific claims. |
| I38 | 负责人 | https://www.skills.sh/davila7/claude-code-templates/scientific-critical-thinking |
| A（合并继承自 A37；A37:A46） | 原值见锚点 | 其他 |

<a id="entry-a9021dc5f2ded172a883"></a>
### entry-a9021dc5f2ded172a883 · scientific-brainstorming

技能  - 专家整理.xlsx / 技能2 / 第 39 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B39 | 场景标签 | 科研/选题构思 |
| C39 | 技能名称 | scientific-brainstorming |
| D39 | 技能中文名 | 科研选题头脑风暴 |
| E39 | 功能点序号 | 1 |
| G39 | 功能点（中文） | 研究选题、跨学科连接与研究空白构思 |
| H39 | 描述 | Research ideation partner. Generate hypotheses, explore interdisciplinary connections, challenge assumptions, develop methodologies, identify research gaps, for creative scientific problem-solving. |
| I39 | 负责人 | https://www.skills.sh/davila7/claude-code-templates/scientific-brainstorming |
| A（合并继承自 A37；A37:A46） | 原值见锚点 | 其他 |

<a id="entry-f62de41dd99b0be923c5"></a>
### entry-f62de41dd99b0be923c5 · hypothesis-generation

技能  - 专家整理.xlsx / 技能2 / 第 40 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B40 | 场景标签 | 科研/研究假设 |
| C40 | 技能名称 | hypothesis-generation |
| D40 | 技能中文名 | 研究假设生成 |
| E40 | 功能点序号 | 1 |
| G40 | 功能点（中文） | 从观察出发形成可检验假设与竞争性解释 |
| H40 | 描述 | Generate testable hypotheses. Formulate from observations, design experiments, explore competing explanations, develop predictions, propose mechanisms, for scientific inquiry across domains. |
| I40 | 负责人 | https://www.skills.sh/davila7/claude-code-templates/hypothesis-generation |
| A（合并继承自 A37；A37:A46） | 原值见锚点 | 其他 |

<a id="entry-30d9d8cf410670d7c9d1"></a>
### entry-30d9d8cf410670d7c9d1 · peer-review

技能  - 专家整理.xlsx / 技能2 / 第 41 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B41 | 场景标签 | 科研/成果评审 |
| C41 | 技能名称 | peer-review |
| D41 | 技能中文名 | 科研同行评审 |
| E41 | 功能点序号 | 1 |
| G41 | 功能点（中文） | 论文与研究方案的方法、统计、复现和伦理评审 |
| H41 | 描述 | Systematic peer review toolkit. Evaluate methodology, statistics, design, reproducibility, ethics, figure integrity, reporting standards, for manuscript and grant review across disciplines. |
| I41 | 负责人 | https://www.skills.sh/davila7/claude-code-templates/peer-review |
| A（合并继承自 A37；A37:A46） | 原值见锚点 | 其他 |

<a id="entry-a4b373d48eebef9ba225"></a>
### entry-a4b373d48eebef9ba225 · openalex-database

技能  - 专家整理.xlsx / 技能2 / 第 42 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B42 | 场景标签 | 科研/文献检索 |
| C42 | 技能名称 | openalex-database |
| D42 | 技能中文名 | OpenAlex 学术检索 |
| E42 | 功能点序号 | 1 |
| G42 | 功能点（中文） | 学术论文、作者、机构、主题与引用关系检索 |
| H42 | 描述 | Query and analyze scholarly literature using the OpenAlex database. This skill should be used when searching for academic papers, analyzing research trends, finding works by authors or institutions, tracking citations, discovering open access publications, or conducting bibliometric analysis across 240M+ scholarly works. Use for literature searches, research output analysis, citation analysis, and academic database queries. |
| I42 | 负责人 | https://www.skills.sh/davila7/claude-code-templates/openalex-database |
| A（合并继承自 A37；A37:A46） | 原值见锚点 | 其他 |

<a id="entry-39edb9d43822b66b5b8b"></a>
### entry-39edb9d43822b66b5b8b · research-lookup

技能  - 专家整理.xlsx / 技能2 / 第 43 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B43 | 场景标签 | 信息查询/科研 |
| C43 | 技能名称 | research-lookup |
| D43 | 技能中文名 | 最新研究信息查询 |
| E43 | 功能点序号 | 1 |
| G43 | 功能点（中文） | 查询最新论文、研究发现、技术资料与统计信息 |
| H43 | 描述 | Look up current research information using Perplexity's Sonar Pro Search or Sonar Reasoning Pro models through OpenRouter. Automatically selects the best model based on query complexity. Search academic papers, recent studies, technical documentation, and general research information with citations. |
| I43 | 负责人 | https://www.skills.sh/davila7/claude-code-templates/research-lookup |
| A（合并继承自 A37；A37:A46） | 原值见锚点 | 其他 |

<a id="entry-203ff94c5a881b504172"></a>
### entry-203ff94c5a881b504172 · perplexity-search

技能  - 专家整理.xlsx / 技能2 / 第 44 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B44 | 场景标签 | 信息查询/竞赛机会 |
| C44 | 技能名称 | perplexity-search |
| D44 | 技能中文名 | 实时信息与竞赛机会检索 |
| E44 | 功能点序号 | 1 |
| G44 | 功能点（中文） | 检索最新竞赛、活动、奖学金、科研机会与公开信息 |
| H44 | 描述 | Perform AI-powered web searches with real-time information using Perplexity models via LiteLLM and OpenRouter. This skill should be used when conducting web searches for current information, finding recent scientific literature, getting grounded answers with source citations, or accessing information beyond the model's knowledge cutoff. Provides access to multiple Perplexity models including Sonar Pro, Sonar Pro Search (advanced agentic search), and Sonar Reasoning Pro through a single OpenRouter API key. |
| I44 | 负责人 | https://www.skills.sh/davila7/claude-code-templates/perplexity-search |
| A（合并继承自 A37；A37:A46） | 原值见锚点 | 其他 |

<a id="entry-c78e6ae76da81aaf372c"></a>
### entry-c78e6ae76da81aaf372c · scientific-visualization

技能  - 专家整理.xlsx / 技能2 / 第 45 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B45 | 场景标签 | 科研/数据表达 |
| C45 | 技能名称 | scientific-visualization |
| D45 | 技能中文名 | 科研数据可视化 |
| E45 | 功能点序号 | 1 |
| G45 | 功能点（中文） | 科研数据图表、误差与显著性结果可视化 |
| H45 | 描述 | Create publication figures with matplotlib/seaborn/plotly. Multi-panel layouts, error bars, significance markers, colorblind-safe, export PDF/EPS/TIFF, for journal-ready scientific plots. |
| I45 | 负责人 | https://www.skills.sh/davila7/claude-code-templates/scientific-visualization |
| A（合并继承自 A37；A37:A46） | 原值见锚点 | 其他 |

<a id="entry-c21805b2b9906e5824b8"></a>
### entry-c21805b2b9906e5824b8 · planning-with-files

技能  - 专家整理.xlsx / 技能2 / 第 46 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B46 | 场景标签 | 学习减压/任务规划 |
| C46 | 技能名称 | planning-with-files |
| D46 | 技能中文名 | 复杂学习任务拆解 |
| E46 | 功能点序号 | 1 |
| G46 | 功能点（中文） | 将复杂学习或研究任务拆成计划、发现与进度记录 |
| H46 | 描述 | Implements Manus-style file-based planning for complex tasks. Creates task_plan.md, findings.md, and progress.md. Use when starting complex multi-step tasks, research projects, or any task requiring &gt;5 tool calls. |
| I46 | 负责人 | https://www.skills.sh/davila7/claude-code-templates/planning-with-files |
| A（合并继承自 A37；A37:A46） | 原值见锚点 | 其他 |

<a id="entry-2093e7ed69daa4b1c041"></a>
### entry-2093e7ed69daa4b1c041 · polymas-student-basic-skills

技能  - 专家整理.xlsx / 技能推荐列表2 / 第 2 行

NID：P0oNhYY02C；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A2 | 类型 | 课代表默认技能 |
| B2 | 来源 | 业务开发 |
| C2 | 技能 | polymas-student-basic-skills |
| D2 | 技能nid | P0oNhYY02C |
| E2 | 是否必须推送 | 必须 |

<a id="entry-7bf0944077057b3fd448"></a>
### entry-7bf0944077057b3fd448 · polymas-get-student-course-homework

技能  - 专家整理.xlsx / 技能推荐列表2 / 第 3 行

NID：y9azCkSHMg；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A3 | 类型 | 课代表默认技能 |
| B3 | 来源 | 业务开发 |
| C3 | 技能 | polymas-get-student-course-homework |
| D3 | 技能nid | y9azCkSHMg |
| E3 | 是否必须推送 | 必须 |

<a id="entry-1254f64ed2757ba633e8"></a>
### entry-1254f64ed2757ba633e8 · find-skills

技能  - 专家整理.xlsx / 技能推荐列表2 / 第 4 行

NID：jwzVQMBIuj；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A4 | 类型 | 学生通用技能 |
| B4 | 来源 | 第三方拉取 |
| C4 | 技能 | find-skills |
| D4 | 技能nid | jwzVQMBIuj |
| E4 | 是否必须推送 | 必须 |

<a id="entry-421aeb73c87712e1c7ec"></a>
### entry-421aeb73c87712e1c7ec · skill-creator

技能  - 专家整理.xlsx / 技能推荐列表2 / 第 5 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A5 | 类型 | 学生通用技能 |
| B5 | 来源 | 第三方拉取 |
| C5 | 技能 | skill-creator |
| D5 | 技能nid | 待补 |
| E5 | 是否必须推送 | 必须 |

<a id="entry-dfa076c9e28dd72b9d91"></a>
### entry-dfa076c9e28dd72b9d91 · rank

技能  - 专家整理.xlsx / 技能推荐列表2 / 第 6 行

NID：pROAU0vQvX；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A6 | 类型 | 学生推荐（随机3-4个） |
| B6 | 来源 | 第三方拉取 |
| C6 | 技能 | rank |
| D6 | 技能nid | pROAU0vQvX |
| E6 | 是否必须推送 | 否 |

<a id="entry-c9c3d6ce0493a556c3cc"></a>
### entry-c9c3d6ce0493a556c3cc · book

技能  - 专家整理.xlsx / 技能推荐列表2 / 第 7 行

NID：vHGv7DMv6T；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A7 | 类型 | 学生推荐（随机3-4个） |
| B7 | 来源 | 第三方拉取 |
| C7 | 技能 | book |
| D7 | 技能nid | vHGv7DMv6T |
| E7 | 是否必须推送 | 否 |

<a id="entry-eea36744d404366d85c2"></a>
### entry-eea36744d404366d85c2 · think

技能  - 专家整理.xlsx / 技能推荐列表2 / 第 8 行

NID：mxtNqLtCS7；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A8 | 类型 | 学生推荐（随机3-4个） |
| B8 | 来源 | 第三方拉取 |
| C8 | 技能 | think |
| D8 | 技能nid | mxtNqLtCS7 |
| E8 | 是否必须推送 | 否 |

<a id="entry-f61f5595c41331c12717"></a>
### entry-f61f5595c41331c12717 · word

技能  - 专家整理.xlsx / 技能推荐列表2 / 第 9 行

NID：Fph4Q3Ao19；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A9 | 类型 | 学生推荐（随机3-4个） |
| B9 | 来源 | 第三方拉取 |
| C9 | 技能 | word |
| D9 | 技能nid | Fph4Q3Ao19 |
| E9 | 是否必须推送 | 否 |

<a id="entry-7f22917570e2d3b6f5aa"></a>
### entry-7f22917570e2d3b6f5aa · baoyu-infographic

技能  - 专家整理.xlsx / 技能推荐列表2 / 第 10 行

NID：umw5xMPtgY；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A10 | 类型 | 学生推荐（随机3-4个） |
| B10 | 来源 | 第三方拉取 |
| C10 | 技能 | baoyu-infographic |
| D10 | 技能nid | umw5xMPtgY |
| E10 | 是否必须推送 | 否 |

<a id="entry-062dd82203dbf753c57d"></a>
### entry-062dd82203dbf753c57d · explain-like-socrates

技能  - 专家整理.xlsx / 技能推荐列表2 / 第 11 行

NID：SRpzIG2wNw；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A11 | 类型 | 学生推荐（随机3-4个） |
| B11 | 来源 | 第三方拉取 |
| C11 | 技能 | explain-like-socrates |
| D11 | 技能nid | SRpzIG2wNw |
| E11 | 是否必须推送 | 否 |

<a id="entry-b0b7d910db3a2424c836"></a>
### entry-b0b7d910db3a2424c836 · math-intuition-builder

技能  - 专家整理.xlsx / 技能推荐列表2 / 第 12 行

NID：2JDf8tyead；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A12 | 类型 | 学生推荐（随机3-4个） |
| B12 | 来源 | 第三方拉取 |
| C12 | 技能 | math-intuition-builder |
| D12 | 技能nid | 2JDf8tyead |
| E12 | 是否必须推送 | 否 |

<a id="entry-415d6a36e51f32514d1c"></a>
### entry-415d6a36e51f32514d1c · statistical-analysis

技能  - 专家整理.xlsx / 技能推荐列表2 / 第 13 行

NID：PQG3F99qxM；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A13 | 类型 | 学生推荐（随机3-4个） |
| B13 | 来源 | 第三方拉取 |
| C13 | 技能 | statistical-analysis |
| D13 | 技能nid | PQG3F99qxM |
| E13 | 是否必须推送 | 否 |

<a id="entry-5fafffd2fe12e7fca657"></a>
### entry-5fafffd2fe12e7fca657 · meeting-skill

技能  - 专家整理.xlsx / 业务-专家 / 第 7 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A7 | 标配 | 是 |
| B7 | 专家名称 | 会议专员 |
| C7 | 平台功能 | 会议 |
| D7 | 附属技能 | meeting-skill |
| E7 | 技能解释 | 会议全流程：创建会议、查询会议列表（Markdown展示）、取消会议、查询会议纪要/总结 |
| F7 | 状态 | 确认 |
| G7 | 触发场景 | 当用户在“会议”场景中需要创建、查询或取消会议，或查询会议纪要与总结时触发。 |
| H7 | 未命名列 H | k7dlkkkioO |

<a id="entry-5718531eacda6ff2fbf9"></a>
### entry-5718531eacda6ff2fbf9 · polymas-agent-readme

技能  - 专家整理.xlsx / 业务-专家 / 第 8 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A8 | 标配 | 是 |
| B8 | 专家名称 | 基础工具 |
| C8 | 平台功能 | 基础 |
| D8 | 附属技能 | polymas-agent-readme |
| E8 | 技能解释 | 展示平台8大模块、34项核心能力及典型问法；引导用户用自然语言描述需求，不执行业务操作 |
| F8 | 状态 | 合在一起 |
| G8 | 触发场景 | 当用户在“基础”场景中需要了解平台模块、核心能力或典型使用方式时触发。 |
| H8 | 未命名列 H | BHPnyKh2QN |

<a id="entry-df0bc64e58c3d8a7b1c9"></a>
### entry-df0bc64e58c3d8a7b1c9 · polymas-page-navigation

技能  - 专家整理.xlsx / 业务-专家 / 第 9 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A9 | 标配 | 是 |
| B9 | 专家名称 | 基础工具 |
| C9 | 平台功能 | 基础 |
| D9 | 附属技能 | polymas-page-navigation |
| E9 | 技能解释 | 页面导航指引：用户想做某操作但需在页面完成时，返回对应页面链接+一句话操作指引 |
| G9 | 触发场景 | 当用户在“基础”场景中需要查找某项平台操作的页面入口与操作路径时触发。 |
| H（合并继承自 H8；H8:H10） | 原值见锚点 | BHPnyKh2QN |
| F（合并继承自 F8；F8:F9） | 原值见锚点 | 合在一起 |

<a id="entry-00dd1a66aedec0399d81"></a>
### entry-00dd1a66aedec0399d81 · polymas-tool-skills

技能  - 专家整理.xlsx / 业务-专家 / 第 10 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A10 | 标配 | 是 |
| B10 | 专家名称 | 基础工具 |
| C10 | 平台功能 | 基础 |
| D10 | 附属技能 | polymas-tool-skills |
| E10 | 技能解释 | 仅用于联网搜索互联网公开内容，返回标题、描述、URL、封面、平台名称、相似度、发布时间等信息。纯搜索，不做任何内容操作。 |
| F10 | 状态 | 确认  -  换个名字 |
| G10 | 触发场景 | 当用户在“基础”场景中需要联网搜索互联网公开内容时触发。 |
| H（合并继承自 H8；H8:H10） | 原值见锚点 | BHPnyKh2QN |

<a id="entry-5d140bbd72c4af643731"></a>
### entry-5d140bbd72c4af643731 · polymas-course-obe-skills

技能  - 专家整理.xlsx / 业务-专家 / 第 11 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A11 | 标配 | 是 |
| B11 | 专家名称 | 教学活动专员 |
| C11 | 平台功能 | OBE管理 |
| D11 | 附属技能 | polymas-course-obe-skills |
| E11 | 技能解释 | 查询课程OBE达成度，包括课程整体平均达成度、各课程目标平均达成度及各班级达成度 |
| F11 | 状态 | 确认 |
| G11 | 触发场景 | 当用户在“OBE管理”场景中需要查询OBE达成度，或识别、保存OBE目标时触发。 |

<a id="entry-a83f3a82a2e0165bad0e"></a>
### entry-a83f3a82a2e0165bad0e · polymas-teacher-score-skills

技能  - 专家整理.xlsx / 业务-专家 / 第 12 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A12 | 标配 | 是 |
| B12 | 专家名称 | 教学活动专员 |
| C12 | 平台功能 | 成绩管理 |
| D12 | 附属技能 | polymas-teacher-score-skills |
| E12 | 技能解释 | 教师多维成绩查询：总成绩 / 考勤 / 平时 / 作业 / 考试 / 自定义考核项，支持个人与班级分布两种视角 |
| F12 | 状态 | 确认 - 需要能设置 |
| G12 | 触发场景 | 当用户在“成绩管理”场景中需要查询总成绩、考勤、作业、考试或自定义考核项时触发。 |

<a id="entry-8c35278939cc078cdb0a"></a>
### entry-8c35278939cc078cdb0a · 暂无匹配技能

技能  - 专家整理.xlsx / 业务-专家 / 第 13 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A13 | 标配 | 是 |
| B13 | 专家名称 | 教学活动专员 |
| C13 | 平台功能 | 代办 |
| D13 | 附属技能 | 暂无匹配技能 |
| G13 | 触发场景 | 当前没有匹配技能，不触发。 |

<a id="entry-0937759bb38a4e6410d4"></a>
### entry-0937759bb38a4e6410d4 · polymas-teacher-homework-skills

技能  - 专家整理.xlsx / 业务-专家 / 第 14 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A14 | 标配 | 是 |
| B14 | 专家名称 | 教学活动专员 |
| C14 | 平台功能 | 教学活动（作业、考试、话题讨论、通知） |
| D14 | 附属技能 | polymas-teacher-homework-skills |
| E14 | 技能解释 | 查询教师在课程下的作业信息，包括作业详细信息、作业关联班级信息、班级作业结束时间、完成率统计等数据 |
| F14 | 状态 | 确认 |
| G14 | 触发场景 | 当用户在“教学活动（作业、考试、话题讨论、通知）”场景中需要查询课程作业详情、关联班级、截止时间或完成率时触发。 |

<a id="entry-10b49cd03ee62eebe209"></a>
### entry-10b49cd03ee62eebe209 · polymas-teacher-homework-detail-skills

技能  - 专家整理.xlsx / 业务-专家 / 第 15 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A15 | 标配 | 是 |
| B15 | 专家名称 | 教学活动专员 |
| C15 | 平台功能 | 教学活动（作业、考试、话题讨论、通知） |
| D15 | 附属技能 | polymas-teacher-homework-detail-skills |
| E15 | 技能解释 | 教师查看考试作业详情与学情分析，包括考试基本信息、成绩统计、分段人数及各班级对比数据 |
| F15 | 状态 | 确认 |
| G15 | 触发场景 | 当用户在“教学活动（作业、考试、话题讨论、通知）”场景中需要查看考试或作业详情、成绩统计、分段人数或班级对比时触发。 |

<a id="entry-dce90b0424ed4e6ea404"></a>
### entry-dce90b0424ed4e6ea404 · polymas-teacher-exam-skills

技能  - 专家整理.xlsx / 业务-专家 / 第 16 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A16 | 标配 | 是 |
| B16 | 专家名称 | 教学活动专员 |
| C16 | 平台功能 | 教学活动（作业、考试、话题讨论、通知） |
| D16 | 附属技能 | polymas-teacher-exam-skills |
| E16 | 技能解释 | 查询教师在课程下的考试信息，包括考试详细信息、关联班级安排、考试开始/结束时间、防作弊配置及组卷信息等数据 |
| F16 | 状态 | 确认 |
| G16 | 触发场景 | 当用户在“教学活动（作业、考试、话题讨论、通知）”场景中需要查询课程考试详情、关联班级、考试时间、防作弊或组卷信息时触发。 |

<a id="entry-c808d94cd4cedade8830"></a>
### entry-c808d94cd4cedade8830 · polymas-teacher-activity-skills

技能  - 专家整理.xlsx / 业务-专家 / 第 17 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A17 | 标配 | 是 |
| B17 | 专家名称 | 教学活动专员 |
| C17 | 平台功能 | 教学活动（作业、考试、话题讨论、通知） |
| D17 | 附属技能 | polymas-teacher-activity-skills |
| E17 | 技能解释 | 教师向课程下班级或全部学生发布一条通知，支持指定标题、内容、附件以及目标班级 |
| F17 | 状态 | 确认 |
| G17 | 触发场景 | 当用户在“教学活动（作业、考试、话题讨论、通知）”场景中需要向课程班级或全体学生发布通知或教学活动消息时触发。 |

<a id="entry-9fe7b3e35a490a8b9d80"></a>
### entry-9fe7b3e35a490a8b9d80 · polymas-teacher-class-group-assistant

技能  - 专家整理.xlsx / 业务-专家 / 第 18 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A18 | 标配 | 是 |
| B18 | 专家名称 | 教学活动专员 |
| C18 | 平台功能 | 教学活动（作业、考试、话题讨论、通知） |
| D18 | 附属技能 | polymas-teacher-class-group-assistant |
| E18 | 技能解释 | 向班级群发送消息通知 |
| G18 | 触发场景 | 当用户在“教学活动（作业、考试、话题讨论、通知）”场景中需要向班级群发送消息或通知时触发。 |

<a id="entry-5ba873983a9d028ea099"></a>
### entry-5ba873983a9d028ea099 · polymas-get-student-course-homework

技能  - 专家整理.xlsx / 业务-专家 / 第 19 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A19 | 标配 | 是 |
| B19 | 专家名称 | 教学活动专员 |
| C19 | 平台功能 | 教学活动（作业、考试、话题讨论、通知） |
| D19 | 附属技能 | polymas-get-student-course-homework |
| E19 | 技能解释 | 查询学生在课程下的所有作业信息，包括作业详细信息、作业关联班级信息、班级作业结束时间、完成率统计等数据。 |
| G19 | 触发场景 | 当用户在“教学活动（作业、考试、话题讨论、通知）”场景中需要查询学生在课程下的作业详情、截止时间或完成情况时触发。 |

<a id="entry-828520b42dc96c5ee0b8"></a>
### entry-828520b42dc96c5ee0b8 · polymas-teacher-work-calendar

技能  - 专家整理.xlsx / 业务-专家 / 第 20 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A20 | 标配 | 是 |
| B20 | 专家名称 | 教学活动专员 |
| C20 | 平台功能 | 教学日历 |
| D20 | 附属技能 | polymas-teacher-work-calendar |
| E20 | 技能解释 | 工作日历查询：查教学日程（课程/会议/作业截止/考试/AI提醒） |
| F20 | 状态 | 确认 |
| G20 | 触发场景 | 当用户在“教学日历”场景中需要查询课程、会议、作业截止、考试或AI提醒等日程时触发。 |

<a id="entry-48fa3f6d141978413d3d"></a>
### entry-48fa3f6d141978413d3d · polymas-teacher-class-group-skills

技能  - 专家整理.xlsx / 业务-专家 / 第 21 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A21 | 标配 | 是 |
| B21 | 专家名称 | 教学活动专员 |
| C21 | 平台功能 | 小组教学 |
| D21 | 附属技能 | polymas-teacher-class-group-skills |
| E21 | 技能解释 | 查询课程下的分组方案列表、分组方案详情、组内学生名单及未进组学生 |
| F21 | 状态 | 确认 |
| G21 | 触发场景 | 当用户在“小组教学”场景中需要查询分组方案、组内学生或未进组学生时触发。 |

<a id="entry-334c5eef14c662b784c4"></a>
### entry-334c5eef14c662b784c4 · polymas-course-comprehensive-skills

技能  - 专家整理.xlsx / 业务-专家 / 第 22 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A22 | 标配 | 是 |
| B22 | 专家名称 | 学情分析专员 |
| C22 | 平台功能 | 学情分析 |
| D22 | 附属技能 | polymas-course-comprehensive-skills |
| E22 | 技能解释 | 教师按课程、班级查看指定学生的学情分析报告，包括作业完成情况、成绩趋势、学习活跃度等数据 |
| F22 | 状态 | 确认 |
| G22 | 触发场景 | 当用户在“学情分析”场景中需要查看学生、班级、课程或知识点维度的综合学情分析时触发。 |

<a id="entry-854a190a405e67a29f09"></a>
### entry-854a190a405e67a29f09 · polymas-teacher-learning-analytics-skills

技能  - 专家整理.xlsx / 业务-专家 / 第 23 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A23 | 标配 | 是 |
| C23 | 平台功能 | 学情分析 |
| D23 | 附属技能 | polymas-teacher-learning-analytics-skills |
| E23 | 技能解释 | 将单个学生的作业完成率、考试成绩、课堂互动次数整合到一起，给出综合视图 |
| F23 | 状态 | 确认 |
| G23 | 触发场景 | 当用户在“学情分析”场景中需要汇总单个学生的作业、考试与课堂互动数据时触发。 |
| B（合并继承自 B22；B22:B27） | 原值见锚点 | 学情分析专员 |

<a id="entry-827e6f2db31a168d9750"></a>
### entry-827e6f2db31a168d9750 · polymas-teacher-teaching-observation-skills

技能  - 专家整理.xlsx / 业务-专家 / 第 24 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A24 | 标配 | 是 |
| C24 | 平台功能 | 学情分析 |
| D24 | 附属技能 | polymas-teacher-teaching-observation-skills |
| E24 | 技能解释 | 查询学习进度：学习资源完成率、必学完成率分组分布 |
| F24 | 状态 | 确认 |
| G24 | 触发场景 | 当用户在“学情分析”场景中需要查询学习资源完成率、必学完成率或学习进度分布时触发。 |
| B（合并继承自 B22；B22:B27） | 原值见锚点 | 学情分析专员 |

<a id="entry-acde3a2087b6c8a23a91"></a>
### entry-acde3a2087b6c8a23a91 · polymas-teacher-lession-analysis

技能  - 专家整理.xlsx / 业务-专家 / 第 25 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A25 | 标配 | 是 |
| C25 | 平台功能 | 学情分析 |
| D25 | 附属技能 | polymas-teacher-lession-analysis |
| E25 | 技能解释 | 按课程、课堂查看学生课堂表现：成绩得分、互动参与、弹幕次数、在线时长；支持分页 |
| F25 | 状态 | 确认 - 没有i |
| G25 | 触发场景 | 当用户在“学情分析”场景中需要查看学生课堂得分、互动、弹幕次数或在线时长时触发。 |
| B（合并继承自 B22；B22:B27） | 原值见锚点 | 学情分析专员 |

<a id="entry-0f74ce99b47e5b9b0a34"></a>
### entry-0f74ce99b47e5b9b0a34 · polymas-teacher-classroom-report-skills

技能  - 专家整理.xlsx / 业务-专家 / 第 26 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A26 | 标配 | 是 |
| C26 | 平台功能 | 学情分析 |
| D26 | 附属技能 | polymas-teacher-classroom-report-skills |
| E26 | 技能解释 | 课堂核心数据分析：查询课堂基本数据统计与授课方式分布 |
| F26 | 状态 | 确认 |
| G26 | 触发场景 | 当用户在“学情分析”场景中需要查看课堂基本统计、授课方式分布或课堂核心数据时触发。 |
| B（合并继承自 B22；B22:B27） | 原值见锚点 | 学情分析专员 |

<a id="entry-d7f38d4e8a735a9c3d9f"></a>
### entry-d7f38d4e8a735a9c3d9f · statistical-analysis

技能  - 专家整理.xlsx / 业务-专家 / 第 27 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A27 | 标配 | 是 |
| C27 | 平台功能 | 学情分析 |
| D27 | 附属技能 | statistical-analysis |
| E27 | 技能解释 | Apply statistical methods including descriptive stats, trend analysis, outlier detection, and hypothesis testing. Use when analyzing distributions, testing for significance, detecting anomalies, computing correlations, or interpreting statistical results. |
| F27 | 状态 | 确认 |
| G27 | 触发场景 | 当用户在“学情分析”场景中需要进行描述统计、趋势分析、异常检测或假设检验时触发。 |
| B（合并继承自 B22；B22:B27） | 原值见锚点 | 学情分析专员 |

<a id="entry-440a8859566fce64a33b"></a>
### entry-440a8859566fce64a33b · polymas-teacher-resource-skills

技能  - 专家整理.xlsx / 业务-专家 / 第 28 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A28 | 标配 | 是 |
| B28 | 专家名称 | 教学活动专员 |
| C28 | 平台功能 | 学习资源（普通、闯关、复习模式） |
| D28 | 附属技能 | polymas-teacher-resource-skills |
| E28 | 技能解释 | 仅用于查询/搜索教师知识库内容，包括标题、资源类型、资源封面、资源链接、资源预览图标、资源名称、资源摘要。不支持新增、编辑、删除、上传、下载等操作。 |
| F28 | 状态 | 不确认<br>备注：这个资源是指学习资源还是知识库资源？ |
| G28 | 触发场景 | 当用户在“学习资源（普通、闯关、复习模式）”场景中需要查询或搜索教师知识库中的资源内容时触发。 |

<a id="entry-e1279fa61eae2778dd58"></a>
### entry-e1279fa61eae2778dd58 · polymas-teacher-teaching-observation-skills

技能  - 专家整理.xlsx / 业务-专家 / 第 29 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A29 | 标配 | 是 |
| B29 | 专家名称 | 教学活动专员 |
| C29 | 平台功能 | 学习资源（普通、闯关、复习模式） |
| D29 | 附属技能 | polymas-teacher-teaching-observation-skills |
| E29 | 技能解释 | 查询学习进度：学习资源完成率、必学完成率分组分布 |
| F29 | 状态 | 确认 |
| G29 | 触发场景 | 当用户在“学习资源（普通、闯关、复习模式）”场景中需要查询学习资源完成率、必学完成率或学习进度分布时触发。 |

<a id="entry-3152f3fcc47040c88da2"></a>
### entry-3152f3fcc47040c88da2 · 暂无匹配技能

技能  - 专家整理.xlsx / 业务-专家 / 第 30 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A30 | 标配 | 是 |
| B30 | 专家名称 | 教学活动专员 |
| C30 | 平台功能 | 自定义学习 |
| D30 | 附属技能 | 暂无匹配技能 |
| G30 | 触发场景 | 当前没有匹配技能，不触发。 |

<a id="entry-ca7d6625e3d7e018b793"></a>
### entry-ca7d6625e3d7e018b793 · 暂无匹配技能

技能  - 专家整理.xlsx / 业务-专家 / 第 31 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B31 | 专家名称 | 课中智能体 |
| C31 | 平台功能 | 教室授课 |
| D31 | 附属技能 | 暂无匹配技能 |
| G31 | 触发场景 | 当前没有匹配技能，不触发。 |

<a id="entry-970ec4981342f6f98f6d"></a>
### entry-970ec4981342f6f98f6d · polymas-teacher-classroom-report-skills

技能  - 专家整理.xlsx / 业务-专家 / 第 32 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B32 | 专家名称 | 课中智能体 |
| C32 | 平台功能 | 课堂报告、回放 |
| D32 | 附属技能 | polymas-teacher-classroom-report-skills |
| E32 | 技能解释 | 课堂核心数据分析：查询课堂基本数据统计与授课方式分布 |
| F32 | 状态 | 报告回放智能体 |
| G32 | 触发场景 | 当用户在“课堂报告、回放”场景中需要查看课堂基本统计、授课方式分布或课堂核心数据时触发。 |

<a id="entry-62214bb50c4087027a64"></a>
### entry-62214bb50c4087027a64 · polymas-teacher-lession-analysis

技能  - 专家整理.xlsx / 业务-专家 / 第 33 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B33 | 专家名称 | 课中智能体 |
| C33 | 平台功能 | 课堂报告、回放 |
| D33 | 附属技能 | polymas-teacher-lession-analysis |
| E33 | 技能解释 | 按课程、课堂查看学生课堂表现：成绩得分、互动参与、弹幕次数、在线时长；支持分页 |
| G33 | 触发场景 | 当用户在“课堂报告、回放”场景中需要查看学生课堂得分、互动、弹幕次数或在线时长时触发。 |
| F（合并继承自 F32；F32:F33） | 原值见锚点 | 报告回放智能体 |

<a id="entry-31f9d7d0282aab992e99"></a>
### entry-31f9d7d0282aab992e99 · 暂无匹配技能

技能  - 专家整理.xlsx / 业务-专家 / 第 34 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B34 | 专家名称 | 课中智能体 |
| C34 | 平台功能 | 课堂互动 |
| D34 | 附属技能 | 暂无匹配技能 |
| G34 | 触发场景 | 当前没有匹配技能，不触发。 |

<a id="entry-2ad1d56f25a0806600a0"></a>
### entry-2ad1d56f25a0806600a0 · 暂无匹配技能

技能  - 专家整理.xlsx / 业务-专家 / 第 35 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B35 | 专家名称 | 课中智能体 |
| C35 | 平台功能 | 直播授课 |
| D35 | 附属技能 | 暂无匹配技能 |
| G35 | 触发场景 | 当前没有匹配技能，不触发。 |

<a id="entry-b391b1ffcde0892bca09"></a>
### entry-b391b1ffcde0892bca09 · polymas-teacher-course-skills

技能  - 专家整理.xlsx / 业务-专家 / 第 36 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A36 | 标配 | 是 |
| B36 | 专家名称 | 学课管理专员 |
| C36 | 平台功能 | 课程管理 |
| D36 | 附属技能 | polymas-teacher-course-skills |
| E36 | 技能解释 | 老师创建课程，支持邀请码建课和AI智课建课两种方式 |
| F36 | 状态 | 确认 |
| G36 | 触发场景 | 当用户在“课程管理”场景中需要创建课程，包括邀请码建课或AI智课建课时触发。 |

<a id="entry-e74272f5b613edde7c66"></a>
### entry-e74272f5b613edde7c66 · polymas-course-list-skills

技能  - 专家整理.xlsx / 业务-专家 / 第 37 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A37 | 标配 | 是 |
| B37 | 专家名称 | 学课管理专员 |
| C37 | 平台功能 | 课程管理 |
| D37 | 附属技能 | polymas-course-list-skills |
| E37 | 技能解释 | 查询课程列表信息，包括当前学期课程、归档课程和共享课列表，共享课仅返回state==3的课程 |
| F37 | 状态 | 确认 |
| G37 | 触发场景 | 当用户在“课程管理”场景中需要查询当前学期、归档或共享课程列表时触发。 |

<a id="entry-9c9b7d783e3d68db8610"></a>
### entry-9c9b7d783e3d68db8610 · polymas-course-overview-skills

技能  - 专家整理.xlsx / 业务-专家 / 第 38 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A38 | 标配 | 是 |
| B38 | 专家名称 | 学课管理专员 |
| C38 | 平台功能 | 课程管理 |
| D38 | 附属技能 | polymas-course-overview-skills |
| E38 | 技能解释 | 查询课程概况信息，包括教学计划状态、单元/章节数量、课代表对话次数、AI知识库资源数量及教学活动列表 |
| F38 | 状态 | 确认 |
| G38 | 触发场景 | 当用户在“课程管理”场景中需要查询课程概况、教学计划状态、单元数量、资源或活动概览时触发。 |

<a id="entry-ab5a9bafb488dda05e13"></a>
### entry-ab5a9bafb488dda05e13 · polymas-query-teaching-unit

技能  - 专家整理.xlsx / 业务-专家 / 第 39 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A39 | 标配 | 是 |
| B39 | 专家名称 | 学课管理专员 |
| C39 | 平台功能 | 课程管理 |
| D39 | 附属技能 | polymas-query-teaching-unit |
| E39 | 技能解释 | 查询指定课程的教学单元、主题、知识点及知识点关系的层级结构；仅可查当前用户有权访问的课程 |
| F39 | 状态 | 确认 |
| G39 | 触发场景 | 当用户在“课程管理”场景中需要查询课程的教学单元、主题、知识点或知识点关系时触发。 |

<a id="entry-4d5dd3b1fd7165880575"></a>
### entry-4d5dd3b1fd7165880575 · polymas-teacher-teaching-plan

技能  - 专家整理.xlsx / 业务-专家 / 第 40 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A40 | 标配 | 是 |
| B40 | 专家名称 | 学课管理专员 |
| C40 | 平台功能 | 课程管理 |
| D40 | 附属技能 | polymas-teacher-teaching-plan |
| E40 | 技能解释 | 教学计划查询：查询单元/主题(小节)/知识点结构及关联的作业与考试活动 |
| F40 | 状态 | 确认 |
| G40 | 触发场景 | 当用户在“课程管理”场景中需要查询教学单元、知识点及其关联的作业或考试活动时触发。 |

<a id="entry-4a71d91a70598bca7165"></a>
### entry-4a71d91a70598bca7165 · polymas-teacher-class-skills

技能  - 专家整理.xlsx / 业务-专家 / 第 41 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A41 | 标配 | 是 |
| B41 | 专家名称 | 学课管理专员 |
| C41 | 平台功能 | 课程管理 |
| D41 | 附属技能 | polymas-teacher-class-skills |
| E41 | 技能解释 | 教师在课程下创建班级，支持按课程名称定位课程、输入班级名称后完成创建，创建后可按需手动添加学生并支持循环添加 |
| F41 | 状态 | 确认 |
| G41 | 触发场景 | 当用户在“课程管理”场景中需要在课程下创建班级时触发。 |

<a id="entry-2a8343b34677fca1c00b"></a>
### entry-2a8343b34677fca1c00b · polymas-teacher-class-student-skills

技能  - 专家整理.xlsx / 业务-专家 / 第 42 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A42 | 标配 | 是 |
| B42 | 专家名称 | 学课管理专员 |
| C42 | 平台功能 | 课程管理 |
| D42 | 附属技能 | polymas-teacher-class-student-skills |
| E42 | 技能解释 | 按入班状态查询课程/班级下的学生信息，支持已入班、待审核、待激活三种状态路由，返回学生名单、标签、院系等数据 |
| F42 | 状态 | 确认 |
| G42 | 触发场景 | 当用户在“课程管理”场景中需要查询已入班、待审核或待激活的班级学生时触发。 |

<a id="entry-429380e074b69d66b445"></a>
### entry-429380e074b69d66b445 · polymas-teacher-class-group-skills

技能  - 专家整理.xlsx / 业务-专家 / 第 43 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A43 | 标配 | 是 |
| B43 | 专家名称 | 学课管理专员 |
| C43 | 平台功能 | 课程管理 |
| D43 | 附属技能 | polymas-teacher-class-group-skills |
| E43 | 技能解释 | 查询课程下的分组方案列表、分组方案详情、组内学生名单及未进组学生 |
| F43 | 状态 | 确认 |
| G43 | 触发场景 | 当用户在“课程管理”场景中需要查询分组方案、组内学生或未进组学生时触发。 |

<a id="entry-d00a24d148b470a58b39"></a>
### entry-d00a24d148b470a58b39 · polymas-student-basic-skills

技能  - 专家整理.xlsx / 业务-专家 / 第 44 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A44 | 标配 | 是 |
| B44 | 专家名称 | 学课管理专员 |
| C44 | 平台功能 | 课程管理 |
| D44 | 附属技能 | polymas-student-basic-skills |
| E44 | 技能解释 | 学生基础技能：根据用户需求智能选择课程搜索和作业查询功能 |
| G44 | 触发场景 | 当用户在“课程管理”场景中需要查询学生的课程或课程作业时触发。 |

<a id="entry-14d17b41291a75ab4aa3"></a>
### entry-14d17b41291a75ab4aa3 · 暂无匹配技能

技能  - 专家整理.xlsx / 业务-专家 / 第 47 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B47 | 专家名称 | 暂无 |
| C47 | 平台功能 | 教学研讨 |
| D47 | 附属技能 | 暂无匹配技能 |
| F47 | 状态 | 无技能 |
| G47 | 触发场景 | 当前没有匹配技能，不触发。 |

<a id="entry-68dd6703f34c3860e88b"></a>
### entry-68dd6703f34c3860e88b · 暂无匹配技能

技能  - 专家整理.xlsx / 业务-专家 / 第 51 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B51 | 专家名称 | 暂无 |
| C51 | 平台功能 | 能力训练（黄卓） |
| D51 | 附属技能 | 暂无匹配技能 |
| G51 | 触发场景 | 当前没有匹配技能，不触发。 |

<a id="entry-7433e4b61ffd73b76831"></a>
### entry-7433e4b61ffd73b76831 · 暂无匹配技能

技能  - 专家整理.xlsx / 业务-专家 / 第 52 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B52 | 专家名称 | 暂无 |
| C52 | 平台功能 | 协作空间（灵美） |
| D52 | 附属技能 | 暂无匹配技能 |
| G52 | 触发场景 | 当前没有匹配技能，不触发。 |

<a id="entry-0740180b3fef117cebde"></a>
### entry-0740180b3fef117cebde · polymas-teacher-work-calendar

技能  - 专家整理.xlsx / 业务-专家 / 第 53 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B53 | 专家名称 | 暂无 |
| C53 | 平台功能 | 学习任务 |
| D53 | 附属技能 | polymas-teacher-work-calendar |
| E53 | 技能解释 | 工作日历查询：查教学日程（课程/会议/作业截止/考试/AI提醒） |
| G53 | 触发场景 | 当用户在“学习任务”场景中需要查询课程、会议、作业截止、考试或AI提醒等日程时触发。 |

<a id="entry-aec4a2a07ffe49a47ba0"></a>
### entry-aec4a2a07ffe49a47ba0 · polymas-teacher-activity-skills

技能  - 专家整理.xlsx / 业务-专家 / 第 54 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B54 | 专家名称 | 暂无 |
| C54 | 平台功能 | 学习任务 |
| D54 | 附属技能 | polymas-teacher-activity-skills |
| E54 | 技能解释 | 教师向课程下班级或全部学生发布一条通知，支持指定标题、内容、附件以及目标班级 |
| G54 | 触发场景 | 当用户在“学习任务”场景中需要向课程班级或全体学生发布通知或教学活动消息时触发。 |

<a id="entry-98150564d4dd630dac99"></a>
### entry-98150564d4dd630dac99 · polymas-teacher-homework-skills

技能  - 专家整理.xlsx / 业务-专家 / 第 55 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B55 | 专家名称 | 暂无 |
| C55 | 平台功能 | 学习任务 |
| D55 | 附属技能 | polymas-teacher-homework-skills |
| E55 | 技能解释 | 查询教师在课程下的作业信息，包括作业详细信息、作业关联班级信息、班级作业结束时间、完成率统计等数据 |
| G55 | 触发场景 | 当用户在“学习任务”场景中需要查询课程作业详情、关联班级、截止时间或完成率时触发。 |

<a id="entry-4d7dfa0ffbdac78fe418"></a>
### entry-4d7dfa0ffbdac78fe418 · polymas-teacher-exam-skills

技能  - 专家整理.xlsx / 业务-专家 / 第 56 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B56 | 专家名称 | 暂无 |
| C56 | 平台功能 | 学习任务 |
| D56 | 附属技能 | polymas-teacher-exam-skills |
| E56 | 技能解释 | 查询教师在课程下的考试信息，包括考试详细信息、关联班级安排、考试开始/结束时间、防作弊配置及组卷信息等数据 |
| G56 | 触发场景 | 当用户在“学习任务”场景中需要查询课程考试详情、关联班级、考试时间、防作弊或组卷信息时触发。 |

<a id="entry-279be5e7f6dd1a5a0077"></a>
### entry-279be5e7f6dd1a5a0077 · 暂无匹配技能

技能  - 专家整理.xlsx / 业务-专家 / 第 58 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B58 | 专家名称 | 暂无 |
| C58 | 平台功能 | 智能体对话 |
| D58 | 附属技能 | 暂无匹配技能 |
| G58 | 触发场景 | 当前没有匹配技能，不触发。 |

<a id="entry-811e6a49bde9474759ab"></a>
### entry-811e6a49bde9474759ab · polymas-teacher-agent-create

技能  - 专家整理.xlsx / 业务-专家 / 第 59 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B59 | 专家名称 | 暂无 |
| C59 | 平台功能 | 智能体教学（不清楚） |
| D59 | 附属技能 | polymas-teacher-agent-create |
| E59 | 技能解释 | 创建课堂智能体：所有接口的参数定义与调用示例 |
| F59 | 状态 | 确认 |
| G59 | 触发场景 | 当用户在“智能体教学（不清楚）”场景中需要创建课堂智能体并准备所需参数时触发。 |

<a id="entry-bd76346ff5e1abba0d93"></a>
### entry-bd76346ff5e1abba0d93 · polymas-teacher-agent-teaching-gen

技能  - 专家整理.xlsx / 业务-专家 / 第 60 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B60 | 专家名称 | 暂无 |
| C60 | 平台功能 | 智能体教学（不清楚） |
| D60 | 附属技能 | polymas-teacher-agent-teaching-gen |
| E60 | 技能解释 | 生成单个智能体课堂：抽取信息 → 定位课程/学期 → 匹配数字人 → 创建课堂 → 发布活动 → 轮询生成状态 |
| F60 | 状态 | 确认 |
| G60 | 触发场景 | 当用户在“智能体教学（不清楚）”场景中需要生成、创建并发布单个智能体课堂时触发。 |

<a id="entry-f985d4b7ff4df5869381"></a>
### entry-f985d4b7ff4df5869381 · polymas-teacher-agent-create

技能  - 专家整理.xlsx / 业务-专家 / 第 61 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B61 | 专家名称 | 智能体课程专员 |
| C61 | 平台功能 | 智能体授课（不清楚） |
| D61 | 附属技能 | polymas-teacher-agent-create |
| E61 | 技能解释 | 创建课堂智能体：所有接口的参数定义与调用示例 |
| F61 | 状态 | 确认 |
| G61 | 触发场景 | 当用户在“智能体授课（不清楚）”场景中需要创建课堂智能体并准备所需参数时触发。 |

<a id="entry-4c33bd8682f956743c3e"></a>
### entry-4c33bd8682f956743c3e · polymas-teacher-agent-teaching-gen

技能  - 专家整理.xlsx / 业务-专家 / 第 62 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B62 | 专家名称 | 智能体课程专员 |
| C62 | 平台功能 | 智能体授课（不清楚） |
| D62 | 附属技能 | polymas-teacher-agent-teaching-gen |
| E62 | 技能解释 | 生成单个智能体课堂：抽取信息 → 定位课程/学期 → 匹配数字人 → 创建课堂 → 发布活动 → 轮询生成状态 |
| F62 | 状态 | 确认 |
| G62 | 触发场景 | 当用户在“智能体授课（不清楚）”场景中需要生成、创建并发布单个智能体课堂时触发。 |

<a id="entry-47d19e1b6ab874837264"></a>
### entry-47d19e1b6ab874837264 · polymas-teacher-resource-skills

技能  - 专家整理.xlsx / 业务-专家 / 第 63 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A63 | 标配 | 是 |
| B63 | 专家名称 | 资源管理专员 |
| C63 | 平台功能 | 三大资源库（个人、团队、课程） |
| D63 | 附属技能 | polymas-teacher-resource-skills |
| E63 | 技能解释 | 仅用于查询/搜索教师知识库内容，包括标题、资源类型、资源封面、资源链接、资源预览图标、资源名称、资源摘要。不支持新增、编辑、删除、上传、下载等操作。 |
| F63 | 状态 | 不确认<br>备注：这个资源是指学习资源还是知识库资源？ |
| G63 | 触发场景 | 当用户在“三大资源库（个人、团队、课程）”场景中需要查询或搜索教师知识库中的资源内容时触发。 |

<a id="entry-328901ad8b318be1ae67"></a>
### entry-328901ad8b318be1ae67 · polymas-teacher-questionbank-skills

技能  - 专家整理.xlsx / 业务-专家 / 第 64 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A64 | 标配 | 是 |
| B64 | 专家名称 | 资源管理专员 |
| C64 | 平台功能 | 题库、试卷库 |
| D64 | 附属技能 | polymas-teacher-questionbank-skills |
| E64 | 技能解释 | 查询教师的题库资源与题目信息，包括课程题库和个人题库分类、题目详情（题干、题型、选项、答案）等数据 |
| F64 | 状态 | 确认 |
| G64 | 触发场景 | 当用户在“题库、试卷库”场景中需要查询课程题库、个人题库或题目详情时触发。 |

<a id="entry-ec15f22cf47dcd0abdf6"></a>
### entry-ec15f22cf47dcd0abdf6 · polymas-teacher-questions-query

技能  - 专家整理.xlsx / 业务-专家 / 第 65 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A65 | 标配 | 是 |
| B65 | 专家名称 | 资源管理专员 |
| C65 | 平台功能 | 题库、试卷库 |
| D65 | 附属技能 | polymas-teacher-questions-query |
| E65 | 技能解释 | 教师题库查询技能：查询题库题目数量、分布、具体题目，支持按题型/难度/知识点/标签/来源等多维度筛选 |
| F65 | 状态 | 确认 |
| G65 | 触发场景 | 当用户在“题库、试卷库”场景中需要按题型、难度、知识点、标签或来源筛选题目时触发。 |

<a id="entry-1c549d2d743590da2325"></a>
### entry-1c549d2d743590da2325 · polymas-teacher-file-import-questions

技能  - 专家整理.xlsx / 业务-专家 / 第 66 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A66 | 标配 | 是 |
| B66 | 专家名称 | 资源管理专员 |
| C66 | 平台功能 | 题库、试卷库 |
| D66 | 附属技能 | polymas-teacher-file-import-questions |
| E66 | 技能解释 | 教师文件导题技能：上传试卷文件（支持PDF、DOC、DOCX、PNG、JPG、JPEG、XLS、XLSX，单文件≤500MB），AI解析提取题目，逐题确认后导入题库 |
| F66 | 状态 | 确认 |
| G66 | 触发场景 | 当用户在“题库、试卷库”场景中需要上传试卷文件、解析题目并导入题库时触发。 |

<a id="entry-e2bdf6dfbdf007c904d6"></a>
### entry-e2bdf6dfbdf007c904d6 · polymas-teacher-problem-skills

技能  - 专家整理.xlsx / 业务-专家 / 第 67 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A67 | 标配 | 是 |
| B67 | 专家名称 | 资源管理专员 |
| C67 | 平台功能 | 题库、试卷库 |
| D67 | 附属技能 | polymas-teacher-problem-skills |
| E67 | 技能解释 | 教师出题技能：根据知识点、难度、题型等要求，通过 AI 自动生成题目并保存到题库 |
| F67 | 状态 | 确认 |
| G67 | 触发场景 | 当用户在“题库、试卷库”场景中需要按知识点、难度或题型自动生成题目并保存时触发。 |

<a id="entry-63cb98651f01c7852b02"></a>
### entry-63cb98651f01c7852b02 · polymas-teacher-questionbank-skills

技能  - 专家整理.xlsx / 业务-专家 / 第 68 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A68 | 标配 | 是 |
| B68 | 专家名称 | 资源管理专员 |
| C68 | 平台功能 | 训练题库 |
| D68 | 附属技能 | polymas-teacher-questionbank-skills |
| E68 | 技能解释 | 查询教师的题库资源与题目信息，包括课程题库和个人题库分类、题目详情（题干、题型、选项、答案）等数据 |
| F68 | 状态 | 确认 |
| G68 | 触发场景 | 当用户在“训练题库”场景中需要查询课程题库、个人题库或题目详情时触发。 |

<a id="entry-5f5124ee2284c41006f3"></a>
### entry-5f5124ee2284c41006f3 · polymas-teacher-questions-query

技能  - 专家整理.xlsx / 业务-专家 / 第 69 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A69 | 标配 | 是 |
| B69 | 专家名称 | 资源管理专员 |
| C69 | 平台功能 | 训练题库 |
| D69 | 附属技能 | polymas-teacher-questions-query |
| E69 | 技能解释 | 教师题库查询技能：查询题库题目数量、分布、具体题目，支持按题型/难度/知识点/标签/来源等多维度筛选 |
| F69 | 状态 | 确认 |
| G69 | 触发场景 | 当用户在“训练题库”场景中需要按题型、难度、知识点、标签或来源筛选题目时触发。 |

<a id="entry-f705c6f112befed40c05"></a>
### entry-f705c6f112befed40c05 · polymas-teacher-file-import-questions

技能  - 专家整理.xlsx / 业务-专家 / 第 70 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A70 | 标配 | 是 |
| B70 | 专家名称 | 资源管理专员 |
| C70 | 平台功能 | 训练题库 |
| D70 | 附属技能 | polymas-teacher-file-import-questions |
| E70 | 技能解释 | 教师文件导题技能：上传试卷文件（支持PDF、DOC、DOCX、PNG、JPG、JPEG、XLS、XLSX，单文件≤500MB），AI解析提取题目，逐题确认后导入题库 |
| F70 | 状态 | 确认 |
| G70 | 触发场景 | 当用户在“训练题库”场景中需要上传试卷文件、解析题目并导入题库时触发。 |

<a id="entry-7dd4a1340936f807be2b"></a>
### entry-7dd4a1340936f807be2b · polymas-teacher-problem-skills

技能  - 专家整理.xlsx / 业务-专家 / 第 71 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A71 | 标配 | 是 |
| B71 | 专家名称 | 资源管理专员 |
| C71 | 平台功能 | 训练题库 |
| D71 | 附属技能 | polymas-teacher-problem-skills |
| E71 | 技能解释 | 教师出题技能：根据知识点、难度、题型等要求，通过 AI 自动生成题目并保存到题库 |
| F71 | 状态 | 确认 |
| G71 | 触发场景 | 当用户在“训练题库”场景中需要按知识点、难度或题型自动生成题目并保存时触发。 |

<a id="entry-62602ba16460cafbcd81"></a>
### entry-62602ba16460cafbcd81 · polymas-teacher-resource-skills

技能  - 专家整理.xlsx / 业务-专家 / 第 72 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A72 | 标配 | 是 |
| B72 | 专家名称 | 资源管理专员 |
| C72 | 平台功能 | 知识库 |
| D72 | 附属技能 | polymas-teacher-resource-skills |
| E72 | 技能解释 | 仅用于查询/搜索教师知识库内容，包括标题、资源类型、资源封面、资源链接、资源预览图标、资源名称、资源摘要。不支持新增、编辑、删除、上传、下载等操作。 |
| F72 | 状态 | 确认 |
| G72 | 触发场景 | 当用户在“知识库”场景中需要查询或搜索教师知识库中的资源内容时触发。 |

<a id="entry-f0b52d37bc2fdba5e856"></a>
### entry-f0b52d37bc2fdba5e856 · polymas-teacher-knowledge-graph

技能  - 专家整理.xlsx / 业务-专家 / 第 73 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A73 | 标配 | 是 |
| B73 | 专家名称 | 资源管理专员 |
| C73 | 平台功能 | 知识库 |
| D73 | 附属技能 | polymas-teacher-knowledge-graph |
| E73 | 技能解释 | 知识图谱查询：查三谱（知识/问题/能力）结构与统计 |
| F73 | 状态 | 确认 |
| G73 | 触发场景 | 当用户在“知识库”场景中需要查询知识图谱、问题图谱或能力图谱时触发。 |

<a id="entry-42ce99d8d1a3e6660ca7"></a>
### entry-42ce99d8d1a3e6660ca7 · lesson_plan<br>polymas-student-basic-skills

技能  - 专家整理.xlsx / 模版推荐 / 第 26 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A26 | 助教 | lesson_plan |
| B26 | 未命名列 B | polymas-student-basic-skills |
| C26 | 未命名列 C | 业务专家都推送 |

<a id="entry-613d2714f26278896fb3"></a>
### entry-613d2714f26278896fb3 · courseware<br>polymas-get-student-course-homework

技能  - 专家整理.xlsx / 模版推荐 / 第 27 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A27 | 助教 | courseware |
| B27 | 未命名列 B | polymas-get-student-course-homework |
| C27 | 未命名列 C | 算法 |

<a id="entry-e13c4ffb9234b2d0d993"></a>
### entry-e13c4ffb9234b2d0d993 · teaching_video<br>question_generate

技能  - 专家整理.xlsx / 模版推荐 / 第 28 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A28 | 助教 | teaching_video |
| B28 | 未命名列 B | question_generate |
| C28 | 未命名列 C | 检索 |

<a id="entry-583713ce4c7af2f1ecf0"></a>
### entry-583713ce4c7af2f1ecf0 · teaching_image<br>job_resume_match

技能  - 专家整理.xlsx / 模版推荐 / 第 29 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A29 | 助教 | teaching_image |
| B29 | 未命名列 B | job_resume_match |
| C29 | 未命名列 C | 文件理解 |

<a id="entry-e87a3b51e111729a795d"></a>
### entry-e87a3b51e111729a795d · domain_rank<br>custom_question

技能  - 专家整理.xlsx / 模版推荐 / 第 30 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A30 | 助教 | domain_rank |
| B30 | 未命名列 B | custom_question |
| C30 | 未命名列 C | 创作小助手 |

<a id="entry-2b12e5f994c5f48dd2b7"></a>
### entry-2b12e5f994c5f48dd2b7 · essence_decompose<br>domain_rank

技能  - 专家整理.xlsx / 模版推荐 / 第 31 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A31 | 助教 | essence_decompose |
| B31 | 未命名列 B | domain_rank |
| C31 | 未命名列 C | 智题策略专家 |

<a id="entry-cf29783d826ea1ee8889"></a>
### entry-cf29783d826ea1ee8889 · book_decompose<br>essence_decompose

技能  - 专家整理.xlsx / 模版推荐 / 第 32 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A32 | 助教 | book_decompose |
| B32 | 未命名列 B | essence_decompose |

<a id="entry-c9e1cfa742b7726bf65f"></a>
### entry-c9e1cfa742b7726bf65f · cognitive_shift<br>book_decompose

技能  - 专家整理.xlsx / 模版推荐 / 第 33 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A33 | 助教 | cognitive_shift |
| B33 | 未命名列 B | book_decompose |

<a id="entry-a93c1fef8ea1a2fb9103"></a>
### entry-a93c1fef8ea1a2fb9103 · book_predict<br>cognitive_shift

技能  - 专家整理.xlsx / 模版推荐 / 第 34 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A34 | 助教 | book_predict |
| B34 | 未命名列 B | cognitive_shift |

<a id="entry-ab20b90ebaa36c94ac61"></a>
### entry-ab20b90ebaa36c94ac61 · deep_drill<br>book_predict

技能  - 专家整理.xlsx / 模版推荐 / 第 35 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A35 | 助教 | deep_drill |
| B35 | 未命名列 B | book_predict |

<a id="entry-c4b5491667793a8a4833"></a>
### entry-c4b5491667793a8a4833 · essence_trace<br>deep_drill

技能  - 专家整理.xlsx / 模版推荐 / 第 36 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A36 | 助教 | essence_trace |
| B36 | 未命名列 B | deep_drill |

<a id="entry-1bab8869a63a0e6eb6dc"></a>
### entry-1bab8869a63a0e6eb6dc · socratic_dialogue<br>essence_trace

技能  - 专家整理.xlsx / 模版推荐 / 第 37 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A37 | 助教 | socratic_dialogue |
| B37 | 未命名列 B | essence_trace |

<a id="entry-58b6f1e183b93411359f"></a>
### entry-58b6f1e183b93411359f · descriptive_stats<br>word_mastery

技能  - 专家整理.xlsx / 模版推荐 / 第 38 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A38 | 助教 | descriptive_stats |
| B38 | 未命名列 B | word_mastery |

<a id="entry-8fd1a30593c072ae784f"></a>
### entry-8fd1a30593c072ae784f · hypothesis_test<br>infographic_gen

技能  - 专家整理.xlsx / 模版推荐 / 第 39 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A39 | 助教 | hypothesis_test |
| B39 | 未命名列 B | infographic_gen |

<a id="entry-ae105e67738e5337cc38"></a>
### entry-ae105e67738e5337cc38 · outlier_detect<br>socratic_dialogue

技能  - 专家整理.xlsx / 模版推荐 / 第 40 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A40 | 助教 | outlier_detect |
| B40 | 未命名列 B | socratic_dialogue |

<a id="entry-5751aa4dace4a6a3fadf"></a>
### entry-5751aa4dace4a6a3fadf · find-skills<br>sci_diagram

技能  - 专家整理.xlsx / 模版推荐 / 第 41 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A41 | 助教 | find-skills |
| B41 | 未命名列 B | sci_diagram |

<a id="entry-f4398a0ac55e2b2c3b6b"></a>
### entry-f4398a0ac55e2b2c3b6b · skill-creator<br>descriptive_stats

技能  - 专家整理.xlsx / 模版推荐 / 第 42 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A42 | 助教 | skill-creator |
| B42 | 未命名列 B | descriptive_stats |

<a id="entry-ca6b447146e9511992b8"></a>
### entry-ca6b447146e9511992b8 · hypothesis_test

技能  - 专家整理.xlsx / 模版推荐 / 第 43 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B43 | 未命名列 B | hypothesis_test |

<a id="entry-021d65a54499711c2fee"></a>
### entry-021d65a54499711c2fee · outlier_detect

技能  - 专家整理.xlsx / 模版推荐 / 第 44 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B44 | 未命名列 B | outlier_detect |

<a id="entry-72ff9b3e344149d19611"></a>
### entry-72ff9b3e344149d19611 · find-skills

技能  - 专家整理.xlsx / 模版推荐 / 第 45 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B45 | 未命名列 B | find-skills |

<a id="entry-cdffccacf8845e3591ff"></a>
### entry-cdffccacf8845e3591ff · skill-creator

技能  - 专家整理.xlsx / 模版推荐 / 第 46 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B46 | 未命名列 B | skill-creator |

<a id="entry-28f389935077437f6a60"></a>
### entry-28f389935077437f6a60 · DeepRag

技能一览表.xlsx / 技能一览 / 第 2 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A2 | 类别 | 检索 |
| B2 | 技能 | DeepRag |
| D2 | 是否有 | 有 |
| E2 | 上线时间 | 0603 |
| F2 | 挂载的Agent | 基础工具 |
| G2 | 最佳实践 | 帮我查询一下今日热点新闻 |
| H2 | 说明 | 技能返回格式化markdown |
| I2 | 备注 | 技能返回已修改为markdown约束 |
| J2 | 验证 | 支持 |

<a id="entry-1f24fadc1c28a0309bc3"></a>
### entry-1f24fadc1c28a0309bc3 · 外网检索

技能一览表.xlsx / 技能一览 / 第 3 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B3 | 技能 | 外网检索 |
| D3 | 是否有 | 有 |
| E3 | 上线时间 | 0610 |
| F3 | 挂载的Agent | 基础工具 |
| G3 | 最佳实践 | 帮我联网搜索一下XX技能 |
| J3 | 验证 | 支持 |
| A（合并继承自 A2；A2:A4） | 原值见锚点 | 检索 |

<a id="entry-ff3082e6b6882eb66639"></a>
### entry-ff3082e6b6882eb66639 · 资源库检索

技能一览表.xlsx / 技能一览 / 第 4 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B4 | 技能 | 资源库检索 |
| D4 | 是否有 | 有 |
| E4 | 上线时间 | 0603 |
| F4 | 挂载的Agent | 基础工具 |
| G4 | 最佳实践 | 我的资源库是否有Qoder相关知识 |
| H4 | 说明 | 技能返回格式化markdown |
| I4 | 备注 | 技能返回的描述有问题 |
| J4 | 验证 | 支持 |
| A（合并继承自 A2；A2:A4） | 原值见锚点 | 检索 |

<a id="entry-8d1f32d945ff0c406d61"></a>
### entry-8d1f32d945ff0c406d61 · 大明白V5帮助文档

技能一览表.xlsx / 技能一览 / 第 5 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A5 | 类别 | 帮助 |
| B5 | 技能 | 大明白V5帮助文档 |
| D5 | 是否有 | 有 |
| E5 | 上线时间 | 0603 |
| F5 | 挂载的Agent | 基础工具 |
| G5 | 最佳实践 | help，我需要帮助 |
| H5 | 说明 | 技能返回格式化markdown |
| J5 | 验证 | 支持 |

<a id="entry-0826b071711fc1dca524"></a>
### entry-0826b071711fc1dca524 · 检索

技能一览表.xlsx / 技能一览 / 第 6 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A6 | 类别 | 安装 |
| B6 | 技能 | 检索 |
| D6 | 是否有 | 有 |
| E6 | 上线时间 | 0603 |
| F6 | 挂载的Agent | 基础工具 |
| G6 | 最佳实践 | 当前技能平台有哪些能力 |
| H6 | 说明 | 技能返回格式化markdown |
| J6 | 验证 | 支持 |

<a id="entry-fce712cd5c91877ff531"></a>
### entry-fce712cd5c91877ff531 · 安装

技能一览表.xlsx / 技能一览 / 第 7 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B7 | 技能 | 安装 |
| D7 | 是否有 | 有 |
| E7 | 上线时间 | 0603 |
| F7 | 挂载的Agent | 基础工具 |
| G7 | 最佳实践 | 我要安装技能平台能力 |
| H7 | 说明 | 技能返回格式化markdown |
| J7 | 验证 | 不支持 |
| A（合并继承自 A6；A6:A8） | 原值见锚点 | 安装 |

<a id="entry-3eaed8c8fafb92b8cb03"></a>
### entry-3eaed8c8fafb92b8cb03 · 从外网安装技能

技能一览表.xlsx / 技能一览 / 第 8 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B8 | 技能 | 从外网安装技能 |
| D8 | 是否有 | 是 |
| E8 | 上线时间 | 0610 |
| F8 | 挂载的Agent | 基础工具 |
| G8 | 最佳实践 | 帮我联网安装一下XX技能 |
| J8 | 验证 | 不支持 |
| A（合并继承自 A6；A6:A8） | 原值见锚点 | 安装 |

<a id="entry-352f01efc2dd2f7bf12c"></a>
### entry-352f01efc2dd2f7bf12c · 课程数据

技能一览表.xlsx / 技能一览 / 第 9 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A9 | 类别 | 课程 |
| B9 | 技能 | 课程数据 |
| C9 | 要求 | 课程名称 |
| D9 | 是否有 | 有 |
| E9 | 上线时间 | 0530 |
| F9 | 挂载的Agent | 学课管理专员 |
| J9 | 验证 | 支持 |

<a id="entry-9214794ba0094a935aa2"></a>
### entry-9214794ba0094a935aa2 · 课程数据

技能一览表.xlsx / 技能一览 / 第 10 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C10 | 要求 | 章节 |
| D10 | 是否有 | 否 |
| H10 | 说明 | 不支持 |
| J10 | 验证 | 不支持 |
| A（合并继承自 A9；A9:A12） | 原值见锚点 | 课程 |
| B（合并继承自 B9；B9:B12） | 原值见锚点 | 课程数据 |

<a id="entry-6cb92202a5107b7b1be7"></a>
### entry-6cb92202a5107b7b1be7 · 课程数据

技能一览表.xlsx / 技能一览 / 第 11 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C11 | 要求 | 教学进度 |
| D11 | 是否有 | 是 |
| E11 | 上线时间 | 0611 |
| F11 | 挂载的Agent | 学科管理员 |
| J11 | 验证 | 不支持 |
| A（合并继承自 A9；A9:A12） | 原值见锚点 | 课程 |
| B（合并继承自 B9；B9:B12） | 原值见锚点 | 课程数据 |

<a id="entry-db180a48ebd16d05ff07"></a>
### entry-db180a48ebd16d05ff07 · 课程数据

技能一览表.xlsx / 技能一览 / 第 12 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C12 | 要求 | 课程资料 |
| D12 | 是否有 | 是 |
| E12 | 上线时间 | 0603 |
| F12 | 挂载的Agent | 基础工具 |
| G12 | 最佳实践 | 帮我搜素一下xx课程资源库中的数据 |
| J12 | 验证 | 不支持 |
| A（合并继承自 A9；A9:A12） | 原值见锚点 | 课程 |
| B（合并继承自 B9；B9:B12） | 原值见锚点 | 课程数据 |

<a id="entry-f20ad806dd203c1f1ea2"></a>
### entry-f20ad806dd203c1f1ea2 · 班级数据

技能一览表.xlsx / 技能一览 / 第 13 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A13 | 类别 | 班级 |
| B13 | 技能 | 班级数据 |
| C13 | 要求 | 学生数据 |
| D13 | 是否有 | 有 |
| E13 | 上线时间 | 0530 |
| F13 | 挂载的Agent | 学课管理专员 |

<a id="entry-ef61f07f84ff70587944"></a>
### entry-ef61f07f84ff70587944 · 班级数据

技能一览表.xlsx / 技能一览 / 第 14 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C14 | 要求 | 状态 |
| D14 | 是否有 | 否 |
| I14 | 备注 | 不知道是什么 |
| A（合并继承自 A13；A13:A14） | 原值见锚点 | 班级 |
| B（合并继承自 B13；B13:B14） | 原值见锚点 | 班级数据 |

<a id="entry-adc0e0535f0e502d508f"></a>
### entry-adc0e0535f0e502d508f · 发布作业

技能一览表.xlsx / 技能一览 / 第 15 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A15 | 类别 | 作业 |
| B15 | 技能 | 发布作业 |
| C15 | 要求 | 发布各种类型作业 |
| D15 | 是否有 | 有 |
| I15 | 备注 | 需要调试 |
| J15 | 验证 | 支持 |

<a id="entry-627e61fe081cb2cbb84c"></a>
### entry-627e61fe081cb2cbb84c · 修改作业

技能一览表.xlsx / 技能一览 / 第 16 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B16 | 技能 | 修改作业 |
| C16 | 要求 | 修改作业 |
| D16 | 是否有 | 有 |
| I16 | 备注 | 需要调试 |
| J16 | 验证 | 支持 |
| A（合并继承自 A15；A15:A21） | 原值见锚点 | 作业 |

<a id="entry-f0e3d3cbd522da8fd14a"></a>
### entry-f0e3d3cbd522da8fd14a · 作业数据

技能一览表.xlsx / 技能一览 / 第 17 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B17 | 技能 | 作业数据 |
| C17 | 要求 | 作业基础数据 |
| D17 | 是否有 | 有 |
| E17 | 上线时间 | 0603 |
| F17 | 挂载的Agent | 教学活动专员 |
| G17 | 最佳实践 | 帮我查询一下全部作业，帮我查询一下XX课程下的作业 |
| J17 | 验证 | 支持/老师、学生 |
| A（合并继承自 A15；A15:A21） | 原值见锚点 | 作业 |

<a id="entry-623197754e543e6378da"></a>
### entry-623197754e543e6378da · 作业数据

技能一览表.xlsx / 技能一览 / 第 18 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C18 | 要求 | 分数 |
| D18 | 是否有 | 有 |
| E18 | 上线时间 | 0603 |
| F18 | 挂载的Agent | 教学活动专员 |
| G18 | 最佳实践 | 帮我查看一下分数低于60份的作业 |
| J18 | 验证 | 支持 |
| A（合并继承自 A15；A15:A21） | 原值见锚点 | 作业 |
| B（合并继承自 B17；B17:B21） | 原值见锚点 | 作业数据 |

<a id="entry-71d79f072076532aaba0"></a>
### entry-71d79f072076532aaba0 · 作业数据

技能一览表.xlsx / 技能一览 / 第 19 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C19 | 要求 | 完成状态 |
| D19 | 是否有 | 有 |
| E19 | 上线时间 | 0603 |
| F19 | 挂载的Agent | 教学活动专员 |
| G19 | 最佳实践 | 查询当前未完成的作业 |
| J19 | 验证 | 支持 |
| A（合并继承自 A15；A15:A21） | 原值见锚点 | 作业 |
| B（合并继承自 B17；B17:B21） | 原值见锚点 | 作业数据 |

<a id="entry-8b439be63f33e3bdb48b"></a>
### entry-8b439be63f33e3bdb48b · 作业数据

技能一览表.xlsx / 技能一览 / 第 20 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C20 | 要求 | 催交 |
| D20 | 是否有 | 有 |
| E20 | 上线时间 | 0603 |
| F20 | 挂载的Agent | 教学活动专员 |
| G20 | 最佳实践 | 帮我催交一下全部作业，帮我催交一下XX课程下的作业 |
| J20 | 验证 | 支持 |
| A（合并继承自 A15；A15:A21） | 原值见锚点 | 作业 |
| B（合并继承自 B17；B17:B21） | 原值见锚点 | 作业数据 |

<a id="entry-def2d34d28033038aa5c"></a>
### entry-def2d34d28033038aa5c · 作业数据

技能一览表.xlsx / 技能一览 / 第 21 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C21 | 要求 | 打回 |
| D21 | 是否有 | 有 |
| E21 | 上线时间 | 0603 |
| F21 | 挂载的Agent | 教学活动专员 |
| G21 | 最佳实践 | 帮我打回一下全部作业，帮我打回一下XX课程下的作业 |
| J21 | 验证 | 支持 |
| A（合并继承自 A15；A15:A21） | 原值见锚点 | 作业 |
| B（合并继承自 B17；B17:B21） | 原值见锚点 | 作业数据 |

<a id="entry-6f46450695463f9f734a"></a>
### entry-6f46450695463f9f734a · 测验 / 考试数据

技能一览表.xlsx / 技能一览 / 第 22 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A22 | 类别 | 考试 |
| B22 | 技能 | 测验 / 考试数据 |
| C22 | 要求 | 至少 1 次阶段测验，用于和作业、问答数据交叉分析 |
| D22 | 是否有 | 否 |
| J22 | 验证 | 不支持 |

<a id="entry-a2eff6128f85483e03ad"></a>
### entry-a2eff6128f85483e03ad · 学生互动数据

技能一览表.xlsx / 技能一览 / 第 23 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A23 | 类别 | 互动 |
| B23 | 技能 | 学生互动数据 |
| D23 | 是否有 | 否 |
| J23 | 验证 | 不支持 |

<a id="entry-711edaba5c1c1a7724f6"></a>
### entry-711edaba5c1c1a7724f6 · 视频

技能一览表.xlsx / 技能一览 / 第 24 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A24 | 类别 | 内容创作 |
| B24 | 技能 | 视频 |
| D24 | 是否有 | 有 |
| J24 | 验证 | 支持 |

<a id="entry-12b08ed3dda7d98cea52"></a>
### entry-12b08ed3dda7d98cea52 · 图片

技能一览表.xlsx / 技能一览 / 第 25 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B25 | 技能 | 图片 |
| D25 | 是否有 | 有 |
| J25 | 验证 | 支持 |
| A（合并继承自 A24；A24:A28） | 原值见锚点 | 内容创作 |

<a id="entry-d794590682ab96b53fae"></a>
### entry-d794590682ab96b53fae · PPT

技能一览表.xlsx / 技能一览 / 第 26 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B26 | 技能 | PPT |
| D26 | 是否有 | 有 |
| J26 | 验证 | 支持 |
| A（合并继承自 A24；A24:A28） | 原值见锚点 | 内容创作 |

<a id="entry-ab71616f3c4751947274"></a>
### entry-ab71616f3c4751947274 · HTML

技能一览表.xlsx / 技能一览 / 第 27 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B27 | 技能 | HTML |
| D27 | 是否有 | 有 |
| J27 | 验证 | 支持 |
| A（合并继承自 A24；A24:A28） | 原值见锚点 | 内容创作 |

<a id="entry-c8f9a51db2f0e4876eb8"></a>
### entry-c8f9a51db2f0e4876eb8 · 文本

技能一览表.xlsx / 技能一览 / 第 28 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B28 | 技能 | 文本 |
| D28 | 是否有 | 有 |
| J28 | 验证 | 支持 |
| A（合并继承自 A24；A24:A28） | 原值见锚点 | 内容创作 |

<a id="entry-bad24347f333b177ff92"></a>
### entry-bad24347f333b177ff92 · anysearch-skill

技能一览表.xlsx / 技能一览 / 第 31 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B31 | 技能 | anysearch-skill |

<a id="entry-986d9b429325942f18d3"></a>
### entry-986d9b429325942f18d3 · docx

技能一览表.xlsx / V5技能 / 第 2 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A2 | agent | 文件解析 |
| B2 | 技能小类 | 文档操作 |
| C2 | 技能名称 | docx |
| D2 | 适用范围 | 学生/老师 |
| E2 | 技能说明 | docx文档操作 |
| F2 | 技能详情 | docx文档操作 |

<a id="entry-1d087942f3625ec59304"></a>
### entry-1d087942f3625ec59304 · xlsx

技能一览表.xlsx / V5技能 / 第 3 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C3 | 技能名称 | xlsx |
| D3 | 适用范围 | 学生/老师 |
| E3 | 技能说明 | xlsx表格操作 |
| F3 | 技能详情 | xlsx表格操作 |
| A（合并继承自 A2；A2:A5） | 原值见锚点 | 文件解析 |
| B（合并继承自 B2；B2:B5） | 原值见锚点 | 文档操作 |

<a id="entry-98b06b51f50297fe455c"></a>
### entry-98b06b51f50297fe455c · ppt

技能一览表.xlsx / V5技能 / 第 4 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C4 | 技能名称 | ppt |
| D4 | 适用范围 | 学生/老师 |
| E4 | 技能说明 | ppt操作 |
| F4 | 技能详情 | ppt操作 |
| A（合并继承自 A2；A2:A5） | 原值见锚点 | 文件解析 |
| B（合并继承自 B2；B2:B5） | 原值见锚点 | 文档操作 |

<a id="entry-a5f8c0ae6baa2c0051b2"></a>
### entry-a5f8c0ae6baa2c0051b2 · pdf

技能一览表.xlsx / V5技能 / 第 5 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C5 | 技能名称 | pdf |
| D5 | 适用范围 | 学生/老师 |
| E5 | 技能说明 | pdf操作 |
| F5 | 技能详情 | pdf操作 |
| A（合并继承自 A2；A2:A5） | 原值见锚点 | 文件解析 |
| B（合并继承自 B2；B2:B5） | 原值见锚点 | 文档操作 |

<a id="entry-72b08c75792b6f8fd89a"></a>
### entry-72b08c75792b6f8fd89a · polymas-agent-readme

技能一览表.xlsx / V5技能 / 第 6 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A6 | agent | 基础工作 |
| B6 | 技能小类 | 操作说明 |
| C6 | 技能名称 | polymas-agent-readme |
| D6 | 适用范围 | 学生/老师 |
| E6 | 技能说明 | V5-使用说明 |
| F6 | 技能详情 | V5-使用说明 |

<a id="entry-1ecf6761f76eb78a0593"></a>
### entry-1ecf6761f76eb78a0593 · polymas-online-search

技能一览表.xlsx / V5技能 / 第 7 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B7 | 技能小类 | 联网操作 |
| C7 | 技能名称 | polymas-online-search |
| D7 | 适用范围 | 学生/老师 |
| E7 | 技能说明 | 联网搜索 |
| F7 | 技能详情 | 联网搜索 |
| A（合并继承自 A6；A6:A13） | 原值见锚点 | 基础工作 |

<a id="entry-d6cc6458807d8ba6e07b"></a>
### entry-d6cc6458807d8ba6e07b · polymas-skill-online-search-install

技能一览表.xlsx / V5技能 / 第 8 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C8 | 技能名称 | polymas-skill-online-search-install |
| D8 | 适用范围 | 学生/老师 |
| E8 | 技能说明 | 联网搜索/安装SKILL |
| F8 | 技能详情 | 网搜索 Skill 市场并安装到平台。支持仅搜索和搜索即安装。<br>默认 ClawHub（纯 API，零浏览器），也支持 ModelScope 和 SkillsMP |
| B（合并继承自 B7；B7:B8） | 原值见锚点 | 联网操作 |
| A（合并继承自 A6；A6:A13） | 原值见锚点 | 基础工作 |

<a id="entry-b3549915d233ed6f6a49"></a>
### entry-b3549915d233ed6f6a49 · polymas-capability-search-install

技能一览表.xlsx / V5技能 / 第 9 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B9 | 技能小类 | 技能广场 |
| C9 | 技能名称 | polymas-capability-search-install |
| D9 | 适用范围 | 学生/老师 |
| E9 | 技能说明 | 能力广场搜索/安装能力 |
| F9 | 技能详情 | 用于搜索/安装技能广场的AI能力（技能SKILL、技能套件SKILL_SUITE、<br>MCP工具MCP） |
| A（合并继承自 A6；A6:A13） | 原值见锚点 | 基础工作 |

<a id="entry-5701713791fe21c6b269"></a>
### entry-5701713791fe21c6b269 · polymas-user-detail-query

技能一览表.xlsx / V5技能 / 第 10 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B10 | 技能小类 | 用户详情 |
| C10 | 技能名称 | polymas-user-detail-query |
| D10 | 适用范围 | 学生/老师 |
| E10 | 技能说明 | 用户详情查询 |
| F10 | 技能详情 | 查询当前用户详细信息 |
| A（合并继承自 A6；A6:A13） | 原值见锚点 | 基础工作 |

<a id="entry-f6a9e1df46bf01feda49"></a>
### entry-f6a9e1df46bf01feda49 · polymas-teacher-knowledge-search

技能一览表.xlsx / V5技能 / 第 11 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B11 | 技能小类 | 文件/资源操作 |
| C11 | 技能名称 | polymas-teacher-knowledge-search |
| D11 | 适用范围 | 老师 |
| E11 | 技能说明 | 教师搜索知识库 |
| F11 | 技能详情 | 搜索教师知识库内容，包括标题、资源类型、资源封面、<br>资源链接、资源预览图标、资源名称、资源摘要 |
| A（合并继承自 A6；A6:A13） | 原值见锚点 | 基础工作 |

<a id="entry-4cb249404d18846cdfd1"></a>
### entry-4cb249404d18846cdfd1 · polymas-teacher-resource-file-search

技能一览表.xlsx / V5技能 / 第 12 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C12 | 技能名称 | polymas-teacher-resource-file-search |
| D12 | 适用范围 | 老师 |
| E12 | 技能说明 | 教师搜索资源库文件 |
| F12 | 技能详情 | 搜索资源库中的教师文件，包括文件标题、文件后缀、文件大小、<br>文件地址、创建/更新时间 |
| B（合并继承自 B11；B11:B13） | 原值见锚点 | 文件/资源操作 |
| A（合并继承自 A6；A6:A13） | 原值见锚点 | 基础工作 |

<a id="entry-4fdac110bdb75ada7d69"></a>
### entry-4fdac110bdb75ada7d69 · polymas-file-upload

技能一览表.xlsx / V5技能 / 第 13 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C13 | 技能名称 | polymas-file-upload |
| D13 | 适用范围 | 学生/老师 |
| E13 | 技能说明 | 通用文件上传 |
| F13 | 技能详情 | 通用文件上传 |
| B（合并继承自 B11；B11:B13） | 原值见锚点 | 文件/资源操作 |
| A（合并继承自 A6；A6:A13） | 原值见锚点 | 基础工作 |

<a id="entry-72e4a15b641984d06b9b"></a>
### entry-72e4a15b641984d06b9b · polymas-teaching-unit-query

技能一览表.xlsx / V5技能 / 第 14 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A14 | agent | 学课管理员 |
| B14 | 技能小类 | 教学单元 |
| C14 | 技能名称 | polymas-teaching-unit-query |
| D14 | 适用范围 | 老师 |
| E14 | 技能说明 | 教学单元查询 |
| F14 | 技能详情 | 查询课程的教学单元、教学主题及知识点信息 |

<a id="entry-629a84e97afc1cd1b558"></a>
### entry-629a84e97afc1cd1b558 · polymas-teacher-course-search

技能一览表.xlsx / V5技能 / 第 15 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B15 | 技能小类 | 班/课查询 |
| C15 | 技能名称 | polymas-teacher-course-search |
| D15 | 适用范围 | 老师 |
| E15 | 技能说明 | 教师课程查询 |
| F15 | 技能详情 | 教师搜索当前学期的课程信息，返回完整的课程列表数据 |
| A（合并继承自 A14；A14:A18） | 原值见锚点 | 学课管理员 |

<a id="entry-1a6f619987b2f4c013da"></a>
### entry-1a6f619987b2f4c013da · polymas-teacher-class-search

技能一览表.xlsx / V5技能 / 第 16 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C16 | 技能名称 | polymas-teacher-class-search |
| D16 | 适用范围 | 老师 |
| E16 | 技能说明 | 教师管理班级查询 |
| F16 | 技能详情 | 教师查询自己管理的班级列表信息，包括班级人数及学生明细 |
| A（合并继承自 A14；A14:A18） | 原值见锚点 | 学课管理员 |
| B（合并继承自 B15；B15:B18） | 原值见锚点 | 班/课查询 |

<a id="entry-3f948f433dd3842beb9d"></a>
### entry-3f948f433dd3842beb9d · polymas-student-course-search

技能一览表.xlsx / V5技能 / 第 17 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C17 | 技能名称 | polymas-student-course-search |
| D17 | 适用范围 | 学生 |
| E17 | 技能说明 | 学生课程查询 |
| F17 | 技能详情 | 学生查询当前学期课程信息，返回完成的课程列表数据 |
| A（合并继承自 A14；A14:A18） | 原值见锚点 | 学课管理员 |
| B（合并继承自 B15；B15:B18） | 原值见锚点 | 班/课查询 |

<a id="entry-7cda31772e815bf813e9"></a>
### entry-7cda31772e815bf813e9 · polymas-student-class-search

技能一览表.xlsx / V5技能 / 第 18 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C18 | 技能名称 | polymas-student-class-search |
| D18 | 适用范围 | 学生 |
| E18 | 技能说明 | 学生班级查询 |
| F18 | 技能详情 | 学生查询关联的班级信息，支持查询班级列表和对应班级下学生数据 |
| A（合并继承自 A14；A14:A18） | 原值见锚点 | 学课管理员 |
| B（合并继承自 B15；B15:B18） | 原值见锚点 | 班/课查询 |

<a id="entry-961a6cde40d971f2837d"></a>
### entry-961a6cde40d971f2837d · polymas-teacher-homework-search

技能一览表.xlsx / V5技能 / 第 19 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A19 | agent | 教学活动专员 |
| B19 | 技能小类 | 作业操作 |
| C19 | 技能名称 | polymas-teacher-homework-search |
| D19 | 适用范围 | 老师 |
| E19 | 技能说明 | 教师作业查询 |
| F19 | 技能详情 | 查询教师在课程下的作业信息，包括作业详细信息、<br>作业关联班级信息、班级作业结束时间、完成率统计等数据 |

<a id="entry-bf5177a1cc205f5beabd"></a>
### entry-bf5177a1cc205f5beabd · polymas-teacher-homework-hit-back

技能一览表.xlsx / V5技能 / 第 20 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C20 | 技能名称 | polymas-teacher-homework-hit-back |
| D20 | 适用范围 | 老师 |
| E20 | 技能说明 | 教师打回作业 |
| F20 | 技能详情 | 教师按课程、作业、班级、学号等条件筛选已提交学生，<br>批量打回学生作业 |
| B（合并继承自 B19；B19:B24） | 原值见锚点 | 作业操作 |
| A（合并继承自 A19；A19:A25） | 原值见锚点 | 教学活动专员 |

<a id="entry-7d429f6a62a82d9c8b9d"></a>
### entry-7d429f6a62a82d9c8b9d · polymas-teacher-homework-urge

技能一览表.xlsx / V5技能 / 第 21 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C21 | 技能名称 | polymas-teacher-homework-urge |
| D21 | 适用范围 | 老师 |
| E21 | 技能说明 | 教师催交作业 |
| F21 | 技能详情 | 教师催促作业下未提交作业的学生，支持按课程、作业、<br>学生等条件精确筛选待催交学生并批量发送催交通知 |
| B（合并继承自 B19；B19:B24） | 原值见锚点 | 作业操作 |
| A（合并继承自 A19；A19:A25） | 原值见锚点 | 教学活动专员 |

<a id="entry-46694fafc48b3af5fabd"></a>
### entry-46694fafc48b3af5fabd · polymas-teacher-homework-analysis

技能一览表.xlsx / V5技能 / 第 22 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C22 | 技能名称 | polymas-teacher-homework-analysis |
| D22 | 适用范围 | 老师 |
| E22 | 技能说明 | 教师分析作业完成情况 |
| F22 | 技能详情 | 教师按课程、作业查看作业学情分析报告，包括成绩概览、<br>高频错题、预警学生等数据 |
| B（合并继承自 B19；B19:B24） | 原值见锚点 | 作业操作 |
| A（合并继承自 A19；A19:A25） | 原值见锚点 | 教学活动专员 |

<a id="entry-a4be5a7b9ca61fb2fbe8"></a>
### entry-a4be5a7b9ca61fb2fbe8 · polymas-teacher-homework-chat-query

技能一览表.xlsx / V5技能 / 第 23 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C23 | 技能名称 | polymas-teacher-homework-chat-query |
| D23 | 适用范围 | 老师 |
| E23 | 技能说明 | 教师查询/分析作业下互动交流内容 |
| F23 | 技能详情 | 教师查看作业下学生与教师的互动交流记录，支持分页展示<br>和嵌套回复浏览 |
| B（合并继承自 B19；B19:B24） | 原值见锚点 | 作业操作 |
| A（合并继承自 A19；A19:A25） | 原值见锚点 | 教学活动专员 |

<a id="entry-e9a5686af70c108c67c2"></a>
### entry-e9a5686af70c108c67c2 · polymas-student-homework-search

技能一览表.xlsx / V5技能 / 第 24 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C24 | 技能名称 | polymas-student-homework-search |
| D24 | 适用范围 | 学生 |
| E24 | 技能说明 | 学生作业查询 |
| F24 | 技能详情 | 学生查询在课程下的所有作业信息，包括作业详细信息、作业关联<br>班级信息、班级作业结束时间、完成率统计等数据 |
| B（合并继承自 B19；B19:B24） | 原值见锚点 | 作业操作 |
| A（合并继承自 A19；A19:A25） | 原值见锚点 | 教学活动专员 |

<a id="entry-31dcc5270a12c1d9e27f"></a>
### entry-31dcc5270a12c1d9e27f · polymas-teacher-lession-analysis

技能一览表.xlsx / V5技能 / 第 25 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B25 | 技能小类 | 课堂操作 |
| C25 | 技能名称 | polymas-teacher-lession-analysis |
| D25 | 适用范围 | 老师 |
| E25 | 技能说明 | 教师查看课堂分析报告 |
| F25 | 技能详情 | 教师按课程、课堂查看学生课堂表现分析报告，包括成绩得分、<br>互动参与、弹幕次数、在线时长等数据 |
| A（合并继承自 A19；A19:A25） | 原值见锚点 | 教学活动专员 |

<a id="entry-f1b9f3e95c6cce589082"></a>
### entry-f1b9f3e95c6cce589082 · schedule-meeting

技能一览表.xlsx / V5技能 / 第 26 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A26 | agent | 会议/日程专员 |
| B26 | 技能小类 | 会议/日程管理 |
| C26 | 技能名称 | schedule-meeting |
| D26 | 适用范围 | 老师/学生 |
| E26 | 技能说明 | 会议日程管理 |
| F26 | 技能详情 | 该技能用于管理日程与会议：创建、查询、取消；查询日程/会议列表。 |

<a id="entry-329699efebd43720932f"></a>
### entry-329699efebd43720932f · aigc-teaching-material

技能一览表.xlsx / V5技能 / 第 27 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A27 | agent | 智能备课专员 |
| B27 | 技能小类 | 教学AIGC生成 |
| C27 | 技能名称 | aigc-teaching-material |
| D27 | 适用范围 | 老师/学生 |
| E27 | 技能说明 | 教学AIGC生成 |
| F27 | 技能详情 | 生成教学相关 AIGC 素材，涵盖教案、报告、代码、PPT/HTML 课件、网页、图片、教学视频。 |

<a id="entry-31045ddec5224f42cc70"></a>
### entry-31045ddec5224f42cc70 · 创建作业

技能一览表.xlsx / V5技能 / 第 28 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| E28 | 技能说明 | 创建作业 |

<a id="entry-5a7780f6214eb0be28d2"></a>
### entry-5a7780f6214eb0be28d2 · 修改作业

技能一览表.xlsx / V5技能 / 第 29 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| E29 | 技能说明 | 修改作业 |

<a id="entry-aed6cdd426aeb683725a"></a>
### entry-aed6cdd426aeb683725a · 课表查询

技能一览表.xlsx / V5技能 / 第 30 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| E30 | 技能说明 | 课表查询 |

<a id="entry-48e5c3dfa980cd145252"></a>
### entry-48e5c3dfa980cd145252 · 题库查询

技能一览表.xlsx / V5技能 / 第 31 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| E31 | 技能说明 | 题库查询 |

<a id="entry-1440208af7a68ca52042"></a>
### entry-1440208af7a68ca52042 · 知识点查询

技能一览表.xlsx / V5技能 / 第 32 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| E32 | 技能说明 | 知识点查询 |

<a id="entry-51388db58bb2d1309ce1"></a>
### entry-51388db58bb2d1309ce1 · 能力训练查询

技能一览表.xlsx / V5技能 / 第 33 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| E33 | 技能说明 | 能力训练查询 |

<a id="entry-e380bc88346028cb6ae9"></a>
### entry-e380bc88346028cb6ae9 · 智能辅查询

技能一览表.xlsx / V5技能 / 第 34 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| E34 | 技能说明 | 智能辅查询 |

<a id="entry-484ba5abcfcda5ee2d58"></a>
### entry-484ba5abcfcda5ee2d58 · polymas-teacher-homework-skills

技能一览表.xlsx / V5技能列表 / 第 2 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A2 | 技能类型 | 老师 |
| C2 | 适用范围 | 教学活动 |
| D2 | 技能名称 | polymas-teacher-homework-skills |
| E2 | 技能简介 | 作业查询、催促、打回、创建、编辑、分析、作业下方交流分析 |

<a id="entry-9d484cddfb2f306ad382"></a>
### entry-9d484cddfb2f306ad382 · polymas-teacher-exam-skills

技能一览表.xlsx / V5技能列表 / 第 3 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| D3 | 技能名称 | polymas-teacher-exam-skills |
| E3 | 技能简介 | 考试创建、编辑、查询 |
| A（合并继承自 A2；A2:A18） | 原值见锚点 | 老师 |
| C（合并继承自 C2；C2:C6） | 原值见锚点 | 教学活动 |

<a id="entry-afd3d32f92f569345ab3"></a>
### entry-afd3d32f92f569345ab3 · polymas-teacher-score-skills

技能一览表.xlsx / V5技能列表 / 第 4 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| D4 | 技能名称 | polymas-teacher-score-skills |
| E4 | 技能简介 | 成绩汇总、成绩加权计算、班级成绩查询、成绩导出 |
| A（合并继承自 A2；A2:A18） | 原值见锚点 | 老师 |
| C（合并继承自 C2；C2:C6） | 原值见锚点 | 教学活动 |

<a id="entry-69320239af01eb670d3d"></a>
### entry-69320239af01eb670d3d · polymas-teacher-activity-skills

技能一览表.xlsx / V5技能列表 / 第 5 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| D5 | 技能名称 | polymas-teacher-activity-skills |
| E5 | 技能简介 | 通知发布、通知查看、通知分析、话题讨论发布、话题讨论查看、话题讨论分析 |
| A（合并继承自 A2；A2:A18） | 原值见锚点 | 老师 |
| C（合并继承自 C2；C2:C6） | 原值见锚点 | 教学活动 |

<a id="entry-ecf5094891bfc0ebd504"></a>
### entry-ecf5094891bfc0ebd504 · polymas-teacher-lession-analysis

技能一览表.xlsx / V5技能列表 / 第 6 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| D6 | 技能名称 | polymas-teacher-lession-analysis |
| E6 | 技能简介 | 教师按课程、课堂查看学生课堂表现分析报告，包括成绩得分、<br>互动参与、弹幕次数、在线时长等数据 |
| A（合并继承自 A2；A2:A18） | 原值见锚点 | 老师 |
| C（合并继承自 C2；C2:C6） | 原值见锚点 | 教学活动 |

<a id="entry-7403b63f751c757b83ac"></a>
### entry-7403b63f751c757b83ac · polymas-teacher-course-skills

技能一览表.xlsx / V5技能列表 / 第 7 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C7 | 适用范围 | 学课管理 |
| D7 | 技能名称 | polymas-teacher-course-skills |
| E7 | 技能简介 | 课程查询、创建 |
| A（合并继承自 A2；A2:A18） | 原值见锚点 | 老师 |

<a id="entry-f2a27b48a34b0ae5a197"></a>
### entry-f2a27b48a34b0ae5a197 · polymas-teacher-class-skills

技能一览表.xlsx / V5技能列表 / 第 8 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| D8 | 技能名称 | polymas-teacher-class-skills |
| E8 | 技能简介 | 班级查询、创建、批量导入、学生入班 |
| C（合并继承自 C7；C7:C11） | 原值见锚点 | 学课管理 |
| A（合并继承自 A2；A2:A18） | 原值见锚点 | 老师 |

<a id="entry-3df081ace7c934a81fdb"></a>
### entry-3df081ace7c934a81fdb · polymas-query-teaching-unit

技能一览表.xlsx / V5技能列表 / 第 9 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| D9 | 技能名称 | polymas-query-teaching-unit |
| E9 | 技能简介 | 教学计划查询 |
| C（合并继承自 C7；C7:C11） | 原值见锚点 | 学课管理 |
| A（合并继承自 A2；A2:A18） | 原值见锚点 | 老师 |

<a id="entry-25713d7685f8cadc5803"></a>
### entry-25713d7685f8cadc5803 · 课程更换负责人---待产品审核

技能一览表.xlsx / V5技能列表 / 第 10 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| E10 | 技能简介 | 课程更换负责人---待产品审核 |
| C（合并继承自 C7；C7:C11） | 原值见锚点 | 学课管理 |
| A（合并继承自 A2；A2:A18） | 原值见锚点 | 老师 |

<a id="entry-c572b7c6e9196f0ff5a4"></a>
### entry-c572b7c6e9196f0ff5a4 · 团队老师查询、添加、设置为管理员、分配班级、移除班级、移除团队老师---待产品审核

技能一览表.xlsx / V5技能列表 / 第 11 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| E11 | 技能简介 | 团队老师查询、添加、设置为管理员、分配班级、移除班级、移除团队老师---待产品审核 |
| C（合并继承自 C7；C7:C11） | 原值见锚点 | 学课管理 |
| A（合并继承自 A2；A2:A18） | 原值见锚点 | 老师 |

<a id="entry-8d1c2595006760dfc03b"></a>
### entry-8d1c2595006760dfc03b · 教学日程查询---待产品审核

技能一览表.xlsx / V5技能列表 / 第 12 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C12 | 适用范围 | 教学日历 |
| E12 | 技能简介 | 教学日程查询---待产品审核 |
| A（合并继承自 A2；A2:A18） | 原值见锚点 | 老师 |

<a id="entry-2a49d1b0732d08e52ba6"></a>
### entry-2a49d1b0732d08e52ba6 · polymas-teacher-problem-skills

技能一览表.xlsx / V5技能列表 / 第 13 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C13 | 适用范围 | 备课 |
| D13 | 技能名称 | polymas-teacher-problem-skills |
| E13 | 技能简介 | 根据知识点、难度、题型等要求，通过 AI 自动生成题目并保存到题库 |
| A（合并继承自 A2；A2:A18） | 原值见锚点 | 老师 |

<a id="entry-26e6bd3d651a9ae89b3a"></a>
### entry-26e6bd3d651a9ae89b3a · polymas-teacher-case-skills

技能一览表.xlsx / V5技能列表 / 第 14 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| D14 | 技能名称 | polymas-teacher-case-skills |
| E14 | 技能简介 | 根据课程内容与教学需求，生成真实商业案例、生活化案例、行业案例等教学案例，支持自定义案例类型 |
| C（合并继承自 C13；C13:C17） | 原值见锚点 | 备课 |
| A（合并继承自 A2；A2:A18） | 原值见锚点 | 老师 |

<a id="entry-e889a1e7035ccfbc58e1"></a>
### entry-e889a1e7035ccfbc58e1 · polymas-teacher-lesson-design

技能一览表.xlsx / V5技能列表 / 第 15 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| D15 | 技能名称 | polymas-teacher-lesson-design |
| E15 | 技能简介 | 根据教师提供的课程主题与教学要求，生成结构化课堂教学流程方案，支持多轮迭代与细化 |
| F15 | 技能依赖 | 老师/学生&gt;文档操作&gt;(docx、xlsx、ppt、pdf) |
| C（合并继承自 C13；C13:C17） | 原值见锚点 | 备课 |
| A（合并继承自 A2；A2:A18） | 原值见锚点 | 老师 |

<a id="entry-38b73e2d119a3585e791"></a>
### entry-38b73e2d119a3585e791 · polymas-teacher-analogy-skills

技能一览表.xlsx / V5技能列表 / 第 16 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| D16 | 技能名称 | polymas-teacher-analogy-skills |
| E16 | 技能简介 | 将抽象概念转化为类比、例子或反例，帮助教师将复杂理论转化为通俗易懂的课堂讲解内容 |
| C（合并继承自 C13；C13:C17） | 原值见锚点 | 备课 |
| A（合并继承自 A2；A2:A18） | 原值见锚点 | 老师 |

<a id="entry-ebe9170b61c6a142aeaf"></a>
### entry-ebe9170b61c6a142aeaf · polymas-teacher-content-creation

技能一览表.xlsx / V5技能列表 / 第 17 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| D17 | 技能名称 | polymas-teacher-content-creation |
| E17 | 技能简介 | 根据教学需求，智能生成教案、复习提纲、课堂讲稿、PPT等备课材料的提示词，并调用内容生成引擎完成创作 |
| F17 | 技能依赖 | 老师/学生&gt;文档操作&gt;(docx、xlsx、ppt、pdf) |
| C（合并继承自 C13；C13:C17） | 原值见锚点 | 备课 |
| A（合并继承自 A2；A2:A18） | 原值见锚点 | 老师 |

<a id="entry-4958f95d48f08bbd7ad6"></a>
### entry-4958f95d48f08bbd7ad6 · polymas-teacher-resource-skills

技能一览表.xlsx / V5技能列表 / 第 18 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C18 | 适用范围 | 资源管理 |
| D18 | 技能名称 | polymas-teacher-resource-skills |
| E18 | 技能简介 | 知识库内容搜索、资源库文件搜索/上传 |
| A（合并继承自 A2；A2:A18） | 原值见锚点 | 老师 |

<a id="entry-1343af9310575fe6b603"></a>
### entry-1343af9310575fe6b603 · polymas-teacher-questionbank-skills

技能一览表.xlsx / V5技能列表 / 第 19 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| D19 | 技能名称 | polymas-teacher-questionbank-skills |
| E19 | 技能简介 | 根据用户需求智能选择题库查询或Excel批量导入题目 |
| C（合并继承自 C18；C18:C21） | 原值见锚点 | 资源管理 |

<a id="entry-14ef7da87b85332c3036"></a>
### entry-14ef7da87b85332c3036 · schedule-meeting

技能一览表.xlsx / V5技能列表 / 第 22 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A22 | 技能类型 | 老师/学生 |
| C22 | 适用范围 | 会议日程管理 |
| D22 | 技能名称 | schedule-meeting |
| E22 | 技能简介 | 该技能用于管理日程与会议：创建、查询、取消；查询日程/会议列表。 |

<a id="entry-721972c5c3de8edac21b"></a>
### entry-721972c5c3de8edac21b · aigc-teaching-material

技能一览表.xlsx / V5技能列表 / 第 23 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C23 | 适用范围 | 教学AIGC生成 |
| D23 | 技能名称 | aigc-teaching-material |
| E23 | 技能简介 | 生成教学相关 AIGC 素材，涵盖教案、报告、代码、PPT/HTML 课件、网页、图片、教学视频。 |
| A（合并继承自 A22；A22:A29） | 原值见锚点 | 老师/学生 |

<a id="entry-4b28395248f511f1eaf2"></a>
### entry-4b28395248f511f1eaf2 · polymas-tool-skills

技能一览表.xlsx / V5技能列表 / 第 24 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C24 | 适用范围 | 通用工具 |
| D24 | 技能名称 | polymas-tool-skills |
| E24 | 技能简介 | 联网搜索互联网公开内容、搜索 Skill（可选择性安装）、能力广场搜索/安装、查询当前登录用户信息、文件上传 |
| A（合并继承自 A22；A22:A29） | 原值见锚点 | 老师/学生 |

<a id="entry-eb50ca296dbdc19f3d3c"></a>
### entry-eb50ca296dbdc19f3d3c · polymas-agent-readme

技能一览表.xlsx / V5技能列表 / 第 25 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C25 | 适用范围 | 平台助手 |
| D25 | 技能名称 | polymas-agent-readme |
| E25 | 技能简介 |  平台帮助手册 |
| A（合并继承自 A22；A22:A29） | 原值见锚点 | 老师/学生 |

<a id="entry-09a86973f1351332b1ba"></a>
### entry-09a86973f1351332b1ba · docx

技能一览表.xlsx / V5技能列表 / 第 26 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C26 | 适用范围 | 文档操作 |
| D26 | 技能名称 | docx |
| E26 | 技能简介 | docx文档操作 |
| A（合并继承自 A22；A22:A29） | 原值见锚点 | 老师/学生 |

<a id="entry-f1e33a9e52f3c0bf01f7"></a>
### entry-f1e33a9e52f3c0bf01f7 · xlsx

技能一览表.xlsx / V5技能列表 / 第 27 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| D27 | 技能名称 | xlsx |
| E27 | 技能简介 | xlsx表格操作 |
| C（合并继承自 C26；C26:C29） | 原值见锚点 | 文档操作 |
| A（合并继承自 A22；A22:A29） | 原值见锚点 | 老师/学生 |

<a id="entry-a2aa958097a2a8719a76"></a>
### entry-a2aa958097a2a8719a76 · ppt

技能一览表.xlsx / V5技能列表 / 第 28 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| D28 | 技能名称 | ppt |
| E28 | 技能简介 | ppt操作 |
| C（合并继承自 C26；C26:C29） | 原值见锚点 | 文档操作 |
| A（合并继承自 A22；A22:A29） | 原值见锚点 | 老师/学生 |

<a id="entry-d35bc3521570d92bbc7d"></a>
### entry-d35bc3521570d92bbc7d · pdf

技能一览表.xlsx / V5技能列表 / 第 29 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| D29 | 技能名称 | pdf |
| E29 | 技能简介 | pdf操作 |
| C（合并继承自 C26；C26:C29） | 原值见锚点 | 文档操作 |
| A（合并继承自 A22；A22:A29） | 原值见锚点 | 老师/学生 |

<a id="entry-741eb103568fc83d3828"></a>
### entry-741eb103568fc83d3828 · 学情数据

技能一览表.xlsx / V5技能列表 / 第 30 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| E30 | 技能简介 | 学情数据 |

<a id="entry-f55b717d95345d427510"></a>
### entry-f55b717d95345d427510 · 数据分析

技能一览表.xlsx / V5技能列表 / 第 31 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| E31 | 技能简介 | 数据分析 |

<a id="entry-084af90d330a3d04c021"></a>
### entry-084af90d330a3d04c021 · polymas-teacher-homework-skills

技能一览表.xlsx / Agent与Skill列表 / 第 2 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A2 | Agent | 教学活动 Agent |
| B2 | SKILL | 作业 Skill |
| C2 | 标签 | 老师 |
| D2 | skill名称 | polymas-teacher-homework-skills |
| E2 | Skill描述 | 支持作业创建、修改、查询、操作(催交/打回) |
| F2 | 场景样例 | “给今天的课布置一份作业，和上次的配置一样”“查一下这次作业还有哪些同学没交。”“把新能源3班的作业截止时间提前一周” |
| G2 | 功能列表 | 作业创建 |
| H2 | 功能是否具备 | 是 |
| I2 | 负责人 | 刘庆烽 |
| J2 | 是否提测 | 是 |
| K2 | 提测时间 | 0625 |
| L2 | 说明 | 创建流程需优化 |
| M2 | 测试情况 | 通过 |

<a id="entry-36eb68f381e75f906f6e"></a>
### entry-36eb68f381e75f906f6e · polymas-teacher-homework-skills

技能一览表.xlsx / Agent与Skill列表 / 第 3 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| G3 | 功能列表 | 作业编辑 |
| H3 | 功能是否具备 | 是 |
| J3 | 是否提测 | 是 |
| K3 | 提测时间 | 0625 |
| L3 | 说明 | 编辑流程需优化 |
| M3 | 测试情况 | 通过 |
| I（合并继承自 I2；I2:I11） | 原值见锚点 | 刘庆烽 |
| E（合并继承自 E2；E2:E8） | 原值见锚点 | 支持作业创建、修改、查询、操作(催交/打回) |
| F（合并继承自 F2；F2:F8） | 原值见锚点 | “给今天的课布置一份作业，和上次的配置一样”“查一下这次作业还有哪些同学没交。”“把新能源3班的作业截止时间提前一周” |
| B（合并继承自 B2；B2:B8） | 原值见锚点 | 作业 Skill |
| D（合并继承自 D2；D2:D8） | 原值见锚点 | polymas-teacher-homework-skills |
| A（合并继承自 A2；A2:A17） | 原值见锚点 | 教学活动 Agent |
| C（合并继承自 C2；C2:C22） | 原值见锚点 | 老师 |

<a id="entry-71d09955cce5c9966ff0"></a>
### entry-71d09955cce5c9966ff0 · polymas-teacher-homework-skills

技能一览表.xlsx / Agent与Skill列表 / 第 4 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| G4 | 功能列表 | 作业查询 |
| H4 | 功能是否具备 | 是 |
| K4 | 提测时间 | - |
| M4 | 测试情况 | 通过 |
| I（合并继承自 I2；I2:I11） | 原值见锚点 | 刘庆烽 |
| E（合并继承自 E2；E2:E8） | 原值见锚点 | 支持作业创建、修改、查询、操作(催交/打回) |
| F（合并继承自 F2；F2:F8） | 原值见锚点 | “给今天的课布置一份作业，和上次的配置一样”“查一下这次作业还有哪些同学没交。”“把新能源3班的作业截止时间提前一周” |
| B（合并继承自 B2；B2:B8） | 原值见锚点 | 作业 Skill |
| D（合并继承自 D2；D2:D8） | 原值见锚点 | polymas-teacher-homework-skills |
| A（合并继承自 A2；A2:A17） | 原值见锚点 | 教学活动 Agent |
| C（合并继承自 C2；C2:C22） | 原值见锚点 | 老师 |

<a id="entry-3f6e77d9c9e24cf2c992"></a>
### entry-3f6e77d9c9e24cf2c992 · polymas-teacher-homework-skills

技能一览表.xlsx / Agent与Skill列表 / 第 5 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| G5 | 功能列表 | 作业催交 |
| H5 | 功能是否具备 | 是 |
| K5 | 提测时间 | - |
| M5 | 测试情况 | 通过 |
| I（合并继承自 I2；I2:I11） | 原值见锚点 | 刘庆烽 |
| E（合并继承自 E2；E2:E8） | 原值见锚点 | 支持作业创建、修改、查询、操作(催交/打回) |
| F（合并继承自 F2；F2:F8） | 原值见锚点 | “给今天的课布置一份作业，和上次的配置一样”“查一下这次作业还有哪些同学没交。”“把新能源3班的作业截止时间提前一周” |
| B（合并继承自 B2；B2:B8） | 原值见锚点 | 作业 Skill |
| D（合并继承自 D2；D2:D8） | 原值见锚点 | polymas-teacher-homework-skills |
| A（合并继承自 A2；A2:A17） | 原值见锚点 | 教学活动 Agent |
| C（合并继承自 C2；C2:C22） | 原值见锚点 | 老师 |

<a id="entry-7a879870d5980e03abc9"></a>
### entry-7a879870d5980e03abc9 · polymas-teacher-homework-skills

技能一览表.xlsx / Agent与Skill列表 / 第 6 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| G6 | 功能列表 | 作业打回 |
| H6 | 功能是否具备 | 是 |
| K6 | 提测时间 | - |
| M6 | 测试情况 | 没有展示打回原因 |
| I（合并继承自 I2；I2:I11） | 原值见锚点 | 刘庆烽 |
| E（合并继承自 E2；E2:E8） | 原值见锚点 | 支持作业创建、修改、查询、操作(催交/打回) |
| F（合并继承自 F2；F2:F8） | 原值见锚点 | “给今天的课布置一份作业，和上次的配置一样”“查一下这次作业还有哪些同学没交。”“把新能源3班的作业截止时间提前一周” |
| B（合并继承自 B2；B2:B8） | 原值见锚点 | 作业 Skill |
| D（合并继承自 D2；D2:D8） | 原值见锚点 | polymas-teacher-homework-skills |
| A（合并继承自 A2；A2:A17） | 原值见锚点 | 教学活动 Agent |
| C（合并继承自 C2；C2:C22） | 原值见锚点 | 老师 |

<a id="entry-36caceadb388e09a015b"></a>
### entry-36caceadb388e09a015b · polymas-teacher-homework-skills

技能一览表.xlsx / Agent与Skill列表 / 第 7 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| G7 | 功能列表 | 作业分析 |
| H7 | 功能是否具备 | 是 |
| K7 | 提测时间 | - |
| M7 | 测试情况 | 系统分析拉取不到 |
| I（合并继承自 I2；I2:I11） | 原值见锚点 | 刘庆烽 |
| E（合并继承自 E2；E2:E8） | 原值见锚点 | 支持作业创建、修改、查询、操作(催交/打回) |
| F（合并继承自 F2；F2:F8） | 原值见锚点 | “给今天的课布置一份作业，和上次的配置一样”“查一下这次作业还有哪些同学没交。”“把新能源3班的作业截止时间提前一周” |
| B（合并继承自 B2；B2:B8） | 原值见锚点 | 作业 Skill |
| D（合并继承自 D2；D2:D8） | 原值见锚点 | polymas-teacher-homework-skills |
| A（合并继承自 A2；A2:A17） | 原值见锚点 | 教学活动 Agent |
| C（合并继承自 C2；C2:C22） | 原值见锚点 | 老师 |

<a id="entry-3215eda53c36b3949564"></a>
### entry-3215eda53c36b3949564 · polymas-teacher-homework-skills

技能一览表.xlsx / Agent与Skill列表 / 第 8 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| G8 | 功能列表 | 作业互动交流分析 |
| H8 | 功能是否具备 | 是 |
| K8 | 提测时间 | - |
| M8 | 测试情况 | 互动交流拉取不到 |
| I（合并继承自 I2；I2:I11） | 原值见锚点 | 刘庆烽 |
| E（合并继承自 E2；E2:E8） | 原值见锚点 | 支持作业创建、修改、查询、操作(催交/打回) |
| F（合并继承自 F2；F2:F8） | 原值见锚点 | “给今天的课布置一份作业，和上次的配置一样”“查一下这次作业还有哪些同学没交。”“把新能源3班的作业截止时间提前一周” |
| B（合并继承自 B2；B2:B8） | 原值见锚点 | 作业 Skill |
| D（合并继承自 D2；D2:D8） | 原值见锚点 | polymas-teacher-homework-skills |
| A（合并继承自 A2；A2:A17） | 原值见锚点 | 教学活动 Agent |
| C（合并继承自 C2；C2:C22） | 原值见锚点 | 老师 |

<a id="entry-88f4805a08b55a55a80d"></a>
### entry-88f4805a08b55a55a80d · polymas-teacher-exam-skills

技能一览表.xlsx / Agent与Skill列表 / 第 9 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B9 | SKILL | 考试 Skill |
| D9 | skill名称 | polymas-teacher-exam-skills |
| E9 | Skill描述 | 支持考试或测验的创建、查<br>询、编辑 |
| F9 | 场景样例 | “帮我创建一场期中考试，时长90分钟，覆盖前六章内容。”“把这次期末考试的截止时间改到下周五晚上10点。”“帮我看一下《管理学》这门课目前有哪些考试安排。” |
| G9 | 功能列表 | 考试/测验创建 |
| H9 | 功能是否具备 | 是 |
| J9 | 是否提测 | 是 |
| K9 | 提测时间 | 0625 |
| L9 | 说明 | 做个小工具 |
| M9 | 测试情况 | 只是生成了试卷，没有创建考试 |
| I（合并继承自 I2；I2:I11） | 原值见锚点 | 刘庆烽 |
| A（合并继承自 A2；A2:A17） | 原值见锚点 | 教学活动 Agent |
| C（合并继承自 C2；C2:C22） | 原值见锚点 | 老师 |

<a id="entry-d5f8dd569e7c40fdbb98"></a>
### entry-d5f8dd569e7c40fdbb98 · polymas-teacher-exam-skills

技能一览表.xlsx / Agent与Skill列表 / 第 10 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| G10 | 功能列表 | 考试/测验编辑 |
| H10 | 功能是否具备 | 是 |
| J10 | 是否提测 | 是 |
| K10 | 提测时间 | 0625 |
| M10 | 测试情况 | 通过 |
| B（合并继承自 B9；B9:B11） | 原值见锚点 | 考试 Skill |
| E（合并继承自 E9；E9:E11） | 原值见锚点 | 支持考试或测验的创建、查<br>询、编辑 |
| F（合并继承自 F9；F9:F11） | 原值见锚点 | “帮我创建一场期中考试，时长90分钟，覆盖前六章内容。”“把这次期末考试的截止时间改到下周五晚上10点。”“帮我看一下《管理学》这门课目前有哪些考试安排。” |
| L（合并继承自 L9；L9:L11） | 原值见锚点 | 做个小工具 |
| I（合并继承自 I2；I2:I11） | 原值见锚点 | 刘庆烽 |
| D（合并继承自 D9；D9:D11） | 原值见锚点 | polymas-teacher-exam-skills |
| A（合并继承自 A2；A2:A17） | 原值见锚点 | 教学活动 Agent |
| C（合并继承自 C2；C2:C22） | 原值见锚点 | 老师 |

<a id="entry-f57d059150bc1df05ddf"></a>
### entry-f57d059150bc1df05ddf · polymas-teacher-exam-skills

技能一览表.xlsx / Agent与Skill列表 / 第 11 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| G11 | 功能列表 | 考试/测验查询 |
| H11 | 功能是否具备 | 是 |
| J11 | 是否提测 | 是 |
| K11 | 提测时间 | 0624 |
| M11 | 测试情况 | 通过 |
| B（合并继承自 B9；B9:B11） | 原值见锚点 | 考试 Skill |
| E（合并继承自 E9；E9:E11） | 原值见锚点 | 支持考试或测验的创建、查<br>询、编辑 |
| F（合并继承自 F9；F9:F11） | 原值见锚点 | “帮我创建一场期中考试，时长90分钟，覆盖前六章内容。”“把这次期末考试的截止时间改到下周五晚上10点。”“帮我看一下《管理学》这门课目前有哪些考试安排。” |
| L（合并继承自 L9；L9:L11） | 原值见锚点 | 做个小工具 |
| I（合并继承自 I2；I2:I11） | 原值见锚点 | 刘庆烽 |
| D（合并继承自 D9；D9:D11） | 原值见锚点 | polymas-teacher-exam-skills |
| A（合并继承自 A2；A2:A17） | 原值见锚点 | 教学活动 Agent |
| C（合并继承自 C2；C2:C22） | 原值见锚点 | 老师 |

<a id="entry-e63bf1361c94b22c5927"></a>
### entry-e63bf1361c94b22c5927 · polymas-teacher-score-skills

技能一览表.xlsx / Agent与Skill列表 / 第 12 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B12 | SKILL | 成绩Skill |
| D12 | skill名称 | polymas-teacher-score-skills |
| E12 | Skill描述 | 支持成绩查询、汇总、计算<br>和导出 |
| F12 | 场景样例 | “帮我把这学期所有作业和考试成绩汇总一下。”“把每个班级的成绩导出一张表给我。”“帮我算一下每个同学的平时分，作业占60%，考试占40%。”“看看这次新能源1班的作业成绩情况”<br> |
| G12 | 功能列表 | 成绩查询 |
| H12 | 功能是否具备 | 是 |
| I12 | 负责人 | 赵洪恩 |
| K12 | 提测时间 | 0626 |
| M12 | 测试情况 | 通过，但目前都是假数据 |
| A（合并继承自 A2；A2:A17） | 原值见锚点 | 教学活动 Agent |
| C（合并继承自 C2；C2:C22） | 原值见锚点 | 老师 |

<a id="entry-1759063e6f4dc997daf8"></a>
### entry-1759063e6f4dc997daf8 · polymas-teacher-score-skills

技能一览表.xlsx / Agent与Skill列表 / 第 13 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| G13 | 功能列表 | 成绩汇总 |
| H13 | 功能是否具备 | 是 |
| M13 | 测试情况 | 通过，但目前都是假数据 |
| B（合并继承自 B12；B12:B14） | 原值见锚点 | 成绩Skill |
| E（合并继承自 E12；E12:E14） | 原值见锚点 | 支持成绩查询、汇总、计算<br>和导出 |
| F（合并继承自 F12；F12:F14） | 原值见锚点 | “帮我把这学期所有作业和考试成绩汇总一下。”“把每个班级的成绩导出一张表给我。”“帮我算一下每个同学的平时分，作业占60%，考试占40%。”“看看这次新能源1班的作业成绩情况”<br> |
| K（合并继承自 K12；K12:K14） | 原值见锚点 | 0626 |
| D（合并继承自 D12；D12:D14） | 原值见锚点 | polymas-teacher-score-skills |
| I（合并继承自 I12；I12:I22） | 原值见锚点 | 赵洪恩 |
| A（合并继承自 A2；A2:A17） | 原值见锚点 | 教学活动 Agent |
| C（合并继承自 C2；C2:C22） | 原值见锚点 | 老师 |

<a id="entry-0b1971e8a937050d17ec"></a>
### entry-0b1971e8a937050d17ec · polymas-teacher-score-skills

技能一览表.xlsx / Agent与Skill列表 / 第 14 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| G14 | 功能列表 | 成绩计算 |
| H14 | 功能是否具备 | 是 |
| M14 | 测试情况 | 通过，但目前都是假数据 |
| B（合并继承自 B12；B12:B14） | 原值见锚点 | 成绩Skill |
| E（合并继承自 E12；E12:E14） | 原值见锚点 | 支持成绩查询、汇总、计算<br>和导出 |
| F（合并继承自 F12；F12:F14） | 原值见锚点 | “帮我把这学期所有作业和考试成绩汇总一下。”“把每个班级的成绩导出一张表给我。”“帮我算一下每个同学的平时分，作业占60%，考试占40%。”“看看这次新能源1班的作业成绩情况”<br> |
| K（合并继承自 K12；K12:K14） | 原值见锚点 | 0626 |
| D（合并继承自 D12；D12:D14） | 原值见锚点 | polymas-teacher-score-skills |
| I（合并继承自 I12；I12:I22） | 原值见锚点 | 赵洪恩 |
| A（合并继承自 A2；A2:A17） | 原值见锚点 | 教学活动 Agent |
| C（合并继承自 C2；C2:C22） | 原值见锚点 | 老师 |

<a id="entry-5322e28552ed8de85649"></a>
### entry-5322e28552ed8de85649 · polymas-teacher-activity-skills

技能一览表.xlsx / Agent与Skill列表 / 第 15 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B15 | SKILL | 通知讨论 Skill |
| D15 | skill名称 | polymas-teacher-activity-skills |
| E15 | Skill描述 | 支持面向课程、班级、学生<br>的消息发布与讨论管理 |
| F15 | 场景样例 | “帮我给全班发一条通知，提醒明天下午有期末考试。”“把下周课程调整的安排通知到所有选课学生。”“帮我看看最近讨论区里学生都在问什么问题。” |
| G15 | 功能列表 | 消息/讨论发布 |
| H15 | 功能是否具备 | 是 |
| K15 | 提测时间 | 0625<br> |
| L15 | 说明 | 走一下辉哥的平台 |
| M15 | 测试情况 | 通过 |
| I（合并继承自 I12；I12:I22） | 原值见锚点 | 赵洪恩 |
| A（合并继承自 A2；A2:A17） | 原值见锚点 | 教学活动 Agent |
| C（合并继承自 C2；C2:C22） | 原值见锚点 | 老师 |

<a id="entry-17f2b0237b4fa297cce5"></a>
### entry-17f2b0237b4fa297cce5 · polymas-teacher-activity-skills

技能一览表.xlsx / Agent与Skill列表 / 第 16 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| G16 | 功能列表 | 消息/讨论查看 |
| H16 | 功能是否具备 | 是 |
| M16 | 测试情况 | 通过 |
| B（合并继承自 B15；B15:B17） | 原值见锚点 | 通知讨论 Skill |
| E（合并继承自 E15；E15:E17） | 原值见锚点 | 支持面向课程、班级、学生<br>的消息发布与讨论管理 |
| F（合并继承自 F15；F15:F17） | 原值见锚点 | “帮我给全班发一条通知，提醒明天下午有期末考试。”“把下周课程调整的安排通知到所有选课学生。”“帮我看看最近讨论区里学生都在问什么问题。” |
| K（合并继承自 K15；K15:K17） | 原值见锚点 | 0625<br> |
| L（合并继承自 L15；L15:L17） | 原值见锚点 | 走一下辉哥的平台 |
| D（合并继承自 D15；D15:D17） | 原值见锚点 | polymas-teacher-activity-skills |
| I（合并继承自 I12；I12:I22） | 原值见锚点 | 赵洪恩 |
| A（合并继承自 A2；A2:A17） | 原值见锚点 | 教学活动 Agent |
| C（合并继承自 C2；C2:C22） | 原值见锚点 | 老师 |

<a id="entry-60fc22220b5c0452061f"></a>
### entry-60fc22220b5c0452061f · polymas-teacher-activity-skills

技能一览表.xlsx / Agent与Skill列表 / 第 17 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| G17 | 功能列表 | 消息/讨论分析 |
| H17 | 功能是否具备 | 是 |
| B（合并继承自 B15；B15:B17） | 原值见锚点 | 通知讨论 Skill |
| E（合并继承自 E15；E15:E17） | 原值见锚点 | 支持面向课程、班级、学生<br>的消息发布与讨论管理 |
| F（合并继承自 F15；F15:F17） | 原值见锚点 | “帮我给全班发一条通知，提醒明天下午有期末考试。”“把下周课程调整的安排通知到所有选课学生。”“帮我看看最近讨论区里学生都在问什么问题。” |
| K（合并继承自 K15；K15:K17） | 原值见锚点 | 0625<br> |
| L（合并继承自 L15；L15:L17） | 原值见锚点 | 走一下辉哥的平台 |
| D（合并继承自 D15；D15:D17） | 原值见锚点 | polymas-teacher-activity-skills |
| I（合并继承自 I12；I12:I22） | 原值见锚点 | 赵洪恩 |
| A（合并继承自 A2；A2:A17） | 原值见锚点 | 教学活动 Agent |
| C（合并继承自 C2；C2:C22） | 原值见锚点 | 老师 |

<a id="entry-0f29867d788f6bb8ec49"></a>
### entry-0f29867d788f6bb8ec49 · polymas-teacher-problem-skills

技能一览表.xlsx / Agent与Skill列表 / 第 18 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A18 | Agent | 备课Agent |
| B18 | SKILL | 出题 Skill |
| D18 | skill名称 | polymas-teacher-problem-skills |
| E18 | Skill描述 | 根据知识点、难度、题型生成题目 |
| F18 | 场景样例 | “帮我出5道关于供需关系的选择题，难度中等。”“给’财务报表分析’这个知识点出3道综合分析题。”“帮我出一道适合期末考试用的案例分析题，附上参考答案和评分标准。”“我下周要随堂测验，帮我出10道判断题考第二章的内容。” |
| G18 | 功能列表 | 题目生成 |
| H18 | 功能是否具备 | 是 |
| K18 | 提测时间 | 0630 |
| I（合并继承自 I12；I12:I22） | 原值见锚点 | 赵洪恩 |
| C（合并继承自 C2；C2:C22） | 原值见锚点 | 老师 |

<a id="entry-a44d8cd8f0be36969f16"></a>
### entry-a44d8cd8f0be36969f16 · polymas-teacher-case-skills

技能一览表.xlsx / Agent与Skill列表 / 第 19 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B19 | SKILL | 案例 Skill |
| D19 | skill名称 | polymas-teacher-case-skills |
| E19 | Skill描述 | 根据课程内容生成教学案例 |
| F19 | 场景样例 | “帮我找一个关于品牌定位失败的真实商业案例，用于课堂讨论。”“给’规模经济’这个概念设计一个学生容易理解的生活化案例。”“我下节课讲供应链管理，帮我准备一个近两年的行业案例。” |
| G19 | 功能列表 | 教案生成 |
| H19 | 功能是否具备 | 是 |
| K19 | 提测时间 | 0630 |
| A（合并继承自 A18；A18:A22） | 原值见锚点 | 备课Agent |
| I（合并继承自 I12；I12:I22） | 原值见锚点 | 赵洪恩 |
| C（合并继承自 C2；C2:C22） | 原值见锚点 | 老师 |

<a id="entry-b96442a90e0cb7b42512"></a>
### entry-b96442a90e0cb7b42512 · polymas-teacher-lesson-design

技能一览表.xlsx / Agent与Skill列表 / 第 20 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B20 | SKILL | 课堂设计 Skill |
| D20 | skill名称 | polymas-teacher-lesson-design |
| E20 | Skill描述 | 设计课堂教学流程和互动环节 |
| F20 | 场景样例 | “帮我设计下节课的课堂流程，要有互动环节和案例引入。”“这节课我想让学生分组讨论，帮我设计一个小组活动方案。”“下节课我想用OBE教学，给我设计一下” |
| G20 | 功能列表 | 课堂设计 |
| H20 | 功能是否具备 | 是 |
| K20 | 提测时间 | 46204 |
| A（合并继承自 A18；A18:A22） | 原值见锚点 | 备课Agent |
| I（合并继承自 I12；I12:I22） | 原值见锚点 | 赵洪恩 |
| C（合并继承自 C2；C2:C22） | 原值见锚点 | 老师 |

<a id="entry-3fc8aa3e2ece333eb3bb"></a>
### entry-3fc8aa3e2ece333eb3bb · polymas-teacher-analogy-skills

技能一览表.xlsx / Agent与Skill列表 / 第 21 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B21 | SKILL | 概念类比 Skill |
| D21 | skill名称 | polymas-teacher-analogy-skills |
| E21 | Skill描述 | 将抽象概念转化为类比、<br>例子或反例 |
| F21 | 场景样例 | “边际成本怎么跟本科生解释比较好懂？”“帮我用生活中的例子解释一下’机会成本’”“帮我把’货币时间价值’的原理用类比的方式解释一遍。” |
| G21 | 功能列表 | 概念解释 |
| H21 | 功能是否具备 | 是 |
| K21 | 提测时间 | 6/29 |
| A（合并继承自 A18；A18:A22） | 原值见锚点 | 备课Agent |
| I（合并继承自 I12；I12:I22） | 原值见锚点 | 赵洪恩 |
| C（合并继承自 C2；C2:C22） | 原值见锚点 | 老师 |

<a id="entry-cc40133891e1fb2bf5f2"></a>
### entry-cc40133891e1fb2bf5f2 · polymas-teacher-content-creation

技能一览表.xlsx / Agent与Skill列表 / 第 22 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B22 | SKILL | 内容创作 Skill |
| D22 | skill名称 | polymas-teacher-content-creation |
| E22 | Skill描述 | 生成备课相关文本内容 |
| F22 | 场景样例 | “帮我写一份第五章的教案，教学目标是让学生掌握三个核心模型。”“帮我生成一份期末复习提纲，覆盖全学期的重点知识。”“帮我写一段课堂讲稿，用于介绍本节课的背景和学习目标。”“帮我把下节课的资料做成一个PPT” |
| G22 | 功能列表 | 备课内容生成 |
| H22 | 功能是否具备 | 是 |
| K22 | 提测时间 | 7/01 |
| A（合并继承自 A18；A18:A22） | 原值见锚点 | 备课Agent |
| I（合并继承自 I12；I12:I22） | 原值见锚点 | 赵洪恩 |
| C（合并继承自 C2；C2:C22） | 原值见锚点 | 老师 |

<a id="entry-7d7d852bcd980b7d7bfd"></a>
### entry-7d7d852bcd980b7d7bfd · TODO

技能一览表.xlsx / Agent与Skill列表 / 第 23 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A23 | Agent | 学课管理 Agent |
| B23 | SKILL | 学生管理 Skill |
| D23 | skill名称 | TODO |
| E23 | Skill描述 | 管理学生信息、学习状态和个体画像 |
| F23 | 场景样例 | “帮我看看李明最近的学习情况，作业和考试都怎么样？”“班里有哪些同学存在挂科风险，我想重点跟进。”“给学习比较吃力的同学推荐一些补充学习资料。”“帮我整理一下这个同学这学期的学习轨迹。” |
| G23 | 功能列表 | 学生信息查询 |
| H23 | 功能是否具备 | 是 |
| I23 | 负责人 | 刘庆烽 |
| K23 | 提测时间 | - |

<a id="entry-32fd8733de57f82e0bf9"></a>
### entry-32fd8733de57f82e0bf9 · TODO

技能一览表.xlsx / Agent与Skill列表 / 第 24 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| G24 | 功能列表 | 学生学习状态查询 |
| H24 | 功能是否具备 | 否 |
| K24 | 提测时间 | - |
| L24 | 说明 | 移动至学情分析 |
| B（合并继承自 B23；B23:B25） | 原值见锚点 | 学生管理 Skill |
| E（合并继承自 E23；E23:E25） | 原值见锚点 | 管理学生信息、学习状态和个体画像 |
| F（合并继承自 F23；F23:F25） | 原值见锚点 | “帮我看看李明最近的学习情况，作业和考试都怎么样？”“班里有哪些同学存在挂科风险，我想重点跟进。”“给学习比较吃力的同学推荐一些补充学习资料。”“帮我整理一下这个同学这学期的学习轨迹。” |
| D（合并继承自 D23；D23:D25） | 原值见锚点 | TODO |
| I（合并继承自 I23；I23:I37） | 原值见锚点 | 刘庆烽 |
| A（合并继承自 A23；A23:A31） | 原值见锚点 | 学课管理 Agent |

<a id="entry-f0f703845ef0957bea44"></a>
### entry-f0f703845ef0957bea44 · TODO

技能一览表.xlsx / Agent与Skill列表 / 第 25 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| G25 | 功能列表 | 学生画像查询 |
| H25 | 功能是否具备 | 否 |
| K25 | 提测时间 | - |
| B（合并继承自 B23；B23:B25） | 原值见锚点 | 学生管理 Skill |
| E（合并继承自 E23；E23:E25） | 原值见锚点 | 管理学生信息、学习状态和个体画像 |
| F（合并继承自 F23；F23:F25） | 原值见锚点 | “帮我看看李明最近的学习情况，作业和考试都怎么样？”“班里有哪些同学存在挂科风险，我想重点跟进。”“给学习比较吃力的同学推荐一些补充学习资料。”“帮我整理一下这个同学这学期的学习轨迹。” |
| L（合并继承自 L24；L24:L25） | 原值见锚点 | 移动至学情分析 |
| D（合并继承自 D23；D23:D25） | 原值见锚点 | TODO |
| I（合并继承自 I23；I23:I37） | 原值见锚点 | 刘庆烽 |
| A（合并继承自 A23；A23:A31） | 原值见锚点 | 学课管理 Agent |

<a id="entry-e29e614ce446eafa1b67"></a>
### entry-e29e614ce446eafa1b67 · polymas-teacher-class-skills

技能一览表.xlsx / Agent与Skill列表 / 第 26 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B26 | SKILL | 班级管理 Skill |
| D26 | skill名称 | polymas-teacher-class-skills |
| E26 | Skill描述 | 管理班级信息和班级成员 |
| F26 | 场景样例 | “帮我新建一个2024级市场营销1班。”“把这份学生名单导入到班级里。”“帮我查一下这个班现在有多少人，有没有退课的？” |
| G26 | 功能列表 | 班级查询 |
| H26 | 功能是否具备 | 是 |
| K26 | 提测时间 | - |
| M26 | 测试情况 | 通过 |
| I（合并继承自 I23；I23:I37） | 原值见锚点 | 刘庆烽 |
| A（合并继承自 A23；A23:A31） | 原值见锚点 | 学课管理 Agent |

<a id="entry-ba452cce3ff980ef417e"></a>
### entry-ba452cce3ff980ef417e · polymas-teacher-class-skills

技能一览表.xlsx / Agent与Skill列表 / 第 27 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| G27 | 功能列表 | 班级学生查询 |
| H27 | 功能是否具备 | 是 |
| K27 | 提测时间 | - |
| M27 | 测试情况 | 通过 |
| E（合并继承自 E26；E26:E28） | 原值见锚点 | 管理班级信息和班级成员 |
| B（合并继承自 B26；B26:B28） | 原值见锚点 | 班级管理 Skill |
| F（合并继承自 F26；F26:F28） | 原值见锚点 | “帮我新建一个2024级市场营销1班。”“把这份学生名单导入到班级里。”“帮我查一下这个班现在有多少人，有没有退课的？” |
| D（合并继承自 D26；D26:D28） | 原值见锚点 | polymas-teacher-class-skills |
| I（合并继承自 I23；I23:I37） | 原值见锚点 | 刘庆烽 |
| A（合并继承自 A23；A23:A31） | 原值见锚点 | 学课管理 Agent |

<a id="entry-dbf432c40aa36c755222"></a>
### entry-dbf432c40aa36c755222 · polymas-teacher-class-skills

技能一览表.xlsx / Agent与Skill列表 / 第 28 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| G28 | 功能列表 | 班级创建/导入 |
| H28 | 功能是否具备 | 是 |
| K28 | 提测时间 | 0630 |
| M28 | 测试情况 | 通过 |
| E（合并继承自 E26；E26:E28） | 原值见锚点 | 管理班级信息和班级成员 |
| B（合并继承自 B26；B26:B28） | 原值见锚点 | 班级管理 Skill |
| F（合并继承自 F26；F26:F28） | 原值见锚点 | “帮我新建一个2024级市场营销1班。”“把这份学生名单导入到班级里。”“帮我查一下这个班现在有多少人，有没有退课的？” |
| D（合并继承自 D26；D26:D28） | 原值见锚点 | polymas-teacher-class-skills |
| I（合并继承自 I23；I23:I37） | 原值见锚点 | 刘庆烽 |
| A（合并继承自 A23；A23:A31） | 原值见锚点 | 学课管理 Agent |

<a id="entry-58bc5b4a6bfededbd38d"></a>
### entry-58bc5b4a6bfededbd38d · polymas-teacher-course-skills

技能一览表.xlsx / Agent与Skill列表 / 第 29 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B29 | SKILL | 课程管理 Skill |
| D29 | skill名称 | polymas-teacher-course-skills |
| E29 | Skill描述 | 管理课程基础信息和课程上下文 |
| F29 | 场景样例 | “帮我创建一门《管理学原理》，下学期开课。”“帮我查一下这门课目前有哪些班级在选。”“把这份参考教材关联到课程资料里。” |
| G29 | 功能列表 | 课程创建 |
| H29 | 功能是否具备 | 是 |
| K29 | 提测时间 | 0630 |
| M29 | 测试情况 | 通过 |
| I（合并继承自 I23；I23:I37） | 原值见锚点 | 刘庆烽 |
| A（合并继承自 A23；A23:A31） | 原值见锚点 | 学课管理 Agent |

<a id="entry-72d3a6b803e27a71c68c"></a>
### entry-72d3a6b803e27a71c68c · polymas-teacher-course-skills

技能一览表.xlsx / Agent与Skill列表 / 第 30 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| G30 | 功能列表 | 课程查询 |
| H30 | 功能是否具备 | 是 |
| K30 | 提测时间 | - |
| M30 | 测试情况 | 通过 |
| B（合并继承自 B29；B29:B30） | 原值见锚点 | 课程管理 Skill |
| E（合并继承自 E29；E29:E30） | 原值见锚点 | 管理课程基础信息和课程上下文 |
| F（合并继承自 F29；F29:F30） | 原值见锚点 | “帮我创建一门《管理学原理》，下学期开课。”“帮我查一下这门课目前有哪些班级在选。”“把这份参考教材关联到课程资料里。” |
| D（合并继承自 D29；D29:D30） | 原值见锚点 | polymas-teacher-course-skills |
| I（合并继承自 I23；I23:I37） | 原值见锚点 | 刘庆烽 |
| A（合并继承自 A23；A23:A31） | 原值见锚点 | 学课管理 Agent |

<a id="entry-8358bb041955ba87374a"></a>
### entry-8358bb041955ba87374a · polymas-query-teaching-unit

技能一览表.xlsx / Agent与Skill列表 / 第 31 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B31 | SKILL | 教学计划 Skill |
| D31 | skill名称 | polymas-query-teaching-unit |
| E31 | Skill描述 | 教学计划查询 |
| F31 | 场景样例 | 教学计划查询 |
| G31 | 功能列表 | 教学计划查询 |
| H31 | 功能是否具备 | 是 |
| I（合并继承自 I23；I23:I37） | 原值见锚点 | 刘庆烽 |
| A（合并继承自 A23；A23:A31） | 原值见锚点 | 学课管理 Agent |

<a id="entry-93abb2050efd60c1efce"></a>
### entry-93abb2050efd60c1efce · polymas-teacher-resource-skills

技能一览表.xlsx / Agent与Skill列表 / 第 32 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A32 | Agent | 资源管理 Agent |
| B32 | SKILL | 资源库管理 Skill |
| D32 | skill名称 | polymas-teacher-resource-skills |
| E32 | Skill描述 | 管理个人、课程、团队资源库 |
| F32 | 场景样例 | “帮我把这份PPT上传到《会计学》课程的资料库里。”“我之前上传过一份关于SWOT分析的文档，帮我找一下。”“帮我找到下节课相关的资料，并且生成一个便于讲解的HTML” |
| G32 | 功能列表 | 资源库查询 |
| H32 | 功能是否具备 | 是 |
| K32 | 提测时间 | - |
| I（合并继承自 I23；I23:I37） | 原值见锚点 | 刘庆烽 |

<a id="entry-c11b9ad4118da4364d3d"></a>
### entry-c11b9ad4118da4364d3d · polymas-teacher-resource-skills

技能一览表.xlsx / Agent与Skill列表 / 第 33 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| G33 | 功能列表 | 资源库同步 |
| H33 | 功能是否具备 | 是 |
| J33 | 是否提测 | 是 |
| K33 | 提测时间 | 0701 |
| E（合并继承自 E32；E32:E33） | 原值见锚点 | 管理个人、课程、团队资源库 |
| F（合并继承自 F32；F32:F33） | 原值见锚点 | “帮我把这份PPT上传到《会计学》课程的资料库里。”“我之前上传过一份关于SWOT分析的文档，帮我找一下。”“帮我找到下节课相关的资料，并且生成一个便于讲解的HTML” |
| B（合并继承自 B32；B32:B33） | 原值见锚点 | 资源库管理 Skill |
| A（合并继承自 A32；A32:A37） | 原值见锚点 | 资源管理 Agent |
| D（合并继承自 D32；D32:D33） | 原值见锚点 | polymas-teacher-resource-skills |
| I（合并继承自 I23；I23:I37） | 原值见锚点 | 刘庆烽 |

<a id="entry-3f3d80fbafa2553130ed"></a>
### entry-3f3d80fbafa2553130ed · 和产品对一下

技能一览表.xlsx / Agent与Skill列表 / 第 34 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B34 | SKILL | 问答对管理 Skill |
| D34 | skill名称 | 和产品对一下 |
| E34 | Skill描述 | 管理课程知识库中的问答对 |
| F34 | 场景样例 | “查一下知识库里有没有关于现金流量表的问答。”<br>“把刚才那条问答的答案更新一下，原来写的不够准确。”“将《高等数学》这门课学生的问题和回答进行归类总结发给我看看” |
| G34 | 功能列表 | 问答内容查询 |
| H34 | 功能是否具备 | 否 |
| A（合并继承自 A32；A32:A37） | 原值见锚点 | 资源管理 Agent |
| I（合并继承自 I23；I23:I37） | 原值见锚点 | 刘庆烽 |

<a id="entry-1c28c2bcd36e3df4d293"></a>
### entry-1c28c2bcd36e3df4d293 · 和产品对一下

技能一览表.xlsx / Agent与Skill列表 / 第 35 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| G35 | 功能列表 | 问答内容更新 |
| H35 | 功能是否具备 | 否 |
| B（合并继承自 B34；B34:B35） | 原值见锚点 | 问答对管理 Skill |
| E（合并继承自 E34；E34:E35） | 原值见锚点 | 管理课程知识库中的问答对 |
| F（合并继承自 F34；F34:F35） | 原值见锚点 | “查一下知识库里有没有关于现金流量表的问答。”<br>“把刚才那条问答的答案更新一下，原来写的不够准确。”“将《高等数学》这门课学生的问题和回答进行归类总结发给我看看” |
| A（合并继承自 A32；A32:A37） | 原值见锚点 | 资源管理 Agent |
| D（合并继承自 D34；D34:D35） | 原值见锚点 | 和产品对一下 |
| I（合并继承自 I23；I23:I37） | 原值见锚点 | 刘庆烽 |

<a id="entry-21bcc3863be783e9e31f"></a>
### entry-21bcc3863be783e9e31f · polymas-teacher-questionbank-skills

技能一览表.xlsx / Agent与Skill列表 / 第 36 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B36 | SKILL | 题库管理 Skill |
| D36 | skill名称 | polymas-teacher-questionbank-skills |
| E36 | Skill描述 | 管理课程题目和题库资源 |
| F36 | 场景样例 | “把我刚才生成的那5道题存到《财务管理》题库里。”“帮我从题库里找10道关于成本核算的中等难度题目。”“把这批题目批量导入到题库里。”“帮我查一下题库里目前有多少道关于’资本结构’的题目。 |
| G36 | 功能列表 | 题目查询 |
| H36 | 功能是否具备 | 是 |
| K36 | 提测时间 | 0702 |
| A（合并继承自 A32；A32:A37） | 原值见锚点 | 资源管理 Agent |
| I（合并继承自 I23；I23:I37） | 原值见锚点 | 刘庆烽 |

<a id="entry-a59faa71003967ffa1be"></a>
### entry-a59faa71003967ffa1be · polymas-teacher-questionbank-skills

技能一览表.xlsx / Agent与Skill列表 / 第 37 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| G37 | 功能列表 | 题库同步 |
| H37 | 功能是否具备 | 是 |
| K37 | 提测时间 | 0702 |
| B（合并继承自 B36；B36:B37） | 原值见锚点 | 题库管理 Skill |
| E（合并继承自 E36；E36:E37） | 原值见锚点 | 管理课程题目和题库资源 |
| A（合并继承自 A32；A32:A37） | 原值见锚点 | 资源管理 Agent |
| F（合并继承自 F36；F36:F37） | 原值见锚点 | “把我刚才生成的那5道题存到《财务管理》题库里。”“帮我从题库里找10道关于成本核算的中等难度题目。”“把这批题目批量导入到题库里。”“帮我查一下题库里目前有多少道关于’资本结构’的题目。 |
| I（合并继承自 I23；I23:I37） | 原值见锚点 | 刘庆烽 |
| D（合并继承自 D36；D36:D37） | 原值见锚点 | polymas-teacher-questionbank-skills |

<a id="entry-841bb61d254be4583895"></a>
### entry-841bb61d254be4583895 · schedule-meeting

技能一览表.xlsx / Agent与Skill列表 / 第 38 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A38 | Agent | 会议日程管理 Agent |
| B38 | SKILL | 会议管理 Skill |
| D38 | skill名称 | schedule-meeting |
| E38 | Skill描述 | 管理会议创建、修改、取消和纪要 |
| F38 | 场景样例 | “帮我安排一个下周三下午3点的教研组会议，参会人发给你。”“把明天的组会取消掉，通知一下所有参会人。”“帮我整理一下上次教研会议的纪要。”“把下周的会议时间改到周四上午10点。” |
| G38 | 功能列表 | 会议创建 |
| H38 | 功能是否具备 | 是 |
| I38 | 负责人 | 洪恩 |
| K38 | 提测时间 | - |

<a id="entry-80c1142e563ae0ed2ce8"></a>
### entry-80c1142e563ae0ed2ce8 · schedule-meeting

技能一览表.xlsx / Agent与Skill列表 / 第 39 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| G39 | 功能列表 | 会议取消 |
| H39 | 功能是否具备 | 是 |
| K39 | 提测时间 | - |
| F（合并继承自 F38；F38:F41） | 原值见锚点 | “帮我安排一个下周三下午3点的教研组会议，参会人发给你。”“把明天的组会取消掉，通知一下所有参会人。”“帮我整理一下上次教研会议的纪要。”“把下周的会议时间改到周四上午10点。” |
| E（合并继承自 E38；E38:E41） | 原值见锚点 | 管理会议创建、修改、取消和纪要 |
| B（合并继承自 B38；B38:B41） | 原值见锚点 | 会议管理 Skill |
| A（合并继承自 A38；A38:A44） | 原值见锚点 | 会议日程管理 Agent |
| I（合并继承自 I38；I38:I45） | 原值见锚点 | 洪恩 |
| D（合并继承自 D38；D38:D41） | 原值见锚点 | schedule-meeting |

<a id="entry-29c0c39e42420695b844"></a>
### entry-29c0c39e42420695b844 · schedule-meeting

技能一览表.xlsx / Agent与Skill列表 / 第 40 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| G40 | 功能列表 | 会议查询 |
| H40 | 功能是否具备 | 是 |
| K40 | 提测时间 | - |
| F（合并继承自 F38；F38:F41） | 原值见锚点 | “帮我安排一个下周三下午3点的教研组会议，参会人发给你。”“把明天的组会取消掉，通知一下所有参会人。”“帮我整理一下上次教研会议的纪要。”“把下周的会议时间改到周四上午10点。” |
| E（合并继承自 E38；E38:E41） | 原值见锚点 | 管理会议创建、修改、取消和纪要 |
| B（合并继承自 B38；B38:B41） | 原值见锚点 | 会议管理 Skill |
| A（合并继承自 A38；A38:A44） | 原值见锚点 | 会议日程管理 Agent |
| I（合并继承自 I38；I38:I45） | 原值见锚点 | 洪恩 |
| D（合并继承自 D38；D38:D41） | 原值见锚点 | schedule-meeting |

<a id="entry-a6c9282f68a57ea0219e"></a>
### entry-a6c9282f68a57ea0219e · schedule-meeting

技能一览表.xlsx / Agent与Skill列表 / 第 41 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| G41 | 功能列表 | 会议纪要 |
| H41 | 功能是否具备 | 是 |
| K41 | 提测时间 | 0706 |
| F（合并继承自 F38；F38:F41） | 原值见锚点 | “帮我安排一个下周三下午3点的教研组会议，参会人发给你。”“把明天的组会取消掉，通知一下所有参会人。”“帮我整理一下上次教研会议的纪要。”“把下周的会议时间改到周四上午10点。” |
| E（合并继承自 E38；E38:E41） | 原值见锚点 | 管理会议创建、修改、取消和纪要 |
| B（合并继承自 B38；B38:B41） | 原值见锚点 | 会议管理 Skill |
| A（合并继承自 A38；A38:A44） | 原值见锚点 | 会议日程管理 Agent |
| I（合并继承自 I38；I38:I45） | 原值见锚点 | 洪恩 |
| D（合并继承自 D38；D38:D41） | 原值见锚点 | schedule-meeting |

<a id="entry-38ebd5cd621ab0434958"></a>
### entry-38ebd5cd621ab0434958 · 日程管理 Skill

技能一览表.xlsx / Agent与Skill列表 / 第 42 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B42 | SKILL | 日程管理 Skill |
| E42 | Skill描述 | 管理个人和课程相关日程 |
| F42 | 场景样例 | “帮我查一下下周有什么安排，有没有冲突？”<br>“提醒我周五下午4点要收作业。”“帮我把这学期所有的上课时间加到日程里。”“下周三我有两个会议时间重叠了，帮我看一下怎么调整。” |
| G42 | 功能列表 | 日程查询 |
| H42 | 功能是否具备 | 是 |
| K42 | 提测时间 | - |
| A（合并继承自 A38；A38:A44） | 原值见锚点 | 会议日程管理 Agent |
| I（合并继承自 I38；I38:I45） | 原值见锚点 | 洪恩 |

<a id="entry-a4d888331baf45178b23"></a>
### entry-a4d888331baf45178b23 · 日程管理 Skill

技能一览表.xlsx / Agent与Skill列表 / 第 43 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| G43 | 功能列表 | 日程创建 |
| H43 | 功能是否具备 | 是 |
| K43 | 提测时间 | - |
| B（合并继承自 B42；B42:B44） | 原值见锚点 | 日程管理 Skill |
| E（合并继承自 E42；E42:E44） | 原值见锚点 | 管理个人和课程相关日程 |
| F（合并继承自 F42；F42:F44） | 原值见锚点 | “帮我查一下下周有什么安排，有没有冲突？”<br>“提醒我周五下午4点要收作业。”“帮我把这学期所有的上课时间加到日程里。”“下周三我有两个会议时间重叠了，帮我看一下怎么调整。” |
| A（合并继承自 A38；A38:A44） | 原值见锚点 | 会议日程管理 Agent |
| I（合并继承自 I38；I38:I45） | 原值见锚点 | 洪恩 |

<a id="entry-1153843a7562edf63c30"></a>
### entry-1153843a7562edf63c30 · 日程管理 Skill

技能一览表.xlsx / Agent与Skill列表 / 第 44 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| G44 | 功能列表 | 日程取消 |
| H44 | 功能是否具备 | 是 |
| K44 | 提测时间 | - |
| B（合并继承自 B42；B42:B44） | 原值见锚点 | 日程管理 Skill |
| E（合并继承自 E42；E42:E44） | 原值见锚点 | 管理个人和课程相关日程 |
| F（合并继承自 F42；F42:F44） | 原值见锚点 | “帮我查一下下周有什么安排，有没有冲突？”<br>“提醒我周五下午4点要收作业。”“帮我把这学期所有的上课时间加到日程里。”“下周三我有两个会议时间重叠了，帮我看一下怎么调整。” |
| A（合并继承自 A38；A38:A44） | 原值见锚点 | 会议日程管理 Agent |
| I（合并继承自 I38；I38:I45） | 原值见锚点 | 洪恩 |

<a id="entry-dbb1e66cd2f8fb5bd346"></a>
### entry-dbb1e66cd2f8fb5bd346 · aigc-teaching-material

技能一览表.xlsx / Agent与Skill列表 / 第 45 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A45 | Agent |  内容创作Agent |
| B45 | SKILL | 多格式内容生成 Skill |
| D45 | skill名称 | aigc-teaching-material |
| E45 | Skill描述 | 支持 PPT、HTML、Word、Video 等内容生成 |
| F45 | 场景样例 | “帮我做一份关于’数字营销’的PPT，大概15页，面向大三学生。”“把我这份教案转成Word文档，排版正式一点。”“帮我生成一个可以在课堂上用的HTML互动页面，展示供需曲线。”“帮我写一段视频讲解脚本，介绍本章的三个核心模型。” |
| G45 | 功能列表 | AIGC内容生成 |
| H45 | 功能是否具备 | 是 |
| K45 | 提测时间 | - |
| I（合并继承自 I38；I38:I45） | 原值见锚点 | 洪恩 |

<a id="entry-725da6cc2ad39aea2204"></a>
### entry-725da6cc2ad39aea2204 · polymas-teacher-learning-analytics-skills

技能一览表.xlsx / Agent与Skill列表 / 第 46 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A46 | Agent | 数据分析Agent |
| B46 | SKILL | 学情分析 Skill |
| D46 | skill名称 | polymas-teacher-learning-analytics-skills |
| E46 | Skill描述 | 分析学生、班级、课程的学习情况 |
| F46 | 场景样例 | “上次考试情况怎么样”“这学期哪些知识点学生掌握得最差？”“帮我生成一份本次作业的班级学情分析报告。” |
| G46 | 功能列表 | 学情分析 |
| H46 | 功能是否具备 | 否 |
| I46 | 负责人 | 张康 + 朱希文 |
| L46 | 说明 | 找代老师确认一下学情分析等等<br>先做学生的分析 |

<a id="entry-6c96110b179cb545876d"></a>
### entry-6c96110b179cb545876d · 全平台数据查询与分析 Skill

技能一览表.xlsx / Agent与Skill列表 / 第 47 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B47 | SKILL | 全平台数据查询与分析 Skill |
| E47 | Skill描述 | 查询并整合平台内多来源数据 |
| F47 | 场景样例 | “把这个学生的作业完成率、考试成绩、课堂互动次数整合到一起，给我一个综合视图。”“帮我把三个班级的出勤、作业提交、成绩数据汇总到一张表里，横向对比一下。”“把作业、测验、讨论、出勤这几类数据都拉出来，整合成一份完整的学期学情报告。” |
| G47 | 功能列表 | 数据分析 |
| H47 | 功能是否具备 | 是 |
| A（合并继承自 A46；A46:A47） | 原值见锚点 | 数据分析Agent |
| L（合并继承自 L46；L46:L47） | 原值见锚点 | 找代老师确认一下学情分析等等<br>先做学生的分析 |
| I（合并继承自 I46；I46:I47） | 原值见锚点 | 张康 + 朱希文 |

<a id="entry-3a610231f6c128835a42"></a>
### entry-3a610231f6c128835a42 · Cron 定时任务

技能一览表.xlsx / Agent与Skill列表 / 第 48 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A48 | Agent | 平台工具 |
| B48 | SKILL | Cron 定时任务 |
| E48 | Skill描述 | 支持创建、修改、删除周期性任务和一次性定时任务，可绑定任意 Agent 动作，任务失败时触发告警 |

<a id="entry-a6613cdbca55fb0727d4"></a>
### entry-a6613cdbca55fb0727d4 · Web Search

技能一览表.xlsx / Agent与Skill列表 / 第 49 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B49 | SKILL | Web Search |
| E49 | Skill描述 | 支持关键词搜索、多源结果聚合、内容摘要提取、指定站点搜索，可作为其他 Agent 的资料补充入口 |
| A（合并继承自 A48；A48:A55） | 原值见锚点 | 平台工具 |

<a id="entry-614debba6a3c7ab9b824"></a>
### entry-614debba6a3c7ab9b824 · Hook

技能一览表.xlsx / Agent与Skill列表 / 第 50 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B50 | SKILL | Hook |
| E50 | Skill描述 | 监听平台内外部事件（作业提交、成绩录入、<br>学生加入等），触发预设 Agent 任务或通知流程 |
| A（合并继承自 A48；A48:A55） | 原值见锚点 | 平台工具 |

<a id="entry-8888f1f073d0b9f9d592"></a>
### entry-8888f1f073d0b9f9d592 · 数据查询

技能一览表.xlsx / Agent与Skill列表 / 第 51 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B51 | SKILL | 数据查询 |
| E51 | Skill描述 | 支持对平台结构化数据进行条件查询，包括作业、成绩、出勤、互动、AI 使用等多类数据表，返回原始数据供Agent 使用 |
| A（合并继承自 A48；A48:A55） | 原值见锚点 | 平台工具 |

<a id="entry-cb83e77429356b7d8db5"></a>
### entry-cb83e77429356b7d8db5 · 脚本执行

技能一览表.xlsx / Agent与Skill列表 / 第 52 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B52 | SKILL | 脚本执行 |
| E52 | Skill描述 | 支持执行预定义或动态生成的脚本，用于数据<br>处理、批量操作、格式转换等复杂任务 |
| A（合并继承自 A48；A48:A55） | 原值见锚点 | 平台工具 |

<a id="entry-4aa3a747ed17e96c88d3"></a>
### entry-4aa3a747ed17e96c88d3 · 会话管理

技能一览表.xlsx / Agent与Skill列表 / 第 53 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B53 | SKILL | 会话管理 |
| E53 | Skill描述 | 维护多轮对话的上下文状态，支持跨 Agent 的<br>会话传递、上下文注入和对话历史查询 |
| A（合并继承自 A48；A48:A55） | 原值见锚点 | 平台工具 |

<a id="entry-1c72005e74e6cf215284"></a>
### entry-1c72005e74e6cf215284 · 记忆管理

技能一览表.xlsx / Agent与Skill列表 / 第 54 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B54 | SKILL | 记忆管理 |
| E54 | Skill描述 | 持久化存储用户偏好、历史指令、常用配置等信息，供 Agent 在后续对话中主动召回和复用 |
| A（合并继承自 A48；A48:A55） | 原值见锚点 | 平台工具 |

<a id="entry-deb3d50df06185ceab64"></a>
### entry-deb3d50df06185ceab64 · 文件读写

技能一览表.xlsx / Agent与Skill列表 / 第 55 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B55 | SKILL | 文件读写 |
| E55 | Skill描述 | 支持对文件的读取和写入（包括office文档、html等），用于内容存储、日志记录、配置读取等场景 |
| A（合并继承自 A48；A48:A55） | 原值见锚点 | 平台工具 |

<a id="entry-c2886e595b43616e57d3"></a>
### entry-c2886e595b43616e57d3 · 适用范围

技能一览表.xlsx / Agent与Skill列表 / 第 64 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A64 | Agent | 技能类型 |
| B64 | SKILL | AGENT |
| D64 | skill名称 | 适用范围 |
| E64 | Skill描述 | 技能依赖 |

<a id="entry-e763418ced7bd42fa1e3"></a>
### entry-e763418ced7bd42fa1e3 · 教学活动

技能一览表.xlsx / Agent与Skill列表 / 第 65 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A65 | Agent | 老师 |
| D65 | skill名称 | 教学活动 |

<a id="entry-2132a4f131d93180e639"></a>
### entry-2132a4f131d93180e639 · 学课管理

技能一览表.xlsx / Agent与Skill列表 / 第 70 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| D70 | skill名称 | 学课管理 |
| A（合并继承自 A65；A65:A77） | 原值见锚点 | 老师 |

<a id="entry-30f5b1d42ae1c8595de9"></a>
### entry-30f5b1d42ae1c8595de9 · 备课

技能一览表.xlsx / Agent与Skill列表 / 第 72 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| D72 | skill名称 | 备课 |
| A（合并继承自 A65；A65:A77） | 原值见锚点 | 老师 |

<a id="entry-261d5a9b53f9ab523326"></a>
### entry-261d5a9b53f9ab523326 · 备课

技能一览表.xlsx / Agent与Skill列表 / 第 74 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| E74 | Skill描述 | 老师/学生&gt;文档操作&gt;(docx、xlsx、ppt、pdf) |
| A（合并继承自 A65；A65:A77） | 原值见锚点 | 老师 |
| D（合并继承自 D72；D72:D76） | 原值见锚点 | 备课 |

<a id="entry-199046a7f414afcbbe72"></a>
### entry-199046a7f414afcbbe72 · 备课

技能一览表.xlsx / Agent与Skill列表 / 第 76 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| E76 | Skill描述 | 老师/学生&gt;文档操作&gt;(docx、xlsx、ppt、pdf) |
| A（合并继承自 A65；A65:A77） | 原值见锚点 | 老师 |
| D（合并继承自 D72；D72:D76） | 原值见锚点 | 备课 |

<a id="entry-6848ae34cff2340a3c9d"></a>
### entry-6848ae34cff2340a3c9d · 资源管理

技能一览表.xlsx / Agent与Skill列表 / 第 77 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| D77 | skill名称 | 资源管理 |
| A（合并继承自 A65；A65:A77） | 原值见锚点 | 老师 |

<a id="entry-0f622b4f1ea20087fb0a"></a>
### entry-0f622b4f1ea20087fb0a · 会议日程管理

技能一览表.xlsx / Agent与Skill列表 / 第 78 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A78 | Agent | 老师/学生 |
| D78 | skill名称 | 会议日程管理 |

<a id="entry-6ca0693112d6be3c291e"></a>
### entry-6ca0693112d6be3c291e · 教学AIGC生成

技能一览表.xlsx / Agent与Skill列表 / 第 79 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| D79 | skill名称 | 教学AIGC生成 |
| A（合并继承自 A78；A78:A85） | 原值见锚点 | 老师/学生 |

<a id="entry-61743b852b9579df14d1"></a>
### entry-61743b852b9579df14d1 · 通用工具

技能一览表.xlsx / Agent与Skill列表 / 第 80 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| D80 | skill名称 | 通用工具 |
| A（合并继承自 A78；A78:A85） | 原值见锚点 | 老师/学生 |

<a id="entry-084f129cf6efa287a544"></a>
### entry-084f129cf6efa287a544 · 平台助手

技能一览表.xlsx / Agent与Skill列表 / 第 81 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| D81 | skill名称 | 平台助手 |
| A（合并继承自 A78；A78:A85） | 原值见锚点 | 老师/学生 |

<a id="entry-eb52f79ae49e51e36a99"></a>
### entry-eb52f79ae49e51e36a99 · 文档操作

技能一览表.xlsx / Agent与Skill列表 / 第 82 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| D82 | skill名称 | 文档操作 |
| A（合并继承自 A78；A78:A85） | 原值见锚点 | 老师/学生 |

<a id="entry-003fea35b66f755d573b"></a>
### entry-003fea35b66f755d573b · 课程管理

技能一览表.xlsx / Agent与Skill列表 / 第 87 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| D87 | skill名称 | 课程管理 |

<a id="entry-85646c4cb40d734782fa"></a>
### entry-85646c4cb40d734782fa · 教学日历

技能一览表.xlsx / Agent与Skill列表 / 第 88 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| D88 | skill名称 | 教学日历 |

<a id="entry-f828eafaa4aead6a0bb8"></a>
### entry-f828eafaa4aead6a0bb8 · 教学活动（作业、考试、话题讨论、通知）

技能一览表.xlsx / Agent与Skill列表 / 第 89 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| D89 | skill名称 | 教学活动（作业、考试、话题讨论、通知） |

<a id="entry-007294a7779c9a5e0cc5"></a>
### entry-007294a7779c9a5e0cc5 · 教学研讨

技能一览表.xlsx / Agent与Skill列表 / 第 90 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| D90 | skill名称 | 教学研讨 |

<a id="entry-39c8d2d7592edfc2e55f"></a>
### entry-39c8d2d7592edfc2e55f · 智能体教学

技能一览表.xlsx / Agent与Skill列表 / 第 91 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| D91 | skill名称 | 智能体教学 |

<a id="entry-3f18c6ed9a5796afe391"></a>
### entry-3f18c6ed9a5796afe391 · 备课

技能一览表.xlsx / Agent与Skill列表 / 第 92 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| D92 | skill名称 | 备课 |

<a id="entry-613803fa7d66052f8a48"></a>
### entry-613803fa7d66052f8a48 · 教室授课

技能一览表.xlsx / Agent与Skill列表 / 第 93 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| D93 | skill名称 | 教室授课 |

<a id="entry-968088ef8a0c6f44228c"></a>
### entry-968088ef8a0c6f44228c · 直播授课

技能一览表.xlsx / Agent与Skill列表 / 第 94 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| D94 | skill名称 | 直播授课 |

<a id="entry-848c77511ba05506507c"></a>
### entry-848c77511ba05506507c · 课堂互动

技能一览表.xlsx / Agent与Skill列表 / 第 95 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| D95 | skill名称 | 课堂互动 |

<a id="entry-29f024bb8e8b49050a3c"></a>
### entry-29f024bb8e8b49050a3c · 课堂报告、回放

技能一览表.xlsx / Agent与Skill列表 / 第 96 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| D96 | skill名称 | 课堂报告、回放 |

<a id="entry-7d1bfdef5c438aa83f51"></a>
### entry-7d1bfdef5c438aa83f51 · 小组教学

技能一览表.xlsx / Agent与Skill列表 / 第 97 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| D97 | skill名称 | 小组教学 |

<a id="entry-9ae7b06364a315ef25bb"></a>
### entry-9ae7b06364a315ef25bb · 训练题库

技能一览表.xlsx / Agent与Skill列表 / 第 98 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| D98 | skill名称 | 训练题库 |

<a id="entry-9ba2556702df7ddfc187"></a>
### entry-9ba2556702df7ddfc187 · 成绩管理

技能一览表.xlsx / Agent与Skill列表 / 第 99 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| D99 | skill名称 | 成绩管理 |

<a id="entry-2dc5a9dbd5ff9f5cc74e"></a>
### entry-2dc5a9dbd5ff9f5cc74e · OBE管理

技能一览表.xlsx / Agent与Skill列表 / 第 100 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| D100 | skill名称 | OBE管理 |

<a id="entry-f9b6470f5307a28d4fa0"></a>
### entry-f9b6470f5307a28d4fa0 · 学习资源（普通、闯关、复习模式）

技能一览表.xlsx / Agent与Skill列表 / 第 101 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| D101 | skill名称 | 学习资源（普通、闯关、复习模式） |

<a id="entry-d41c3a28dadca9ddeef0"></a>
### entry-d41c3a28dadca9ddeef0 · 三大资源库（个人、团队、课程）

技能一览表.xlsx / Agent与Skill列表 / 第 102 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| D102 | skill名称 | 三大资源库（个人、团队、课程） |

<a id="entry-7816dd435c5f867d8659"></a>
### entry-7816dd435c5f867d8659 · 题库、试卷库

技能一览表.xlsx / Agent与Skill列表 / 第 103 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| D103 | skill名称 | 题库、试卷库 |

<a id="entry-6838a6439dfe075901f1"></a>
### entry-6838a6439dfe075901f1 · 学情分析

技能一览表.xlsx / Agent与Skill列表 / 第 104 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| D104 | skill名称 | 学情分析 |

<a id="entry-6d7be10a08484d6f0e7f"></a>
### entry-6d7be10a08484d6f0e7f · 课程主页（原智能体课程评审主页）

技能一览表.xlsx / Agent与Skill列表 / 第 105 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| D105 | skill名称 | 课程主页（原智能体课程评审主页） |

<a id="entry-f3ecdc18f759777ac47b"></a>
### entry-f3ecdc18f759777ac47b · 协作空间

技能一览表.xlsx / Agent与Skill列表 / 第 106 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| D106 | skill名称 | 协作空间 |

<a id="entry-67201ae7ec8562fc4b82"></a>
### entry-67201ae7ec8562fc4b82 · AI翻转

技能一览表.xlsx / Agent与Skill列表 / 第 107 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| D107 | skill名称 | AI翻转 |

<a id="entry-e0994396ffbf01f2421f"></a>
### entry-e0994396ffbf01f2421f · 智能体对话

技能一览表.xlsx / Agent与Skill列表 / 第 108 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| D108 | skill名称 | 智能体对话 |

<a id="entry-39e0ba91c6881cb5b3cf"></a>
### entry-39e0ba91c6881cb5b3cf · 能力训练

技能一览表.xlsx / Agent与Skill列表 / 第 109 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| D109 | skill名称 | 能力训练 |

<a id="entry-6c74804367edd580e4ab"></a>
### entry-6c74804367edd580e4ab · 智能体授课

技能一览表.xlsx / Agent与Skill列表 / 第 110 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| D110 | skill名称 | 智能体授课 |

<a id="entry-627d521d4739bd2cbf3c"></a>
### entry-627d521d4739bd2cbf3c · AI批阅

技能一览表.xlsx / Agent与Skill列表 / 第 111 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| D111 | skill名称 | AI批阅 |

<a id="entry-71fb73976a652a194455"></a>
### entry-71fb73976a652a194455 · 大师版的： 智能辅导 能力阶梯 等

技能一览表.xlsx / Agent与Skill列表 / 第 112 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| D112 | skill名称 | 大师版的： 智能辅导 能力阶梯 等 |

<a id="entry-7f74fe33fa0154218004"></a>
### entry-7f74fe33fa0154218004 · polymas-tool-skills

技能一览表.xlsx / 生产智能体-技能映射 / 第 2 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A2 | 智能体 | 基础工具 |
| B2 | 智能体说明 | 通用工具服务，主要功能：联网搜索互联网公开内容，查询当前用户详情，搜索/安装技能广场能力，联网搜索/安装SKILL，文件上传至工作空间，平台使用助手 |
| C2 | 技能 | polymas-tool-skills |
| D2 | 技能说明 | 平台通用工具技能：提供联网搜索互联网公开内容、<br>搜索 Skill（可选择性安装）、能力广场搜索/安装、查询当前登录用户信息、文件上传至工作空间等功能 |

<a id="entry-dda85746407e32ac4d5c"></a>
### entry-dda85746407e32ac4d5c · polymas-agent-readme

技能一览表.xlsx / 生产智能体-技能映射 / 第 3 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C3 | 技能 | polymas-agent-readme |
| D3 | 技能说明 | 平台智能体功能帮助手册。当用户说'帮助'、'Help'、'你能做什么'、'有什么功能'等寻求帮助的表达时自动调用，展示全部功能模块及典型用法 |
| A（合并继承自 A2；A2:A3） | 原值见锚点 | 基础工具 |
| B（合并继承自 B2；B2:B3） | 原值见锚点 | 通用工具服务，主要功能：联网搜索互联网公开内容，查询当前用户详情，搜索/安装技能广场能力，联网搜索/安装SKILL，文件上传至工作空间，平台使用助手 |

<a id="entry-396a386776e979b103ee"></a>
### entry-396a386776e979b103ee · polymas-teacher-course-skills

技能一览表.xlsx / 生产智能体-技能映射 / 第 4 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A4 | 智能体 | 学课管理专员 |
| B4 | 智能体说明 | 专注于课程、班级、学生、教学计划的管理，支持课程查询、创建；班级及下属学生查询、班级创建、批量创建班级及下属学生；教学单元/计划查询 |
| C4 | 技能 | polymas-teacher-course-skills |
| D4 | 技能说明 | 根据用户需求智能选择课程查询或课程创建 |

<a id="entry-67f6ce7b693cc29e7524"></a>
### entry-67f6ce7b693cc29e7524 · polymas-teacher-class-skills

技能一览表.xlsx / 生产智能体-技能映射 / 第 5 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C5 | 技能 | polymas-teacher-class-skills |
| D5 | 技能说明 | 根据用户需求智能选择班级查询、创建及批量导入 |
| A（合并继承自 A4；A4:A6） | 原值见锚点 | 学课管理专员 |
| B（合并继承自 B4；B4:B6） | 原值见锚点 | 专注于课程、班级、学生、教学计划的管理，支持课程查询、创建；班级及下属学生查询、班级创建、批量创建班级及下属学生；教学单元/计划查询 |

<a id="entry-657ffb4ba1b25b81908e"></a>
### entry-657ffb4ba1b25b81908e · polymas-query-teaching-unit

技能一览表.xlsx / 生产智能体-技能映射 / 第 6 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C6 | 技能 | polymas-query-teaching-unit |
| D6 | 技能说明 | 课程计划/单元查询 |
| A（合并继承自 A4；A4:A6） | 原值见锚点 | 学课管理专员 |
| B（合并继承自 B4；B4:B6） | 原值见锚点 | 专注于课程、班级、学生、教学计划的管理，支持课程查询、创建；班级及下属学生查询、班级创建、批量创建班级及下属学生；教学单元/计划查询 |

<a id="entry-9ed191e96182bf10e4d0"></a>
### entry-9ed191e96182bf10e4d0 · polymas-teacher-homework-skills

技能一览表.xlsx / 生产智能体-技能映射 / 第 7 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A7 | 智能体 | 教学活动专员 |
| B7 | 智能体说明 | 专注于作业流程管理，考试流程管理，成绩管理，通知/活动管理，学生课堂表现分析,主要内容如下： 1.作业创建，作业修改，作业查询，作业打回，作业催交，作业分析，作业下的交流内容分析 2.考试创建，考试班级，考试查询 3.成绩汇总，成绩加权计算，班级成绩查询，成绩导出 4.通知发布，通知查看，通知分析，话题/讨论发布，话题/讨论查看，话题/讨论分析 5.学生课堂表现分析 |
| C7 | 技能 | polymas-teacher-homework-skills |
| D7 | 技能说明 | 根据用户需求智能选择作业查询、分析、交流、<br>催促、打回、创建及编辑 |

<a id="entry-037d22846c3d9bbd9a01"></a>
### entry-037d22846c3d9bbd9a01 · polymas-teacher-exam-skills

技能一览表.xlsx / 生产智能体-技能映射 / 第 8 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C8 | 技能 | polymas-teacher-exam-skills |
| D8 | 技能说明 | 根据用户需求智能选择考试查询、创建及编辑 |
| B（合并继承自 B7；B7:B11） | 原值见锚点 | 专注于作业流程管理，考试流程管理，成绩管理，通知/活动管理，学生课堂表现分析,主要内容如下： 1.作业创建，作业修改，作业查询，作业打回，作业催交，作业分析，作业下的交流内容分析 2.考试创建，考试班级，考试查询 3.成绩汇总，成绩加权计算，班级成绩查询，成绩导出 4.通知发布，通知查看，通知分析，话题/讨论发布，话题/讨论查看，话题/讨论分析 5.学生课堂表现分析 |
| A（合并继承自 A7；A7:A11） | 原值见锚点 | 教学活动专员 |

<a id="entry-19199e42f8212f0f61f1"></a>
### entry-19199e42f8212f0f61f1 · polymas-teacher-score-skills

技能一览表.xlsx / 生产智能体-技能映射 / 第 9 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C9 | 技能 | polymas-teacher-score-skills |
| D9 | 技能说明 | 根据用户需求智能选择成绩汇总、成绩加权计算、<br>班级成绩查询、成绩导出 |
| B（合并继承自 B7；B7:B11） | 原值见锚点 | 专注于作业流程管理，考试流程管理，成绩管理，通知/活动管理，学生课堂表现分析,主要内容如下： 1.作业创建，作业修改，作业查询，作业打回，作业催交，作业分析，作业下的交流内容分析 2.考试创建，考试班级，考试查询 3.成绩汇总，成绩加权计算，班级成绩查询，成绩导出 4.通知发布，通知查看，通知分析，话题/讨论发布，话题/讨论查看，话题/讨论分析 5.学生课堂表现分析 |
| A（合并继承自 A7；A7:A11） | 原值见锚点 | 教学活动专员 |

<a id="entry-f7376ba0cecd8e7b476c"></a>
### entry-f7376ba0cecd8e7b476c · polymas-teacher-activity-skills

技能一览表.xlsx / 生产智能体-技能映射 / 第 10 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C10 | 技能 | polymas-teacher-activity-skills |
| D10 | 技能说明 | 根据用户需求智能选择通知发布、通知查看、<br>通知分析、话题讨论发布、话题讨论查看、话题讨论分析 |
| B（合并继承自 B7；B7:B11） | 原值见锚点 | 专注于作业流程管理，考试流程管理，成绩管理，通知/活动管理，学生课堂表现分析,主要内容如下： 1.作业创建，作业修改，作业查询，作业打回，作业催交，作业分析，作业下的交流内容分析 2.考试创建，考试班级，考试查询 3.成绩汇总，成绩加权计算，班级成绩查询，成绩导出 4.通知发布，通知查看，通知分析，话题/讨论发布，话题/讨论查看，话题/讨论分析 5.学生课堂表现分析 |
| A（合并继承自 A7；A7:A11） | 原值见锚点 | 教学活动专员 |

<a id="entry-70a8b21c7ca1a2756f17"></a>
### entry-70a8b21c7ca1a2756f17 · polymas-teacher-lession-analysis

技能一览表.xlsx / 生产智能体-技能映射 / 第 11 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C11 | 技能 | polymas-teacher-lession-analysis |
| D11 | 技能说明 | 教师按课程、课堂查看学生课堂表现分析报告，包括成绩得分、<br>互动参与、弹幕次数、在线时长等数据 |
| B（合并继承自 B7；B7:B11） | 原值见锚点 | 专注于作业流程管理，考试流程管理，成绩管理，通知/活动管理，学生课堂表现分析,主要内容如下： 1.作业创建，作业修改，作业查询，作业打回，作业催交，作业分析，作业下的交流内容分析 2.考试创建，考试班级，考试查询 3.成绩汇总，成绩加权计算，班级成绩查询，成绩导出 4.通知发布，通知查看，通知分析，话题/讨论发布，话题/讨论查看，话题/讨论分析 5.学生课堂表现分析 |
| A（合并继承自 A7；A7:A11） | 原值见锚点 | 教学活动专员 |

<a id="entry-f788df50ce55c95b9bc9"></a>
### entry-f788df50ce55c95b9bc9 · polymas-teacher-resource-skills

技能一览表.xlsx / 生产智能体-技能映射 / 第 12 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A12 | 智能体 | 资源管理专员 |
| B12 | 智能体说明 | 专注于资源管理，包括知识库查询，资源库查询，<br>资源库同步，题库查询，题库同步 |
| C12 | 技能 | polymas-teacher-resource-skills |
| D12 | 技能说明 | 提供知识库内容搜索、资源库文件搜索/上传等功能 |

<a id="entry-2924f00e0a6f5a8f8edc"></a>
### entry-2924f00e0a6f5a8f8edc · polymas-teacher-questionbank-skills

技能一览表.xlsx / 生产智能体-技能映射 / 第 13 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C13 | 技能 | polymas-teacher-questionbank-skills |
| D13 | 技能说明 | 根据用户需求智能选择题库查询或Excel批量导入题目 |
| A（合并继承自 A12；A12:A13） | 原值见锚点 | 资源管理专员 |
| B（合并继承自 B12；B12:B13） | 原值见锚点 | 专注于资源管理，包括知识库查询，资源库查询，<br>资源库同步，题库查询，题库同步 |

<a id="entry-5fe76ae7f29eeea6a64c"></a>
### entry-5fe76ae7f29eeea6a64c · docx

技能一览表.xlsx / 生产智能体-技能映射 / 第 14 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A14 | 智能体 | 文件解析 |
| B14 | 智能体说明 | 用于读取与解析办公文档内容。支持 PDF、Word（.doc/.docx）、PowerPoint（.ppt/.pptx）、Excel（.xlsx/.xlsm/.csv/.tsv）。适用于：提取全文/目录/表格、按页或按 sheet 摘要、对比多份文档、回答“文件里写了什么”、从附件中检索关键信息。不支持：直接修改版式、批量重排版、加密文件破解。扫描版 PDF 需 OCR；损坏或 XML 异常的 PPT 可能只能部分提取。<br> |
| C14 | 技能 | docx |

<a id="entry-9077d950adb0da66cf55"></a>
### entry-9077d950adb0da66cf55 · xlsx

技能一览表.xlsx / 生产智能体-技能映射 / 第 15 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C15 | 技能 | xlsx |
| A（合并继承自 A14；A14:A17） | 原值见锚点 | 文件解析 |
| B（合并继承自 B14；B14:B17） | 原值见锚点 | 用于读取与解析办公文档内容。支持 PDF、Word（.doc/.docx）、PowerPoint（.ppt/.pptx）、Excel（.xlsx/.xlsm/.csv/.tsv）。适用于：提取全文/目录/表格、按页或按 sheet 摘要、对比多份文档、回答“文件里写了什么”、从附件中检索关键信息。不支持：直接修改版式、批量重排版、加密文件破解。扫描版 PDF 需 OCR；损坏或 XML 异常的 PPT 可能只能部分提取。<br> |

<a id="entry-15800caff149faf3ea58"></a>
### entry-15800caff149faf3ea58 · ppt

技能一览表.xlsx / 生产智能体-技能映射 / 第 16 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C16 | 技能 | ppt |
| A（合并继承自 A14；A14:A17） | 原值见锚点 | 文件解析 |
| B（合并继承自 B14；B14:B17） | 原值见锚点 | 用于读取与解析办公文档内容。支持 PDF、Word（.doc/.docx）、PowerPoint（.ppt/.pptx）、Excel（.xlsx/.xlsm/.csv/.tsv）。适用于：提取全文/目录/表格、按页或按 sheet 摘要、对比多份文档、回答“文件里写了什么”、从附件中检索关键信息。不支持：直接修改版式、批量重排版、加密文件破解。扫描版 PDF 需 OCR；损坏或 XML 异常的 PPT 可能只能部分提取。<br> |

<a id="entry-23af0051dd1bd21b7f4f"></a>
### entry-23af0051dd1bd21b7f4f · pdf

技能一览表.xlsx / 生产智能体-技能映射 / 第 17 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C17 | 技能 | pdf |
| A（合并继承自 A14；A14:A17） | 原值见锚点 | 文件解析 |
| B（合并继承自 B14；B14:B17） | 原值见锚点 | 用于读取与解析办公文档内容。支持 PDF、Word（.doc/.docx）、PowerPoint（.ppt/.pptx）、Excel（.xlsx/.xlsm/.csv/.tsv）。适用于：提取全文/目录/表格、按页或按 sheet 摘要、对比多份文档、回答“文件里写了什么”、从附件中检索关键信息。不支持：直接修改版式、批量重排版、加密文件破解。扫描版 PDF 需 OCR；损坏或 XML 异常的 PPT 可能只能部分提取。<br> |

<a id="entry-92a895061ba7ea27cabd"></a>
### entry-92a895061ba7ea27cabd · polymas-teacher-problem-skills

技能一览表.xlsx / 生产智能体-技能映射 / 第 18 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A18 | 智能体 | 智能备课专员 |
| B18 | 智能体说明 | 专注于备课场景的智能化教学准备，支持教学案例生成、概念类比阐释、课堂流程设计、多类型 AIGC 素材创作与自动出题。可结合课程内容、教学需求及学科特点，自动生成贴合实际的商业/生活化案例、结构化教案、PPT/HTML 课件、讲稿、复习提纲、教学视频、网页、图片等配套资源，并将抽象概念转化为通俗易懂的类比或反例。适用于：为理论知识点创建行业应用案例、用生活类比解释复杂原理、设计分步骤的课堂互动方案、根据薄弱知识点批量生成练习题并存入题库、快速制作微课脚本或代码演示课件等。不支持：直接发布作业、学情数据修改、成绩录入。 |
| C18 | 技能 | polymas-teacher-problem-skills |
| D18 | 技能说明 | 教师出题技能：根据知识点、难度、题型等要求，通过 AI 自动生成题目并保存到题库 |

<a id="entry-da5cc5355c6cdf090976"></a>
### entry-da5cc5355c6cdf090976 · polymas-teacher-case-skills

技能一览表.xlsx / 生产智能体-技能映射 / 第 19 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C19 | 技能 | polymas-teacher-case-skills |
| D19 | 技能说明 | 教师案例生成技能：根据课程内容与教学需求，生成真实商业案例、生活化案例、行业案例等教学案例，支持自定义案例类型 |
| A（合并继承自 A18；A18:A23） | 原值见锚点 | 智能备课专员 |
| B（合并继承自 B18；B18:B23） | 原值见锚点 | 专注于备课场景的智能化教学准备，支持教学案例生成、概念类比阐释、课堂流程设计、多类型 AIGC 素材创作与自动出题。可结合课程内容、教学需求及学科特点，自动生成贴合实际的商业/生活化案例、结构化教案、PPT/HTML 课件、讲稿、复习提纲、教学视频、网页、图片等配套资源，并将抽象概念转化为通俗易懂的类比或反例。适用于：为理论知识点创建行业应用案例、用生活类比解释复杂原理、设计分步骤的课堂互动方案、根据薄弱知识点批量生成练习题并存入题库、快速制作微课脚本或代码演示课件等。不支持：直接发布作业、学情数据修改、成绩录入。 |

<a id="entry-54db0b301994266051f4"></a>
### entry-54db0b301994266051f4 · polymas-teacher-lesson-design

技能一览表.xlsx / 生产智能体-技能映射 / 第 20 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C20 | 技能 | polymas-teacher-lesson-design |
| D20 | 技能说明 | 课堂设计技能：根据教师提供的课程主题与教学要求，生成结构化课堂教学流程方案，支持多轮迭代与细化 |
| A（合并继承自 A18；A18:A23） | 原值见锚点 | 智能备课专员 |
| B（合并继承自 B18；B18:B23） | 原值见锚点 | 专注于备课场景的智能化教学准备，支持教学案例生成、概念类比阐释、课堂流程设计、多类型 AIGC 素材创作与自动出题。可结合课程内容、教学需求及学科特点，自动生成贴合实际的商业/生活化案例、结构化教案、PPT/HTML 课件、讲稿、复习提纲、教学视频、网页、图片等配套资源，并将抽象概念转化为通俗易懂的类比或反例。适用于：为理论知识点创建行业应用案例、用生活类比解释复杂原理、设计分步骤的课堂互动方案、根据薄弱知识点批量生成练习题并存入题库、快速制作微课脚本或代码演示课件等。不支持：直接发布作业、学情数据修改、成绩录入。 |

<a id="entry-5de4f43b2b225e8faaff"></a>
### entry-5de4f43b2b225e8faaff · polymas-teacher-analogy-skills

技能一览表.xlsx / 生产智能体-技能映射 / 第 21 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C21 | 技能 | polymas-teacher-analogy-skills |
| D21 | 技能说明 | 教师概念类比技能：将抽象概念转化为类比、例子或反例，帮助教师将复杂理论转化为通俗易懂的课堂讲解内容，支持自定义解释风格与目标听众群体 |
| A（合并继承自 A18；A18:A23） | 原值见锚点 | 智能备课专员 |
| B（合并继承自 B18；B18:B23） | 原值见锚点 | 专注于备课场景的智能化教学准备，支持教学案例生成、概念类比阐释、课堂流程设计、多类型 AIGC 素材创作与自动出题。可结合课程内容、教学需求及学科特点，自动生成贴合实际的商业/生活化案例、结构化教案、PPT/HTML 课件、讲稿、复习提纲、教学视频、网页、图片等配套资源，并将抽象概念转化为通俗易懂的类比或反例。适用于：为理论知识点创建行业应用案例、用生活类比解释复杂原理、设计分步骤的课堂互动方案、根据薄弱知识点批量生成练习题并存入题库、快速制作微课脚本或代码演示课件等。不支持：直接发布作业、学情数据修改、成绩录入。 |

<a id="entry-815de93694418af77fc5"></a>
### entry-815de93694418af77fc5 · polymas-teacher-content-creation

技能一览表.xlsx / 生产智能体-技能映射 / 第 22 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C22 | 技能 | polymas-teacher-content-creation |
| D22 | 技能说明 | 教师内容创作技能：根据教学需求，智能生成教案、复习提纲、课堂讲稿、PPT等备课材料的提示词，并调用内容生成引擎完成创作 |
| A（合并继承自 A18；A18:A23） | 原值见锚点 | 智能备课专员 |
| B（合并继承自 B18；B18:B23） | 原值见锚点 | 专注于备课场景的智能化教学准备，支持教学案例生成、概念类比阐释、课堂流程设计、多类型 AIGC 素材创作与自动出题。可结合课程内容、教学需求及学科特点，自动生成贴合实际的商业/生活化案例、结构化教案、PPT/HTML 课件、讲稿、复习提纲、教学视频、网页、图片等配套资源，并将抽象概念转化为通俗易懂的类比或反例。适用于：为理论知识点创建行业应用案例、用生活类比解释复杂原理、设计分步骤的课堂互动方案、根据薄弱知识点批量生成练习题并存入题库、快速制作微课脚本或代码演示课件等。不支持：直接发布作业、学情数据修改、成绩录入。 |

<a id="entry-c6dd1824525f22161958"></a>
### entry-c6dd1824525f22161958 · aigc-teaching-material

技能一览表.xlsx / 生产智能体-技能映射 / 第 23 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C23 | 技能 | aigc-teaching-material |
| D23 | 技能说明 | 生成教学相关 AIGC 素材，涵盖教案、报告、代码、PPT/HTML 课件、网页、图片、教学视频。通过 Python 脚本调用桥接接口；用于备课、课件开发、教学内容创作等场景。 |
| A（合并继承自 A18；A18:A23） | 原值见锚点 | 智能备课专员 |
| B（合并继承自 B18；B18:B23） | 原值见锚点 | 专注于备课场景的智能化教学准备，支持教学案例生成、概念类比阐释、课堂流程设计、多类型 AIGC 素材创作与自动出题。可结合课程内容、教学需求及学科特点，自动生成贴合实际的商业/生活化案例、结构化教案、PPT/HTML 课件、讲稿、复习提纲、教学视频、网页、图片等配套资源，并将抽象概念转化为通俗易懂的类比或反例。适用于：为理论知识点创建行业应用案例、用生活类比解释复杂原理、设计分步骤的课堂互动方案、根据薄弱知识点批量生成练习题并存入题库、快速制作微课脚本或代码演示课件等。不支持：直接发布作业、学情数据修改、成绩录入。 |

<a id="entry-4bb59e70d734a53f5e5d"></a>
### entry-4bb59e70d734a53f5e5d · schedule-meeting

技能一览表.xlsx / 生产智能体-技能映射 / 第 24 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A24 | 智能体 | 会议日程专员 |
| B24 | 智能体说明 | 专注于日程、会议的管理，支持查询创建删除会议、日程，会议纪要查询。 |
| C24 | 技能 | schedule-meeting |
| D24 | 技能说明 | 该技能用于管理日程与会议：创建、查询、取消、会议纪要查询；查询日程/会议列表成功且有条目时以 Markdown 列表/表格直接展示。只要用户提到日程、会议、提醒、排期、站会、取消日程、取消会议、查列表、删除提醒、会议纪要、会议总结等，就应使用本技能。不要用于：一般性日历/会议软件使用咨询、与本 API 无关的日程规划讨论、或用户仅想要文字建议而不需要实际创建/查询/取消操作。 |

<a id="entry-effbcffcdccae08f5253"></a>
### entry-effbcffcdccae08f5253 · polymas-teacher-homework-detail-skills

技能一览表.xlsx / SKILL开发方向划分 / 第 4 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B4 | 数据与学情增强 | A1 |
| C4 | 未命名列 C | §3 #40 |
| F4 | 未命名列 F | 选题作业学情分析：作业/考试/刷题训练的薄弱知识点、高频错题、学生预警、改进建议；自定义作业没有分析； |
| G4 | 未命名列 G | “薄弱知识点定位”和“预警名单”维度（产品文档：“薄弱知识点/高频错题/学生预警/改进建议”） |
| H4 | 未命名列 H | P-1 |
| M4 | 技能名称 | polymas-teacher-homework-detail-skills<br><br> |
| N4 | 前置技能 | 1. 学情分析（基于大数据表 + 权限（环境变量 - POLYMAS_USER_ID））<br>2. 在辉哥的平台<br>3. 可以求助下辉哥、代老师、王丹 |
| O4 | 技能的实现说明 | 1. 查询作业学情分析情况<br>2.查询作业详情<br>3.获取考试学情分析<br>4.获取某次考试详情信息<br>5.获取课程下作业及考试列表 |
| P4 | 负责人 | @朱希文 |
| Q4 | 是否完成 | -是 |
| R4 | 提测时间 | 46217 |
| S4 | 测试情况 | 测试通过（线上） |
| U4 | 规范 | 1. 零散功能<br>2. 组合完整<br>3. 备课 - 能做啥就做啥（对话框先弄 - 洪恩接口）<br>4. 拖拉视频框巨小<br>5. 汪勇负责主要的技能与专家 - 收拢口子<br>6. 用户初始化能力必须固定 - <br>7. 暑期冲刺 - 测试<br><br>1. 备课 - 7.30上到线上<br>2. 生成拆分 - 7.30 上到线上（四个agent）<br>3. 整理技能 -  类教学类 + 通用类（初始化）<br>本周五: 理清楚表格 <br>下周二: 开始调整<br>下周四: 上线<br>4. 分类 - 场景类, 基础工具<br><br><br> V5 - 开放日（8.17）<br>UI - 走查<br> |
| A（合并继承自 A1；A1:A29） | 原值见锚点 | 第一批次<br>高优先级 |

<a id="entry-ddf6e061cbfdd99a2ee1"></a>
### entry-ddf6e061cbfdd99a2ee1 · polymas-teacher-classroom-report-skills

技能一览表.xlsx / SKILL开发方向划分 / 第 5 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B5 | 数据与学情增强 | A2 |
| C5 | 未命名列 C | §3 #41-2.10 |
| F5 | 未命名列 F | 课堂报告查询：AI回顾三件套（摘要/导图/知识点）+随堂测验错题+互动数据，支持“今天这节课”定位 |
| G5 | 未命名列 G | 新增（产品文档：“AI回顾三件套(摘要/导图/知识点)可直接引用”） |
| H5 | 未命名列 H | P-1 |
| M5 | 技能名称 | polymas-teacher-classroom-report-skills |
| O5 | 技能的实现说明 | 1.课堂的核心数据分析； <br>2. 课堂的核心回顾 <br>    2.1 知识导图，<br>    2.2 知识点请单，<br>    2.3 知识摘要    <br>3.课堂互动数据分析；<br>4. 随堂测验详情    |
| P5 | 负责人 | @朱希文 |
| Q5 | 是否完成 | -是 |
| R5 | 提测时间 | 46218 |
| S5 | 测试情况 | 已测试（预发） |
| T5 | 测试时间 | 回顾测试通过 |
| A（合并继承自 A1；A1:A29） | 原值见锚点 | 第一批次<br>高优先级 |

<a id="entry-4a3b84ff574d8c1fc2da"></a>
### entry-4a3b84ff574d8c1fc2da · polymas-teacher-homework-detail-skills

技能一览表.xlsx / SKILL开发方向划分 / 第 6 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B6 | 数据与学情增强 | A3 |
| C6 | 未命名列 C | §3 #22-2.2/2.3 |
| F6 | 未命名列 F | 完成情况查询（作业/考试）：未交/已批/未批名单、提交次数、完成率%，可按班级/分组方案筛选 |
| G6 | 未命名列 G | 新增，需补充“未交名单”“提交次数”“完成率%”维度（产品文档：“未交/已批/未批名单、提交次数、完成率%维度”） |
| H6 | 未命名列 H | P0 |
| I6 | 未命名列 I | 按照班级去查还是存在问题 |
| M6 | 技能名称 | polymas-teacher-homework-detail-skills |
| P6 | 负责人 | @朱希文 |
| Q6 | 是否完成 | -是 |
| R6 | 提测时间 |                    2026/7/17 |
| S6 | 测试情况 | 已测试（预发） |
| A（合并继承自 A1；A1:A29） | 原值见锚点 | 第一批次<br>高优先级 |

<a id="entry-923a0b1192574be3e753"></a>
### entry-923a0b1192574be3e753 · polymas-teacher-class-skills<br>polymas-teacher-class-student-skills

技能一览表.xlsx / SKILL开发方向划分 / 第 7 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B7 | 数据与学情增强 | A4 |
| C7 | 未命名列 C | §3 #15-2.5 |
| F7 | 未命名列 F | 班级学生查询：入班三状态（已入班/待审核/待激活）+学生标签筛选维度 |
| G7 | 未命名列 G | 已有，需补充“入班状态与标签维度”（产品文档：“差量：入班状态与标签维度”） |
| H7 | 未命名列 H | P0 |
| M7 | 技能名称 | polymas-teacher-class-skills<br>polymas-teacher-class-student-skills<br> |
| O7 | 技能的实现说明 | 入班状态、标签、院系等信息<br>1. 按入班状态查询课程/班级下的学生信息，支持已入班、待审核、待激活三种状态路由<br>2. 审核入班申请：查看待审核列表、批量同意全部申请、忽略指定申请<br>3. 待激活学生管理：查看待激活列表、删除待激活学生<br>学生调班/退班：调整学生班级归属，查当前班级→查目标班级→执行调班/退班<br>学生标签管理：打/改/查/删标签，智能复用语义相近的已有标签避免重复创建 |
| P7 | 负责人 | @倪吉龙 |
| Q7 | 是否完成 | 是 |
| S7 | 测试情况 | 待测试 |
| A（合并继承自 A1；A1:A29） | 原值见锚点 | 第一批次<br>高优先级 |

<a id="entry-e51558dd71b306a12bfc"></a>
### entry-e51558dd71b306a12bfc · polymas-teacher-teaching-observation-skills

技能一览表.xlsx / SKILL开发方向划分 / 第 8 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B8 | 数据与学情增强 | A5 |
| C8 | 未命名列 C | §3 #6-2.22 |
| F8 | 未命名列 F | 课程综合分析：课程级学情大盘，含AI综合评价、知识点掌握度、预警学生名单；回答给出学情数据的综合评价。 |
| G8 | 未命名列 G | 新增（产品文档：“课程级学情/教学大盘（含AI综合评价）”） |
| H8 | 未命名列 H | P0 |
| M8 | 技能名称 | polymas-teacher-teaching-observation-skills<br> |
| O8 | 技能的实现说明 | 课程综合分析：<br>含AI综合评价、<br>知识点掌握度、<br>预警学生名单； |
| P8 | 负责人 | @朱希文 |
| Q8 | 是否完成 | -是 |
| R8 | 提测时间 | 46218 |
| S8 | 测试情况 | 测试通过（线上） |
| T8 | 测试时间 | 7.30. |
| A（合并继承自 A1；A1:A29） | 原值见锚点 | 第一批次<br>高优先级 |

<a id="entry-de2cf7ed8914616adace"></a>
### entry-de2cf7ed8914616adace · polymas-teacher-teaching-plan

技能一览表.xlsx / SKILL开发方向划分 / 第 9 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B9 | 数据与学情增强 | A6 |
| C9 | 未命名列 C | §3 #9-2.7 |
| F9 | 未命名列 F | 教学计划查询：查询单元/主题(小节)/知识点结构、关联的作业与考试活动 |
| G9 | 未命名列 G | 已有，需补充“关联活动”维度（产品文档：“主题与作业考试双向关联”） |
| H9 | 未命名列 H | P1 |
| M9 | 技能名称 | polymas-teacher-teaching-plan |
| P9 | 负责人 | @陈源富 |
| Q9 | 是否完成 | 是 |
| S9 | 测试情况 | 待测试 |
| A（合并继承自 A1；A1:A29） | 原值见锚点 | 第一批次<br>高优先级 |

<a id="entry-1c6035e986ebb8cf4b6d"></a>
### entry-1c6035e986ebb8cf4b6d · 1.简单要求生题，<br>2.附件生题，<br>3.学情分析出题，<br>复用算法skill，增加保存入库能力。（数据流转结构待确认）<br>4.从对话中获取文件。

技能一览表.xlsx / SKILL开发方向划分 / 第 14 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B14 | 数据与学情增强 | B1 |
| C14 | 未命名列 C | §3 #44 |
| F14 | 未命名列 F | AI出题：接收学情分析结果（薄弱知识点、错题），布鲁姆六级考核目标，出题并入库保存至题库 |
| G14 | 未命名列 G | 已有出题+保存题库能力，需补“接收学情分析结果作为输入”（产品文档：“参数可直接映射学情分析输出的薄弱知识点”） |
| H14 | 未命名列 H | P-1 |
| O14 | 技能的实现说明 | 1.简单要求生题，<br>2.附件生题，<br>3.学情分析出题，<br>复用算法skill，增加保存入库能力。（数据流转结构待确认）<br>4.从对话中获取文件。 |
| P14 | 负责人 | @赵洪恩 |
| Q14 | 是否完成 | - |
| A（合并继承自 A1；A1:A29） | 原值见锚点 | 第一批次<br>高优先级 |

<a id="entry-3cb728719d19289a54ec"></a>
### entry-3cb728719d19289a54ec · lesson-prep

技能一览表.xlsx / SKILL开发方向划分 / 第 15 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B15 | 数据与学情增强 | B2 |
| C15 | 未命名列 C | §3 #50 |
| F15 | 未命名列 F | 智能备课生成：支持多文件参考解析，生成教案/课件/德育案例等 |
| G15 | 未命名列 G | 已有，需补“多文件参考”“草稿输出”“德育案例”（产品文档：“参考文件(≤5)；生成物挂进备课方案需教师确认”） |
| H15 | 未命名列 H | P-1 |
| J15 | 未命名列 J | 日历-查对应时间上的什么课-查看或新备课-根据用户描述路由到对应的生成能力<br>--参考资料：文件信息-教案-课件  章节对应教学计划（教学计划通过课程查询） |
| M15 | 技能名称 | lesson-prep |
| O15 | 技能的实现说明 | §3 #50 <br>1.是否和课堂设计相关？<br>课堂设计用于把互动测验编排进课堂流程。<br>课堂设计编排能力暂未开发-需求还未评审<br>2.备课流程已梳理-原子化流程与算法协作<br>生成教案-生成课件-生成的案例<br>添加资源<br>生成自定义投票-生成头脑风暴-生成随堂测验<br><br> |
| P15 | 负责人 | @赵洪恩 |
| Q15 | 是否完成 | -是 |
| A（合并继承自 A1；A1:A29） | 原值见锚点 | 第一批次<br>高优先级 |

<a id="entry-7bd42adfe1e1ae08bfbc"></a>
### entry-7bd42adfe1e1ae08bfbc · polymas-teacher-knowledge-distillation

技能一览表.xlsx / SKILL开发方向划分 / 第 16 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B16 | 数据与学情增强 | B3 |
| C16 | 未命名列 C | §3 #58 |
| F16 | 未命名列 F | 个人知识蒸馏：对话中接收教师经验/规则文本，存入“我的知识库”供智能体对话引用 |
| G16 | 未命名列 G | 新增（产品文档：“平台明示‘用于智能体对话’——V5回答质量的直接来源”） |
| H16 | 未命名列 H | P1 |
| M16 | 技能名称 | polymas-teacher-knowledge-distillation |
| O16 | 技能的实现说明 | 1.获取个人资源库<br>2.上传文件<br>3.润色-经确认-上传知识块 |
| P16 | 负责人 | @陈源富 |
| Q16 | 是否完成 | -是 |
| S16 | 测试情况 | 待测试 |
| A（合并继承自 A1；A1:A29） | 原值见锚点 | 第一批次<br>高优先级 |

<a id="entry-3994647697addb203b3e"></a>
### entry-3994647697addb203b3e · lesson-prep

技能一览表.xlsx / SKILL开发方向划分 / 第 17 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B17 | 数据与学情增强 | B4 |
| C17 | 未命名列 C | 单P-1 |
| F17 | 未命名列 F | 课堂设计Skill |
| G17 | 未命名列 G | 已有（补充数据源：“教学数据、课程大纲、知识图谱、资源（各个资源库中已有的教材、课件等），与用户一起讨论和设计一堂课”，补充设计规范：例如讲授式、讨论式、小组协作式、PBL等，设计好什么时候发签到点名、讨论、小测验等） |
| H17 | 未命名列 H | P-1 |
| M17 | 技能名称 | lesson-prep |
| O17 | 技能的实现说明 | 提供业务操作/绑定/入库 skill<br>课堂设计用于把互动测验编排进课堂流程。<br><br>与算法串流程 |
| P17 | 负责人 | @余洲@赵洪恩 |
| Q17 | 是否完成 | -是 |
| A（合并继承自 A1；A1:A29） | 原值见锚点 | 第一批次<br>高优先级 |

<a id="entry-cc14debf77f52e33a28f"></a>
### entry-cc14debf77f52e33a28f · polymas-teacher-file-import-questions

技能一览表.xlsx / SKILL开发方向划分 / 第 18 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B18 | 数据与学情增强 | B6 |
| C18 | 未命名列 C | §3 #46 |
| F18 | 未命名列 F | 智能导入题目：上传PDF/Word/图片/Excel试卷文件，解析入库，逐题确认 |
| G18 | 未命名列 G | 新增  “解析失败态处理”“逐题确认环节”（产品文档：“解析失败态；逐题确认环节保留在页面或对话卡片”） |
| H18 | 未命名列 H | P1 |
| I18 | 未命名列 I | 时间过长 |
| M18 | 技能名称 | polymas-teacher-file-import-questions |
| O18 | 技能的实现说明 | 1.确定题库<br>2.启动识别任务<br>3.确认任务成功<br>4.展示题目<br>5.导入题库 |
| P18 | 负责人 | @赵洪恩 |
| Q18 | 是否完成 | -是 |
| R18 | 提测时间 | 46216 |
| S18 | 测试情况 | 已测试（预发） |
| A（合并继承自 A1；A1:A29） | 原值见锚点 | 第一批次<br>高优先级 |

<a id="entry-e5714eaed271b77ce28d"></a>
### entry-e5714eaed271b77ce28d · polymas-teacher-homework-skills

技能一览表.xlsx / SKILL开发方向划分 / 第 24 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B24 | 数据与学情增强 | C1 |
| C24 | 未命名列 C | §3 #20 |
| F24 | 未命名列 F | 发布作业：补齐按班级分别设截止时间、提交规则三开关（迟交/重做审批限次/修改N次）、AI批阅Agent绑定、关联教学计划 |
| G24 | 未命名列 G | 已有，需补上述参数（产品文档：“差量：现状参数远少于此字段全集，尤其按班级截止、提交规则三开关、AI批阅Agent绑定”） |
| H24 | 未命名列 H | P-1 |
| M24 | 技能名称 | polymas-teacher-homework-skills |
| O24 | 技能的实现说明 | 1.创建自定义作业、选题作业发布<br>2.绑定ai批阅 ai查重 <br>3.设截止时间、提交规则三开关（迟交/重做审批限次/修改N次）、AI批阅Agent绑定、关联教学计划<br>4.发布作业 |
| P24 | 负责人 | @张康 |
| Q24 | 是否完成 | -是 |
| R24 | 提测时间 | 46216 |
| S24 | 测试情况 | 已测试（线上，有bug） |
| T24 | 测试时间 | 7.29 |
| A（合并继承自 A1；A1:A29） | 原值见锚点 | 第一批次<br>高优先级 |

<a id="entry-ebc4c9c38f1cd02106c7"></a>
### entry-ebc4c9c38f1cd02106c7 · polymas-teacher-resource-skills

技能一览表.xlsx / SKILL开发方向划分 / 第 25 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B25 | 数据与学情增强 | C2 |
| C25 | 未命名列 C | §3 #56 |
| F25 | 未命名列 F | 资源库检索：修复返回描述问题，增加类型过滤（10类）、文件夹定位、三级库（课程/我的/团队） |
| G25 | 未命名列 G | 已有，需修复+补类型过滤和文件夹定位（产品文档：“现状‘有’——差量：类型过滤与文件夹定位”） |
| H25 | 未命名列 H | P0 |
| M25 | 技能名称 | polymas-teacher-resource-skills |
| P25 | 负责人 | @张康 |
| Q25 | 是否完成 | -是 |
| R25 | 提测时间 | 46217 |
| S25 | 测试情况 | 已测试（预发） |
| A（合并继承自 A1；A1:A29） | 原值见锚点 | 第一批次<br>高优先级 |

<a id="entry-5dc4b6ea97e0a9fb8277"></a>
### entry-5dc4b6ea97e0a9fb8277 · polymas-teacher-resource-skills

技能一览表.xlsx / SKILL开发方向划分 / 第 26 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B26 | 数据与学情增强 | C3 |
| C26 | 未命名列 C | §3 #57 |
| F26 | 未命名列 F | 上传文件到资源库：对话内上传文件并指定目标文件夹 |
| G26 | 未命名列 G | 已有，需补“目标文件夹指定”“重名处理”（产品文档：“目标文件夹；重名处理⚠️”） |
| H26 | 未命名列 H | P0 |
| M26 | 技能名称 | polymas-teacher-resource-skills |
| P26 | 负责人 | @张康 |
| Q26 | 是否完成 | -是 |
| R26 | 提测时间 | 46218 |
| S26 | 测试情况 | 已测试（预发） |
| A（合并继承自 A1；A1:A29） | 原值见锚点 | 第一批次<br>高优先级 |

<a id="entry-4df081c73b27b04e4004"></a>
### entry-4df081c73b27b04e4004 · 代老师

技能一览表.xlsx / SKILL开发方向划分 / 第 27 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B27 | 数据与学情增强 | C4 |
| C27 | 未命名列 C | §3 #3 |
| F27 | 未命名列 F | 我的权限查询：查询自己在各班级的功能权限（7组30+项），输出权限不足原因，提供鉴权中间件 |
| G27 | 未命名列 G | 新增（产品文档：“权限=班级×功能树(7组30+项)”“权限不足时所有skill的统一解释出口”） |
| H27 | 未命名列 H | P0 |
| O27 | 技能的实现说明 | 代老师 |
| P27 | 负责人 | @张康 |
| Q27 | 是否完成 | - |
| A（合并继承自 A1；A1:A29） | 原值见锚点 | 第一批次<br>高优先级 |

<a id="entry-8ee581725446cd05a853"></a>
### entry-8ee581725446cd05a853 · polymas-teacher-class-student-skills

技能一览表.xlsx / SKILL开发方向划分 / 第 28 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B28 | 数据与学情增强 | C5 |
| C28 | 未命名列 C | §3 #16 |
| F28 | 未命名列 F | 审核入班申请：同意/忽略入班申请，支持全部操作 |
| G28 | 未命名列 G | 新增（产品文档：“把待审核的全部同意”） |
| H28 | 未命名列 H | P1 |
| M28 | 技能名称 | polymas-teacher-class-student-skills |
| O28 | 技能的实现说明 | 代老师 |
| P28 | 负责人 | @倪吉龙 |
| Q28 | 是否完成 | 是 |
| A（合并继承自 A1；A1:A29） | 原值见锚点 | 第一批次<br>高优先级 |

<a id="entry-c8aac64a3543889fcae3"></a>
### entry-c8aac64a3543889fcae3 · polymas-teacher-homework-skills<br>polymas-teacher-exam-skills

技能一览表.xlsx / SKILL开发方向划分 / 第 29 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B29 | 数据与学情增强 | C6 |
| C29 | 未命名列 C | §3 #26 |
| F29 | 未命名列 F | 发布成绩（作业/考试）：手动发布成绩给学生，未批完时提示剩余数 |
| G29 | 未命名列 G | 已有，需补“手动发布”“未批完提示”（产品文档：“成绩需手动发布后学生可见”“未批完时提示剩余数”） |
| H29 | 未命名列 H | P1 |
| M29 | 技能名称 | polymas-teacher-homework-skills<br>polymas-teacher-exam-skills |
| O29 | 技能的实现说明 | 刘庆峰，黄博 |
| P29 | 负责人 | @张康 |
| Q29 | 是否完成 | -是 |
| R29 | 提测时间 | 46218 |
| S29 | 测试情况 | 已测试（线上） |
| T29 | 测试时间 | 7.29 |
| A（合并继承自 A1；A1:A29） | 原值见锚点 | 第一批次<br>高优先级 |

<a id="entry-c414e5dad645f71f246f"></a>
### entry-c414e5dad645f71f246f · polymas-page-navigation

技能一览表.xlsx / SKILL开发方向划分 / 第 37 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A37 | 第一批次<br>高优先级 | 2.1 来自「用户、账号与登录」页 |
| B37 | 数据与学情增强 | 通用 |
| C37 | 未命名列 C | 平台入口导航 |
| D37 | 未命名列 D | 用户想做某操作但需在页面完成时，返回对应页面链接+一句话操作指引（全平台通用，路由表逐页扩充） |
| E37 | 未命名列 E | 目标操作/页面名\*(文本) |
| F37 | 未命名列 F | 本页 D 型全部 |
| G37 | 未命名列 G | 否 |
| H37 | 未命名列 H | P1 |
| I37 | 未命名列 I | 基础工具 |
| J37 | 未命名列 J | ①我想改一下密码；②怎么更换手机号；③头像在哪里换 |
| K37 | 未命名列 K | 路由表未命中时回退到帮助文档 skill |
| L37 | 未命名列 L | 建议新增的通用 skill：跨模块复用，后续每页走查只加路由条目 |
| M37 | 技能名称 | polymas-page-navigation |
| P37 | 负责人 | @陈源富@汪勇 |
| Q37 | 是否完成 | 是 |
| S37 | 测试情况 | 测试不通过（线上） |
| T37 | 测试时间 | 7.31 |

<a id="entry-4edf4c7e25cbfc7be650"></a>
### entry-4edf4c7e25cbfc7be650 · polymas-teacher-homework-skills

技能一览表.xlsx / SKILL开发方向划分 / 第 39 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A39 | 第一批次<br>高优先级 | 2.2 来自「作业-UI」页 |
| B39 | 数据与学情增强 | 作业 |
| C39 | 未命名列 C | 发布作业 |
| D39 | 未命名列 D | 创建并发布作业（五类型） |
| E39 | 未命名列 E | 名称\(≤20字)；描述；附件(资源库/上传)；类型(题库选题/知识点/能力训练/智能辅导/自定义，默认自定义)；班级\(多选/全选)；截止时间\(支持按班级分别设)；分值\；允许迟交(开关)；允许重做(自动通过/手动审批+次数)；允许修改N次；AI批阅(开关+批阅Agent)；关联教学计划 |
| F39 | 未命名列 F | zy-03 |
| G39 | 未命名列 G | 部分 |
| H39 | 未命名列 H | P0 |
| I39 | 未命名列 I | 教学活动专员 |
| J39 | 未命名列 J | ①帮我创建一个作业；②给新能源一班建个作业周五晚截止；③根据上次作业的薄弱知识点出一份新作业 |
| K39 | 未命名列 K | 选题类需先组卷(引导跳转)；知识点类需课程有知识图谱；缺班级/截止时间必追问 |
| L39 | 未命名列 L | 现状"有/需调试"——差量：现状参数远少于此字段全集，尤其按班级截止、提交规则三开关、AI批阅Agent 绑定 |
| M39 | 技能名称 | polymas-teacher-homework-skills |
| P39 | 负责人 | C1发布作业:@张康 |
| Q39 | 是否完成 | 是 |
| R39 | 提测时间 | 46216 |
| S39 | 测试情况 | 测试通过（线上） |
| T39 | 测试时间 | 7.29 |

<a id="entry-6748c5d9b452e4803a0e"></a>
### entry-6748c5d9b452e4803a0e · polymas-teacher-homework-skills

技能一览表.xlsx / SKILL开发方向划分 / 第 40 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B40 | 数据与学情增强 | 作业 |
| C40 | 未命名列 C | 修改作业 |
| D40 | 未命名列 D | 修改作业内容/时间/规则 |
| E40 | 未命名列 E | 作业名\*(定位)；可改字段同发布 |
| F40 | 未命名列 F | zy-13 |
| G40 | 未命名列 G | 部分 |
| H40 | 未命名列 H | P0 |
| I40 | 未命名列 I | 教学活动专员 |
| J40 | 未命名列 J | ①把XX作业截止时间延到周日晚上；②XX作业允许迟交改成开 |
| K40 | 未命名列 K | 改题目属强交互→引导跳转；改题会向学生提示 |
| L40 | 未命名列 L | 现状"有/需调试"——差量：延期(改截止时间)应支持自然语言时间、按班级改 |
| M40 | 技能名称 | polymas-teacher-homework-skills |
| P40 | 负责人 | D @张康 |
| Q40 | 是否完成 | 是 |
| R40 | 提测时间 | 46219 |
| S40 | 测试情况 | 测试通过 |
| T40 | 测试时间 | 7.29 |
| A（合并继承自 A39；A39:A50） | 原值见锚点 | 2.2 来自「作业-UI」页 |

<a id="entry-b2dd42adb1e63d2ebcd4"></a>
### entry-b2dd42adb1e63d2ebcd4 · polymas-teacher-homework-detail-skills

技能一览表.xlsx / SKILL开发方向划分 / 第 41 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B41 | 数据与学情增强 | 作业 |
| C41 | 未命名列 C | 作业完成情况查询 |
| D41 | 未命名列 D | 查作业列表/完成率/学生明细 |
| E41 | 未命名列 E | 课程；班级；作业名；状态(已批/未批/未交)；学生名 |
| F41 | 未命名列 F | zy-01/12 |
| G41 | 未命名列 G | 部分 |
| H41 | 未命名列 H | P0 |
| I41 | 未命名列 I | 教学活动专员 |
| J41 | 未命名列 J | ①XX作业谁还没交；②帮我看下XX班作业完成率；③哪些作业还有没批完的 |
| K41 | 未命名列 K | 无匹配作业时列候选 |
| L41 | 未命名列 L | 现状 3 条查询技能——差量：未交/已批/未批名单、提交次数、完成率% 维度 |
| M41 | 技能名称 | polymas-teacher-homework-detail-skills |
| P41 | 负责人 | A3完成情况查询：@朱希文 |
| Q41 | 是否完成 | 是<br> |
| R41 | 提测时间 | 46220 |
| S41 | 测试情况 | 测试不通过（线上） |
| T41 | 测试时间 | 7.31 |
| A（合并继承自 A39；A39:A50） | 原值见锚点 | 2.2 来自「作业-UI」页 |

<a id="entry-722539a5af9872f21d17"></a>
### entry-722539a5af9872f21d17 · polymas-teacher-homework-skills

技能一览表.xlsx / SKILL开发方向划分 / 第 42 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B42 | 数据与学情增强 | 作业 |
| C42 | 未命名列 C | 催交作业 |
| D42 | 未命名列 D | 向未交学生发提醒 |
| E42 | 未命名列 E | 作业名\*；范围(默认未交/指定学生) |
| F42 | 未命名列 F | zy-14 |
| G42 | 未命名列 G | 有 |
| H42 | 未命名列 H | P0 |
| I42 | 未命名列 I | 教学活动专员 |
| J42 | 未命名列 J | （现状已有） |
| L42 | 未命名列 L | 已有；建议补"按学生指定催交" |
| M42 | 技能名称 | polymas-teacher-homework-skills |
| P42 | 负责人 | D @张康 |
| Q42 | 是否完成 | 是 |
| R42 | 提测时间 | 46219 |
| S42 | 测试情况 | 已测试（预发） |
| A（合并继承自 A39；A39:A50） | 原值见锚点 | 2.2 来自「作业-UI」页 |

<a id="entry-e1f184bbe7c9f3667b16"></a>
### entry-e1f184bbe7c9f3667b16 · polymas-teacher-homework-skills

技能一览表.xlsx / SKILL开发方向划分 / 第 43 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B43 | 数据与学情增强 | 作业 |
| C43 | 未命名列 C | 打回作业 |
| D43 | 未命名列 D | 退回学生作业要求重做 |
| E43 | 未命名列 E | 作业名\；学生\；理由⚠️ |
| F43 | 未命名列 F | zy-18 |
| G43 | 未命名列 G | 有 |
| H43 | 未命名列 H | P1 |
| I43 | 未命名列 I | 教学活动专员 |
| J43 | 未命名列 J | （现状已有） |
| K43 | 未命名列 K | 打回理由是否支持待实证 |
| L43 | 未命名列 L | 已有 |
| M43 | 技能名称 | polymas-teacher-homework-skills |
| P43 | 负责人 | D @张康 |
| Q43 | 是否完成 | 是 |
| R43 | 提测时间 | 46219 |
| S43 | 测试情况 | 已测试（预发） |
| A（合并继承自 A39；A39:A50） | 原值见锚点 | 2.2 来自「作业-UI」页 |

<a id="entry-9c90ae1ad8353e19dbdf"></a>
### entry-9c90ae1ad8353e19dbdf · polymas-teacher-homework-skills

技能一览表.xlsx / SKILL开发方向划分 / 第 44 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B44 | 数据与学情增强 | 作业 |
| C44 | 未命名列 C | 审批重做申请 |
| D44 | 未命名列 D | 查询/同意/拒绝学生重做申请 |
| E44 | 未命名列 E | 作业名；学生(可批量)；决定\(同意/拒绝)；拒绝理由\(拒绝时) |
| F44 | 未命名列 F | zy-17 |
| G44 | 未命名列 G | 否 |
| H44 | 未命名列 H | P1 |
| I44 | 未命名列 I | 教学活动专员 |
| J44 | 未命名列 J | ①有没有人申请重做；②同意郭燕兵的重做申请；③把这几个申请都拒了，理由是已过补交期 |
| K44 | 未命名列 K | 仅"手动审批"作业存在申请 |
| L44 | 未命名列 L | 新增 |
| M44 | 技能名称 | polymas-teacher-homework-skills |
| P44 | 负责人 | D @张康 |
| Q44 | 是否完成 | 是 |
| R44 | 提测时间 | 46219 |
| S44 | 测试情况 | 已测试（预发） |
| A（合并继承自 A39；A39:A50） | 原值见锚点 | 2.2 来自「作业-UI」页 |

<a id="entry-dbd88da0b98d13e2970d"></a>
### entry-dbd88da0b98d13e2970d · polymas-teacher-homework-skills

技能一览表.xlsx / SKILL开发方向划分 / 第 45 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B45 | 数据与学情增强 | 作业 |
| C45 | 未命名列 C | 发布成绩 |
| D45 | 未命名列 D | 将批阅成绩发布给学生 |
| E45 | 未命名列 E | 作业名\* |
| F45 | 未命名列 F | zy-16 |
| G45 | 未命名列 G | 否 |
| H45 | 未命名列 H | P1 |
| I45 | 未命名列 I | 教学活动专员 |
| J45 | 未命名列 J | ①XX作业成绩发布一下；②把批完的作业成绩都发了 |
| K45 | 未命名列 K | 未批完时提示剩余数；能否撤回待实证 |
| L45 | 未命名列 L | 新增 |
| M45 | 技能名称 | polymas-teacher-homework-skills |
| P45 | 负责人 | C6发布成绩:@张康 |
| Q45 | 是否完成 | 是 |
| R45 | 提测时间 | 46218 |
| S45 | 测试情况 | 已测试（预发） |
| A（合并继承自 A39；A39:A50） | 原值见锚点 | 2.2 来自「作业-UI」页 |

<a id="entry-0423bc0fa16bd7a2c7bb"></a>
### entry-0423bc0fa16bd7a2c7bb · polymas-teacher-homework-skills

技能一览表.xlsx / SKILL开发方向划分 / 第 46 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B46 | 数据与学情增强 | 作业 |
| C46 | 未命名列 C | AI批阅进度与结果查询 |
| D46 | 未命名列 D | 查 AI 批阅进度、分数分布、待复核项 |
| E46 | 未命名列 E | 作业名\*；维度(进度/结果) |
| F46 | 未命名列 F | zy-21 |
| G46 | 未命名列 G | 否 |
| H46 | 未命名列 H | P1 |
| I46 | 未命名列 I | 教学活动专员 |
| J46 | 未命名列 J | ①XX作业AI批得怎么样了；②AI批阅结果里有没有分数特别低的 |
| K46 | 未命名列 K | 未开启AI批阅时说明并引导 |
| L46 | 未命名列 L | 新增；复核调整分数建议 D 型（页面完成） |
| M46 | 技能名称 | polymas-teacher-homework-skills |
| P46 | 负责人 | D @张康 |
| Q46 | 是否完成 | 是 |
| R46 | 提测时间 | 46220 |
| S46 | 测试情况 | 已测试（预发）  |
| A（合并继承自 A39；A39:A50） | 原值见锚点 | 2.2 来自「作业-UI」页 |

<a id="entry-94daef1f1d5762cc19a8"></a>
### entry-94daef1f1d5762cc19a8 · polymas-teacher-homework-detail-skills

技能一览表.xlsx / SKILL开发方向划分 / 第 47 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B47 | 数据与学情增强 | 学情 |
| C47 | 未命名列 C | 作业学情分析 |
| D47 | 未命名列 D | 作业维度学情报告：均分/优秀率/及格率/薄弱知识点/高频错题/学生预警/改进建议 |
| E47 | 未命名列 E | 作业名\*(或"最近一次") |
| F47 | 未命名列 F | zy-23 |
| G47 | 未命名列 G | 否 |
| H47 | 未命名列 H | P0 |
| I47 | 未命名列 I | 教学活动专员 |
| J47 | 未命名列 J | ①分析一下XX作业的情况；②这次作业学生哪里掌握得不好；③有哪些学生需要重点关注 |
| K47 | 未命名列 K | 无批阅数据时提示先批阅(自定义作业是没有学情分析的) |
| L47 | 未命名列 L | 新增；"根据今天的情况出作业"编排链的取数端 |
| M47 | 技能名称 | polymas-teacher-homework-detail-skills |
| P47 | 负责人 | A1 学情分析：@朱希文 |
| Q47 | 是否完成 | 是 |
| R47 | 提测时间 | 46217 |
| S47 | 测试情况 | 测试通过（线上） |
| A（合并继承自 A39；A39:A50） | 原值见锚点 | 2.2 来自「作业-UI」页 |

<a id="entry-4497e2113428165c57ce"></a>
### entry-4497e2113428165c57ce · polymas-teacher-homework-detail-skills

技能一览表.xlsx / SKILL开发方向划分 / 第 48 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B48 | 数据与学情增强 | 学情 |
| C48 | 未命名列 C | 查重报告查询 |
| D48 | 未命名列 D | 查作业查重率与相似明细 |
| E48 | 未命名列 E | 作业名\*；学生(可选) |
| F48 | 未命名列 F | zy-22 |
| G48 | 未命名列 G | 否 |
| H48 | 未命名列 H | P2 |
| I48 | 未命名列 I | 教学活动专员 |
| J48 | 未命名列 J | ①XX作业查重结果怎么样；②有没有查重率超过50%的 |
| K48 | 未命名列 K | 未开启查重时说明（查重仅智能体课程） |
| L48 | 未命名列 L | 新增 |
| M48 | 技能名称 | polymas-teacher-homework-detail-skills |
| P48 | 负责人 | D @朱希文 |
| Q48 | 是否完成 | 是 |
| R48 | 提测时间 |                     2026/7/23 |
| S48 | 测试情况 | 待测试 |
| A（合并继承自 A39；A39:A50） | 原值见锚点 | 2.2 来自「作业-UI」页 |

<a id="entry-7c3dbd4977ead828fc94"></a>
### entry-7c3dbd4977ead828fc94 · polymas-teacher-homework-skills

技能一览表.xlsx / SKILL开发方向划分 / 第 49 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B49 | 数据与学情增强 | 作业 |
| C49 | 未命名列 C | 作业数据导出 |
| D49 | 未命名列 D | 触发高级导出并送下载中心 |
| E49 | 未命名列 E | 作业名\*；范围⚠️ |
| F49 | 未命名列 F | zy-15 |
| G49 | 未命名列 G | 否 |
| H49 | 未命名列 H | P2 |
| I49 | 未命名列 I | 教学活动专员 |
| J49 | 未命名列 J | ①把XX作业的成绩导出来②把学生作答记录导出来③学生提交附件的导出④把我的批注导出来⑤作业分析下载下来 |
| K49 | 未命名列 K | 参数细节待"下载表格组件"页走查 |
| L49 | 未命名列 L | 新增；暂缓细化 |
| M49 | 技能名称 | polymas-teacher-homework-skills |
| P49 | 负责人 | D @张康 |
| Q49 | 是否完成 | 是 |
| R49 | 提测时间 | 46227 |
| S49 | 测试情况 | 待测试 |
| A（合并继承自 A39；A39:A50） | 原值见锚点 | 2.2 来自「作业-UI」页 |

<a id="entry-82571798d636e429da69"></a>
### entry-82571798d636e429da69 · polymas-teacher-homework-skills

技能一览表.xlsx / SKILL开发方向划分 / 第 50 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B50 | 数据与学情增强 | 互动 |
| C50 | 未命名列 C | 回复学生提问 |
| D50 | 未命名列 D | 查看/回复作业下的学生提问 |
| E50 | 未命名列 E | 作业名；提问(定位)；回复内容\* |
| F50 | 未命名列 F | zy-24 |
| G50 | 未命名列 G | 否 |
| H50 | 未命名列 H | P2 |
| I50 | 未命名列 I | 教学活动专员 |
| J50 | 未命名列 J | ①学生对这次作业有什么疑问；②帮我回复一下那个关于建筑材料的提问（草拟+确认） |
| K50 | 未命名列 K | 回复属对外发布，需教师确认后发送 |
| L50 | 未命名列 L | 新增；对应现状"互动-学生互动数据(否)"的教师侧 |
| M50 | 技能名称 | polymas-teacher-homework-skills |
| P50 | 负责人 | D @张康 |
| Q50 | 是否完成 | 是 |
| R50 | 提测时间 | 46227 |
| S50 | 测试情况 | 待测试 |
| A（合并继承自 A39；A39:A50） | 原值见锚点 | 2.2 来自「作业-UI」页 |

<a id="entry-a7c04cd61d28fa4638d0"></a>
### entry-a7c04cd61d28fa4638d0 · polymas-teacher-exam-skills

技能一览表.xlsx / SKILL开发方向划分 / 第 52 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A52 | 第一批次<br>高优先级 | 2.3 来自「考试-UI」页 |
| B52 | 数据与学情增强 | 考试 |
| C52 | 未命名列 C | 创建考试 |
| D52 | 未命名列 D | 创建并发布考试（四内容类型） |
| E52 | 未命名列 E | 名称\；描述；附件；类型(题库选题/随机组卷/无题/自定义)；班级\；考试时间\*(按班级)；时长(分钟)；防作弊(10 项开关)；AI批阅(开关+Agent)；成绩发布(手动/自动)；教学计划 |
| F52 | 未命名列 F | ks-01 |
| G52 | 未命名列 G | 否 |
| H52 | 未命名列 H | P1 |
| I52 | 未命名列 I | 教学活动专员 |
| J52 | 未命名列 J | ①帮我创建一个期中考试；②给新能源一班安排下周三晚 8 点的考试，90 分钟，开切屏限制和人脸验证；③用题库出一套随机卷考试（组卷引导跳转） |
| K52 | 未命名列 K | 选题/随机需题库有题；已开始班级时间不可改 |
| L52 | 未命名列 L | 新增；防作弊 10 项做成参数枚举 |
| M52 | 技能名称 | polymas-teacher-exam-skills |
| O52 | 技能的实现说明 | 随机组卷类型暂时不做 |
| P52 | 负责人 | D @张康 |
| Q52 | 是否完成 | 是 |
| R52 | 提测时间 | 46220 |
| S52 | 测试情况 | 测试不通过（线上） |

<a id="entry-2670fe3d6bec54a88590"></a>
### entry-2670fe3d6bec54a88590 · polymas-teacher-homework-detail-skills

技能一览表.xlsx / SKILL开发方向划分 / 第 53 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B53 | 数据与学情增强 | 考试 |
| C53 | 未命名列 C | 考试完成情况查询 |
| D53 | 未命名列 D | 查考试进度/完成率/学生明细/异常 |
| E53 | 未命名列 E | 考试名\*；班级；状态(已批/未批/未交)；学生 |
| F53 | 未命名列 F | ks-03 |
| G53 | 未命名列 G | 否 |
| H53 | 未命名列 H | P0 |
| I53 | 未命名列 I | 教学活动专员 |
| J53 | 未命名列 J | ①期中考谁还没交卷；②考试批阅进度怎么样；③这次考试完成率多少 |
| L53 | 未命名列 L | 新增；现状表明确要求考试数据用于交叉分析 |
| M53 | 技能名称 | polymas-teacher-homework-detail-skills |
| P53 | 负责人 | A3完成情况查询：@朱希文 |
| Q53 | 是否完成 | 是 |
| R53 | 提测时间 |                   2026/0717 |
| S53 | 测试情况 | 已测试（预发） |
| A（合并继承自 A52；A52:A59） | 原值见锚点 | 2.3 来自「考试-UI」页 |

<a id="entry-afc02de8abc15e43a910"></a>
### entry-afc02de8abc15e43a910 · polymas-teacher-exam-skills

技能一览表.xlsx / SKILL开发方向划分 / 第 54 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B54 | 数据与学情增强 | 考试 |
| C54 | 未命名列 C | 修改考试 |
| D54 | 未命名列 D | 改时间/时长/设置 |
| E54 | 未命名列 E | 考试名\*；可改字段 |
| F54 | 未命名列 F | ks-04 |
| G54 | 未命名列 G | 否 |
| H54 | 未命名列 H | P1 |
| I54 | 未命名列 I | 教学活动专员 |
| J54 | 未命名列 J | ①把期中考延长半小时；②考试时间改到下周五 |
| K54 | 未命名列 K | 已开始班级不可改时间；延后已结束考试清空已打回试卷（必须提示确认） |
| L54 | 未命名列 L | 新增；规则复杂，执行前强确认 |
| M54 | 技能名称 | polymas-teacher-exam-skills |
| P54 | 负责人 | D @张康 |
| Q54 | 是否完成 | 是 |
| R54 | 提测时间 | 46223 |
| S54 | 测试情况 | 测试不通过（线上） |
| A（合并继承自 A52；A52:A59） | 原值见锚点 | 2.3 来自「考试-UI」页 |

<a id="entry-9895f15780f76f675764"></a>
### entry-9895f15780f76f675764 · polymas-teacher-exam-skills

技能一览表.xlsx / SKILL开发方向划分 / 第 55 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B55 | 数据与学情增强 | 考试 |
| C55 | 未命名列 C | 考试批量操作 |
| D55 | 未命名列 D | 全部催交/全部打回/公布试卷及答案 |
| E55 | 未命名列 E | 考试名\；动作\(三选一) |
| F55 | 未命名列 F | ks-09~12 |
| G55 | 未命名列 G | 否 |
| H55 | 未命名列 H | P1 |
| I55 | 未命名列 I | 教学活动专员 |
| J55 | 未命名列 J | ①考试没交的都催一下；③把试卷和答案公布给学生 |
| K55 | 未命名列 K | 打回属重操作需确认 |
| L55 | 未命名列 L | 新增；四个菜单动作合并为一个带动作参数的 skill |
| M55 | 技能名称 | polymas-teacher-exam-skills |
| P55 | 负责人 | D @张康 |
| Q55 | 是否完成 | 是 |
| R55 | 提测时间 | 46223 |
| S55 | 测试情况 | 测试不通过（线上） |
| A（合并继承自 A52；A52:A59） | 原值见锚点 | 2.3 来自「考试-UI」页 |

<a id="entry-87297fe6143567a23a89"></a>
### entry-87297fe6143567a23a89 · polymas-teacher-exam-skills

技能一览表.xlsx / SKILL开发方向划分 / 第 56 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B56 | 数据与学情增强 | 考试 |
| C56 | 未命名列 C | 发布考试成绩 |
| D56 | 未命名列 D | 手动发布成绩 |
| E56 | 未命名列 E | 考试名\* |
| F56 | 未命名列 F | ks-13 |
| G56 | 未命名列 G | 否 |
| H56 | 未命名列 H | P1 |
| I56 | 未命名列 I | 教学活动专员 |
| J56 | 未命名列 J | ①期中考成绩发布一下 |
| K56 | 未命名列 K | 未批完提示；自动发布模式下说明无需操作 |
| L56 | 未命名列 L | 新增；与作业"发布成绩"同族 |
| M56 | 技能名称 | polymas-teacher-exam-skills |
| P56 | 负责人 | C6发布成绩:@张康 |
| Q56 | 是否完成 | 是 |
| R56 | 提测时间 | 46218 |
| S56 | 测试情况 | 测试通过（线上） |
| A（合并继承自 A52；A52:A59） | 原值见锚点 | 2.3 来自「考试-UI」页 |

<a id="entry-a6da5e48298d08e26309"></a>
### entry-a6da5e48298d08e26309 · polymas-teacher-exam-skills

技能一览表.xlsx / SKILL开发方向划分 / 第 57 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B57 | 数据与学情增强 |                        |
| C57 | 未命名列 C | 创建补考 |
| D57 | 未命名列 D | 按条件筛选学生创建补考 |
| E57 | 未命名列 E | 原考试名\；分数线(低于 X 分)；补考学生(自动筛+可调)；时间\；时长；成绩规则；防作弊 |
| F57 | 未命名列 F | ks-14 |
| G57 | 未命名列 G | 否 |
| H57 | 未命名列 H | P1 |
| I57 | 未命名列 I | 教学活动专员 |
| J57 | 未命名列 J | ①给低于 60 分的学生安排补考；②期中考不及格的下周三晚补考 |
| K57 | 未命名列 K | 原考试需已出成绩；支持多轮补考 |
| L57 | 未命名列 L | 新增；分数线筛选是对话强项 |
| M57 | 技能名称 | polymas-teacher-exam-skills |
| P57 | 负责人 | D @张康 |
| Q57 | 是否完成 | 是 |
| R57 | 提测时间 | 46225 |
| S57 | 测试情况 | 测试通过（线上） |
| A（合并继承自 A52；A52:A59） | 原值见锚点 | 2.3 来自「考试-UI」页 |

<a id="entry-62df32e9e055afcf3ee7"></a>
### entry-62df32e9e055afcf3ee7 · polymas-teacher-exam-skills

技能一览表.xlsx / SKILL开发方向划分 / 第 58 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B58 | 数据与学情增强 | 考试 |
| C58 | 未命名列 C | 监考异常查询 |
| D58 | 未命名列 D | 查监考异常统计与名单 |
| E58 | 未命名列 E | 考试名\*；(学生) |
| F58 | 未命名列 F | ks-05/07 |
| G58 | 未命名列 G | 否 |
| H58 | 未命名列 H | P2 |
| I58 | 未命名列 I | 教学活动专员 |
| J58 | 未命名列 J | ①这场考试有什么异常情况；②谁切屏次数超了 |
| K58 | 未命名列 K | 未开监考时说明 |
| L58 | 未命名列 L | 新增；实时盯屏是 D 型，事后查询是 B 型 |
| M58 | 技能名称 | polymas-teacher-exam-skills |
| P58 | 负责人 | D @张康 |
| Q58 | 是否完成 | 是 |
| R58 | 提测时间 | 46226 |
| S58 | 测试情况 | 测试通过（线上） |
| A（合并继承自 A52；A52:A59） | 原值见锚点 | 2.3 来自「考试-UI」页 |

<a id="entry-ce09ed5e83b74d96a186"></a>
### entry-ce09ed5e83b74d96a186 · polymas-teacher-homework-detail-skills

技能一览表.xlsx / SKILL开发方向划分 / 第 59 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B59 | 数据与学情增强 | 学情 |
| C59 | 未命名列 C | 考试学情分析 |
| D59 | 未命名列 D | 考试维度学情报告 |
| E59 | 未命名列 E | 考试名\* |
| F59 | 未命名列 F | ks-15 |
| G59 | 未命名列 G | 否 |
| H59 | 未命名列 H | P0 |
| I59 | 未命名列 I | 教学活动专员 |
| J59 | 未命名列 J | ①分析一下期中考情况；②考试反映出哪些薄弱点 |
| K59 | 未命名列 K | tab 内容待实证 |
| L59 | 未命名列 L | 新增；与作业学情分析同族，建议一个 skill 双实体 |
| M59 | 技能名称 | polymas-teacher-homework-detail-skills |
| P59 | 负责人 | A1 学情分析：@朱希文 |
| Q59 | 是否完成 | 是 |
| R59 | 提测时间 |                   2026/0717 |
| S59 | 测试情况 | 已测试（预发） |
| A（合并继承自 A52；A52:A59） | 原值见锚点 | 2.3 来自「考试-UI」页 |

<a id="entry-42e5e14b7b7f67e178a8"></a>
### entry-42e5e14b7b7f67e178a8 · polymas-teacher-score-skills

技能一览表.xlsx / SKILL开发方向划分 / 第 61 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A61 | 第一批次<br>高优先级 | 2.4 来自「成绩管理-UI」页 |
| B61 | 数据与学情增强 | 成绩 |
| C61 | 未命名列 C | 成绩查询 |
| D61 | 未命名列 D | 查总成绩与分项成绩（考勤/平时/作业/考试/实验/AI翻转/自定义）<br>https://hike-teaching-center.polymas.com/agent-course-full/course-hub/j2DpGLjjXWiLwKgv99a1/grade-manage |
| E61 | 未命名列 E | 班级；学生(可选)；维度(总成绩/分项)；统计口径(个人/班级分布) |
| F61 | 未命名列 F | cj-01/02 |
| G61 | 未命名列 G | 否 |
| H61 | 未命名列 H | P0 |
| I61 | 未命名列 I | 学课管理专员 |
| J61 | 未命名列 J | ①查一下新能源一班的总成绩分布；②邓文杰这学期成绩怎么样，弱在哪；③谁缺勤次数最多 |
| K61 | 未命名列 K | 数据有截止时间需随答复说明；成绩构成随课程配置变化 |
| L61 | 未命名列 L | 新增；跨模块追因（联动作业/考试学情） |
| M61 | 技能名称 | polymas-teacher-score-skills |
| O61 | 技能的实现说明 | 多维成绩查询：总成绩 / 考勤 / 平时 / 作业 / 考试 / 自定义考核项<br>支持个人与班级分布两种视角 |
| P61 | 负责人 | D @倪吉龙 |
| Q61 | 是否完成 | 是 |
| R61 | 提测时间 | 46226 |
| S61 | 测试情况 | 测试通过（线上） |
| T61 | 测试时间 | 7.28 |

<a id="entry-aaa73690d6def6d38198"></a>
### entry-aaa73690d6def6d38198 · polymas-teacher-score-skills

技能一览表.xlsx / SKILL开发方向划分 / 第 62 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B62 | 数据与学情增强 | 成绩 |
| C62 | 未命名列 C | 成绩加权设置 |
| D62 | 未命名列 D | 设置/调整成绩权重与考核项 |
| E62 | 未命名列 E | 各项权重(合计100)；缺勤扣分/次；增删考核项(AI翻转/自定义)；应用到其他班级(开关) |
| F62 | 未命名列 F | cj-03 |
| G62 | 未命名列 G | 否 |
| H62 | 未命名列 H | P1 |
| I62 | 未命名列 I | 学课管理专员 |
| J62 | 未命名列 J | ①把作业权重调到 40%考试 30%；②加一个自定义考核项"课堂展示"占 10 分；③把这套权重应用到其他班 |
| K62 | 未命名列 K | 合计必须=100 需校验追问；改权重影响已出成绩需确认 |
| L62 | 未命名列 L | 新增 |
| M62 | 技能名称 | polymas-teacher-score-skills |
| O62 | 技能的实现说明 | 成绩加权设置（服务端持久化）：<br>四项权重配置、缺勤扣分、互动计分、应用到其他班级、最终成绩设置 |
| P62 | 负责人 | D @倪吉龙 |
| Q62 | 是否完成 | 是 |
| R62 | 提测时间 | 46226 |
| S62 | 测试情况 | 测试通过（线上） |
| T62 | 测试时间 | 7.31 |
| A（合并继承自 A61；A61:A66） | 原值见锚点 | 2.4 来自「成绩管理-UI」页 |

<a id="entry-f3ff068dddc66b60e2f1"></a>
### entry-f3ff068dddc66b60e2f1 · polymas-teacher-score-skills

技能一览表.xlsx / SKILL开发方向划分 / 第 63 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B63 | 数据与学情增强 | 成绩 |
| C63 | 未命名列 C | 添加线下考勤 |
| D63 | 未命名列 D | 录入一次线下考勤 |
| E63 | 未命名列 E | 班级\；缺勤/出勤名单\(说人名即可，其余默认) |
| F63 | 未命名列 F | cj-04 |
| G63 | 未命名列 G | 否 |
| H63 | 未命名列 H | P1 |
| I63 | 未命名列 I | 学课管理专员 |
| J63 | 未命名列 J | ①记一次考勤，王蓝星和刘捷没来；②今天全勤，帮我记上 |
| K63 | 未命名列 K | 名单按"默认出勤+例外缺勤"理解；可删除本次考勤兜底 |
| L63 | 未命名列 L | 新增；口述点名是对话强项 |
| M63 | 技能名称 | polymas-teacher-score-skills |
| O63 | 技能的实现说明 | 线下考勤全生命周期：<br>查询考勤列表、录入一次考勤、修改考勤（改为已签/未签）、删除本次考勤 |
| P63 | 负责人 | D @倪吉龙 |
| Q63 | 是否完成 | 是 |
| R63 | 提测时间 | 46226 |
| S63 | 测试情况 | 测试通过（线上） |
| T63 | 测试时间 | 7.31 |
| A（合并继承自 A61；A61:A66） | 原值见锚点 | 2.4 来自「成绩管理-UI」页 |

<a id="entry-8e57dd2b04c73463c7e4"></a>
### entry-8e57dd2b04c73463c7e4 · polymas-teacher-score-skills

技能一览表.xlsx / SKILL开发方向划分 / 第 64 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B64 | 数据与学情增强 | 成绩 |
| C64 | 未命名列 C | 添加线下成绩 |
| D64 | 未命名列 D | 录入线下成绩列 |
| E64 | 未命名列 E | 类别(作业/实验/自定义)；列名；分数(逐生口述 或 Excel 按官方模板导入) |
| F64 | 未命名列 F | cj-05；jx-02 |
| G64 | 未命名列 G | 否 |
| H64 | 未命名列 H | P1 |
| I64 | 未命名列 I | 学课管理专员 |
| J64 | 未命名列 J | ①把小测成绩录进去：张三 90、李四 85…；②这个 Excel 是实验二成绩，帮我导入 |
| K64 | 未命名列 K | 平台校验：学号不在教学班则该行拒绝（"教学班下未找到该学生"）；建议复用 ChatExcel 解析 |
| L64 | 未命名列 L | 新增；线下作业页已证实双录入方式（教学活动页 jx-02） |
| M64 | 技能名称 | polymas-teacher-score-skills |
| O64 | 技能的实现说明 | 线下成绩（考试/作业）全生命周期：<br>增/改/删、Excel 模板导入、导入结果查询 |
| P64 | 负责人 | D @倪吉龙 |
| Q64 | 是否完成 | 是 |
| R64 | 提测时间 | 46226 |
| S64 | 测试情况 | 测试通过（线上） |
| T64 | 测试时间 | 7.31 |
| A（合并继承自 A61；A61:A66） | 原值见锚点 | 2.4 来自「成绩管理-UI」页 |

<a id="entry-9bbb6ca10088d58dcbce"></a>
### entry-9bbb6ca10088d58dcbce · polymas-teacher-score-skills

技能一览表.xlsx / SKILL开发方向划分 / 第 65 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B65 | 数据与学情增强 | 成绩 |
| C65 | 未命名列 C | 成绩导出 |
| D65 | 未命名列 D | 下载各类成绩/高级导出（预发开发中，暂未接） |
| E65 | 未命名列 E | 范围(tab)\*；方式(普通/高级) |
| F65 | 未命名列 F | cj-09 |
| G65 | 未命名列 G | 否 |
| H65 | 未命名列 H | P2 |
| I65 | 未命名列 I | 学课管理专员 |
| J65 | 未命名列 J | ①把总成绩导出来 |
| K65 | 未命名列 K | 文件进下载中心 |
| L65 | 未命名列 L | 新增；与作业导出同族 |
| M65 | 技能名称 | polymas-teacher-score-skills |
| O65 | 技能的实现说明 | 成绩下载、下载中心、文件地址 |
| P65 | 负责人 | D @倪吉龙 |
| Q65 | 是否完成 | 是 |
| R65 | 提测时间 | 46226 |
| S65 | 测试情况 | 测试通过（线上） |
| T65 | 测试时间 | 7.31 |
| A（合并继承自 A61；A61:A66） | 原值见锚点 | 2.4 来自「成绩管理-UI」页 |

<a id="entry-76c5778c3fb6f68e06e2"></a>
### entry-76c5778c3fb6f68e06e2 · polymas-teacher-score-skills

技能一览表.xlsx / SKILL开发方向划分 / 第 66 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B66 | 数据与学情增强 | 成绩 |
| C66 | 未命名列 C | 学生成绩可见性开关 |
| D66 | 未命名列 D | 允许/关闭学生查看总成绩 |
| E66 | 未命名列 E | 开关\* |
| F66 | 未命名列 F | cj-07 |
| G66 | 未命名列 G | 否 |
| H66 | 未命名列 H | P2 |
| I66 | 未命名列 I | 学课管理专员 |
| J66 | 未命名列 J | ①让学生能看到总成绩 |
| L66 | 未命名列 L | 新增 |
| M66 | 技能名称 | polymas-teacher-score-skills |
| O66 | 技能的实现说明 | 学生查看开关 |
| P66 | 负责人 | D @倪吉龙 |
| Q66 | 是否完成 | 是 |
| R66 | 提测时间 | 46226 |
| S66 | 测试情况 | 测试通过（线上） |
| T66 | 测试时间 | 7.31 |
| A（合并继承自 A61；A61:A66） | 原值见锚点 | 2.4 来自「成绩管理-UI」页 |

<a id="entry-d339a57099d2cc2d09fc"></a>
### entry-d339a57099d2cc2d09fc · polymas-teacher-class-skills<br>polymas-teacher-class-student-skills

技能一览表.xlsx / SKILL开发方向划分 / 第 68 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A68 | 第一批次<br>高优先级 | 2.5 来自「课程管理-UI」页 |
| B68 | 数据与学情增强 | 班级 |
| C68 | 未命名列 C | 班级学生查询 |
| D68 | 未命名列 D | 查学生名单/入班状态/标签/院系<br>https://hike-teaching-center.polymas.com/agent-course-full/course-hub/j2DpGLjjXWiLwKgv99a1/course-manage/student-manager |
| E68 | 未命名列 E | 班级；状态(已入班/待审核/待激活)；标签；学生名 |
| F68 | 未命名列 F | kc-01 |
| G68 | 未命名列 G | 部分 |
| H68 | 未命名列 H | P0 |
| I68 | 未命名列 I | 学课管理专员 |
| J68 | 未命名列 J | ①一班有多少学生；②还有谁没激活；③重点关注的学生有哪些 |
| L68 | 未命名列 L | 现状"学生数据(有)"——差量：入班状态与标签维度；"状态(否)"之谜已解 |
| M68 | 技能名称 | polymas-teacher-class-skills<br>polymas-teacher-class-student-skills |
| O68 | 技能的实现说明 | 入班状态、标签、院系等信息 |
| P68 | 负责人 | A4班级学生查询：@倪吉龙 |
| Q68 | 是否完成 | 是 |
| R68 | 提测时间 | 46223 |
| S68 | 测试情况 | 测试不通过（线上，有bug） |
| T68 | 测试时间 | 7.30. |

<a id="entry-4fc163f07f51d69bd7c1"></a>
### entry-4fc163f07f51d69bd7c1 · polymas-teacher-class-student-skills

技能一览表.xlsx / SKILL开发方向划分 / 第 69 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B69 | 数据与学情增强 | 班级 |
| C69 | 未命名列 C | 审核入班申请 |
| D69 | 未命名列 D | 同意/忽略入班申请 |
| E69 | 未命名列 E | 班级；学生(或"全部") |
| F69 | 未命名列 F | kc-05 |
| G69 | 未命名列 G | 否 |
| H69 | 未命名列 H | P1 |
| I69 | 未命名列 I | 学课管理专员 |
| J69 | 未命名列 J | ①有入班申请吗；②把待审核的全部同意 |
| K69 | 未命名列 K | 忽略操作建议二次确认 |
| L69 | 未命名列 L | 新增 |
| M69 | 技能名称 | polymas-teacher-class-student-skills |
| O69 | 技能的实现说明 | 1. 按入班状态查询课程/班级下的学生信息，支持已入班、待审核、待激活三种状态路由<br>2. 审核入班申请：查看待审核列表、批量同意全部申请、忽略指定申请<br>3. 待激活学生管理：查看待激活列表、删除待激活学生 |
| P69 | 负责人 | C5审核入班申请：@倪吉龙 |
| Q69 | 是否完成 | 是 |
| R69 | 提测时间 | 46223 |
| S69 | 测试情况 | 待测试 |
| A（合并继承自 A68；A68:A75） | 原值见锚点 | 2.5 来自「课程管理-UI」页 |

<a id="entry-94d5f49f03eb8c4dcea5"></a>
### entry-94d5f49f03eb8c4dcea5 · polymas-teacher-class-student-skills

技能一览表.xlsx / SKILL开发方向划分 / 第 70 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B70 | 数据与学情增强 | 班级 |
| C70 | 未命名列 C | 学生调班/退班 |
| D70 | 未命名列 D | 调整学生班级归属 |
| E70 | 未命名列 E | 学生\*(可多)；动作(调班/退班)；目标班级(调班时) |
| F70 | 未命名列 F | kc-03 |
| G70 | 未命名列 G | 否 |
| H70 | 未命名列 H | P1 |
| I70 | 未命名列 I | 学课管理专员 |
| J70 | 未命名列 J | ①把郭燕兵调到二班；②这几个学生退班 |
| K70 | 未命名列 K | 退班需确认 |
| L70 | 未命名列 L | 新增 |
| M70 | 技能名称 | polymas-teacher-class-student-skills |
| O70 | 技能的实现说明 | 学生调班/退班：调整学生班级归属，查当前班级→查目标班级→执行调班/退班 |
| P70 | 负责人 | D @倪吉龙 |
| Q70 | 是否完成 | 是 |
| R70 | 提测时间 | 46223 |
| S70 | 测试情况 | 测试通过（线上） |
| T70 | 测试时间 | 7.30. |
| A（合并继承自 A68；A68:A75） | 原值见锚点 | 2.5 来自「课程管理-UI」页 |

<a id="entry-ae8a67f7cc6336ef6742"></a>
### entry-ae8a67f7cc6336ef6742 · polymas-teacher-class-student-skills

技能一览表.xlsx / SKILL开发方向划分 / 第 71 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B71 | 数据与学情增强 | 班级 |
| C71 | 未命名列 C | 学生标签管理 |
| D71 | 未命名列 D | 给学生打/改标签 |
| E71 | 未命名列 E | 学生\(可批量)；标签\ |
| F71 | 未命名列 F | kc-04 |
| G71 | 未命名列 G | 否 |
| H71 | 未命名列 H | P1 |
| I71 | 未命名列 I | 学课管理专员 |
| J71 | 未命名列 J | ①把这次不及格的都标为重点关注（编排）；②给王蓝星打个优生标签 |
| K71 | 未命名列 K | 标签枚举待实证 |
| L71 | 未命名列 L | 新增；与成绩/学情联动价值高 |
| M71 | 技能名称 | polymas-teacher-class-student-skills |
| O71 | 技能的实现说明 | 学生标签管理：打/改/查/删标签，智能复用语义相近的已有标签避免重复创建 |
| P71 | 负责人 | D @倪吉龙 |
| Q71 | 是否完成 | 是 |
| R71 | 提测时间 | 46223 |
| S71 | 测试情况 | 测试通过（线上） |
| T71 | 测试时间 | 7.30. |
| A（合并继承自 A68；A68:A75） | 原值见锚点 | 2.5 来自「课程管理-UI」页 |

<a id="entry-5dac373c854851eac375"></a>
### entry-5dac373c854851eac375 · polymas-teacher-class-group-skills

技能一览表.xlsx / SKILL开发方向划分 / 第 72 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B72 | 数据与学情增强 | 班级 |
| C72 | 未命名列 C | 创建分组方案 |
| D72 | 未命名列 D | 建随机/自由/指定分组方案 |
| E72 | 未命名列 E | 方案名\；班级\；方式\*(随机/自由/指定)；组数(随机自动均分) |
| F72 | 未命名列 F | kc-15 |
| G72 | 未命名列 G | 否 |
| H72 | 未命名列 H | P1 |
| I72 | 未命名列 I | 学课管理专员 |
| J72 | 未命名列 J | ①把一班随机分成 5 组；②建一个自由组队方案让学生自己报 |
| K72 | 未命名列 K | 指定分组的逐人分配引导页面完成 |
| L72 | 未命名列 L | 新增；小组作业的前置 |
| M72 | 技能名称 | polymas-teacher-class-group-skills |
| O72 | 技能的实现说明 | 1. 查询课程下的分组方案列表、方案详情、组内学生名单及未进组学生 <br>2. 创建随机分组、自由分组或指定分组方案，支持跨班/不可跨班配置<br>3. 编辑或删除已有的分组方案，支持修改方案名称和简介<br>4. 管理分组方案内的小组和成员：调组、小组改名、小组删除 |
| P72 | 负责人 | D @倪吉龙 |
| Q72 | 是否完成 | 是 |
| R72 | 提测时间 | 46223 |
| S72 | 测试情况 | 测试不通过（线上） |
| T72 | 测试时间 | 7.29 |
| A（合并继承自 A68；A68:A75） | 原值见锚点 | 2.5 来自「课程管理-UI」页 |

<a id="entry-13ac8fe6664ec558aa3a"></a>
### entry-13ac8fe6664ec558aa3a · polymas-teacher-exam-skills

技能一览表.xlsx / SKILL开发方向划分 / 第 73 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B73 | 数据与学情增强 | 班级 |
| C73 | 未命名列 C | 我的权限查询 |
| D73 | 未命名列 D | 查自己(或团队成员)的班级与功能权限 |
| E73 | 未命名列 E | 成员(默认自己) |
| F73 | 未命名列 F | kc-12 |
| G73 | 未命名列 G | 否 |
| H73 | 未命名列 H | P1 |
| I73 | 未命名列 I | 基础工具 |
| J73 | 未命名列 J | ①我能发布哪些班级的考试；②刘亦菲管哪些班、有什么权限 |
| K73 | 未命名列 K | 权限不足时所有 skill 的统一解释出口 |
| L73 | 未命名列 L | 新增；Agent 权限校验的用户侧镜像 |
| M73 | 技能名称 | polymas-teacher-exam-skills |
| P73 | 负责人 | C4我的权限查询:@张康 |
| A（合并继承自 A68；A68:A75） | 原值见锚点 | 2.5 来自「课程管理-UI」页 |

<a id="entry-94736a5214b0e4ba3ee4"></a>
### entry-94736a5214b0e4ba3ee4 · polymas-teacher-course-skills

技能一览表.xlsx / SKILL开发方向划分 / 第 74 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B74 | 数据与学情增强 | 课程 |
| C74 | 未命名列 C | 课程信息查询/编辑 |
| D74 | 未命名列 D | 查/改课程基本信息 |
| E74 | 未命名列 E | 课程\*；可改字段(名称/层次/类型/学分学时/学科/简介) |
| F74 | 未命名列 F | kc-18 |
| G74 | 未命名列 G | 部分 |
| H74 | 未命名列 H | P2 |
| I74 | 未命名列 I | 学课管理专员 |
| J74 | 未命名列 J | ①这门课多少学分；②把课程简介改成… |
| K74 | 未命名列 K | 封面上传引导页面 |
| L74 | 未命名列 L | 现状"课程名称(有)"——差量：其余字段 |
| M74 | 技能名称 | polymas-teacher-course-skills |
| P74 | 负责人 | D @陈源富 |
| Q74 | 是否完成 | 是 |
| S74 | 测试情况 | 待测试 |
| A（合并继承自 A68；A68:A75） | 原值见锚点 | 2.5 来自「课程管理-UI」页 |

<a id="entry-0ceaaa8490aefba0b720"></a>
### entry-0ceaaa8490aefba0b720 · polymas-teacher-class-skills

技能一览表.xlsx / SKILL开发方向划分 / 第 75 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B75 | 数据与学情增强 | 班级 |
| C75 | 未命名列 C | 导出学生名单 |
| D75 | 未命名列 D | 导出名单文件 |
| E75 | 未命名列 E | 班级；范围 |
| F75 | 未命名列 F | kc-08 |
| G75 | 未命名列 G | 否 |
| H75 | 未命名列 H | P2 |
| I75 | 未命名列 I | 学课管理专员 |
| J75 | 未命名列 J | ①把一班名单导出来 |
| L75 | 未命名列 L | 新增 |
| M75 | 技能名称 | polymas-teacher-class-skills |
| P75 | 负责人 | D @陈源富 |
| Q75 | 是否完成 | 是 |
| S75 | 测试情况 | 待测试 |
| A（合并继承自 A68；A68:A75） | 原值见锚点 | 2.5 来自「课程管理-UI」页 |

<a id="entry-c13445d5a98efc3866cd"></a>
### entry-c13445d5a98efc3866cd · polymas-course-overview-skills

技能一览表.xlsx / SKILL开发方向划分 / 第 77 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A77 | 第一批次<br>高优先级 | 2.6 来自「课程主页(ai智课)-UI」页 |
| B77 | 数据与学情增强 | 课程 |
| C77 | 未命名列 C | 课程概览查询 |
| D77 | 未命名列 D | 一句话拿到课程全貌：教学计划/AI知识库资源数/AI课代表对话量/班级/近期活动/待办 |
| E77 | 未命名列 E | 课程\*；学期 |
| F77 | 未命名列 F | zc-01/03 |
| G77 | 未命名列 G | 否 |
| H77 | 未命名列 H | P1 |
| I77 | 未命名列 I | 学课管理专员 |
| J77 | 未命名列 J | ①我这门课现在什么情况；②理论力学这学期跑得怎么样 |
| K77 | 未命名列 K | 数据牌各有更新时间 |
| L77 | 未命名列 L | 新增；对话产品的"课程仪表盘" |
| M77 | 技能名称 | polymas-course-overview-skills |
| P77 | 负责人 | D @孟祥利 |
| Q77 | 是否完成 | 是 |
| R77 | 提测时间 |                     2026/7/22 |
| S77 | 测试情况 | 测试不通过（线上） |
| T77 | 测试时间 | 7.29 |

<a id="entry-3dddbf61e67e361f2e31"></a>
### entry-3dddbf61e67e361f2e31 · polymas-course-obe-skills

技能一览表.xlsx / SKILL开发方向划分 / 第 78 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B78 | 数据与学情增强 | 课程 |
| C78 | 未命名列 C | 课程达成度查询 |
| D78 | 未命名列 D | OBE 达成度：课程/单元/班级/学生四级 |
| E78 | 未命名列 E | 课程\*；班级；层级(课程/单元/学生) |
| F78 | 未命名列 F | zc-06 |
| G78 | 未命名列 G | 否 |
| H78 | 未命名列 H | P1 |
| I78 | 未命名列 I | 学科管理员 |
| J78 | 未命名列 J | ①这门课达成度多少；③机械工程1班为什么只有26% |
| K78 | 未命名列 K | 未配权重时引导设置；数据日更需注明 |
| L78 | 未命名列 L | 新增；与成绩权重、OBE-UI 页联动 |
| M78 | 技能名称 | polymas-course-obe-skills |
| P78 | 负责人 | D @孟祥利 |
| Q78 | 是否完成 | 是 |
| R78 | 提测时间 |                     2026/7/22 |
| S78 | 测试情况 | 测试不通过（线上） |
| A（合并继承自 A77；A77:A78） | 原值见锚点 | 2.6 来自「课程主页(ai智课)-UI」页 |

<a id="entry-cef143fcde54c18ca86a"></a>
### entry-cef143fcde54c18ca86a · polymas-teacher-teaching-plan

技能一览表.xlsx / SKILL开发方向划分 / 第 80 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A80 | 第一批次<br>高优先级 | 2.7 来自「教学计划-UI」页 |
| B80 | 数据与学情增强 | 课程 |
| C80 | 未命名列 C | 教学计划查询 |
| D80 | 未命名列 D | 查计划结构/主题知识点/关联活动 |
| E80 | 未命名列 E | 课程\*；单元/主题(可选) |
| F80 | 未命名列 F | jh-02/05 |
| G80 | 未命名列 G | 部分 |
| H80 | 未命名列 H | P1 |
| I80 | 未命名列 I | 学科管理员 |
| J80 | 未命名列 J | ①这门课的教学计划是什么安排；②第三单元有哪些知识点；③1.1 主题关联了哪些作业 |
| K80 | 未命名列 K | 无计划时引导创建 |
| L80 | 未命名列 L | 现状"教学进度(是/0611/学科管理员)"疑似即此——待与研发对齐口径 |
| M80 | 技能名称 | polymas-teacher-teaching-plan |
| P80 | 负责人 | C6 @陈源富 |
| Q80 | 是否完成 | 是 |
| S80 | 测试情况 | 待测试 |

<a id="entry-cd54046cc5e7913c9568"></a>
### entry-cd54046cc5e7913c9568 · polymas-teacher-teaching-plan

技能一览表.xlsx / SKILL开发方向划分 / 第 81 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B81 | 数据与学情增强 | 课程 |
| C81 | 未命名列 C | 教学计划编辑 |
| D81 | 未命名列 D | 增删改单元/主题/知识点标签 |
| E81 | 未命名列 E | 课程\*；操作(加单元/加主题/改名/排序/删)；内容 |
| F81 | 未命名列 F | jh-01 |
| G81 | 未命名列 G | 否 |
| H81 | 未命名列 H | P1 |
| I81 | 未命名列 I | 学科管理员 |
| J81 | 未命名列 J | ①在第二单元后面加一个"刚体力学"单元；②把 1.3 的主题名改成…；③根据这份教材目录帮我生成教学计划（生成+写入，编排深度写作） |
| K81 | 未命名列 K | 删除需确认；结构变化影响达成度统计 |
| L81 | 未命名列 L | 新增；"AI 生成教学计划草稿→确认写入"是高价值编排 |
| M81 | 技能名称 | polymas-teacher-teaching-plan |
| P81 | 负责人 | D  @陈源富 |
| Q81 | 是否完成 | 是 |
| S81 | 测试情况 | 测试不通过（线上，有bug） |
| T81 | 测试时间 | 7.30. |
| A（合并继承自 A80；A80:A81） | 原值见锚点 | 2.7 来自「教学计划-UI」页 |

<a id="entry-1beec9de583076f7f60b"></a>
### entry-1beec9de583076f7f60b · generate-questions

技能一览表.xlsx / SKILL开发方向划分 / 第 83 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A83 | 第一批次<br>高优先级 | 2.8 来自「题库-UI」页 |
| B83 | 数据与学情增强 | 题库 |
| C83 | 未命名列 C | AI 出题 |
| D83 | 未命名列 D | 按要求生成题目入题库/组卷 |
| E83 | 未命名列 E | 出题要求\*(自然语言)；题型和题数(8 类，每类≤20)；考核目标(布鲁姆六级)；参考资料(文件/资源)；学科；保存位置 |
| F83 | 未命名列 F | tk-06 |
| G83 | 未命名列 G | 否 |
| H83 | 未命名列 H | P0 |
| I83 | 未命名列 I | 教学活动专员 |
| J83 | 未命名列 J | ①出 10 道牛顿第二定律的应用题；②根据这份讲义出一套章节测验，要有 5 道单选 3 道简答；③按"分析"层次出几道案例题 |
| K83 | 未命名列 K | 每类≤20 题；生成后需教师确认入库 |
| L83 | 未命名列 L | 新增；出题设置页参数可直接映射，天然对话型功能 |
| M83 | 技能名称 | generate-questions |
| P83 | 负责人 | B1AI出题：@赵洪恩 |
| Q83 | 是否完成 | 是 |
| R83 | 提测时间 | 46227 |
| S83 | 测试情况 | 测试不通过（线上，有bug） |
| T83 | 测试时间 | 8.5 |

<a id="entry-66bcc2de8c69f554221d"></a>
### entry-66bcc2de8c69f554221d · polymas-teacher-questions-query

技能一览表.xlsx / SKILL开发方向划分 / 第 84 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B84 | 数据与学情增强 | 题库 |
| C84 | 未命名列 C | 题库查询 |
| D84 | 未命名列 D | 查题目数量/分布/具体题目 |
| E84 | 未命名列 E | 范围(课程/我的/团队/共享)；题型；知识点；难度；关键词 |
| F84 | 未命名列 F | tk-01 |
| G84 | 未命名列 G | 否 |
| H84 | 未命名列 H | P1 |
| I84 | 未命名列 I | 教学活动专员 |
| J84 | 未命名列 J | ①题库里有多少道单选题；②关于电磁感应的题够不够出一套卷子；③找几道难度高的证明题 |
| K84 | 未命名列 K | 空题库时引导 AI 出题/导入 |
| L84 | 未命名列 L | 新增；组卷前的探底查询 |
| M84 | 技能名称 | polymas-teacher-questions-query |
| P84 | 负责人 | D @赵洪恩 |
| Q84 | 是否完成 | 是 |
| R84 | 提测时间 | 46217 |
| S84 | 测试情况 | 测试通过（线上） |
| T84 | 测试时间 | 7.28 |
| A（合并继承自 A83；A83:A88） | 原值见锚点 | 2.8 来自「题库-UI」页 |

<a id="entry-c0210fed2e0a6d78d2cc"></a>
### entry-c0210fed2e0a6d78d2cc · polymas-teacher-file-import-questions

技能一览表.xlsx / SKILL开发方向划分 / 第 85 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B85 | 数据与学情增强 | 题库 |
| C85 | 未命名列 C | 智能导入题目 |
| D85 | 未命名列 D | 上传试卷文件解析入库 |
| E85 | 未命名列 E | 文件\*(PDF/Word/图片/Excel)；目标位置 |
| F85 | 未命名列 F | tk-05 |
| G85 | 未命名列 G | 否 |
| H85 | 未命名列 H | P1 |
| I85 | 未命名列 I | 教学活动专员 |
| J85 | 未命名列 J | ①把这份期末试卷 PDF 导入题库；②这张试卷照片里的题帮我收进去 |
| K85 | 未命名列 K | 解析失败态；逐题确认环节保留在页面或对话卡片 |
| L85 | 未命名列 L | 新增；对话+文件上传强场景 |
| M85 | 技能名称 | polymas-teacher-file-import-questions |
| P85 | 负责人 | B6智能导入题目：@赵洪恩 |
| Q85 | 是否完成 | 是 |
| R85 | 提测时间 | 46216 |
| S85 | 测试情况 | 测试通过（线上） |
| T85 | 测试时间 | 7.28 |
| A（合并继承自 A83；A83:A88） | 原值见锚点 | 2.8 来自「题库-UI」页 |

<a id="entry-068f699d2b0e8e6ce030"></a>
### entry-068f699d2b0e8e6ce030 · polymas-teacher-questionbank-skills

技能一览表.xlsx / SKILL开发方向划分 / 第 86 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B86 | 数据与学情增强 | 题库 |
| C86 | 未命名列 C | 随机组卷 |
| D86 | 未命名列 D | 按规则自动生成试卷 |
| E86 | 未命名列 E | 题型清单+每型：数量/比例、知识点(可设必出)、文件夹、标签、难度；每题分值 |
| F86 | 未命名列 F | tk-13 |
| G86 | 未命名列 G | 否 |
| H86 | 未命名列 H | P1 |
| I86 | 未命名列 I | 教学活动专员 |
| J86 | 未命名列 J | ①从题库出一套 20 题的期中卷，必须覆盖第三章知识点；②按难度中等出一套练习卷 |
| K86 | 未命名列 K | 可用题量不足时提示缺口 |
| L86 | 未命名列 L | 新增；与创建作业/考试编排衔接 |
| M86 | 技能名称 | polymas-teacher-questionbank-skills |
| P86 | 负责人 | D @陈源富 |
| Q86 | 是否完成 | 是 |
| S86 | 测试情况 | 测试不通过（线上，有bug） |
| T86 | 测试时间 | 7.28 |
| A（合并继承自 A83；A83:A88） | 原值见锚点 | 2.8 来自「题库-UI」页 |

<a id="entry-ef58f4987f4aba6bab75"></a>
### entry-ef58f4987f4aba6bab75 · polymas-teacher-questionbank-skills

技能一览表.xlsx / SKILL开发方向划分 / 第 87 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B87 | 数据与学情增强 | 题库 |
| C87 | 未命名列 C | 新建单题 |
| D87 | 未命名列 D | 对话录入一道题 |
| E87 | 未命名列 E | 题型\；题干\；选项/答案\*；解析；知识点/难度/标签；位置 |
| F87 | 未命名列 F | tk-02 |
| G87 | 未命名列 G | 否 |
| H87 | 未命名列 H | P2 |
| I87 | 未命名列 I | 教学活动专员 |
| J87 | 未命名列 J | ①帮我录一道单选题：题干是…答案是 B |
| K87 | 未命名列 K | 相似题提示透传给用户 |
| L87 | 未命名列 L | 新增 |
| M87 | 技能名称 | polymas-teacher-questionbank-skills |
| P87 | 负责人 | D @陈源富 |
| Q87 | 是否完成 | 是 |
| S87 | 测试情况 | 测试不通过（线上，有bug） |
| T87 | 测试时间 | 7.28 |
| A（合并继承自 A83；A83:A88） | 原值见锚点 | 2.8 来自「题库-UI」页 |

<a id="entry-753a1966611ca3986caf"></a>
### entry-753a1966611ca3986caf · polymas-teacher-questionbank-skills

技能一览表.xlsx / SKILL开发方向划分 / 第 88 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B88 | 数据与学情增强 | 题库 |
| C88 | 未命名列 C | 试题去重 |
| D88 | 未命名列 D | 找出并清理重复题 |
| E88 | 未命名列 E | 范围；相似度阈值(默认全部/仅 100%) |
| F88 | 未命名列 F | tk-07 |
| G88 | 未命名列 G | 否 |
| H88 | 未命名列 H | P2 |
| I88 | 未命名列 I | 教学活动专员 |
| J88 | 未命名列 J | ①题库里重复的题帮我清一下 |
| K88 | 未命名列 K | 删除前列清单确认 |
| L88 | 未命名列 L | 新增 |
| M88 | 技能名称 | polymas-teacher-questionbank-skills |
| P88 | 负责人 | D @陈源富 |
| Q88 | 是否完成 | 是 |
| S88 | 测试情况 | 测试不通过（线上，有bug） |
| T88 | 测试时间 | 7.28 |
| A（合并继承自 A83；A83:A88） | 原值见锚点 | 2.8 来自「题库-UI」页 |

<a id="entry-9742d709d33e3951134f"></a>
### entry-9742d709d33e3951134f · polymas-teacher-homework-detail-skills

技能一览表.xlsx / SKILL开发方向划分 / 第 90 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A90 | 第一批次<br>高优先级 | 2.9 来自「训练题库-UI」页 |
| B90 | 数据与学情增强 | 学情 |
| C90 | 未命名列 C | 刷题训练学情查询 |
| D90 | 未命名列 D | 查训练完成度/易错题/易错知识点/学生掌握等级 |
| E90 | 未命名列 E | 课程\*；班级；维度(概览/易错/逐生)；掌握等级筛选 |
| F90 | 未命名列 F | xl-01/05 |
| G90 | 未命名列 G | 否 |
| H90 | 未命名列 H | P1 |
| I90 | 未命名列 I | 教学活动专员 |
| J90 | 未命名列 J | ①刷题训练大家做得怎么样；②哪些知识点最容易错；③掌握程度还在入门的有谁 |
| K90 | 未命名列 K | 无答题数据时说明 |
| L90 | 未命名列 L | 新增；与作业/考试学情组成学情 skill 三件套 |
| M90 | 技能名称 | polymas-teacher-homework-detail-skills |
| P90 | 负责人 | A1 学情分析：@朱希文 |
| Q90 | 是否完成 | 是 |
| R90 | 提测时间 |                    2026/7/22 |
| S90 | 测试情况 | 测试通过（线上） |
| T90 | 测试时间 | 8.5 |

<a id="entry-338e9d7792a3c13a8c07"></a>
### entry-338e9d7792a3c13a8c07 · polymas-teacher-classroom-report-skills

技能一览表.xlsx / SKILL开发方向划分 / 第 92 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A92 | 第一批次<br>高优先级 | 2.10 来自「课堂报告-UI」页 |
| B92 | 数据与学情增强 | 学情 |
| C92 | 未命名列 C | 课堂报告查询 |
| D92 | 未命名列 D | 课堂全维报告：核心数据/AI回顾/互动/测验/智能体使用 |
| E92 | 未命名列 E | 课堂*(或"今天这节课"/最近一次)；维度(概览/回顾/互动/测验/智能体) |
| F92 | 未命名列 F | kb-02/03/05/06/07 |
| G92 | 未命名列 G | 否 |
| H92 | 未命名列 H | P0 |
| I92 | 未命名列 I | 教学活动专员 |
| J92 | 未命名列 J | ①今天这节课上得怎么样；②这节课讲了哪些知识点；③随堂测验哪道题错得最多 |
| K92 | 未命名列 K | 课堂未结束/无录像时降级说明 |
| L92 | 未命名列 L | 新增；AI 回顾三件套(摘要/导图/知识点)可直接引用 |
| M92 | 技能名称 | polymas-teacher-classroom-report-skills |
| P92 | 负责人 | A2课堂报告查询：@朱希文 |
| Q92 | 是否完成 | 是 |
| R92 | 提测时间 |                   2026/0720 |
| S92 | 测试情况 | 测试通过（线上） |
| T92 | 测试时间 | 8.5 |

<a id="entry-d8fdcab4f476603c45c8"></a>
### entry-d8fdcab4f476603c45c8 · polymas-teacher-classroom-report-skills

技能一览表.xlsx / SKILL开发方向划分 / 第 93 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B93 | 数据与学情增强 | 学情 |
| C93 | 未命名列 C | 课堂出勤与表现查询 |
| D93 | 未命名列 D | 逐生出勤/表现分/互动/在线时长 |
| E93 | 未命名列 E | 课堂*；班级；学生(可选) |
| F93 | 未命名列 F | kb-04/05 |
| G93 | 未命名列 G | 否 |
| H93 | 未命名列 H | P1 |
| I93 | 未命名列 I | 教学活动专员 |
| J93 | 未命名列 J | ①今天谁没来上课；②这节课谁最活跃；③王蓝星最近上课状态怎么样(跨课堂聚合) |
| K93 | 未命名列 K | 三种签到出勤率口径需说明 |
| L93 | 未命名列 L | 新增；与考勤成绩(cj)联动 |
| M93 | 技能名称 | polymas-teacher-classroom-report-skills |
| P93 | 负责人 | D @朱希文 |
| Q93 | 是否完成 | 是 |
| R93 | 提测时间 |                    2026/7/21 |
| S93 | 测试情况 | 测试通过（线上） |
| T93 | 测试时间 | 8.5 |
| A（合并继承自 A92；A92:A93） | 原值见锚点 | 2.10 来自「课堂报告-UI」页 |

<a id="entry-d8804d506c170b6f3308"></a>
### entry-d8804d506c170b6f3308 · lesson-prep

技能一览表.xlsx / SKILL开发方向划分 / 第 95 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A95 | 第一批次<br>高优先级 | 2.11 来自「课堂教学-UI」页 |
| B95 | 数据与学情增强 | 课堂 |
| C95 | 未命名列 C | 备课预置课堂互动 |
| D95 | 未命名列 D | 提前备好签到/投票/测验/头脑风暴/分组讨论，课上一键发布 |
| E95 | 未命名列 E | 互动类型\*；对应参数（测验：题目来源[AI出题/题库]+时长；投票：题目+时长+加分；风暴：主题+次数；讨论：主题+时长+结论开关） |
| F95 | 未命名列 F | kt-09 |
| G95 | 未命名列 G | 否 |
| H95 | 未命名列 H | P1 |
| I95 | 未命名列 I | 教学活动专员 |
| J95 | 未命名列 J | ①帮我准备明天课上的随堂测验，出 6 道本章的题；②备一个关于"电流热效应"的头脑风暴；③下节课要分组讨论，主题是…，8 分钟 |
| K95 | 未命名列 K | 存为"备课"态，课上教师自行发布；测验题目可编排 AI 出题 |
| L95 | 未命名列 L | 新增；课中实时发起判 D，备课是对话的正确切入 |
| M95 | 技能名称 | lesson-prep |
| P95 | 负责人 | B2智能备课生成：@赵洪恩 |
| Q95 | 是否完成 | 是 |
| S95 | 测试情况 | 测试不通过（线上） |
| T95 | 测试时间 | 8.5 |

<a id="entry-0c56b7ffab1dc0e4e623"></a>
### entry-0c56b7ffab1dc0e4e623 · polymas-teacher-classroom-replay-management

技能一览表.xlsx / SKILL开发方向划分 / 第 96 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B96 | 数据与学情增强 | 课堂 |
| C96 | 未命名列 C | 课堂回放管理 |
| D96 | 未命名列 D | 发布/同步/重命名课堂回放 |
| E96 | 未命名列 E | 课堂(日期/主题定位)\*；动作(发布/同步至学习资源/改名)；可批量 |
| F96 | 未命名列 F | kt-12 |
| G96 | 未命名列 G | 否 |
| H96 | 未命名列 H | P2 |
| I96 | 未命名列 I | 教学活动专员 |
| J96 | 未命名列 J | ①把昨天的课堂回放发布给学生；②这周的回放都同步到学习资源 |
| K96 | 未命名列 K | 未发布学生不可见 |
| L96 | 未命名列 L | 新增 |
| M96 | 技能名称 | polymas-teacher-classroom-replay-management |
| P96 | 负责人 | D @陈源富 |
| Q96 | 是否完成 | 是 |
| S96 | 测试情况 | 测试不通过（线上） |
| T96 | 测试时间 | 7.30. |
| A（合并继承自 A95；A95:A96） | 原值见锚点 | 2.11 来自「课堂教学-UI」页 |

<a id="entry-d8e67e3479c91c62ce70"></a>
### entry-d8e67e3479c91c62ce70 · polymas-teacher-resource-skills

技能一览表.xlsx / SKILL开发方向划分 / 第 98 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A98 | 第一批次<br>高优先级 | 2.12 来自「资源库-UI」页 |
| B98 | 数据与学情增强 | 检索 |
| C98 | 未命名列 C | 资源库检索 |
| D98 | 未命名列 D | 检索课程资源库内容 |
| E98 | 未命名列 E | 关键词；类型(文件/视频/题目/能力训练/图谱/智能体/备课等 10 类)；文件夹 |
| F98 | 未命名列 F | zk-01 |
| G98 | 未命名列 G | 部分 |
| H98 | 未命名列 H | P0 |
| I98 | 未命名列 I | 基础工具 |
| J98 | 未命名列 J | ①资源库里有没有关于 Qoder 的资料；②找一下上周上传的那个 PPT；③我的批阅智能体有哪些 |
| K98 | 未命名列 K | 现状备注"返回描述有问题"待修 |
| L98 | 未命名列 L | 现状"有"——差量：类型过滤与文件夹定位；类型枚举据本页固化 |
| M98 | 技能名称 | polymas-teacher-resource-skills |
| P98 | 负责人 | C2资源库检索：@张康 |
| Q98 | 是否完成 | 是 |
| R98 | 提测时间 | 46217 |
| S98 | 测试情况 | 测试通过（线上） |
| T98 | 测试时间 | 7.30. |

<a id="entry-b34b5809f2df4fd747d3"></a>
### entry-b34b5809f2df4fd747d3 · polymas-teacher-resource-skills

技能一览表.xlsx / SKILL开发方向划分 / 第 99 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B99 | 数据与学情增强 | 资源 |
| C99 | 未命名列 C | 上传文件到资源库 |
| D99 | 未命名列 D | 对话内上传文件并归档 |
| E99 | 未命名列 E | 文件\*；目标文件夹；(重名处理⚠️) |
| F99 | 未命名列 F | zk-02 |
| G99 | 未命名列 G | 否 |
| H99 | 未命名列 H | P1 |
| I99 | 未命名列 I | 基础工具 |
| J99 | 未命名列 J | ①把这个课件传到资源库的第三章文件夹 |
| K99 | 未命名列 K | 大文件/格式限制待实证 |
| L99 | 未命名列 L | 新增；对话+文件上传天然场景 |
| M99 | 技能名称 | polymas-teacher-resource-skills |
| P99 | 负责人 | C3上传文件到资源库:@张康 |
| Q99 | 是否完成 | 是 |
| R99 | 提测时间 | 46218 |
| S99 | 测试情况 | 测试通过（线上） |
| T99 | 测试时间 | 7.30. |
| A（合并继承自 A98；A98:A100） | 原值见锚点 | 2.12 来自「资源库-UI」页 |

<a id="entry-0963bc04d39b7bda1ebe"></a>
### entry-0963bc04d39b7bda1ebe · polymas-teacher-knowledge-graph

技能一览表.xlsx / SKILL开发方向划分 / 第 100 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B100 | 数据与学情增强 | 课程 |
| C100 | 未命名列 C | 知识图谱查询 |
| D100 | 未命名列 D | 查三谱结构与统计 |
| E100 | 未命名列 E | 课程\*；图谱类型(知识/问题/能力)；知识点(可选) |
| F100 | 未命名列 F | zk-05 |
| G100 | 未命名列 G | 否 |
| H100 | 未命名列 H | P1 |
| I100 | 未命名列 I | 学科管理员 |
| J100 | 未命名列 J | ①这门课的知识图谱建了多少知识点；②"牛顿第二定律"在图谱里关联了哪些问题 |
| K100 | 未命名列 K | 未建图谱时引导 |
| L100 | 未命名列 L | 新增；知识点作业/学情薄弱点的数据底座 |
| M100 | 技能名称 | polymas-teacher-knowledge-graph |
| P100 | 负责人 | D @陈源富 |
| Q100 | 是否完成 | 是 |
| S100 | 测试情况 | 测试通过（线上） |
| T100 | 测试时间 | 7.30. |
| A（合并继承自 A98；A98:A100） | 原值见锚点 | 2.12 来自「资源库-UI」页 |

<a id="entry-53bfc1f2f41543ef41a8"></a>
### entry-53bfc1f2f41543ef41a8 · polymas-teacher-agent-teaching-gen

技能一览表.xlsx / SKILL开发方向划分 / 第 102 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A102 | 第一批次<br>高优先级 | 2.13 来自「智能体教学-UI」页 |
| B102 | 数据与学情增强 | 智能体教学 |
| C102 | 未命名列 C | 创建智能体课堂 |
| D102 | 未命名列 D | AI 生成可自动授课的课堂合集 |
| E102 | 未命名列 E | 合集名称\；要求描述\(自然语言)；资料(≤5 文件，资源库检索/上传)；教学主题；生成方式(默认 AI 生成)；标签 |
| F102 | 未命名列 F | zn-02 |
| G102 | 未命名列 G | 否 |
| H102 | 未命名列 H | P0 |
| I102 | 未命名列 I | 学科管理员 |
| J102 | 未命名列 J | ①用第三章课件生成一个智能体课堂给学生课前预习；②把这两份讲义做成 5 节的 AI 辅导课 |
| K102 | 未命名列 K | 异步生成需回报进度（生成中/失败）；生成后引导确认发布 |
| L102 | 未命名列 L | 新增；平台 AI 智课核心能力 |
| M102 | 技能名称 | polymas-teacher-agent-teaching-gen<br>课堂 合集 都已支持 |
| P102 | 负责人 | D @赵洪恩 |
| Q102 | 是否完成 | 是<br> |
| R102 | 提测时间 | 46218 |
| S102 | 测试情况 | 测试不通过（线上） |
| T102 | 测试时间 | 7.28 |

<a id="entry-e5038035ab33f1537d5b"></a>
### entry-e5038035ab33f1537d5b · polymas-teacher-agent-teaching-gen

技能一览表.xlsx / SKILL开发方向划分 / 第 103 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B103 | 数据与学情增强 | 智能体教学 |
| C103 | 未命名列 C | 智能体教学查询 |
| D103 | 未命名列 D | 查生成状态/完成率/授课统计 |
| E103 | 未命名列 E | 合集或课堂；维度(状态/完成率/AI老师统计) |
| F103 | 未命名列 F | zn-01/06 |
| G103 | 未命名列 G | 否 |
| H103 | 未命名列 H | P1 |
| I103 | 未命名列 I | 学科管理员 |
| J103 | 未命名列 J | ①我的智能体课堂生成好了吗；②微积分那个课堂学生完成率多少；③AI 老师这学期讲了多少分钟 |
| K103 | 未命名列 K | 未发布无学情数据 |
| L103 | 未命名列 L | 新增 |
| M103 | 技能名称 | polymas-teacher-agent-teaching-gen |
| P103 | 负责人 | D @朱希文 |
| Q103 | 是否完成 | 是<br> |
| R103 | 提测时间 |                    2026/7/25 |
| S103 | 测试情况 | 测试不通过（线上） |
| T103 | 测试时间 | 7.28 |
| A（合并继承自 A102；A102:A104） | 原值见锚点 | 2.13 来自「智能体教学-UI」页 |

<a id="entry-89b65f4e83191d948649"></a>
### entry-89b65f4e83191d948649 · polymas-teacher-agent-teaching-gen

技能一览表.xlsx / SKILL开发方向划分 / 第 104 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B104 | 数据与学情增强 | 智能体教学 |
| C104 | 未命名列 C | 合集/课堂管理 |
| D104 | 未命名列 D | 复制/删除/移动/加入资源库/发布 |
| E104 | 未命名列 E | 对象\；动作\ |
| F104 | 未命名列 F | zn-05/07 |
| G104 | 未命名列 G | 否 |
| H104 | 未命名列 H | P2 |
| I104 | 未命名列 I | 学科管理员 |
| J104 | 未命名列 J | ①把这个课堂合集复制一份到资源库 |
| K104 | 未命名列 K | 删除需确认；发布参数待实证 |
| L104 | 未命名列 L | 新增 |
| M104 | 技能名称 | polymas-teacher-agent-teaching-gen |
| N104 | 前置技能 | 移动和加入资源库不支持 |
| P104 | 负责人 | D @朱希文 |
| Q104 | 是否完成 | 是<br> |
| R104 | 提测时间 |                     2026/7/27 |
| S104 | 测试情况 | 测试通过（线上） |
| T104 | 测试时间 | 7.28 |
| A（合并继承自 A102；A102:A104） | 原值见锚点 | 2.13 来自「智能体教学-UI」页 |

<a id="entry-e4b5ce31b6ed5f98691a"></a>
### entry-e4b5ce31b6ed5f98691a · lesson-prep

技能一览表.xlsx / SKILL开发方向划分 / 第 106 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A106 | 第一批次<br>高优先级 | 2.14 来自「日历与备课-UI」页 |
| B106 | 数据与学情增强 | 备课 |
| C106 | 未命名列 C | 智能备课 |
| D106 | 未命名列 D | 为某节课生成教案/课件/德育案例并组织进备课方案，可连带预置互动 |
| E106 | 未命名列 E | 课堂(或时间)\；生成物(教案/课件/德育案例，多选)；主题\；要求描述；参考文件(≤5)；预置互动(可选) |
| F106 | 未命名列 F | bk-04/05 |
| G106 | 未命名列 G | 部分 |
| H106 | 未命名列 H | P0 |
| I106 | 未命名列 I | 教学活动专员 |
| J106 | 未命名列 J | ①帮我备下周三《大学物理》的课：生成教案和课件，再加一个 5 题随堂测验；②用这两份讲义生成教案 |
| K106 | 未命名列 K | 生成物挂进备课方案需教师确认；现状"内容创作 PPT/文本(有)"仅覆盖生成、不覆盖挂载到备课 |
| L106 | 未命名列 L | 现状内容创作类可复用生成端——差量：备课方案的组织与关联 |
| M106 | 技能名称 | lesson-prep |
| P106 | 负责人 | B2智能备课生成：@赵洪恩 |
| Q106 | 是否完成 | 是 |
| S106 | 测试情况 | 测试不通过（线上） |

<a id="entry-6d90eed8eba6f966a036"></a>
### entry-6d90eed8eba6f966a036 · polymas-teacher-work-calendar

技能一览表.xlsx / SKILL开发方向划分 / 第 107 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B107 | 数据与学情增强 | 日历 |
| C107 | 未命名列 C | 工作日历查询 |
| D107 | 未命名列 D | 查教学日程（课/会/作业截止） |
| E107 | 未命名列 E | 时间范围\*(今天/明天/本周…)；类型 |
| F107 | 未命名列 F | bk-01 |
| G107 | 未命名列 G | 否 |
| H107 | 未命名列 H | P0 |
| I107 | 未命名列 I | 基础工具 |
| J107 | 未命名列 J | ①我明天有什么课；②这周有什么安排；③下节课在哪个教室 |
| K107 | 未命名列 K | 高频入口；数据聚合五类 |
| L107 | 未命名列 L | 新增；对话产品的每日起点 |
| M107 | 技能名称 | polymas-teacher-work-calendar |
| P107 | 负责人 | D @陈源富 |
| Q107 | 是否完成 | 是 |
| S107 | 测试情况 | 测试不通过 |
| T107 | 测试时间 | 7.29 |
| A（合并继承自 A106；A106:A109） | 原值见锚点 | 2.14 来自「日历与备课-UI」页 |

<a id="entry-4fedcc81c5cacfa10a46"></a>
### entry-4fedcc81c5cacfa10a46 · polymas-teacher-agent-create

技能一览表.xlsx / SKILL开发方向划分 / 第 108 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B108 | 数据与学情增强 | 智能体教学 |
| C108 | 未命名列 C | 创建课堂智能体 |
| D108 | 未命名列 D | 建课堂 AI 助教并上线 |
| E108 | 未命名列 E | 名称\*；描述(可AI生成)；提示词(可AI生成)；音色(6 选)；模型 |
| F108 | 未命名列 F | bk-07 |
| G108 | 未命名列 G | 否 |
| H108 | 未命名列 H | P1 |
| I108 | 未命名列 I | 学科管理员 |
| J108 | 未命名列 J | ①给我的课建一个叫"阿强"的课堂助教，负责答疑，声音用小云 |
| K108 | 未命名列 K | 上线前保存草稿；高级编排引导页面 |
| L108 | 未命名列 L | 新增 |
| M108 | 技能名称 | polymas-teacher-agent-create |
| P108 | 负责人 | D @陈源富 |
| Q108 | 是否完成 | 是 |
| S108 | 测试情况 | 测试通过 |
| T108 | 测试时间 | 7.29 |
| A（合并继承自 A106；A106:A109） | 原值见锚点 | 2.14 来自「日历与备课-UI」页 |

<a id="entry-e9ccaa7e84fd320ce8e4"></a>
### entry-e9ccaa7e84fd320ce8e4 · polymas-teacher-preparation-management

技能一览表.xlsx / SKILL开发方向划分 / 第 109 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B109 | 数据与学情增强 | 备课 |
| C109 | 未命名列 C | 备课管理 |
| D109 | 未命名列 D | 新建/复制/同步/删除备课 |
| E109 | 未命名列 E | 备课\*；动作 |
| F109 | 未命名列 F | bk-03 |
| G109 | 未命名列 G | 否 |
| H109 | 未命名列 H | P2 |
| I109 | 未命名列 I | 教学活动专员 |
| J109 | 未命名列 J | ①把上周的备课复制到这周三的课 |
| K109 | 未命名列 K | 同步范围待实证 |
| L109 | 未命名列 L | 新增 |
| M109 | 技能名称 | polymas-teacher-preparation-management |
| P109 | 负责人 | D @陈源富 |
| Q109 | 是否完成 | 是 |
| S109 | 测试情况 | 测试不通过 |
| T109 | 测试时间 | 7.29 |
| A（合并继承自 A106；A106:A109） | 原值见锚点 | 2.14 来自「日历与备课-UI」页 |

<a id="entry-abbdc07a08011a784d0d"></a>
### entry-abbdc07a08011a784d0d · polymas-teacher-course-skills

技能一览表.xlsx / SKILL开发方向划分 / 第 111 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A111 | 第一批次<br>高优先级 | 2.15 来自「大平台主站-UI」页 |
| B111 | 数据与学情增强 | 课程 |
| C111 | 未命名列 C | 我教的课查询 |
| D111 | 未命名列 D | 查任教课程清单 |
| E111 | 未命名列 E | tab(校内/共享)；学期；含归档 |
| F111 | 未命名列 F | zs-02 |
| G111 | 未命名列 G | 部分 |
| H111 | 未命名列 H | P1 |
| I111 | 未命名列 I | 学课管理专员 |
| J111 | 未命名列 J | ①我这学期教哪几门课；②我有没有共享课程 |
| L111 | 未命名列 L | 现状"课程名称(有)"——差量：共享/归档/学期维度 |
| M111 | 技能名称 | polymas-teacher-course-skills |
| P111 | 负责人 | D @孟祥利 |
| Q111 | 是否完成 | 是 |
| R111 | 提测时间 |                     2026/7/22 |
| S111 | 测试情况 | 测试通过（线上） |
| T111 | 测试时间 | 7.29 |

<a id="entry-cedf52e57fa825e49f8d"></a>
### entry-cedf52e57fa825e49f8d · polymas-teacher-study-resource

技能一览表.xlsx / SKILL开发方向划分 / 第 113 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A113 | 第一批次<br>高优先级 | 2.16 来自「学习资源-UI」页 |
| B113 | 数据与学情增强 | 资源 |
| C113 | 未命名列 C | 发布学习资源 |
| D113 | 未命名列 D | 添加资源并发布给学生学习 |
| E113 | 未命名列 E | 资源\*(上传/资源库/链接)；章节位置；必学(开关)；允许下载(开关)；学习要求；知识点关联 |
| F113 | 未命名列 F | xz-01/02/03 |
| G113 | 未命名列 G | 否 |
| H113 | 未命名列 H | P1 |
| I113 | 未命名列 I | 教学活动专员 |
| J113 | 未命名列 J | ①把这个视频发到第三章让学生必学；②这份讲义发给学生，不允许下载 |
| K113 | 未命名列 K | 发布对象范围待实证 |
| L113 | 未命名列 L | 新增；与课堂回放"同步至学习资源"衔接 |
| M113 | 技能名称 | polymas-teacher-study-resource |
| P113 | 负责人 | D @朱希文 |
| Q113 | 是否完成 | 是 |
| R113 | 提测时间 |                     2026/7/24 |
| S113 | 测试情况 | 测试通过（线上） |
| T113 | 测试时间 | 7.30. |

<a id="entry-d4ca85c7b32de73d1b21"></a>
### entry-d4ca85c7b32de73d1b21 · polymas-teacher-activity-skills

技能一览表.xlsx / SKILL开发方向划分 / 第 115 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A115 | 第一批次<br>高优先级 | 2.17 来自「问答讨论-UI」页 |
| B115 | 数据与学情增强 | 互动 |
| C115 | 未命名列 C | 创建讨论话题 |
| D115 | 未命名列 D | 发布课程讨论 |
| E115 | 未命名列 E | 话题内容\；班级\；附件；规则(多次作答/未答不可见他人答) |
| F115 | 未命名列 F | wd-01 |
| G115 | 未命名列 G | 否 |
| H115 | 未命名列 H | P1 |
| I115 | 未命名列 I | 教学活动专员 |
| J115 | 未命名列 J | ①发个讨论：大家怎么看 MCP 协议的前景，一班参加；②建个话题，学生答完才能看别人的 |
| K115 | 未命名列 K | 内容草拟需教师确认后发布 |
| L115 | 未命名列 L | 新增 |
| M115 | 技能名称 | polymas-teacher-activity-skills |
| P115 | 负责人 | D @赵洪恩 |
| Q115 | 是否完成 | 是<br> |
| R115 | 提测时间 | 2026/7/17<br>新增传附件能力 |
| S115 | 测试情况 | 测试通过 |
| T115 | 测试时间 | 7.29 |

<a id="entry-0ee2439a4f49be325658"></a>
### entry-0ee2439a4f49be325658 · polymas-teacher-activity-skills

技能一览表.xlsx / SKILL开发方向划分 / 第 116 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B116 | 数据与学情增强 | 互动 |
| C116 | 未命名列 C | 讨论情况查询 |
| D116 | 未命名列 D | 查参与度/词云/AI 总结 |
| E116 | 未命名列 E | 话题\*(或最近)；班级；维度(统计/总结/热词) |
| F116 | 未命名列 F | wd-02/03 |
| G116 | 未命名列 G | 否 |
| H116 | 未命名列 H | P1 |
| I116 | 未命名列 I | 教学活动专员 |
| J116 | 未命名列 J | ①这个讨论大家聊得怎么样；②帮我总结下讨论里的主要观点（引用课代表 AI 总结） |
| K116 | 未命名列 K | AI 总结标注"仅供参考" |
| L116 | 未命名列 L | 已有；对应现状"学生互动数据(否)"<br>（现在是agent自己总结分析的，是否强制需要引用“课代表 AI 总结”可以问一下产品） |
| M116 | 技能名称 | polymas-teacher-activity-skills |
| O116 | 技能的实现说明 | 目前ai总结有bug 找不到接口 |
| P116 | 负责人 | D @张康 |
| Q116 | 是否完成 | 是 |
| R116 | 提测时间 | 46227 |
| S116 | 测试情况 | 测试通过，没有ai总结的标识 |
| A（合并继承自 A115；A115:A118） | 原值见锚点 | 2.17 来自「问答讨论-UI」页 |

<a id="entry-a00b8f1e84e8caafd858"></a>
### entry-a00b8f1e84e8caafd858 · polymas-teacher-activity-skills

技能一览表.xlsx / SKILL开发方向划分 / 第 117 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B117 | 数据与学情增强 | 互动 |
| C117 | 未命名列 C | 讨论加分 |
| D117 | 未命名列 D | 按条件给回答加互动分 |
| E117 | 未命名列 E | 话题\；范围(全部/指定学生/条件筛选)；分值\ |
| F117 | 未命名列 F | wd-06 |
| G117 | 未命名列 G | 否 |
| H117 | 未命名列 H | P1 |
| I117 | 未命名列 I | 教学活动专员 |
| J117 | 未命名列 J | ①参与这次讨论的每人加 1 分；②给被加精的回答加 2 分 |
| K117 | 未命名列 K | 有历史评分防重复；联动平时成绩 |
| L117 | 未命名列 L | 新增；对话强项 |
| M117 | 技能名称 | polymas-teacher-activity-skills |
| P117 | 负责人 | D @张康 |
| Q117 | 是否完成 | 是 |
| R117 | 提测时间 | 46226 |
| S117 | 测试情况 | 测试通过（线上） |
| A（合并继承自 A115；A115:A118） | 原值见锚点 | 2.17 来自「问答讨论-UI」页 |

<a id="entry-51a5f120a8f2aa929e9f"></a>
### entry-51a5f120a8f2aa929e9f · polymas-teacher-activity-skills

技能一览表.xlsx / SKILL开发方向划分 / 第 118 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B118 | 数据与学情增强 | 互动 |
| C118 | 未命名列 C | 回复讨论/管理回答 |
| D118 | 未命名列 D | 回复、置顶、加精、删除 |
| E118 | 未命名列 E | 话题；对象；动作/回复内容 |
| F118 | 未命名列 F | wd-04/05 |
| G118 | 未命名列 G | 否 |
| H118 | 未命名列 H | P2 |
| I118 | 未命名列 I | 教学活动专员 |
| J118 | 未命名列 J | ①帮我回复那个关于成本计算的问题（草拟+确认）；②把李铁军的回答置顶 |
| K118 | 未命名列 K | 对外发言需确认 |
| L118 | 未命名列 L | 新增 |
| M118 | 技能名称 | polymas-teacher-activity-skills |
| P118 | 负责人 | D @张康 |
| Q118 | 是否完成 | 是 |
| R118 | 提测时间 | 46226 |
| S118 | 测试情况 | 测试通过（线上） |
| A（合并继承自 A115；A115:A118） | 原值见锚点 | 2.17 来自「问答讨论-UI」页 |

<a id="entry-39ced6914188be1fb73e"></a>
### entry-39ced6914188be1fb73e · polymas-teacher-class-group-assistant

技能一览表.xlsx / SKILL开发方向划分 / 第 120 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A120 | 第一批次<br>高优先级 | 2.18 来自「群聊-UI」页 |
| B120 | 数据与学情增强 | 互动 |
| C120 | 未命名列 C | 班级群消息与公告 |
| D120 | 未命名列 D | 向班级群发消息/发布群公告 |
| E120 | 未命名列 E | 群(按班级定位)\；类型(消息/公告)；内容\(草拟+确认) |
| F120 | 未命名列 F | ql-01/02 |
| G120 | 未命名列 G | 否 |
| H120 | 未命名列 H | P1 |
| I120 | 未命名列 I | 教学活动专员 |
| J120 | 未命名列 J | ①在一班群里发个通知让大家记得交作业；②给班级群发个公告：明天考试带计算器 |
| K120 | 未命名列 K | 对外发言必须教师确认后发送 |
| L120 | 未命名列 L | 新增；与"催交""课堂回顾推送"编排衔接 |
| M120 | 技能名称 | polymas-teacher-class-group-assistant |
| P120 | 负责人 | D @陈源富 |
| Q120 | 是否完成 | 是 |
| S120 | 测试情况 | 测试通过（线上） |

<a id="entry-58a0fc3f6a07d67beeef"></a>
### entry-58a0fc3f6a07d67beeef · polymas-teacher-class-group-assistant

技能一览表.xlsx / SKILL开发方向划分 / 第 121 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B121 | 数据与学情增强 | 互动 |
| C121 | 未命名列 C | 班级群管理 |
| D121 | 未命名列 D | 入群申请审批/禁言/成员管理 |
| E121 | 未命名列 E | 群\*；动作(同意申请/忽略/全员禁言/移出成员) |
| F121 | 未命名列 F | ql-03/04/05 |
| G121 | 未命名列 G | 否 |
| H121 | 未命名列 H | P2 |
| I121 | 未命名列 I | 教学活动专员 |
| J121 | 未命名列 J | ①把入群申请都同意了；②考试周把班级群全员禁言 |
| K121 | 未命名列 K | 移出成员需确认 |
| L121 | 未命名列 L | 新增 |
| M121 | 技能名称 | polymas-teacher-class-group-assistant |
| P121 | 负责人 | D @陈源富 |
| Q121 | 是否完成 | 是 |
| S121 | 测试情况 | 测试通过（线上） |
| A（合并继承自 A120；A120:A121） | 原值见锚点 | 2.18 来自「群聊-UI」页 |

<a id="entry-989d0f7efdae22894194"></a>
### entry-989d0f7efdae22894194 · polymas-teacher-knowledge-distillation

技能一览表.xlsx / SKILL开发方向划分 / 第 123 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A123 | 第一批次<br>高优先级 | 2.19 来自「个人资源库-UI」页 |
| B123 | 数据与学情增强 | 资源 |
| C123 | 未命名列 C | 个人知识库管理 |
| D123 | 未命名列 D | 向"我的知识库"添加文件/知识块（供智能体对话引用） |
| E123 | 未命名列 E | 内容\*(文件/文本知识块)；文件夹 |
| F123 | 未命名列 F | gr-02 |
| G123 | 未命名列 G | 否 |
| H123 | 未命名列 H | P1 |
| I123 | 未命名列 I | 基础工具 |
| J123 | 未命名列 J | ①把这份 PDF 加进我的知识库；②记一个知识块：本课程期末考核方案是… |
| K123 | 未命名列 K | 平台明示"用于智能体对话"——V5 回答质量的直接来源 |
| L123 | 未命名列 L | 新增 |
| M123 | 技能名称 | polymas-teacher-knowledge-distillation |
| P123 | 负责人 | B3个人知识蒸馏:@陈源富 |
| Q123 | 是否完成 | 是 |
| S123 | 测试情况 | 测试通过（线上） |

<a id="entry-75b2b059b6e7908ed3d3"></a>
### entry-75b2b059b6e7908ed3d3 · polymas-teacher-homework-skills

技能一览表.xlsx / SKILL开发方向划分 / 第 124 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B124 | 数据与学情增强 | 作业 |
| C124 | 未命名列 C | 作业模版管理 |
| D124 | 未命名列 D | 存/用作业模版 |
| E124 | 未命名列 E | 动作(存为模版/用模版发布)；模版\*；发布时补(班级/时间) |
| F124 | 未命名列 F | gr-03 |
| G124 | 未命名列 G | 否 |
| H124 | 未命名列 H | P2 |
| I124 | 未命名列 I | 教学活动专员 |
| J124 | 未命名列 J | ①把这次作业存成模版下学期用；②用"实验报告模版"给二班发作业，下周五截止 |
| K124 | 未命名列 K | 模版缺省班级与时间 |
| L124 | 未命名列 L | 新增；发布作业 skill 增加"从模版"参数 |
| M124 | 技能名称 | polymas-teacher-homework-skills |
| P124 | 负责人 | D @张康 |
| Q124 | 是否完成 | 是 |
| R124 | 提测时间 | 46226 |
| S124 | 测试情况 | 测试通过（线上） |
| A（合并继承自 A123；A123:A124） | 原值见锚点 | 2.19 来自「个人资源库-UI」页 |

<a id="entry-db7daaf98f7779a691d1"></a>
### entry-db7daaf98f7779a691d1 · polymas-course-obe-skills

技能一览表.xlsx / SKILL开发方向划分 / 第 126 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A126 | 第一批次<br>高优先级 | 2.21 来自「OBE-UI」页 |
| B126 | 数据与学情增强 | 课程 |
| C126 | 未命名列 C | OBE 目标录入(AI 识别) |
| D126 | 未命名列 D | 上传培养方案文档，AI 抽取毕业要求/课程目标录入 |
| E126 | 未命名列 E | 文档\*(文件)；确认修订 |
| F126 | 未命名列 F | obe-01 |
| G126 | 未命名列 G | 否 |
| H126 | 未命名列 H | P2 |
| I126 | 未命名列 I | 学科管理员 |
| J126 | 未命名列 J | ①把培养方案里的毕业要求识别进来 |
| K126 | 未命名列 K | 抽取结果需逐条确认 |
| L126 | 未命名列 L | 新增；对话+文件上传场景 |
| M126 | 技能名称 | polymas-course-obe-skills |
| P126 | 负责人 | D @孟祥利 |
| Q126 | 是否完成 | 是 |
| R126 | 提测时间 |                     2026/7/22 |
| S126 | 测试情况 | 测试不通过（线上） |

<a id="entry-d7507ae9182912fca384"></a>
### entry-d7507ae9182912fca384 · polymas-teacher-teaching-observation-skills

技能一览表.xlsx / SKILL开发方向划分 / 第 128 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A128 | 第一批次<br>高优先级 | 2.22 来自「教学观测-UI」页 |
| B128 | 数据与学情增强 | 学情 |
| C128 | 未命名列 C | 课程学情综合分析 |
| D128 | 未命名列 D | 课程级学情/教学大盘（含 AI 综合评价） |
| E128 | 未命名列 E | 课程\*；班级；维度(综合/预警/掌握度/进度/互动/成绩) |
| F128 | 未命名列 F | gc-01/02/03 |
| G128 | 未命名列 G | 否 |
| H128 | 未命名列 H | P0 |
| I128 | 未命名列 I | 教学活动专员 |
| J128 | 未命名列 J | ①这门课整体学情怎么样（直接引用 AI 综合评价）；②哪些知识点掌握最差；③给我看预警学生名单 |
| K128 | 未命名列 K | 数据非实时(标更新时间) |
| L128 | 未命名列 L | 新增；与作业/考试/课堂/刷题四个专项学情组成完整学情体系 |
| M128 | 技能名称 | polymas-teacher-teaching-observation-skills |
| P128 | 负责人 | A5课程综合分析：@朱希文 |
| Q128 | 是否完成 | 是 |
| R128 | 提测时间 | 46224 |
| S128 | 测试情况 | 测试通过（线上） |
| T128 | 测试时间 | 7.30. |

<a id="entry-6536b5884b9df930a2ec"></a>
### entry-6536b5884b9df930a2ec · polymas-teacher-teaching-observation-skills

技能一览表.xlsx / SKILL开发方向划分 / 第 129 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B129 | 数据与学情增强 | 学情 |
| C129 | 未命名列 C | 智能体问答分析 |
| D129 | 未命名列 D | 学生向 AI 提问的热词/类型/满意度分析 |
| E129 | 未命名列 E | 课程\*；周期；维度(热词/类型/趋势/不满意清单) |
| F129 | 未命名列 F | gc-04 |
| G129 | 未命名列 G | 否 |
| H129 | 未命名列 H | P1 |
| I129 | 未命名列 I | 教学活动专员 |
| J129 | 未命名列 J | ①学生最近都在问 AI 什么问题；②有哪些回答学生不满意；③根据学生提问热点安排下节课内容（编排） |
| L129 | 未命名列 L | 新增；教师洞察 AI 助教质量与学生困惑点 |
| M129 | 技能名称 | polymas-teacher-teaching-observation-skills |
| P129 | 负责人 | D @朱希文 |
| Q129 | 是否完成 | 是<br> |
| R129 | 提测时间 |                     2026/7/21 |
| S129 | 测试情况 | 测试通过（线上） |
| T129 | 测试时间 | 7.30. |
| A（合并继承自 A128；A128:A129） | 原值见锚点 | 2.22 来自「教学观测-UI」页 |

<a id="entry-ddb309aa2f58a2d74632"></a>
### entry-ddb309aa2f58a2d74632 · polymas-project-tech-skills

技能一览表.xlsx / SKILL开发方向划分 / 第 131 行

NID：待核对；版本：待核对；线上：未核对。

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A131 | 第一批次<br>高优先级 | 2.23 来自「协作空间-UI」页 |
| B131 | 数据与学情增强 | 协作 |
| C131 | 未命名列 C | 协作空间任务管理 |
| D131 | 未命名列 D | 在协作空间创建/查询任务 |
| E131 | 未命名列 E | 空间\；任务标题\；目标；起止时间；同步至个人资源库(开关) |
| F131 | 未命名列 F | hz-02 |
| G131 | 未命名列 G | 否 |
| H131 | 未命名列 H | P2 |
| I131 | 未命名列 I | 教学活动专员 |
| J131 | 未命名列 J | ①在毕设空间建个任务：下周五前提交开题报告 |
| K131 | 未命名列 K | 频率待阶段 3 校验 |
| L131 | 未命名列 L | 新增；偏毕设/课题场景 |
| M131 | 技能名称 | polymas-project-tech-skills |
| P131 | 负责人 | D @孟祥利 |
| Q131 | 是否完成 | 是<br> |
| R131 | 提测时间 |                    2026/7/28 |
| S131 | 测试情况 | 测试通过（线上） |
| T131 | 测试时间 | 7.30. |

## 非能力行来源上下文

保留表头、专家说明、问题、开发日志和无法确认的记录，以供追溯；不能据此直接挂载 Skill。

### 技能  - 专家整理.xlsx / 技能(学生测)

第 1 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A1 | 类型 | 类型 |
| B1 | 场景标签 | 场景标签 |
| C1 | 技能名称 | 技能名称 |
| D1 | 技能中文名 | 技能中文名 |
| E1 | 功能点序号 | 功能点序号 |
| F1 | 功能点（英文） | 功能点（英文） |
| G1 | 功能点（中文） | 功能点（中文） |
| H1 | 描述 | 描述 |
| I1 | 线上状态 | 线上状态 |
| J1 | 负责人 | 负责人 |
| K1 | 提测状态 | 提测状态 |
| L1 | 提测时间 | 提测时间 |
| M1 | 使用场景 | 使用场景 |

第 21 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B21 | 场景标签 | 成绩查询 |

第 22 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B22 | 场景标签 | 学情分析 |

第 23 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B23 | 场景标签 | 推荐类 |

第 24 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B24 | 场景标签 | AIGC |

第 25 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B25 | 场景标签 | 知识中心 |

### 技能  - 专家整理.xlsx / 技能(教师测)

第 1 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A1 | 类型 | 类型 |
| B1 | 场景标签 | 场景标签 |
| C1 | 技能名称 | 技能名称 |
| D1 | 技能中文名 | 技能中文名 |
| E1 | 功能点序号 | 功能点序号 |
| F1 | 功能点（英文） | 功能点（英文） |
| G1 | 功能点（中文） | 功能点（中文） |
| H1 | 描述 | 描述 |
| I1 | 线上状态 | 线上状态 |
| J1 | 负责人 | 负责人 |
| K1 | 提测状态 | 提测状态 |
| L1 | 提测时间 | 提测时间 |

第 31 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B31 | 场景标签 | 知识中心 |

### 技能  - 专家整理.xlsx / 技能(公共)

第 1 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A1 | 类型 | 类型 |
| B1 | 场景标签 | 场景标签 |
| C1 | 技能名称 | 技能名称 |
| D1 | 技能中文名 | 技能中文名 |
| E1 | 功能点序号 | 功能点序号 |
| F1 | 功能点（英文） | 功能点（英文） |
| G1 | 功能点（中文） | 功能点（中文） |
| H1 | 描述 | 描述 |
| I1 | 线上状态 | 线上状态 |
| J1 | 负责人 | 负责人 |
| K1 | 提测状态 | 提测状态 |
| L1 | 提测时间 | 提测时间 |

### 技能  - 专家整理.xlsx / 技能

第 2 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A2 | 类型 | 类型 |
| B2 | 场景标签 | 场景标签 |
| C2 | 技能名称 | 技能名称 |
| D2 | 技能中文名 | 技能中文名 |
| E2 | 功能点序号 | 功能点序号 |
| F2 | 功能点（英文） | 功能点（英文） |
| G2 | 功能点（中文） | 功能点（中文） |
| H2 | 描述 | 描述 |

### 技能  - 专家整理.xlsx / 专家

第 2 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A2 | 类型 | 类型 |
| B2 | 专家名称 | 专家名称 |
| C2 | 专家描述 | 专家描述 |
| D2 | 附属技能 | 附属技能 |
| E2 | 触发场景 | 触发场景 |
| F2 | 备注 | 备注 |
| G2 | 负责人 | 负责人 |

第 3 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A3 | 类型 | 业务 |
| B3 | 专家名称 | 会议专员 |
| C3 | 专家描述 | 会议全流程：创建会议、查询会议列表（Markdown展示）、取消会议、查询会议纪要/总结 |

第 44 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A44 | 类型 | 算法 |
| B44 | 专家名称 | 检索小助手 |
| D44 | 附属技能 | 代替处理 |

第 45 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B45 | 专家名称 | 文件理解 |
| A（合并继承自 A44；A44:A51） | 原值见锚点 | 算法 |
| D（合并继承自 D44；D44:D51） | 原值见锚点 | 代替处理 |

第 46 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B46 | 专家名称 | 创作小助手 |
| A（合并继承自 A44；A44:A51） | 原值见锚点 | 算法 |
| D（合并继承自 D44；D44:D51） | 原值见锚点 | 代替处理 |

第 47 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B47 | 专家名称 | 创作小助手-尊享版 |
| A（合并继承自 A44；A44:A51） | 原值见锚点 | 算法 |
| D（合并继承自 D44；D44:D51） | 原值见锚点 | 代替处理 |

第 48 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B48 | 专家名称 | PPT小能手 |
| C48 | 专家描述 | PPT智能创作。从需求理解到成品交付全链路覆盖：基于知识库检索资源智能规划叙事路线，自动设计故事线与页面结构，生成设计系统，RAG 配图复用与 AI 生图，逐页 HTML 高精度渲染，自动质检回流修正，最终输出在线播放器 + PPTX 双格式交付。 |
| A（合并继承自 A44；A44:A51） | 原值见锚点 | 算法 |
| D（合并继承自 D44；D44:D51） | 原值见锚点 | 代替处理 |

第 49 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B49 | 专家名称 | 备课专家 |
| C49 | 专家描述 | 你是一位课程与课堂设计专家，帮助老师完成从学期章节规划、教学大纲、进度表到单课教案与课件PPT的全流程设计，并能将每节课细化为精确到分钟的内容与活动安排。 |
| A（合并继承自 A44；A44:A51） | 原值见锚点 | 算法 |
| D（合并继承自 D44；D44:D51） | 原值见锚点 | 代替处理 |

第 50 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B50 | 专家名称 | 智题策略专家 |
| A（合并继承自 A44；A44:A51） | 原值见锚点 | 算法 |
| D（合并继承自 D44；D44:D51） | 原值见锚点 | 代替处理 |

第 51 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B51 | 专家名称 | 创作小助手-快速版 |
| C51 | 专家描述 | 知识库创作 Agent支持生成 PPT、HTML、Markdown 文档、视频、动画、图片、统计图表、图片编辑、视频编辑、动图编辑 |
| A（合并继承自 A44；A44:A51） | 原值见锚点 | 算法 |
| D（合并继承自 D44；D44:D51） | 原值见锚点 | 代替处理 |

### 技能  - 专家整理.xlsx / 专家推荐列表

第 1 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A1 | 助教/课代表推荐 | 助教/课代表推荐 |
| B1 | 来源 | 来源 |
| C1 | 专家名称 | 专家名称 |
| D1 | 专家描述 | 专家描述 |
| E1 | 专家NID | 专家NID |

第 2 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A2 | 助教/课代表推荐 | 助教/课代表推荐 |
| B2 | 来源 | 业务 - 场景 |
| C2 | 专家名称 | 会议专员 |
| D2 | 专家描述 | 会议全流程：创建会议、查询会议列表（Markdown展示）、取消会议、查询会议纪要/总结 |
| E2 | 专家NID | k7dlkkkioO |

第 3 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C3 | 专家名称 | 基础工具 |
| D3 | 专家描述 | 展示平台8大模块、34项核心能力及典型问法；引导用户用自然语言描述需求，不执行业务操作;<br>页面导航指引：用户想做某操作但需在页面完成时，返回对应页面链接+一句话操作指引<br>仅用于联网搜索互联网公开内容，返回标题、描述、URL、封面、平台名称、相似度、发布时间等信息。纯搜索，不做任何内容操作。 |
| E3 | 专家NID | 82basicol |
| B（合并继承自 B2；B2:B36） | 原值见锚点 | 业务 - 场景 |
| A（合并继承自 A2；A2:A42） | 原值见锚点 | 助教/课代表推荐 |

第 6 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C6 | 专家名称 | 教学活动专员 |
| D6 | 专家描述 | 作业信息查询<br>教师端： 查询教师在课程下的作业信息，包括作业详细信息、作业关联班级信息、班级作业结束时间、完成率统计等数据。<br><br>学生端： 查询学生在课程下的所有作业信息，包括作业详细信息、作业关联班级信息、班级作业结束时间、完成率统计等数据。<br><br>考试信息查询<br>查询教师在课程下的考试信息，包括考试详细信息、关联班级安排、考试开始/结束时间、防作弊配置及组卷信息等数据。<br><br>考试/作业学情分析<br>教师查看考试或作业的详情与学情分析，包括基本信息、成绩统计、分段人数及各班级对比数据。<br><br>课程 OBE 达成度查询<br>查询课程 OBE 达成度，包括课程整体平均达成度、各课程目标平均达成度及各班级达成度。<br><br>教师多维成绩查询<br>支持查询总成绩、考勤、平时、作业、考试、自定义考核项等多维成绩数据，提供个人与班级分布两种视角。<br><br>通知发布<br>课程通知： 教师向课程下指定班级或全部学生发布通知，支持设置标题、内容、附件及目标班级。<br><br>班级群消息： 向班级群发送消息通知。<br><br>工作日历查询<br>查询教学日程，包括课程、会议、作业截止、考试、AI 提醒等日程安排。<br><br>课程分组查询<br>查询课程下的分组方案列表、分组方案详情、组内学生名单及未进组学生信息。<br><br>教师知识库查询<br>仅用于查询/搜索教师知识库内容，包括标题、资源类型、资源封面、资源链接、资源预览图标、资源名称、资源摘要。不支持新增、编辑、删除、上传、下载等操作。<br><br>学习进度查询<br>查询学习进度相关数据，包括学习资源完成率、必学完成率及按分组维度的完成率分布。 |
| E6 | 专家NID | 4AwO3Bbell |
| B（合并继承自 B2；B2:B36） | 原值见锚点 | 业务 - 场景 |
| A（合并继承自 A2；A2:A42） | 原值见锚点 | 助教/课代表推荐 |

第 18 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C18 | 专家名称 | 课中专员 |
| D18 | 专家描述 | 课堂核心数据分析：查询课堂基本数据统计与授课方式分布;<br>按课程、课堂查看学生课堂表现：成绩得分、互动参与、弹幕次数、在线时长；支持分页 |
| E18 | 专家NID | klKOtKpuaJ |
| B（合并继承自 B2；B2:B36） | 原值见锚点 | 业务 - 场景 |
| A（合并继承自 A2；A2:A42） | 原值见锚点 | 助教/课代表推荐 |

第 20 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C20 | 专家名称 | 学课管理专员 |
| D20 | 专家描述 | 1. 课程创建<br>教师创建课程，支持邀请码建课和 AI 智课建课两种方式。<br><br>2. 课程列表查询<br>查询课程列表信息，包括当前学期课程、归档课程和共享课列表；其中共享课仅返回 state == 3 的课程。<br><br>3. 课程概况查询<br>查询课程概况信息，包括教学计划状态、单元/章节数量、课代表对话次数、AI 知识库资源数量及教学活动列表。<br><br>4. 课程知识结构查询<br>查询指定课程的教学单元、主题、知识点及知识点关系的层级结构；仅可查询当前用户有权访问的课程。<br><br>5. 教学计划查询<br>查询课程的教学单元、主题（小节）、知识点结构，以及关联的作业与考试活动。<br><br>6. 班级创建<br>教师在课程下创建班级，支持按课程名称定位课程、输入班级名称后完成创建；创建后可按需手动添加学生，并支持循环添加。<br><br>7. 学生入班信息查询<br>按入班状态查询课程/班级下的学生信息，支持已入班、待审核、待激活三种状态；返回学生名单、标签、院系等数据。<br><br>8. 课程分组查询<br>查询课程下的分组方案列表、分组方案详情、组内学生名单及未进组学生信息。<br><br>9. 学生基础技能<br>根据用户需求，智能选择并调用课程搜索、作业查询等相关功能。 |
| E20 | 专家NID | fnYl389cpo |
| B（合并继承自 B2；B2:B36） | 原值见锚点 | 业务 - 场景 |
| A（合并继承自 A2；A2:A42） | 原值见锚点 | 助教/课代表推荐 |

第 24 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C24 | 专家名称 | 智能体课程专员 |
| D24 | 专家描述 | 创建课堂智能体；<br>生成单个智能体课堂：抽取信息 → 定位课程/学期 → 匹配数字人 → 创建课堂 → 发布活动 → 轮询生成状态 |
| E24 | 专家NID | oJVr5WPWS2 |
| B（合并继承自 B2；B2:B36） | 原值见锚点 | 业务 - 场景 |
| A（合并继承自 A2；A2:A42） | 原值见锚点 | 助教/课代表推荐 |

第 26 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C26 | 专家名称 | 资源管理专员 |
| D26 | 专家描述 | 1. 教师知识库查询<br>仅用于查询/搜索教师知识库内容，包括标题、资源类型、资源封面、资源链接、资源预览图标、资源名称、资源摘要。不支持新增、编辑、删除、上传、下载等操作。<br><br>2. 知识图谱查询<br>查询教学知识图谱中知识谱、问题谱、能力谱的结构与统计数据。<br><br>3. 教师题库查询<br>查询教师的题库资源与题目信息，包括课程题库和个人题库分类、题目详情（题干、题型、选项、答案）等数据；支持查询题目数量、分布及具体题目，可按题型、难度、知识点、标签、来源等多维度筛选。<br><br>4. 教师文件导题<br>上传试卷文件（支持 PDF、DOC、DOCX、PNG、JPG、JPEG、XLS、XLSX，单文件 ≤ 500MB），由 AI 解析提取题目，教师逐题确认后导入题库。<br><br>5. 教师 AI 出题<br>根据知识点、难度、题型等要求，通过 AI 自动生成题目并保存到题库。 |
| E26 | 专家NID | 6fIn8ih1nY |
| B（合并继承自 B2；B2:B36） | 原值见锚点 | 业务 - 场景 |
| A（合并继承自 A2；A2:A42） | 原值见锚点 | 助教/课代表推荐 |

第 32 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C32 | 专家名称 | 学情分析专员 |
| D32 | 专家描述 | 1. 学生学情分析报告查询<br>教师可按课程、班级查看指定学生的学情分析报告，包括作业完成情况、成绩趋势、学习活跃度等数据。<br><br>2. 学生综合学情视图<br>将单个学生的作业完成率、考试成绩、课堂互动次数整合展示，提供该学生的综合学情视图。<br><br>3. 学习进度查询<br>查询学习进度相关数据，包括学习资源完成率、必学完成率，以及按分组维度的完成率分布。<br><br>4. 课堂表现查询<br>按课程、课堂查看学生课堂表现，包括成绩得分、互动参与、弹幕次数、在线时长等；支持分页查询。<br><br>5. 课堂核心数据分析<br>查询课堂基本数据统计与授课方式分布等核心分析数据。<br><br>6. 统计分析<br>运用描述性统计、趋势分析、异常值检测、假设检验等统计方法，用于分析数据分布、检验显著性、识别异常、计算相关性并解读统计结果。适用于需要对学情、成绩、活跃度等数据进行量化分析的场景。 |
| E32 | 专家NID | TUe49s5ObS |
| B（合并继承自 B2；B2:B36） | 原值见锚点 | 业务 - 场景 |
| A（合并继承自 A2；A2:A42） | 原值见锚点 | 助教/课代表推荐 |

第 37 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B37 | 来源 | 算法 |
| C37 | 专家名称 | 检索小助手 |
| D37 | 专家描述 | 本agent为检索agent，支持检索词改写，知识库检索(检索方式：deep检索+wiki检索，检索内容：知识库包含知识点/文件信息/图片信息/知识库id等)+联网检索 上游传入的query需为用户原query，请勿进行增删改简 （为了更好的检索，检索时需要带上用户检索的目的，如问答/生成PPT/生成视频/生成文档/生成html等） |
| E37 | 专家NID | F144GDEVj2 |
| A（合并继承自 A2；A2:A42） | 原值见锚点 | 助教/课代表推荐 |

第 38 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C38 | 专家名称 | 文件理解 |
| D38 | 专家描述 | 具备完整的文件资源解析能力，支持文档、表格、PDF、图片、音视频、压缩包、代码等任意格式文件的理解。可提取文件结构化内容与纯文本信息，默认自动生成文件摘要并匹配用户意图输出精准应答。支持两种工作模式：问答模式用于解读、查询、总结文件内容；写作模式精准抽取原文片段，作为创作素材复用。 |
| E38 | 专家NID | 5av4S1lCWe |
| B（合并继承自 B37；B37:B42） | 原值见锚点 | 算法 |
| A（合并继承自 A2；A2:A42） | 原值见锚点 | 助教/课代表推荐 |

第 39 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C39 | 专家名称 | 创作小助手 |
| D39 | 专家描述 | 生成Markdown，html，图片 【接受内容要求】： 源文件URL：&lt;原始文件链接&gt;（若有） 结构化解析URL：&lt;结构化json链接&gt;（若有） resource_parse_result:&lt;原始解析内容&gt;（若有） search_reference_path：&lt;上游检索结果保存路径&gt;（若有） search_reference_result：&lt;完整上游检索结果检索内容&gt;（若有search_reference_path，则该部分内容可忽略） 执行要求：&lt;纯原始执行指令拆解；严格使用归一后的用户需求，禁止模型自行新增、扩写、脑补额外规则&gt; |
| E39 | 专家NID | Sjgt0EcTFX |
| B（合并继承自 B37；B37:B42） | 原值见锚点 | 算法 |
| A（合并继承自 A2；A2:A42） | 原值见锚点 | 助教/课代表推荐 |

第 40 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C40 | 专家名称 | 智题策略专家 |
| D40 | 专家描述 | 我是智题策略专家，能深度解析您上传的学科资料，智能识别知识重点与考查方向，自动生成难度适配、题型丰富的定制化试题，并提供详细解析，让备考与教学出题事半功倍。 |
| E40 | 专家NID | XLbeGlUgFr |
| B（合并继承自 B37；B37:B42） | 原值见锚点 | 算法 |
| A（合并继承自 A2；A2:A42） | 原值见锚点 | 助教/课代表推荐 |

第 41 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C41 | 专家名称 | 备课专家 |
| D41 | 专家描述 | 你是一位课程与课堂设计专家，帮助老师完成从学期章节规划、教学大纲、进度表到单课教案与课件PPT的全流程设计，并能将每节课细化为精确到分钟的内容与活动安排。 |
| E41 | 专家NID | 6MgccXaRL1 |
| B（合并继承自 B37；B37:B42） | 原值见锚点 | 算法 |
| A（合并继承自 A2；A2:A42） | 原值见锚点 | 助教/课代表推荐 |

第 42 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C42 | 专家名称 | 创作小助手-快速版 |
| D42 | 专家描述 | 知识库创作 Agent支持生成 PPT、HTML、Markdown 文档、视频、动画、图片、统计图表、图片编辑、视频编辑、动图编辑； PPT类：演示、汇报、路演、pitch、答辩、课件、讲解材料等PPT文件(格式为pptx) HTML类：网页、官网、落地页、活动页、展示页、宣传页、HTML文件(格式为html) Markdown文档：README、md文件、说明、提纲、大纲、技术文档(格式为md) 视频/动画类：支持教学类视频、知识点讲解、实景 、动态特效类视频（生成文件类型为mp4格式/gif格式，时长支持5秒-30分钟）； 图片生成类：支持流程图、示意图、风景图、建筑图、物品图、知识点图、解剖图等各类创意生成的图片，支持图生图、文生图(格式无法指定)； 统计图表类：支持柱状图、折线图、饼图、小提琴图等不同类型的统计图表(格式无法指定)； 图片编辑：支持图片优化，图风格切换，P图 调用要求(传入指令需精简清晰，必须包含1-3信息,且生成内容仅在4提到的范围内)： 1. 明确产出文件类型（PPT/HTML/Markdown/ 视频 / 图片等）； 2. 清晰创作主题； 3. 按需补充对应素材（图片链接、参考资料、原图等），缺失必要素材将无法执行任务； 4. 该agent仅支持生成mp4、gif、jpeg、png、md、pptx、html文件的生成。 【出参强制约束】 1. 解析传入的抽象意图必须极致精简，禁止添加任何额外解释以及用户未明确提出的内容； 2. 若单次需求需要拆分为多次调用本Agent并行/串行执行多个独立创作任务，**每一条子任务入参都必须严格遵守上面精简规则，不得为每个子任务自行脑补扩充细节、拓展创作范围、补充额外创作要求**； |
| E42 | 专家NID | x6lMEVioO |
| B（合并继承自 B37；B37:B42） | 原值见锚点 | 算法 |
| A（合并继承自 A2；A2:A42） | 原值见锚点 | 助教/课代表推荐 |

### 技能  - 专家整理.xlsx / 技能推荐列表

第 1 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A1 | 类型 | 类型 |
| B1 | 来源 | 来源 |
| C1 | 技能 | 技能 |
| D1 | 技能nid | 技能nid |
| E1 | 是否必须推送 | 是否必须推送 |

### 技能  - 专家整理.xlsx / 应用广场数据整理

第 1 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A1 | 类型 | 类型 |
| B1 | 来源 | 来源 |
| C1 | 名称 | 名称 |
| D1 | 中文名 | 中文名 |

第 64 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A64 | 类型 | 专家 |
| B64 | 来源 | 业务 |
| C64 | 名称 | 会议专员 |

第 65 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C65 | 名称 | 基础工具 |
| B（合并继承自 B64；B64:B71） | 原值见锚点 | 业务 |
| A（合并继承自 A64；A64:A77） | 原值见锚点 | 专家 |

第 66 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C66 | 名称 | 教学活动专员 |
| B（合并继承自 B64；B64:B71） | 原值见锚点 | 业务 |
| A（合并继承自 A64；A64:A77） | 原值见锚点 | 专家 |

第 67 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C67 | 名称 | 课中专员 |
| B（合并继承自 B64；B64:B71） | 原值见锚点 | 业务 |
| A（合并继承自 A64；A64:A77） | 原值见锚点 | 专家 |

第 68 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C68 | 名称 | 学课管理专员 |
| B（合并继承自 B64；B64:B71） | 原值见锚点 | 业务 |
| A（合并继承自 A64；A64:A77） | 原值见锚点 | 专家 |

第 69 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C69 | 名称 | 智能体课程专员 |
| B（合并继承自 B64；B64:B71） | 原值见锚点 | 业务 |
| A（合并继承自 A64；A64:A77） | 原值见锚点 | 专家 |

第 70 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C70 | 名称 | 资源管理专员 |
| B（合并继承自 B64；B64:B71） | 原值见锚点 | 业务 |
| A（合并继承自 A64；A64:A77） | 原值见锚点 | 专家 |

第 71 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C71 | 名称 | 学情分析专员 |
| B（合并继承自 B64；B64:B71） | 原值见锚点 | 业务 |
| A（合并继承自 A64；A64:A77） | 原值见锚点 | 专家 |

第 72 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B72 | 来源 | 算法 |
| C72 | 名称 | 检索小助手 |
| A（合并继承自 A64；A64:A77） | 原值见锚点 | 专家 |

第 73 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C73 | 名称 | 文件理解 |
| B（合并继承自 B72；B72:B77） | 原值见锚点 | 算法 |
| A（合并继承自 A64；A64:A77） | 原值见锚点 | 专家 |

第 74 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C74 | 名称 | 创作小助手 |
| B（合并继承自 B72；B72:B77） | 原值见锚点 | 算法 |
| A（合并继承自 A64；A64:A77） | 原值见锚点 | 专家 |

第 75 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C75 | 名称 | 备课专家 |
| B（合并继承自 B72；B72:B77） | 原值见锚点 | 算法 |
| A（合并继承自 A64；A64:A77） | 原值见锚点 | 专家 |

第 76 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C76 | 名称 | 智题策略专家 |
| B（合并继承自 B72；B72:B77） | 原值见锚点 | 算法 |
| A（合并继承自 A64；A64:A77） | 原值见锚点 | 专家 |

第 77 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C77 | 名称 | 创作小助手-快速版 |
| B（合并继承自 B72；B72:B77） | 原值见锚点 | 算法 |
| A（合并继承自 A64；A64:A77） | 原值见锚点 | 专家 |

### 技能  - 专家整理.xlsx / 技能2

第 1 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A1 | 类型 | 类型 |
| B1 | 场景标签 | 场景标签 |
| C1 | 技能名称 | 技能名称 |
| D1 | 技能中文名 | 技能中文名 |
| E1 | 功能点序号 | 功能点序号 |
| F1 | 功能点（英文） | 功能点（英文） |
| G1 | 功能点（中文） | 功能点（中文） |
| H1 | 描述 | 描述 |
| I1 | 负责人 | 负责人 |
| J1 | 提测状态 | 提测状态 |
| K1 | 提测时间 | 提测时间 |
| L1 | 验证人 | 验证人 |

### 技能  - 专家整理.xlsx / 技能推荐列表2

第 1 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A1 | 类型 | 类型 |
| B1 | 来源 | 来源 |
| C1 | 技能 | 技能 |
| D1 | 技能nid | 技能nid |
| E1 | 是否必须推送 | 是否必须推送 |

### 技能  - 专家整理.xlsx / 业务-专家

第 1 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A1 | 标配 | 标配 |
| B1 | 专家名称 | 专家名称 |
| C1 | 平台功能 | 平台功能 |
| D1 | 附属技能 | 附属技能 |
| E1 | 技能解释 | 技能解释 |
| F1 | 状态 | 状态 |
| G1 | 触发场景 | 触发场景 |

第 2 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B2 | 专家名称 | 翻转课专员 |
| C2 | 平台功能 | AI翻转（马先仙） |
| G2 | 触发场景 | 当前未配置附属技能，不触发。 |

第 3 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B3 | 专家名称 | 翻转课专员 |
| C3 | 平台功能 | AI翻转（马先仙） |
| G3 | 触发场景 | 当前未配置附属技能，不触发。 |

第 4 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B4 | 专家名称 | 翻转课专员 |
| C4 | 平台功能 | AI翻转（马先仙） |
| G4 | 触发场景 | 当前未配置附属技能，不触发。 |

第 5 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B5 | 专家名称 | 翻转课专员 |
| C5 | 平台功能 | AI翻转（马先仙） |
| G5 | 触发场景 | 当前未配置附属技能，不触发。 |

第 6 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B6 | 专家名称 | 翻转课专员 |
| C6 | 平台功能 | AI翻转（马先仙） |
| G6 | 触发场景 | 当前未配置附属技能，不触发。 |

第 45 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B45 | 专家名称 | 暂无 |
| C45 | 平台功能 | 错题本（黄卓） |
| G45 | 触发场景 | 当前未配置附属技能，不触发。 |

第 46 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B46 | 专家名称 | 暂无 |
| C46 | 平台功能 | 错题本（黄卓） |
| G46 | 触发场景 | 当前未配置附属技能，不触发。 |

第 48 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B48 | 专家名称 | 暂无 |
| C48 | 平台功能 | 课程主页（原智能体课程评审主页） |
| G48 | 触发场景 | 当前未配置附属技能，不触发。 |

第 49 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B49 | 专家名称 | 暂无 |
| C49 | 平台功能 | 课程主页（原智能体课程评审主页） |
| G49 | 触发场景 | 当前未配置附属技能，不触发。 |

第 50 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B50 | 专家名称 | 暂无 |
| C50 | 平台功能 | 能力阶梯（黄卓） |
| G50 | 触发场景 | 当前未配置附属技能，不触发。 |

第 57 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B57 | 专家名称 | 暂无 |
| C57 | 平台功能 | 智能辅导（不清楚，黄卓） |
| G57 | 触发场景 | 当前未配置附属技能，不触发。 |

第 74 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B74 | 专家名称 | 检索小助手 |

第 75 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B75 | 专家名称 | 文件理解 |

第 76 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B76 | 专家名称 | 创作小助手 |

第 77 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B77 | 专家名称 | 创作小助手-尊享版 |

第 78 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B78 | 专家名称 | PPT小能手 |

第 79 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B79 | 专家名称 | 备课小助手 |
| C79 | 平台功能 |  - 改名字 |

第 80 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B80 | 专家名称 | 出题小助手 |
| C80 | 平台功能 |  - 改名字 |

第 81 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B81 | 专家名称 | 创作小助手-快速版 |

### 技能  - 专家整理.xlsx / 模版推荐

第 1 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A1 | 助教 | 助教 |

第 2 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A2 | 助教 | 推荐专家 |
| B2 | 未命名列 B | 推荐技能 |

第 3 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A3 | 助教 | 业务专家都推送 |
| B3 | 未命名列 B | "其他"里面是“放”的，都可以推荐， 不用全量推荐，随机推荐几个就行。课代表的也是这样推荐<br><br>固定推荐：find-skills、skill-creator |

第 4 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A4 | 助教 | 算法 |
| B（合并继承自 B3；B3:B13） | 原值见锚点 | "其他"里面是“放”的，都可以推荐， 不用全量推荐，随机推荐几个就行。课代表的也是这样推荐<br><br>固定推荐：find-skills、skill-creator |

第 5 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A5 | 助教 | 检索 |
| B（合并继承自 B3；B3:B13） | 原值见锚点 | "其他"里面是“放”的，都可以推荐， 不用全量推荐，随机推荐几个就行。课代表的也是这样推荐<br><br>固定推荐：find-skills、skill-creator |

第 6 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A6 | 助教 | 文件理解 |
| B（合并继承自 B3；B3:B13） | 原值见锚点 | "其他"里面是“放”的，都可以推荐， 不用全量推荐，随机推荐几个就行。课代表的也是这样推荐<br><br>固定推荐：find-skills、skill-creator |

第 7 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A7 | 助教 | 创作小助手 |
| B（合并继承自 B3；B3:B13） | 原值见锚点 | "其他"里面是“放”的，都可以推荐， 不用全量推荐，随机推荐几个就行。课代表的也是这样推荐<br><br>固定推荐：find-skills、skill-creator |

第 8 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A8 | 助教 | 智题策略专家 |
| B（合并继承自 B3；B3:B13） | 原值见锚点 | "其他"里面是“放”的，都可以推荐， 不用全量推荐，随机推荐几个就行。课代表的也是这样推荐<br><br>固定推荐：find-skills、skill-creator |

第 24 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A24 | 助教 | 课代表 |

第 25 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A25 | 助教 | 推荐教师技能 |
| B25 | 未命名列 B | 推荐学生技能 |
| C25 | 未命名列 C | 推荐专家 |

第 48 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A48 | 助教 | 助教 + 课代表 |

第 49 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B49 | 未命名列 B | 会议专员 |

### 技能一览表.xlsx / 技能一览

第 1 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A1 | 类别 | 类别 |
| B1 | 技能 | 技能 |
| C1 | 要求 | 要求 |
| D1 | 是否有 | 是否有 |
| E1 | 上线时间 | 上线时间 |
| F1 | 挂载的Agent | 挂载的Agent |
| G1 | 最佳实践 | 最佳实践 |
| H1 | 说明 | 说明 |
| I1 | 备注 | 备注 |
| J1 | 验证 | 验证 |

第 30 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A30 | 类别 | 1. 亚伟说下班前 6.4号给场景 |

第 34 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A34 | 类别 | 综合案例 |

第 36 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A36 | 类别 | 案例 |
| B36 | 技能 | 问题示例 |

第 37 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A37 | 类别 | 教研汇报 |
| B37 | 技能 | 帮我整理新能源技术基础本月教学运行情况，生成一份适合教研组汇报的要点。 |

第 38 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A38 | 类别 | 课前准备 |
| B38 | 技能 | 明天我要讲第三章，根据学生目前的学习情况，我需要重点讲解哪些内容。 |
| F38 | 挂载的Agent | 学习情况：特指哪些 |

第 39 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A39 | 类别 | 阶段退步分析 |
| B39 | 技能 | 帮我找出最近两周学习表现明显下降的学生，并说明可能原因。 |

第 40 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A40 | 类别 | 低参与学生识别 |
| B40 | 技能 | 找出最近课堂互动少、AI 提问少、作业完成也一般的学生。 |

第 41 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A41 | 类别 | 教案 / 讲义生成 |
| B41 | 技能 | 根据第三章教学目标，帮我生成一份 Word 版课堂讲义提纲。 |

第 42 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A42 | 类别 | HTML生成 |
| B42 | 技能 | 基于我引用的这几个学情情况，给我改成网页版 |

第 43 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A43 | 类别 | 视频生成 |
| B43 | 技能 | 给我下一章要讲的内容生成一个讲解视频 |

第 44 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A44 | 类别 | PPT生成 |
| B44 | 技能 | 基于这次学情分析，针对其中学生掌握的比较差的知识点，生成一份讲解PPT |

第 45 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A45 | 类别 | 作业查询 |
| B45 | 技能 | 帮我查一下新能源 1 班还有一周内截止的作业，按截止时间列出来。 |

第 46 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A46 | 类别 | 作业催交 |
| B46 | 技能 | 帮我找出这次作业还没提交的学生，并生成一段催交提醒。 |

第 47 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A47 | 类别 | 批量操作 |
| B47 | 技能 | 如果在12月2日前有学生提交了“函数作业20261211”这份作业的记录，都给我打回重做。 |

第 49 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A49 | 类别 | V5演示问题记录 |

### 技能一览表.xlsx / 推广问题修复

第 1 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A1 | 问题链接 | 问题链接 |
| B1 | 问题列表 | 问题列表 |
| C1 | 教学中心是否支持 | 教学中心是否支持 |
| D1 | 是否需新增技能 | 是否需新增技能 |
| E1 | 技能是否需要补充 | 技能是否需要补充 |
| F1 | 是否补充完成 | 是否补充完成 |
| G1 | 上线时间 | 上线时间 |
| H1 | 挂载子agent | 挂载子agent |
| I1 | 备注 | 备注 |
| J1 | 说明 | 说明 |

第 2 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A2 | 问题链接 | V5演示推广问题记录 |
| B2 | 问题列表 | 目前不支持分析学生与课代表进行对话的问答数据分析 |
| C2 | 教学中心是否支持 | - |
| D2 | 是否需新增技能 | - |
| E2 | 技能是否需要补充 | - |
| F2 | 是否补充完成 | - |
| I2 | 备注 | 已咨询熊小龙优先级较低 |

第 3 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B3 | 问题列表 | 基于作业分析互动角内容无法支持 |
| C3 | 教学中心是否支持 | 支持 |
| D3 | 是否需新增技能 | 否 |
| E3 | 技能是否需要补充 | 是 |
| F3 | 是否补充完成 | 已完成 |
| G3 | 上线时间 | 0609 |
| H3 | 挂载子agent | 教学活动专员 |
| J3 | 说明 | 依旧不支持 |
| A（合并继承自 A2；A2:A12） | 原值见锚点 | V5演示推广问题记录 |

第 4 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B4 | 问题列表 | 助教无法查询课表，不知道有哪些课 |
| C4 | 教学中心是否支持 | - |
| D4 | 是否需新增技能 | - |
| E4 | 技能是否需要补充 | - |
| F4 | 是否补充完成 | - |
| I4 | 备注 | 是否本期需支持助教角色，<br>当前只支持教师/学生 |
| A（合并继承自 A2；A2:A12） | 原值见锚点 | V5演示推广问题记录 |

第 5 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B5 | 问题列表 | 根据作业去学情分析，目前不支持掌握度、高频错题的问答 |
| C5 | 教学中心是否支持 | 支持 |
| D5 | 是否需新增技能 | 是 |
| E5 | 技能是否需要补充 | 是 |
| F5 | 是否补充完成 | 已完成 |
| G5 | 上线时间 | 0609 |
| H5 | 挂载子agent | 教学活动专员 |
| J5 | 说明 | 数据上存在一些问题 |
| A（合并继承自 A2；A2:A12） | 原值见锚点 | V5演示推广问题记录 |

第 6 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B6 | 问题列表 | 作业批注、学生作业、学生成绩、完成情况直接通过对话让导出excel不支持  |
| C6 | 教学中心是否支持 | - |
| D6 | 是否需新增技能 | 否 |
| E6 | 技能是否需要补充 | 是 |
| F6 | 是否补充完成 | 已完成 |
| G6 | 上线时间 | 0611 |
| H6 | 挂载子agent | 教学活动专员 |
| I6 | 备注 | 已在workspace生成，需在页面端进行展示 |
| A（合并继承自 A2；A2:A12） | 原值见锚点 | V5演示推广问题记录 |

第 7 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B7 | 问题列表 | 直接在对话里去上传对应的题目文件让它去上传到课程下目前不支持 |
| C7 | 教学中心是否支持 | 支持 |
| D7 | 是否需新增技能 | 是 |
| E7 | 技能是否需要补充 | 是 |
| F7 | 是否补充完成 | 待确定 |
| A（合并继承自 A2；A2:A12） | 原值见锚点 | V5演示推广问题记录 |

第 8 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B8 | 问题列表 | 对话设置作业自动处理规则，如低于60分直接打回暂时不支持 |
| C8 | 教学中心是否支持 | 不支持 |
| D8 | 是否需新增技能 | 否 |
| E8 | 技能是否需要补充 | 否 |
| F8 | 是否补充完成 | 否 |
| A（合并继承自 A2；A2:A12） | 原值见锚点 | V5演示推广问题记录 |

第 9 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B9 | 问题列表 | 定时收集科研资料暂不支持 |
| C9 | 教学中心是否支持 | - |
| D9 | 是否需新增技能 | - |
| E9 | 技能是否需要补充 | - |
| F9 | 是否补充完成 | - |
| I9 | 备注 | 需额外配置定时任务 |
| A（合并继承自 A2；A2:A12） | 原值见锚点 | V5演示推广问题记录 |

第 10 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B10 | 问题列表 | 学生互动数据目前待支持 - 周五支持互动数据展示<br>除能查询到提交数据和查询作业这些外，其他不支持 |
| C10 | 教学中心是否支持 | 支持 |
| D10 | 是否需新增技能 | 否 |
| E10 | 技能是否需要补充 | 是 |
| F10 | 是否补充完成 | 已完成 |
| G10 | 上线时间 | 0612 |
| H10 | 挂载子agent | 教学活动专员 |
| A（合并继承自 A2；A2:A12） | 原值见锚点 | V5演示推广问题记录 |

第 11 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B11 | 问题列表 | 知识块查询查不出来 |
| C11 | 教学中心是否支持 | - |
| D11 | 是否需新增技能 | - |
| E11 | 技能是否需要补充 | - |
| F11 | 是否补充完成 | 已完成 |
| G11 | 上线时间 | 0609 |
| H11 | 挂载子agent | 基础工具 |
| I11 | 备注 | 知识库查询已支持，部分请求可能存在<br>查询意图不明的问题，提示词端优化 |
| A（合并继承自 A2；A2:A12） | 原值见锚点 | V5演示推广问题记录 |

第 12 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B12 | 问题列表 | 查询课程数据智能查到作业信息这些，并不能查询到课程资料、章节、教学进度 |
| C12 | 教学中心是否支持 | 无章节数据 |
| D12 | 是否需新增技能 | 否 |
| E12 | 技能是否需要补充 | 教学进度需补充 |
| F12 | 是否补充完成 | 已完成 |
| G12 | 上线时间 | 0611 |
| H12 | 挂载子agent | 学课管理专员 |
| I12 | 备注 | 课程资料可在资源库查询中进行查询 |
| A（合并继承自 A2；A2:A12） | 原值见锚点 | V5演示推广问题记录 |

### 技能一览表.xlsx / V5技能

第 1 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A1 | agent | agent |
| B1 | 技能小类 | 技能小类 |
| C1 | 技能名称 | 技能名称 |
| D1 | 适用范围 | 适用范围 |
| E1 | 技能说明 | 技能说明 |
| F1 | 技能详情 | 技能详情 |

### 技能一览表.xlsx / V5技能列表

第 1 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A1 | 技能类型 | 技能类型 |
| B1 | AGENT | AGENT |
| C1 | 适用范围 | 适用范围 |
| D1 | 技能名称 | 技能名称 |
| E1 | 技能简介 | 技能简介 |
| F1 | 技能依赖 | 技能依赖 |

第 43 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C43 | 适用范围 | 课程管理 |

第 44 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C44 | 适用范围 | 教学日历 |

第 45 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C45 | 适用范围 | 教学活动（作业、考试、话题讨论、通知） |

第 46 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C46 | 适用范围 | 教学研讨 |

第 47 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C47 | 适用范围 | 智能体教学 |

第 48 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C48 | 适用范围 | 备课 |

第 49 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C49 | 适用范围 | 教室授课 |

第 50 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C50 | 适用范围 | 直播授课 |

第 51 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C51 | 适用范围 | 课堂互动 |

第 52 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C52 | 适用范围 | 课堂报告、回放 |

第 53 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C53 | 适用范围 | 小组教学 |

第 54 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C54 | 适用范围 | 训练题库 |

第 55 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C55 | 适用范围 | 成绩管理 |

第 56 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C56 | 适用范围 | OBE管理 |

第 57 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C57 | 适用范围 | 学习资源（普通、闯关、复习模式） |

第 58 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C58 | 适用范围 | 三大资源库（个人、团队、课程） |

第 59 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C59 | 适用范围 | 题库、试卷库 |

第 60 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C60 | 适用范围 | 学情分析 |

第 61 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C61 | 适用范围 | 课程主页（原智能体课程评审主页） |

第 62 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C62 | 适用范围 | 协作空间 |

第 63 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C63 | 适用范围 | AI翻转 |

第 64 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C64 | 适用范围 | 智能体对话 |

第 65 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C65 | 适用范围 | 能力训练 |

第 66 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C66 | 适用范围 | 智能体授课 |

第 67 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C67 | 适用范围 | AI批阅 |

第 68 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| C68 | 适用范围 | 大师版的： 智能辅导 能力阶梯 等 |

### 技能一览表.xlsx / Agent与Skill列表

第 1 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A1 | Agent | Agent |
| B1 | SKILL | SKILL |
| C1 | 标签 | 标签 |
| D1 | skill名称 | skill名称 |
| E1 | Skill描述 | Skill描述 |
| F1 | 场景样例 | 场景样例 |
| G1 | 功能列表 | 功能列表 |
| H1 | 功能是否具备 | 功能是否具备 |
| I1 | 负责人 | 负责人 |
| J1 | 是否提测 | 是否提测 |
| K1 | 提测时间 | 提测时间 |
| L1 | 说明 | 说明 |
| M1 | 测试情况 | 测试情况 |

### 技能一览表.xlsx / 生产智能体-技能映射

第 1 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A1 | 智能体 | 智能体 |
| B1 | 智能体说明 | 智能体说明 |
| C1 | 技能 | 技能 |
| D1 | 技能说明 | 技能说明 |

### 技能一览表.xlsx / SKILL开发方向划分

第 1 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A1 | 第一批次<br>高优先级 | 第一批次<br>高优先级 |
| B1 | 数据与学情增强 | 数据与学情增强 |
| M1 | 技能名称 | 技能名称 |
| N1 | 前置技能 | 前置技能 |
| O1 | 技能的实现说明 | 技能的实现说明 |
| P1 | 负责人 | 负责人 |
| Q1 | 是否完成 | 是否完成 |
| R1 | 提测时间 | 提测时间 |
| S1 | 测试情况 | 测试情况 |
| T1 | 测试时间 | 测试时间 |
| U1 | 规范 | 规范 |

第 2 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B2 | 数据与学情增强 | 核心职责：补全学情分析、课堂数据、班级/课程查询的缺失维度和结构化输出。 |
| Q2 | 是否完成 | - |
| U2 | 规范 | 1. 流程放在专家里面 |
| A（合并继承自 A1；A1:A29） | 原值见锚点 | 第一批次<br>高优先级 |

第 3 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B3 | 数据与学情增强 | # |
| C3 | 未命名列 C | 来源 |
| F3 | 未命名列 F | 功能简述（引用产品文档） |
| G3 | 未命名列 G | 已有/需补/新增 |
| H3 | 未命名列 H | 优先级 |
| J3 | 未命名列 J | z |
| P3 | 负责人 | @朱希文 |
| Q3 | 是否完成 | - |
| U3 | 规范 | 2. 技能 约等于多个独立的功能点 |
| A（合并继承自 A1；A1:A29） | 原值见锚点 | 第一批次<br>高优先级 |

第 10 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| Q10 | 是否完成 | - |
| A（合并继承自 A1；A1:A29） | 原值见锚点 | 第一批次<br>高优先级 |

第 11 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B11 | 数据与学情增强 | 内容生成与知识蒸馏增强 |
| Q11 | 是否完成 | - |
| A（合并继承自 A1；A1:A29） | 原值见锚点 | 第一批次<br>高优先级 |

第 12 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B12 | 数据与学情增强 | 核心职责：打通学情数据到内容生成的消费链路，支持原子化生成和教师经验沉淀。 |
| Q12 | 是否完成 | - |
| A（合并继承自 A1；A1:A29） | 原值见锚点 | 第一批次<br>高优先级 |

第 13 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B13 | 数据与学情增强 | # |
| C13 | 未命名列 C | 来源 |
| F13 | 未命名列 F | 功能简述（引用产品文档） |
| G13 | 未命名列 G | 已有/需补/新增 |
| H13 | 未命名列 H | 优先级 |
| Q13 | 是否完成 | - |
| A（合并继承自 A1；A1:A29） | 原值见锚点 | 第一批次<br>高优先级 |

第 19 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| Q19 | 是否完成 | - |
| A（合并继承自 A1；A1:A29） | 原值见锚点 | 第一批次<br>高优先级 |

第 20 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| Q20 | 是否完成 | - |
| A（合并继承自 A1；A1:A29） | 原值见锚点 | 第一批次<br>高优先级 |

第 21 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B21 | 数据与学情增强 | 平台执行与资源闭环增强 |
| Q21 | 是否完成 | - |
| A（合并继承自 A1；A1:A29） | 原值见锚点 | 第一批次<br>高优先级 |

第 22 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B22 | 数据与学情增强 | 核心职责：补齐发布参数、资源闭环、权限校验、入班审核等落地能力。 |
| Q22 | 是否完成 | - |
| A（合并继承自 A1；A1:A29） | 原值见锚点 | 第一批次<br>高优先级 |

第 23 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| B23 | 数据与学情增强 | # |
| C23 | 未命名列 C | 来源 |
| F23 | 未命名列 F | 功能简述（引用产品文档） |
| G23 | 未命名列 G | 已有/需补/新增 |
| H23 | 未命名列 H | 优先级 |
| Q23 | 是否完成 | - |
| A（合并继承自 A1；A1:A29） | 原值见锚点 | 第一批次<br>高优先级 |

第 30 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| Q30 | 是否完成 | - |

第 31 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| Q31 | 是否完成 | - |

第 32 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A32 | 第一批次<br>高优先级 | 后续追加 |
| Q32 | 是否完成 | - |

第 33 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A33 | 第一批次<br>高优先级 | 来源页面 |
| B33 | 数据与学情增强 | 类别 |
| C33 | 未命名列 C | 技能 |
| D33 | 未命名列 D | 要求 |
| E33 | 未命名列 E | 参数/槽位 |
| F33 | 未命名列 F | 来源 |
| G33 | 未命名列 G | 是否有 |
| H33 | 未命名列 H | 优先级 |
| I33 | 未命名列 I | 挂载Agent |
| J33 | 未命名列 J | 最佳实践 |
| K33 | 未命名列 K | 边界与异常 |
| L33 | 未命名列 L | 说明/备注 |
| Q33 | 是否完成 | - |

第 34 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A34 | 第一批次<br>高优先级 | 交付需求 |
| Q34 | 是否完成 | - |

第 35 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A35 | 第一批次<br>高优先级 | 交付需求 |
| D35 | 未命名列 D | 推荐资源：支持根据当前上下文的知识点从指定课程/全课程（KG+慕课+AI智课）进行课程资源推荐和课程常规信息获取（如链接、名称、老师、章节等） |
| G35 | 未命名列 G | 否 |
| H35 | 未命名列 H | P0 |
| L35 | 未命名列 L | 新增，许多交付项目都有这个资源推荐的需求 |
| P35 | 负责人 | D @陈源富@汪勇 |
| Q35 | 是否完成 | 否 |

第 36 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A36 | 第一批次<br>高优先级 | 2.1 来自「用户、账号与登录」页（2026-07-07 转化） |
| Q36 | 是否完成 | - |

第 38 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A38 | 第一批次<br>高优先级 | 2.2 来自「作业-UI」页（2026-07-07 转化，25 操作 → 五分法） |
| Q38 | 是否完成 | - |

第 51 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A51 | 第一批次<br>高优先级 | 2.3 来自「考试-UI」页（2026-07-07 转化，15 操作 → 五分法） |
| Q51 | 是否完成 | - |

第 60 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A60 | 第一批次<br>高优先级 | 2.4 来自「成绩管理-UI」页（2026-07-07 转化，11 操作 → 五分法） |
| Q60 | 是否完成 | - |

第 67 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A67 | 第一批次<br>高优先级 | 2.5 来自「课程管理-UI」页（2026-07-07 转化，19 操作 → 五分法） |
| Q67 | 是否完成 | - |

第 76 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A76 | 第一批次<br>高优先级 | 2.6 来自「课程主页(ai智课)-UI」页（2026-07-07 转化，7 操作 → 五分法） |
| Q76 | 是否完成 | - |

第 79 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A79 | 第一批次<br>高优先级 | 2.7 来自「教学计划-UI」页（2026-07-07 转化，5 操作 → 五分法） |
| Q79 | 是否完成 | - |

第 82 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A82 | 第一批次<br>高优先级 | 2.8 来自「题库-UI」页（2026-07-07 转化，14 操作 → 五分法） |
| Q82 | 是否完成 | - |

第 89 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A89 | 第一批次<br>高优先级 | 2.9 来自「训练题库-UI」页（2026-07-07 转化，6 操作 → 五分法） |
| Q89 | 是否完成 | - |

第 91 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A91 | 第一批次<br>高优先级 | 2.10 来自「课堂报告-UI」页（2026-07-07 转化，9 操作 → 五分法） |
| Q91 | 是否完成 | - |

第 94 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A94 | 第一批次<br>高优先级 | 2.11 来自「课堂教学-UI」页（2026-07-07 转化，12 操作 → 五分法） |
| Q94 | 是否完成 | - |

第 97 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A97 | 第一批次<br>高优先级 | 2.12 来自「资源库-UI」页（2026-07-07 转化，8 操作 → 五分法） |
| Q97 | 是否完成 | - |

第 101 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A101 | 第一批次<br>高优先级 | 2.13 来自「智能体教学-UI」页（2026-07-07 转化，7 操作 → 五分法） |
| Q101 | 是否完成 | - |

第 105 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A105 | 第一批次<br>高优先级 | 2.14 来自「日历与备课-UI」页（2026-07-07 转化，8 操作 → 五分法） |
| Q105 | 是否完成 | - |

第 110 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A110 | 第一批次<br>高优先级 | 2.15 来自「大平台主站-UI」页（2026-07-07 转化，6 操作 → 五分法） |
| Q110 | 是否完成 | - |

第 112 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A112 | 第一批次<br>高优先级 | 2.16 来自「学习资源-UI」页（2026-07-07 转化，4 操作 → 五分法） |
| Q112 | 是否完成 | - |

第 114 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A114 | 第一批次<br>高优先级 | 2.17 来自「问答讨论-UI」页（2026-07-07 转化，6 操作 → 五分法） |
| Q114 | 是否完成 | - |

第 119 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A119 | 第一批次<br>高优先级 | 2.18 来自「群聊-UI」页（2026-07-07 转化，7 操作 → 五分法） |
| Q119 | 是否完成 | - |

第 122 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A122 | 第一批次<br>高优先级 | 2.19 来自「个人资源库-UI」页（2026-07-07 转化，6 操作 → 五分法） |
| Q122 | 是否完成 | - |

第 125 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A125 | 第一批次<br>高优先级 | 2.21 来自「OBE-UI」页（2026-07-07 转化，6 操作 → 五分法） |
| Q125 | 是否完成 | - |

第 127 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A127 | 第一批次<br>高优先级 | 2.22 来自「教学观测-UI」页（2026-07-07 转化，6 操作 → 五分法） |
| Q127 | 是否完成 | - |

第 130 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A130 | 第一批次<br>高优先级 | 2.23 来自「协作空间-UI」页（2026-07-07 转化，7 操作） |
| Q130 | 是否完成 | - |

### 技能一览表.xlsx / SKILL开发日报

第 1 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A1 | 日期 | 日期 |
| B1 | 每日小结 | 每日小结 |
| C1 | 负责人 | 负责人 |
| D1 | @赵洪恩@朱希文@张康@陈源富@倪吉龙@孟祥利@汪勇 | @赵洪恩@朱希文@张康@陈源富@倪吉龙@孟祥利@汪勇 |

第 2 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A2 | 日期 | 7.9 |
| B2 | 每日小结 | 1.a2ui 学情分析和教学数据修改<br>2. 发布作业skill 完成30%<br>3.跟产品过skill |
| C2 | 负责人 | @张康 |

第 3 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A3 | 日期 | 7.9 |
| B3 | 每日小结 | 1. 和产品对skills相关需求的接口，整理功能点<br>2. 学情分析skill完成 |
| C3 | 负责人 | @朱希文 |

第 4 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A4 | 日期 | 7.9 |
| B4 | 每日小结 | 1.功能点表格梳理分配。<br>2.生题流程梳理。<br>3.备课流程梳理。<br>4.个人知识库流程梳理。 |
| C4 | 负责人 | @赵洪恩 |

第 5 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A5 | 日期 | 7.10 |
| B5 | 每日小结 | 1. a2ui复审重置 数据结构重改<br>2.a2ui 学情取值修改<br>3.发布作业skill 缺题库发布<br>4.资源库搜索30% |
| C5 | 负责人 | @张康 |

第 6 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A6 | 日期 | 7.10 |
| B6 | 每日小结 | 1.拆解skill需求并分配<br>2.与算法对齐skill开发流程<br>3.提供出题skill业务接口以及编排 |
| C6 | 负责人 | @赵洪恩 |

第 7 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A7 | 日期 | 7.10 |
| B7 | 每日小结 | 1. 梳理skill业务相关接口<br>2. 完成选题作业学情分析skill |
| C7 | 负责人 | @朱希文 |
| E7 | 未命名列 E | 学情分析可以提测 |

第 8 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A8 | 日期 | 7.13 |
| B8 | 每日小结 | 1.提供单题保存编排接口<br>2.文件识别导题入库技能-开发/调试/提测<br>3.任务拆分分配 |
| C8 | 负责人 | @赵洪恩 |

第 9 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A9 | 日期 | 7.13 |
| B9 | 每日小结 | 1.a2ui综合评价不显示问题排查<br>2.作业创建选择题目流程梳理<br>3.上传资源库文件功能编写 |
| C9 | 负责人 | @张康 |

第 10 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A10 | 日期 | 7.13 |
| B10 | 每日小结 | 1. 作业及考试详情学情分析skill(已提测)<br>2. 课程综合报告技能(进度70%) |
| C10 | 负责人 | @朱希文 |

第 11 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A11 | 日期 | 7.14 |
| B11 | 每日小结 | 1.a2ui prompt调试（晚上上线）<br>2.复审a2ui 已批阅修改（晚上上线）<br>2.资源库定位逻辑梳理<br>3.资源库指定文件夹上传<br>4.资源库定位（待测试） |
| C11 | 负责人 | @张康 |

第 12 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A12 | 日期 | 7.14 |
| B12 | 每日小结 | 1.提测：题库检索擦查询skill<br>2.智能体教学-合集skill流程梳理<br>3.备课需求评审 |
| C12 | 负责人 | @赵洪恩 |

第 13 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A13 | 日期 | 7.14 |
| B13 | 每日小结 | 1.课程综合分析skills(已提测)<br>2.课堂报告功能梳理<br>3.课堂报告skills开发中 |
| C13 | 负责人 | @朱希文 |

第 14 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A14 | 日期 | 7.15 |
| B14 | 每日小结 | 1.上传文件到制定文件夹重名处理(已提测)<br>2.发布考试成绩(已提测)<br>3.发布作业成绩 (已提测) |
| C14 | 负责人 | @张康 |

第 15 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A15 | 日期 | 7.15 |
| B15 | 每日小结 | 课程报告分析skills<br>1.核心数据分析(已提测)<br>2. 课堂的AI核心回顾三件套(已提测)<br>3.课堂互动数据分析(已提测)<br>4. 随堂测验详情(开发中)<br><br> |
| C15 | 负责人 | @朱希文 |

第 16 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A16 | 日期 | 7.15 |
| B16 | 每日小结 | 1.skill开发参考手册<br>2.提测：智能体单课堂生成 |
| C16 | 负责人 | @赵洪恩 |

第 17 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A17 | 日期 | 7.16 |
| B17 | 每日小结 | 1.修改作业内容/时间/规则(已提测)<br>2.向未交学生发提醒(已提测)<br>3.退回学生作业要求重做(已提测)<br>4.查询/同意/拒绝学生重做申请(已提测) |
| C17 | 负责人 | @张康 |

第 18 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A18 | 日期 | 7.16 |
| B18 | 每日小结 | 1.智能体合集生成（已提测）<br>2.智能体课堂生成问题修复 |
| C18 | 负责人 | @赵洪恩 |

第 19 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A19 | 日期 |                        7.16 |
| B19 | 每日小结 | 1.课程报告-随堂测验详情(已提测)<br>2. 课程报告-课堂模糊时间定位(已提测)<br>3.作业/考试新增完成情况skill(开发中) |
| C19 | 负责人 | @朱希文 |
| F19 | 未命名列 F | 课程 |

第 20 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A20 | 日期 | 7.16 |
| B20 | 每日小结 | 1. 业务skill规范、流程熟悉<br>2. 班级相关业务接口梳理<br>2.1班级学生查询<br>2.2学生调班/退班<br>2.3学生标签管理<br>2.4创建分组方案 |
| C20 | 负责人 | 倪吉龙 |

第 21 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A21 | 日期 | 7.16 |
| B21 | 每日小结 | 1、知识蒸馏技能<br>2、教学计划查询技能<br>3、知识图谱技能<br>4、页面导览技能 |
| C21 | 负责人 | @陈源富 |

第 22 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A22 | 日期 | 7.17 |
| B22 | 每日小结 | 1.话题技能增加附件（已提测）<br>2.日程会议技能-剔除日程能力（已提测）<br>3.AIGC问题排查<br>4.辅助算法了解V5能力 |
| C22 | 负责人 | @赵洪恩 |

第 23 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A23 | 日期 | 7.17 |
| B23 | 每日小结 | 1. 作业AI批阅进度与结果查询（已提测）<br>2.创建考试接口调用逻辑梳理<br>3. 创建并发布考试（已提测） |
| C23 | 负责人 | @张康 |

第 24 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A24 | 日期 | 7.17 |
| B24 | 每日小结 | 1.作业/考试新增完成情况skill(已提测)<br>2.提交名单，完成率维度(已提测)<br>3.学生情况(已提测) |
| C24 | 负责人 | @朱希文 |

第 25 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A25 | 日期 | 7.17 |
| B25 | 每日小结 | 1.班级分组管理技能（80%）<br>2. 班级学生管理技能（80%）<br>3. 班级学生状态（审核、调班、标签）技能（80%） |
| C25 | 负责人 | 倪吉龙 |

第 26 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A26 | 日期 | 7.17 |
| B26 | 每日小结 | 1、教学计划编辑skill接口包装 |
| C26 | 负责人 | @陈源富 |

第 27 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A27 | 日期 | 7.20 |
| B27 | 每日小结 | 1、完善教学计划编辑skill<br>2、工作日历skill<br>3、课堂智能体skill |
| C27 | 负责人 | @陈源富 |

第 28 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A28 | 日期 | 7.20 |
| B28 | 每日小结 | 1.学情prompt脚本修改<br>2.修改考试(已提测)<br>3.考试批量操作(已提测)<br>4.线上发布作业skill学期选择 |
| C28 | 负责人 | @张康 |
| G28 | 未命名列 G |   |

第 29 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A29 | 日期 | 7.20 |
| B29 | 每日小结 | 1.班级分组管理技能（提测）<br>2. 班级学生管理技能（提测）<br>3. 班级学生状态（审核、调班、标签）技能（提测） |
| C29 | 负责人 | 倪吉龙 |

第 30 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A30 | 日期 | 7.20 |
| B30 | 每日小结 | 1. 原skill学期及课程修改<br>2. 课堂出勤、表现查询<br>3. 互动，在线时长 |
| C30 | 负责人 | @朱希文 |

第 31 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A31 | 日期 | 7.20 |
| B31 | 每日小结 | 1.导题技能BUG修复<br>2.智能体教学课程BUG修复<br>3.课程助手技能BUG修复<br>4.生产课程助手技适配学期<br>5.更新技能参考文档-课程搜索学期相关 |
| C31 | 负责人 | @赵洪恩 |

第 32 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A32 | 日期 | 7.21 |
| B32 | 每日小结 | 1、群组发通知发公告skill |
| C32 | 负责人 | @陈源富 |

第 33 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A33 | 日期 | 7.21 |
| B33 | 每日小结 | 1.线上发布作业skill bug修复及回归<br>2.线上资源库skill问题排查<br>3.发布作业skill bug修复<br>4.发布考试成绩skill bug修复<br>5.发布作业题库类型作业逻辑梳理 |
| C33 | 负责人 | @张康 |

第 34 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A34 | 日期 | 7.21 |
| B34 | 每日小结 | 1. 多维成绩查询：总成绩 / 考勤 / 平时 / 作业 / 考试 / 自定义考核项个人｜班级两种视角<br>2. 成绩加权设置：四项权重配置、缺勤扣分、互动计分、应用到其他班级、学生查看开关、最终成绩设置<br>3. 线下考勤全生命周期：查询考勤列表、录入一次考勤、修改考勤（改为已签/未签）、删除本次考勤 |
| C34 | 负责人 | 倪吉龙 |

第 35 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A35 | 日期 | 7.21 |
| B35 | 每日小结 | 1.教学观测：学习进度，排行榜，<br>教学活动，知识点掌握，学生预警，<br>综合tab详情等 (提测)<br>2. 智能体问答分析（提测）<br>3. 课堂出勤（提测）<br>4.课堂报告人员概况skill调整 |
| C35 | 负责人 | @朱希文 |

第 36 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A36 | 日期 | 7.21 |
| B36 | 每日小结 | 1、课程概览查询 skill开发初版<br>2、课程达成度查询 skill开发初版<br>3、我教的课查询 skill开发初版<br>4、OBE 目标录入(AI 识别) skill开发初版 |
| C36 | 负责人 | 孟祥利 |

第 37 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A37 | 日期 | 7.21 |
| B37 | 每日小结 | 1.课程技能重复创建课程问题修复。<br>2.备课技能问题沟通。<br>3.会议日程技能改名上线<br>4.班级及能线上问题排查。<br>5.线上资源库专员路由必错问题解决。<br>6.任务拆分分配。 |
| C37 | 负责人 | @赵洪恩 |

第 38 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A38 | 日期 | 7.22 |
| B38 | 每日小结 | 1.发布作业新增题库作业类型（已提测）<br>2.补考相关逻辑梳理<br>3.创建补考（已提测） |
| C38 | 负责人 | @张康 |

第 39 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A39 | 日期 | 7.22 |
| B39 | 每日小结 | 1、补充群聊管理skill的功能<br>2、备课管理skill |
| C39 | 负责人 | @陈源富 |

第 40 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A40 | 日期 | 7.22 |
| B40 | 每日小结 | 1. 多维成绩查询 80%<br>2. 成绩加权设置 80%<br>3. 线下考勤全生命周期 50% |
| C40 | 负责人 | 倪吉龙 |

第 41 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A41 | 日期 | 7.22 |
| B41 | 每日小结 | 1.线上班级技能问题排查。<br>2.线上资源库技能问题排查。<br>3.技能-备课会议。<br>4.备课流程梳理。 |
| C41 | 负责人 | @赵洪恩 |

第 42 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A42 | 日期 | 7.22 |
| B42 | 每日小结 | 1. 刷题训练<br>2.训练结果分析(提测)<br>3.学生掌握情况分析(提测)<br>4.查重报告查询(开发中)<br> |
| C42 | 负责人 | @朱希文 |

第 43 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A43 | 日期 | 7.22 |
| B43 | 每日小结 | 1、课程概览查询 调试<br>2、课程达成度查询 调试<br>3、我教的课查询 调试<br>4、OBE 目标录入(AI 识别) 调试<br>5、教学进度接口开发 |
| C43 | 负责人 | 孟祥利 |

第 44 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A44 | 日期 | 7.23 |
| B44 | 每日小结 | 1、课堂回放skill<br>2、课程管理skill新增课程详情和编辑功能<br>3、班级管理skill新增学生导出功能 |
| C44 | 负责人 | @陈源富 |

第 45 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A45 | 日期 | 7.23 |
| B45 | 每日小结 | 1.查作业查重率与相似明细(提测)<br>2.增加学情综合评价(提测)<br>3.学习资源(开发中) |
| C45 | 负责人 | @朱希文 |

第 46 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A46 | 日期 | 7.23 |
| B46 | 每日小结 | 1、课程资源库 分类接口调整<br>2、查询老师课程概览接口调整<br>3、查询教师班级列表（含总成绩）接口调整 |
| C46 | 负责人 | 孟祥利 |

第 47 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A47 | 日期 | 7.23 |
| B47 | 每日小结 | 1.监考异常查询 提测<br>2.讨论加分 提测<br>3.回复讨论/管理回答 提测<br>4.作业模版管理 提测<br>5.修复 考试催交 修改bug |
| C47 | 负责人 | @张康 |

第 48 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A48 | 日期 | 7.23 |
| B48 | 每日小结 | 1. 多维成绩查询 提测<br>2. 成绩加权设置 提测<br>3. 线下考勤全生命周期 提测<br>4. 线下成绩（考试/作业）全生命周期：增/改/删、Excel 模板导入、导入结果查询 提测<br>5. 成绩导出 提测 |
| C48 | 负责人 | 倪吉龙 |

第 49 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A49 | 日期 | 7.23 |
| B49 | 每日小结 | 1、补充题库技能skil功能（随机组卷、创建题目、题库去重） |
| C49 | 负责人 | @陈源富 |

第 50 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A50 | 日期 | 7.23 |
| B50 | 每日小结 | 1.梳理备课业务流程<br>2.备课教学设计接口编排 |
| C50 | 负责人 | @赵洪恩 |

第 51 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A51 | 日期 | 7.24 |
| B51 | 每日小结 | 1.回复讨论/管理回答 提测<br>2.作业5种类型数据导出 提测<br>3.回复学生提问 提测 |
| C51 | 负责人 | @张康 |

第 52 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A52 | 日期 | 7.24 |
| B52 | 每日小结 | 1.备课教学设计脚本提供<br>2.备课课堂设计脚本提供<br>3.AIGC问题排查 |
| C52 | 负责人 | @赵洪恩 |

第 53 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A53 | 日期 | 7.25 |
| B53 | 每日小结 | 1.备课脚本更新<br>2.学期参数确定使用逻辑 |
| C53 | 负责人 | @赵洪恩 |

第 54 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A54 | 日期 | 7.27 |
| B54 | 每日小结 | 1.分批上线编排接口<br>2.备课脚本补充 |
| C54 | 负责人 | @赵洪恩 |

第 55 行

| 单元格 | 原始表头 | 原始值 |
| --- | --- | --- |
| A55 | 日期 | 7.27 |
| B55 | 每日小结 | 1. 智能体教学-发布<br>2.skill功能学期及课程查询调整 |
| C55 | 负责人 | @朱希文 |
