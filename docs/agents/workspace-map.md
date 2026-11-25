# 工作区总览（能力训练）

各项目的职责、AGENTS.md 与专属 skill / agent 的位置。清单段落由脚本生成，其余为手写约定。人工校对：2026-11-16。

## 项目与职责

| 目录 | 职责 | Git |
|---|---|---|
| `./`（根） | 能力训练自动化脚本、`training-*` 技能、对话评测、凭证与登录约定 | `Skills_Training_Course` |
| `skills_training_course/` | 能力训练课程资料与交付物，按 `学校名-课程名/` 分目录 | 无独立 repo，被根 `.gitignore` 忽略 |
| `HTML/` | 互动网页、视觉小说类项目 | 无独立 repo，被根 `.gitignore` 忽略 |
| `polymas_v5/` | 专家智能体搭建 | 独立 repo `polymas_v5` |
| `homework_review/` | 作业批阅 | 独立 repo |
| `agent_microcourse/` | 智能体微课：旁白微课视频生产（原 `homework_review/智能体微课`，2026-11-16 迁出并改英文名） | 独立 repo `agent-microcourse` |

## 约定

- 每个项目的规则写在自己的 `AGENTS.md`，`CLAUDE.md` 做指向它的软链接（Claude Code 只读 `CLAUDE.md`）。
- 一个技能只放一份实体（清单里标 R），其余位置（`.claude/skills`、`.agents/skills`、`.qoder/skills`）用软链接（L）。出现多处 R 或 X，清单会标 ⚠。
- 业务路由（能力训练 / 专家智能体 / 作业批阅放哪个目录）见 [企业微信任务记录与资料归档](wecom-task-intake.md)。
- 凭证不写入文档，规则见根 `AGENTS.md` 的「共享服务凭证」。
- 增删项目、技能或 agent 后重新生成清单：

```bash
python3 scripts/workspace_inventory.py
```

## 兼容别名

`homework_review/智能体微课` 是指向 `../agent_microcourse` 的软链接。原因：ChatCut Desktop 项目 `3eb94bc3…` 有 178 个素材/对话记录文件，以及历史 Claude 会话，仍写着旧绝对路径。ChatCut 素材全部重新关联后可删除：`rm homework_review/智能体微课`。

## 清单（脚本生成）

<!-- BEGIN GENERATED -->
_生成于 2026-11-16，由 `scripts/workspace_inventory.py` 写入，勿手改。_

| 目录 | Git | AGENTS.md | CLAUDE.md | skills | agents | 散落 SKILL.md |
|---|---|---|---|---|---|---|
| 能力训练（根） | https://github.com/richardzhangy26/Skills_Training_Course.git | 198 行 | → AGENTS.md | 16 | 0 | 0 |
| skills_training_course | 独立 repo（无 origin） | 15 行 | → AGENTS.md | 0 | 0 | 0 |
| HTML | 独立 repo（无 origin） | 21 行 | → AGENTS.md | 0 | 0 | 7 |
| polymas_v5 | https://github.com/richardzhangy26/polymas_v5.git | 268 行 | → AGENTS.md | 1 | 4 | 36 |
| homework_review | https://github.com/richardzhangy26/homework_review.git | 285 行 | → AGENTS.md | 154 | 0 | 0 |
| agent_microcourse | https://github.com/richardzhangy26/agent-microcourse.git | 44 行 | → AGENTS.md | 5 | 0 | 0 |

Skill 表图例：R=实体目录 L=有效软链接 X=失效软链接 ·=不存在。

### 能力训练（根）（`./`）
- Git：https://github.com/richardzhangy26/Skills_Training_Course.git
- AGENTS.md：198 行；CLAUDE.md：→ AGENTS.md

