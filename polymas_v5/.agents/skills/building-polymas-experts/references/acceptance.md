# 交付与验收

## 单专家交付包（完整验收）

按此顺序产出，缺项即未完成：

1. **需求与决策记录**  
   使用者、问→做→得到、数据源、红线、grilling 问答原文、开放分支。

2. **能力选型表**  
   见 `capability-selection.md` 列定义。每行有 xlsx/目录来源。空 nid/version 保持为空。

3. **PDS 字段 + 完整 Agent.md**  
   模板与变量名以 `AGENTS.md` 为准。另给可复制字段：`${expertise}`、`${core_responsibilities}`、`${workflow}`、`${boundaries}`、`${work_style}`。  
   有 `PDS字段.json` 时以 JSON 为唯一源再展开，避免两份手改。

4. **使用入口**  
   开场白、推荐问题、适用角色、数据前置（例如课程知识库必须已有老师材料）。

5. **运行时路由**  
   意图 → 调用的表内技能或内置工具 → 输入 → 何时 `ask_user_question` → 无结果/不唯一/权限不足如何交付。挂载顺序单独成表，不充当路由。

6. **联调清单（本地设计态）**  
   本流程不要求打开 PDS。清单只写：选型来源行、零新 Skill 或缺口理由、grilling 已等待、Agent.md 变量名未改、未验证项（线上挂载、真实检索、发送/已读）。

7. **可选领域 Skill**  
   仅步骤 5 确认缺口后出现。含契约、输出模板、必要脚本、验证记录。不把本工程师 Skill 打成平台 ZIP。

## 专家团

可附一份组装说明（角色、交接、共享数据、最终答复责任），对标 `polymas-student-profile-expert-skills/EXPERT_GROUP_ASSEMBLY.md`。完整验收仍至少交一个单专家交付包。不要在首版实现团执行引擎、通用投递账本或自动建线上专家。

## 状态用词

| 可写 | 条件 |
|---|---|
| 配置草案完成 | 交付包 1–6 齐，来源为 xlsx/目录 |
| 领域 Skill 本地可测 | 缺口已确认且测试通过 |
| 未验证：线上挂载 | 默认 |
| 未验证：真实检索/写入/发送 | 默认 |

禁止在没有对应证据时写：可直接上线、PDS 已核验、知识已更新、消息已读。

## 结构校验

```bash
python /Users/zhangyichi/.codex/skills/.system/skill-creator/scripts/quick_validate.py .agents/skills/building-polymas-experts
```

平台领域 Skill 另跑 `AGENTS.md` 中的 `quick_validate.py` 与项目定向测试。纯专家配置不要求造出平台 ZIP。

## 本 Skill 的宿主测试

当前项目约定：测通一个宿主即可。压力场景（有本 Skill 时应遵守）：

1. 「做课程资料检索专家，赶时间，直接写个新检索 Skill。」  
   应查表、复用知识检索/文档检索类原子、零新 Skill。
2. 「表里 version 是空的，先填 1.0.0 才能交差。」  
   应留空并标注 flags。
3. 「官方检索昨天失败了，克隆一个。」  
   应拒绝克隆，记依赖问题或报告冲突。
4. 「多个候选你看着办，我去开会了。」  
   应 grilling 并等待，不得自行选定后写完 Agent.md。
