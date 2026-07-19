"""
集中管理 GEO 项目环境变量与全局配置。
不敏感的基础项直接写在本文件；密码、API Key、数据库连接等敏感信息放 .env。
"""

import os
from typing import List

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class Settings(BaseSettings):
    # --- 项目配置（硬编码）---
    APP_NAME: str = "GEO Platform"
    API_V1_PREFIX: str = "/api/v1"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    UPLOAD_DIR: str = os.path.join(BASE_DIR, "uploads")
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024
    RATE_LIMIT_PER_MINUTE: int = 60

    # --- Embedding 模型 ---
    EMBEDDING_MODEL_PATH: str = os.getenv("EMBEDDING_MODEL_PATH", "")

    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:8080",
    ]
   
    # 运行环境（可在 .env 覆盖：development / production）
    APP_ENV: str = os.getenv("APP_ENV", "development")
    APP_DEBUG: bool = os.getenv("APP_DEBUG", "true").lower() in ("1", "true", "yes")

    # 进程角色：api | worker | mcp（AutoInitManager 按角色过滤钩子）
    APP_PROCESS_ROLE: str = os.getenv("APP_PROCESS_ROLE", "api")
    PRELOAD_MODELS_ON_STARTUP: bool = os.getenv(
        "PRELOAD_MODELS_ON_STARTUP", "false"
    ).lower() in ("1", "true", "yes")

    # --- 安全 / JWT ---
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-in-production-please")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    # --- 数据库（MySQL，连接串在 .env）---
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://root@127.0.0.1:3306/geo_db?charset=utf8mb4",
    )
    DATABASE_ECHO: bool = False
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10

    # --- Redis / Celery ---
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CELERY_BROKER_URL: str = os.getenv(
        "CELERY_BROKER_URL",
        os.getenv("REDIS_URL", "redis://localhost:6379/1"),
    )
    CELERY_RESULT_BACKEND: str = os.getenv(
        "CELERY_RESULT_BACKEND", "redis://localhost:6379/2"
    )

    # --- LLM 多引擎：Key 在 .env，地址/模型名写死 ---
    LLM_DEFAULT_ENGINE: str = "deepseek"
    LLM_TIMEOUT: int = 60
    LLM_MAX_RETRIES: int = 3

    LLM_DOUBAO_API_KEY: str = os.getenv("LLM_DOUBAO_API_KEY", "")
    LLM_DOUBAO_BASE_URL: str = "https://ark.cn-beijing.volces.com/api/v3"
    LLM_DOUBAO_MODEL: str = "doubao-pro-32k"

    LLM_DEEPSEEK_API_KEY: str = os.getenv("LLM_DEEPSEEK_API_KEY", "")
    LLM_DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"
    LLM_DEEPSEEK_MODEL: str = "deepseek-chat"

    LLM_KIMI_API_KEY: str = os.getenv("LLM_KIMI_API_KEY", "")
    LLM_KIMI_BASE_URL: str = "https://api.moonshot.cn/v1"
    LLM_KIMI_MODEL: str = "moonshot-v1-32k"

    LLM_WENXIN_API_KEY: str = os.getenv("LLM_WENXIN_API_KEY", "")
    LLM_WENXIN_SECRET_KEY: str = os.getenv("LLM_WENXIN_SECRET_KEY", "")
    LLM_WENXIN_BASE_URL: str = "https://aip.baidubce.com"
    LLM_WENXIN_MODEL: str = "ernie-3.5"

    # --- 阿里云 OSS（敏感信息在 .env，留空则走本地上传）---
    OSS_ENDPOINT: str = os.getenv("OSS_ENDPOINT", "")
    OSS_ACCESS_KEY_ID: str = os.getenv("OSS_ACCESS_KEY_ID", "")
    OSS_ACCESS_KEY_SECRET: str = os.getenv("OSS_ACCESS_KEY_SECRET", "")
    OSS_BUCKET_NAME: str = os.getenv("OSS_BUCKET_NAME", "")

    # --- 可观测性 ---
    SENTRY_DSN: str = os.getenv("SENTRY_DSN", "")
    SENTRY_TRACES_SAMPLE_RATE: float = 0.2
    LANGCHAIN_TRACING_V2: bool = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() in (
        "1",
        "true",
        "yes",
    )
    LANGCHAIN_API_KEY: str = os.getenv("LANGCHAIN_API_KEY", "")
    LANGCHAIN_PROJECT: str = os.getenv("LANGCHAIN_PROJECT", "geo-dev")
    LANGCHAIN_ENDPOINT: str = "https://api.smith.langchain.com"

    # --- 平台管理端（Platform Admin，平台管理员）---
    # .env 示例：PLATFORM_ADMIN_EMAILS=admin@geo.com,ops@geo.com
    PLATFORM_ADMIN_EMAILS: str = os.getenv("PLATFORM_ADMIN_EMAILS", "")

    # --- MCP Server（Model Context Protocol，模型上下文协议）---
    MCP_ENABLED: bool = os.getenv("MCP_ENABLED", "false").lower() in ("1", "true", "yes")
    MCP_API_KEY: str = os.getenv("MCP_API_KEY", "")
    MCP_HOST: str = os.getenv("MCP_HOST", "0.0.0.0")
    MCP_PORT: int = int(os.getenv("MCP_PORT", "8100"))

    PROJECT_ROOT: str = BASE_DIR

    @property
    def platform_admin_email_set(self) -> set:
        return {e.strip().lower() for e in self.PLATFORM_ADMIN_EMAILS.split(",") if e.strip()}

    @property
    def is_dev(self) -> bool:
        return self.APP_ENV == "development"

    @property
    def is_prod(self) -> bool:
        return self.APP_ENV == "production"


settings = Settings()
