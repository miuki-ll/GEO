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
    def _prepare_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _to_body(self, request: LLMRequest) -> dict:
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
    ENGINE_CODE = "doubao"
    NAME = "豆包"

    def _load_config(self) -> None:
        self.api_key = settings.LLM_DOUBAO_API_KEY
        self.base_url = settings.LLM_DOUBAO_BASE_URL
        self.default_model = getattr(settings, "LLM_DOUBAO_MODEL", "doubao-pro-32k")


class DeepseekAdapter(_OpenAICompatAdapter):
    ENGINE_CODE = "deepseek"
    NAME = "DeepSeek"

    def _load_config(self) -> None:
        self.api_key = settings.LLM_DEEPSEEK_API_KEY
        self.base_url = settings.LLM_DEEPSEEK_BASE_URL
        self.default_model = getattr(settings, "LLM_DEEPSEEK_MODEL", "deepseek-chat")


class KimiAdapter(_OpenAICompatAdapter):
    ENGINE_CODE = "kimi"
    NAME = "Kimi (月之暗面)"

    def _load_config(self) -> None:
        self.api_key = settings.LLM_KIMI_API_KEY
        self.base_url = settings.LLM_KIMI_BASE_URL
        self.default_model = getattr(settings, "LLM_KIMI_MODEL", "moonshot-v1-32k")


class WenxinAdapter(BaseEngineAdapter):
    ENGINE_CODE = "wenxin"
    NAME = "文心一言"

    def _load_config(self) -> None:
        self.api_key = settings.LLM_WENXIN_API_KEY
        self.secret_key = settings.LLM_WENXIN_SECRET_KEY
        self.base_url = settings.LLM_WENXIN_BASE_URL.rstrip("/")
        self.default_model = getattr(settings, "LLM_WENXIN_MODEL", "ernie-3.5")
        self._token_cache: Optional[tuple] = None

    async def _get_access_token(self) -> str:
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
        mapping = {
            "ernie-3.5": "ernie-3.5-128k",
            "ernie-4": "ernie-4.0-8k",
            "ernie-lite": "ernie-lite-8k",
        }
        return mapping.get(model, model)

    async def chat(self, request: LLMRequest) -> LLMResponse:
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
