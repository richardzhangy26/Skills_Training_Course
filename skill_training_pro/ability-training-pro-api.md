# 能力训练 Pro 接口文档

> 最后核对：2026-07-22  
> 主站：`https://hike-teaching-center.polymas.com`  
> API Host：`https://cloudapi.polymas.com`

## 1. 文档范围与证据等级

本文覆盖从“省区账号定位课程”到“创建 Pro 任务、成员、数字人、步骤并运行测试”的完整接口链。普通能力训练旧版接口单独列在兼容章节，不能与 Pro 写入接口混用。

证据等级：

| 标记 | 含义 |
| --- | --- |
| **实测** | 2026-07-22 在 Bit Chrome 配置下通过 Network/CDP 或接口请求确认，HTTP 200 |
| **前端确认** | 当前线上前端 JS 包中存在明确路径、方法和组装请求体的代码 |
| **HAR 确认** | `能力训练pro_har.json` 中存在真实 WebSocket 握手或消息 |
| **待实测** | 路径已确认，但本次没有主动触发写操作；响应字段仍可能随服务端版本变化 |

这是一份面向当前线上前端版本的逆向接口说明，不是服务端 OpenAPI。调用方必须容忍新增字段，并以 `code/success` 判断业务结果。

## 2. 通用约定

### 2.1 鉴权

REST 请求通常需要：

```http
Authorization: ${AUTHORIZATION}
Cookie: ${COOKIE}
Content-Type: application/json; charset=utf-8
```

上传文件时不要手动设置 `Content-Type`，交给 HTTP 客户端生成 `multipart/form-data` boundary。

WebSocket 握手至少需要同一登录态的 Cookie；当前测试脚本同时发送 `Authorization`。不要记录或提交完整 Cookie、JWT、`Sec-WebSocket-Key`、临时 `secretStr`。

### 2.2 统一响应信封

```ts
interface PolymasResponse<T> {
  code: number | string;
  msg?: string | null;
  message?: string | null;
  data: T;
  currentTime?: number | string;
  time?: string | null;
  traceId?: string | null;
  success?: boolean;
}
```

成功判断建议：

```python
def is_success(result):
    return result.get("code") in (200, "200") or result.get("success") is True
```

HTTP 200 不代表业务成功。课程中心曾出现 HTTP 200、响应体 `code=500` 的外围菜单请求。

### 2.3 ID 命名

| 字段 | 含义 |
| --- | --- |
| `courseId` | 智能体课程 ID，通常来自课程搜索结果或课程 URL |
| `trainTaskId` / `trainTaskNid` | Pro 任务 ID；不同接口命名不统一 |
| `taskId` | 查询任务/步骤/技能时使用的 Pro 任务 ID |
| `roleId` / `nid` | 全局成员 ID |
| `stepId` / `nid` | Pro 步骤 ID |
| `userNid` | 当前登录用户 ID |
| `schoolNid` | 当前登录租户/学校认证 ID |
| `schoolId` | 在不同课程搜索请求中可能是数字学校 ID，也可能实际传 `schoolNid`，不可只按字段名判断 |
| `libraryFolderId` / `libraryId` | 课程资源库目录 ID |

## 3. 接口总览

### 3.1 账号、省区与课程

| 方法 | 路径 | 用途 | 证据 |
| --- | --- | --- | --- |
| POST | `/console/v1/get-current-user-detail` | 当前用户、省区账号、租户学校信息 | 实测 |
| GET | `/oauth/token/getIdentity` | 当前身份、账号编码、`schoolNid` | 实测 |
| GET | `/user/user/get-current-user-identity` | 当前身份权限列表 | 实测 |
| GET | `/teachingCenterAi/user/getLoginUserInfo` | 教学中心登录用户摘要 | 实测 |
| GET | `/course-search/course/search/history` | 最近课程搜索词 | 实测 |
| POST | `/course-search/course/search/suggest` | 课程名搜索建议 | 实测 |
| POST | `/course-search/course/search` | 分页查询课程和课程 ID | 实测 |
| GET | `/teachingCenterAi/course/queryIdentity` | 当前账号的课程身份能力 | 实测 |

### 3.2 Pro 任务、成员、技能与步骤

