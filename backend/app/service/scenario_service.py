from typing import List, Tuple, Optional
from datetime import datetime
import json

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.logging_config import get_logger
from app.models import Scenario
from app.schemas.business import (
    ScenarioCreate,
    ScenarioUpdate,
    ScenarioListParams,
)
from app.utils.helpers import ensure_json_list, ensure_json_dict
from app.service.auth_service import EnterpriseService

logger = get_logger(__name__)


def _jloads(v, default):
    if v is None:
        return default
    if isinstance(v, (dict, list)):
        return v
    try:
        return json.loads(v)
    except Exception:
        return default


def _jdumps(v):
    if v is None:
        return "{}"
    if isinstance(v, str):
        return v
    try:
        return json.dumps(v, ensure_ascii=False)
    except Exception:
        return "{}"


class ScenarioService:
    @staticmethod
    def list(
        db: Session, enterprise_id: int, params: ScenarioListParams
    ) -> Tuple[List[Scenario], int]:
        q = db.query(Scenario).filter(Scenario.enterprise_id == enterprise_id)
        if params.channel:
            q = q.filter(Scenario.channel == params.channel)
        if params.skill:
            q = q.filter(Scenario.skill == params.skill)
        if params.status:
            q = q.filter(Scenario.status == params.status)
        if params.keyword:
            kw = f"%{params.keyword}%"
            q = q.filter(or_(Scenario.title.ilike(kw), Scenario.user_query.ilike(kw)))
        total = q.count()
        items = (
            q.order_by(Scenario.priority.asc(), Scenario.updated_at.desc())
            .offset((params.page - 1) * params.page_size)
            .limit(params.page_size)
            .all()
        )
        return items, total

    @staticmethod
    def get(db: Session, enterprise_id: int, sid: int) -> Optional[Scenario]:
        it = (
            db.query(Scenario)
            .filter(Scenario.id == sid, Scenario.enterprise_id == enterprise_id)
            .first()
        )
        return ScenarioService._load(it) if it else None

    @staticmethod
    def _load(it: Optional[Scenario]) -> Optional[Scenario]:
        if not it:
            return it
        target_engines_val = ensure_json_list(getattr(it, "target_engines", []))
        fact_refs_val = ensure_json_list(getattr(it, "fact_refs", []))
        persona_ref_val = ensure_json_dict(getattr(it, "persona_ref", {}))
        competitor_ref_val = ensure_json_dict(getattr(it, "competitor_ref", {}))
        if target_engines_val is not None and hasattr(it, "target_engines"):
            try:
                it.__dict__["target_engines"] = target_engines_val
            except Exception:
                object.__setattr__(it, "target_engines", target_engines_val)
        if fact_refs_val is not None and hasattr(it, "fact_refs"):
            try:
                it.__dict__["fact_refs"] = fact_refs_val
            except Exception:
                object.__setattr__(it, "fact_refs", fact_refs_val)
        if persona_ref_val is not None and hasattr(it, "persona_ref"):
            try:
                it.__dict__["persona_ref"] = persona_ref_val
            except Exception:
                object.__setattr__(it, "persona_ref", persona_ref_val)
        if competitor_ref_val is not None and hasattr(it, "competitor_ref"):
            try:
                it.__dict__["competitor_ref"] = competitor_ref_val
            except Exception:
                object.__setattr__(it, "competitor_ref", competitor_ref_val)
        return it

    @staticmethod
    def _save_dict(data: ScenarioCreate | ScenarioUpdate, payload: dict):
        if hasattr(data, "target_engines") and data.target_engines is not None:
            payload["target_engines"] = list(data.target_engines)
        if hasattr(data, "fact_refs") and data.fact_refs is not None:
            payload["fact_refs"] = list(data.fact_refs)
        return payload

    @staticmethod
    def create(db: Session, enterprise_id: int, data: ScenarioCreate) -> Scenario:
        payload = data.model_dump(
            exclude={"target_engines", "fact_refs", "persona_ref", "competitor_ref", "metadata"}, by_alias=True
        )
        payload["enterprise_id"] = enterprise_id
        payload["target_engines"] = list(data.target_engines or [])
        payload["fact_refs"] = list(data.fact_refs or [])
        payload["persona_ref"] = dict(data.persona_ref or {})
        payload["competitor_ref"] = dict(data.competitor_ref or {})
        payload["metadata_"] = data.metadata_ or {}
        it = Scenario(**payload)
        db.add(it)
        db.commit()
        db.refresh(it)
        EnterpriseService.touch_kb(db, enterprise_id)
        logger.info("Scenario created id=%s enterprise=%s", it.id, enterprise_id)
        return ScenarioService._load(it)

    @staticmethod
    def update(
        db: Session, enterprise_id: int, sid: int, data: ScenarioUpdate
    ) -> Scenario:
        it = ScenarioService.get(db, enterprise_id, sid)
        if not it:
            raise ValueError("Scenario 不存在")
        upd = data.model_dump(exclude_unset=True, by_alias=True)
        if "target_engines" in upd and upd["target_engines"] is not None:
            upd["target_engines"] = list(upd["target_engines"])
        if "fact_refs" in upd and upd["fact_refs"] is not None:
            upd["fact_refs"] = list(upd["fact_refs"])
        if "persona_ref" in upd and upd["persona_ref"] is not None:
            upd["persona_ref"] = dict(upd["persona_ref"])
        if "competitor_ref" in upd and upd["competitor_ref"] is not None:
            upd["competitor_ref"] = dict(upd["competitor_ref"])
        if "metadata" in upd and upd["metadata"] is None:
            upd.pop("metadata", None)
        elif "metadata" in upd:
            upd["metadata_"] = upd.pop("metadata")
        for k, v in upd.items():
            setattr(it, k, v)
        it.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(it)
        return ScenarioService._load(it)

    @staticmethod
    def delete(db: Session, enterprise_id: int, sid: int) -> None:
        it = ScenarioService.get(db, enterprise_id, sid)
        if not it:
            raise ValueError("Scenario 不存在")
        db.delete(it)
        db.commit()
        logger.info("Scenario deleted id=%s", sid)

    @staticmethod
    def bulk_upsert_placeholder(
        db: Session, enterprise_id: int, items: List[ScenarioCreate]
    ) -> List[Scenario]:
        out = []
        for it in items:
            try:
                out.append(ScenarioService.create(db, enterprise_id, it))
            except Exception as e:
                logger.warning("bulk upsert skip: %s", e)
        return out
