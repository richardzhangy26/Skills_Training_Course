#!/usr/bin/env python3
"""Polymas dynamic HTML publisher (Python stdlib only, macOS/Windows)."""
from __future__ import annotations

import argparse
import hashlib
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import mimetypes
import os
from pathlib import Path
import secrets
import stat
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
import webbrowser
from typing import Any, Dict, Optional, Tuple

APP = "company-app-publish"
CONFIG_ENV = "COMPANY_APP_PUBLISH_CONFIG"
STATE_DIR = ".company-app-publish"
STATE_FILE = "state.json"
TOKEN_CACHE_FILE = "token-cache.json"
CONFIG_TEMPLATE_FILE = Path(__file__).resolve().parents[1] / "config" / "config.example.json"
AUTHORIZATION_URL = "https://pds.polymas.com/html-manage/authorization"
AUTHORIZATION_ORIGIN = "https://pds.polymas.com"
# Exact origins only; do not allow arbitrary loopback ports or wildcard origins.
ALLOWED_AUTHORIZATION_ORIGINS = frozenset({AUTHORIZATION_ORIGIN, "http://127.0.0.1"})
MAX_CALLBACK_QUERY = 16384


class AppError(Exception):
    pass


def redact(value: Any) -> Any:
    sensitive = {"password", "passwd", "appid", "appkey", "usernid", "token", "accesstoken", "refreshtoken", "logintoken", "idtoken", "authorization", "cookie"}
    if isinstance(value, dict):
        return {k: ("***" if str(k).lower().replace("_", "").replace("-", "") in sensitive else redact(v)) for k, v in value.items()}
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value


def emit(ok: bool, **values: Any) -> None:
    print(json.dumps(redact({"ok": ok, **values}), ensure_ascii=False, indent=2))


def default_config_path() -> Path:
    configured = os.getenv(CONFIG_ENV)
    if configured:
        path = Path(configured).expanduser()
        if not path.is_absolute():
            raise AppError(f"环境变量 {CONFIG_ENV} 必须使用绝对路径")
        return path
    if os.name == "nt":
        return Path(os.getenv("APPDATA", str(Path.home()))) / APP / "config.json"
    return Path.home() / ".config" / APP / "config.json"


def state_path(workspace: Path) -> Path:
    return workspace.resolve() / STATE_DIR / STATE_FILE


def token_cache_path(config_path: Path) -> Path:
    return config_path.parent / TOKEN_CACHE_FILE


def check_private(path: Path) -> None:
    if path.is_symlink() or not path.is_file():
        raise AppError(f"配置路径必须是普通文件且不能是符号链接: {path}")
    if os.name != "nt":
        mode = stat.S_IMODE(path.stat().st_mode)
        if mode & 0o077:
            raise AppError(f"配置文件权限过宽 ({oct(mode)})；请执行 chmod 600 '{path}'")


def load_json(path: Path, label: str) -> Dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise AppError(f"找不到{label}: {path}")
    except (OSError, json.JSONDecodeError) as exc:
        raise AppError(f"无法读取{label}: {exc}")
    if not isinstance(value, dict):
        raise AppError(f"{label}必须是 JSON 对象")
    return value


def initialize_config(path: Path) -> bool:
    """Create a private local config from the bundled template if missing."""
    if path.exists():
        return False
    if not CONFIG_TEMPLATE_FILE.is_file():
        raise AppError(f"找不到配置模板: {CONFIG_TEMPLATE_FILE}")
    try:
        template = CONFIG_TEMPLATE_FILE.read_text(encoding="utf-8")
        path.parent.mkdir(parents=True, exist_ok=True)
        if os.name != "nt":
            os.chmod(path.parent, 0o700)
        # Exclusive creation avoids overwriting a config created concurrently.
        create_private(path, template)
        return True
    except FileExistsError:
        return False
    except OSError as exc:
        raise AppError(f"无法从模板创建配置文件 {path}: {exc}")


def create_private(path: Path, content: str) -> None:
    """Create the file at path with owner-only permissions, refusing to overwrite.

    Passing 0o600 to os.open matters: a file created with the default umask is
    world-readable during the window before chmod runs.
    """
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(content)
    if os.name != "nt":
        os.chmod(path, 0o600)


