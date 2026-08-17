export const meta = {
  name: 'training-batch-build',
  description: '批量生成能力训练的评价标准、训练剧本和背景图。传入任务文件夹名列表，三合一 pipeline。',
  phases: [
    { title: '评价标准' },
    { title: '训练剧本' },
    { title: '背景图' },
  ],
}

// ── 参数 ──────────────────────────────────────────────────
// args = {
//   tasks:  ['任务A', '任务B'],          // 必填，任务文件夹名
//   stages: ['rubric','script','bg'],    // 可选，默认全部
//   baseDir: 'skills_training_course/...', // 可选，有默认值
//   force:  false                        // 可选，true 忽略已有产物
// }

const DEFAULT_BASE = '/Users/zhangyichi/工作/能力训练/skills_training_course/临沂大学-单片机原理与应用'
const ROOT    = '/Users/zhangyichi/工作/能力训练'
const SKILLS  = ROOT + '/.claude/skills'
const BASEDIR = (args && args.baseDir) || DEFAULT_BASE
const TASKS   = (args && args.tasks)   || []
const STAGES  = new Set((args && args.stages) || ['rubric', 'script', 'bg'])
const FORCE   = !!(args && args.force)

if (!TASKS.length) {
  log('❌ args.tasks 为空，无需处理。')
  return { error: 'args.tasks is required and must be non-empty' }
}

log(`📋 任务: ${TASKS.join(', ')}`)
log(`📦 阶段: ${[...STAGES].join(' + ')}${FORCE ? ' [force]' : ''}`)

// ── Schema ────────────────────────────────────────────────
const RUBRIC_SCHEMA = {
  type: 'object',
  required: ['file', 'totalScore', 'items'],
  additionalProperties: false,
  properties: {
    file:       { type: 'string' },
    totalScore: { type: 'number' },
    items: {
      type: 'array',
      items: {
        type: 'object',
        required: ['name', 'score', 'subPoints'],
        additionalProperties: false,
        properties: {
          name:      { type: 'string' },
          score:     { type: 'number' },
          subPoints: { type: 'integer', description: '子得分点数量' },
        },
      },
    },
  },
}

const SCRIPT_SCHEMA = {
  type: 'object',
  required: ['file', 'validationPassed', 'stages', 'note'],
  additionalProperties: false,
  properties: {
    file:              { type: 'string' },
    validationPassed:  { type: 'boolean' },
    validationSummary: { type: 'string' },
    stages: {
      type: 'array',
      items: {
        type: 'object',
        required: ['num', 'name', 'templateType', 'jumpCondition'],
        additionalProperties: false,
        properties: {
          num:           { type: 'integer' },
          name:          { type: 'string' },
          templateType:  { type: 'string' },
          jumpCondition: { type: 'string' },
        },
      },
    },
    note: { type: 'string' },
  },
}

// ── Prompt 模板 ───────────────────────────────────────────
function rubricPrompt(t) {
  return `你是训练评价标准生成器。为实训任务「${t}」生成层级化评价标准。

【路径】
- 任务文档: ${BASEDIR}/${t}/实训任务文档.md
- 技能定义: ${SKILLS}/training-rubric-generator/SKILL.md

【步骤】
1. Read 上述任务文档和技能定义 SKILL.md。
2. 文档「四、实训评价标准」已有评分项表格（评分项/分值/考核内容，总分100分）。必须完整、准确提取，保留原始评分项名称、分值和总分100。
3. 按 SKILL.md「层级化得分点结构」，把每个主评分项拆为 3-5 个子得分点：每个子得分点有独立分值和详细、可被AI评判的评价要求。子得分点分值之和必须等于该主评分项分值。
4. 把结果写入 ${BASEDIR}/${t}/评价标准.md，格式严格遵循 SKILL.md 第四步模板。
5. 全程用中文。

${FORCE ? '' : '【增量检查】先 Read 评价标准.md，若文件已存在且格式完整，直接返回验证通过，不要重写文件。'}

完成后返回结构化结果（file=绝对路径，totalScore=100，items=各主评分项名称/分值/子得分点数量）。`
}

