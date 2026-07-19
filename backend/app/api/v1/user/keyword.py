"""关键词词库路由 — 四源汇聚 + CRUD + 四层汇总。"""
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional

from app.core.config import settings
from app.core.db import get_db
from app.api.common import get_current_active_user
from app.models import User
from app.schemas.keyword import (
    KeywordCreate,
    KeywordUpdate,
    KeywordResponse,
    KeywordGenerateRequest,
    KeywordGenerateResponse,
)
from app.service.keyword_service import KeywordService
from app.service.agent_task_service import AgentTaskService
from app.schemas.business import AgentTaskCreate
from app.schemas.common import ApiResponse

router = APIRouter(prefix=f"{settings.API_V1_PREFIX}/user/keywords", tags=["用户端·舱1·词库"])


# ── Generate（Celery 异步）──

@router.post("/generate", response_model=KeywordGenerateResponse, summary="触发四源汇聚+LLM分类（异步）")
def keyword_generate(
    body: KeywordGenerateRequest,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """触发词库生成任务。四源汇聚 → LLM 四层分类 → 批量写入。"""
    from app.models import Enterprise

    ent = db.query(Enterprise).filter(Enterprise.id == user.enterprise_id).first()
    city = (ent.settings or {}).get("city", "") if ent else ""

    # 创建 AgentTask
    task = AgentTaskService.create(
        db, user.enterprise_id,
        AgentTaskCreate(
            task_type="keyword_generate",
            graph_name="keyword",
            input_data={"enterprise_name": ent.name if ent else "", "city": city},
        ),
    )

    # 发 Celery 任务
    from app.tasks.all_tasks import keyword_generate as _celery_task
    _celery_task.delay(
        enterprise_id=user.enterprise_id,
        enterprise_name=ent.name if ent else "",
        city=city,
        task_id=task.id,
    )

    return KeywordGenerateResponse(task_id=task.id)


# ── SSE 进度 ──

@router.get("/events/{task_id}", summary="SSE 词库生成进度推送")
async def keyword_events(
    task_id: int,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """SSE 端点 — 实时推送词库生成进度。"""
    from app.core.sse import subscribe_progress

    t = AgentTaskService.get(db, user.enterprise_id, task_id)
    if not t:
        raise HTTPException(status_code=404, detail="任务不存在")

    return StreamingResponse(
        subscribe_progress(task_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ── 四层汇总（放在 /{keyword_id} 之前，避免路径冲突）──

@router.get("/summary/layers", response_model=ApiResponse, summary="四层汇总")
def keyword_layer_summary(
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """返回四层关键词汇总，供 B 侧方案包 E 区使用。"""
    layers = KeywordService.get_layer_summary(db, user.enterprise_id)
    return {"code": 0, "message": "", "data": layers}


# ── CRUD ──

@router.get("", response_model=ApiResponse, summary="关键词列表（分页+筛选）")
def keyword_list(
    layer: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    keyword_type: Optional[str] = Query(None),
    pool_hint: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """分页查询关键词，支持按 layer/source/type/pool 筛选 + phrase 模糊搜索。"""
    result = KeywordService.list_keywords(
        db, user.enterprise_id,
        layer=layer, source=source, keyword_type=keyword_type,
        pool_hint=pool_hint, search=search,
        page=page, page_size=page_size,
    )
    return {
        "code": 0, "message": "",
        "data": {
            "items": [KeywordResponse.model_validate(r).model_dump() for r in result["items"]],
            "total": result["total"],
            "page": result["page"],
            "page_size": result["page_size"],
        },
    }


@router.post("", response_model=ApiResponse, summary="手动添加关键词")
def keyword_create(
    body: KeywordCreate,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    kw = KeywordService.create_keyword(db, user.enterprise_id, body.model_dump())
    return {"code": 0, "message": "", "data": KeywordResponse.model_validate(kw).model_dump()}


@router.put("/{keyword_id}", response_model=ApiResponse, summary="编辑关键词")
def keyword_update(
    keyword_id: int,
    body: KeywordUpdate,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    kw = KeywordService.update_keyword(db, user.enterprise_id, keyword_id, body.model_dump(exclude_none=True))
    if not kw:
        raise HTTPException(status_code=404, detail="关键词不存在")
    return {"code": 0, "message": "", "data": KeywordResponse.model_validate(kw).model_dump()}


@router.delete("/{keyword_id}", response_model=ApiResponse, summary="删除关键词")
def keyword_delete(
    keyword_id: int,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    ok = KeywordService.delete_keyword(db, user.enterprise_id, keyword_id)
    if not ok:
        raise HTTPException(status_code=404, detail="关键词不存在")
    return {"code": 0, "message": "已删除", "data": None}
