from typing import Any, Dict, List

from app.core.celery import celery_app
from app.core.logging_config import get_logger

logger = get_logger(__name__)


@celery_app.task(name="app.tasks.diagnosis_run", bind=True, acks_late=True)
def diagnosis_run(self, enterprise_id: int, scenario_id: int, **kwargs) -> Dict[str, Any]:
    """异步执行诊断分析（生产模式会调用 DiagnosisService）。当前同步冒烟测试直接使用 service。"""
    logger.info("[diagnosis_run] enterprise_id=%s scenario_id=%s kwargs=%s", enterprise_id, scenario_id, kwargs)
    try:
        from app.service.diagnosis_service import DiagnosisService
        from app.core.db import SessionLocal

        db = SessionLocal()
        try:
            result = DiagnosisService.run_all(db, enterprise_id)
            return {"ok": True, "task_id": self.request.id, "result": result}
        finally:
            db.close()
    except Exception as e:
        logger.exception("[diagnosis_run] failed: %s", e)
        return {"ok": False, "task_id": self.request.id, "error": str(e)}


@celery_app.task(name="app.tasks.content_generate", bind=True, acks_late=True)
def content_generate(self, enterprise_id: int, scenario_id: int, persona: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """异步生成内容草稿。"""
    logger.info("[content_generate] enterprise_id=%s scenario_id=%s", enterprise_id, scenario_id)
    try:
        from app.service.content_service import ContentService
        from app.core.db import SessionLocal

        db = SessionLocal()
        try:
            drafts = ContentService.generate_drafts_for_scenario(db, enterprise_id, scenario_id, persona)
            ids = [d.id for d in drafts] if drafts else []
            return {"ok": True, "task_id": self.request.id, "draft_ids": ids}
        finally:
            db.close()
    except Exception as e:
        logger.exception("[content_generate] failed: %s", e)
        return {"ok": False, "task_id": self.request.id, "error": str(e)}


@celery_app.task(name="app.tasks.monitor_sample", bind=True, acks_late=True)
def monitor_sample(self, enterprise_id: int, batch_id: int, probes: List[Dict[str, Any]] | None = None) -> Dict[str, Any]:
    """异步执行监测样本生成与回采。"""
    logger.info("[monitor_sample] enterprise_id=%s batch_id=%s probes=%s", enterprise_id, batch_id, probes and len(probes))
    try:
        return {"ok": True, "task_id": self.request.id, "enterprise_id": enterprise_id, "batch_id": batch_id}
    except Exception as e:
        logger.exception("[monitor_sample] failed: %s", e)
        return {"ok": False, "task_id": self.request.id, "error": str(e)}
