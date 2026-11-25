# -*- coding: utf-8 -*-
"""提示词审核对抗工具（本地离线）。

python3 -m prompt_guard.cli scan -f 剧本.md
"""
from . import shield  # noqa: F401

__all__ = ["shield"]
