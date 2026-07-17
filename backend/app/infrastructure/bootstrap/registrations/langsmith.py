"""LangSmith tracing 开关（骨架）。"""
from __future__ import annotations

import logging
import os

from fastapi import FastAPI

from app.core.config import settings

logger = logging.getLogger(__name__)


def init_langsmith(app: FastAPI) -> None:
    enabled = bool(settings.LANGCHAIN_TRACING_V2 and settings.LANGCHAIN_API_KEY)
    if enabled:
        os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
        os.environ.setdefault("LANGCHAIN_API_KEY", settings.LANGCHAIN_API_KEY)
        os.environ.setdefault("LANGCHAIN_PROJECT", settings.LANGCHAIN_PROJECT)
        os.environ.setdefault("LANGCHAIN_ENDPOINT", settings.LANGCHAIN_ENDPOINT)
        logger.info("LangSmith tracing enabled project=%s", settings.LANGCHAIN_PROJECT)
    app.state.resources["langsmith"] = {"enabled": enabled}