| 方法 | 路径 | 用途 | 证据 |
| --- | --- | --- | --- |
| POST | `/ai-platform/ability-train/tasks/create` | 创建 Pro 任务 | 前端确认 |
| POST | `/ai-platform/ability-train/tasks/edit` | 更新 Pro 任务基础配置 | 前端确认 |
| GET | `/ai-platform/ability-train/tasks/detail` | 查询 Pro 任务详情 | 实测 |
| POST | `/ai-platform/ability-train/tasks/publish` | 发布任务到课程 | 前端确认 |
| POST | `/ai-platform/ability-train/progress/unfinished` | 查询/恢复未完成进度 | 前端确认 |
| POST | `/ai-platform/ability-train/memory/list` | 查询训练记忆 | 前端确认 |
| GET | `/ai-platform/ability-train/global-roles/list` | 查询全局成员，含系统角色 | 实测 |
| GET | `/ai-platform/ability-train/global-roles/detail` | 查询单个成员完整配置 | 实测 |
| POST | `/ai-platform/ability-train/global-roles/create` | 创建成员 | 前端确认 |
| POST | `/ai-platform/ability-train/global-roles/edit` | 更新成员 | 前端确认 |
| POST | `/ai-platform/ability-train/global-roles/remove` | 删除成员 | 前端确认 |
| GET | `/ai-platform/ability-train/skills/types` | 查询技能类型 | 前端确认 |
| GET | `/ai-platform/ability-train/skills/list` | 查询任务技能 | 实测 |
| GET | `/ai-platform/ability-train/skills/detail` | 查询技能详情 | 前端确认 |
| POST | `/ai-platform/ability-train/skills/create` | 创建技能 | 前端确认 |
| POST | `/ai-platform/ability-train/skills/edit` | 更新技能 | 前端确认 |
| GET | `/ai-platform/ability-train/steps/list` | 查询所有步骤 | 实测 |
| POST | `/ai-platform/ability-train/steps/create` | 创建步骤 | 前端确认 |
| POST | `/ai-platform/ability-train/steps/edit` | 更新步骤和位置 | 前端确认 |
| POST | `/ai-platform/ability-train/steps/remove` | 删除步骤 | 前端确认 |

当前 Pro API 模块没有发现 `skills/remove`，也没有旧版那种独立 `step-flow` CRUD。

### 3.3 模型、声音、数字人与资源

| 方法 | 路径 | 用途 | 证据 |
| --- | --- | --- | --- |
| POST | `/ai-tools/llm/model/query` | 查询可用模型 | 前端确认 |
| POST | `/ai-profile/ai_voice/list` | 查询当前可选声音 | 前端确认、脚本已使用 |
| POST | `/ai-profile/digital_human/owner/list` | 查询已创建数字人 | 前端确认、脚本已使用 |
| POST | `/ai-profile/ai_avatar/getOwnerAvatar` | 查询可选/已上传形象 | 前端确认 |
| POST | `/ai-profile/ai_avatar/saveAndSyncResource` | 把上传图片同步成形象资源 | 前端确认、脚本已使用 |
| POST | `/ai-profile/digital_human/custom/addAndSyncResource` | 用声音和形象创建数字人 | 前端确认、脚本已使用 |
| POST | `/ai-profile/digital_human/custom/delete` | 删除可删除的自定义数字人 | 前端确认 |
| POST | `/basic-resource/file/upload` | 上传本地图片/媒体 | 前端确认、脚本已使用 |
| POST | `/ai-tools/abilityTrain/queryEnvSoundList` | 查询环境音 | 前端确认 |
| POST | `/ai-platform/voiceprint/register` | 注册声纹 | 前端确认、待实测 |

### 3.4 小测与题库

| 方法 | 路径 | 用途 | 证据 |
| --- | --- | --- | --- |
| POST | `/ai-platform/ability-train/quiz-records/create` | 保存一次小测作答记录 | 前端确认 |
| GET | `/ai-platform/ability-train/quiz-paper/user-answer/get` | 查询用户小测答案/得分 | 前端确认 |
| GET | `/question-base-platform/folder/rootFolderId` | 获取课程题库根目录 | 前端确认 |
| GET | `/question-base-platform/folder/byBusiness` | 获取个人题库目录 | 前端确认 |
| POST | `/question-base-platform/paper/library/save` | 创建试卷方案 | 前端确认 |
| GET | `/question-base-platform/paper/library/detail` | 查询试卷方案详情 | 前端确认 |

### 3.5 运行时

| 协议 | 地址 | 用途 | 证据 |
| --- | --- | --- | --- |
| WebSocket | `/ai-platform/ws/trainV2` | Pro 多角色训练运行时 | HAR 确认、脚本已验证 |

## 4. 省区、学校与课程定位

### 4.1 获取当前用户和省区

```http
POST /console/v1/get-current-user-detail
Content-Type: application/json

{}
```

核心响应：

