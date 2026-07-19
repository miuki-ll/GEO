from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any

from app.core.config import settings
from app.core.db import get_db
from app.api.common import get_current_active_user, require_role
from app.models import User
from app.schemas.business import (
    MonitorResultListParams,
    MonitorTriggerRequest,
)
from app.schemas.common import ApiResponse
from app.service import MonitorService

router = APIRouter(prefix=f"{settings.API_V1_PREFIX}/user/monitor", tags=["用户端·舱3·监测"])


def _list_payload(db, enterprise_id, params: MonitorResultListParams):
    items, total = MonitorService.list(db, enterprise_id, params)
    return {
        "items": [MonitorService.result_view(i) for i in items],
        "total": total,
        "page": params.page,
        "page_size": params.page_size,
    }


@router.get("")
def list_results(
    page: int = 1,
    page_size: int = 20,
    pool: str = Query("core", pattern="^(core|probe)$"),
    engine: Optional[str] = None,
    scenario_id: Optional[int] = None,
    batch_no: Optional[str] = None,
    baseline: Optional[bool] = None,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    if settings.is_dev:
        MonitorService.ensure_profile(db, user.enterprise_id)
    params = MonitorResultListParams(
        page=page,
        page_size=page_size,
        pool_type=pool,
        engine=engine,
        scenario_id=scenario_id,
        batch_no=batch_no,
        baseline=baseline,
    )
    return {"code": 0, "message": "ok", "data": _list_payload(db, user.enterprise_id, params)}


@router.get("/profile", summary="Core/Probe 监测配置")
def get_profile(user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    profile = MonitorService.ensure_profile(db, user.enterprise_id)
    return {"code": 0, "message": "ok", "data": MonitorService.profile_view(profile)}


@router.post("/profile/ensure", response_model=ApiResponse, summary="确保监测 profile（跟随 target_engines）")
@require_role(["owner", "admin", "editor"])
def ensure_profile(user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    profile = MonitorService.ensure_profile(db, user.enterprise_id)
    return {"code": 0, "message": "ok", "data": MonitorService.profile_view(profile)}


@router.get("/core", summary="Core 监测结果")
def list_core(
    page: int = 1,
    page_size: int = 20,
    engine: Optional[str] = None,
    scenario_id: Optional[int] = None,
    baseline: Optional[bool] = None,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    if settings.is_dev:
        MonitorService.ensure_profile(db, user.enterprise_id)
    params = MonitorResultListParams(
        page=page,
        page_size=page_size,
        pool_type="core",
        engine=engine,
        scenario_id=scenario_id,
        baseline=baseline,
    )
    return {"code": 0, "message": "ok", "data": _list_payload(db, user.enterprise_id, params)}


@router.get("/probe", summary="Probe 探测结果")
def list_probe(
    page: int = 1,
    page_size: int = 20,
    engine: Optional[str] = None,
    scenario_id: Optional[int] = None,
    baseline: Optional[bool] = None,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    if settings.is_dev:
        MonitorService.ensure_profile(db, user.enterprise_id)
    params = MonitorResultListParams(
        page=page,
        page_size=page_size,
        pool_type="probe",
        engine=engine,
        scenario_id=scenario_id,
        baseline=baseline,
    )
    return {"code": 0, "message": "ok", "data": _list_payload(db, user.enterprise_id, params)}


@router.post("/trigger", response_model=ApiResponse, summary="触发 Core/Probe，写入 T1（baseline=false）")
@require_role(["owner", "admin", "editor"])
def trigger(req: MonitorTriggerRequest, user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    if req.pool not in ("core", "probe"):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "pool 必须是 core 或 probe")
    result = MonitorService.trigger(db, user.enterprise_id, req)
    return {"code": 0, "message": "T1 监测已写入", "data": result}


@router.post("/seed-t0", response_model=ApiResponse, summary="开发态假 T0（WAIT_FOR A7）")
@require_role(["owner", "admin", "editor"])
def seed_t0(user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    if not settings.is_dev:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "仅 development 可写假 T0")
    data = MonitorService.seed_mock_t0(db, user.enterprise_id)
    return {"code": 0, "message": "ok", "data": data}


@router.get("/delta", response_model=ApiResponse, summary="T0/T1 提及率 Δ")
def delta(
    pool: str = Query("core", pattern="^(core|probe)$"),
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return {"code": 0, "message": "ok", "data": MonitorService.delta(db, user.enterprise_id, pool)}


@router.get("/trend", response_model=ApiResponse, summary="按日期聚合的提及率/可信度趋势")
def trend(
    pool: str = Query("core", pattern="^(core|probe)$"),
    days: int = Query(7, ge=1, le=90),
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return {"code": 0, "message": "ok", "data": MonitorService.latest_trend(db, user.enterprise_id, pool, days)}
