from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from geo_core.core.db import get_db
from geo_core.api.v1.common import get_current_active_user, require_role
from geo_core.models import User
from geo_core.schemas.business import (
    AgentTaskCreate,
    AgentTaskUpdate,
    AgentTaskResponse,
    AgentTaskListParams,
)
from geo_core.schemas.common import PaginatedResponse, ApiResponse
from geo_core.services import AgentTaskService

router = APIRouter(tags=["Agent 任务 L1-L3"])


@router.get("", response_model=PaginatedResponse)
def list_tasks(
    page: int = 1, page_size: int = 20,
    task_type: Optional[str] = None, status: Optional[str] = None,
    user: User = Depends(get_current_active_user), db: Session = Depends(get_db),
):
    items, total = AgentTaskService.list(
        db, user.enterprise_id,
        AgentTaskListParams(page=page, page_size=page_size, task_type=task_type, status=status),
    )
    return {"code": 0, "message": "", "data": {"items": [AgentTaskResponse.model_validate(i) for i in items], "total": total, "page": page, "page_size": page_size}}


@router.post("", response_model=AgentTaskResponse, summary="自定义触发 LangGraph L2 graph")
@require_role(["owner", "admin", "editor"])
def create_task(data: AgentTaskCreate, user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    return AgentTaskService.create(db, user.enterprise_id, data)


@router.get("/{tid}", response_model=AgentTaskResponse)
def get_task(tid: int, user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    t = AgentTaskService.get(db, user.enterprise_id, tid)
    if not t:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Agent 任务不存在")
    return t


@router.patch("/{tid}", response_model=AgentTaskResponse)
@require_role(["owner", "admin", "editor"])
def update_task(tid: int, data: AgentTaskUpdate, user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    t = AgentTaskService.update_progress(db, user.enterprise_id, tid, **data.model_dump(exclude_unset=True))
    if not t:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Agent 任务不存在")
    return t
