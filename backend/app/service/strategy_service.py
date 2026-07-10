from typing import List, Tuple, Optional
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.logging_config import get_logger
from app.models import StrategyPack
from app.schemas.business import (
    StrategyPackCreate,
    StrategyPackUpdate,
    StrategyPackListParams,
    StrategyPackResponse,
    PersonaData,
)

logger = get_logger(__name__)


class StrategyPackService:
    @staticmethod
    def list(db: Session, enterprise_id: int, params: StrategyPackListParams) -> Tuple[List[StrategyPack], int]:
        q = db.query(StrategyPack).filter(StrategyPack.enterprise_id == enterprise_id)
        if params.status:
            q = q.filter(StrategyPack.status == params.status)
        total = q.count()
        items = (
            q.order_by(StrategyPack.updated_at.desc())
            .offset((params.page - 1) * params.page_size)
            .limit(params.page_size)
            .all()
        )
        return items, total

    @staticmethod
    def get(db: Session, enterprise_id: int, pid: int) -> Optional[StrategyPack]:
        return (
            db.query(StrategyPack)
            .filter(StrategyPack.id == pid, StrategyPack.enterprise_id == enterprise_id)
            .first()
        )

    @staticmethod
    def get_latest(db: Session, enterprise_id: int, status: Optional[str] = None) -> Optional[StrategyPack]:
        q = db.query(StrategyPack).filter(StrategyPack.enterprise_id == enterprise_id)
        if status:
            q = q.filter(StrategyPack.status == status)
        return q.order_by(StrategyPack.updated_at.desc()).first()

    @staticmethod
    def create(db: Session, enterprise_id: int, data: StrategyPackCreate, actor_id: Optional[int] = None) -> StrategyPack:
        payload = data.model_dump(exclude={"metadata"}, by_alias=True)
        payload["enterprise_id"] = enterprise_id
        payload["status"] = payload.get("status") or "draft"
        payload["metadata_"] = data.metadata_ or {}
        pack = StrategyPack(**payload)
        db.add(pack)
        db.commit()
        db.refresh(pack)
        logger.info("StrategyPack created id=%s enterprise=%s", pack.id, enterprise_id)
        return pack

    @staticmethod
    def update(db: Session, enterprise_id: int, pid: int, data: StrategyPackUpdate) -> StrategyPack:
        pack = StrategyPackService.get(db, enterprise_id, pid)
        if not pack:
            raise ValueError("方案包不存在")
        upd = data.model_dump(exclude_unset=True, by_alias=True)
        if "metadata" in upd and upd["metadata"] is None:
            upd.pop("metadata", None)
        elif "metadata" in upd:
            upd["metadata_"] = upd.pop("metadata")
        for k, v in upd.items():
            setattr(pack, k, v)
        pack.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(pack)
        return pack

    @staticmethod
    def confirm(db: Session, enterprise_id: int, actor_id: int, pid: Optional[int] = None) -> StrategyPack:
        pack = StrategyPackService.get(db, enterprise_id, pid) if pid else StrategyPackService.get_latest(db, enterprise_id)
        if not pack:
            raise ValueError("未找到可确认的方案包，请先创建草案")
        if pack.status == "confirmed":
            return pack
        pack.status = "confirmed"
        pack.confirmed_at = datetime.utcnow()
        pack.confirmed_by = actor_id
        db.commit()
        db.refresh(pack)
        logger.info("StrategyPack confirmed id=%s by user=%s", pack.id, actor_id)
        return pack

    @staticmethod
    def ensure_draft_default(db: Session, enterprise_id: int, actor_id: Optional[int] = None) -> StrategyPack:
        existing = StrategyPackService.get_latest(db, enterprise_id)
        if existing:
            return existing
        default = StrategyPackCreate(
            version="1.0-draft",
            persona=PersonaData(
                age_range=[25, 45],
                genders=["女性"],
                core_needs=["补水", "抗衰", "敏感肌修护"],
                decision_factors=["口碑", "资质", "距离", "价格"],
                typical_queries=[
                    "XX区做敏感肌修护推荐哪家美容院？",
                    "夏天油皮补水美容院做什么项目？",
                ],
            ),
            status="draft",
        )
        return StrategyPackService.create(db, enterprise_id, default, actor_id)
