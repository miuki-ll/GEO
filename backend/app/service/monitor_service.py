from typing import List, Tuple, Dict, Any
from datetime import datetime, timedelta
import random
import string

from sqlalchemy.orm import Session

from app.core.logging_config import get_logger
from app.models import MonitorResult
from app.schemas.business import MonitorResultListParams, MonitorTriggerRequest
from app.service.auth_service import EnterpriseService

logger = get_logger(__name__)


def _rand_id(n: int = 12) -> str:
    return "".join(random.choices(string.ascii_letters + string.digits, k=n))


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
        from app.service.scenario_service import ScenarioService
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
