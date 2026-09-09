"""真实 requests Session → transport → client 的离线内存集成回归。"""

from __future__ import annotations

from io import BytesIO
import copy
import json
from pathlib import Path
import sys
import unittest
from urllib.parse import parse_qs, urlsplit

import requests
from requests.adapters import BaseAdapter

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from online_e2e.requests_transport import RequestsTransport
from online_e2e.transport import ClientError
from online_e2e.clients import PdsClient, TeachingCenterClient, WriteConfirmation, teaching_request_digest
from online_e2e.contracts import ConfirmationBinding
from online_e2e.profiles import Endpoint, EndpointProfile, SaveProfile
from online_e2e.safety import ConfirmationTokenManager
from test_online_e2e_clients import SyntheticTransport


class MemoryAdapter(BaseAdapter):
    """在 requests 最底层接收真实 PreparedRequest，永不使用网络。"""

    def __init__(self, handler):
        self.handler = handler
        self.requests = []

    def send(self, request, **kwargs):
        self.requests.append(request)
        status, body, headers = self.handler(request)
        response = requests.Response()
        response.request = request
        response.url = request.url
        response.status_code = status
        response.headers.update(headers)
        response._content = body
        response.raw = BytesIO(body)
        return response

    def close(self):
        pass


def memory_transport(handler):
    session = requests.Session()
    session.trust_env = False
    adapter = MemoryAdapter(handler)
    session.mount("https://", adapter)
    return RequestsTransport(
        base_url="https://example.invalid",
        allowed_hosts=("example.invalid",),
        authorization="Bearer synthetic-auth",
        cookie="synthetic-session-cookie",
        session=session,
    ), adapter


def write_response(mode):
    if mode == "timeout":
        raise requests.ReadTimeout("synthetic timeout")
    if mode == "connection":
        raise requests.ConnectionError("synthetic connection error")
    if mode == "invalid-json":
        return 200, b"not json", {}
    if mode == "invalid-envelope":
        return 200, b"{}", {}
    if mode == "auth":
        return 401, b"{}", {}
    if mode == "rejected":
        return 503, b"{}", {}
    if mode == "redirect":
        return 307, b"{}", {"Location": "https://external.invalid/body-sink"}
    raise AssertionError(mode)


class MemoryPdsService:
    def __init__(self, mode, *, apply_write=True):
        self.service = SyntheticTransport()
        self.service.apply_write = apply_write
        self.mode = mode

    def __call__(self, request):
        url = urlsplit(request.url)
        writing = url.path.endswith("/saveAssistant")
        if writing and self.mode in ("auth", "rejected", "redirect"):
            return write_response(self.mode)
        data = self.service.request(
            request.method, url.path,
            params={key: value[0] for key, value in parse_qs(url.query).items()},
            json=json.loads(request.body) if request.body else None,
        )
        if writing:
            return write_response(self.mode)
        return 200, json.dumps(data).encode(), {}