| skill | .claude/skills | .agents/skills | .qoder/skills | .codex/skills | 说明 |
|---|---|---|---|---|---|
| `app-submit-publish` | · | R | · | · | 通过 Polymas 浏览器授权上传前端构建产物 ZIP，创建或覆盖并发布为在线… |
| `english-speaking-prompt-expert` | R | L | L | R | English-speaking training prompt expert … |
| `exam-to-question-bank` | R | L | · | · | 将试卷文档（.doc/.docx/.pdf/txt）整理为可导入题库系统的"题号… |
| `homework-answer-generator` | R | L | L | · |  |
| `task-router` | R | · | · | · | （无 SKILL.md） |
| `training-auto-login` | R | L | L | · | 智能体课程平台自动登录并自动进入课程。根据训练剧本文件路径识别学校和课程，查找省… |
| `training-background-generator` | R | L | L | · | 根据能力训练剧本 Markdown 批量生成阶段背景图和任务封面，优先使用项目 … |
| `training-config-setup` | R | L | L | · | 根据实训任务文档生成基础配置，包括提取任务名称、描述，以及使用Doubao模型生… |
| `training-deploy-and-test` | R | L | L | · | 端到端自动化流程：根据训练剧本Markdown生成背景图、导入Polymas平台… |
| `training-dialogue-simulator` | R | L | L | R | 根据训练剧本配置生成纯净的学生-智能体对话流程,采用简洁的一问一答格式,无需额外… |
| `training-evaluator` | R | L | R | · | 对能力训练智能体的教学对话做批量 LLM 评测，输入教师文档 + 对话日志（单文… |
| `training-pro-script-generator` | R | L | · | · | Use when users need an Ability Training … |
| `training-prompt-expert` | R | L | L | R | 提示词内容专家 - 基于4种经实战验证的Skill模板（循序过关型/模拟人物型/… |
| `training-rubric-generator` | R | L | L | R | 根据实训任务文档生成层级化的评价标准，采用"主评分项-子得分点"结构，每个子得分… |
| `training-script-generator` | R | L | L | · | 根据实训任务文档自动生成完整的能力训练剧本配置。生成包含阶段名称、互动轮次、提示… |
| `training-script-generator-v2` | R | L | L | R | 实训剧本架构师 - 将非标准化实训任务文档转化为结构清晰、逻辑严密的Markdo… |

- ⚠ 多处实体或失效链接：`english-speaking-prompt-expert`, `training-dialogue-simulator`, `training-evaluator`, `training-prompt-expert`, `training-rubric-generator`, `training-script-generator-v2`

### skills_training_course（`skills_training_course/`）
- Git：独立 repo（无 origin）
- AGENTS.md：15 行；CLAUDE.md：→ AGENTS.md

### HTML（`HTML/`）
- Git：独立 repo（无 origin）
- AGENTS.md：21 行；CLAUDE.md：→ AGENTS.md

- 散落的 SKILL.md（7）：`creator_tool_vip`, `polymas-webpage-generate-skills`, `东北师范-外国文学史/literary-bookshelf-component/literature-bookshelf`, `东北师范-外国文学史/literary-course-component/literature-course`, `东北师范-外国文学史/literary-reading-director`, `东北师范-外国文学史/local-skill-to-zhs-component`, `东北师范-外国文学史/zhs-lit-web-component`

- 子目录 AGENTS.md（2）：`-demo/AGENTS.md`, `chuanzang-interactive-map/AGENTS.md`

### polymas_v5（`polymas_v5/`）
- Git：https://github.com/richardzhangy26/polymas_v5.git
- AGENTS.md：268 行；CLAUDE.md：→ AGENTS.md

| skill | .agents/skills | 说明 |
|---|---|---|
| `building-polymas-experts` | R | Use when designing or revising a Polymas… |

- Agents：`.codex/agents/polymas_architect.toml`, `.codex/agents/polymas_implementer.toml`, `.codex/agents/polymas_reviewer.toml`, `.codex/agents/polymas_verifier.toml`

