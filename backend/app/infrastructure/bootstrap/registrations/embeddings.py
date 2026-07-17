"""Embedding 预热骨架（PRELOAD 开启时再接真实逻辑）。"""
from __future__ import annotations

import logging

from fastapi import FastAPI

from app.core.config import settings
from app.infrastructure.bootstrap.init_manager import auto_init

logger = logging.getLogger(__name__)


async def _warmup_embeddings() -> None:
    # TODO: 接入 app.core.embedding 真实预热
    logger.info("embeddings warmup stub done")


def init_embeddings(app: FastAPI) -> None:
    if not settings.PRELOAD_MODELS_ON_STARTUP:
        app.state.resources["embeddings"] = {"preloaded": False}
        return

    auto_init.schedule_background(_warmup_embeddings())
    app.state.resources["embeddings"] = {"preloaded": "background"}