class TransportClientIntegrationTests(unittest.TestCase):
    def _confirmed_save(self, mode, *, apply_write=True):
        service = MemoryPdsService(mode, apply_write=apply_write)
        transport, adapter = memory_transport(service)
        manager = ConfirmationTokenManager(secret=b"synthetic-signing-key")
        client = PdsClient(
            transport, confirmation_manager=manager, user_nid="synthetic-user",
            save_profile=SaveProfile(True, "synthetic", lambda config: "synthetic-model",
                                     ("appName", "appType", "categoryNid")),
        )
        before = client.snapshot("synthetic-page")
        desired = copy.deepcopy(service.service.config)
        desired["expertMd"]["customContent"] = "synthetic changed content"
        expected = client.snapshot_from_config("synthetic-page", desired, [])
        binding = ConfirmationBinding(
            "synthetic-page", before.digest, expected.digest, "synthetic-knowledge",
            "synthetic-knowledge-digest",
            client.save_and_publish_request_digest("synthetic-page", desired),
            "synthetic-nonce",
        )
        confirmation = WriteConfirmation(manager.issue(binding), binding)
        return client, desired, expected, confirmation, adapter

    def test_307_never_resends_body_to_second_external_host(self):
        def handler(request):
            if request.url == "https://example.invalid/write":
                return 307, b"{}", {"Location": "https://external.invalid/body-sink"}
            return 200, b'{"code":200,"data":true}', {}

        transport, adapter = memory_transport(handler)
        with self.assertRaises(ClientError) as error:
            transport.request("POST", "/write", json={"body": "synthetic-private-body"})
        self.assertEqual(error.exception.code, "REDIRECT_BLOCKED")
        self.assertEqual(len(adapter.requests), 1)
        self.assertEqual(adapter.requests[0].url, "https://example.invalid/write")
        self.assertIn(b"synthetic-private-body", adapter.requests[0].body)

    def test_pds_uncertain_real_transport_writes_read_back_once_without_retry(self):
        for mode in ("timeout", "connection", "invalid-json", "invalid-envelope"):
            for applied in (True, False):
                with self.subTest(mode=mode, applied=applied):
                    client, desired, expected, confirmation, adapter = self._confirmed_save(
                        mode, apply_write=applied
                    )
                    if applied:
                        result = client.save_and_publish("synthetic-page", desired, confirmation=confirmation)
                        self.assertEqual(result.digest, expected.digest)
                    else:
                        with self.assertRaises(ClientError) as error:
                            client.save_and_publish("synthetic-page", desired, confirmation=confirmation)
                        self.assertEqual(error.exception.code, "WRITE_STATE_UNKNOWN")
                    writes = [index for index, request in enumerate(adapter.requests)
                              if request.url.endswith("/saveAssistant")]
                    self.assertEqual(len(writes), 1)
                    after_write = adapter.requests[writes[0] + 1:]
                    self.assertEqual([urlsplit(request.url).path.rsplit("/", 1)[-1]
                                      for request in after_write], ["preview", "agentFullConfig", "list"])

    def test_pds_deterministic_rejection_is_preserved_without_readback(self):
        for mode, code in (("auth", "AUTH_REQUIRED"), ("rejected", "UPSTREAM_REJECTED"),
                           ("redirect", "REDIRECT_BLOCKED")):
            with self.subTest(mode=mode):
                client, desired, _, confirmation, adapter = self._confirmed_save(mode)
                with self.assertRaises(ClientError) as error:
                    client.save_and_publish("synthetic-page", desired, confirmation=confirmation)
                self.assertEqual(error.exception.code, code)
                self.assertTrue(adapter.requests[-1].url.endswith("/saveAssistant"))

    def test_teaching_nonstream_real_transport_uncertainty_never_retries(self):
        for mode, code in (("timeout", "WRITE_STATE_UNKNOWN"), ("connection", "WRITE_STATE_UNKNOWN"),
                           ("invalid-json", "WRITE_STATE_UNKNOWN"), ("invalid-envelope", "WRITE_STATE_UNKNOWN"),
                           ("auth", "AUTH_REQUIRED"), ("rejected", "UPSTREAM_REJECTED"),
                           ("redirect", "REDIRECT_BLOCKED")):
            with self.subTest(mode=mode):
                transport, adapter = memory_transport(lambda request: write_response(mode))
                manager = ConfirmationTokenManager(secret=b"synthetic-signing-key")
                profile = EndpointProfile({"create_session": Endpoint(
                    "POST", "/synthetic/session", True, "synthetic", (), ("sessionId",))})
                client = TeachingCenterClient(transport, profile=profile, confirmation_manager=manager,
                                              target_id="synthetic-target", snapshot_digest="synthetic-before")
                digest = teaching_request_digest("create_session", {})
                binding = ConfirmationBinding("synthetic-target", "synthetic-before", digest,
                                              "synthetic-version", "synthetic-knowledge-digest", digest,
                                              "synthetic-nonce")
                with self.assertRaises(ClientError) as error:
                    client.create_session({}, confirmation=WriteConfirmation(manager.issue(binding), binding))
                self.assertEqual(error.exception.code, code)
                self.assertEqual(len(adapter.requests), 1)


if __name__ == "__main__":
    unittest.main()
