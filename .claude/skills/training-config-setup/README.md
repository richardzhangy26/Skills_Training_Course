# Training Config Setup - 训练基础配置生成器

快速为能力训练生成基础配置和AI生成的16:9封面图。

## 功能特性

✨ **自动提取任务信息**
- 从MD文档中智能提取任务名称
- 自动抓取任务描述

🎨 **Doubao智能生成封面图**
- 使用Doubao模型生成专业级16:9封面图
- 智能提示词生成（根据课程类型自动匹配）
- 支持水印自动添加

📋 **生成规范化配置**
- JSON格式基础配置
- 包含元数据和来源信息
- 兼容现有训练系统

## 快速开始

### 1. 环境配置

确保已设置 `ARK_API_KEY` 环境变量：

```bash
export ARK_API_KEY='your-api-key-from-volces'
```

### 2. 使用方法

#### 方式A：通过Claude Code调用
```
请根据以下文档生成基础配置:
@化工原理-武夷学院/实训任务文档1-离心泵"汽蚀"故障紧急诊断.md
```

Claude会自动调用此skill：
- 提取任务名称和描述
- 生成封面图提示词
- 调用Doubao生成16:9的高清封面图
- 保存配置文件到任务目录

#### 方式B：直接运行Python脚本
```bash
cd /Users/richardzhang/工作/能力训练/.claude/skills/training-config-setup/
python config_generator.py "path/to/your/markdown/file.md"
```

## 输出文件说明

执行后会在任务文档目录创建如下文件结构：

```
化工原理-武夷学院/
├── 实训任务文档1-离心泵"汽蚀"故障紧急诊断.md
└── 离心泵汽蚀故障紧急诊断/                    ← 新创建的任务目录
    ├── 基础配置.json                          ← 主配置文件
    └── 封面图提示词.txt                        ← 提示词备份
```

### 基础配置.json 结构

```json
{
  "taskName": "离心泵汽蚀故障紧急诊断",
  "taskDescription": "通过模拟真实的工业现场故障场景，让学生作为工程师快速诊断和处理离心泵汽蚀问题。",
  "coverImage": {
    "url": "https://ark.cn-beijing.volces.com/api/v3/image/...",
    "prompt": "工业化工厂，离心泵运行场景，技术人员在仔细检查泵的状态...",
    "format": "16:9",
    "size": "2K",
    "model": "doubao-seedream-4-0-250828"
  },
  "metadata": {
    "createdAt": "2025-11-25T10:30:00.000Z",
    "source": "化工原理-武夷学院/实训任务文档1-离心泵汽蚀故障紧急诊断.md"
  }
}
```

## 提示词生成规则

系统会根据任务内容自动匹配和生成提示词：

| 关键词 | 提示词风格 | 应用场景 |
|-------|-----------|--------|
| 离心泵、汽蚀 | 工业现场、故障诊断 | 工业故障排查 |
| 精馏 | 化学实验、科学仪器 | 化工实验操作 |
| 展馆 | 科技展示、互动体验 | 虚拟展馆参观 |
| 非暴力沟通 | 协作、人物互动 | 软技能培训 |
| 投资 | 会议、商务环境 | 商务沟通 |

## 与其他Skill的配合

```
┌─────────────────────────────────────┐
│  1. training-config-setup           │
│  生成基础配置和封面图                │
└──────────────────┬──────────────────┘
                   │
                   ↓
┌─────────────────────────────────────┐
│  2. training-script-generator       │
│  生成完整的训练剧本配置              │
└──────────────────┬──────────────────┘
                   │
                   ↓
┌─────────────────────────────────────┐
│  3. training-dialogue-simulator     │
│  模拟对话流程测试                    │
└─────────────────────────────────────┘
```

## 错误处理

| 错误类型 | 原因 | 解决方案 |
|---------|------|--------|
| ARK_API_KEY未设置 | 环境变量缺失 | `export ARK_API_KEY='...'` |
| Doubao API调用失败 | 网络问题或API额度 | 检查网络，确认API配额 |
| 文件不存在 | 路径错误 | 确认MD文档路径正确 |
| 提示词为空 | 文档内容不足 | 查看是否有任务描述 |

## 技术细节

### 使用的Doubao模型
- **模型**: doubao-seedream-4-0-250828
- **图片大小**: 2K (2560×1440，16:9比例)
- **响应格式**: URL（可直接使用）
- **水印**: 自动添加

### API调用示例
```python
from openai import OpenAI

client = OpenAI(
    base_url="https://ark.cn-beijing.volces.com/api/v3",
    api_key=os.environ.get("ARK_API_KEY"),
)

response = client.images.generate(
    model="doubao-seedream-4-0-250828",
    prompt="您的提示词",
    size="2K",
    response_format="url",
    extra_body={"watermark": True},
)

print(response.data[0].url)
```

## 常见问题

**Q: 如果我不满意生成的提示词？**
A: 可以编辑 `封面图提示词.txt` 文件，使用新的提示词重新调用API生成图片。

**Q: 支持哪些文档格式？**
A: 目前只支持 Markdown (.md) 格式。

**Q: 生成的图片可以直接使用吗？**
A: 可以。URL是永久有效的，包含水印。如需去除水印，需要付费版本。

**Q: 如何批量生成多个任务的配置？**
A: 目前需要逐个调用，后续可以开发批量处理功能。

## 版本信息

- **当前版本**: v1.0
- **发布日期**: 2025-11-25
- **状态**: 稳定版本

## 相关资源

- [SKILL.md](./SKILL.md) - 完整技术文档
- [config_generator.py](./config_generator.py) - 核心Python实现
- [examples.md](./examples.md) - 使用示例

## 许可证

内部使用版本，仅供教学和培训使用。
