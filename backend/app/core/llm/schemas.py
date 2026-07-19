# =============================================================================
# LLM 请求/响应数据模型（Pydantic schemas）
# 定义与各厂商适配器交互的标准数据结构，包括聊天消息、用量统计、
# 请求参数、响应结果以及 Embedding 相关模型
# =============================================================================

from typing import List, Optional, Literal, Any, Dict
from pydantic import Field, BaseModel

from app.schemas import BaseSchema


class ChatMessage(BaseSchema):
    """单条聊天消息，包含角色、内容及可选名称"""
    role: Literal["system", "user", "assistant", "tool"]
    content: str
    name: Optional[str] = None


class LLMUsage(BaseSchema):
    """Token 用量统计，包含输入/输出/总量及可选费用（美分）"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_cents: Optional[float] = None


class LLMRequest(BaseSchema):
    """LLM 聊天请求参数，支持多引擎、温度、最大 token 数等通用控制"""
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
    """LLM 聊天响应，包含生成内容、用量、错误信息及性能指标"""
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
        """判断响应是否成功：无错误且内容非空"""
        return self.error is None and bool(self.content)


class EmbeddingRequest(BaseSchema):
    """Embedding 请求，支持批量文本向量化"""
    engine: Optional[str] = None
    texts: List[str]
    model: Optional[str] = None


class EmbeddingResponse(BaseSchema):
    """Embedding 响应，返回每条文本对应的向量及用量"""
    engine: str
    model: str
    vectors: List[List[float]]
    usage: LLMUsage
    error: Optional[str] = None


class SearchCitation(BaseSchema):
    """联网搜索返回的单条引用 — 豆包 Responses API 的 url_citation annotation"""
    url: str = ""
    title: str = ""
    summary: str = ""  # 豆包返回 1200+ 字摘要，足够分析痛点/场景/竞品
    site_name: str = ""
    publish_time: Optional[str] = None


class SearchRequest(BaseSchema):
    """联网搜索请求 — 指定引擎、查询词、超时等"""
    engine: Optional[str] = None     # 默认 doubao
    model: Optional[str] = None
    query: str = Field(..., min_length=1, max_length=500)  # 搜索查询
    max_keywords: int = Field(3, ge=1, le=10)              # web_search 关键词数
    limit: int = Field(10, ge=1, le=20)                    # 返回引用数上限
    timeout: Optional[int] = None                           # 联网搜索建议 ≥180s
    trace_id: Optional[str] = None
    extra: Dict[str, Any] = Field(default_factory=dict)


class SearchResponse(BaseSchema):
    """联网搜索响应 — AI 总结 + 引用列表 + 用量"""
    engine: str
    model: str
    answer: str = ""                                  # AI 对搜索结果的总结回答
    citations: List[SearchCitation] = Field(default_factory=list)
    usage: LLMUsage = Field(default_factory=LLMUsage)
    error: Optional[str] = None
    latency_ms: int = 0
    trace_id: Optional[str] = None
    extra: Dict[str, Any] = Field(default_factory=dict)

    @property
    def ok(self) -> bool:
        """判断搜索是否成功：无错误且有回答内容"""
        return self.error is None and bool(self.answer)