function scriptPrompt(t) {
  return `你是提示词内容专家。为实训任务「${t}」生成完整的训练剧本配置。全程自主完成，不要中途停下等待用户确认。

【路径】
- 工作目录(cwd): ${ROOT}
- 任务文档: ${BASEDIR}/${t}/实训任务文档.md
- 技能定义: ${SKILLS}/training-prompt-expert/SKILL.md
- 模板目录: ${SKILLS}/training-prompt-expert/references/templates/
- 示例目录: ${SKILLS}/training-prompt-expert/references/examples/

【步骤】
1. Read 任务文档、SKILL.md、template_renwushu.md。
2. 做模块拆分与类型识别。「智能体提问、学生作答有对错之分」→循序过关型；「总结/验收」→总结型；「智能体被动应答」→模拟人物型。
3. 对用到的每种模板 Read 对应模板文件和 1-2 个最匹配示例，严格按模板结构生成。
4. 写入 ${BASEDIR}/${t}/训练剧本配置.md，格式严格遵循 SKILL.md 第三步。
5. 运行验证: cd ${ROOT} && python .claude/skills/training-prompt-expert/scripts/validate_markdown.py "${BASEDIR}/${t}/训练剧本配置.md" --strict
6. 若验证报 ❌ 错误，【只修改训练剧本配置.md】反复修到通过。禁止修改任何校验脚本。

【硬性约束】
- transitionPrompt 直接使用 SKILL.md 第三步固定模板原样填入，不要自由发挥。
- 跳转条件宁松勿严：每关 ≤3-4 个核心判定点，达到即放行。
- 跳转分支命中时【只输出纯跳转关键词】，无前后缀、无标点。
- 提示词内【严禁三反引号】，结构化示例用单反引号包裹。
- 每个阶段必须保留 **背景图**: (选填) 字段。

${FORCE ? '' : '【增量检查】先 Read 训练剧本配置.md，若文件已存在且 validate_markdown.py --strict 通过，直接返回验证结果，不要重写文件。'}

全程用中文。完成后返回结构化结果：file=绝对路径，validationPassed，stages（各阶段编号/名称/模板类型/跳转判定点），note。`
}

function bgPrompt(t) {
  return `为实训任务「${t}」的训练剧本各阶段生成背景图。

用 Bash 运行下面的命令（会真实生成付费图片，timeout 设为 600000）：

cd ${ROOT} && python .claude/skills/training-background-generator/scripts/generate_background.py "${BASEDIR}/${t}/训练剧本配置.md"

【说明】
- 脚本自动解析剧本、调用 LLM 生成提示词、调用 Doubao Seedream 生成 16:9 背景图、下载保存到 backgrounds/ 目录、回填路径到剧本。
- 不要修改任何脚本或剧本文件。
- 命令完成后从标准输出读取：成功图片数、保存目录、是否有失败阶段及原因。
- 如果输出中脚本报错（如环境变量缺失），原样报告错误，不要尝试自行修复。`
}

// ── 辅助：构建 agent thunk（含增量检查）──────────────────
function makeRubricThunk(t) {
  return () => agent(rubricPrompt(t), {
    label: `评价标准:${t}`, phase: '评价标准', schema: RUBRIC_SCHEMA,
  })
}

function makeScriptThunk(t) {
  return () => agent(scriptPrompt(t), {
    label: `训练剧本:${t}`, phase: '训练剧本', schema: SCRIPT_SCHEMA,
  })
}

function makeBgThunk(t) {
  return () => agent(bgPrompt(t), {
    label: `背景图:${t}`, phase: '背景图',
  })
}

// ── 执行 ──────────────────────────────────────────────────
const results = {}

// Phase 1: 评价标准
if (STAGES.has('rubric')) {
  log(`📝 生成评价标准 (${TASKS.length} 个任务)`)
  phase('评价标准')
  const r = await parallel(TASKS.map(makeRubricThunk))
  results.rubrics = TASKS.map((t, i) => ({ task: t, result: r[i] }))
  log(`✅ 评价标准完成: ${r.filter(Boolean).length}/${TASKS.length}`)
} else {
  results.rubrics = 'skipped'
}

// Phase 2: 训练剧本
if (STAGES.has('script')) {
  log(`📝 生成训练剧本 (${TASKS.length} 个任务)`)
  phase('训练剧本')
  const s = await parallel(TASKS.map(makeScriptThunk))
  results.scripts = TASKS.map((t, i) => ({ task: t, result: s[i] }))

  // ── 屏障：验证所有剧本通过后才能进入背景图 ──
  const failedScripts = results.scripts.filter(x => x.result && !x.result.validationPassed)
  if (STAGES.has('bg') && failedScripts.length > 0) {
    log(`❌ ${failedScripts.length} 个剧本验证未通过，背景图阶段中止`)
    log(`   失败任务: ${failedScripts.map(x => x.task).join(', ')}`)
    results.bgBlocked = true
    return results
  }
  log(`✅ 训练剧本完成: ${s.filter(Boolean).length}/${TASKS.length}`)
} else {
  results.scripts = 'skipped'
}

// Phase 3: 背景图
if (STAGES.has('bg') && !results.bgBlocked) {
  log(`🖼️  生成背景图 (${TASKS.length} 个任务，付费 API)`)
  phase('背景图')
  const b = await parallel(TASKS.map(makeBgThunk))
  results.backgrounds = TASKS.map((t, i) => ({ task: t, result: b[i] }))
  log(`✅ 背景图完成: ${b.filter(Boolean).length}/${TASKS.length}`)
} else {
  results.backgrounds = results.bgBlocked ? 'blocked' : 'skipped'
}

return results
