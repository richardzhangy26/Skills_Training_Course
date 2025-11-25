# 能力训练项目说明

本项目的目标是：

- **借助 Claude Code Skills 或其他大模型**，搭建一套可复用的「能力训练」流程
- 把训练剧本、指令模版、素材文档（docx → md）、以及技能脚本代码统一管理
- 让大模型可以按既定流程，引导学员完成多轮互动训练

---

## 项目结构

整体目录（简化）：

- `docx_to_md.py`
  - 将培训用的 Word 文档（`.docx`）转换为 Markdown（`.md`）
  - 支持表格、图片基本保留
  - 图片会输出到：`media/<文档名>/` 目录中

- `media/`
  - 存放从 docx 中提取出的图片资源
  - 已在 `.gitignore` 中忽略，不会进入版本库

- `.claude/skills/`
  - 存放针对本项目定制的 **Claude Code Skill** 配置
  - 每个子目录代表一个技能，目前已实现 4 个核心技能：
    - **training-config-setup** (v1.0): 生成基础配置和 Doubao AI 封面图
    - **training-rubric-generator** (v1.0): 生成详细的评价标准（包含大模型评判指南）
    - **training-script-generator** (v1.2): 生成完整的训练剧本配置
    - **training-dialogue-simulator** (v1.1): 生成对话流程模拟和测试脚本
  - 通过这些技能，可以在 IDE 中一键生成 / 调整完整的训练流程

- `README.md`
  - 项目整体说明（当前文件）

---

## 能力训练整体思路

1. **内容准备阶段**
   - 培训内容通常由产品、运营或培训负责人以 **Word 文档（docx）** 形式提供
   - 使用 `docx_to_md.py` 将这些文档批量转换为 Markdown，便于版本管理与后续处理

2. **自动化配置生成阶段**（新增 ✨）
   - 通过 4 个专用 Skill，自动生成完整的训练配置：

   | 步骤 | Skill | 输出 | 说明 |
   |-----|-------|------|------|
   | 第1步 | training-config-setup | `基础配置.json`、`封面图` | 生成任务基础配置和 AI 生成的专业级 16:9 封面图 |
   | 第2步 | training-rubric-generator | `评价标准.json`、`评价标准.md` | 生成包含大模型评判指南、正反例的详细评价标准 |
   | 第3步 | training-script-generator | `训练剧本配置.md` | 生成完整的多阶段训练剧本，包含 LangGPT 框架提示词 |
   | 第4步 | training-dialogue-simulator | `对话流程模拟.md` | 生成真实对话示例和测试验证脚本 |

   - 可以一次性调用所有 4 个 Skill，或按需单步调用

3. **结构化训练流程**
   - 每个训练任务自动生成包含以下内容的完整配置：
     - **基础配置**：任务名称、描述、封面、元数据
     - **评价标准**：3-5 个评分项，每项包含：
       - 满分值、用户描述
       - 大模型评判指南（200-300字）
       - 关键评判点、常见错误、评分逻辑
       - 优秀示例和不足示例
     - **训练剧本**：多阶段线性流程，每阶段包含：
       - 阶段名称、目标、互动轮次
       - 开场白、LangGPT 框架提示词
       - 场景配置和阶段跳转条件
     - **对话流程**：NPC 角色设定、多等级学生示例、完整对话路径、测试要点

4. **执行训练流程**
   - 在 IDE 中调用 Claude Code Skills：
     - 读取对应的 Markdown 培训文档
     - 自动生成多层次的训练配置
     - 按剧本流程驱动与学员的多轮互动
   - 目标是：**让大模型像"教练"一样，按照既定步骤完成整套能力训练**。

5. **版本管理与迭代**
   - 所有训练配置、提示模版、示例对话都放在仓库中统一管理
   - 每个任务生成独立的配置目录，包含所有必要文件
   - 通过 Git 进行版本控制，便于：
     - 比较每次训练方案的变化
     - 回滚到历史版本
     - 针对不同批次学员不断优化训练流程

---

## docx → md 转换脚本使用

> 脚本文件：`docx_to_md.py`

1. 安装依赖：

   ```bash
   pip install python-docx
   ```

2. 在包含 docx 的目录下运行：

   ```bash
   python docx_to_md.py "培训文档-能力训练（持续更新）.docx"
   ```

3. 输出结果：

   - 同目录生成同名 Markdown：`培训文档-能力训练（持续更新）.md`
   - 图片输出到：`media/培训文档-能力训练（持续更新）/` 下
   - Markdown 中会：
     - 转换标题、正文、表格
     - 尝试让图片出现在与原 docx 接近的位置

这些 Markdown 文档将作为 **大模型的输入素材**，用于生成训练剧本与对话流程。

---

