# Pro 数字人资源解析

## 字段边界

可作为固定候选写入配置，但导入前仍需验证：

- `voiceNid`、`voiceType`
- 平台预置 `avatarNid`

必须运行时解析，不写死到跨任务剧本：

- `customDigitalHuman`：与当前用户及声音、形象组合相关
- `roleNid`：由目标任务创建或查询得到
- `skillNid`：由目标任务创建或查询得到

固定候选只能取自 `resource_catalog.json`。目录没有合适资源时，把资源 ID 写成 `运行时解析`，同时写清选择条件和形象描述，禁止编造 ID。

## 默认生成策略

1. 根据角色年龄、性别、职业、表达气质和语言选择声音。
2. 根据角色年龄、性别、职业服装和场景选择形象。
3. 优先使用目录中语义匹配度最高且无明显冲突的声音、形象。
4. 无高置信匹配时保留 `运行时解析`，不要为了填满字段强配资源。
5. `数字人组合ID` 始终写 `运行时解析`。

## 可选实时核验

只有用户明确要求“核验当前账号资源”并且环境中已有合法凭证时才执行。不得在输出、日志或配置中写出凭证。

```text
POST /console/v1/get-current-user-detail
POST /ai-profile/ai_voice/list
POST /ai-profile/ai_avatar/getOwnerAvatar
POST /ai-profile/digital_human/owner/list
```

核验顺序：当前账号 → 声音 ID 是否存在 → 形象 ID 是否存在 → 是否已有相同名称、声音和形象组合的数字人。

本 Skill 默认只生成剧本，不调用创建、编辑、发布接口。
