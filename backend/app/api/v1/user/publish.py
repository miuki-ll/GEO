from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any

from app.core.config import settings
from app.core.db import get_db
from app.api.common import get_current_active_user, require_role
from app.models import User
from app.schemas.business import (
    PublishTaskCreate,
    PublishTaskUpdate,
    PublishTaskResponse,
    PublishTaskListParams,
)
from app.schemas.common import PaginatedResponse, ApiResponse
from app.service import PublishService

router = APIRouter(prefix=f"{settings.API_V1_PREFIX}/user/publish", tags=["用户端·舱3·发布"])


@router.get("", response_model=PaginatedResponse)
def list_tasks(
    page: int = 1, page_size: int = 20,
    draft_id: Optional[int] = None, channel: Optional[str] = None,
    mode: Optional[str] = None, status: Optional[str] = None,
    user: User = Depends(get_current_active_user), db: Session = Depends(get_db),
):
    items, total = PublishService.list(
        db, user.enterprise_id,
        PublishTaskListParams(page=page, page_size=page_size, draft_id=draft_id, channel=channel, mode=mode, status=status),
    )
    return {"code": 0, "message": "", "data": {"items": [PublishTaskResponse.model_validate(i) for i in items], "total": total, "page": page, "page_size": page_size}}


@router.post("", response_model=PublishTaskResponse, summary="创建发布任务（auto/semi/guided 三模式）")
@require_role(["owner", "admin", "editor"])
def create_task(data: PublishTaskCreate, user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    try:
        return PublishService.create(db, user.enterprise_id, data)
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))


@router.get("/{tid}", response_model=PublishTaskResponse)
def get_task(tid: int, user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    t = PublishService.get(db, user.enterprise_id, tid)
    if not t:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "发布任务不存在")
    return t


@router.post("/{tid}/auto", response_model=PublishTaskResponse, summary="AUTO：托管模式立即发布")
@require_role(["owner", "admin", "editor"])
def run_auto(tid: int, user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    try:
        return PublishService.run_publish_auto(db, user.enterprise_id, tid)
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))


@router.post("/{tid}/semi", response_model=ApiResponse, summary="SEMI：半托管模式提交外链+发布单号，自动标记已发布")
@require_role(["owner", "admin", "editor"])
def run_semi(
    tid: int,
    payload: Dict[str, Any] = Body(..., embed=False),
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    try:
        url = payload.get("published_url") or payload.get("url")
        pub_id = payload.get("published_id")
        if not url:
            raise ValueError("SEMI 模式需字段 published_url（已发布外链），可选 published_id")
        t = PublishService.run_semi_submit(db, user.enterprise_id, tid, url, pub_id)
        return {"code": 0, "message": "", "data": PublishTaskResponse.model_validate(t).model_dump()}
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))


@router.post("/{tid}/retry", response_model=PublishTaskResponse, summary="GUIDED：导览模式重试或标记发布完成")
@require_role(["owner", "admin", "editor"])
def run_retry(
    tid: int,
    payload: Optional[Dict[str, Any]] = Body(default_factory=dict),
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    try:
        payload = payload or {}
        note = payload.get("note")
        completed = bool(payload.get("completed", True))  # 默认：运营提交就是"已手动完成"
        return PublishService.run_guided_retry(db, user.enterprise_id, tid, note=note, completed=completed)
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
