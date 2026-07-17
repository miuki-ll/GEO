from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.core.logging_config import get_logger
from app.models import StrategyPack, Scenario
from app.schemas.business import (
    StrategyPackCreate,
    StrategyPackUpdate,
    StrategyPackListParams,
    PersonaData,
)
from app.schemas.strategy import ChannelWeight
from app.channel_weights import (
    compute_mixed_weight,
    load_handoff_mock,
    build_five_zone_payload,
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
    def draft_view(pack: StrategyPack) -> Dict[str, Any]:
        meta = pack.metadata_ or {}
        five = meta.get("five_zone")
        if five:
            view = dict(five)
            view["id"] = pack.id
            view["status"] = pack.status
            view["version"] = pack.version
            view["confirmed_at"] = pack.confirmed_at.isoformat() if pack.confirmed_at else None
            return view
        return {
            "id": pack.id,
            "status": pack.status,
            "version": pack.version,
            "persona": pack.persona or {},
            "competitors": {"profiles": pack.competitors or [], "differentiation_brief": "", "content_gaps": []},
            "scenarios": {
                "candidates": pack.scenarios or [],
                "recommended_count": min(3, len(pack.scenarios or [])),
                "max": 5,
            },
            "channels": pack.channels or [],
            "keywords": (pack.metadata_ or {}).get("keywords") or {"layers": {}},
            "kb_freshness": {"warning": False, "updated_at": None},
            "confirmed_at": pack.confirmed_at.isoformat() if pack.confirmed_at else None,
        }

    @staticmethod
    def ensure_draft_default(db: Session, enterprise_id: int, actor_id: Optional[int] = None) -> StrategyPack:
        existing = StrategyPackService.get_latest(db, enterprise_id)
        if existing:
            meta = existing.metadata_ or {}
            if not meta.get("five_zone"):
                five = build_five_zone_payload()
                existing.metadata_ = {**meta, "five_zone": five, "mock": True}
                existing.channels = five["channels"]
                existing.scenarios = five["scenarios"]["candidates"]
                existing.competitors = five["competitors"]["profiles"]
                existing.persona = {
                    "age_range": five["persona"]["buyer_personas"][0]["age_range"],
                    "genders": ["女性"],
                    "core_needs": five["persona"]["buyer_personas"][0]["pain_tags"],
                    "decision_factors": five["persona"]["buyer_personas"][0]["decision_factors"],
                    "typical_queries": [s["user_query"] for s in five["scenarios"]["candidates"]],
                }
                db.commit()
                db.refresh(existing)
            return existing

        five = build_five_zone_payload()
        channel_models = []
        for c in five["channels"]:
            channel_models.append(
                ChannelWeight(
                    name=c["name"],
                    weight=c.get("weight", 0),
                    mode=c.get("mode", "auto"),
                    model_weight=c.get("model_weight"),
                    probe_weight=c.get("probe_weight"),
                    mixed_weight=c.get("mixed_weight"),
                    scenario_count=c.get("scenario_count"),
                )
            )
        default = StrategyPackCreate(
            version="1.0-draft",
            persona=PersonaData(
                age_range=five["persona"]["buyer_personas"][0]["age_range"],
                genders=["女性"],
                core_needs=five["persona"]["buyer_personas"][0]["pain_tags"],
                decision_factors=five["persona"]["buyer_personas"][0]["decision_factors"],
                typical_queries=[s["user_query"] for s in five["scenarios"]["candidates"]],
            ),
            competitors=[],
            scenarios=five["scenarios"]["candidates"],
            channels=channel_models,
            status="draft",
            metadata={"five_zone": five, "mock": True},
        )
        return StrategyPackService.create(db, enterprise_id, default, actor_id)

    @staticmethod
    def confirm(
        db: Session,
        enterprise_id: int,
        actor_id: int,
        pid: Optional[int] = None,
        selected_scenarios: Optional[List[str]] = None,
        channel_overrides: Optional[Dict[str, int]] = None,
    ) -> Tuple[StrategyPack, Dict[str, Any]]:
        pack = (
            StrategyPackService.get(db, enterprise_id, pid)
            if pid
            else StrategyPackService.get_latest(db, enterprise_id)
        )
        if not pack:
            raise ValueError("未找到可确认的方案包，请先创建草案")

        selected = selected_scenarios or []
        if not selected:
            raise ValueError("请至少选择 1 个 scenario")
        if len(selected) > 5:
            raise ValueError("最多选择 5 个 scenario")

        five = (pack.metadata_ or {}).get("five_zone") or build_five_zone_payload()
        candidates = {str(c["id"]): c for c in five.get("scenarios", {}).get("candidates", [])}
        chosen = []
        for sid in selected:
            c = candidates.get(str(sid))
            if not c:
                raise ValueError(f"未知 scenario: {sid}")
            chosen.append(c)

        for c in chosen:
            exists = (
                db.query(Scenario)
                .filter(Scenario.enterprise_id == enterprise_id, Scenario.user_query == c["user_query"])
                .first()
            )
            if exists:
                sc = exists
            else:
                sc = Scenario(
                    enterprise_id=enterprise_id,
                    title=(c["user_query"][:80]),
                    user_query=c["user_query"],
                    intent=c.get("intent"),
                    channel=c.get("channel") or "hosted",
                    skill=c.get("skill") or "faq",
                    priority=1,
                    status="ready",
                    target_engines=[],
                    fact_refs=[],
                )
                db.add(sc)
                db.flush()

            # B3：confirm 触发内容工厂（固定链）；TODO(WAIT_FOR: A2+A3)
            from app.service.content_service import ContentService

            ContentService.generate_for_unit(
                db,
                enterprise_id,
                scenario_id=sc.id,
                user_query=c["user_query"],
                channel=c.get("channel") or "hosted",
                skill=c.get("skill") or "faq",
            )

        pack.status = "confirmed"
        pack.confirmed_at = datetime.utcnow()
        pack.confirmed_by = actor_id
        pack.scenarios = chosen
        meta = dict(pack.metadata_ or {})
        if channel_overrides:
            meta["channel_overrides"] = channel_overrides
        meta["selected_scenarios"] = selected
        meta["content_job"] = "triggered"
        pack.metadata_ = meta
        db.commit()
        db.refresh(pack)
        logger.info("StrategyPack confirmed id=%s by user=%s selected=%s", pack.id, actor_id, selected)
        extra = {
            "strategy_pack_id": pack.id,
            "status": "confirmed",
            "next_route": "/content/drafts",
            "selected_scenarios": selected,
        }
        return pack, extra
