# CLAUDE SKILLS

**Generated:** 2026-03-04

## OVERVIEW

Claude Code自动化技能系统。根据实训任务文档自动生成训练配置、评价标准、封面图、背景图。

---

## STRUCTURE

```
.claude/skills/
├── training-config-setup/          # 基础配置+封面图生成
├── training-rubric-generator/      # 评价标准生成
├── training-script-generator/      # 训练剧本配置
├── training-dialogue-simulator/    # 对话流程模拟
├── training-background-generator/  # 阶段背景图生成
├── training-deploy-and-test/       # 部署+自动测试
├── homework-answer-generator/      # 作业答案生成
└── doubao_skill_runner.py          # Doubao API调用基类
```

---

## WHERE TO LOOK

| 任务 | Skill | 触发词 | 输出 |
|------|-------|--------|------|
| 生成基础配置 | `training-config-setup` | "基础配置"、"封面图" | 基础配置.json + 封面图 |
| 生成评价标准 | `training-rubric-generator` | "评价标准"、"评分标准" | 评价标准.json/.md |
| 生成训练剧本 | `training-script-generator` | "训练剧本"、"实训配置" | 训练剧本配置.md |
| 模拟对话流程 | `training-dialogue-simulator` | "对话流程"、"模拟对话" | 对话流程模拟.md |
| 生成背景图 | `training-background-generator` | "背景图"、"阶段图片" | backgrounds/*.png |
| 一键部署测试 | `training-deploy-and-test` | "部署测试"、"导入平台" | 平台任务+测试报告 |

---

## CONVENTIONS

### Skill调用方式
```
@路径/实训任务文档.md [指令]
```

### 一键全量生成
```
@化工原理/实训任务.md 生成基础配置、评价标准、训练剧本和对话流程
```
自动执行顺序：
1. config-setup → 基础配置+封面图
2. rubric-generator → 评价标准
3. script-generator → 训练剧本
4. dialogue-simulator → 对话流程
5. background-generator → 阶段背景图（如要求）

### 输出目录结构
```
课程文件夹/
├── 实训任务文档.md
└── 任务名称/                      # 自动生成
    ├── 基础配置.json
    ├── 封面图提示词.txt
    ├── 封面图.png
    ├── 评价标准.json
    ├── 评价标准.md
    ├── 训练剧本配置.md
    ├── 对话流程模拟.md
    └── backgrounds/
        ├── stage_1_xxx.png
        └── generation_record.json
```

### LangGPT框架
所有提示词使用标准LangGPT结构：
- Role / Profile / Rules / Workflow / Constraints / Context / Examples

---

## ANTI-PATTERNS

| 禁止 | 正确做法 |
|------|----------|
| 手动复制到平台 | 使用training-deploy-and-test自动导入 |
| 跳过对话示例 | 文档中包含对话示例可生成更精确的剧本 |
| 覆盖已调优配置 | 手动修改后标记`# 手动调优`避免被覆盖 |

---

## COMMANDS

```bash
# Skills通过Claude Code @引用自动调用
# 无需直接运行，但调试时可执行：

cd .claude/skills/training-config-setup
python config_generator.py

cd .claude/skills/training-rubric-generator
# 阅读SKILL.md了解详细配置
```

---

## NOTES

1. **环境变量**: `.claude/skills/.env`配置`ARK_API_KEY`
2. **封面图**: 16:9比例(2560×1440)，Doubao Seedream生成
3. **背景图**: 16:9比例(512×288)，写实中国风
4. **版本管理**: 各Skill有独立CHANGELOG.md
5. **详细文档**: 每个Skill目录下有SKILL.md完整技术文档
