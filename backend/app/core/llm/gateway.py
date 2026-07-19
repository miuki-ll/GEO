# =============================================================================
# LLM 网关 — 多引擎调度与容错
# 提供统一的 chat / embed 入口，自动按优先级尝试多个引擎，
# 失败时自动降级到下一个可用引擎，并累积全局用量统计
# =============================================================================

from typing import Any, Dict, List, Optional, Type

from app.core.config import settings
from app.core.logging_config import get_logger
from app.core.llm.base import BaseEngineAdapter
from app.core.llm.adapters import (
    DoubaoAdapter,
    DeepseekAdapter,
    KimiAdapter,
    WenxinAdapter,
)
from app.core.llm.schemas import (
    LLMRequest,
    LLMResponse,
    LLMUsage,
    EmbeddingRequest,
    EmbeddingResponse,
    SearchCitation,
    SearchRequest,
    SearchResponse,
)

logger = get_logger(__name__)


ENGINE_ORDER: List[str] = ["deepseek", "doubao", "kimi", "wenxin"]

_REGISTRY: Dict[str, BaseEngineAdapter] = {}
_ADAPTER_CLASSES: Dict[str, Type[BaseEngineAdapter]] = {
    DoubaoAdapter.ENGINE_CODE: DoubaoAdapter,
    DeepseekAdapter.ENGINE_CODE: DeepseekAdapter,
    KimiAdapter.ENGINE_CODE: KimiAdapter,
    WenxinAdapter.ENGINE_CODE: WenxinAdapter,
}


def get_adapter(engine: str) -> Optional[BaseEngineAdapter]:
    """获取指定引擎的适配器实例（懒加载，首次调用时创建并缓存）"""
    if engine not in _REGISTRY:
        cls = _ADAPTER_CLASSES.get(engine)
        if not cls:
            return None
        _REGISTRY[engine] = cls()
    return _REGISTRY[engine]


def list_available_engines() -> List[Dict]:
    """列出所有已注册引擎的状态（是否配置 API Key、是否为默认引擎等）"""
    out = []
    for code in ENGINE_ORDER:
        a = get_adapter(code)
        if not a:
            continue
        configured = bool(a.api_key)
        out.append(
            {
                "engine": code,
                "name": a.NAME,
                "default_model": a.default_model,
                "configured": configured,
                "is_default": settings.LLM_DEFAULT_ENGINE == code,
            }
        )
    return out


def _fallback_order(preferred: Optional[str]) -> List[str]:
    """生成引擎降级顺序：优先使用指定引擎，之后按默认顺序尝试"""
    order = list(ENGINE_ORDER)
    if preferred and preferred in order:
        order.remove(preferred)
        order.insert(0, preferred)
    default = settings.LLM_DEFAULT_ENGINE
    if default and default in order and order[0] != default:
        pass
    return order


_TOTAL_USAGE = LLMUsage()


def _accumulate(u: LLMUsage) -> None:
    """累积全局 Token 用量"""
    _TOTAL_USAGE.prompt_tokens += u.prompt_tokens
    _TOTAL_USAGE.completion_tokens += u.completion_tokens
    _TOTAL_USAGE.total_tokens += u.total_tokens


def get_total_usage() -> LLMUsage:
    """获取全局累计 Token 用量快照"""
    return LLMUsage(
        prompt_tokens=_TOTAL_USAGE.prompt_tokens,
        completion_tokens=_TOTAL_USAGE.completion_tokens,
        total_tokens=_TOTAL_USAGE.total_tokens,
    )


async def chat(request: LLMRequest) -> LLMResponse:
    """统一聊天入口：按优先级尝试各引擎，失败自动降级，全部失败则返回汇总错误"""
    preferred = request.engine or settings.LLM_DEFAULT_ENGINE
    order = _fallback_order(preferred)
    errors: List[str] = []
    retry_count = 0
    last_response: Optional[LLMResponse] = None
    for engine in order:
        adapter = get_adapter(engine)
        if not adapter:
            errors.append(f"[{engine}] no adapter")
            continue
        if not adapter.api_key:
            errors.append(f"[{engine}] not configured (missing API key)")
            continue
        one = request.model_copy(update={"engine": engine})
        resp = await adapter.chat(one)
        retry_count = resp.retry_count + (1 if last_response else 0)
        resp.retry_count = retry_count
        last_response = resp
        if resp.ok:
            _accumulate(resp.usage)
            return resp
        errors.append(f"[{engine}] {resp.error}")
    if last_response:
        last_response.error = " || ".join(errors)
        return last_response
    return LLMResponse(
        engine="none",
        model="none",
        content="",
        usage=LLMUsage(),
        error="所有引擎均调用失败：" + " ; ".join(errors),
        retry_count=retry_count,
        trace_id=request.trace_id,
    )


