from typing import List, Optional, Literal, Any, Dict
from pydantic import Field, BaseModel

from geo_core.schemas import BaseSchema


class ChatMessage(BaseSchema):
    role: Literal["system", "user", "assistant", "tool"]
    content: str
    name: Optional[str] = None


class LLMUsage(BaseSchema):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_cents: Optional[float] = None


class LLMRequest(BaseSchema):
    engine: Optional[str] = None
    model: Optional[str] = None
    messages: List[ChatMessage] = Field(..., min_length=1)
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    top_p: float = Field(1.0, ge=0.0, le=1.0)
    max_tokens: int = Field(2048, ge=1, le=128000)
    frequency_penalty: float = Field(0.0, ge=-2.0, le=2.0)
    presence_penalty: float = Field(0.0, ge=-2.0, le=2.0)
    response_format: Optional[Literal["json", "text"]] = None
    stop: Optional[List[str]] = None
    timeout: Optional[int] = None
    retries: Optional[int] = None
    trace_id: Optional[str] = None
    extra: Dict[str, Any] = Field(default_factory=dict)


class LLMResponse(BaseSchema):
    engine: str
    model: str
    content: str
    usage: LLMUsage
    finish_reason: str = "stop"
    raw_response: Any = None
    error: Optional[str] = None
    retry_count: int = 0
    latency_ms: int = 0
    trace_id: Optional[str] = None

    @property
    def ok(self) -> bool:
        return self.error is None and bool(self.content)


class EmbeddingRequest(BaseSchema):
    engine: Optional[str] = None
    texts: List[str]
    model: Optional[str] = None


class EmbeddingResponse(BaseSchema):
    engine: str
    model: str
    vectors: List[List[float]]
    usage: LLMUsage
    error: Optional[str] = None
