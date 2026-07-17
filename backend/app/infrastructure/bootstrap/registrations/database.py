"""ORM 加载与表结构 ensure。"""
from __future__ import annotations

import logging
import os

from fastapi import FastAPI

from app.core.config import settings

logger = logging.getLogger(__name__)


def init_database(app: FastAPI) -> None:
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    from app.core.db import Base, engine
    from app.models import (  # noqa: F401
        audit,
        auth,
        content,
        events,
        kb,
        monitor,
        ops,
        publish,
        strategy,
    )

    try:
        Base.metadata.create_all(bind=engine)
        logger.info("DB schema ensure_all_tables OK")
        app.state.resources["database"] = {"status": "ok"}
    except Exception as exc:
        # 与改造前 lifespan 行为一致：连不上库不阻断进程（critical 由 register 决定）
        logger.warning("DB create_all skipped/warn: %s", exc)
        app.state.resources["database"] = {"status": "degraded", "error": str(exc)}
