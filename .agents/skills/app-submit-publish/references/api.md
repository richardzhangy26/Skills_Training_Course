# Polymas 接口契约

## 浏览器授权链路

1. 读取本机 `token-cache.json`；每次使用前都通过校验接口验证。
2. 缓存不存在或校验失败时，仅在 `127.0.0.1` 随机端口启动一次性回调服务。
3. 打开：`https://pds.polymas.com/html-manage/authorization?redirect=<URL编码回调>&state=<随机值>`。
4. 授权应用通过 GET 请求 `http://127.0.0.1:<随机端口>/callback?code=<token>&state=<原值>`。
5. 本地服务仅精确允许来源 `https://pds.polymas.com` 和 `http://127.0.0.1`（不含额外端口）的跨域请求，无 Origin 的直接回调保持支持，并处理 GET/OPTIONS；仅对白名单内的来源回显 `Access-Control-Allow-Origin`，响应包含 `Access-Control-Allow-Credentials: true` 以支持应用端 `withCredentials`，且不允许任意来源 CORS。
6. 脚本校验路径、唯一的 `code`/`state`、随机 state 和 Token 格式；回调不记录或展示 Token。
7. 校验成功返回 HTTP 200 和 JSON `{"code":200,"message":"authorization received"}`，由授权应用自行跳转；校验失败返回 HTTP 400 和不含敏感信息的 JSON，不再返回重定向地址。
8. Token 校验成功后才以权限 `600` 原子写入本地缓存。授权默认 300 秒超时。

`code` 在当前协议中直接承载 Token，不需要服务端换票。完整回调 URL、Token 和 Authorization 请求头不得出现在日志或聊天中。

## Token 校验

`POST https://cloudapi.polymas.com/console/v1/current-user-menu`

请求头使用原样 `Authorization: <token>`（无 `Bearer`），不发送 Cookie。JSON 请求体：

```json
{"moduleType":"agent_course_delivery"}
```

只有业务成功响应才视为有效。失败时不得执行上传、创建、更新、发布或详情查询。

## 业务接口

业务域名为 `https://cloudapi.polymas.com`。所有请求使用经过校验的 Token。

- 新项目上传：`POST /course-deliver/dynamic-html/upload`，表单含 ZIP `file` 与 `resourceType`。
- 创建：`POST /course-deliver/dynamic-html/create`。
- 覆盖上传：先调用 `POST /course-deliver/dynamic-html/upload`，multipart 表单必须包含 ZIP `file` 与 `spaceName=<绑定ID>`；只有接口成功返回后才能继续。
- 详情：`GET /course-deliver/dynamic-html/detail?pageNid=<项目ID>`。
- 发布：`POST /course-deliver/dynamic-html/updateAndPublish`，请求体包含 `pageNid`、`spaceName`、`accessAuth`。不再调用 `/dynamic-html/changeStatus`。
- 更新项目信息：`POST /course-deliver/dynamic-html/update`，请求体包含 `pageNid`、`pageName`、`pageDesc`、`spaceName`、`accessAuth`；覆盖发布时必须作为最后一个远程接口调用。
- `accessAuth` 映射：`1` 表示不需要登录（公开访问），`2` 表示需要登录；CLI 未传 `--need-login` 时发送 `1`，传入时发送 `2`。`needLogin` 字段已废弃，不再发送。

首次创建后查询详情；若 `data.status == 2` 则跳过重复发布，否则调用 `updateAndPublish`。覆盖发布的固定顺序为：登录成功 → `upload(file + spaceName)` 成功回调 → `updateAndPublish` → 查询详情确认 `status == 2` → 最后调用 `update` 更新名称、描述和访问权限。任一步失败立即停止，全部成功后才写工作空间状态。
