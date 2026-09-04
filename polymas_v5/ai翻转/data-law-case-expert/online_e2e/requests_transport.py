"""显式 env 注入的 requests transport；凭证只保存在内存请求头。"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import requests

from .transport import ClientError


def _read_env(path: Path) -> dict[str, str]:
    try:
        lines = Path(path).read_text(encoding="utf-8").splitlines()
    except OSError:
        raise ClientError("AUTH_REQUIRED", "load_env", "无法读取显式 env 文件") from None
    values: dict[str, str] = {}
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


class RequestsTransport:
    def __init__(
        self,
        *,
        base_url: str,
        authorization: str,
        cookie: str,
        timeout: float = 20.0,
        session: Any = None,
    ):
        if not authorization or not cookie:
            raise ClientError("AUTH_REQUIRED", "transport_init")
        self._base_url = base_url.rstrip("/") + "/"
        self._headers = {"Authorization": authorization, "Cookie": cookie}
        self._timeout = timeout
        self._session = session or requests.Session()

    def __repr__(self) -> str:
        return f"RequestsTransport(base_url={self._base_url!r}, authenticated=True)"

    @classmethod
    def from_env_file(cls, path: Path, *, session: Any = None) -> "RequestsTransport":
        values = _read_env(path)
        authorization = values.get("AUTHORIZATION", "")
        cookie = values.get("COOKIE", "")
        if not authorization or not cookie:
            raise ClientError("AUTH_REQUIRED", "load_env", "AUTHORIZATION/COOKIE 缺失")
        return cls(
            base_url=values.get("POLYMAS_BASE_URL", "https://cloudapi.polymas.com"),
            authorization=authorization,
            cookie=cookie,
            timeout=float(values.get("POLYMAS_TIMEOUT_SECONDS", "20")),
            session=session,
        )

    def _response(self, method: str, path: str, *, params=None, json=None, files=None, stream=False):
        if not isinstance(path, str) or not path.startswith("/") or path.startswith("//"):
            raise ClientError("CONTRACT_CHANGED", "transport", "path 无效")
        try:
            response = self._session.request(
                method=method,
                url=urljoin(self._base_url, path.lstrip("/")),
                headers=dict(self._headers),
                params=params,
                json=json,
                files=files,
                timeout=self._timeout,
                stream=stream,
            )
        except requests.Timeout:
            raise ClientError("TRANSPORT_TIMEOUT", "transport") from None
        except requests.RequestException:
            raise ClientError("TRANSPORT_ERROR", "transport") from None
        if response.status_code in (401, 403):
            response.close()
            raise ClientError("AUTH_REQUIRED", "transport")
        if response.status_code >= 400:
            response.close()
            raise ClientError("UPSTREAM_REJECTED", "transport")
        return response

    def request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping | None = None,
        json: Mapping | None = None,
        files: Any = None,
    ) -> Any:
        response = self._response(method, path, params=params, json=json, files=files)
        try:
            try:
                return response.json()
            except (TypeError, ValueError):
                raise ClientError("CONTRACT_CHANGED", "transport", "响应不是 JSON") from None
        finally:
            response.close()

    def stream(self, method: str, path: str, *, json: Mapping) -> Iterable[bytes]:
        response = self._response(method, path, json=json, stream=True)

        def chunks():
            try:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        yield bytes(chunk)
            except requests.Timeout:
                raise ClientError("TRANSPORT_TIMEOUT", "transport_stream") from None
            except requests.RequestException:
                raise ClientError("TRANSPORT_ERROR", "transport_stream") from None
            finally:
                response.close()

        return chunks()
