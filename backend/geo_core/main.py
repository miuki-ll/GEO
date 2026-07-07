from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from geo_core.core.config import settings
from geo_core.core.logging_config import get_logger
from geo_core.api import health_router, v1_router

logger = get_logger(__name__)


def setup_cors(app: FastAPI) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )


def setup_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        errors = []
        for err in exc.errors():
            loc = ".".join(str(p) for p in err.get("loc", []))
            errors.append(f"[{loc}] {err.get('msg', '')}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={
                "code": 422,
                "message": "请求参数校验失败",
                "errors": errors,
            },
        )

    @app.exception_handler(Exception)
    async def base_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled exception on %s: %s", request.url, exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"code": 500, "message": f"服务器内部错误: {exc}" if settings.is_dev else "服务器内部错误"},
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting GEO Platform (env=%s)...", settings.APP_ENV)
    from geo_core.core.db import engine
    from geo_core.models import kb, tenant, business  # noqa: F401 - ensure models registered
    from geo_core.core.db import Base
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("DB schema ensure_all_tables OK")
    except Exception as e:
        logger.warning("DB create_all skipped/warn: %s", e)
    if settings.SENTRY_DSN and settings.is_prod:
        try:
            import sentry_sdk

            sentry_sdk.init(dsn=settings.SENTRY_DSN, traces_sample_rate=0.2)
        except Exception as e:
            logger.warning("Sentry init failed: %s", e)
    yield
    logger.info("GEO Platform shutting down...")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        description="GEO 多企业 AI 可见度运营平台 — 后端 API",
        version="1.0.0",
        debug=settings.APP_DEBUG,
        lifespan=lifespan,
    )
    setup_cors(app)
    setup_exception_handlers(app)

    app.include_router(health_router, prefix="", tags=["系统"])
    app.include_router(v1_router, prefix=settings.API_V1_PREFIX)

    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        import uuid as _uuid

        rid = _uuid.uuid4().hex[:12]
        request.state.request_id = rid
        response = await call_next(request)
        response.headers["X-Request-ID"] = rid
        return response

    return app


app = create_app()