```ts
interface CurrentUserDetail {
  userNid: string;
  realName: string;
  nickName?: string;
  schoolCertificationNid: string;
  roleNid?: string;
  schoolInfo: {
    id: number;
    nid: string;       // schoolNid
    schoolId: string;  // 数字学校 ID
    schoolName: string;
  };
}
```

本次实测中，`realName` 是“云南省区”，`schoolInfo.schoolName` 是“Polymas实验室”。因此：

- `realName/nickName` 可用于校验当前登录的是哪个省区账号。
- `schoolInfo.schoolName` 是当前平台租户，不是课程合作学校。
- 要处理四川省课程，应先切换到四川省区账号，再用该接口确认 `realName`，不能只给课程搜索接口增加一个“province=四川”的猜测参数。

辅助身份接口：

```http
GET /oauth/token/getIdentity
```

响应中可获取 `userNid`、`schoolNid`、`userCode` 和 `realName`。自动化主流程优先使用 `get-current-user-detail`，因为它同时给出数字 `schoolId` 与 `schoolNid`。

### 4.2 获取课程搜索建议

```http
POST /course-search/course/search/suggest
```

```json
{
  "keyword": "通信原理",
  "schoolId": "15257"
}
```

响应 `data` 是课程名字符串数组。这里实测传的是当前用户 `schoolInfo.schoolId` 的数字字符串。

### 4.3 分页查询课程

课程中心首次加载实测请求：

```http
POST /course-search/course/search
```

```json
{
  "page": 1,
  "size": 100,
  "schoolId": "15257",
  "courseTypes": ["agent", "hike_ai", "ai_map", "graph_kg"]
}
```

输入关键词后的实测请求：

```json
{
  "keyword": "通信原理",
  "term": "",
  "schoolId": "c6EL6hPNdS",
  "type": 1,
  "page": 1,
  "size": 24
}
```

注意同一路径的两个页面调用形态不同：首次列表使用数字 `schoolId`，关键词搜索实测使用了 `schoolNid`。自动化应从当前用户响应同时保留这两个值，并按已验证的调用形态传递。

核心响应：

```ts
interface CourseSearchData {
  list: Array<{
    course: {
      courseId: string;
      courseName: string;
      courseType: string;
      term: number;
      termName: string;
      coverImage?: string;
      isArchived: boolean;
      schoolId: string;
      teacher?: { teacherId: string; teacherName: string };
      teachers?: Array<{ teacherId: string; teacherName: string }>;
      lastUpdateTime?: string;
    };
    highlights?: Record<string, string[]>;
  }>;
  page: number;
  size: number;
  total: number | string;
  totalPage: number;
  last: boolean;
}
```

学校识别限制：

- 当前返回结构没有独立的合作学校名称字段。
- `course.schoolId` 实测仍是当前租户 `schoolNid`，不能当作“西南林业大学”等合作学校 ID。
- 合作学校名通常拼在 `courseName` 尾部。应先对课程名做精确/包含匹配，再用本地学校表识别学校。
- 搜索是模糊匹配，输入“通信原理”也可能返回其他含“原理”的课程；不能直接取第一条。

推荐匹配顺序：完整平台课程名精确匹配 > 课程关键词与学校名同时命中 > 仅课程关键词命中 > 人工确认。

### 4.4 搜索历史

```http
GET /course-search/course/search/history
```

响应 `data` 为最近搜索词数组。它适合 UI 提示，不应作为学校或课程的权威数据源。

### 4.5 当前未发现的省区接口

本次没有发现“列出全部省区”“学校到省区映射”“根据四川省直接查询所有合作学校”的平台接口。现有 `training-auto-login` 使用本地 `school_province_map.json` 选择省区账号，再通过课程搜索接口取课程 ID。这仍是当前最可靠的链路。

## 5. Pro 任务接口

### 5.1 创建任务

```http
POST /ai-platform/ability-train/tasks/create
```

```json
{
  "trainTaskName": "任务名称",
  "description": "任务描述",
  "trainTaskCover": null,
  "trainTime": null,
  "firstStepId": null,
  "publishStatus": null,
  "voiceUrl": null,
  "openSubtitle": null,
  "openVideo": null,
  "communicateMethod": "SELF",
  "entranceVoiceType": null,
  "entranceVoiceSpeed": null,
  "entranceVoiceNid": null
}
```

前端把成功响应 `data` 当作新任务 ID。

### 5.2 更新任务

```http
POST /ai-platform/ability-train/tasks/edit
```

请求体与创建相同，增加：

```json
{
  "trainTaskId": "${TASK_ID}"
}
```

设置初始步骤也是调用此接口更新 `firstStepId`，不是创建一条流程边。

