from typing import List, Tuple, Optional, TypeVar, Type
from datetime import datetime

from sqlalchemy import or_, desc
from sqlalchemy.orm import Session

from app.core.logging_config import get_logger
from app.models import KBFact, KBFaq, KBSignal, KBExternal, Enterprise
from app.schemas.kb import (
    KBFactCreate,
    KBFactUpdate,
    KBFactResponse,
    KBFactListParams,
    KBFaqCreate,
    KBFaqUpdate,
    KBFaqResponse,
    KBFaqListParams,
    KBSignalCreate,
    KBSignalUpdate,
    KBSignalResponse,
    KBSignalListParams,
    KBExternalCreate,
    KBExternalUpdate,
    KBExternalResponse,
    KBExternalListParams,
    KBSummary,
)
from app.utils.helpers import ensure_json_list

logger = get_logger(__name__)

T = TypeVar("T")


class _BaseKBService:
    MODEL: type = object
    RESP: type = object

    @classmethod
    def _list(
        cls,
        db: Session,
        enterprise_id: int,
        params,
    ) -> Tuple[List, int]:
        q = db.query(cls.MODEL).filter(cls.MODEL.enterprise_id == enterprise_id)
        if getattr(params, "category", None):
            q = q.filter(cls.MODEL.category == params.category)
        if getattr(params, "status", None):
            q = q.filter(cls.MODEL.status == params.status)
        if getattr(params, "verified", None) is not None:
            q = q.filter(cls.MODEL.verified == params.verified)
        if getattr(params, "signal_type", None):
            q = q.filter(cls.MODEL.signal_type == params.signal_type)
        if getattr(params, "source_type", None):
            q = q.filter(cls.MODEL.source_type == params.source_type)
        if getattr(params, "source_platform", None):
            q = q.filter(cls.MODEL.source_platform == params.source_platform)
        if params.keyword:
            kw = f"%{params.keyword}%"
            title_col = getattr(cls.MODEL, "title", None)
            question_col = getattr(cls.MODEL, "question", None)
            content_col = getattr(cls.MODEL, "content", None)
            clauses = []
            if title_col is not None:
                clauses.append(title_col.ilike(kw))
            if question_col is not None:
                clauses.append(question_col.ilike(kw))
            if content_col is not None:
                clauses.append(content_col.ilike(kw))
            q = q.filter(or_(*clauses))
        total = q.count()
        items = (
            q.order_by(desc(cls.MODEL.updated_at))
            .offset((params.page - 1) * params.page_size)
            .limit(params.page_size)
            .all()
        )
        return items, total

    @classmethod
    def _get(cls, db: Session, enterprise_id: int, item_id: int) -> Optional:
        return (
            db.query(cls.MODEL)
            .filter(cls.MODEL.id == item_id, cls.MODEL.enterprise_id == enterprise_id)
            .first()
        )

    @classmethod
    def _create(
        cls,
        db: Session,
        enterprise_id: int,
        data,
    ):
        payload = data.model_dump(exclude={"tags", "fact_refs", "metadata"}, by_alias=True)
        payload["enterprise_id"] = enterprise_id
        if hasattr(data, "tags"):
            payload["tags"] = list(data.tags or [])
        if hasattr(data, "fact_refs"):
            payload["fact_refs"] = list(data.fact_refs or [])
        if hasattr(data, "metadata_"):
            payload["metadata_"] = data.metadata_ or {}
        item = cls.MODEL(**payload)
        db.add(item)
        db.commit()
        db.refresh(item)
        Enterprise.touch_kb(db, enterprise_id)
        logger.info(
            "KB create %s id=%s enterprise=%s",
            cls.MODEL.__name__,
            item.id,
            enterprise_id,
        )
        return item

    @classmethod
    def _update(
        cls,
        db: Session,
        enterprise_id: int,
        item_id: int,
        data,
    ):
        item = cls._get(db, enterprise_id, item_id)
        if not item:
            raise ValueError("记录不存在")
        update_dict = data.model_dump(exclude_unset=True, by_alias=True)
        if "tags" in update_dict and update_dict["tags"] is not None:
            update_dict["tags"] = list(update_dict["tags"])
        if "fact_refs" in update_dict and update_dict["fact_refs"] is not None:
            update_dict["fact_refs"] = list(update_dict["fact_refs"])
        if "metadata" in update_dict and update_dict["metadata"] is None:
            update_dict.pop("metadata", None)
        elif "metadata" in update_dict:
            update_dict["metadata_"] = update_dict.pop("metadata")
        for k, v in update_dict.items():
            setattr(item, k, v)
        item.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(item)
        Enterprise.touch_kb(db, enterprise_id)
        return item

    @classmethod
    def _delete(cls, db: Session, enterprise_id: int, item_id: int) -> None:
        item = cls._get(db, enterprise_id, item_id)
        if not item:
            raise ValueError("记录不存在")
        db.delete(item)
        db.commit()
        Enterprise.touch_kb(db, enterprise_id)
        logger.info(
            "KB delete %s id=%s enterprise=%s",
            cls.MODEL.__name__,
            item_id,
            enterprise_id,
        )

    @classmethod
    def _post_load(cls, item):
        if item is None:
            return None
        tags_val = None
        fact_refs_val = None
        if hasattr(item, "tags"):
            tags_val = ensure_json_list(getattr(item, "tags", []))
        if hasattr(item, "fact_refs"):
            fact_refs_val = ensure_json_list(getattr(item, "fact_refs", []))
        if tags_val is not None and hasattr(item, "tags"):
            try:
                item.__dict__["tags"] = tags_val
            except Exception:
                object.__setattr__(item, "tags", tags_val)
        if fact_refs_val is not None and hasattr(item, "fact_refs"):
            try:
                item.__dict__["fact_refs"] = fact_refs_val
            except Exception:
                object.__setattr__(item, "fact_refs", fact_refs_val)
        return item


