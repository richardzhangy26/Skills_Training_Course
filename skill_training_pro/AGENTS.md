# 能力训练 Pro 导入

## 入口

通用 Markdown 导入使用 `python -m skill_training_pro.deploy_pro_from_markdown`。`deploy_thermodynamics_pro.py`、`configure_xray_pro_roles.py` 和 `create_xray_pro_stage_cards.py` 是专项脚本或底层适配层；只有处理其原始课程时才直接运行。

## 导入契约

1. 任务必须从 `/ability-training-pro/create` 创建，平台任务 ID 必须以 `PRO` 开头。普通能力训练 ID 在预检阶段直接拒绝。
2. 教学内容以 `<能力名称>-Pro配置.md` 为单一来源；账号相关资源放在独立的资源映射 JSON，不把 `roleNid`、`customDigitalHuman` 等账号 ID 回写到跨任务剧本。
   资源映射结构参考 `pro_resource_map.example.json`。
3. 资源映射必须提供：
   - `members`：仅为需要消歧的成员指定 `customDigitalHuman`，也可覆盖 `voiceNid`、`voiceType`、`avatarNid`。
   - `stageBackgrounds`：按阶段名称或从 1 开始的序号提供 `fileId` + `fileUrl`，或本地绝对 `path`。
   - `scoreItems`：至少一项，每项包含 `name`、正数 `score`、`requirement`，`description` 可选。
   - `cover`：可选；省略时使用第一阶段背景。
   - `entranceVoice`：必需，包含 `voiceNid`、`voiceType`、`speed`。
4. `运行时解析` 必须在写入前解析完成。只有一个同名数字人时可自动采用；存在多个同名资源时，通过资源映射指定 `customDigitalHuman`，不得按列表顺序猜测。
5. 优先复用 Pro 编辑器自动生成的空白“未命名阶段”。只自动移除无描述、无提示词、无背景的剩余占位卡；含内容的未命名阶段作为冲突停止导入。
6. 平台评价标准是 Pro 保存与发布的必需配置。阶段提示词里的复盘分数不能替代 `/score-items/edit` 的平台评分项。

## 执行顺序

```bash
# 1. 预检：无平台写入
python -m skill_training_pro.deploy_pro_from_markdown \
  --config '<配置.md>' \
  --resource-map '<资源映射.json>' \
  --course-id '<COURSE_ID>' \
  --library-id '<LIBRARY_ID>' \
  --term '<TERM>' \
  --task-id '<可选的PRO任务ID>'

# 2. 写入未发布草稿
python -m skill_training_pro.deploy_pro_from_markdown <同上参数> --apply

# 3. 只有用户明确要求发布时
python -m skill_training_pro.deploy_pro_from_markdown <同上参数> --apply --publish
```

## 完成标准

导入完成必须回查：任务 ID 为 Pro 类型、任务入口指向第一张卡片、成员提示词与技能挂载一致、全部阶段提示词含有效角色 ID、背景存在、无多余占位卡、平台评分项与资源映射一致。发布状态必须符合本次命令；没有 `--publish` 时保持草稿。
