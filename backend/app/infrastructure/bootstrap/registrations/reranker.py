"""Reranker 骨架（仅 worker）。"""
from __future__ import annotations

import logging

from fastapi import FastAPI

logger = logging.getLogger(__name__)


def init_reranker(app: FastAPI) -> None:
    # TODO: 接入真实 reranker；API 进程不应加载
    app.state.resources["reranker"] = {"loaded": False}
    logger.info("reranker init stub (not loaded)")