### 5.3 查询任务

```http
GET /ai-platform/ability-train/tasks/detail?taskId=${TASK_ID}
```

关键字段：`trainTaskId`、`trainTaskName`、`description`、`firstStepId`、`publishStatus`。`supervisorPrompt` 可能为 `null`，不能因此判断任务无提示词。

### 5.4 发布任务

```http
POST /ai-platform/ability-train/tasks/publish
```

```json
{
  "courseId": "${COURSE_ID}",
  "taskId": "${TASK_ID}",
  "libraryFolderId": "${LIBRARY_FOLDER_ID}"
}
```

发布是有外部状态变化的写操作。构建脚本应把“保存草稿”和“发布”拆成两个明确动作。

### 5.5 未完成进度与记忆

```http
POST /ai-platform/ability-train/progress/unfinished
POST /ai-platform/ability-train/memory/list
```

当前 API 模块确认了路径，但编辑器页面未暴露稳定请求体。本次不建议把猜测字段写入自动构建脚本；应在真实恢复训练/查看记忆时补抓 Network。

## 6. 全局成员接口

### 6.1 列表与详情

```http
GET /ai-platform/ability-train/global-roles/list?trainTaskId=${TASK_ID}&needSystemRole=true
GET /ai-platform/ability-train/global-roles/detail?roleId=${ROLE_ID}
```

`needSystemRole=true` 会包含 `nid="system"` 的主理人角色。成员配置 UI 会过滤系统角色，但训练上下文聚合不能丢掉它。

### 6.2 创建与更新

```http
POST /ai-platform/ability-train/global-roles/create
POST /ai-platform/ability-train/global-roles/edit
```

```json
{
  "trainTaskNid": "${TASK_ID}",
  "nickname": "陈工",
  "roleName": "工程师",
  "modelCode": "Doubao-Seed-2.0-pro",
  "prompt": "人物基础提示词",
  "voiceNid": "${VOICE_NID}",
  "voiceType": "${VOICE_TYPE}",
  "voiceSpeed": 1,
  "avatarNid": "${AVATAR_NID}",
  "customDigitalHuman": "${CUSTOM_NID}",
  "description": "角色简介",
  "skills": "skill-id-1,skill-id-2",
  "searchEngine": 0,
  "knowledgeSearch": 0,
  "knowledgeFileIds": ["file-id-1"]
}
```

更新时增加 `nid`。前端必填校验：`nickname`、`roleName`、`modelCode`、`prompt`、`description`、`voiceNid`。

字段关系：

| 字段 | 用途 |
| --- | --- |
| `voiceNid` | 声音资源 ID；当前前端缺失时会回退到 `avatarNid` |
| `voiceType` | TTS 音色参数，如 `zh_male_..._bigtts` |
| `avatarNid` | 形象资源 ID |
| `customDigitalHuman` | “声音 + 形象”组合后的自定义数字人 ID |
| `skills` | 写入时是逗号分隔的技能 ID；读取时详情通常返回 `skillList` |
| `knowledgeFileIds` | 写入时为 ID 数组；详情响应可能返回带名称和 URL 的对象数组 |

### 6.3 删除成员

```http
POST /ai-platform/ability-train/global-roles/remove?roleId=${ROLE_ID}
```

删除前应扫描所有步骤 `llmPrompt` 中的 `<role>${ROLE_ID}</role>`，否则会留下悬空引用。

### 6.4 提示词职责

成员 `prompt` 只负责身份、语气、知识边界和稳定行为，不应塞入具体阶段流程。阶段发生什么写在步骤 `llmPrompt`；`system_prompt.md` 在运行时把阶段剧本规划为 `subtasks`；卡片切换由平台外层完成。

2026-07-22 当前 Bit 任务实测发现：某成员描述完整，但 `prompt` 实际只有字符串 `"1"`。因此导入回查必须检查提示词最小长度和内容质量，不能只判断非空。

## 7. 声音、形象与数字人

### 7.1 查询声音

```http
POST /ai-profile/ai_voice/list
```

```json
{
  "voiceTemplateType": "ONLINE_DOUBAO",
  "courseId": "${COURSE_ID}"
}
```

`courseId` 可选。选择声音时至少保留：`nid`、声音显示名、`voiceType/voiceParam/bigModelVoiceParam`、试听 URL、性别/风格标签。不要继续使用旧版硬编码默认音色作为唯一策略。

### 7.2 查询可用数字人

```http
POST /ai-profile/digital_human/owner/list
```

