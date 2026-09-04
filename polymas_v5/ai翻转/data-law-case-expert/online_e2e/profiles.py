"""端点契约集中配置；未核验的协议没有猜测路径。"""
from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

from .transport import ClientError


@dataclass(frozen=True)
class Endpoint:
    method: str = ''
    path: str = ''
    verified: bool = False
    provenance: str = 'unverified'
    request_fields: tuple[str, ...] = ()
    response_fields: tuple[str, ...] = ()
    response_list: bool = False

    def require_verified(self, operation: str) -> None:
        if (not self.verified or self.provenance == 'unverified'
                or self.method not in ('GET', 'POST') or not self.path.startswith('/')
                or self.path.startswith('//') or '?' in self.path):
            raise ClientError('DEPENDENCY_UNVERIFIED', operation)


@dataclass(frozen=True)
class EndpointProfile:
    endpoints: Mapping[str, Endpoint] = field(default_factory=dict)

    def __post_init__(self):
        object.__setattr__(self, 'endpoints', MappingProxyType(dict(self.endpoints)))

    def get(self, operation: str) -> Endpoint:
        endpoint = self.endpoints.get(operation, Endpoint())
        endpoint.require_verified(operation)
        return endpoint


@dataclass(frozen=True)
class SaveProfile:
    """模型/UI 派生字段转换没有核验前禁止生产保存。"""
    verified: bool = False
    provenance: str = 'unverified'
    normalize_model: Callable[[Mapping[str, Any]], Any] | None = None
    basic_fields: tuple[str, ...] = ()


PDS_PROFILE = EndpointProfile({
    'preview': Endpoint('GET', '/llmOps/agent/v1/preview', True, 'observed-read'),
    'full_config': Endpoint('GET', '/llmOps/mdTemplate/v1/agentFullConfig', True, 'observed-read'),
    'knowledge_bindings': Endpoint('POST', '/llmOps/agent/knowledge/bind/list', True, 'deployed-source'),
    'save_and_publish': Endpoint('POST', '/llmOps/application/saveAssistant', True, 'deployed-source'),
    'bind_knowledge': Endpoint('POST', '/llmOps/agent/knowledge/bind', True, 'deployed-source'),
    'unbind_knowledge': Endpoint('POST', '/llmOps/agent/knowledge/unbind', True, 'deployed-source'),
})

TEACHING_PROFILE = EndpointProfile({
    'resolve_relationship': Endpoint('GET', '/llmOps/mdTemplate/v1/agentFullConfig', True,
        'observed-read', ('agentNid',), ('basicInfo', 'subAgentVOS')),
    'current_user': Endpoint('POST', '/console/v1/get-current-user-detail', True,
        'observed-read', (), ('userNid', 'roleList')),
    'assistants': Endpoint('POST', '/polymasApp/user/relation/new/agent/list', True,
        'observed-read', ('userNid', 'terminalType', 'roleTypeForPC'),
        ('friendNid', 'friendNickName', 'appType', 'appCategory', 'isV5'), True),
    # history 端点已知，但结果结构尚未采集，故不把它冒充新会话或可用历史 API。
})
