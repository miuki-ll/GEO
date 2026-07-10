from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any

from app.core.config import settings
from app.core.db import get_db
from app.api.common import get_current_active_user, require_role
from app.models import User
from app.schemas.business import (
    MonitorResultResponse,
    MonitorResultListParams,
    MonitorTriggerRequest,
)
from app.schemas.common import PaginatedResponse, ApiResponse
from app.service import MonitorService

router = APIRouter(prefix=f"{settings.API_V1_PREFIX}/user/monitor", tags=["用户端·舱3·监测"])


@router.get("", response_model=PaginatedResponse)
def list_results(
    page: int = 1, page_size: int = 20,
    pool: str = Query("core", pattern="^(core|probe)$"),
    engine: Optional[str] = None, scenario_id: Optional[int] = None, batch_no: Optional[str] = None,
    user: User = Depends(get_current_active_user), db: Session = Depends(get_db),
):
    items, total = MonitorService.list(
        db, user.enterprise_id,
        MonitorResultListParams(page=page, page_size=page_size, pool_type=pool, engine=engine, scenario_id=scenario_id, batch_no=batch_no),
    )
    return {"code": 0, "message": "", "data": {"items": [MonitorResultResponse.model_validate(i) for i in items], "total": total, "page": page, "page_size": page_size}}


@router.get("/core", response_model=PaginatedResponse, summary="Core 监测：固定 Scenario 池的结果")
def list_core(page: int = 1, page_size: int = 20, engine: Optional[str] = None, scenario_id: Optional[int] = None,
              user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    items, total = MonitorService.list(
        db, user.enterprise_id,
        MonitorResultListParams(page=page, page_size=page_size, pool_type="core", engine=engine, scenario_id=scenario_id),
    )
    return {"code": 0, "message": "", "data": {"items": [MonitorResultResponse.model_validate(i) for i in items], "total": total, "page": page, "page_size": page_size}}


@router.get("/probe", response_model=PaginatedResponse, summary="Probe 探测：长尾扩展信源的结果")
def list_probe(page: int = 1, page_size: int = 20, engine: Optional[str] = None, scenario_id: Optional[int] = None,
               user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    items, total = MonitorService.list(
        db, user.enterprise_id,
        MonitorResultListParams(page=page, page_size=page_size, pool_type="probe", engine=engine, scenario_id=scenario_id),
    )
    return {"code": 0, "message": "", "data": {"items": [MonitorResultResponse.model_validate(i) for i in items], "total": total, "page": page, "page_size": page_size}}


@router.post("/trigger", response_model=ApiResponse, summary="触发 Core 或 Probe 全量采集")
@require_role(["owner", "admin", "editor"])
def trigger(req: MonitorTriggerRequest, user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    if req.pool not in ("core", "probe"):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "pool 必须是 core 或 probe")
    result = MonitorService.trigger(db, user.enterprise_id, req)
    return {"code": 0, "message": "监测任务已触发", "data": result}


@router.get("/trend", response_model=ApiResponse, summary="按日期聚合的提及率/可信度趋势")
def trend(
    pool: str = Query("core", pattern="^(core|probe)$"),
    days: int = Query(7, ge=1, le=90),
    user: User = Depends(get_current_active_user), db: Session = Depends(get_db),
):
    return {"code": 0, "message": "", "data": MonitorService.latest_trend(db, user.enterprise_id, pool, days)}
