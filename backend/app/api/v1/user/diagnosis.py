"""用户端 — 源诊断 API 与 SSE 事件流。"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import Field
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.api.common import get_current_active_user
from app.models import User
from app.schemas.business import (
    AgentTaskResponse,
    AgentTaskCreate,
)
from app.schemas.common import ApiResponse, BaseSchema
from app.schemas.diagnosis import PersonaData
from app.service import (
    DiagnosisService,
    AgentTaskService,
)

router = APIRouter(prefix=f"{settings.API_V1_PREFIX}/user/diagnosis", tags=["用户端·舱1·诊断"])


class DiagnosisRunRequest(BaseSchema):
    """POST /all 请求体。"""
    enterprise_name: str = ""
    city: str = ""
    district: str = ""
    services: List[str] = Field(default_factory=list)
    extra_context: str = ""
    probes: Optional[List[str]] = None  # 复用已有探针（A5 产出）


@router.post("/all", response_model=AgentTaskResponse, summary="异步：触发全量诊断（探针→搜索→分析→T0）")
def diagnosis_all(
    body: DiagnosisRunRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """触发全量诊断流水线。返回 task_id，前端通过 SSE 订阅进度。"""
    task = AgentTaskService.create(
        db, user.enterprise_id,
        AgentTaskCreate(
            task_type="diagnosis_all",
            graph_name="diagnosis",
            input_data=body.model_dump(),
        ),
    )

    # 发 Celery 任务
    from app.tasks.all_tasks import diagnosis_run
    diagnosis_run.delay(
        enterprise_id=user.enterprise_id,
        enterprise_name=body.enterprise_name,
        city=body.city,
        district=body.district,
        services=body.services,
        extra_context=body.extra_context,
        existing_probes=body.probes,
        task_id=task.id,
    )

    return task


@router.get("/events/{task_id}", summary="SSE 诊断进度推送")
async def diagnosis_events(
    task_id: int,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """SSE 端点 — 实时推送诊断进度。"""
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


# ── 向后兼容旧端点（必须在 /{batch_no} 之前注册，避免被路径参数吃掉）──

@router.get("/pain", response_model=ApiResponse, summary="[deprecated] 诊断：痛点分析", deprecated=True)
def diagnosis_pain(user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    # A7-2 已移除 diagnose_pain；deprecated 端点返回空列表，请改用 POST /all
    return {"code": 0, "message": "deprecated: use POST /all", "data": []}


@router.get("/persona", response_model=PersonaData, summary="[deprecated] 诊断：人群画像", deprecated=True)
def diagnosis_persona(user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    # A7-2 已移除 diagnose_persona；返回默认画像壳
    return PersonaData()


@router.get("/competitor", response_model=ApiResponse, summary="[deprecated] 诊断：竞品画像", deprecated=True)
def diagnosis_competitor(user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    return {"code": 0, "message": "deprecated: use POST /all", "data": []}


@router.get("/{batch_no}", response_model=ApiResponse, summary="查询诊断结果（五区 JSON）")
def diagnosis_result(
    batch_no: str,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """按批次号查询完整诊断结果。"""
    from app.models.strategy import SearchResult
    from app.models.monitor import MonitorResult

    # 搜索原始结果
    search_rows = (
        db.query(SearchResult)
        .filter(
            SearchResult.enterprise_id == user.enterprise_id,
            SearchResult.diagnosis_batch_no == batch_no,
        )
        .all()
    )

    if not search_rows:
        raise HTTPException(status_code=404, detail="批次不存在或不属于当前企业")

    # T0 基线
    t0_rows = (
        db.query(MonitorResult)
        .filter(
            MonitorResult.enterprise_id == user.enterprise_id,
            MonitorResult.batch_no == batch_no,
            MonitorResult.baseline == True,  # noqa: E712
        )
        .all()
    )

    # 信源地图
    source_map = DiagnosisService.build_source_map(db, user.enterprise_id, batch_no)

    # 从 T0 的 metrics 中提取分析结果
    analysis = {}
    if t0_rows:
        first = t0_rows[0]
        analysis = {
            "brand_mentioned": first.mentioned,
            "mention_context": first.mention_snippet,
            "rank_estimate": first.position_rank,
            "competitor_occupancy": first.competitor_mentions,
        }

    return {
        "code": 0,
        "message": "",
        "data": {
            "batch_no": batch_no,
            "enterprise_id": user.enterprise_id,
            "probes": [r.probe_query for r in search_rows],
            "search_results": [
                {
                    "id": r.id,
                    "enterprise_id": r.enterprise_id,
                    "probe_query": r.probe_query,
                    "engine": r.engine,
                    "answer": r.answer,
                    "citations": r.citations,
                    "citation_count": r.citation_count,
                    "diagnosis_batch_no": r.diagnosis_batch_no,
                    "latency_ms": r.latency_ms,
                    "error": r.error,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in search_rows
            ],
            "source_map": source_map,
            "pain_points": analysis.get("pain_points", []),
            "persona": analysis.get("persona"),
            "competitors": analysis.get("competitor_occupancy", []),
            "t0_written": len(t0_rows) > 0,
            "created_at": search_rows[0].created_at.isoformat() if search_rows and search_rows[0].created_at else None,
        },
    }
