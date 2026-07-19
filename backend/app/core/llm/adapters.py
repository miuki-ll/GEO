# =============================================================================
# LLM 厂商适配器实现
# 包含 OpenAI 兼容协议的通用适配器（Doubao / DeepSeek / Kimi 复用）
# 以及文心一言独立适配器（使用百度自有 API 协议）
# =============================================================================

import json
import time
from typing import Optional, List

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.core.config import settings
from app.core.logging_config import get_logger
from app.core.llm.base import BaseEngineAdapter
from app.core.llm.schemas import (
    LLMRequest,
    LLMResponse,
    LLMUsage,
    ChatMessage,
    EmbeddingRequest,
    EmbeddingResponse,
)

logger = get_logger(__name__)


class _OpenAICompatAdapter(BaseEngineAdapter):
    """OpenAI 兼容协议通用适配器，Doubao / DeepSeek / Kimi 均复用此实现"""

    def _prepare_headers(self) -> dict:
        """构造 HTTP 请求头（Bearer 认证 + JSON Content-Type）"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _to_body(self, request: LLMRequest) -> dict:
        """将 LLMRequest 转换为 OpenAI 兼容的 JSON 请求体"""
        model = self.resolve_model(request.model)
        messages: List[dict] = []
        for m in request.messages:
            md = {"role": m.role, "content": m.content}
            if m.name:
                md["name"] = m.name
            messages.append(md)
        body = {
            "model": model,
            "messages": messages,
            "temperature": request.temperature,
            "top_p": request.top_p,
            "max_tokens": request.max_tokens,
            "frequency_penalty": request.frequency_penalty,
            "presence_penalty": request.presence_penalty,
        }
        if request.response_format == "json":
            body["response_format"] = {"type": "json_object"}
        if request.stop:
            body["stop"] = request.stop
        return body

    async def chat(self, request: LLMRequest) -> LLMResponse:
        """执行 OpenAI 兼容协议的聊天补全请求"""
        url = f"{self.base_url.rstrip('/')}/chat/completions"
        model = self.resolve_model(request.model)
        timeout = request.timeout or self.timeout
        t0 = time.perf_counter()
        try:
            raw = await self._do_request(
                url=url,
                headers=self._prepare_headers(),
                body=self._to_body(request),
                timeout=timeout,
                retries=request.retries or self.max_retries,
            )
            content = raw["choices"][0]["message"].get("content", "") or ""
            usage = raw.get("usage", {}) or {}
            finish = raw["choices"][0].get("finish_reason", "stop")
            latency_ms = int((time.perf_counter() - t0) * 1000)
            return LLMResponse(
                engine=self.ENGINE_CODE,
                model=raw.get("model", model),
                content=content,
                usage=LLMUsage(
                    prompt_tokens=usage.get("prompt_tokens", 0),
                    completion_tokens=usage.get("completion_tokens", 0),
                    total_tokens=usage.get("total_tokens", 0),
                ),
                finish_reason=finish,
                raw_response=raw,
                latency_ms=latency_ms,
                trace_id=request.trace_id,
            )
        except Exception as e:
            latency_ms = int((time.perf_counter() - t0) * 1000)
            logger.warning(
                "[%s] chat failed model=%s err=%s", self.ENGINE_CODE, model, e
            )
            return LLMResponse(
                engine=self.ENGINE_CODE,
                model=model,
                content="",
                usage=LLMUsage(),
                error=str(e),
                latency_ms=latency_ms,
                trace_id=request.trace_id,
            )

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=0.5, max=6),
        retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.ConnectError, httpx.TimeoutException)),
    )
    async def _do_request(self, url, headers, body, timeout, retries):
        """发送 HTTP POST 请求，带自动重试（指数退避，最多 3 次）"""
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(url, headers=headers, json=body)
            if r.status_code >= 400:
                try:
                    detail = r.json()
                except Exception:
                    detail = r.text
                raise httpx.HTTPStatusError(
                    f"HTTP {r.status_code}: {detail}", request=r.request, response=r
                )
            return r.json()

    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """执行 OpenAI 兼容协议的文本向量化请求"""
        url = f"{self.base_url.rstrip('/')}/embeddings"
        model = self.resolve_model(request.model)
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                r = await client.post(
                    url,
                    headers=self._prepare_headers(),
                    json={"model": model, "input": request.texts},
                )
                r.raise_for_status()
                payload = r.json()
            vectors: List[List[float]] = [d["embedding"] for d in payload["data"]]
            usage = payload.get("usage", {}) or {}
            return EmbeddingResponse(
                engine=self.ENGINE_CODE,
                model=payload.get("model", model),
                vectors=vectors,
                usage=LLMUsage(
                    prompt_tokens=usage.get("prompt_tokens", 0),
                    total_tokens=usage.get("total_tokens", 0),
                ),
            )
        except Exception as e:
            logger.warning("[%s] embed failed: %s", self.ENGINE_CODE, e)
            return EmbeddingResponse(
                engine=self.ENGINE_CODE,
                model=model,
                vectors=[[] for _ in request.texts],
                usage=LLMUsage(),
                error=str(e),
            )


class DoubaoAdapter(_OpenAICompatAdapter):
    """豆包（字节跳动）适配器，使用 OpenAI 兼容协议"""

    ENGINE_CODE = "doubao"
    NAME = "豆包"

    def _load_config(self) -> None:
        self.api_key = settings.LLM_DOUBAO_API_KEY
        self.base_url = settings.LLM_DOUBAO_BASE_URL
        self.default_model = getattr(settings, "LLM_DOUBAO_MODEL", "doubao-pro-32k")

    async def search(self, request: "SearchRequest") -> "SearchResponse":
        """豆包联网搜索 — 调用 Responses API + web_search tool"""
        from app.core.llm.schemas import SearchRequest, SearchResponse, SearchCitation, LLMUsage

        # 联网搜索必须用模型名，不能用 chat 的 default_model / ep-xxx
        model = request.model or "doubao-seed-2-1-pro-260628"
        url = f"{self.base_url.rstrip('/')}/responses"
        timeout = request.timeout or 200  # 联网搜索慢，默认 200s

        # 构造请求体 — Responses API 格式，不是 Chat Completions 格式
        body = {
            "model": model,
            "tools": [{"type": "web_search", "max_keyword": request.max_keywords, "limit": request.limit}],
            "input": [{"role": "user", "content": request.query}],
        }

        t0 = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                r = await client.post(
                    url,
                    headers=self._prepare_headers(),
                    json=body,
                )
                if r.status_code >= 400:
                    try:
                        detail = r.json()
                    except Exception:
                        detail = r.text
                    raise httpx.HTTPStatusError(
                        f"HTTP {r.status_code}: {detail}",
                        request=r.request,
                        response=r,
                    )
                payload = r.json()

            # 解析回答文本
            answer_parts: List[str] = []
            citations: List[SearchCitation] = []

            for output in payload.get("output", []):
                for content in output.get("content", []):
                    if content.get("text"):
                        answer_parts.append(content["text"])
                    for ann in content.get("annotations", []):
                        if ann.get("type") == "url_citation":
                            citations.append(SearchCitation(
                                url=ann.get("url", ""),
                                title=ann.get("title", ""),
                                summary=ann.get("summary", ""),
                                site_name=ann.get("site_name", ""),
                                publish_time=ann.get("publish_time"),
                            ))

            answer = "\n\n".join(answer_parts)
            usage_raw = payload.get("usage", {}) or {}
            latency_ms = int((time.perf_counter() - t0) * 1000)

            return SearchResponse(
                engine=self.ENGINE_CODE,
                model=payload.get("model", model),
                answer=answer,
                citations=citations,
                usage=LLMUsage(
                    prompt_tokens=usage_raw.get("input_tokens", 0),
                    completion_tokens=usage_raw.get("output_tokens", 0),
                    total_tokens=usage_raw.get("total_tokens", 0),
                ),
                latency_ms=latency_ms,
                trace_id=request.trace_id,
                extra=request.extra,
            )

        except Exception as e:
            latency_ms = int((time.perf_counter() - t0) * 1000)
            logger.warning("[doubao] search failed query=%s err=%s", request.query[:50], e)
            return SearchResponse(
                engine=self.ENGINE_CODE,
                model=model,
                error=str(e),
                latency_ms=latency_ms,
                trace_id=request.trace_id,
                extra=request.extra,
            )


class DeepseekAdapter(_OpenAICompatAdapter):
    """DeepSeek 适配器，使用 OpenAI 兼容协议"""

    ENGINE_CODE = "deepseek"
    NAME = "DeepSeek"

    def _load_config(self) -> None:
        self.api_key = settings.LLM_DEEPSEEK_API_KEY
        self.base_url = settings.LLM_DEEPSEEK_BASE_URL
        self.default_model = getattr(settings, "LLM_DEEPSEEK_MODEL", "deepseek-chat")


class KimiAdapter(_OpenAICompatAdapter):
    """Kimi（月之暗面）适配器，使用 OpenAI 兼容协议"""

    ENGINE_CODE = "kimi"
    NAME = "Kimi (月之暗面)"

    def _load_config(self) -> None:
        self.api_key = settings.LLM_KIMI_API_KEY
        self.base_url = settings.LLM_KIMI_BASE_URL
        self.default_model = getattr(settings, "LLM_KIMI_MODEL", "moonshot-v1-32k")


class WenxinAdapter(BaseEngineAdapter):
    """文心一言（百度）适配器，使用百度自有 API 协议（非 OpenAI 兼容）"""

    ENGINE_CODE = "wenxin"
    NAME = "文心一言"

    def _load_config(self) -> None:
        self.api_key = settings.LLM_WENXIN_API_KEY
        self.secret_key = settings.LLM_WENXIN_SECRET_KEY
        self.base_url = settings.LLM_WENXIN_BASE_URL.rstrip("/")
        self.default_model = getattr(settings, "LLM_WENXIN_MODEL", "ernie-3.5")
        self._token_cache: Optional[tuple] = None

    async def _get_access_token(self) -> str:
        """获取百度 OAuth 2.0 access_token，带缓存，过期前 5 分钟自动刷新"""
        if self._token_cache and self._token_cache[1] > time.time():
            return self._token_cache[0]
        url = f"{self.base_url}/oauth/2.0/token"
        params = {
            "grant_type": "client_credentials",
            "client_id": self.api_key,
            "client_secret": self.secret_key,
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r = await client.post(url, params=params)
            r.raise_for_status()
            data = r.json()
        token = data["access_token"]
        expires = time.time() + int(data.get("expires_in", 2592000)) - 300
        self._token_cache = (token, expires)
        return token

    def _model_path(self, model: str) -> str:
        """将模型别名映射为百度 API 实际模型路径"""
        mapping = {
            "ernie-3.5": "ernie-3.5-128k",
            "ernie-4": "ernie-4.0-8k",
            "ernie-lite": "ernie-lite-8k",
        }
        return mapping.get(model, model)

    async def chat(self, request: LLMRequest) -> LLMResponse:
        """执行文心一言聊天补全请求（百度自有协议）"""
        model = self.resolve_model(request.model)
        t0 = time.perf_counter()
        try:
            token = await self._get_access_token()
            url = f"{self.base_url}/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/{self._model_path(model)}?access_token={token}"
            messages = [{"role": m.role, "content": m.content} for m in request.messages]
            body = {
                "messages": messages,
                "temperature": request.temperature,
                "top_p": request.top_p,
                "max_output_tokens": min(request.max_tokens, 8192),
            }
            if request.stop:
                body["stop"] = request.stop
            if request.response_format == "json":
                body["response_format"] = "json_object"
            async with httpx.AsyncClient(timeout=request.timeout or self.timeout) as client:
                r = await client.post(url, json=body)
                if r.status_code >= 400:
                    raise Exception(f"HTTP {r.status_code}: {r.text}")
                payload = r.json()
            if "error_code" in payload and payload["error_code"]:
                raise Exception(f"{payload['error_code']}: {payload.get('error_msg')}")
            content = payload.get("result", "") or ""
            usage = payload.get("usage", {}) or {}
            latency = int((time.perf_counter() - t0) * 1000)
            return LLMResponse(
                engine=self.ENGINE_CODE,
                model=model,
                content=content,
                usage=LLMUsage(
                    prompt_tokens=usage.get("prompt_tokens", 0),
                    completion_tokens=usage.get("completion_tokens", 0),
                    total_tokens=usage.get("total_tokens", 0),
                ),
                finish_reason=payload.get("finish_reason", "stop"),
                raw_response=payload,
                latency_ms=latency,
                trace_id=request.trace_id,
            )
        except Exception as e:
            logger.warning("[wenxin] chat failed: %s", e)
            return LLMResponse(
                engine=self.ENGINE_CODE,
                model=model,
                content="",
                usage=LLMUsage(),
                error=str(e),
                latency_ms=int((time.perf_counter() - t0) * 1000),
                trace_id=request.trace_id,
            )

    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """执行文心一言文本向量化请求（百度自有协议，逐条请求）"""
        model = self.resolve_model(request.model)
        try:
            token = await self._get_access_token()
            url = f"{self.base_url}/rpc/2.0/ai_custom/v1/wenxinworkshop/embeddings/embedding-v1?access_token={token}"
            vectors: List[List[float]] = []
            total = 0
            for t in request.texts:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    r = await client.post(url, json={"input": t})
                    r.raise_for_status()
                    d = r.json()
                vectors.append(d.get("data", [{}])[0].get("embedding", []))
                total += int(d.get("usage", {}).get("prompt_tokens", 0))
            return EmbeddingResponse(
                engine=self.ENGINE_CODE,
                model=model,
                vectors=vectors,
                usage=LLMUsage(prompt_tokens=total, total_tokens=total),
            )
        except Exception as e:
            return EmbeddingResponse(
                engine=self.ENGINE_CODE,
                model=model,
                vectors=[[] for _ in request.texts],
                usage=LLMUsage(),
                error=str(e),
            )