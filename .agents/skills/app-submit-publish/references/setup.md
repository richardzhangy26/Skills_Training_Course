# 安装与本地配置

## 依赖

安装 Python 3.9 或更高版本，并配置系统默认浏览器。核心脚本不依赖第三方包。

## 自动创建配置

首次执行需要配置的命令时，如果本地配置不存在，脚本会自动从 `config/config.example.json` 创建：

- macOS：`~/.config/company-app-publish/config.json`
- Windows：`%APPDATA%\company-app-publish\config.json`

无需填写任何登录凭据。脚本不会覆盖已有配置。macOS 下配置目录权限为 `700`、配置文件和 Token 缓存权限为 `600`。也可用绝对路径环境变量 `COMPANY_APP_PUBLISH_CONFIG` 指定配置位置。

## 浏览器授权

执行 `login` 时先验证缓存 Token。缓存无效或不存在时，脚本在 `127.0.0.1` 随机端口启动临时服务并打开 Polymas 授权页。用户点击授权后，Token 通过带随机 `state` 的本地回调传给脚本，经 `current-user-menu` 接口校验后保存到 `token-cache.json`。

不要在聊天、命令行或日志中粘贴 Token。不要提交配置、`token-cache.json` 或工作空间状态到 Git。

```bash
bash scripts/app-publish.sh doctor
bash scripts/app-publish.sh login
```

授权默认等待 300 秒，可通过 `authTimeoutSeconds` 调整。

## 工作空间绑定

绑定保存在 `<工作空间>/.company-app-publish/state.json`，只包含 `projectId`。首次完整发布成功后自动绑定。以后必须先执行 `status`、提示覆盖风险并取得明确确认。发布新项目必须新建工作空间，不得删除或篡改状态绕过规则。

## macOS 证书信任

当 Python 默认信任库为空且未显式设置 `SSL_CERT_FILE` 或 `SSL_CERT_DIR` 时，脚本使用 `/etc/ssl/cert.pem` 系统 CA 文件。始终保留 TLS 证书和主机名验证，不使用跳过证书校验的方式解决连接问题。
