"""LangGraph 资源骨架（仅 worker 角色注册加载）。"""
from __future__ import annotations

import logging

from fastapi import FastAPI

logger = logging.getLogger(__name__)


async def init_langgraph(app: FastAPI) -> None:
    # TODO: 接入 agents graphs 进程内句柄
    app.state.resources["langgraph"] = {"status": "stub"}
    logger.info("langgraph init stub")


async def stop_langgraph(app: FastAPI) -> None:
    if app is not None and hasattr(app.state, "resources"):
        app.state.resources.pop("langgraph", None)
    logger.info("langgraph stop stub")
