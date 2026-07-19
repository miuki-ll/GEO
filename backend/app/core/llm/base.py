# =============================================================================
# LLM 引擎适配器抽象基类
# 定义所有厂商适配器必须实现的接口：配置加载、聊天、Embedding
# 子类只需实现 _load_config / chat / embed 三个抽象方法即可接入新引擎
# =============================================================================

from abc import ABC, abstractmethod
from typing import Optional

from app.core.config import settings
from app.core.llm.schemas import (
    LLMRequest,
    LLMResponse,
    EmbeddingRequest,
    EmbeddingResponse,
)


class BaseEngineAdapter(ABC):
    """LLM 引擎适配器抽象基类，所有厂商适配器继承此类"""

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
    def _load_config(self) -> None:
        """加载厂商配置（API Key、Base URL、默认模型等），子类必须实现"""
        ...

    @abstractmethod
    async def chat(self, request: LLMRequest) -> LLMResponse:
        """执行聊天补全请求，子类必须实现"""
        ...

    @abstractmethod
    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """执行文本向量化请求，子类必须实现"""
        ...

    async def search(self, request: "SearchRequest") -> "SearchResponse":
        """联网搜索 — 可选实现。仅豆包支持真联网搜索，其他引擎默认返回不支持"""
        from app.core.llm.schemas import SearchRequest, SearchResponse, SearchCitation
        return SearchResponse(
            engine=self.ENGINE_CODE,
            model="",
            error=f"[{self.ENGINE_CODE}] 不支持联网搜索",
        )

    def resolve_model(self, request_model: Optional[str]) -> str:
        """解析模型名称：请求指定则使用请求值，否则回退到默认模型"""
        return request_model or self.default_model