"""Faiss 向量库 Celery 异步任务 — sync 单条同步 + rebuild 全量重建"""
from app.core.celery_app import celery_app
from app.core.logging_config import get_logger

logger = get_logger(__name__)


@celery_app.task(name="app.tasks.faiss_sync_item", bind=True, acks_late=True)
def faiss_sync_item(
    self,
    enterprise_id: int,
    index_type: str,
    item_id: int,
    action: str,  # "create" | "update" | "delete"
):
    """异步同步单条 KB 记录到 Faiss 索引。

    由 FactService/FaqService 的 create/update/delete 后触发。
    """
    from app.rag.faiss_service import FaissService
    from app.core.db import SessionLocal
    from app.models.kb import KBFact, KBFaq

    logger.info("[faiss_sync] eid=%s type=%s id=%s action=%s", enterprise_id, index_type, item_id, action)

    try:
        db = SessionLocal()
        try:
            if action == "delete":
                FaissService.delete(enterprise_id, index_type, [item_id])
                return {"ok": True, "action": "delete", "item_id": item_id}

            # create / update → 从 DB 读取最新文本，重新 embed
            if index_type == "kb_facts":
                row = db.query(KBFact).filter(
                    KBFact.id == item_id,
                    KBFact.enterprise_id == enterprise_id,
                ).first()
                if row:
                    text = row.title + " " + (row.content or "")
                else:
                    text = None
            else:
                row = db.query(KBFaq).filter(
                    KBFaq.id == item_id,
                    KBFaq.enterprise_id == enterprise_id,
                ).first()
                if row:
                    text = row.question + " " + (row.answer or "")
                else:
                    text = None

            if not text or not text.strip():
                # 文本为空 → 从索引中删除
                FaissService.delete(enterprise_id, index_type, [item_id])
                return {"ok": True, "action": "delete_empty", "item_id": item_id}

            # 先删旧的（如果存在），再加新的
            FaissService.delete(enterprise_id, index_type, [item_id])
            FaissService.add(enterprise_id, index_type, [text], [item_id])

            return {"ok": True, "action": action, "item_id": item_id}
        finally:
            db.close()
    except Exception as e:
        logger.exception("[faiss_sync] failed: %s", e)
        return {"ok": False, "error": str(e)}


@celery_app.task(name="app.tasks.faiss_rebuild_index", bind=True, acks_late=True)
def faiss_rebuild_index(self, enterprise_id: int, index_type: str):
    """全量重建指定租户的 Faiss 索引。"""
    from app.rag.faiss_service import FaissService

    logger.info("[faiss_rebuild] eid=%s type=%s", enterprise_id, index_type)
    try:
        count = FaissService.rebuild(enterprise_id, index_type)
        return {"ok": True, "enterprise_id": enterprise_id, "index_type": index_type, "count": count}
    except Exception as e:
        logger.exception("[faiss_rebuild] failed: %s", e)
        return {"ok": False, "error": str(e)}