```json
{
  "userNid": "${USER_NID}",
  "appCode": "${APP_CODE}",
  "courseId": "${COURSE_ID}",
  "type": "NORMAL",
  "sort": 2,
  "libraryFolderId": "${LIBRARY_FOLDER_ID}"
}
```

除 `userNid`、`sort` 外，其余字段按上下文可选。`type` 当前前端只接受 `NORMAL` 或 `RTC`。

### 7.3 查询形象库

```http
POST /ai-profile/ai_avatar/getOwnerAvatar
```

请求体可包含 `userNid`、`appCode`、`courseId`、`libraryFolderId`、`sort` 和 `type`。前端会把返回值规范为 `nid/avatar/avatarDynamic/recordUrl/recordDynamicUrl`。

### 7.4 上传本地图片

```http
POST /basic-resource/file/upload?hidden=false
Content-Type: multipart/form-data
```

表单：

| 字段 | 示例 |
| --- | --- |
| `file` | 图片二进制 |
| `identifyCode` | UUID |
| `name` | 原始文件名 |
| `chunk` | `0` |
| `chunks` | `1` |
| `size` | 文件字节数 |

成功响应关键字段：`data.fileId`、`data.ossUrl`。`hidden` 在不同上传入口可省略，不要固定假设为 `false`。

### 7.5 同步图片为形象资源

```http
POST /ai-profile/ai_avatar/saveAndSyncResource
```

```json
{
  "userNid": "${USER_NID}",
  "appCode": "${APP_CODE}",
  "avatarUrl": "${OSS_URL}",
  "avatarDynamicUrl": "${OSS_URL}",
  "avatarNid": "${OLD_AVATAR_NID}",
  "sync": false
}
```

`appCode`、旧 `avatarNid`、录制资源字段可选。成功后优先取 `data.avatarNid`，其次 `data.nid`。

### 7.6 创建数字人

```http
POST /ai-profile/digital_human/custom/addAndSyncResource
```

普通图片数字人：

```json
{
  "userNid": "${USER_NID}",
  "appCode": "${APP_CODE}",
  "type": "NORMAL",
  "voiceNid": "${VOICE_NID}",
  "avatarNid": "${AVATAR_NID}",
  "digitalHumanName": "陈工"
}
```

RTC 数字人把 `avatarNid` 替换为 `digitalHumanNid`，并设置 `type="RTC"`。成功响应优先取 `data.customNid`。

### 7.7 删除自定义数字人

```http
POST /ai-profile/digital_human/custom/delete
```

```json
{
  "customNid": "${CUSTOM_NID}",
  "userNid": "${USER_NID}",
  "appCode": "${APP_CODE}"
}
```

仅删除返回项中明确标记 `canDeleteFlag=true` 的自定义资源。

## 8. 技能接口

### 8.1 查询

```http
GET /ai-platform/ability-train/skills/types
GET /ai-platform/ability-train/skills/list?taskId=${TASK_ID}
GET /ai-platform/ability-train/skills/detail?skillId=${SKILL_ID}
```

技能列表主要字段：`nid`、`typeNid/typeCode/type`、`name`、`packageName`、`description`、`businessConfig`、`skillDetailVO`。`content` 为空不代表技能无效；角色的真实挂载关系应看 `global-roles/*` 返回的 `skillList`。

### 8.2 创建与更新

```http
POST /ai-platform/ability-train/skills/create
POST /ai-platform/ability-train/skills/edit
```

```json
{
  "trainTaskNid": "${TASK_ID}",
  "typeNid": "${SKILL_TYPE_NID}",
  "name": "项目考点出题",
  "packageName": "项目考点出题",
  "description": "触发条件和用途",
  "businessConfig": null,
  "instruction": "技能指令"
}
```

更新增加 `nid`。非 `custom/review` 类型通常要求 `businessConfig`；前端当前没有暴露删除技能接口。

## 9. 步骤接口

### 9.1 查询与删除

```http
GET /ai-platform/ability-train/steps/list?taskId=${TASK_ID}
POST /ai-platform/ability-train/steps/remove?stepId=${STEP_ID}
```

步骤查询会返回顶层字段和嵌套 `extConfig`。读取时应把 `extConfig` 展平作为兼容回退，但写入时仍按当前请求结构嵌套。

### 9.2 创建与更新

```http
POST /ai-platform/ability-train/steps/create
POST /ai-platform/ability-train/steps/edit
```

