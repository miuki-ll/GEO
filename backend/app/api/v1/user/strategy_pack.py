from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.db import get_db
from app.api.common import get_current_active_user, require_role
from app.models import User
from app.schemas.business import (
    StrategyPackCreate,
    StrategyPackUpdate,
    StrategyPackListParams,
)
from app.schemas.common import PaginatedResponse, ApiResponse
from app.service import StrategyPackService

router = APIRouter(prefix=f"{settings.API_V1_PREFIX}/user/strategy-pack", tags=["用户端·舱2·方案包"])


class ConfirmBody(BaseModel):
    selected_scenarios: List[str] = Field(default_factory=list)
    channel_overrides: Optional[Dict[str, int]] = None
    persona_confirmed: bool = True
    competitor_confirmed: bool = True
    pack_id: Optional[int] = None


@router.get("", response_model=PaginatedResponse)
@require_role(["owner", "admin", "editor", "member", "viewer"])
def list_packs(
    page: int = 1, page_size: int = 20,
    status: Optional[str] = None,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    items, total = StrategyPackService.list(
        db, user.enterprise_id, StrategyPackListParams(page=page, page_size=page_size, status=status)
    )
    from app.schemas.business import StrategyPackResponse

    return {
        "code": 0,
        "message": "ok",
        "data": {
            "items": [StrategyPackResponse.model_validate(i) for i in items],
            "total": total,
            "page": page,
            "page_size": page_size,
        },
    }


@router.get("/draft")
def get_draft(user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    if settings.is_dev:
        from app.dev_seed import ensure_tenant_seed_data

        ensure_tenant_seed_data(db, user.enterprise_id, user.id)
    pack = StrategyPackService.ensure_draft_default(db, user.enterprise_id, user.id)
    return {"code": 0, "message": "ok", "data": StrategyPackService.draft_view(pack)}


@router.post("/draft")
@require_role(["owner", "admin", "editor"])
def upsert_draft(
    data: StrategyPackUpdate,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    pack = StrategyPackService.ensure_draft_default(db, user.enterprise_id, user.id)
    pack = StrategyPackService.update(db, user.enterprise_id, pack.id, data)
    return {"code": 0, "message": "ok", "data": StrategyPackService.draft_view(pack)}


@router.get("/{pack_id}")
def get_pack(pack_id: int, user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    p = StrategyPackService.get(db, user.enterprise_id, pack_id)
    if not p:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "方案包不存在")
    return {"code": 0, "message": "ok", "data": StrategyPackService.draft_view(p)}


@router.post("")
@require_role(["owner", "admin", "editor"])
def create_pack(
    data: StrategyPackCreate,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    pack = StrategyPackService.create(db, user.enterprise_id, data, user.id)
    return {"code": 0, "message": "ok", "data": StrategyPackService.draft_view(pack)}


@router.put("/{pack_id}")
@require_role(["owner", "admin", "editor"])
def update_pack(
    pack_id: int,
    data: StrategyPackUpdate,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    try:
        pack = StrategyPackService.update(db, user.enterprise_id, pack_id, data)
        return {"code": 0, "message": "ok", "data": StrategyPackService.draft_view(pack)}
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))


@router.post("/confirm", summary="闸门：确认方案包 + 勾选 scenario")
@require_role(["owner", "admin", "editor"])
def confirm_pack(
    body: ConfirmBody = Body(default_factory=ConfirmBody),
    pack_id: Optional[int] = Query(None, description="兼容旧查询参数"),
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    try:
        pid = body.pack_id or pack_id
        pack, extra = StrategyPackService.confirm(
            db,
            user.enterprise_id,
            user.id,
            pid,
            selected_scenarios=body.selected_scenarios,
            channel_overrides=body.channel_overrides,
        )
        data = StrategyPackService.draft_view(pack)
        data.update(extra)
        return {"code": 0, "message": "ok", "data": data}
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
