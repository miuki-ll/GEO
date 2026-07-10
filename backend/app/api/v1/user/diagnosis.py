from fastapi import APIRouter, Depends, Query, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.api.common import get_current_active_user
from app.models import User
from app.schemas.business import (
    PersonaData,
    CompetitorItem,
    PainPoint,
    AgentTaskResponse,
    AgentTaskCreate,
)
from app.service import (
    DiagnosisService,
    AgentTaskService,
)
from app.schemas.common import ApiResponse

router = APIRouter(prefix=f"{settings.API_V1_PREFIX}/user/diagnosis", tags=["用户端·舱1·诊断"])


@router.get("/pain", response_model=ApiResponse, summary="诊断：痛点分析")
def diagnosis_pain(user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    return {"code": 0, "message": "", "data": [p.model_dump() for p in DiagnosisService.diagnose_pain(db, user.enterprise_id)]}


@router.get("/persona", response_model=PersonaData, summary="诊断：人群画像")
def diagnosis_persona(user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    return DiagnosisService.diagnose_persona(db, user.enterprise_id)


@router.get("/competitor", response_model=ApiResponse, summary="诊断：竞品画像")
def diagnosis_competitor(user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    return {"code": 0, "message": "", "data": [c.model_dump() for c in DiagnosisService.diagnose_competitor(db, user.enterprise_id)]}


@router.post("/all", response_model=AgentTaskResponse, summary="异步：后台触发全量诊断")
def diagnosis_all(
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    task = AgentTaskService.create(
        db,
        user.enterprise_id,
        AgentTaskCreate(
            task_type="diagnosis_all",
            graph_name="diagnosis:pain:persona:competitor",
            input_data={},
        ),
    )

    def _bg():
        from app.core.db import SessionLocal
        s = SessionLocal()
        try:
            AgentTaskService.update_progress(s, user.enterprise_id, task.id, status="running", progress_pct=20, progress_message="生成画像")
            AgentTaskService.update_progress(s, user.enterprise_id, task.id, progress_pct=60, progress_message="生成竞品")
            result = DiagnosisService.run_all(s, user.enterprise_id)
            AgentTaskService.complete_task(s, user.enterprise_id, task.id, output_data=result)
        except Exception as e:
            AgentTaskService.complete_task(s, user.enterprise_id, task.id, output_data={}, error=str(e))
        finally:
            s.close()

    background_tasks.add_task(_bg)
    return task