```json
{
  "trainTaskNid": "${TASK_ID}",
  "stepName": "绪论与研发背景问答",
  "description": "阶段描述",
  "modelCode": "Doubao-Seed-2.0-pro",
  "llmPrompt": "<role>member-id</role> ... <role>user</role>",
  "skills": "skill-id-1,skill-id-2",
  "positionX": "570",
  "positionY": "100",
  "voiceNid": null,
  "voiceSpeed": null,
  "voiceType": null,
  "avatarNid": null,
  "customDigitalHuman": null,
  "timeLimit": -1,
  "useWhiteboard": 0,
  "isSkipStep": 0,
  "isNeedBegin": 1,
  "isTransition": 0,
  "flowHideSubtitle": 0,
  "extConfig": {
    "userRoleName": "单片机课程设计实训学生",
    "userNameType": 2,
    "userAssignName": "同学",
    "userDescription": "用户在本阶段的角色、目标与边界",
    "bgMediaType": 1,
    "bgMedia": "${BACKGROUND_URL}",
    "bgMediaId": "${BACKGROUND_FILE_ID}",
    "bgMediaVolume": 80,
    "bgMediaTheme": null,
    "bgMusicCategory": null,
    "bgMusicId": null,
    "bgMusic": null,
    "bgMusicVolume": null,
    "transitionBgMediaType": null,
    "transitionBgMedia": null,
    "transitionBgMediaId": null,
    "transitionBgMediaVolume": null,
    "transitionBgMediaTheme": null,
    "transitionBgMediaFullScreen": null,
    "transitionBgMusicCategory": null,
    "transitionBgMusicId": null,
    "transitionBgMusic": null,
    "transitionBgMusicVolume": null,
    "flowAsideContent": null,
    "flowUseAside": null,
    "flowAsideVoiceNid": null,
    "flowAsideVoiceType": null,
    "flowAsideVoiceAvatarNid": null,
    "flowAsideVoiceCustomDigitalHuman": null,
    "flowAsideVoiceSpeed": null,
    "flowAsideVoiceVolume": null
  }
}
```

更新增加 `nid`。前端对拖拽位置保存做了约 500ms 防抖，并支持取消上一条步骤更新请求。

### 9.3 用户角色字段

| 字段 | 规则 |
| --- | --- |
| `userRoleName` | 用户扮演的角色名称，必填 |
| `userNameType=1` | 使用平台用户名，此时 `userAssignName=null` |
| `userNameType=2` | 使用指定名称，`userAssignName` 必填 |
| `userDescription` | 用户身份、目标、已知信息和禁止越界内容，必填 |

### 9.4 成员提示词注入

持久化格式不是普通 `@名字`，而是：

```text
<role>user</role>
<role>Fauh4BgVIb</role>
```

UI 中选择 `@用户` 或某成员后，编辑器才会写入对应 `<role>ID</role>`。直接在 Markdown 中写 `@林医生` 不会自动创建成员，也不会变成角色引用。

导入前校验：

1. `llmPrompt` 至少包含一个 `<role>`。
2. 每个非 `user/system` ID 都存在于 `global-roles/list`。
3. 需要发言的人物不能只以普通 `@名称` 文本出现。
4. 用户参与应拆为“非用户角色发出引导并等待”与“`roleId=user` 承接回答”两个子任务。

### 9.5 步骤必填校验

当前前端要求：`stepName`、`description`、用户角色四项、`modelCode`、`llmPrompt`、`timeLimit`、背景画面。开启转场后必须配置转场画面；开启旁白后必须配置旁白声音和文本。

### 9.6 Pro 卡片切换不是旧版流程边

当前 Pro 前端只保存步骤节点，没有发现 `/flows` 或 `createScriptStepFlow`。初始卡片由任务 `firstStepId` 指定；卡片内由 `system_prompt.md` 生成 `subtasks`；外层运行时在阶段结束后发送 `nextStep`。不要把旧版 `conditionRule/flowCondition/NEXT_TO_STAGE` 写进 Pro 步骤提示词。

## 10. 小测与题库接口

### 10.1 保存小测记录

```http
POST /ai-platform/ability-train/quiz-records/create
```

```json
{
  "paperInfo": {},
  "trainTaskNid": "${TASK_ID}",
  "bizNid": "${STEP_ID}",
  "sessionId": "${SESSION_ID}",
  "quizId": "${QUIZ_ID}",
  "paperId": "${PAPER_ID}"
}
```

### 10.2 查询小测答案

```http
GET /ai-platform/ability-train/quiz-paper/user-answer/get?trainTaskNid=${TASK_ID}&quizId=${QUIZ_ID}&paperId=${PAPER_ID}
```

### 10.3 创建/复用试卷方案

课程题库：

```http
GET /question-base-platform/folder/rootFolderId?businessId=${COURSE_ID}
```

个人题库：

