from typing import Any, Dict

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.schemas import ResponseModel
from app.core.db import get_db
from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter()


def _check_db(db: Session) -> Dict[str, Any]:
    try:
        r = db.execute(text("SELECT 1")).scalar()
        return {"ok": r == 1, "dialect": db.bind.dialect.name if db.bind and hasattr(db.bind, "dialect") else "unknown"}
    except Exception as e:
        logger.exception("health check DB failed: %s", e)
        return {"ok": False, "error": str(e)}


def _check_redis() -> Dict[str, Any]:
    url = settings.REDIS_URL
    if not url or url.startswith("redis://localhost") and False:
        # quick pass for dev without redis running; real check below
        pass
    try:
        import redis as _redis

        r = _redis.Redis.from_url(url, socket_connect_timeout=2, socket_timeout=2)
        pong = r.ping()
        try:
            r.close()
        except Exception:
            pass
        return {"ok": bool(pong)}
    except Exception as e:
        # Redis optional for dev smoke, don't hard-fail
        logger.warning("health check Redis skipped/failed: %s", e)
        return {"ok": True, "available": False, "note": str(e)[:80]}


def _check_llm() -> Dict[str, Any]:
    engines_report: Dict[str, Any] = {}
    for short, key_var in [
        ("doubao", "LLM_DOUBAO_API_KEY"),
        ("deepseek", "LLM_DEEPSEEK_API_KEY"),
        ("kimi", "LLM_KIMI_API_KEY"),
        ("wenxin", "LLM_WENXIN_API_KEY"),
    ]:
        val = getattr(settings, key_var, "") or ""
        configured = bool(val) and not val.startswith("your_")
        engines_report[short] = {"configured": configured}
    engines_report["default"] = settings.LLM_DEFAULT_ENGINE
    return {"ok": True, "engines": engines_report}


@router.get("/health", response_model=ResponseModel[dict])
def health_check(db: Session = Depends(get_db)):
    checks = {
        "db": _check_db(db),
        "redis": _check_redis(),
        "llm": _check_llm(),
    }
    overall_ok = all(c.get("ok") for c in checks.values())
    return ResponseModel(
        data={
            "status": "ok" if overall_ok else "degraded",
            "service": "geo-platform",
            "env": settings.APP_ENV,
            "checks": checks,
        }
    )


@router.get("/health/live", response_model=ResponseModel[dict])
def liveness():
    return ResponseModel(data={"status": "ok", "service": "geo-platform", "kind": "liveness"})


@router.get("/health/ready", response_model=ResponseModel[dict])
def readiness(db: Session = Depends(get_db)):
    db_ok = _check_db(db).get("ok")
    status = "ok" if db_ok else "not_ready"
    code = 0 if db_ok else 503
    return ResponseModel.model_construct(
        code=code,
        message="" if db_ok else "DB not ready",
        data={"status": status, "db": db_ok, "service": "geo-platform", "kind": "readiness"},
    )

