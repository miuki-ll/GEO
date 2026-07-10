from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.core.config import settings
from app.core.db import get_db
from app.api.common import get_current_active_user
from app.models import User
from app.schemas.business import (
    AgentTaskResponse,
    DashboardData,
    AgentTaskCreate,
)
from app.service import (
    DiagnosisService,
    StrategyPackService,
    ScenarioService,
    ContentService,
    AgentTaskService,
    EnterpriseService,
)

router = APIRouter(prefix=f"{settings.API_V1_PREFIX}/user/onboarding", tags=["用户端·舱1·开店向导"])


@router.post("/run", response_model=AgentTaskResponse, summary="A1.1 触发完整开店向导（懂我→出结果全链路 AgentTask")
def onboarding_run(
    background_tasks: BackgroundTasks,
    force: bool = Query(False, description="是否重建数据，忽略已存在"),
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    task = AgentTaskService.create(
        db,
        user.enterprise_id,
        AgentTaskCreate(
            task_type="onboarding_pipeline",
            graph_name="onboarding:diagnosis:strategy:production:review",
            input_data={"force": force},
        ),
    )

    def _bg():
        from app.core.db import SessionLocal
        s = SessionLocal()
        try:
            _ = AgentTaskService.update_progress(s, user.enterprise_id, task.id, status="running", progress_pct=10, progress_message="STEP 1/4 运行全量诊断（痛点/画像/竞品")
            diag = DiagnosisService.run_all(s, user.enterprise_id)
            _ = AgentTaskService.update_progress(s, user.enterprise_id, task.id, progress_pct=25, progress_message="STEP 2/4 构建默认方案包草稿")
            from app.schemas.business import StrategyPackCreate
            sp = StrategyPackService.ensure_draft_default(s, user.enterprise_id, user.id)
            _ = StrategyPackService.update(
                s,
                user.enterprise_id,
                sp.id,
                StrategyPackCreate(
                    version=sp.version or "1.0",
                    persona=diag["persona"],
                    competitors=diag["competitors"],
                    pain_points=diag["pain_points"],
                    scenarios=diag["scenarios"],
                    channels=diag["channels"],
                    weights={"persona": 0.3, "competitors": 0.3, "channels": 0.2, "scenarios": 0.2},
                ).model_dump(exclude_unset=True),
            )
            _ = AgentTaskService.update_progress(s, user.enterprise_id, task.id, progress_pct=45, progress_message="STEP 3/4 写入 Scenario（6+ 典型场景")
            from app.schemas.business import ScenarioCreate
            scenarios = diag["scenarios"] or []
            for sc in scenarios:
                try:
                    ScenarioService.create(s, user.enterprise_id, ScenarioCreate(**sc))
                except Exception as e:
                    from app.core.logging_config import get_logger
                    get_logger(__name__).warning("onboarding create scenario skip: %s", e)
            _ = AgentTaskService.update_progress(s, user.enterprise_id, task.id, progress_pct=70, progress_message="STEP 4/4 为每个 Scenario 生成草稿+机器审")
            items, _ = ScenarioService.list(
                s,
                user.enterprise_id,
                type("P", (), {"channel": None, "skill": None, "status": None, "keyword": "", "page": 1, "page_size": 50})(),
            )
            for sc in items:
                try:
                    drafts = ContentService.generate_drafts_for_scenario(s, user.enterprise_id, sc.id, diag["persona"])
                    for d in drafts:
                        try:
                            ContentService.run_machine_review(s, user.enterprise_id, d.id)
                        except Exception:
                            pass
                except Exception as e:
                    from app.core.logging_config import get_logger
                    get_logger(__name__).warning("onboarding gen draft skip sc=%s err=%s", sc.id, e)
            _ = AgentTaskService.complete_task(s, user.enterprise_id, task.id, output_data={"msg": "onboarding 完成", "scenarios": len(items), "diagnosis": diag})
            EnterpriseService.touch_kb(s, user.enterprise_id)
        except Exception as e:
            AgentTaskService.update_progress(s, user.enterprise_id, task.id, status="failed", progress_pct=100, error_message=str(e), completed_at="__ignore__")
            _ = AgentTaskService.complete_task(s, user.enterprise_id, task.id, output_data={}, error=str(e))
        finally:
            s.close()

    background_tasks.add_task(_bg)
    return task


@router.get("/status/{task_id}", response_model=AgentTaskResponse)
def onboarding_status(task_id: int, user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    t = AgentTaskService.get(db, user.enterprise_id, task_id)
    if not t:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "任务不存在")
    return t


@router.get("/snapshot", response_model=DashboardData, summary="返回当前企业 S3 三舱全量 Dashboard")
def onboarding_snapshot(user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    sp = StrategyPackService.ensure_draft_default(db, user.enterprise_id, user.id)
    items, total = ScenarioService.list(
        db,
        user.enterprise_id,
        type("P", (), {"channel": None, "skill": None, "status": None, "keyword": "", "page": 1, "page_size": 100})(),
    )
    return {
        "period": "onboarding",
        "kpi": {
            "total_scenarios": total,
            "total_drafts_published": 0,
            "avg_mention_rate": 0.0,
            "avg_trust_score": 0.0,
            "core_queries": 0,
            "probe_discoveries": 0,
            "pending_review": 0,
            "kb_facts_verified": 0,
        },
        "by_channel": [],
        "by_engine": [],
        "trend": [],
        "alerts": [],
        "scenarios": total,
        "strategy_pack_id": sp.id,
    }