```http
GET /question-base-platform/folder/byBusiness?folderBusinessEnum=PERSONAL&businessId=${USER_ID}
```

新建方案：

```http
POST /question-base-platform/paper/library/save
```

```json
{
  "title": "未命名考试",
  "folderId": "${ROOT_FOLDER_ID}",
  "buildMode": "SELECT_QUESTION",
  "businessId": "${BUSINESS_ID}",
  "business": "${BUSINESS_TYPE}",
  "homeworkId": null,
  "eHomeworkId": null
}
```

如果已有 `paperId/schemeId`，前端直接复用，不重复创建。

## 11. 模型、环境音和声纹

```http
POST /ai-tools/llm/model/query
```

```json
{"scene": 0}
```

```http
POST /ai-tools/abilityTrain/queryEnvSoundList
```

```json
{"category": ""}
```

```http
POST /ai-platform/voiceprint/register
```

声纹接口当前只有路径得到前端确认，请在真正录入声纹时补抓上传字段、音频格式和返回 ID。

## 12. trainV2 WebSocket 协议

连接地址：

```text
wss://cloudapi.polymas.com/ai-platform/ws/trainV2
  ?taskId=${TASK_ID}
  &userId=${USER_NID}
  &sessionId=${SESSION_ID}
```

`sessionId` 由客户端生成并在一次运行中保持不变。当前网页依赖应用层心跳，不使用 WebSocket 协议级 ping。

客户端发送：

| 事件 | payload | 时机 |
| --- | --- | --- |
| `scriptStart` | 无 | 握手成功后立即发送 |
| `stepStart` | `{"stepId":"..."}` | 收到 `nextStep` 后 |
| `userTextInput` | `{"text":"..."}` | `selectRoleEnd.roleNid == "user"` 时 |
| `continueCurrentStep` | 无 | 每个角色完整回合后恰好一次 |
| `heartBeat` | `{}` | 每 30 秒 |

服务端关键事件：

| 事件 | 说明 |
| --- | --- |
| `connected` | 连接就绪，实测 `connectType=agentscope` |
| `nextStep` | 给出 `nextStepId` 和状态，客户端随后发 `stepStart` |
| `selectRoleStart` / `selectRoleEnd` | 服务端选择下一位发言角色 |
| `botAnswerStart` / `botAnswer` / `botAnswerEnd` | 智能体流式回答；业务记录以 `botAnswerEnd.payload.content` 为准 |
| `audioStart` / `audioEnd` | 音频播放边界 |
| `heartbeatAck` | 心跳确认 |
| `stepEnd` | 当前步骤结束标记 |
| `scriptEnd` | 整个剧本完成 |
| `error` | 运行错误，应终止或进入受控恢复 |

当 `roleNid="system"` 时，回答是主理人/教练点评，不是普通对话对象。每个 AI 角色必须等 `botAnswerEnd` 后再发 `continueCurrentStep`；过早发送会破坏回合顺序。

## 13. 推荐自动构建顺序

1. `get-current-user-detail` 校验省区账号，保留 `userNid/schoolId/schoolNid`。
2. `course/search` 用课程名和学校名定位唯一 `courseId`；模糊结果不能直接取第一条。
3. `tasks/create` 创建任务草稿。
4. 查询模型、声音、形象和已有数字人。
5. 本地图片依次执行：上传文件 -> 同步形象 -> 创建数字人。
6. 创建技能，记录返回的技能 ID。
7. 创建全局成员，把数字人、声音、形象和技能挂到成员。
8. 把剧本中的人物名解析成成员 ID，并生成 `<role>ID</role>`。
9. 创建步骤，写入用户角色、背景、阶段提示词和位置。
10. `tasks/edit` 设置 `firstStepId`。
11. 回查任务、成员、技能和步骤，执行引用完整性与最小长度校验。
12. 用户明确要求后才调用 `tasks/publish`。
13. 使用 `trainV2` WebSocket 跑真实对话测试。

建议自动构建返回清单：

```json
{
  "provinceAccount": "已验证",
  "courseId": "...",
  "taskId": "...",
  "roles": [{"nid": "...", "nickname": "...", "customDigitalHuman": "..."}],
  "skills": [{"nid": "...", "name": "..."}],
  "steps": [{"nid": "...", "stepName": "..."}],
  "firstStepId": "...",
  "published": false,
  "validationErrors": []
}
```

## 14. 旧版能力训练接口：只读兼容

以下属于普通能力训练，不是 Pro 写入协议：

