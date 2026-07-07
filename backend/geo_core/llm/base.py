from abc import ABC, abstractmethod
from typing import Optional

from geo_core.core.config import settings
from geo_core.llm.schemas import (
    LLMRequest,
    LLMResponse,
    EmbeddingRequest,
    EmbeddingResponse,
)


class BaseEngineAdapter(ABC):
    ENGINE_CODE: str = ""
    NAME: str = ""

    def __init__(self):
        self.api_key = ""
        self.base_url = ""
        self.default_model = ""
        self.timeout = settings.LLM_TIMEOUT
        self.max_retries = settings.LLM_MAX_RETRIES
        self._load_config()

    @abstractmethod
    def _load_config(self) -> None: ...

    @abstractmethod
    async def chat(self, request: LLMRequest) -> LLMResponse: ...

    @abstractmethod
    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse: ...

    def resolve_model(self, request_model: Optional[str]) -> str:
        return request_model or self.default_model
