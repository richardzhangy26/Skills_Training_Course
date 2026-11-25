# app-submit-publish Skill

通过 Polymas 浏览器授权完成前端 ZIP 的首次创建发布或覆盖发布，并把项目 ID 与当前工作空间绑定。

## 安装

将整个目录复制到 `<项目根目录>/.agents/skills/app-submit-publish/`，确保 `SKILL.md` 位于该目录根部。需要 Python 3.9+，支持 macOS shell 与 Windows PowerShell。

## 快速开始

1. 执行 `doctor`；若本地配置不存在，脚本会从模板自动创建且不会覆盖已有文件。
2. 无需填写登录凭据；执行 `login`，在系统浏览器中登录并点击授权。Token 经本地回调校验后安全缓存。
3. 执行 `status --workspace .`。
4. 发布前让用户确认项目名称和描述，支持手动输入；将回复原样同时传给业务参数和 `--confirm-name`、`--confirm-description`。
5. 向用户展示文件、最终名称、最终描述和绑定信息并取得创建或覆盖确认。
6. 首次发布使用 `--confirm-create CREATE`；已有绑定使用 `--confirm-overwrite <绑定ID>`。

macOS：

```bash
bash scripts/app-publish.sh doctor
bash scripts/app-publish.sh login
bash scripts/app-publish.sh status --workspace .
bash scripts/app-publish.sh publish --file ./dist.zip --name demo --description "更新说明" --confirm-name demo --confirm-description "更新说明" --workspace . --confirm-create CREATE
bash scripts/app-publish.sh detail --workspace .
```

Windows：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\app-publish.ps1 doctor
powershell -ExecutionPolicy Bypass -File scripts\app-publish.ps1 login
powershell -ExecutionPolicy Bypass -File scripts\app-publish.ps1 status --workspace .
powershell -ExecutionPolicy Bypass -File scripts\app-publish.ps1 publish --file .\dist.zip --name demo --description "更新说明" --confirm-name demo --confirm-description "更新说明" --workspace . --confirm-create CREATE
powershell -ExecutionPolicy Bypass -File scripts\app-publish.ps1 detail --workspace .
```

已有绑定时，继续会覆盖该 ID 对应项目；发布新项目必须新建工作空间。

## 测试

```bash
python3 -m unittest discover -s tests -v
```
