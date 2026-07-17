from typing import List, Tuple, Optional, Dict, Any
from datetime import datetime, timedelta
import random
import string

from sqlalchemy.orm import Session

from app.core.logging_config import get_logger
from app.models import PublishTask, ContentAsset
from app.schemas.business import (
    PublishTaskCreate,
    PublishTaskUpdate,
    PublishTaskListParams,
)
from app.service.content_service import ContentService
from app.publish_export import (
    build_auto_mock_result,
    build_semi_export_package,
    infer_publish_mode,
    publish_task_api_view,
)

logger = get_logger(__name__)


def _rand_id(n: int = 12) -> str:
    return "".join(random.choices(string.ascii_letters + string.digits, k=n))


class PublishService:
    @staticmethod
    def list(db: Session, enterprise_id: int, params: PublishTaskListParams) -> Tuple[List[PublishTask], int]:
        q = db.query(PublishTask).filter(PublishTask.enterprise_id == enterprise_id)
        if params.draft_id:
            q = q.filter(PublishTask.content_asset_id == params.draft_id)
        if params.channel:
            q = q.filter(PublishTask.channel == params.channel)
        if params.mode:
            q = q.filter(PublishTask.mode == params.mode)
        if params.status:
            q = q.filter(PublishTask.status == params.status)
        total = q.count()
        items = q.order_by(PublishTask.updated_at.desc()).offset((params.page - 1) * params.page_size).limit(params.page_size).all()
        return items, total

    @staticmethod
    def get(db: Session, enterprise_id: int, tid: int) -> Optional[PublishTask]:
        return (
            db.query(PublishTask)
            .filter(PublishTask.id == tid, PublishTask.enterprise_id == enterprise_id)
            .first()
        )

    @staticmethod
    def create(db: Session, enterprise_id: int, data: PublishTaskCreate) -> PublishTask:
        asset = ContentService.get(db, enterprise_id, data.content_asset_id)
        if not asset:
            raise ValueError("内容资产不存在")
        if asset.status not in ("approved", "published", "ready"):
            # ready 允许开发态建任务；正式人审后应为 approved
            raise ValueError("内容未通过人审，不允许发布")
        mode = (data.mode or infer_publish_mode(data.channel or asset.channel or "")).lower()
        channel = data.channel or asset.channel or "hosted"
        meta = dict(data.metadata_ or {})
        meta["title"] = asset.title
        if mode == "semi":
            kws = []
            ameta = getattr(asset, "metadata_", None) or {}
            for sl in ameta.get("rag_slices") or []:
                kws.extend(sl.get("keywords") or [])
            meta["export_package"] = build_semi_export_package(
                title=asset.title or "",
                body=asset.content or "",
                channel=channel,
                keywords=kws,
            )
        t = PublishTask(
            enterprise_id=enterprise_id,
            content_asset_id=asset.id,
            channel=channel,
            mode=mode,
            target_url=data.target_url,
            status="pending",
            utm_content=str(asset.id),
            metadata_=meta,
        )
        db.add(t)
        db.commit()
        db.refresh(t)
        logger.info("PublishTask created id=%s enterprise=%s mode=%s", t.id, enterprise_id, mode)
        return t

    @staticmethod
    def ensure_task_for_asset(db: Session, enterprise_id: int, asset_id: int) -> PublishTask:
        """人审通过后自动建发布任务（已存在则复用 pending/最新）。"""
        existing = (
            db.query(PublishTask)
            .filter(
                PublishTask.enterprise_id == enterprise_id,
                PublishTask.content_asset_id == asset_id,
                PublishTask.status.in_(["pending", "failed"]),
            )
            .order_by(PublishTask.id.desc())
            .first()
        )
        if existing:
            return existing
        asset = ContentService.get(db, enterprise_id, asset_id)
        if not asset:
            raise ValueError("内容资产不存在")
        channel = asset.channel or "hosted"
        mode = infer_publish_mode(channel)
        return PublishService.create(
            db,
            enterprise_id,
            PublishTaskCreate(draft_id=asset_id, channel=channel, mode=mode),
        )

    @staticmethod
    def run_publish_auto(db: Session, enterprise_id: int, tid: int) -> PublishTask:
        t = PublishService.get(db, enterprise_id, tid)
        if not t:
            raise ValueError("任务不存在")
        auto = build_auto_mock_result(enterprise_id, t.id)
        meta = dict(t.metadata_ or {})
        meta["auto_result"] = auto
        upd = PublishTaskUpdate(
            status="published",
            published_id=f"pub-{t.id}-{_rand_id(8)}",
            published_url=auto["published_url"],
            published_at=datetime.utcnow(),
            metadata_=meta,
        )
        return PublishService._apply(db, t, upd)

    @staticmethod
    def run_batch(db: Session, enterprise_id: int, task_ids: List[int]) -> Dict[str, Any]:
        started = 0
        results = []
        for tid in task_ids:
            t = PublishService.get(db, enterprise_id, tid)
            if not t:
                results.append({"id": tid, "ok": False, "error": "not_found"})
                continue
            try:
                mode = (t.mode or "auto").lower()
                if mode == "auto":
                    t = PublishService.run_publish_auto(db, enterprise_id, tid)
                elif mode == "semi":
                    # SEMI：仅确保 export_package 就绪，状态保持 pending 待人工回填 URL
                    meta = dict(t.metadata_ or {})
                    if not meta.get("export_package"):
                        asset = ContentService.get(db, enterprise_id, t.content_asset_id)
                        if asset:
                            meta["export_package"] = build_semi_export_package(
                                title=asset.title or "",
                                body=asset.content or "",
                                channel=t.channel or "xiaohongshu",
                            )
                            t.metadata_ = meta
                            db.commit()
                            db.refresh(t)
                    results.append({"id": tid, "ok": True, "status": t.status, "mode": "semi"})
                    started += 1
                    continue
                else:
                    t = PublishService.run_guided_retry(db, enterprise_id, tid, completed=False)
                results.append({"id": tid, "ok": True, "status": t.status, "mode": mode})
                started += 1
            except Exception as e:
                results.append({"id": tid, "ok": False, "error": str(e)})
        return {"started": started, "results": results}

    @staticmethod
    def task_view(db: Session, enterprise_id: int, task: PublishTask) -> Dict[str, Any]:
        asset = ContentService.get(db, enterprise_id, task.content_asset_id)
        return publish_task_api_view(task, asset)

    @staticmethod
    def run_semi_submit(
        db: Session,
        enterprise_id: int,
        tid: int,
        published_url: str,
        published_id: Optional[str] = None,
    ) -> PublishTask:
        t = PublishService.get(db, enterprise_id, tid)
        if not t:
            raise ValueError("任务不存在")
        if not published_url:
            raise ValueError("半托管模式需提供已发布外链 URL")
        upd = PublishTaskUpdate(
            status="published",
            published_id=published_id or f"semipub-{t.id}-{_rand_id(8)}",
            published_url=published_url,
            published_at=datetime.utcnow(),
        )
        return PublishService._apply(db, t, upd)

    @staticmethod
    def run_guided_retry(
        db: Session,
        enterprise_id: int,
        tid: int,
        note: Optional[str] = None,
        completed: bool = False,
    ) -> PublishTask:
        t = PublishService.get(db, enterprise_id, tid)
        if not t:
            raise ValueError("任务不存在")
        if completed:
            upd = PublishTaskUpdate(
                status="published",
                published_id=f"guided-{t.id}-{_rand_id(8)}",
                retry_count=(t.retry_count or 0) + 1,
                published_at=datetime.utcnow(),
                metadata_={"completion_note": note} if note else None,
            )
        else:
            upd = PublishTaskUpdate(
                status="pending",
                retry_count=(t.retry_count or 0) + 1,
                error_message=None,
                metadata_={"retry_note": note} if note else None,
            )
        return PublishService._apply(db, t, upd)

    @staticmethod
    def _apply(db: Session, t: PublishTask, upd: PublishTaskUpdate) -> PublishTask:
        payload = upd.model_dump(exclude_unset=True, by_alias=True)
        if "metadata" in payload and payload["metadata"] is None:
            payload.pop("metadata", None)
        elif "metadata" in payload:
            payload["metadata_"] = payload.pop("metadata")
        for k, v in payload.items():
            setattr(t, k, v)
        t.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(t)
        return t