def write_private(path: Path, content: str) -> None:
    """Atomically replace path with content while keeping it owner-only.

    The temporary file is created with 0o600 so a cached token is never briefly
    world-readable, and a unique name avoids clobbering a concurrent temporary file.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    if os.name != "nt":
        os.chmod(path.parent, 0o700)
    for _ in range(5):
        temp = path.with_name(path.name + "." + secrets.token_hex(6) + ".tmp")
        try:
            fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            continue
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(content)
            if os.name != "nt":
                os.chmod(temp, 0o600)
            temp.replace(path)
        except BaseException:
            try:
                temp.unlink()
            except OSError:
                pass
            raise
        return
    raise AppError("无法创建临时文件以安全写入: " + str(path))


def load_config() -> Tuple[Dict[str, Any], Path]:
    path = default_config_path()
    created = initialize_config(path)
    if created:
        raise AppError(f"已自动创建本地配置文件: {path}；无需填写凭据，请重新执行命令并在浏览器中完成授权")
    check_private(path)
    config = load_json(path, "配置文件")
    if not isinstance(config.get("endpoints"), dict):
        raise AppError("配置缺少字段: endpoints")
    # Upgrade local configs created before changeStatus was replaced.
    config["endpoints"].setdefault("updateAndPublish", {
        "method": "POST",
        "url": "https://cloudapi.polymas.com/course-deliver/dynamic-html/updateAndPublish",
    })
    config["endpoints"].setdefault("update", {
        "method": "POST",
        "url": "https://cloudapi.polymas.com/course-deliver/dynamic-html/update",
    })
    config["endpoints"].pop("changeStatus", None)
    config["_configPath"] = str(path)
    return config, path


def endpoint(config: Dict[str, Any], name: str) -> Tuple[str, str]:
    item = config.get("endpoints", {}).get(name)
    if not isinstance(item, dict) or not item.get("url"):
        raise AppError(f"未配置接口 endpoints.{name}.url")
    url = str(item["url"])
    if not url.startswith("https://") or "replace-with-" in url:
        raise AppError(f"接口 endpoints.{name}.url 必须是有效 HTTPS 地址")
    return str(item.get("method", "POST")).upper(), url


def dotted(data: Any, path: str) -> Any:
    current = data
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def create_tls_context() -> ssl.SSLContext:
    context = ssl.create_default_context()
    # Some python.org macOS installs have no default CA bundle. Keep certificate
    # verification enabled and use the system bundle only when no trust is loaded.
    if (sys.platform == "darwin"
            and not os.environ.get("SSL_CERT_FILE")
            and not os.environ.get("SSL_CERT_DIR")
            and not context.get_ca_certs()
            and Path("/etc/ssl/cert.pem").is_file()):
        context.load_verify_locations(cafile="/etc/ssl/cert.pem")
    return context


def request(config: Dict[str, Any], name: str, body: Optional[bytes], headers: Dict[str, str], query: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    method, url = endpoint(config, name)
    if query:
        url += ("&" if "?" in url else "?") + urllib.parse.urlencode({k: v for k, v in query.items() if v is not None})
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    # Publishing endpoints are selected through the local hosts file in internal
    # environments. System HTTP(S) proxies may resolve the hostname remotely and
    # silently bypass that mapping, potentially sending credentials to production.
    opener = urllib.request.build_opener(
        urllib.request.ProxyHandler({}),
        urllib.request.HTTPSHandler(context=create_tls_context()),
    )
    try:
        with opener.open(req, timeout=float(config.get("timeoutSeconds", 300))) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        raw_detail = exc.read().decode("utf-8", "replace")[:1000]
        try:
            detail = json.dumps(redact(json.loads(raw_detail)), ensure_ascii=False)
        except (json.JSONDecodeError, TypeError):
            detail = "响应内容已隐藏；请按请求时间和服务端日志排查"
        raise AppError(f"{name} 接口返回 HTTP {exc.code}: {detail}")
    except (urllib.error.URLError, TimeoutError, OSError):
        raise AppError(f"{name} 请求失败，结果可能未知，请勿盲目重试；详细原因请查看本机网络或服务端日志")
    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        raise AppError(f"{name} 接口未返回 JSON")
    if not isinstance(result, dict):
        raise AppError(f"{name} 接口返回格式错误")
    success = result.get("success") is True or result.get("code") in (200, "200")
    if not success:
        raise AppError(f"{name} 业务失败: {json.dumps(redact(result), ensure_ascii=False)[:1000]}")
    return result


def auth_headers(token: str) -> Dict[str, str]:
    return {"Accept": "application/json", "Authorization": token}


def json_request(config: Dict[str, Any], name: str, payload: Dict[str, Any], token: str) -> Dict[str, Any]:
    headers = auth_headers(token)
    headers["Content-Type"] = "application/json; charset=UTF-8"
    return request(config, name, json.dumps(payload, ensure_ascii=False).encode("utf-8"), headers)


def valid_token_value(token: Any) -> bool:
    return isinstance(token, str) and 0 < len(token) <= MAX_CALLBACK_QUERY and not any(ch.isspace() or ord(ch) < 32 for ch in token)


def load_access_token_cache(config: Dict[str, Any]) -> Optional[str]:
    path = token_cache_path(Path(config["_configPath"]))
    if not path.exists():
        return None
    try:
        check_private(path)
        token = load_json(path, "Token 缓存").get("accessToken")
        return token if valid_token_value(token) else None
    except AppError:
        return None


def save_access_token_cache(config: Dict[str, Any], token: str) -> None:
    if not valid_token_value(token):
        raise AppError("授权返回的 Token 格式无效")
    path = token_cache_path(Path(config["_configPath"]))
    write_private(path, json.dumps({"accessToken": token}))


def validate_token(config: Dict[str, Any], token: str) -> None:
    if not valid_token_value(token):
        raise AppError("Token 格式无效")
    json_request(config, "currentUserMenu", {"moduleType": "agent_course_delivery"}, token)


def browser_authorize(config: Dict[str, Any]) -> str:
    state = secrets.token_urlsafe(32)
    result: Dict[str, str] = {}

    class CallbackHandler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: Any) -> None:
            pass

        def cors_headers(self) -> None:
            origin = self.headers.get("Origin")
            if origin in ALLOWED_AUTHORIZATION_ORIGINS:
                self.send_header("Access-Control-Allow-Origin", origin)
                self.send_header("Access-Control-Allow-Credentials", "true")
            self.send_header("Vary", "Origin")
            self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Accept, Content-Type")

        def send_result(self, http_status: int, code: int, message: str) -> None:
            body = json.dumps({"code": code, "message": message}, ensure_ascii=False).encode("utf-8")
            self.send_response(http_status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("Pragma", "no-cache")
            self.send_header("Referrer-Policy", "no-referrer")
            self.cors_headers()
            self.end_headers()
            self.wfile.write(body)

        def do_OPTIONS(self) -> None:
            if urllib.parse.urlsplit(self.path).path != "/callback":
                self.send_error(404)
                return
            self.send_response(204)
            self.cors_headers()
            self.send_header("Access-Control-Max-Age", "600")
            self.end_headers()

        def do_GET(self) -> None:
            parsed = urllib.parse.urlsplit(self.path)
            if parsed.path != "/callback":
                self.send_error(404)
                return
            origin = self.headers.get("Origin")
            if origin is not None and origin not in ALLOWED_AUTHORIZATION_ORIGINS:
                self.send_result(403, 403, "origin not allowed")
                return
            if len(self.path) > MAX_CALLBACK_QUERY:
                self.send_result(400, 400, "invalid authorization callback")
                return
            values = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
            codes, states = values.get("code", []), values.get("state", [])
            if len(codes) != 1 or len(states) != 1 or not secrets.compare_digest(states[0], state) or not valid_token_value(codes[0]):
                self.send_result(400, 400, "invalid authorization callback")
                return
            result["token"] = codes[0]
            self.send_result(200, 200, "authorization received")

    try:
        server = HTTPServer(("127.0.0.1", 0), CallbackHandler)
    except OSError:
        raise AppError("无法启动本地授权回调服务")
    callback = f"http://127.0.0.1:{server.server_port}/callback"
    auth_url = AUTHORIZATION_URL + "?" + urllib.parse.urlencode({"redirect": callback, "state": state})
    timeout = float(config.get("authTimeoutSeconds", 300))
    deadline = time.monotonic() + max(1.0, timeout)
    try:
        if not webbrowser.open(auth_url):
            raise AppError("无法打开系统浏览器，请检查默认浏览器设置")
        while "token" not in result and time.monotonic() < deadline:
            server.timeout = min(0.5, max(0.01, deadline - time.monotonic()))
            server.handle_request()
    finally:
        server.server_close()
    if "token" not in result:
        raise AppError("浏览器授权超时，未执行业务接口")
    return result["token"]


def login(config: Dict[str, Any]) -> str:
    cached = load_access_token_cache(config)
    if cached:
        try:
            validate_token(config, cached)
            return cached
        except AppError:
            pass
    token = browser_authorize(config)
    try:
        validate_token(config, token)
    except AppError:
        raise AppError("浏览器授权 Token 校验失败，未执行业务接口")
    save_access_token_cache(config, token)
    return token


def multipart(fields: Dict[str, Any], file_path: Path) -> Tuple[bytes, str]:
    boundary = "----DSHSkill" + uuid.uuid4().hex
    chunks = []
    for key, value in fields.items():
        chunks += [f"--{boundary}\r\n".encode(), f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode(), str(value).encode(), b"\r\n"]
    mime = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
    safe_name = file_path.name.replace('"', "")
    chunks += [f"--{boundary}\r\n".encode(), f'Content-Disposition: form-data; name="file"; filename="{safe_name}"\r\n'.encode(), f"Content-Type: {mime}\r\n\r\n".encode(), file_path.read_bytes(), b"\r\n", f"--{boundary}--\r\n".encode()]
    return b"".join(chunks), boundary


def upload(config: Dict[str, Any], token: str, package: Path, project_id: Optional[str]) -> Dict[str, Any]:
    fields = {"spaceName": project_id} if project_id else {"resourceType": config.get("resourceType", 2)}
    body, boundary = multipart(fields, package)
    headers = auth_headers(token)
    headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
    return request(config, "upload", body, headers)


def read_state(workspace: Path) -> Dict[str, Any]:
    path = state_path(workspace)
    return load_json(path, "工作空间状态") if path.exists() else {}


def write_state(workspace: Path, project_id: str) -> None:
    path = state_path(workspace)
    write_private(path, json.dumps({"projectId": project_id}, ensure_ascii=False, indent=2) + "\n")


def publish(args: argparse.Namespace, config: Dict[str, Any]) -> Dict[str, Any]:
    workspace = Path(args.workspace).expanduser().resolve()
    package = Path(args.file).expanduser().resolve()
    if not workspace.is_dir():
        raise AppError(f"工作空间目录不存在: {workspace}")
    if not package.is_file():
        raise AppError(f"应用文件不存在: {package}")
    if args.confirm_name != args.name:
        raise AppError("项目名称尚未由用户确认，或确认值与 --name 不一致；请让用户手动输入并确认项目名称")
    if args.confirm_description != args.description:
        raise AppError("项目描述尚未由用户确认，或确认值与 --description 不一致；请让用户手动输入并确认项目描述")

    bound = read_state(workspace).get("projectId")
    if bound and args.confirm_overwrite != str(bound):
        raise AppError(f"工作空间已绑定项目 ID {bound}。继续将覆盖该项目；如需发布新项目请新建工作空间。明确确认后传入 --confirm-overwrite {bound}")
    if not bound and args.confirm_create != "CREATE":
        raise AppError("当前工作空间尚未绑定项目。请展示名称、描述、文件并取得首次创建确认；确认后传入 --confirm-create CREATE")

    token = login(config)  # Hard gate before every business flow.
    uploaded = upload(config, token, package, str(bound) if bound else None)
    upload_id = dotted(uploaded, "data.pageNid")
    entry = dotted(uploaded, "data.entryFileName")
    size = dotted(uploaded, "data.fileSize")
    if not upload_id or not entry or size is None:
        raise AppError("上传响应缺少 data.pageNid、entryFileName 或 fileSize；已停止")

    access_auth = 2 if args.need_login else 1
    if bound:
        project_id = str(bound)
        if str(upload_id) != project_id:
            raise AppError(f"覆盖上传返回 ID {upload_id} 与绑定 ID {bound} 不一致；已停止")
        # Overwrite order is strict: upload(file + spaceName) must succeed first,
        # then updateAndPublish is called with the same bound project ID.
        json_request(config, "updateAndPublish", {"pageNid": project_id, "spaceName": project_id, "accessAuth": access_auth}, token)
        current = request(config, "detail", None, auth_headers(token), {"pageNid": project_id})
        current_status = dotted(current, "data.status")
        if str(current_status) != "2":
            raise AppError("覆盖发布接口成功后详情仍不是发布状态；已停止")
        # Project metadata update is intentionally the final remote call.
        json_request(config, "update", {"pageNid": project_id, "pageName": args.name, "pageDesc": args.description, "spaceName": project_id, "accessAuth": access_auth}, token)
        publish_skipped = False
        message = "覆盖发布并更新项目信息成功"
    else:
        created = json_request(config, "create", {"pageName": args.name, "pageDesc": args.description, "resourceType": config.get("resourceType", 2), "tagIds": [], "pageNid": upload_id, "entryFileName": entry, "fileSize": size}, token)
        created_id = created.get("data")
        if not isinstance(created_id, (str, int)) or not str(created_id):
            raise AppError("创建响应缺少项目 ID data；未写入工作空间绑定")
        project_id = str(created_id)
        publish_id = str(upload_id)
        current = request(config, "detail", None, auth_headers(token), {"pageNid": publish_id})
        current_status = dotted(current, "data.status")
        publish_skipped = str(current_status) == "2"
        if publish_skipped:
            message = "项目已是发布状态，已跳过发布接口"
        else:
            json_request(config, "updateAndPublish", {"pageNid": publish_id, "spaceName": publish_id, "accessAuth": access_auth}, token)
            message = "发布成功"

    write_state(workspace, project_id)
    return {
        "message": message,
        "projectId": project_id,
        "publishStatus": current_status,
        "publishSkipped": publish_skipped,
        "workspace": str(workspace),
        "file": str(package),
        "sha256": hashlib.sha256(package.read_bytes()).hexdigest(),
    }


def detail(args: argparse.Namespace, config: Dict[str, Any]) -> Dict[str, Any]:
    workspace = Path(args.workspace).expanduser().resolve()
    if not workspace.is_dir():
        raise AppError(f"工作空间目录不存在: {workspace}")
    project_id = read_state(workspace).get("projectId")
    if not project_id:
        raise AppError("当前工作空间没有绑定项目 ID")
    token = login(config)
    return {"message": "查询成功", "result": request(config, "detail", None, auth_headers(token), {"pageNid": project_id})}


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="Polymas 前端项目发布工具")
    commands = root.add_subparsers(dest="command", required=True)
    commands.add_parser("doctor", help="检查本地配置")
    commands.add_parser("login", help="验证缓存 Token，失效时打开浏览器授权")
    status = commands.add_parser("status", help="查看当前工作空间绑定")
    status.add_argument("--workspace", default=".")
    query = commands.add_parser("detail", help="登录后查询已绑定项目详情")
    query.add_argument("--workspace", default=".")
    deploy = commands.add_parser("publish", help="登录、上传、创建/覆盖并发布")
    deploy.add_argument("--file", required=True)
    deploy.add_argument("--name", required=True)
    deploy.add_argument("--description", default="")
    deploy.add_argument("--confirm-name", required=True, help="用户手动输入并确认的项目名称，必须与 --name 完全一致")
    deploy.add_argument("--confirm-description", required=True, help="用户手动输入并确认的项目描述，必须与 --description 完全一致")
    deploy.add_argument("--workspace", default=".")
    deploy.add_argument("--need-login", action="store_true")
    deploy.add_argument("--confirm-create", choices=["CREATE"])
    deploy.add_argument("--confirm-overwrite")
    return root


def main() -> int:
    args = parser().parse_args()
    try:
        if args.command == "status":
            workspace = Path(args.workspace).expanduser().resolve()
            if not workspace.is_dir():
                raise AppError(f"工作空间目录不存在: {workspace}")
            state = read_state(workspace)
            emit(True, workspace=str(workspace), bound=bool(state.get("projectId")), projectId=state.get("projectId"))
            return 0
        config, config_path = load_config()
        if args.command == "doctor":
            for name in ("currentUserMenu", "upload", "create", "detail", "updateAndPublish", "update"):
                endpoint(config, name)
            emit(True, message="配置检查通过", configPath=str(config_path))
        elif args.command == "login":
            login(config)
            emit(True, message="浏览器授权 Token 校验成功")
        elif args.command == "detail":
            emit(True, **detail(args, config))
        else:
            emit(True, **publish(args, config))
        return 0
    except AppError as exc:
        emit(False, error=str(exc))
        return 1
    except KeyboardInterrupt:
        emit(False, error="用户取消操作")
        return 130


if __name__ == "__main__":
    sys.exit(main())
