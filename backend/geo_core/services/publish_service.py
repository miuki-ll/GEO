from typing import List, Tuple, Optional, Dict, Any
from datetime import datetime, timedelta
import random
import string

from sqlalchemy.orm import Session

from geo_core.core.logging_config import get_logger
from geo_core.models import PublishTask, MonitorResult
from geo_core.schemas.business import (
    PublishTaskCreate,
    PublishTaskUpdate,
    PublishTaskListParams,
    MonitorResultCreate,
    MonitorResultListParams,
    MonitorTriggerRequest,
)
from geo_core.services.content_service import ContentService
from geo_core.services.auth_service import EnterpriseService

logger = get_logger(__name__)


def _rand_id(n: int = 12) -> str:
    return "".join(random.choices(string.ascii_letters + string.digits, k=n))


class PublishService:
    @staticmethod
    def list(db: Session, enterprise_id: int, params: PublishTaskListParams) -> Tuple[List[PublishTask], int]:
        q = db.query(PublishTask).filter(PublishTask.enterprise_id == enterprise_id)
        if params.draft_id:
            q = q.filter(PublishTask.draft_id == params.draft_id)
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
        draft = ContentService.get(db, enterprise_id, data.draft_id)
        if not draft:
            raise ValueError("草稿不存在")
        if draft.status not in ("approved", "published"):
            raise ValueError("草稿未通过人审，不允许发布")
        payload = data.model_dump(exclude={"metadata"}, by_alias=True)
        payload["enterprise_id"] = enterprise_id
        payload["status"] = "pending"
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


class MonitorService:
    @staticmethod
    def list(db: Session, enterprise_id: int, params: MonitorResultListParams) -> Tuple[List[MonitorResult], int]:
        q = db.query(MonitorResult).filter(MonitorResult.enterprise_id == enterprise_id)
        if params.pool_type:
            q = q.filter(MonitorResult.pool_type == params.pool_type)
        if params.engine:
            q = q.filter(MonitorResult.engine == params.engine)
        if params.scenario_id:
            q = q.filter(MonitorResult.scenario_id == params.scenario_id)
        if params.batch_no:
            q = q.filter(MonitorResult.batch_no == params.batch_no)
        total = q.count()
        items = q.order_by(MonitorResult.created_at.desc()).offset((params.page - 1) * params.page_size).limit(params.page_size).all()
        return items, total

    @staticmethod
    def trigger(db: Session, enterprise_id: int, req: MonitorTriggerRequest) -> Dict[str, Any]:
        from geo_core.services import ScenarioService
        engines = ["豆包", "DeepSeek", "Kimi", "文心一言"]
        if req.scenario_ids:
            scenario_ids = req.scenario_ids
        else:
            srv = ScenarioService()
            items, _ = srv.list(
                db, enterprise_id,
                type("P", (), {"channel": None, "skill": None, "status": None, "keyword": "", "page": 1, "page_size": 100})(),
            )
            scenario_ids = [s.id for s in items] or [None]
        batch_no = f"batch-{enterprise_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{_rand_id(4)}"
        created_count = 0
        for sid in scenario_ids:
            for eng in engines:
                mr = MonitorResult(
                    enterprise_id=enterprise_id,
                    pool_type=req.pool,
                    engine=eng,
                    scenario_id=sid,
                    query="模拟：敏感肌推荐哪家美容院？",
                    mentioned=random.random() < 0.65,
                    mention_snippet="示例提及：" if random.random() < 0.65 else None,
                    trust_score=round(0.4 + random.random() * 0.55, 3),
                    position_rank=random.randint(1, 8),
                    run_at=datetime.utcnow(),
                    batch_no=batch_no,
                    competitor_mentions=[],
                )
                if not mr.mentioned:
                    mr.trust_score = round(mr.trust_score * 0.5, 3)
                db.add(mr)
                created_count += 1
        db.commit()
        EnterpriseService.touch_kb(db, enterprise_id)
        logger.info("MonitorService trigger pool=%s n=%d batch=%s", req.pool, created_count, batch_no)
        return {"batch_no": batch_no, "created": created_count, "scenarios": len(scenario_ids)}

    @staticmethod
    def latest_trend(db: Session, enterprise_id: int, pool: str = "core", days: int = 7) -> List[Dict[str, Any]]:
        results = (
            db.query(MonitorResult)
            .filter(
                MonitorResult.enterprise_id == enterprise_id,
                MonitorResult.pool_type == pool,
                MonitorResult.created_at >= datetime.utcnow() - timedelta(days=days),
            )
            .order_by(MonitorResult.created_at.asc())
            .all()
        )
        by_day: Dict[str, List[MonitorResult]] = {}
        for r in results:
            key = r.created_at.strftime("%Y-%m-%d")
            by_day.setdefault(key, []).append(r)
        out = []
        for day in sorted(by_day.keys()):
            rs = by_day[day]
            total = len(rs)
            m = sum(1 for r in rs if r.mentioned)
            avg_trust = round(sum(r.trust_score or 0 for r in rs) / total, 3) if total else 0.0
            out.append({"date": day, "samples": total, "mention_rate": round(m / total, 3) if total else 0.0, "avg_trust": avg_trust})
        return out
