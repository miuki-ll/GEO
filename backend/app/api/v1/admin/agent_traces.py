from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import require_platform_admin
from app.core.config import settings
from app.core.db import get_db
from app.models import User, AgentTrace
from app.schemas import ListResponse, ResponseModel

router = APIRouter(
    prefix=f"{settings.API_V1_PREFIX}/admin/agent-traces",
    tags=["管理端·Agent审计"],
    dependencies=[Depends(require_platform_admin)],
)


@router.get("", response_model=ListResponse[dict])
def list_agent_traces(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    enterprise_id: int | None = None,
    graph_name: str | None = None,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_platform_admin),
):
    q = db.query(AgentTrace)
    if enterprise_id:
        q = q.filter(AgentTrace.enterprise_id == enterprise_id)
    if graph_name:
        q = q.filter(AgentTrace.graph_name == graph_name)
    total = q.count()
    items = (
        q.order_by(AgentTrace.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return ListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[
            {
                "id": t.id,
                "enterprise_id": t.enterprise_id,
                "agent_task_id": t.agent_task_id,
                "graph_name": t.graph_name,
                "step_idx": t.step_idx,
                "step_name": t.step_name,
                "thought": t.thought,
                "action": t.action,
                "latency_ms": t.latency_ms,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
            for t in items
        ],
    )


@router.get("/{trace_id}", response_model=ResponseModel[dict])
def get_agent_trace(
    trace_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_platform_admin),
):
    t = db.query(AgentTrace).filter(AgentTrace.id == trace_id).first()
    if not t:
        from fastapi import HTTPException

        raise HTTPException(404, "trace 不存在")
    return ResponseModel(
        data={
            "id": t.id,
            "enterprise_id": t.enterprise_id,
            "agent_task_id": t.agent_task_id,
            "graph_name": t.graph_name,
            "step_idx": t.step_idx,
            "step_name": t.step_name,
            "thought": t.thought,
            "action": t.action,
            "observation": t.observation,
            "prompt_tokens": t.prompt_tokens,
            "completion_tokens": t.completion_tokens,
            "latency_ms": t.latency_ms,
            "langsmith_run_id": t.langsmith_run_id,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
    )