- 散落的 SKILL.md（36）：`ai翻转/data-law-case-expert/data-law-case-maintenance`, `ai翻转/data-law-case-expert/data-law-case-query`, `daily-tech-news`, `polymas-finance-news-expert/finance-news-commentary`, `polymas-student-profile-expert-skills/personalized-learning-feed`, `polymas-student-profile-expert-skills/student-survey-profile`, `polymas-teacher-work-calendar`, `北京师范大学-分子生物学/Helix学术检索专家/bioinfo-db-search`, `北京师范大学-分子生物学/Helix学术检索专家/deep-search`, `北京师范大学-分子生物学/deep-search`, `北京师范大学-分子生物学/external-knowledge-search`, `宁波大学-大学生的AI营养师/nutrition-evidence-report`, `西南交通大学-机车车辆结构及强度/LC-P1/skills/swjt-p1-deliverable-coach`, `西南交通大学-机车车辆结构及强度/LC-P1/skills/swjt-p1-foundation-diagnosis`, `西南交通大学-机车车辆结构及强度/LC-P1/skills/swjt-p1-standard-loadcase-guide`, `西南交通大学-机车车辆结构及强度/LC-P2/skills/swjt-p2-deliverable-coach`, `西南交通大学-机车车辆结构及强度/LC-P2/skills/swjt-p2-disassembly-guide`, `西南交通大学-机车车辆结构及强度/LC-P2/skills/swjt-p2-strength-protection-analysis`, `西南交通大学-机车车辆结构及强度/LC-P3/skills/swjt-p3-control-practice-guide`, `西南交通大学-机车车辆结构及强度/LC-P3/skills/swjt-p3-risk-scenario-diagnosis`, `西南交通大学-机车车辆结构及强度/LC-P3/skills/swjt-p3-strategy-deliverable-coach`, `西南交通大学-机车车辆结构及强度/LC-P4/skills/swjt-p4-final-deliverable-coach`, `西南交通大学-机车车辆结构及强度/LC-P4/skills/swjt-p4-integrated-design-diagnosis`, `西南交通大学-机车车辆结构及强度/LC-P4/skills/swjt-p4-test-monitoring-guide`, `西南交通大学-机车车辆结构及强度/验收/修订前草稿/swjt-p1-standard-loadcase-guide`, `西南交通大学-机车车辆结构及强度/验收/修订前草稿/swjt-p2-deliverable-coach`, `西南交通大学-机车车辆结构及强度/验收/修订前草稿/swjt-p2-disassembly-guide`, `西南交通大学-机车车辆结构及强度/验收/修订前草稿/swjt-p3-control-practice-guide`, `西南交通大学-空间信息/01-勘疆/skills/swjtu-spatial-data-3d-guide`, `西南交通大学-空间信息/02-纳川/skills/swjtu-spatiotemporal-data-guide`, `西南交通大学-空间信息/03-御险/skills/swjtu-hazard-modeling-guide`, `西南交通大学-空间信息/04-铸智/skills/swjtu-spatial-agent-twin-guide`, `西南交通大学-空间信息/05-铢较/skills/swjtu-spatial-quality-review`, `西南交通大学-空间信息/06-守界/skills/swjtu-spatial-trust-safety-review`, `西南交通大学-空间信息/07-驿呈/skills/swjtu-project-delivery-defense`, `鲁东大学-船舶快速性实验/船舶快速性试验专家/ship-speed-lab-analysis`

- 子目录 AGENTS.md（1）：`北京师范大学-分子生物学/Helix-Qoder测试/runtime/AGENTS.md`

### homework_review（`homework_review/`）
- Git：https://github.com/richardzhangy26/homework_review.git
- AGENTS.md：285 行；CLAUDE.md：→ AGENTS.md

- Skills 共 154 个（`.claude/skills` 4 个；`.agents/skills` 1 个；`.qoder/skills` 153 个）
<details><summary>名称列表</summary>