```text
/teacher-course/abilityTrain/createConfiguration
/teacher-course/abilityTrain/queryConfiguration
/teacher-course/abilityTrain/editConfiguration
/teacher-course/abilityTrain/queryScoreItemList
/teacher-course/abilityTrain/createScoreItem
/teacher-course/abilityTrain/editScoreItem
/teacher-course/abilityTrain/delScoreItem
/teacher-course/abilityTrain/createScriptStep
/teacher-course/abilityTrain/editScriptStep
/teacher-course/abilityTrain/queryScriptStepList
/teacher-course/abilityTrain/delScriptStep
/teacher-course/abilityTrain/createScriptStepFlow
/teacher-course/abilityTrain/editScriptStepFlow
/teacher-course/abilityTrain/queryScriptStepFlowList
/teacher-course/abilityTrain/delScriptStepFlow
/teacher-course/abilityTrain/publishAbilityTrain
/ai-tools/trainRun/runCard
/ai-tools/trainRun/chat
/ai-tools/trainRun/listLogs
```

`skill_training_build/create_task_from_markdown.py` 当前仍主要写这些旧版任务接口，同时已经接入新的声音/数字人资源链。若目标是 Pro，需要另建 Pro 适配层，不能只把旧路径字符串替换成 `/ai-platform/ability-train/*`，因为任务、角色、步骤、流程和运行协议都不同。

## 15. 仍未考虑或需要补抓的接口

按优先级排序：

1. **Pro 任务列表/复制/导入接口**：当前只确认任务详情和 CRUD，没有确认按课程列出 Pro 任务、复制任务或跨课程导入的正式接口。
2. **省区与学校主数据接口**：当前没有全省区列表、合作学校独立字段或学校到省区映射接口；仍依赖本地映射和课程名解析。
3. **任务级评价标准接口**：当前 Pro API 模块未出现 rubric/score-item CRUD，需要在 Pro“评价标准”页实际保存一次后抓取。
4. **资源面板完整接口**：知识文件、背景图、视频、音乐的搜索、分页、删除和跨课程资源库接口尚未系统整理；这里只确认了上传和被成员/步骤引用的字段。
5. **未完成进度与记忆请求体**：`progress/unfinished`、`memory/list` 路径已确认，但没有稳定请求体和恢复语义。
6. **声纹注册请求体**：`voiceprint/register` 尚未触发实测。
7. **技能删除能力**：当前 Pro 前端未暴露；要确认是产品不支持还是接口在其他包中。
8. **卡片切换可编辑规则**：当前编辑器没有独立流程边接口；需要确认后端是否完全由 planner/运行时决定下一卡，还是另有隐藏配置入口。
9. **并发与幂等约束**：步骤创建前端使用 `useRepeat`，但任务/角色/技能没有公开幂等键。批量导入必须自己按名称和 ID 回查，防止重跑重复创建。
10. **WebSocket 恢复协议**：断线重连、同一 `sessionId` 续跑、超时和主动中止事件尚未在 HAR 中覆盖。
11. **权限与只读接口**：页面有 `readonly`、`from`、发布状态等控制，但缺少统一的“当前用户能否编辑/发布该任务”接口说明。
12. **服务端字段约束**：字段长度、枚举全集、资源大小和音视频格式只看到前端校验，没有正式服务端 schema。

## 16. 自动化必须增加的校验

1. 校验当前省区账号与目标学校所在省区一致。
2. 课程匹配必须唯一；记录课程名、课程 ID、学期和匹配依据。
3. 声音/形象选择要基于剧本人物性别、年龄、职业、语气和场景，不只按名称随机选择。
4. 每个成员 `prompt` 要通过最小长度、占位符、异常短值和角色边界检查。
5. 每个 `<role>ID</role>` 都必须能解析为 `user/system` 或现存成员。
6. 步骤引用的技能、文件、数字人和首步骤都必须存在。
7. 创建后重新 GET 四类核心数据，不把 POST 200 当作最终验收。
8. 发布与删除必须是显式操作；默认只保存草稿。
9. 日志只记录路径、状态、业务 `code`、`traceId`、ID 和数量，不记录凭证或完整私有提示词。

## 17. 页面外围接口

课程中心加载时还会请求以下接口，它们不是 Pro 构建主链：

```text
GET  /base-service/releaseNotice/get
GET  /user/cloud/certify/list?schoolNid=...
GET  /user/user/getSchoolConfig?nid=...&schoolNid=...
GET  /base-service/api/schoolAuth/i18n?schoolNid=...
POST /member/rescource/queryTeacherMenu
GET  /chatim-user/v1/auth/permission
POST /chatim-user/v1/query/user-sig
```

不要为了创建 Pro 任务主动调用聊天鉴权、菜单或公告接口。
