# PROJECT KNOWLEDGE BASE

**Generated:** 2026-03-04

## OVERVIEW

AI教育平台自动化测试系统（能力训练工作流测试）。模拟学生-AI对话，测试对话式教学任务质量。

**Core Stack:** Python + Doubao/DeepSeek LLM + WebSocket

---

## STRUCTURE

```
能力训练/
├── auto_script_train.py              # 主入口：3档学生画像测试
├── auto_script_train_5characters.py  # 扩展：5角色并发测试
├── auto_audio_train.py               # WebSocket语音训练测试
├── workflow_tester_base.py           # 共享基类（API/日志/重试）
├── skill_training_build/             # Markdown→平台任务构建
├── homework_review/                  # AI作业批改工具
├── evaluation/                       # 对话质量评测（5维度20子维度）
├── .claude/skills/                   # Claude Code自动化技能
├── prompts/                          # 评测提示词模板
├── skills_training_course/           # 课程文档/任务源文件
└── log/                              # 测试日志（txt+json）
```

---

## WHERE TO LOOK

| 任务 | 入口文件 | 说明 |
|------|----------|------|
| 运行工作流测试 | `auto_script_train.py` | 3档学生：good/medium/bad |
| 并发压力测试 | `auto_script_train_5characters.py` | 5角色并行 |
| 语音训练测试 | `auto_audio_train.py` | WebSocket+TTS实时 |
| 从Markdown构建任务 | `skill_training_build/create_task_from_markdown.py` | 自动生成节点+流程 |
| 作业批改 | `homework_review/homework_reviewer_v2.py` | 上传→解析→评分 |
| 对话质量评测 | `python -m evaluation` | 5维度规则+LLM混合评测 |
| 查看API基类 | `workflow_tester_base.py` | 所有脚本继承自此 |

---

## CONVENTIONS

### 环境配置
- **必需**: `.env`文件（从`.env.example`复制）
- **认证**: `AUTHORIZATION`(JWT) + `COOKIE`从浏览器DevTools获取
- **LLM后端**: `MODEL_TYPE`选择 `doubao_sdk`/`doubao_post`/`deepseek_sdk`

### 学生画像
- **3档**: good(优秀) / medium(需引导) / bad(跑题)
- **5档**: S1(沉默) / S2(配合) / S3(完美主义) / S4(捣乱) / S5(创新)
- 自定义: `student_profiles.custom.json`覆盖默认值

### 日志规范
```
log/[context]/[profile]/
├── task_[ID]_[ts]_runcard.txt    # API请求响应
├── task_[ID]_[ts]_dialogue.txt   # 对话记录（人可读）
└── task_[ID]_[ts]_dialogue.json  # JSON导出（用于回放）
```

### API调用顺序（强制）
```python
query_script_step_list(task_id)  # 1. 获取步骤列表
run_card(task_id, step_id)       # 2. 初始化步骤
chat(user_answer)                # 3. 循环对话
# 若返回 needSkipStep=true → 自动调用run_card进入下一步
```

---

## ANTI-PATTERNS

| 禁止 | 正确做法 |
|------|----------|
| 硬编码`TASK_ID`或凭证 | 使用`.env`环境变量 |
| 使用英文TTS(`en-US-GuyNeural`)播报中文 | 改用`zh-CN-XiaoxiaoNeural` |
| LLM评测输出非JSON内容 | 强制JSON-only，禁止额外文本 |
| 评测时直接复制示例值 | 示例仅供格式参考，必须独立评判 |
| 省略`run_card`直接`chat` | 必须按顺序初始化 |
| 对话超过50字（AI学生） | 限制回答在50字内，确认/选择题直接答"是"/"1" |
| 主观判断状态转换 | 必须用封闭式确认问题（"明白了吗？"→"是"） |

---

## COMMANDS

```bash
# 工作流测试
python auto_script_train.py              # 交互式选择模式
python auto_script_train_5characters.py  # 5角色并发

# 语音训练测试
python auto_audio_train.py

# 构建任务
python skill_training_build/create_task_from_markdown.py

# 作业批改
cd homework_review && python homework_reviewer_v2.py

# 对话评测
python -m evaluation -t doc.docx -d log.json -v
python -m evaluation -t doc.docx -D ./logs/ -O ./reports/ --workers 3

# 依赖安装
pip install -r requirements.txt
```

---

## NOTES

1. **半交互模式快捷键**: Enter=AI生成, `continue`=全自动, `continue N`=自动到N轮后暂停
2. **回放模式**: 编辑`dialogue.txt/json`后重新运行，自动匹配相似问题复用答案
3. **并发测试**: 5角色脚本输入`1,3,5`可同时跑S1/S3/S5
4. **Skills工作流**: 引用文档`@路径/任务.md` → 自动生成基础配置/评价标准/剧本/对话流程
5. **评测维度**: 目标达成度/流程遵循度(规则) + 交互体验性/幻觉与边界/教学策略(LLM)
6. **所有中文**: 开发交流/思考/任务清单必须使用中文

---

## CHILD AGENTS.md

- [skill_training_build/AGENTS.md](./skill_training_build/AGENTS.md) - Markdown→平台构建
- [homework_review/AGENTS.md](./homework_review/AGENTS.md) - 作业批改
- [evaluation/AGENTS.md](./evaluation/AGENTS.md) - 对话质量评测
- [.claude/skills/AGENTS.md](./.claude/skills/AGENTS.md) - Claude Code技能系统
