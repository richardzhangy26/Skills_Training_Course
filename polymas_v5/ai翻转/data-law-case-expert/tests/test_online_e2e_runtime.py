from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class FakeResponse:
    def __init__(self, status_code=200, payload=None, chunks=()):
        self.status_code = status_code
        self._payload = payload if payload is not None else {"code": 200, "data": {}}
        self._chunks = chunks

    def json(self):
        return self._payload

    def iter_content(self, chunk_size=None):
        return iter(self._chunks)

    def close(self):
        return None


class FakeSession:
    def __init__(self, response=None, error=None):
        self.response = response or FakeResponse()
        self.error = error
        self.calls = []

    def request(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return self.response


class OnlineE2ERuntimeTests(unittest.TestCase):
    def _binding(self):
        from online_e2e.contracts import ConfirmationBinding

        return ConfirmationBinding(
            target_id="data-law-case-expert",
            snapshot_digest="before",
            expected_digest="after",
            knowledge_version="knowledge-v1",
            knowledge_digest="knowledge-digest-v1",
            diff_digest="plan-digest",
            nonce="nonce-001",
        )

    def test_safety_store_and_reports_share_one_private_atomic_io_implementation(self):
        from online_e2e import private_io, reports, run_store, safety

        self.assertIs(safety.write_private_bytes_atomic, private_io.write_private_bytes_atomic)
        self.assertIs(run_store.write_private_bytes_atomic, private_io.write_private_bytes_atomic)
        self.assertIs(run_store.write_private_json_atomic, private_io.write_private_json_atomic)
        self.assertIs(reports.write_private_bytes_atomic, private_io.write_private_bytes_atomic)

    def test_durable_store_creates_private_key_and_consumes_token_across_instances(self):
        from online_e2e.run_store import DurableRunStore

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = DurableRunStore(root)
            token = first.confirmations.issue(self._binding())
            key_path = root / "confirmation.key"

            self.assertTrue(key_path.is_file())
            self.assertEqual(key_path.stat().st_mode & 0o777, 0o600)
            self.assertTrue(first.confirmations.consume(token, self._binding()))
            second = DurableRunStore(root)
            self.assertFalse(second.confirmations.consume(token, self._binding()))
            ledger = (root / "consumed.json").read_text(encoding="utf-8")
            self.assertNotIn(token, ledger)
            self.assertNotIn("nonce-001", ledger)

    def test_durable_token_is_single_use_across_processes(self):
        from online_e2e.run_store import DurableRunStore

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            store = DurableRunStore(root)
            token = store.confirmations.issue(self._binding())
            script = (
                "from online_e2e.contracts import ConfirmationBinding;"
                "from online_e2e.run_store import DurableRunStore;"
                "import pathlib,sys;"
                "b=ConfirmationBinding('data-law-case-expert','before','after','knowledge-v1','knowledge-digest-v1','plan-digest','nonce-001');"
                "print(DurableRunStore(pathlib.Path(sys.argv[1])).confirmations.consume(sys.argv[2],b))"
            )
            environment = dict(os.environ)
            environment["PYTHONPATH"] = str(ROOT)
            first = subprocess.run(
                [sys.executable, "-c", script, str(root), token],
                check=True,
                capture_output=True,
                text=True,
                env=environment,
            )
            second = subprocess.run(
                [sys.executable, "-c", script, str(root), token],
                check=True,
                capture_output=True,
                text=True,
                env=environment,
            )
            self.assertEqual(first.stdout.strip(), "True")
            self.assertEqual(second.stdout.strip(), "False")

    def test_concurrent_first_store_initialization_never_reads_partial_key(self):
        import online_e2e.run_store as run_store
        import online_e2e.private_io as private_io

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "state"
            entered = threading.Event()
            release = threading.Event()
            original_fdopen = private_io.os.fdopen
            calls = 0
            calls_lock = threading.Lock()
            errors = []

            def delayed_first_fdopen(*args, **kwargs):
                nonlocal calls
                with calls_lock:
                    calls += 1
                    is_first = calls == 1
                if is_first:
                    entered.set()
                    release.wait(timeout=5)
                return original_fdopen(*args, **kwargs)

            def create_store():
                try:
                    run_store.DurableRunStore(root)
                except Exception as error:
                    errors.append(error)

            with patch.object(private_io.os, "fdopen", side_effect=delayed_first_fdopen):
                first = threading.Thread(target=create_store)
                second = threading.Thread(target=create_store)
                first.start()
                self.assertTrue(entered.wait(timeout=2))
                second.start()
                time.sleep(0.05)
                self.assertTrue(second.is_alive(), "第二个初始化必须等待 key 锁")
                release.set()
                first.join(timeout=5)
                second.join(timeout=5)

            self.assertEqual(errors, [])
            self.assertEqual((root / "confirmation.key").stat().st_size, 32)

    def test_store_checkpoint_is_atomic_and_omits_token_and_rejects_path_traversal(self):
        from online_e2e.run_store import DurableRunStore

        with tempfile.TemporaryDirectory() as temporary:
            store = DurableRunStore(Path(temporary))
            checkpoint = store.write_checkpoint(
                "run_001",
                {"status": "PRECHECK", "confirmation_token": "must-not-exist"},
            )
            rendered = checkpoint.read_text(encoding="utf-8")
            self.assertNotIn("must-not-exist", rendered)
            self.assertNotIn("confirmation_token", rendered)
            self.assertEqual(checkpoint.stat().st_mode & 0o777, 0o600)
            for value in ("../escape", "two/levels", "..", ""):
                with self.assertRaises(ValueError):
                    store.write_checkpoint(value, {})

    def test_requests_transport_requires_explicit_env_credentials_and_keeps_them_out_of_repr(self):
        from online_e2e.requests_transport import RequestsTransport
        from online_e2e.transport import ClientError

        with tempfile.TemporaryDirectory() as temporary:
            missing = Path(temporary) / "missing.env"
            missing.write_text("AUTHORIZATION=Bearer only-one\n", encoding="utf-8")
            with self.assertRaises(ClientError) as error:
                RequestsTransport.from_env_file(missing)
            self.assertEqual(error.exception.code, "AUTH_REQUIRED")

            env_file = Path(temporary) / "credentials.env"
            env_file.write_text(
                "AUTHORIZATION=Bearer private-auth\nCOOKIE=private-cookie\n",
                encoding="utf-8",
            )
            transport = RequestsTransport.from_env_file(env_file, session=FakeSession())
            self.assertNotIn("private-auth", repr(transport))
            self.assertNotIn("private-cookie", repr(transport))

    def test_requests_transport_classifies_timeout_auth_http_and_json_errors(self):
        import requests
        from online_e2e.requests_transport import RequestsTransport
        from online_e2e.transport import ClientError

        cases = (
            (FakeSession(error=requests.Timeout()), "TRANSPORT_TIMEOUT"),
            (FakeSession(FakeResponse(status_code=401)), "AUTH_REQUIRED"),
            (FakeSession(FakeResponse(status_code=500)), "UPSTREAM_REJECTED"),
        )
        for session, expected in cases:
            with self.subTest(expected=expected):
                transport = RequestsTransport(
                    base_url="https://example.invalid",
                    authorization="Bearer private",
                    cookie="private",
                    session=session,
                    allowed_hosts=("example.invalid",),
                )
                with self.assertRaises(ClientError) as error:
                    transport.request("GET", "/read")
                self.assertEqual(error.exception.code, expected)
                self.assertNotIn("private", str(error.exception))

        response = FakeResponse()
        response.json = lambda: (_ for _ in ()).throw(ValueError("secret body"))
        transport = RequestsTransport(
            base_url="https://example.invalid",
            authorization="Bearer private",
            cookie="private",
            session=FakeSession(response),
            allowed_hosts=("example.invalid",),
        )
        with self.assertRaises(ClientError) as error:
            transport.request("GET", "/read")
        self.assertEqual(error.exception.code, "CONTRACT_CHANGED")
        self.assertNotIn("secret body", str(error.exception))

    def test_requests_transport_rejects_malicious_base_url_before_request(self):
        from online_e2e.requests_transport import RequestsTransport
        from online_e2e.transport import ClientError

        malicious = (
            "http://cloudapi.polymas.com",
            "https://cloudapi.polymas.com:444",
            "https://user@cloudapi.polymas.com",
            "https://cloudapi.polymas.com/path",
            "https://cloudapi.polymas.com?token=leak",
            "https://evil.example",
        )
        for base_url in malicious:
            with self.subTest(base_url=base_url), tempfile.TemporaryDirectory() as temporary:
                session = FakeSession()
                env_file = Path(temporary) / "credentials.env"
                env_file.write_text(
                    "AUTHORIZATION=Bearer private\nCOOKIE=private\n"
                    f"POLYMAS_BASE_URL={base_url}\n",
                    encoding="utf-8",
                )
                with self.assertRaises(ClientError) as error:
                    RequestsTransport.from_env_file(env_file, session=session)
                self.assertEqual(error.exception.code, "CONTRACT_CHANGED")
                self.assertEqual(session.calls, [])

    def test_requests_transport_revalidates_final_url_and_rejects_path_scheme_bypass(self):
        from online_e2e.requests_transport import RequestsTransport
        from online_e2e.transport import ClientError

        session = FakeSession()
        transport = RequestsTransport(
            base_url="https://cloudapi.polymas.com",
            authorization="Bearer private",
            cookie="private",
            session=session,
        )
        for path in (
            "/https://evil.example",
            "/http://evil.example",
            "/\x00https://evil.example",
            "/\nhttps://evil.example",
            "/\\evil.example",
        ):
            with self.subTest(path=path):
                with self.assertRaises(ClientError) as error:
                    transport.request("GET", path)
                self.assertEqual(error.exception.code, "CONTRACT_CHANGED")
        self.assertEqual(session.calls, [])

    def test_pds_client_preserves_transport_auth_classification(self):
        from online_e2e.clients import PdsClient
        from online_e2e.safety import ConfirmationTokenManager
        from online_e2e.transport import ClientError

        class Transport:
            def request(self, *args, **kwargs):
                raise ClientError("AUTH_REQUIRED", "transport")

        client = PdsClient(
            Transport(), confirmation_manager=ConfirmationTokenManager(secret=b"test")
        )
        with self.assertRaises(ClientError) as error:
            client.preview("x3PalTZaWr")
        self.assertEqual(error.exception.code, "AUTH_REQUIRED")

    def test_reports_redact_personal_identity_preserve_trace_ids_and_never_store_confirmation(self):
        from online_e2e.reports import ReportWriter

        payload = {
            "run_id": "run_001",
            "environment": "synthetic",
            "status": "PASSED",
            "confirmation_token": "must-never-persist",
            "Authorization": "Bearer private-auth",
            "userNid": "private-user",
            "sessionId": "private-session",
            "assistantId": "assistant-visible",
            "conversationId": "conversation-visible",
            "messageId": "message-visible",
            "planId": "plan-visible",
            "traceId": "trace-visible",
        }
        with tempfile.TemporaryDirectory() as temporary:
            paths = ReportWriter(Path(temporary)).write(payload)
            combined = paths.json.read_text(encoding="utf-8") + paths.markdown.read_text(encoding="utf-8")

            for secret in ("must-never-persist", "private-auth", "private-user", "private-session"):
                self.assertNotIn(secret, combined)
            for visible in (
                "assistant-visible",
                "conversation-visible",
                "message-visible",
                "plan-visible",
                "trace-visible",
                "synthetic",
                "PASSED",
            ):
                self.assertIn(visible, combined)
            self.assertEqual(paths.json.stat().st_mode & 0o777, 0o600)
            self.assertEqual(paths.markdown.stat().st_mode & 0o777, 0o600)
            self.assertEqual(list(Path(temporary).glob(".*.tmp")), [])

    def test_confirmation_token_hidden_in_plain_text_is_removed_from_report_and_checkpoint(self):
        from online_e2e.reports import ReportWriter
        from online_e2e.run_store import DurableRunStore

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            store = DurableRunStore(root / "state")
            token = store.confirmations.issue(self._binding())
            checkpoint = store.write_checkpoint(
                "run_009", {"status": "BLOCKED", "note": f"approval {token}"}
            )
            reports = ReportWriter(root / "reports").write(
                {
                    "run_id": "run_009",
                    "environment": "synthetic",
                    "status": "BLOCKED",
                    "note": f"approval {token}",
                }
            )
            combined = (
                checkpoint.read_text(encoding="utf-8")
                + reports.json.read_text(encoding="utf-8")
                + reports.markdown.read_text(encoding="utf-8")
            )
            self.assertNotIn(token, combined)


if __name__ == "__main__":
    unittest.main()
