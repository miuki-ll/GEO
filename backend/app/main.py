"""FastAPI 应用入口 — CORS、异常处理、lifespan、create_app。"""

from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging_config import get_logger
from app.api import health_router, v1_router

logger = get_logger(__name__)


def setup_cors(app: FastAPI) -> None:
    """配置 CORS（跨域资源共享）— 允许前端域名调后端 API。"""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,  # 白名单来自配置，非 "*"
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],  # 前端可读到请求追踪 ID
    )


def setup_exception_handlers(app: FastAPI) -> None:
    """统一异常响应格式，避免前端拿到五花八门的错误结构。"""

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        # 请求体/参数校验失败 → 422，附带字段级错误列表
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
        # 未捕获异常 → 500；生产环境不把异常细节暴露给客户端
        logger.exception("Unhandled exception on %s: %s", request.url, exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"code": 500, "message": f"服务器内部错误: {exc}" if settings.is_dev else "服务器内部错误"},
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 注意：勿写 `import app.xxx`（会覆盖参数名 app → 变成包模块）
    import importlib

    from app.infrastructure.bootstrap.init_manager import auto_init

    importlib.import_module("app.infrastructure.bootstrap.registrations.register_all")

    logger.info(
        "Starting GEO Platform (env=%s role=%s)...",
        settings.APP_ENV,
        settings.APP_PROCESS_ROLE,
    )
    await auto_init.start(app)
    yield
    await auto_init.stop()
    logger.info("GEO Platform shutting down...")


def create_app() -> FastAPI:
    """
    应用工厂（factory）— 组装完整 app 后返回。
    好处：测试时可多次 create_app()，不必依赖全局单例细节。
    """
    app = FastAPI(
        title=settings.APP_NAME,
        description="GEO 多企业 AI 可见度运营平台 — 后端 API",
        version="1.0.0",
        debug=settings.APP_DEBUG,
        lifespan=lifespan,
    )
    setup_cors(app)
    setup_exception_handlers(app)

    # 健康检查（不进版本前缀）+ 业务 API v1 总路由
    app.include_router(health_router, prefix="", tags=["系统"])
    app.include_router(v1_router)  # 聚合点：app/api/v1/__init__.py

    from app.api.v1.user.keyword import router as keyword_router
    app.include_router(keyword_router)

    # MCP（Model Context Protocol，给 AI 工具调用的接口）— 配置开关控制
    if settings.MCP_ENABLED:
        from mcp_server.http_router import router as mcp_http_router

        app.include_router(mcp_http_router)

    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        # 每个请求生成短 ID，写入 request.state 和响应头，方便日志串联排查
        import uuid as _uuid

        rid = _uuid.uuid4().hex[:12]
        request.state.request_id = rid
        response = await call_next(request)
        response.headers["X-Request-ID"] = rid
        return response

    return app


# Uvicorn / 进程入口加载的就是这个 app 实例
app = create_app()
