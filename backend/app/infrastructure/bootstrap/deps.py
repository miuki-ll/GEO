"""FastAPI Depends 读取 app.state.resources。"""
from __future__ import annotations

from typing import Any

from fastapi import Request


def get_resources(request: Request) -> dict[str, Any]:
    return getattr(request.app.state, "resources", {}) or {}
