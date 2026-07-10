"""共用 · Agent 异步任务 — 对齐 TalentFlow tasks.py，内容生产/监测/迭代等均可查询。"""
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.agents import list_graphs, run_graph
from app.api.common import get_current_active_user, require_role
from app.core.config import settings
from app.core.db import get_db
from app.models import User
from app.schemas.business import (
    AgentTaskCreate,
    AgentTaskListParams,
    AgentTaskResponse,
    AgentTaskUpdate,
)
from app.schemas.common import ApiResponse, PaginatedResponse
from app.service.agent_task_service import AgentTaskService

router = APIRouter(prefix=f"{settings.API_V1_PREFIX}/agent", tags=["Agent 任务 L1-L3"])


@router.get("/graphs", response_model=ApiResponse)
def list_available_graphs(user: User = Depends(get_current_active_user)):
    """列出可触发的 LangGraph 图名称。"""
    return {"code": 0, "message": "", "data": list_graphs()}


@router.get("", response_model=PaginatedResponse)
def list_tasks(
    page: int = 1,
    page_size: int = 20,
    task_type: Optional[str] = None,
    status: Optional[str] = None,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """分页列出当前企业的 Agent 任务。"""
    items, total = AgentTaskService.list(
        db,
        user.enterprise_id,
        AgentTaskListParams(page=page, page_size=page_size, task_type=task_type, status=status),
    )
    return {
        "code": 0,
        "message": "",
        "data": {
            "items": [AgentTaskResponse.model_validate(i) for i in items],
            "total": total,
            "page": page,
            "page_size": page_size,
        },
    }


async def _run_graph_background(
    enterprise_id: int,
    graph_name: str,
    input_data: dict,
    task_id: int,
) -> None:
    """后台执行 LangGraph，不阻塞 HTTP 响应。"""
    from app.core.db import SessionLocal

    db = SessionLocal()
    try:
        await run_graph(db, enterprise_id, graph_name, input_data, task_id)
    finally:
        db.close()


@router.post("", response_model=AgentTaskResponse, summary="触发 L2 LangGraph")
@require_role(["owner", "admin", "editor"])
async def create_task(
    data: AgentTaskCreate,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """创建 Agent 任务并在后台运行指定 graph。"""
    graph_name = data.graph_name or data.task_type
    if graph_name not in list_graphs():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"未知 graph: {graph_name}")
    task = AgentTaskService.create(db, user.enterprise_id, data)
    background_tasks.add_task(
        _run_graph_background,
        user.enterprise_id,
        graph_name,
        data.input_data or {},
        task.id,
    )
    return task


@router.get("/{tid}", response_model=AgentTaskResponse)
def get_task(
    tid: int,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """查询单个 Agent 任务状态与进度。"""
    t = AgentTaskService.get(db, user.enterprise_id, tid)
    if not t:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Agent 任务不存在")
    return t


@router.patch("/{tid}", response_model=AgentTaskResponse)
@require_role(["owner", "admin", "editor"])
def update_task(
    tid: int,
    data: AgentTaskUpdate,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """更新 Agent 任务进度（内部/回调用）。"""
    t = AgentTaskService.update_progress(
        db, user.enterprise_id, tid, **data.model_dump(exclude_unset=True)
    )
    if not t:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Agent 任务不存在")
    return t
