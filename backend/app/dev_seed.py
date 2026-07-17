"""开发态：租户无业务数据时，向数据库写入可演示的假数据。

仅应在 APP_ENV=development 调用。数据进 MySQL，前端只读 API。
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def ensure_tenant_seed_data(db: "Session", enterprise_id: int, actor_id: Optional[int] = None) -> Dict[str, Any]:
    """确保方案包草案、KB 假事实、至少若干草稿存在于库中。"""
    from app.channel_weights import build_five_zone_payload
    from app.content_factory import load_fixture_kb_facts
    from app.core.config import settings
    from app.models import ContentAsset, KBFact, Scenario
    from app.service.content_service import ContentService
    from app.service.strategy_service import StrategyPackService

    if not settings.is_dev:
        return {"skipped": True, "reason": "not_dev"}

    report: Dict[str, Any] = {"enterprise_id": enterprise_id, "created": {}}

    # 1) KB facts
    existing_facts = db.query(KBFact).filter(KBFact.enterprise_id == enterprise_id).count()
    if existing_facts == 0:
        created_ids: List[int] = []
        for row in load_fixture_kb_facts():
            fact = KBFact(
                enterprise_id=enterprise_id,
                title=row.get("title") or "seed fact",
                content=row.get("content") or "",
                category=row.get("category") or "general",
                source_type="seed",
                verified=True,
                metadata_={"seed_fixture_id": row.get("id")},
            )
            db.add(fact)
            db.flush()
            created_ids.append(fact.id)
        db.commit()
        report["created"]["kb_facts"] = created_ids
        logger.info("seeded kb_facts enterprise=%s n=%s", enterprise_id, len(created_ids))

    # 2) Strategy pack draft
    pack = StrategyPackService.ensure_draft_default(db, enterprise_id, actor_id)
    report["strategy_pack_id"] = pack.id

    # 3) Content drafts if empty
    asset_n = db.query(ContentAsset).filter(ContentAsset.enterprise_id == enterprise_id).count()
    if asset_n == 0:
        five = (pack.metadata_ or {}).get("five_zone") or build_five_zone_payload()
        candidates: List[Dict[str, Any]] = list(
            (five.get("scenarios") or {}).get("candidates") or []
        )[:2]
        seeded_draft_ids = []
        for c in candidates:
            sc = (
                db.query(Scenario)
                .filter(
                    Scenario.enterprise_id == enterprise_id,
                    Scenario.user_query == c.get("user_query"),
                )
                .first()
            )
            if not sc:
                sc = Scenario(
                    enterprise_id=enterprise_id,
                    title=(c.get("user_query") or "seed")[:80],
                    user_query=c.get("user_query") or "seed query",
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

            draft = ContentService.generate_for_unit(
                db,
                enterprise_id,
                scenario_id=sc.id,
                user_query=c.get("user_query") or sc.user_query,
                channel=c.get("channel") or "hosted",
                skill=c.get("skill") or "faq",
            )
            seeded_draft_ids.append(draft.id)
        report["created"]["content_assets"] = seeded_draft_ids
        logger.info("seeded content_assets enterprise=%s ids=%s", enterprise_id, seeded_draft_ids)

    return report
