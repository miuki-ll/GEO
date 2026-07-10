from typing import Dict
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.core.logging_config import get_logger
from app.models import Scenario, ContentAsset, ContentDraft, PublishTask, MonitorResult, OutcomeSnapshot
from app.schemas.business import (
    DashboardData,
    DashboardKpi,
    ChannelBreakdown,
    EngineBreakdown,
)

logger = get_logger(__name__)


class DashboardService:
    @staticmethod
    def compute(db: Session, enterprise_id: int, period: str = "week") -> DashboardData:
        days = {"day": 1, "week": 7, "month": 30, "quarter": 90}.get(period, 7)
        start = datetime.utcnow() - timedelta(days=days)
        n_scenarios = db.query(Scenario).filter(Scenario.enterprise_id == enterprise_id, Scenario.created_at >= start).count()
        n_published = db.query(PublishTask).filter(PublishTask.enterprise_id == enterprise_id, PublishTask.status == "published", PublishTask.published_at >= start).count()
        n_pending_review = db.query(ContentAsset).filter(ContentAsset.enterprise_id == enterprise_id, ContentAsset.status.in_(["draft", "reviewed"])).count()
        rows = db.query(MonitorResult).filter(MonitorResult.enterprise_id == enterprise_id, MonitorResult.created_at >= start).all()
        total = len(rows)
        mention_cnt = sum(1 for r in rows if r.mentioned)
        avg_trust = round(sum(r.trust_score or 0 for r in rows) / total, 3) if total else 0.0
        kpi = DashboardKpi(
            total_scenarios=n_scenarios,
            total_drafts_published=n_published,
            avg_mention_rate=round(mention_cnt / total, 3) if total else 0.0,
            avg_trust_score=avg_trust,
            core_queries=sum(1 for r in rows if r.pool_type == "core"),
            probe_discoveries=sum(1 for r in rows if r.pool_type == "probe"),
            pending_review=n_pending_review,
            kb_facts_verified=DashboardService._kb_verified(db, enterprise_id),
        )
        by_channel = []
        for ch in ["hosted", "xiaohongshu", "zhihu", "douyin", "meituan", "baidu_zhidao"]:
            sub = db.query(PublishTask).filter(PublishTask.enterprise_id == enterprise_id, PublishTask.channel == ch).all()
            pub_n = sum(1 for s in sub if s.status == "published")
            by_channel.append(ChannelBreakdown(channel=ch, published=pub_n, mention_rate=0.0, avg_trust=0.0))
        by_engine = []
        engines = ["豆包", "DeepSeek", "Kimi", "文心一言"]
        for eng in engines:
            sub = [r for r in rows if r.engine == eng]
            n = len(sub)
            if n:
                mr = round(sum(1 for r in sub if r.mentioned) / n, 3)
                at = round(sum(r.trust_score or 0 for r in sub) / n, 3)
            else:
                mr = 0.0
                at = 0.0
            by_engine.append(EngineBreakdown(engine=eng, mention_rate=mr, avg_trust=at, sample_size=n))
        alerts = []
        if kpi.avg_mention_rate < 0.50:
            alerts.append({"level": "critical", "type": "mention_drop", "msg": "整体 AI 提及率低于 50%，建议立即触发迭代诊断"})
        if kpi.pending_review > 10:
            alerts.append({"level": "warning", "type": "review_backlog", "msg": f"待审核草稿 {kpi.pending_review} 条，建议分配审核资源"})
        if kpi.kb_facts_verified < 50:
            alerts.append({"level": "info", "type": "kb_thin", "msg": "已核验事实不足（建议 50+），补充 Fact 可提升引用覆盖率"})
        if total < 30:
            alerts.append({"level": "info", "type": "monitor_thin", "msg": f"监测样本偏少（当前 {total} 条），建议每周触发 Core+Probe 监测以积累基线"})
        if n_published < 5:
            alerts.append({"level": "info", "type": "publish_low", "msg": f"已发布稿件 {n_published} 篇，建议推动审核通过的草稿尽快进入发布队列"})
        from app.service.monitor_service import MonitorService
        trend = MonitorService.latest_trend(db, enterprise_id, pool="core", days=days)
        return DashboardData(period=period, kpi=kpi, by_channel=by_channel, by_engine=by_engine, trend=trend, alerts=alerts)

    @staticmethod
    def _kb_verified(db: Session, enterprise_id: int) -> int:
        try:
            from app.models.kb import KBFact
            return db.query(KBFact).filter(
                KBFact.enterprise_id == enterprise_id,
                KBFact.verified == True,
            ).count()
        except Exception:
            return 0

    @staticmethod
    def take_snapshot(db: Session, enterprise_id: int, period: str = "week") -> OutcomeSnapshot:
        d = DashboardService.compute(db, enterprise_id, period)
        snap = OutcomeSnapshot(
            enterprise_id=enterprise_id,
            period=period,
            period_start=datetime.utcnow() - timedelta(days={"week": 7, "day": 1, "month": 30, "quarter": 90}.get(period, 7)),
            period_end=datetime.utcnow(),
            snapshot_type="dashboard",
            metrics=d.kpi.model_dump(),
            breakdown={"by_channel": [c.model_dump() for c in d.by_channel], "by_engine": [e.model_dump() for e in d.by_engine], "trend": d.trend},
        )
        db.add(snap)
        db.commit()
        db.refresh(snap)
        return snap
