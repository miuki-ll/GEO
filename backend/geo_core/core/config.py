from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
from pydantic import Field, AnyHttpUrl, SecretStr


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    APP_NAME: str = "GEO Platform"
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    API_V1_PREFIX: str = "/api/v1"
    SECRET_KEY: SecretStr = SecretStr("change-me-in-production-please")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    DATABASE_URL: str = "sqlite:///geo_dev.db"
    DATABASE_ECHO: bool = False
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10

    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    LLM_DOUBAO_API_KEY: str = ""
    LLM_DOUBAO_BASE_URL: str = "https://ark.cn-beijing.volces.com/api/v3"
    LLM_DOUBAO_MODEL: str = "doubao-pro-32k"
    LLM_DEEPSEEK_API_KEY: str = ""
    LLM_DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"
    LLM_DEEPSEEK_MODEL: str = "deepseek-chat"
    LLM_KIMI_API_KEY: str = ""
    LLM_KIMI_BASE_URL: str = "https://api.moonshot.cn/v1"
    LLM_KIMI_MODEL: str = "moonshot-v1-32k"
    LLM_WENXIN_API_KEY: str = ""
    LLM_WENXIN_SECRET_KEY: str = ""
    LLM_WENXIN_BASE_URL: str = "https://aip.baidubce.com"
    LLM_WENXIN_MODEL: str = "ernie-3.5"
    LLM_DEFAULT_ENGINE: str = "deepseek"
    LLM_TIMEOUT: int = 60
    LLM_MAX_RETRIES: int = 3

    OSS_ENDPOINT: str = ""
    OSS_ACCESS_KEY_ID: str = ""
    OSS_ACCESS_KEY_SECRET: str = ""
    OSS_BUCKET_NAME: str = ""

    SENTRY_DSN: str = ""
    LANGSMITH_API_KEY: str = ""
    LANGSMITH_TRACING: bool = False

    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:5173", "http://localhost:8080"]
    )
    RATE_LIMIT_PER_MINUTE: int = 60

    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024

    @property
    def is_dev(self) -> bool:
        return self.APP_ENV == "development"

    @property
    def is_prod(self) -> bool:
        return self.APP_ENV == "production"


settings = Settings()
