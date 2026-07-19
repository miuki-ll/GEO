# =============================================================================
# LLM 多引擎模块 — 统一对外入口
# 导出数据模型（schemas）、适配器基类（base）、各厂商适配器（adapters）
# 以及网关便捷函数（gateway），业务代码只需 `from app.core.llm import chat` 即可调用
# =============================================================================

from app.core.llm.schemas import (
    ChatMessage,
    LLMUsage,
    LLMRequest,
    LLMResponse,
    EmbeddingRequest,
    EmbeddingResponse,
    SearchCitation,
    SearchRequest,
    SearchResponse,
)
from app.core.llm.base import BaseEngineAdapter
from app.core.llm.adapters import DoubaoAdapter, DeepseekAdapter, KimiAdapter, WenxinAdapter
from app.core.llm.gateway import (
    chat,
    embed,
    simple_prompt,
    search,
    simple_search,
    get_adapter,
    list_available_engines,
    get_total_usage,
)

__all__ = [
    "ChatMessage",
    "LLMUsage",
    "LLMRequest",
    "LLMResponse",
    "EmbeddingRequest",
    "EmbeddingResponse",
    "SearchCitation",
    "SearchRequest",
    "SearchResponse",
    "BaseEngineAdapter",
    "DoubaoAdapter",
    "DeepseekAdapter",
    "KimiAdapter",
    "WenxinAdapter",
    "chat",
    "embed",
    "simple_prompt",
    "search",
    "simple_search",
    "get_adapter",
    "list_available_engines",
    "get_total_usage",
]
