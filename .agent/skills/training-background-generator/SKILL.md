---
name: training-background-generator
description: 根据能力训练剧本配置文档，为每个训练阶段生成写实中国风的16:9背景图片。解析Markdown格式的剧本配置，提取每个阶段的描述和场景配置，生成对应的背景图并保存到任务配置目录。关键词:背景图生成、阶段背景、中国风、写实风格、16:9、训练剧本、场景图片
---

# 训练阶段背景图生成器

根据能力训练剧本配置文档，为每个训练阶段生成写实中国风的16:9背景图片，并自动保存到对应的任务配置目录。

## 使用时机

当用户需要为能力训练的各个阶段生成背景图片时使用此技能，典型场景包括:
- 用户提供了训练剧本配置文档（Markdown格式），需要为每个阶段生成背景图
- 用户提到"生成阶段背景图"、"生成训练背景"、"为剧本生成图片"等关键词
- 用户需要批量生成多个阶段的场景背景图

## 工作流程

### 第一步: 解析剧本配置文档

1. 读取用户提供的训练剧本配置Markdown文件
2. 识别文档中的所有训练阶段（通过 `### 阶段X:` 标题识别）
3. 对每个阶段提取以下信息:
   - **阶段编号和名称**: 如 "阶段1: 开场与现象认知"
   - **阶段描述**: 阶段的目标和内容概述
   - **场景配置**: 包含背景、关键设备、特殊要求等

### 第二步: 设计图片提示词

为每个阶段设计符合以下要求的提示词:

1. **风格要求**:
   - 写实风格（Realistic style）
   - 中国风元素（Chinese aesthetic）
   - 16:9宽屏比例
   - 高质量、专业级渲染

2. **提示词框架**:
   ```
   [场景描述], [关键元素], [人物描述（如有）],
   realistic style, Chinese aesthetic,
   professional lighting, high quality,
   16:9 aspect ratio, cinematic composition
   ```

3. **提示词设计原则**:
   - 融入阶段的核心场景（如工厂车间、会议室、实验室等）
   - 包含场景配置中提到的关键设备或道具
   - 人物采用中国人形象，穿着符合场景的工作服装
   - 氛围与阶段内容匹配（紧急、探讨、总结等）

### 第三步: 生成图片

使用图像生成能力为每个阶段创建背景图:

1. 根据设计的提示词生成16:9比例的图片
2. 确保图片风格一致（同一任务的各阶段保持视觉连贯性）
3. 图片应该清晰、专业、适合作为训练界面的背景

### 第四步: 保存图片

1. 确定保存目录: 剧本配置文档所在的任务配置目录
2. 创建 `backgrounds/` 子目录（如不存在）
3. 按照命名规则保存图片:
   - 格式: `stage_{阶段编号}_{阶段名称简写}.png`
   - 示例: `stage_1_开场与现象认知.png`

### 第五步: 输出结果

向用户报告:
- 成功生成的图片数量
- 每张图片的文件路径
- 使用的提示词（便于后续调整）
- 保存目录的完整路径

## 示例

### 示例输入

用户提供文件: `skills_training_course/化工原理-武夷学院/实训任务文档1-离心泵"汽蚀"故障紧急诊断/训练剧本配置.md`

### 解析结果

| 阶段 | 名称 | 场景描述 |
|-----|------|---------|
| 1 | 开场与现象认知 | 化工厂车间，B区设备间，泵旁有监控屏幕 |
| 2 | 根因分析 | 李主任办公室或泵房，手里拿着运行记录本 |
| 3 | 应急处理与决策 | 泵房和控制室，李主任在旁边指挥 |
| 4 | 知识整合与总结 | 会议室或办公室，墙上贴着维护记录 |

### 生成的提示词示例

**阶段1 - 开场与现象认知**:
```
Industrial chemical plant workshop interior, B-zone equipment room,
centrifugal pump P-101B with monitoring screen showing pressure fluctuations,
Chinese male engineer in blue work uniform examining the pump,
emergency atmosphere with warning lights,
realistic style, Chinese aesthetic,
professional industrial lighting, high quality render,
16:9 aspect ratio, cinematic composition
```

**阶段4 - 知识整合与总结**:
```
Modern meeting room in Chinese industrial facility,
senior supervisor and young engineer reviewing documents together,
wall displays showing maintenance records and temperature charts,
warm collaborative atmosphere, afternoon sunlight through windows,
realistic style, Chinese aesthetic,
professional lighting, high quality render,
16:9 aspect ratio, cinematic composition
```

### 输出文件结构

```
实训任务文档1-离心泵"汽蚀"故障紧急诊断/
├── 训练剧本配置.md
├── backgrounds/
│   ├── stage_1_开场与现象认知.png
│   ├── stage_2_根因分析.png
│   ├── stage_3_应急处理与决策.png
│   ├── stage_4_知识整合与总结.png
```


## 不同场景类型的提示词指南

### 工业/工厂场景
- 强调工业设备的细节和真实感
- 包含安全标识、管道、仪表等元素
- 使用工业照明（如荧光灯、应急灯）
- 人物穿戴工作服、安全帽等防护装备

### 办公/会议场景
- 现代中式办公环境
- 包含白板、投影、文件资料等
- 自然光与室内照明结合
- 人物着正装或商务休闲装

### 实验室场景
- 精密仪器和实验设备
- 干净整洁的实验台
- 专业的实验室照明
- 人物穿戴实验服、护目镜等

### 教学/培训场景
- 教室或培训室环境
- 黑板/白板、教学设备
- 明亮的教学环境照明
- 师生互动的场景

## 注意事项

1. **风格一致性**: 同一任务的所有阶段背景图应保持视觉风格一致
2. **中国风元素**: 人物形象、建筑风格、装饰细节应体现中国特色
3. **写实风格**: 避免卡通化或过度风格化，保持专业真实感
4. **16:9比例**: 确保生成的图片适合作为宽屏界面背景
5. **场景匹配**: 背景图应准确反映阶段的场景配置描述
6. **文件命名**: 使用中文命名以便于识别，确保编码正确（UTF-8）

## 错误处理

1. **文档格式不正确**: 如果无法识别阶段结构，提示用户检查Markdown格式
2. **场景配置缺失**: 如果某阶段没有场景配置，根据阶段描述推断场景
3. **保存失败**: 检查目录权限，确保可以创建文件和目录
4. **图片生成失败**: 记录失败的阶段，继续处理其他阶段，最后汇总报告
