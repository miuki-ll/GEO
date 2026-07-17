"""Sentry 初始化（生产可选）。"""
from __future__ import annotations

import logging

from fastapi import FastAPI

from app.core.config import settings

logger = logging.getLogger(__name__)


def init_sentry(app: FastAPI) -> None:
    if not (settings.SENTRY_DSN and settings.is_prod):
        app.state.resources["sentry"] = {"enabled": False}
        return

    import sentry_sdk

    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
    )
    app.state.resources["sentry"] = {"enabled": True}
    logger.info("Sentry initialized")