## 快速开始：完整工作流程

### 方式 1：一键生成所有配置（推荐）

```bash
# 在 IDE 中引用任务文档，一次生成完整配置
@实训任务文档.md
我需要生成基础配置、评价标准、训练剧本和对话流程
```

自动执行顺序：
1. training-config-setup → 生成基础配置和 16:9 封面图
2. training-rubric-generator → 生成详细评价标准
3. training-script-generator → 生成训练剧本配置
4. training-dialogue-simulator → 生成对话流程模拟

### 方式 2：分步调用（灵活）

```bash
# 第一步：生成基础配置和封面图
@实训任务文档.md 生成基础配置和封面图

# 第二步：生成评价标准
@实训任务文档.md 生成评价标准

# 第三步：生成训练剧本
@实训任务文档.md 生成训练剧本

# 第四步：生成对话流程
@实训任务文档.md 生成对话流程
```

## 已完成的示例

### 发电厂、变电所的认知（锡林郭勒职业学院）

生成的配置目录：`发电厂变电所 - 锡林郭勒职业学院 2个/任务1：发电厂、变电所的认知/`

包含文件：
- ✅ `基础配置.json` - 任务基本信息和元数据
- ✅ `评价标准.json` + `评价标准.md` - 3 个评分项的详细评价标准
- ✅ `训练剧本配置.md` - 4 个阶段的完整训练流程
- ✅ `对话流程模拟.md` - NPC 角色、3 个学生水平的完整对话示例

配置特点：
- 智能体角色：小智（40 岁电网值班长，15 年经验）
- 4 阶段训练：系统概述 → 深入分析 → 背景了解 → 总结评价
- 完整对话示例：优秀生（9-10分）、中等生（7-8分）、欠佳生（5-6分）
- 详细评判指南：适配大模型的 200-300 字评判参考

## 配合 Claude Code Skills 的使用建议

- **Skill 特性**
  - 4 个核心 Skill 已实现，支持自动化生成完整训练配置
  - 每个 Skill 可独立使用，也可串联调用
  - 所有 Skill 包含完整的 README、SKILL.md 文档和使用示例

- **提示词管理**
  - 高质量的提示词模版已沉淀在 Skill 的配置中
  - 支持基于课程类型的自动匹配和生成
  - 所有生成的提示词都遵循 LangGPT 框架

- **人机协同**
  - 由培训负责人审核 Skill 生成的训练配置
  - 可根据实际测试效果调整提示词和互动轮次
  - 实际训练数据用于持续优化流程

---

## 所有 Skills 文档导航

### 1. training-config-setup (v1.0)
- **功能**：生成基础配置和 Doubao AI 生成的 16:9 封面图
- **输出**：`基础配置.json`、`封面图提示词.txt`、`封面图`
- **文档**：[.claude/skills/training-config-setup/README.md](./.claude/skills/training-config-setup/README.md)

### 2. training-rubric-generator (v1.0)
- **功能**：生成详细的评价标准，包含大模型评判指南
- **输出**：`评价标准.json`、`评价标准.md`
- **文档**：[.claude/skills/training-rubric-generator/README.md](./.claude/skills/training-rubric-generator/README.md)

### 3. training-script-generator (v1.2)
- **功能**：生成完整的训练剧本配置，遵循 LangGPT 框架
- **输出**：`训练剧本配置.md`
- **文档**：[.claude/skills/training-script-generator/README.md](./.claude/skills/training-script-generator/README.md)

### 4. training-dialogue-simulator (v1.1)
- **功能**：生成对话流程模拟和测试验证脚本
- **输出**：`对话流程模拟.md`
- **文档**：[.claude/skills/training-dialogue-simulator/README.md](./.claude/skills/training-dialogue-simulator/README.md)

## 后续可以扩展的方向

- 为化工原理课程的其他任务生成完整配置（离心泵、精馏、二氧化碳吸收）
- 为其他行业和领域创建专用训练 Skill（医疗、金融、客服等）
- 根据训练结果自动生成学员评估报告
- 为每个训练模块自动生成小测验题库
- 接入其他大模型（如 OpenAI / 通义等）作为备选执行引擎
- 构建可视化的训练流程设计器

## 技术栈

- **Skill 开发**：Python + Claude Code SDK
- **图像生成**：Doubao API (doubao-seedream-4-0-250828)
- **提示词框架**：LangGPT
- **文档格式**：Markdown + JSON
- **版本控制**：Git

## 联系与反馈

如有问题或建议，欢迎通过以下方式反馈：
- 提交 Issue：https://github.com/richardzhangy26/Skills_Training_Course/issues
- 更新文档：直接编辑相关 .md 文件
- 改进 Skill：修改 `.claude/skills/` 下的相应文件
