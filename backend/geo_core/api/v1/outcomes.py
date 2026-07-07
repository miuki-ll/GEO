from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks, Body
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any

from geo_core.core.db import get_db
from geo_core.api.v1.common import get_current_active_user, require_role
from geo_core.models import User
from geo_core.schemas.business import (
    DashboardData,
    OutcomeSnapshotResponse,
    AgentTaskResponse,
    AgentTaskCreate,
)
from geo_core.schemas.common import PaginatedResponse, ApiResponse
from geo_core.services import DashboardService, AgentTaskService, DiagnosisService, StrategyPackService, ScenarioService, ContentService, EnterpriseService, MonitorService

router = APIRouter(tags=["出结果·效果舱"])


@router.get("/dashboard", response_model=ApiResponse, summary="F1.1 效果舱 Dashboard（KPI + 拆解）")
def dashboard(period: str = Query("week", pattern="^(day|week|month|quarter)$"),
              user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    d = DashboardService.compute(db, user.enterprise_id, period)
    return {"code": 0, "message": "", "data": d.model_dump()}


@router.post("/snapshot", response_model=OutcomeSnapshotResponse, summary="生成当期效果快照")
@require_role(["owner", "admin", "editor"])
def create_snapshot(period: str = Query("week", pattern="^(day|week|month|quarter)$"),
                    user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    return DashboardService.take_snapshot(db, user.enterprise_id, period)


@router.get("/ai-kpi", response_model=ApiResponse, summary="AI 可见度核心 KPI 精简版")
def ai_kpi(period: str = Query("week"),
           user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    d = DashboardService.compute(db, user.enterprise_id, period)
    return {"code": 0, "message": "", "data": d.kpi.model_dump()}


@router.get("/traffic", response_model=ApiResponse, summary="渠道 / 引擎 拆解")
def traffic(period: str = Query("week"),
            user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    d = DashboardService.compute(db, user.enterprise_id, period)
    return {"code": 0, "message": "", "data": {"by_channel": [c.model_dump() for c in d.by_channel], "by_engine": [e.model_dump() for e in d.by_engine]}}


@router.post("/iterations/trigger", response_model=ApiResponse, summary="G2 临界触发：发起迭代闭环")
@require_role(["owner", "admin", "editor"])
def trigger_iteration(
    background_tasks: BackgroundTasks,
    payload: Dict[str, Any] = Body(default_factory=dict),
    user: User = Depends(get_current_active_user), db: Session = Depends(get_db),
):
    payload = payload or {}
    force = bool(payload.get("force", False))
    reason = payload.get("reason")
    task = AgentTaskService.create(
        db, user.enterprise_id,
        AgentTaskCreate(
            task_type="iteration_closed_loop",
            graph_name="iteration:monitor:diagnosis:strategy:production:publish:monitor",
            input_data={"force": force, "reason": reason},
        ),
    )

    def _bg():
        from geo_core.core.db import SessionLocal
        s = SessionLocal()
        try:
            AgentTaskService.update_progress(s, user.enterprise_id, task.id, status="running", progress_pct=10, progress_message="STEP 1 触发新一轮 Core 监测")
            MonitorService.trigger(s, user.enterprise_id, type("R", (), {"pool": "core", "scenario_ids": []})())
            AgentTaskService.update_progress(s, user.enterprise_id, task.id, progress_pct=30, progress_message="STEP 2 重跑诊断（痛点画像竞品）")
            diag = DiagnosisService.run_all(s, user.enterprise_id)
            AgentTaskService.update_progress(s, user.enterprise_id, task.id, progress_pct=50, progress_message="STEP 3 更新 StrategyPack 草案")
            sp = StrategyPackService.get_latest(s, user.enterprise_id)
            if sp:
                from geo_core.schemas.business import StrategyPackCreate
                StrategyPackService.update(
                    s, user.enterprise_id, sp.id,
                    StrategyPackCreate(version=sp.version, persona=diag["persona"], competitors=diag["competitors"], pain_points=diag["pain_points"], scenarios=diag["scenarios"], channels=diag["channels"], weights={}).model_dump(exclude_unset=True),
                )
            AgentTaskService.update_progress(s, user.enterprise_id, task.id, progress_pct=75, progress_message="STEP 4 为新增 Scenario 生成草稿+机审")
            for sc in diag["scenarios"]:
                try:
                    scenario = ScenarioService.create(s, user.enterprise_id, type("SC", (), sc)())
                except Exception:
                    continue
                try:
                    drafts = ContentService.generate_drafts_for_scenario(s, user.enterprise_id, scenario.id, diag["persona"])
                    for d in drafts:
                        try:
                            ContentService.run_machine_review(s, user.enterprise_id, d.id)
                        except Exception:
                            pass
                except Exception:
                    pass
            AgentTaskService.complete_task(s, user.enterprise_id, task.id, output_data={"msg": "iteration 闭环完成", "reason": reason, "diagnosis": diag})
            EnterpriseService.touch_kb(s, user.enterprise_id)
        except Exception as e:
            AgentTaskService.complete_task(s, user.enterprise_id, task.id, output_data={}, error=str(e))
        finally:
            s.close()

    background_tasks.add_task(_bg)
    resp = AgentTaskResponse.model_validate(task).model_dump()
    resp["task_id"] = task.id
    return {"code": 0, "message": "", "data": resp}
