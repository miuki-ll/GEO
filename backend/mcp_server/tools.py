"""GEO MCP 只读工具 — 与 Harness ToolRegistry 同源（MVP 读 KB）。"""

from typing import Any, Dict, List, Optional

from app.core.db import SessionLocal
from app.service.kb_service import FactService, KBSummaryService
from app.service.kb_freshness_service import kb_freshness, thin_kb_check
from app.schemas.kb import KBFactListParams


def kb_fetch(enterprise_id: int, fact_ids: Optional[List[int]] = None, limit: int = 10) -> Dict[str, Any]:
    db = SessionLocal()
    try:
        if fact_ids:
            items = []
            for fid in fact_ids:
                f = FactService.get(db, enterprise_id, fid)
                if f:
                    items.append({"id": f.id, "title": f.title, "content": f.content, "verified": f.verified})
            return {"enterprise_id": enterprise_id, "facts": items}
        facts, total = FactService.list(db, enterprise_id, KBFactListParams(page=1, page_size=min(limit, 50)))
        return {
            "enterprise_id": enterprise_id,
            "total": total,
            "facts": [{"id": f.id, "title": f.title, "content": f.content, "verified": f.verified} for f in facts],
        }
    finally:
        db.close()


def kb_freshness_tool(enterprise_id: int) -> Dict[str, Any]:
    db = SessionLocal()
    try:
        return {
            "enterprise_id": enterprise_id,
            "freshness": kb_freshness(db, enterprise_id),
            "thin_kb": thin_kb_check(db, enterprise_id),
        }
    finally:
        db.close()


def kb_summary_tool(enterprise_id: int) -> Dict[str, Any]:
    db = SessionLocal()
    try:
        return KBSummaryService.summary(db, enterprise_id).model_dump()
    finally:
        db.close()
