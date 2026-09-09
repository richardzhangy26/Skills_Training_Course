"""将稳定 JSON 值递归克隆为普通 dict/list。"""

from __future__ import annotations

from collections.abc import Mapping
import math


def clone_json(value, path="$", *, allow_tuple: bool = True):
    if isinstance(value, Mapping):
        try:
            items = list(value.items())
        except Exception:
            raise ValueError(f"unstable_json_mapping:{path}") from None
        result = {}
        for key, item in items:
            if type(key) is not str or key in result:
                raise ValueError(f"invalid_json_key:{path}")
            result[key] = clone_json(item, f"{path}.{key}", allow_tuple=allow_tuple)
        return result
    if type(value) is list or (allow_tuple and type(value) is tuple):
        return [
            clone_json(item, f"{path}[{index}]", allow_tuple=allow_tuple)
            for index, item in enumerate(list(value))
        ]
    if value is None or type(value) in (str, bool, int):
        return value
    if type(value) is float and math.isfinite(value):
        return value
    raise ValueError(f"invalid_json_value:{path}")
