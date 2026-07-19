"""业务 Celery 任务 — 诊断 / 内容生成 / 监测采样。"""

from typing import Any, Dict, List, Optional

from app.core.celery import celery_app
from app.core.logging_config import get_logger

logger = get_logger(__name__)


@celery_app.task(name="app.tasks.diagnosis_run", bind=True, acks_late=True)
def diagnosis_run(self, enterprise_id: int, task_id: Optional[int] = None, **kwargs) -> Dict[str, Any]:
    """异步执行诊断分析（探针→搜索→分析→信源地图→T0）。"""
    import asyncio
    from app.core.sse import publish_progress, build_event
    from app.service.diagnosis_service import DiagnosisService

    logger.info("[diagnosis_run] enterprise_id=%s task_id=%s", enterprise_id, task_id)

    def _pub(pct, msg, step="", status="running"):
        if task_id:
            publish_progress(task_id, build_event(
                progress_pct=pct, progress_message=msg, step=step, status=status,
            ))

    try:
        _pub(5, "生成探针问句中…", "probes")
        result = asyncio.run(DiagnosisService.run_full_diagnosis(
            enterprise_id=enterprise_id,
            enterprise_name=kwargs.get("enterprise_name", ""),
            city=kwargs.get("city", ""),
            district=kwargs.get("district", ""),
            services=kwargs.get("services"),
            extra_context=kwargs.get("extra_context", ""),
            existing_probes=kwargs.get("existing_probes"),
        ))

        _pub(100, "诊断完成", "done", status="completed")
        return {"ok": True, "task_id": self.request.id, "result": result}
    except Exception as e:
        logger.exception("[diagnosis_run] failed: %s", e)
        _pub(100, str(e)[:200], "error", status="failed")
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


@celery_app.task(name="app.tasks.keyword_generate", bind=True, acks_late=True)
def keyword_generate(self, enterprise_id: int, enterprise_name: str = "", city: str = "", task_id: Optional[int] = None) -> Dict[str, Any]:
    """异步执行词库生成（四源汇聚 → LLM 分类 → 批量写入）。"""
    import asyncio
    from app.core.sse import publish_progress, build_event
    from app.core.db import SessionLocal
    from app.service.keyword_service import KeywordService

    logger.info("[keyword_generate] enterprise_id=%s name=%s city=%s", enterprise_id, enterprise_name, city)

    def _pub(pct, msg, step="", status="running"):
        if task_id:
            publish_progress(task_id, build_event(
                progress_pct=pct, progress_message=msg, step=step, status=status,
            ))

    try:
        _pub(5, "正在从入驻信息提取关键词…", "raw_inputs")
        _pub(20, "正在从诊断探针提取关键词…", "probes")
        _pub(35, "正在获取 SEO 热词…", "seo")
        _pub(50, "正在用 LLM 补充长尾词…", "llm")
        _pub(70, "正在用 LLM 进行四层分类…", "classify")

        result = asyncio.run(KeywordService.generate_keywords(
            db_factory=SessionLocal,
            enterprise_id=enterprise_id,
            enterprise_name=enterprise_name,
            city=city,
        ))

        _pub(100, f"词库生成完成：新增 {result.get('inserted', 0)} 个关键词", "done", status="completed")
        return {"ok": True, "task_id": self.request.id, "result": result}
    except Exception as e:
        logger.exception("[keyword_generate] failed: %s", e)
        _pub(100, str(e)[:200], "error", status="failed")
        return {"ok": False, "task_id": self.request.id, "error": str(e)}