class FactService(_BaseKBService):
    MODEL = KBFact
    RESP = KBFactResponse

    @classmethod
    def list(cls, db, eid, params):
        return cls._list(db, eid, params)

    @classmethod
    def get(cls, db, eid, iid):
        it = cls._get(db, eid, iid)
        return cls._post_load(it) if it else None

    @classmethod
    def create(cls, db, eid, data: KBFactCreate):
        it = cls._create(db, eid, data)
        return cls._post_load(it)

    @classmethod
    def update(cls, db, eid, iid, data: KBFactUpdate):
        it = cls._update(db, eid, iid, data)
        return cls._post_load(it)

    @classmethod
    def delete(cls, db, eid, iid):
        cls._delete(db, eid, iid)


class FaqService(_BaseKBService):
    MODEL = KBFaq
    RESP = KBFaqResponse

    @classmethod
    def list(cls, db, eid, params):
        return cls._list(db, eid, params)

    @classmethod
    def get(cls, db, eid, iid):
        it = cls._get(db, eid, iid)
        return cls._post_load(it) if it else None

    @classmethod
    def create(cls, db, eid, data: KBFaqCreate):
        it = cls._create(db, eid, data)
        return cls._post_load(it)

    @classmethod
    def update(cls, db, eid, iid, data: KBFaqUpdate):
        it = cls._update(db, eid, iid, data)
        return cls._post_load(it)

    @classmethod
    def delete(cls, db, eid, iid):
        cls._delete(db, eid, iid)


class SignalService(_BaseKBService):
    MODEL = KBSignal
    RESP = KBSignalResponse

    @classmethod
    def list(cls, db, eid, params):
        return cls._list(db, eid, params)

    @classmethod
    def get(cls, db, eid, iid):
        it = cls._get(db, eid, iid)
        return cls._post_load(it) if it else None

    @classmethod
    def create(cls, db, eid, data: KBSignalCreate):
        it = cls._create(db, eid, data)
        return cls._post_load(it)

    @classmethod
    def update(cls, db, eid, iid, data: KBSignalUpdate):
        it = cls._update(db, eid, iid, data)
        return cls._post_load(it)

    @classmethod
    def delete(cls, db, eid, iid):
        cls._delete(db, eid, iid)


class ExternalService(_BaseKBService):
    MODEL = KBExternal
    RESP = KBExternalResponse

    @classmethod
    def list(cls, db, eid, params):
        return cls._list(db, eid, params)

    @classmethod
    def get(cls, db, eid, iid):
        it = cls._get(db, eid, iid)
        return cls._post_load(it) if it else None

    @classmethod
    def create(cls, db, eid, data: KBExternalCreate):
        it = cls._create(db, eid, data)
        return cls._post_load(it)

    @classmethod
    def update(cls, db, eid, iid, data: KBExternalUpdate):
        it = cls._update(db, eid, iid, data)
        return cls._post_load(it)

    @classmethod
    def delete(cls, db, eid, iid):
        cls._delete(db, eid, iid)


class KBSummaryService:
    @staticmethod
    def summary(db: Session, enterprise_id: int) -> KBSummary:
        facts = db.query(KBFact).filter(KBFact.enterprise_id == enterprise_id)
        faqs = db.query(KBFaq).filter(KBFaq.enterprise_id == enterprise_id)
        sigs = db.query(KBSignal).filter(KBSignal.enterprise_id == enterprise_id)
        exts = db.query(KBExternal).filter(KBExternal.enterprise_id == enterprise_id)
        ent = (
            db.query(Enterprise.kb_updated_at)
            .filter(Enterprise.id == enterprise_id)
            .scalar()
        )
        return KBSummary(
            facts=facts.count(),
            faqs=faqs.count(),
            signals=sigs.count(),
            externals=exts.count(),
            verified_facts=facts.filter(KBFact.verified == True).count(),  # noqa: E712
            verified_faqs=faqs.filter(KBFaq.verified == True).count(),  # noqa: E712
            last_updated=ent,
        )
