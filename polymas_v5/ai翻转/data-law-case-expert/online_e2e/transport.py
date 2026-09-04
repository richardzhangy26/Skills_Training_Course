"""客户端唯一 I/O 接口；由运行入口注入认证和网络实现。"""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any, Protocol


class ClientError(RuntimeError):
    """不包含服务端原文、请求体或凭证的稳定错误。"""

    def __init__(self, code: str, operation: str, detail: str = ''):
        self.code = code
        self.operation = operation
        # detail 仅允许调用点提供固定描述，不收集异常字符串。
        self.detail = detail
        super().__init__(f'{code}: {operation}' + (f' ({detail})' if detail else ''))

    def as_dict(self) -> dict[str, str]:
        return {'code': self.code, 'operation': self.operation, 'detail': self.detail}


class Transport(Protocol):
    def request(self, method: str, path: str, *, params: Mapping | None = None,
                json: Mapping | None = None, files: Any = None) -> Any: ...

    def stream(self, method: str, path: str, *, json: Mapping) -> Iterable[bytes]: ...


def envelope_data(value: Any, operation: str) -> Any:
    if not isinstance(value, dict) or 'code' not in value:
        raise ClientError('CONTRACT_CHANGED', operation, '响应信封缺失')
    if value['code'] != 200:
        code = 'AUTH_REQUIRED' if value['code'] in (401, 403) else 'UPSTREAM_REJECTED'
        raise ClientError(code, operation)
    if 'data' not in value:
        raise ClientError('CONTRACT_CHANGED', operation, '响应缺少 data')
    return value['data']
