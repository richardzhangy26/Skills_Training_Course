import importlib.util
from pathlib import Path
import stat
import tempfile
import threading
import unittest
import urllib.error
import urllib.parse
import urllib.request
from unittest.mock import MagicMock, patch

SCRIPT = Path(__file__).parents[1] / "scripts" / "app_publish.py"
spec = importlib.util.spec_from_file_location("app_publish", SCRIPT)
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)


class PublishFlowTests(unittest.TestCase):
    def config(self, config_path="/tmp/config.json"):
        return {
            "_configPath": config_path, "resourceType": 2, "authTimeoutSeconds": 1,
            "endpoints": {name: {"method": "GET" if name == "detail" else "POST", "url": "https://example.test/" + name} for name in ("currentUserMenu", "upload", "create", "detail", "updateAndPublish", "update")},
        }

    def test_redaction_hides_credentials(self):
        value = {"authorization": "secret", "token": "t", "data": {"access_token": "x", "id": "safe"}}
        self.assertEqual("***", app.redact(value)["authorization"])
        self.assertEqual("***", app.redact(value)["data"]["access_token"])

    def test_missing_config_is_initialized_from_template_privately(self):
        with tempfile.TemporaryDirectory() as root:
            config_path = Path(root) / "nested" / "config.json"
            template = Path(root) / "template.json"
            template.write_text('{"endpoints":{}}', encoding="utf-8")
            with patch.object(app, "CONFIG_TEMPLATE_FILE", template):
                self.assertTrue(app.initialize_config(config_path))
                self.assertFalse(app.initialize_config(config_path))
            self.assertEqual(template.read_text(encoding="utf-8"), config_path.read_text(encoding="utf-8"))
            if app.os.name != "nt":
                self.assertEqual(0o700, config_path.parent.stat().st_mode & 0o777)
                self.assertEqual(0o600, config_path.stat().st_mode & 0o777)

    def test_token_cache_and_state_are_private_from_creation(self):
        # A token cache created with the default umask is group/world readable
        # during the window before chmod runs, so assert the real mode of every
        # newly created file at the moment it comes into existence.
        previous = app.os.umask(0o022)
        created_modes = []
        real_open = app.os.open
        real_write_text = Path.write_text

        def recording_open(path, flags, mode=0o777, *args, **kwargs):
            fd = real_open(path, flags, mode, *args, **kwargs)
            if flags & app.os.O_CREAT:
                try:
                    created_modes.append((str(path), stat.S_IMODE(app.os.stat(fd).st_mode)))
                except OSError:
                    pass
            return fd

        def recording_write_text(self, data, *args, **kwargs):
            # The pre-hardening writer creates the temp file through write_text,
            # which applies the default umask instead of 0600.
            result = real_write_text(self, data, *args, **kwargs)
            try:
                created_modes.append((str(self), stat.S_IMODE(self.stat().st_mode)))
            except OSError:
                pass
            return result

        try:
            app.os.open = recording_open
            Path.write_text = recording_write_text
            with tempfile.TemporaryDirectory() as root:
                config_path = Path(root) / "config.json"
                config_path.write_text("{}", encoding="utf-8")
                config_path.chmod(0o600)
                created_modes.clear()
                cache = app.token_cache_path(config_path)
                app.save_access_token_cache({"_configPath": str(config_path)}, "tok-1")
                self.assertEqual(0o600, cache.stat().st_mode & 0o777)
                self.assertEqual(0o700, cache.parent.stat().st_mode & 0o777)
                app.save_access_token_cache({"_configPath": str(config_path)}, "tok-2")
                self.assertEqual(0o600, cache.stat().st_mode & 0o777)
                self.assertEqual("tok-2", app.load_access_token_cache({"_configPath": str(config_path)}))
                workspace = Path(root) / "ws"
                workspace.mkdir()
                app.write_state(workspace, "project-1")
                state = app.state_path(workspace)
                self.assertEqual(0o600, state.stat().st_mode & 0o777)
                self.assertEqual({"projectId": "project-1"}, app.read_state(workspace))
                self.assertEqual([], sorted(p.name for p in cache.parent.iterdir() if p.name.endswith(".tmp")))
                self.assertEqual([], sorted(p.name for p in state.parent.iterdir() if p.name.endswith(".tmp")))
            if app.os.name != "nt":
                # Every file created while caching a token or binding a workspace
                # must be owner-only from birth; a 0644 temp file is the bug.
                self.assertTrue(created_modes, "expected the cache write to create a file")
                self.assertEqual([], [item for item in created_modes if item[1] & 0o077],
                                 "a credential-bearing file was created with permissive mode")
        finally:
            app.os.open = real_open
            Path.write_text = real_write_text
            app.os.umask(previous)

    def test_load_config_reports_newly_initialized_path(self):
        with tempfile.TemporaryDirectory() as root:
            config_path = Path(root) / "config.json"
            template = Path(root) / "template.json"
            template.write_text('{"endpoints":{}}', encoding="utf-8")
            with patch.object(app, "CONFIG_TEMPLATE_FILE", template), patch.object(app, "default_config_path", return_value=config_path):
                with self.assertRaises(app.AppError) as caught:
                    app.load_config()
            self.assertTrue(config_path.is_file())
            self.assertIn("已自动创建本地配置文件", str(caught.exception))
            self.assertIn(str(config_path), str(caught.exception))

    def test_existing_config_replaces_change_status_endpoint(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "config.json"
            path.write_text('{"endpoints":{"changeStatus":{"method":"POST","url":"https://example.test/changeStatus"}}}', encoding="utf-8")
            if app.os.name != "nt":
                path.chmod(0o600)
            with patch.object(app, "default_config_path", return_value=path):
                config, _ = app.load_config()
            self.assertNotIn("changeStatus", config["endpoints"])
            self.assertEqual("https://cloudapi.polymas.com/course-deliver/dynamic-html/updateAndPublish", config["endpoints"]["updateAndPublish"]["url"])

    def test_empty_macos_trust_uses_system_ca_with_verification_enabled(self):
        context = MagicMock()
        context.get_ca_certs.return_value = []
        with patch.object(app.ssl, "create_default_context", return_value=context), patch.object(app.sys, "platform", "darwin"), patch.dict(app.os.environ, {}, clear=True), patch.object(app.Path, "is_file", return_value=True):
            self.assertIs(context, app.create_tls_context())
        context.load_verify_locations.assert_called_once_with(cafile="/etc/ssl/cert.pem")

    def test_existing_or_explicit_trust_is_preserved(self):
        for certs, env in (([{}], {}), ([], {"SSL_CERT_FILE": "/custom/ca.pem"}), ([], {"SSL_CERT_DIR": "/custom/certs"})):
            with self.subTest(env=env, has_certs=bool(certs)):
                context = MagicMock()
                context.get_ca_certs.return_value = certs
                with patch.object(app.ssl, "create_default_context", return_value=context), patch.object(app.sys, "platform", "darwin"), patch.dict(app.os.environ, env, clear=True):
                    self.assertIs(context, app.create_tls_context())
                context.load_verify_locations.assert_not_called()

    def test_request_disables_system_proxy(self):
        response = MagicMock()
        response.__enter__.return_value.read.return_value = b'{"code": 200, "data": {}}'
        opener = MagicMock()
        opener.open.return_value = response
        with patch.object(app.urllib.request, "build_opener", return_value=opener) as build_opener:
            result = app.request(self.config(), "detail", None, {}, {"pageNid": "project-1"})
        self.assertEqual(200, result["code"])
        proxy_handler = build_opener.call_args.args[0]
        self.assertIsInstance(proxy_handler, urllib.request.ProxyHandler)
        self.assertEqual({}, proxy_handler.proxies)

    def test_validate_token_uses_raw_authorization_and_expected_payload(self):
        with patch.object(app, "request", return_value={"code": 200}) as request:
            app.validate_token(self.config(), "user-token")
        args = request.call_args.args
        self.assertEqual("currentUserMenu", args[1])
        self.assertEqual("user-token", args[3]["Authorization"])
        self.assertNotIn("Cookie", args[3])
        self.assertEqual({"moduleType": "agent_course_delivery"}, __import__("json").loads(args[2]))

    def test_callback_origins_cors_and_state(self):
        for origin in (app.AUTHORIZATION_ORIGIN, "http://127.0.0.1", None):
            with self.subTest(origin=origin):
                responses = []
                errors = []
                threads = []

                def open_browser(url):
                    query = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)
                    callback = query["redirect"][0]
                    state = query["state"][0]

                    def send(method, request_origin, request_state):
                        headers = {} if request_origin is None else {"Origin": request_origin}
                        request = urllib.request.Request(
                            callback + "?" + urllib.parse.urlencode({"code": "test-only-token", "state": request_state}),
                            headers=headers, method=method,
                        )
                        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
                        try:
                            response = opener.open(request, timeout=2)
                        except urllib.error.HTTPError as exc:
                            response = exc
                        with response:
                            responses.append((response.status, dict(response.headers), response.read().decode()))

                    def run():
                        try:
                            for forbidden in ("https://untrusted.example", "http://127.0.0.1:5175", "null"):
                                send("OPTIONS", forbidden, state)
                                send("GET", forbidden, state)
                            send("OPTIONS", origin, state)
                            send("GET", origin, "wrong-state")
                            send("GET", origin, state)
                        except Exception as exc:
                            errors.append(type(exc).__name__)

                    thread = threading.Thread(target=run, daemon=True)
                    threads.append(thread)
                    thread.start()
                    return True

                config = self.config()
                config["authTimeoutSeconds"] = 5
                with patch.object(app.webbrowser, "open", side_effect=open_browser):
                    self.assertEqual("test-only-token", app.browser_authorize(config))
                threads[0].join(timeout=2)
                self.assertFalse(errors)
                self.assertEqual([204, 403, 204, 403, 204, 403, 204, 400, 200], [r[0] for r in responses])
                for response in responses[:6]:
                    self.assertNotIn("Access-Control-Allow-Origin", response[1])
                    self.assertNotIn("Access-Control-Allow-Credentials", response[1])
                for response in responses[6:]:
                    self.assertEqual(origin, response[1].get("Access-Control-Allow-Origin"))
                    self.assertEqual("true" if origin else None, response[1].get("Access-Control-Allow-Credentials"))
                self.assertTrue(all("test-only-token" not in r[2] for r in responses))

    def test_cached_token_is_validated_before_use(self):
        with patch.object(app, "load_access_token_cache", return_value="cached-token"), patch.object(app, "validate_token") as validate, patch.object(app, "browser_authorize") as browser:
            self.assertEqual("cached-token", app.login(self.config()))
        validate.assert_called_once_with(self.config(), "cached-token")
        browser.assert_not_called()

    def test_invalid_cache_opens_browser_and_saves_only_after_validation(self):
        events = []
        with patch.object(app, "load_access_token_cache", return_value="stale-token"), patch.object(app, "validate_token", side_effect=lambda config, token: (_ for _ in ()).throw(app.AppError("expired")) if token == "stale-token" else events.append("validated")), patch.object(app, "browser_authorize", return_value="fresh-token"), patch.object(app, "save_access_token_cache", side_effect=lambda config, token: events.append("saved")):
            self.assertEqual("fresh-token", app.login(self.config()))
        self.assertEqual(["validated", "saved"], events)

    def test_publish_requires_exact_name_and_description_confirmation_before_login(self):
        with tempfile.TemporaryDirectory() as root:
            package = Path(root) / "app.zip"; package.write_bytes(b"zip")
            base = {"workspace": root, "file": str(package), "name": "项目名", "description": "项目描述", "confirm_name": "其他名称", "confirm_description": "项目描述", "need_login": False, "confirm_create": "CREATE", "confirm_overwrite": None}
            with patch.object(app, "login") as login:
                with self.assertRaises(app.AppError) as caught:
                    app.publish(type("Args", (), base)(), self.config())
                login.assert_not_called()
                self.assertIn("项目名称", str(caught.exception))

            base["confirm_name"] = "项目名"
            base["confirm_description"] = "其他描述"
            with patch.object(app, "login") as login:
                with self.assertRaises(app.AppError) as caught:
                    app.publish(type("Args", (), base)(), self.config())
                login.assert_not_called()
                self.assertIn("项目描述", str(caught.exception))

    def test_login_failure_blocks_upload(self):
        with tempfile.TemporaryDirectory() as root:
            package = Path(root) / "app.zip"; package.write_bytes(b"zip")
            args = type("Args", (), {"workspace": root, "file": str(package), "name": "n", "description": "d", "confirm_name": "n", "confirm_description": "d", "need_login": False, "confirm_create": "CREATE", "confirm_overwrite": None})()
            with patch.object(app, "login", side_effect=app.AppError("login failed")), patch.object(app, "upload") as upload:
                with self.assertRaises(app.AppError): app.publish(args, self.config())
                upload.assert_not_called()

    def test_first_publish_queries_status_then_publishes_when_needed(self):
        with tempfile.TemporaryDirectory() as root:
            package = Path(root) / "app.zip"; package.write_bytes(b"zip")
            args = type("Args", (), {"workspace": root, "file": str(package), "name": "n", "description": "d", "confirm_name": "n", "confirm_description": "d", "need_login": False, "confirm_create": "CREATE", "confirm_overwrite": None})()
            responses = [{"code": 200, "data": "project-9"}, {"code": 200, "data": None}]
            with patch.object(app, "login", return_value="token"), patch.object(app, "upload", return_value={"code": 200, "data": {"pageNid": "upload-1", "entryFileName": "index.html", "fileSize": 3}}), patch.object(app, "request", return_value={"code": 200, "data": {"status": 1}}) as detail, patch.object(app, "json_request", side_effect=responses) as request:
                result = app.publish(args, self.config())
            self.assertEqual("project-9", result["projectId"])
            self.assertFalse(result["publishSkipped"])
            self.assertEqual("project-9", app.read_state(Path(root))["projectId"])
            self.assertEqual({"pageNid": "upload-1"}, detail.call_args.args[4])
            self.assertEqual("updateAndPublish", request.call_args_list[1].args[1])
            self.assertEqual({"pageNid": "upload-1", "spaceName": "upload-1", "accessAuth": 1}, request.call_args_list[1].args[2])

    def test_first_publish_uses_login_access_auth_when_publishing(self):
        with tempfile.TemporaryDirectory() as root:
            package = Path(root) / "app.zip"; package.write_bytes(b"zip")
            args = type("Args", (), {"workspace": root, "file": str(package), "name": "n", "description": "d", "confirm_name": "n", "confirm_description": "d", "need_login": True, "confirm_create": "CREATE", "confirm_overwrite": None})()
            with patch.object(app, "login", return_value="token"), patch.object(app, "upload", return_value={"code": 200, "data": {"pageNid": "upload-1", "entryFileName": "index.html", "fileSize": 3}}), patch.object(app, "request", return_value={"code": 200, "data": {"status": 1}}), patch.object(app, "json_request", side_effect=[{"code": 200, "data": "project-9"}, {"code": 200, "data": None}]) as request:
                app.publish(args, self.config())
            self.assertEqual({"pageNid": "upload-1", "spaceName": "upload-1", "accessAuth": 2}, request.call_args_list[1].args[2])

    def test_first_publish_skips_change_status_when_detail_is_published(self):
        with tempfile.TemporaryDirectory() as root:
            package = Path(root) / "app.zip"; package.write_bytes(b"zip")
            args = type("Args", (), {"workspace": root, "file": str(package), "name": "n", "description": "d", "confirm_name": "n", "confirm_description": "d", "need_login": False, "confirm_create": "CREATE", "confirm_overwrite": None})()
            with patch.object(app, "login", return_value="token"), patch.object(app, "upload", return_value={"code": 200, "data": {"pageNid": "upload-1", "entryFileName": "index.html", "fileSize": 3}}), patch.object(app, "request", return_value={"code": 200, "data": {"status": 2}}), patch.object(app, "json_request", return_value={"code": 200, "data": "project-9"}) as request:
                result = app.publish(args, self.config())
            self.assertTrue(result["publishSkipped"])
            self.assertEqual("项目已是发布状态，已跳过发布接口", result["message"])
            self.assertEqual(1, request.call_count)
            self.assertEqual("create", request.call_args.args[1])
            self.assertEqual("project-9", app.read_state(Path(root))["projectId"])

    def test_detail_uses_only_workspace_binding(self):
        with tempfile.TemporaryDirectory() as root:
            app.write_state(Path(root), "project-1")
            args = type("Args", (), {"workspace": root})()
            with patch.object(app, "login", return_value="token"), patch.object(app, "request", return_value={"code": 200, "data": {"pageNid": "project-1"}}) as request:
                app.detail(args, self.config())
            self.assertEqual({"pageNid": "project-1"}, request.call_args.args[4])

    def test_bound_publish_requires_exact_confirmation_before_login(self):
        with tempfile.TemporaryDirectory() as root:
            app.write_state(Path(root), "project-1")
            package = Path(root) / "app.zip"; package.write_bytes(b"zip")
            args = type("Args", (), {"workspace": root, "file": str(package), "name": "n", "description": "d", "confirm_name": "n", "confirm_description": "d", "need_login": False, "confirm_create": None, "confirm_overwrite": None})()
            with patch.object(app, "login") as login:
                with self.assertRaises(app.AppError) as caught: app.publish(args, self.config())
                login.assert_not_called()
                self.assertIn("新建工作空间", str(caught.exception))

    def test_existing_project_upload_then_update_and_publish(self):
        with tempfile.TemporaryDirectory() as root:
            app.write_state(Path(root), "project-1")
            package = Path(root) / "app.zip"; package.write_bytes(b"zip")
            args = type("Args", (), {"workspace": root, "file": str(package), "name": "n", "description": "d", "confirm_name": "n", "confirm_description": "d", "need_login": True, "confirm_create": None, "confirm_overwrite": "project-1"})()
            events = []
            def uploaded(*call_args):
                events.append("upload")
                return {"code": 200, "data": {"pageNid": "project-1", "entryFileName": "index.html", "fileSize": 3}}
            def published(*call_args):
                events.append(call_args[1])
                return {"code": 200, "data": None}
            def detailed(*call_args):
                events.append("detail")
                return {"code": 200, "data": {"status": 2}}
            with patch.object(app, "login", return_value="token"), patch.object(app, "upload", side_effect=uploaded) as upload, patch.object(app, "request", side_effect=detailed), patch.object(app, "json_request", side_effect=published) as json_request:
                result = app.publish(args, self.config())
            self.assertFalse(result["publishSkipped"])
            self.assertEqual("覆盖发布并更新项目信息成功", result["message"])
            self.assertEqual(["upload", "updateAndPublish", "detail", "update"], events)
            self.assertEqual(2, json_request.call_count)
            self.assertEqual({"pageNid": "project-1", "spaceName": "project-1", "accessAuth": 2}, json_request.call_args_list[0].args[2])
            self.assertEqual({"pageNid": "project-1", "pageName": "n", "pageDesc": "d", "spaceName": "project-1", "accessAuth": 2}, json_request.call_args_list[1].args[2])
            self.assertEqual("project-1", upload.call_args.args[3])
            self.assertEqual("project-1", app.read_state(Path(root))["projectId"])

    def test_publish_failure_does_not_bind_workspace(self):
        with tempfile.TemporaryDirectory() as root:
            package = Path(root) / "app.zip"; package.write_bytes(b"zip")
            args = type("Args", (), {"workspace": root, "file": str(package), "name": "n", "description": "d", "confirm_name": "n", "confirm_description": "d", "need_login": False, "confirm_create": "CREATE", "confirm_overwrite": None})()
            with patch.object(app, "login", return_value="token"), patch.object(app, "upload", return_value={"code": 200, "data": {"pageNid": "upload-1", "entryFileName": "index.html", "fileSize": 3}}), patch.object(app, "request", return_value={"code": 200, "data": {"status": 1}}), patch.object(app, "json_request", side_effect=[{"code": 200, "data": "project-1"}, app.AppError("publish failed")]):
                with self.assertRaises(app.AppError): app.publish(args, self.config())
            self.assertEqual({}, app.read_state(Path(root)))


if __name__ == "__main__":
    unittest.main()
