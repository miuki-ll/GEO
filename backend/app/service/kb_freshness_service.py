"""KB 新鲜度与 thin KB 门槛检查。"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from sqlalchemy.orm import Session

from app.models import Enterprise, KBFact, KBFaq, Service


def kb_freshness(db: Session, enterprise_id: int) -> Dict[str, Any]:
    ent = db.query(Enterprise).filter(Enterprise.id == enterprise_id).first()
    kb_updated_at = ent.kb_updated_at if ent else None
    stale = kb_updated_at is None
    return {
        "kb_updated_at": kb_updated_at.isoformat() if kb_updated_at else None,
        "is_stale": stale,
        "message": "KB 尚未更新" if stale else "KB 已更新",
    }


def thin_kb_check(db: Session, enterprise_id: int) -> Dict[str, Any]:
    """thin KB 门槛：≥2 Services 且 ≥3 FAQs（verified 优先）。"""
    service_count = db.query(Service).filter(
        Service.enterprise_id == enterprise_id,
        Service.status == "active",
    ).count()
    faq_count = db.query(KBFaq).filter(KBFaq.enterprise_id == enterprise_id).count()
    verified_facts = db.query(KBFact).filter(
        KBFact.enterprise_id == enterprise_id,
        KBFact.verified == True,  # noqa: E712
    ).count()
    passed = service_count >= 2 and faq_count >= 3
    return {
        "passed": passed,
        "service_count": service_count,
        "faq_count": faq_count,
        "verified_facts": verified_facts,
        "requirements": {"min_services": 2, "min_faqs": 3},
        "message": "thin KB 已达标，可确认方案包" if passed else "thin KB 未达标：请至少录入 2 个服务项目 + 3 条 FAQ",
    }
