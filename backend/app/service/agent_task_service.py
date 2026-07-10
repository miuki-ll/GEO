from typing import List, Tuple, Optional, Dict, Any
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.logging_config import get_logger
from app.models import AgentTask
from app.schemas.business import (
    AgentTaskCreate,
    AgentTaskUpdate,
    AgentTaskListParams,
)

logger = get_logger(__name__)


class AgentTaskService:
    @staticmethod
    def list(db: Session, enterprise_id: int, params: AgentTaskListParams) -> Tuple[List[AgentTask], int]:
        q = db.query(AgentTask).filter(AgentTask.enterprise_id == enterprise_id)
        if params.task_type:
            q = q.filter(AgentTask.task_type == params.task_type)
        if params.status:
            q = q.filter(AgentTask.status == params.status)
        total = q.count()
        items = q.order_by(AgentTask.created_at.desc()).offset((params.page - 1) * params.page_size).limit(params.page_size).all()
        return items, total

    @staticmethod
    def get(db: Session, enterprise_id: int, tid: int) -> Optional[AgentTask]:
        return (
            db.query(AgentTask)
            .filter(AgentTask.id == tid, AgentTask.enterprise_id == enterprise_id)
            .first()
        )

    @staticmethod
    def create(db: Session, enterprise_id: int, data: AgentTaskCreate, celery_task_id: Optional[str] = None) -> AgentTask:
        payload = data.model_dump(exclude={"input_data"})
        payload["enterprise_id"] = enterprise_id
        payload["input_data"] = data.input_data or {}
        if celery_task_id:
            payload["celery_task_id"] = celery_task_id
        t = AgentTask(**payload)
        db.add(t)
        db.commit()
        db.refresh(t)
        logger.info("AgentTask created id=%s type=%s enterprise=%s", t.id, data.task_type, enterprise_id)
        return t

    @staticmethod
    def update_progress(db: Session, enterprise_id: int, tid: int, **kwargs) -> Optional[AgentTask]:
        t = AgentTaskService.get(db, enterprise_id, tid)
        if not t:
            return None
        upd = AgentTaskUpdate(**kwargs)
        payload = upd.model_dump(exclude_unset=True, exclude_none=True)
        for k, v in payload.items():
            setattr(t, k, v)
        t.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(t)
        return t

    @staticmethod
    def complete_task(db: Session, enterprise_id: int, tid: int, output_data: Optional[Dict[str, Any]] = None, error: Optional[str] = None) -> AgentTask:
        if error:
            return AgentTaskService.update_progress(db, enterprise_id, tid, status="failed", progress_pct=100, output_data=output_data or {}, error_message=error, completed_at=datetime.utcnow())
        return AgentTaskService.update_progress(db, enterprise_id, tid, status="completed", progress_pct=100, output_data=output_data or {}, completed_at=datetime.utcnow())
