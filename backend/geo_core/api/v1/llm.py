from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException

from geo_core.api.deps import require_role
from geo_core.schemas import ResponseModel
from geo_core.llm.schemas import (
    LLMRequest,
    LLMResponse,
    LLMUsage,
    EmbeddingRequest,
    EmbeddingResponse,
)
from geo_core.llm.gateway import chat, embed, list_available_engines, get_total_usage

router = APIRouter(tags=["LLM Gateway"])


@router.get("/engines", response_model=ResponseModel[List[dict]])
def get_engines():
    return ResponseModel(data=list_available_engines())


@router.get("/usage", response_model=ResponseModel[LLMUsage])
def get_usage(current_user=Depends(require_role("owner", "admin"))):
    return ResponseModel(data=get_total_usage())


@router.post("/chat", response_model=ResponseModel[LLMResponse])
async def run_chat(request: LLMRequest, _=Depends(require_role("owner", "admin", "editor"))):
    resp = await chat(request)
    if not resp.ok and not resp.content:
        raise HTTPException(status_code=502, detail=resp.error or "LLM 调用失败")
    return ResponseModel(data=resp)


@router.post("/embeddings", response_model=ResponseModel[EmbeddingResponse])
async def run_embed(request: EmbeddingRequest, _=Depends(require_role("owner", "admin", "editor"))):
    resp = await embed(request)
    if resp.error and not any(len(v) for v in resp.vectors):
        raise HTTPException(status_code=502, detail=resp.error)
    return ResponseModel(data=resp)