`create-custom-homework-review-skill`, `grade-action-video-comparison`, `grade-ai-sales-consultant-ppt-transcript`, `grade-ai-sales-consultant-transcript-only`, `grade-ai-sales-consultant-video`, `grade-ai-sales-consultant-video-preprocessed`, `grade-aquatic-algae-confusable-species`, `grade-aseptic-slant-inoculation-video`, `grade-basic-chinese-lesson-1-greetings-audio`, `grade-basic-chinese-lesson-1-greetings-writing`, `grade-basic-sterile-technique-video`, `grade-brand-ip-final-poster`, `grade-brand-ip-research-presentation`, `grade-c-number-to-words`, `grade-canteen-healthy-breakfast`, `grade-cet-english-writing`, `grade-college-english-writing-translation`, `grade-communication-principles`, `grade-communication-principles-test-1`, `grade-communication-principles-test-2`, `grade-communication-principles-test-3`, `grade-course-pitch-video`, `grade-digital-logic-ch5-2-3-15`, `grade-digital-logic-four-questions`, `grade-discrete-math-proof-reasoning`, `grade-english-debate-mun`, `grade-english-speech-presentation`, `grade-environmental-health-course-paper`, `grade-environmental-health-ppt-video-presentation`, `grade-gzu-mental-health-ch1-case-analysis`, `grade-gzu-mental-health-ch1-collage-portrait`, `grade-gzu-mental-health-ch1-coordinate-plan`, `grade-gzu-mental-health-ch1-posttest-case`, `grade-gzu-mental-health-ch1-pretest`, `grade-gzu-mental-health-ch1-toolbox-poster`, `grade-gzu-mental-health-ch2-action-card`, `grade-gzu-mental-health-ch2-adaptation-declaration`, `grade-gzu-mental-health-ch2-challenge-panorama`, `grade-gzu-mental-health-ch2-intro`, `grade-gzu-mental-health-ch2-intro-pretest`, `grade-gzu-mental-health-ch2-life-puzzle`, `grade-gzu-mental-health-ch2-peer-help`, `grade-gzu-mental-health-ch2-posttest-case`, `grade-gzu-mental-health-ch2-pretest`, `grade-gzu-mental-health-ch3-action-card`, `grade-gzu-mental-health-ch3-gulf-alchemy`, `grade-gzu-mental-health-ch3-intro-pretest`, `grade-gzu-mental-health-ch3-lifeline`, `grade-gzu-mental-health-ch3-posttest-case`, `grade-gzu-mental-health-ch3-significant-others`, `grade-gzu-mental-health-ch3-three-namecards`, `grade-gzu-mental-health-ch4-big-five`, `grade-gzu-mental-health-ch4-course-summary`, `grade-gzu-mental-health-ch4-inner-critic`, `grade-gzu-mental-health-ch4-intro-pretest`, `grade-gzu-mental-health-ch4-posttest-case`, `grade-gzu-mental-health-ch4-ta-voices`, `grade-gzu-mental-health-ch5-energy-bottle`, `grade-gzu-mental-health-ch5-growth-mindset`, `grade-gzu-mental-health-ch5-hs-vs-college`, `grade-gzu-mental-health-ch5-intro-pretest`, `grade-gzu-mental-health-ch5-learning-designer`, `grade-gzu-mental-health-ch5-posttest-case`, `grade-gzu-mental-health-ch5-study-methods`, `grade-gzu-mental-health-ch5-time-management`, `grade-gzu-mental-health-ch6-action-card`, `grade-gzu-mental-health-ch6-dorm-boundary`, `grade-gzu-mental-health-ch6-intro-pretest`, `grade-gzu-mental-health-ch6-network-map`, `grade-gzu-mental-health-ch6-posttest-case`, `grade-gzu-mental-health-ch6-psych-effects`, `grade-gzu-mental-health-ch6-relation-boat`, `grade-gzu-mental-health-ch6-social-anxiety`, `grade-gzu-mental-health-ch7-action-card`, `grade-gzu-mental-health-ch7-conflict-mediation`, `grade-gzu-mental-health-ch7-intro-pretest`, `grade-gzu-mental-health-ch7-love-languages`, `grade-gzu-mental-health-ch7-love-map`, `grade-gzu-mental-health-ch7-posttest-case`, `grade-gzu-mental-health-ch7-unsent-letter`, `grade-gzu-mental-health-ch8-action-card`, `grade-gzu-mental-health-ch8-emotional-release`, `grade-gzu-mental-health-ch8-expressive-art`, `grade-gzu-mental-health-ch8-intro-pretest`, `grade-gzu-mental-health-ch8-mindful-breathing`, `grade-gzu-mental-health-ch8-posttest-case`, `grade-gzu-mental-health-ch8-resilience-stone`, `grade-gzu-mental-health-ch8-ret-abcde`, `grade-gzu-mental-health-ch9-action-card`, `grade-gzu-mental-health-ch9-crisis-support`, `grade-gzu-mental-health-ch9-intro-pretest`, `grade-gzu-mental-health-ch9-leaf-letter`, `grade-gzu-mental-health-ch9-life-attitude`, `grade-gzu-mental-health-ch9-major-value`, `grade-gzu-mental-health-ch9-meaning-list`, `grade-gzu-mental-health-ch9-posttest-case`, `grade-gzu-mental-health-chapter-summary`, `grade-gzu-semester-start-self-assessment`, `grade-hailuo-bijian-eco-dubbing-subtitles`, `grade-hbut-exp1-context-learning`, `grade-hfut-digital-logic-ch2-258`, `grade-hfut-digital-logic-ch4-18-21-22`, `grade-hfut-digital-logic-ch6`, `grade-hunnu-dorm-workout`, `grade-ielts-writing`, `grade-information-engineering-chapter3-cmos`, `grade-japanese-diary-portfolio`, `grade-java-web-assignment`, `grade-java-web-servlet-exam`, `grade-jimeng-image-to-video-heavy-equipment`, `grade-jimeng-text-to-video-homework`, `grade-knowledge-graph-case-report`, `grade-knowledge-graph-course-summary`, `grade-ldu-propeller-design`, `grade-ldu-propeller-openwater`, `grade-ldu-ship-model-resistance`, `grade-ldu-ship-selfpropulsion`, `grade-legal-clinic-negotiation`, `grade-ljct-graduation-design-thesis`, `grade-low-carbon-ai-voiceover`, `grade-marketing-course-general`, `grade-music-performance`, `grade-nasogastric-feeding-video`, `grade-ntu-english-microteaching`, `grade-qqhr-fourier-properties`, `grade-qqhru-intelligent-communication-ch6`, `grade-sdfmu-surgical-roleplay`, `grade-sme-credit-risk-case`, `grade-surgical-gown-glove-video`, `grade-surgical-handwash-seven-step-video`, `grade-uestc-english-book-video`, `grade-used-car-workorder-01-trade-documents`, `grade-used-car-workorder-02-assessment-tools`, `grade-used-car-workorder-03-assessment-sheet`, `grade-used-car-workorder-04-accident-vehicle`, `grade-used-car-workorder-05-exterior`, `grade-used-car-workorder-06-engine-compartment`, `grade-used-car-workorder-07-interior`, `grade-used-car-workorder-08-luggage-compartment`, `grade-used-car-workorder-09-chassis`, `grade-used-car-workorder-10-usage-records`, `grade-used-car-workorder-11-flood-fire`, `grade-used-car-workorder-12-odometer-tampering`, `grade-used-car-workorder-13-vehicle-photography`, `grade-used-car-workorder-14-dynamic-condition`, `grade-used-car-workorder-15-valuation`, `grade-used-car-workorder-16-appraisal-report`, `grade-used-car-workorder-17-refurbishment`, `grade-waveform-homework`, `grade-wraparound-surgical-gown-glove-video`, `grade-ynart-tourism-creative-ppt`, `grade-zhihuishu-agent-course-document`, `grade-zhihuishu-agent-course-video`, `grade-zust-english-speech-av`

</details>

### agent_microcourse（`agent_microcourse/`）
- Git：https://github.com/richardzhangy26/agent-microcourse.git
- AGENTS.md：44 行；CLAUDE.md：→ AGENTS.md

| skill | .claude/skills | .agents/skills | 说明 |
|---|---|---|---|
| `ai-pptx-video-signoff` | L | R |  |
| `chatcut-integrated-microlesson` | R | L | 用 ChatCut × 本地 seedance 整合工作流制作旁白微课视频：讲稿… |
| `narration-video-generation` | R | L | Route narrated-video requests into the r… |
| `pptx-native-video` | L | R | Mandatory router for narrated-video requ… |
| `pptx-native-video-vip` | L | R | Mandatory router for narrated-video requ… |
<!-- END GENERATED -->