async def embed(request: EmbeddingRequest) -> EmbeddingResponse:
    """统一 Embedding 入口：按优先级尝试各引擎，失败自动降级"""
    preferred = request.engine or settings.LLM_DEFAULT_ENGINE
    order = _fallback_order(preferred)
    last: Optional[EmbeddingResponse] = None
    for engine in order:
        a = get_adapter(engine)
        if not a or not a.api_key:
            continue
        one = request.model_copy(update={"engine": engine})
        r = await a.embed(one)
        last = r
        if r.error is None and any(len(v) for v in r.vectors):
            _accumulate(r.usage)
            return r
    if last:
        return last
    return EmbeddingResponse(
        engine="none",
        model="none",
        vectors=[[] for _ in request.texts],
        usage=LLMUsage(),
        error="所有引擎 embedding 失败（或未配置）",
    )


def simple_prompt(
    prompt: str,
    *,
    system_prompt: Optional[str] = None,
    engine: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
    response_format: Optional[str] = None,
) -> LLMRequest:
    """快捷构造 LLMRequest：传入纯文本 prompt 即可，无需手动拼装 messages 列表"""
    from app.core.llm.schemas import ChatMessage

    msgs = []
    if system_prompt:
        msgs.append(ChatMessage(role="system", content=system_prompt))
    msgs.append(ChatMessage(role="user", content=prompt))
    return LLMRequest(
        engine=engine,
        messages=msgs,
        temperature=temperature,
        max_tokens=max_tokens,
        response_format=response_format,  # type: ignore[arg-type]
    )


async def search(request: SearchRequest) -> SearchResponse:
    """统一搜索入口 — 优先真联网搜索，全部失败则降级到 chat 模拟"""
    preferred = request.engine or settings.LLM_DEFAULT_ENGINE
    order = _fallback_order(preferred)
    errors: List[str] = []

    # 第一轮：尝试真实联网搜索
    for engine in order:
        adapter = get_adapter(engine)
        if not adapter:
            errors.append(f"[{engine}] no adapter")
            continue
        if not adapter.api_key:
            errors.append(f"[{engine}] not configured (missing API key)")
            continue
        resp = await adapter.search(request)
        if resp.ok:
            return resp
        errors.append(f"[{engine}] {resp.error}")

    # 第二轮：全部不支持 → 降级到 chat 模拟搜索
    for engine in order:
        adapter = get_adapter(engine)
        if not adapter or not adapter.api_key:
            continue
        try:
            chat_resp = await chat(simple_prompt(
                f"假设你在搜索引擎上搜索「{request.query}」，请模拟返回以下信息：\n"
                f"1. 针对这个搜索的 AI 总结回答\n"
                f"2. 这个问题的搜索结果中，哪些品牌/门店被提及\n"
                f"3. 竞品出现情况\n\n"
                f"请尽量详细回答，格式：\n"
                f"## AI 回答\n（模拟回答内容）\n\n"
                f"## 品牌提及\n（列出出现的品牌名称）\n\n"
                f"## 竞品情况\n（列出竞品名称和出现位置）",
                engine=engine,
                temperature=0.3,
                max_tokens=4096,
            ))
            if chat_resp.ok:
                return SearchResponse(
                    engine=engine,
                    model=chat_resp.model,
                    answer=chat_resp.content,
                    citations=[],
                    usage=chat_resp.usage,
                    latency_ms=chat_resp.latency_ms,
                    trace_id=request.trace_id,
                    extra={
                        **request.extra,
                        "simulated": True,
                        "search_engine": engine,
                        "fallback_reason": "所有引擎不支持真联网搜索，使用 chat 模拟",
                    },
                )
        except Exception as e:
            errors.append(f"[{engine}] chat fallback failed: {e}")

    # 彻底失败
    return SearchResponse(
        engine="none",
        model="none",
        error="所有搜索方式均失败：" + " ; ".join(errors),
        trace_id=request.trace_id,
    )


def simple_search(
    query: str,
    *,
    engine: Optional[str] = None,
    max_keywords: int = 3,
    limit: int = 10,
    timeout: Optional[int] = 200,
    trace_id: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> SearchRequest:
    """快捷构造 SearchRequest — 只需传入查询词即可"""
    return SearchRequest(
        engine=engine,
        query=query,
        max_keywords=max_keywords,
        limit=limit,
        timeout=timeout,
        trace_id=trace_id,
        extra=extra or {},
    )