from typing import Dict, List, Optional, Type

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
    if engine not in _REGISTRY:
        cls = _ADAPTER_CLASSES.get(engine)
        if not cls:
            return None
        _REGISTRY[engine] = cls()
    return _REGISTRY[engine]


def list_available_engines() -> List[Dict]:
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
    _TOTAL_USAGE.prompt_tokens += u.prompt_tokens
    _TOTAL_USAGE.completion_tokens += u.completion_tokens
    _TOTAL_USAGE.total_tokens += u.total_tokens


def get_total_usage() -> LLMUsage:
    return LLMUsage(
        prompt_tokens=_TOTAL_USAGE.prompt_tokens,
        completion_tokens=_TOTAL_USAGE.completion_tokens,
        total_tokens=_TOTAL_USAGE.total_tokens,
    )


async def chat(request: LLMRequest) -> LLMResponse:
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
