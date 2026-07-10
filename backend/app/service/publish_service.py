from typing import List, Tuple, Optional, Dict, Any
from datetime import datetime, timedelta
import random
import string

from sqlalchemy.orm import Session

from app.core.logging_config import get_logger
from app.models import PublishTask, MonitorResult
from app.schemas.business import (
    PublishTaskCreate,
    PublishTaskUpdate,
    PublishTaskListParams,
    MonitorResultCreate,
    MonitorResultListParams,
    MonitorTriggerRequest,
)
from app.service.content_service import ContentService
from app.service.auth_service import EnterpriseService

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
        if asset.status not in ("approved", "published"):
            raise ValueError("内容未通过人审，不允许发布")
        payload = data.model_dump(exclude={"metadata"}, by_alias=True, exclude_none=True)
        payload.pop("draft_id", None)
        payload["enterprise_id"] = enterprise_id
        payload["content_asset_id"] = asset.id
        payload["status"] = "pending"
        payload["utm_content"] = str(asset.id)
        payload["metadata_"] = data.metadata_ or {}
        t = PublishTask(**payload)
        db.add(t)
        db.commit()
        db.refresh(t)
        logger.info("PublishTask created id=%s enterprise=%s mode=%s", t.id, enterprise_id, data.mode)
        return t

    @staticmethod
    def run_publish_auto(db: Session, enterprise_id: int, tid: int) -> PublishTask:
        t = PublishService.get(db, enterprise_id, tid)
        if not t:
            raise ValueError("任务不存在")
        upd = PublishTaskUpdate(status="published")
        if not t.published_id:
            upd.published_id = f"pub-{t.id}-{_rand_id(8)}"
        if not t.published_url:
            if t.target_url:
                upd.published_url = t.target_url
            else:
                upd.published_url = f"https://geo.example.com/published/{enterprise_id}/{t.id}"
        upd.published_at = datetime.utcnow()
        return PublishService._apply(db, t, upd)

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
