from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.config import settings
from app.core.db import get_db
from app.api.common import get_current_active_user, require_role
from app.models import User
from app.schemas.business import (
    StrategyPackCreate,
    StrategyPackUpdate,
    StrategyPackResponse,
    StrategyPackListParams,
)
from app.schemas.common import PaginatedResponse, ApiResponse
from app.service import StrategyPackService

router = APIRouter(prefix=f"{settings.API_V1_PREFIX}/user/strategy-pack", tags=["用户端·舱2·方案包"])


@router.get("", response_model=PaginatedResponse)
@require_role(["owner", "admin", "editor", "member", "viewer"])
def list_packs(
    page: int = 1, page_size: int = 20,
    status: Optional[str] = None,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    items, total = StrategyPackService.list(db, user.enterprise_id, StrategyPackListParams(page=page, page_size=page_size, status=status))
    return {"code": 0, "message": "", "data": {"items": [StrategyPackResponse.model_validate(i) for i in items], "total": total, "page": page, "page_size": page_size}}


@router.get("/draft", response_model=StrategyPackResponse)
def get_draft(user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    pack = StrategyPackService.ensure_draft_default(db, user.enterprise_id, user.id)
    return pack


@router.post("/draft", response_model=StrategyPackResponse)
@require_role(["owner", "admin", "editor"])
def upsert_draft(data: StrategyPackUpdate, user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    pack = StrategyPackService.ensure_draft_default(db, user.enterprise_id, user.id)
    return StrategyPackService.update(db, user.enterprise_id, pack.id, data)


@router.get("/{pack_id}", response_model=StrategyPackResponse)
def get_pack(pack_id: int, user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    p = StrategyPackService.get(db, user.enterprise_id, pack_id)
    if not p:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "方案包不存在")
    return p


@router.post("", response_model=StrategyPackResponse)
@require_role(["owner", "admin", "editor"])
def create_pack(data: StrategyPackCreate, user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    return StrategyPackService.create(db, user.enterprise_id, data, user.id)


@router.put("/{pack_id}", response_model=StrategyPackResponse)
@require_role(["owner", "admin", "editor"])
def update_pack(pack_id: int, data: StrategyPackUpdate, user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    try:
        return StrategyPackService.update(db, user.enterprise_id, pack_id, data)
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))


@router.post("/confirm", response_model=StrategyPackResponse, summary="闸门 2：确认方案包")
@require_role(["owner", "admin", "editor"])
def confirm_pack(
    pack_id: Optional[int] = Query(None, description="若未传则确认最新方案包"),
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    try:
        return StrategyPackService.confirm(db, user.enterprise_id, user.id, pack_id)
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
