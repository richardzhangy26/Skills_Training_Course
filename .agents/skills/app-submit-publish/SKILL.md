---
name: app-submit-publish
description: 通过 Polymas 浏览器授权上传前端构建产物 ZIP，创建或覆盖并发布为在线应用；适用于当前工作空间的项目发布、覆盖发布、登录验证和发布状态查询。仅用于发布前端项目，不用于导入能力训练剧本或训练任务配置。
metadata:
  short-description: 安全发布 Polymas 前端项目
---

# Polymas 应用提交与发布

必须使用本 Skill 自带脚本，不要自行拼接请求。不得在聊天、命令参数或输出中展示 Token、完整授权回调 URL、Authorization 请求头或 Cookie。

## 执行入口

- macOS：`bash <skill目录>/scripts/app-publish.sh ...`
- Windows：`powershell -ExecutionPolicy Bypass -File <skill目录>\scripts\app-publish.ps1 ...`

两个入口都要求 Python 3.9+，只使用标准库。

## 强制规则

1. 第一次使用先执行 `doctor` 和 `login`。任何业务操作也会重新经过登录门禁。
2. 登录门禁固定：先用 `POST /console/v1/current-user-menu` 验证缓存 Token；失效时在 `127.0.0.1` 随机端口启动一次性回调，并打开 `https://pds.polymas.com/html-manage/authorization`。跨域回调仅精确允许 `https://pds.polymas.com` 和 `http://127.0.0.1`（不含额外端口），不得使用通配来源；无 Origin 的直接回调保持支持。回调必须校验随机 `state`，将 `code` 作为 Token，再次验证成功后才能安全缓存和继续业务操作。
3. 不得要求用户在聊天或命令行发送 Token；授权失败或超时后禁止上传、创建、更新、发布和详情查询。
4. 发布前必须让用户确认项目名称和描述，并支持用户手动输入自定义值；不得仅采用 Skill 猜测值、项目元数据或默认值后直接发布。取得回复后展示：工作空间、ZIP 文件、最终项目名称、最终描述、是否需要登录、当前绑定 ID。
5. 必须将用户确认的名称和描述原样分别传入 `--confirm-name <名称>`、`--confirm-description <描述>`。脚本会在登录和上传前校验它们与 `--name`、`--description` 完全一致；不得推断或伪造确认值。空描述也必须由用户明确确认，并以空字符串传入两个描述参数。
6. 未绑定工作空间：取得用户明确确认后才能传 `--confirm-create CREATE`。上传和创建后先查询项目详情；若 `data.status == 2` 则不再调用发布接口。只有确认已发布或发布接口成功后，才把创建接口返回 ID 写入工作空间状态。
7. 已绑定工作空间：必须明确提醒“继续会覆盖 ID 对应项目；发布新项目必须新建工作空间”。用户明确确认后，才能把 `status` 返回的原 ID 传入 `--confirm-overwrite <ID>`。
8. 禁止猜测确认值、使用 `--yes`，或通过管道输入绕过确认。

## 配置

首次执行需要配置的命令时，如果本地配置不存在，脚本会自动将 `config/config.example.json` 复制到：

- macOS：`~/.config/company-app-publish/config.json`
- Windows：`%APPDATA%\company-app-publish\config.json`

自动创建后命令会停止；无需填写登录凭据，重新执行后在系统浏览器完成授权。不得要求用户手动复制模板，也不得覆盖已有配置。也可用 `COMPANY_APP_PUBLISH_CONFIG` 指向绝对路径。详见 [references/setup.md](references/setup.md)。

## 构建标准：静态资源必须使用相对路径

发布目录可能挂载在动态子路径下，因此构建产物中的 JS、CSS、图片和字体引用必须使用相对路径（例如 `./assets/app.js`），禁止使用根绝对路径（例如 `/assets/app.js`）。除非用户明确要求部署到域名根目录并指定固定 base，否则必须遵循本节。

### 框架配置

| 框架/工具 | 必需配置 |
| --- | --- |
| Vite（Vue/React/vanilla） | `vite.config.js` 设置 `base: './'` |
| Vue CLI | `vue.config.js` 设置 `publicPath: './'` |
| Create React App | `package.json` 设置 `"homepage": "."` |
| Webpack | `output.publicPath: ''`（或 `'./'`） |
| Rsbuild | `output.assetPrefix: './'` |
| 纯 HTML | 手写资源路径使用 `./` 前缀，不得以 `/` 开头 |

Next.js 静态导出不支持纯相对路径；动态子目录部署时，应提示用户改用运行时注入 `basePath` 或改用 Vite。

### 运行时规则

- 默认使用 hash 路由（Vue `createWebHashHistory()`、React `HashRouter`）；只有已明确配置服务端 rewrite 时才使用 history 路由。
- `fetch`/XHR、`<img src>` 和 CSS `url()` 不得硬编码根绝对路径。
- 公共资源优先通过构建工具导入，例如 `import image from '@/assets/image.png'`。

### 构建与验收

1. 识别项目包管理器和构建命令，安装依赖并执行生产构建；不得臆造构建结果。
2. 在构建产物目录**内部**打包，确认 ZIP 根目录直接包含入口文件（通常为 `index.html`），不得把整个 `dist` 目录再嵌套一层：

```bash
cd dist && zip -qr ../app.zip . -x '*.DS_Store'
```

   随后核验顶层条目，出现 `dist/` 即为嵌套错误，必须重新打包：

```bash
zipinfo -1 app.zip | awk -F/ '{print $1}' | sort -u
```

3. 发布前检查 `dist/index.html`：

```bash
rg -n '(src|href)="/' dist/index.html
```

有命中时逐项检查；协议外链（如 `https://`）和注释可放行，根绝对静态资源必须修复并重新构建。合格示例：

```html
<script type="module" src="./assets/app.js"></script>
<link rel="stylesheet" href="./assets/app.css">
```

4. 构建、验收和 ZIP 打包成功后，才进入名称/描述确认与发布流程。任何构建或验收失败都不得上传。

## 标准操作

```text
doctor
login
status --workspace <工作空间>
detail --workspace <工作空间>
publish --file <zip> --name <名称> --description <描述> --confirm-name <用户确认名称> --confirm-description <用户确认描述> --workspace <工作空间> <创建或覆盖确认参数>
```

发布时：

- 先通过提问让用户确认或手动输入名称和描述，再将回复原样用于业务参数与对应确认参数。
- `status` 未绑定：确认摘要后使用 `--confirm-create CREATE`。
- `status` 已绑定：先告知覆盖风险和新建工作空间要求，确认后使用 `--confirm-overwrite <原ID>`。
- 私有项目附加 `--need-login`。

脚本输出 JSON。必须同时检查退出码与 `ok`。网络超时或结果不确定时不要直接重试发布，应先运行 `status`、`detail` 并人工核对后台，防止重复创建。

接口字段与实际调用顺序见 [references/api.md](references/api.md)。
