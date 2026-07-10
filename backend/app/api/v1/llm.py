"""共用 · LLM Gateway（大模型网关）— 对齐 TalentFlow skills/tasks 等横切能力，挂 v1 根目录。"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import require_role
from app.core.config import settings
from app.core.llm.gateway import chat, embed, list_available_engines, get_total_usage
from app.core.llm.schemas import (
    LLMRequest,
    LLMResponse,
    LLMUsage,
    EmbeddingRequest,
    EmbeddingResponse,
)
from app.schemas import ResponseModel

router = APIRouter(prefix=f"{settings.API_V1_PREFIX}/llm", tags=["LLM Gateway"])


@router.get("/engines", response_model=ResponseModel[List[dict]])
def get_engines():
    """列出可用 LLM 引擎（豆包/DeepSeek/Kimi/文心等）。"""
    return ResponseModel(data=list_available_engines())


@router.get("/usage", response_model=ResponseModel[LLMUsage])
def get_usage(_=Depends(require_role("owner", "admin"))):
    """当前企业 Token 用量统计（需 owner/admin）。"""
    return ResponseModel(data=get_total_usage())


@router.post("/chat", response_model=ResponseModel[LLMResponse])
async def run_chat(request: LLMRequest, _=Depends(require_role("owner", "admin", "editor"))):
    """调用 LLM 对话接口。"""
    resp = await chat(request)
    if not resp.ok and not resp.content:
        raise HTTPException(status_code=502, detail=resp.error or "LLM 调用失败")
    return ResponseModel(data=resp)


@router.post("/embeddings", response_model=ResponseModel[EmbeddingResponse])
async def run_embed(request: EmbeddingRequest, _=Depends(require_role("owner", "admin", "editor"))):
    """调用 Embedding（向量嵌入）接口。"""
    resp = await embed(request)
    if resp.error and not any(len(v) for v in resp.vectors):
        raise HTTPException(status_code=502, detail=resp.error)
    return ResponseModel(data=resp)
