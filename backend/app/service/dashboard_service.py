"""B7 效果舱：KPI（含 T0/T1 Δ）+ 四层漏斗壳。"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.core.logging_config import get_logger
from app.models import Scenario, ContentAsset, PublishTask, MonitorResult, OutcomeSnapshot
from app.schemas.business import (
    DashboardData,
    DashboardKpi,
    DashboardFunnel,
    ChannelBreakdown,
    EngineBreakdown,
)
from app.monitor_delta import compute_delta, normalize_engine

logger = get_logger(__name__)


class DashboardService:
    @staticmethod
    def compute(db: Session, enterprise_id: int, period: str = "week") -> DashboardData:
        days = {"day": 1, "week": 7, "month": 30, "quarter": 90}.get(period, 7)
        start = datetime.utcnow() - timedelta(days=days)

        n_scenarios = (
            db.query(Scenario)
            .filter(Scenario.enterprise_id == enterprise_id, Scenario.created_at >= start)
            .count()
        )
        n_published = (
            db.query(PublishTask)
            .filter(
                PublishTask.enterprise_id == enterprise_id,
                PublishTask.status == "published",
                PublishTask.published_at >= start,
            )
            .count()
        )
        n_pending_review = (
            db.query(ContentAsset)
            .filter(
                ContentAsset.enterprise_id == enterprise_id,
                ContentAsset.status.in_(["draft", "ready", "reviewed"]),
            )
            .count()
        )

        rows = (
            db.query(MonitorResult)
            .filter(MonitorResult.enterprise_id == enterprise_id)
            .all()
        )
        # Δ 用全量 T0/T1（不按 period 截断 T0，避免假 T0 被滤掉）
        t0 = [r for r in rows if r.baseline and r.pool_type == "core"]
        t1 = [r for r in rows if (not r.baseline) and r.pool_type == "core"]
        delta = compute_delta(t0, t1)

        recent = [r for r in rows if r.created_at and r.created_at >= start]
        total = len(recent)
        mention_cnt = sum(1 for r in recent if r.mentioned)
        avg_trust = round(sum(r.trust_score or 0 for r in recent) / total, 3) if total else 0.0

        hallu_n = 0
        hallu_d = 0
        for r in recent:
            m = r.metrics if isinstance(r.metrics, dict) else {}
            if "hallucination" in m:
                hallu_d += 1
                if m.get("hallucination"):
                    hallu_n += 1
        hallucination_rate = round(hallu_n / hallu_d, 4) if hallu_d else 0.0

        kpi = DashboardKpi(
            mention_rate_t0=delta["mention_rate_t0"],
            mention_rate_t1=delta["mention_rate_t1"],
            delta_mention=delta["delta_mention"],
            hallucination_rate=hallucination_rate,
            total_scenarios=n_scenarios,
            total_drafts_published=n_published,
            avg_mention_rate=round(mention_cnt / total, 3) if total else 0.0,
            avg_trust_score=avg_trust,
            core_queries=sum(1 for r in recent if r.pool_type == "core"),
            probe_discoveries=sum(1 for r in recent if r.pool_type == "probe"),
            pending_review=n_pending_review,
            kb_facts_verified=DashboardService._kb_verified(db, enterprise_id),
        )

        funnel = DashboardService._build_funnel(
            db, enterprise_id, kpi=kpi, n_published=n_published, start=start
        )
        geo_efficiency = DashboardService._geo_efficiency(kpi, funnel)

        by_channel: List[ChannelBreakdown] = []
        for ch in ["hosted", "xiaohongshu", "zhihu", "dianping", "wechat"]:
            sub = (
                db.query(PublishTask)
                .filter(PublishTask.enterprise_id == enterprise_id, PublishTask.channel == ch)
                .all()
            )
            pub_n = sum(1 for s in sub if s.status == "published")
            by_channel.append(
                ChannelBreakdown(channel=ch, published=pub_n, mention_rate=0.0, avg_trust=0.0)
            )

        by_engine: List[EngineBreakdown] = []
        engine_keys = sorted({normalize_engine(r.engine or "") for r in recent} or {"doubao", "deepseek"})
        for eng in engine_keys:
            sub = [r for r in recent if normalize_engine(r.engine or "") == eng]
            n = len(sub)
            if n:
                mr = round(sum(1 for r in sub if r.mentioned) / n, 3)
                at = round(sum(r.trust_score or 0 for r in sub) / n, 3)
            else:
                mr = 0.0
                at = 0.0
            by_engine.append(EngineBreakdown(engine=eng, mention_rate=mr, avg_trust=at, sample_size=n))

        alerts: List[Dict[str, Any]] = []
        if delta.get("waiting_for_a7"):
            alerts.append(
                {
                    "level": "warning",
                    "type": "waiting_t0",
                    "msg": "尚无真 T0（baseline=true）。TODO(WAIT_FOR: A7)；可用监测页「种假 T0」演示 Δ。",
                }
            )
        if kpi.avg_mention_rate < 0.50 and total:
            alerts.append(
                {
                    "level": "critical",
                    "type": "mention_drop",
                    "msg": "整体 AI 提及率低于 50%，建议触发迭代诊断",
                }
            )
        if n_published < 5:
            alerts.append(
                {
                    "level": "info",
                    "type": "publish_low",
                    "msg": f"已发布稿件 {n_published} 篇，建议推动草稿进入发布队列",
                }
            )

        from app.service.monitor_service import MonitorService

        trend = MonitorService.latest_trend(db, enterprise_id, pool="core", days=days)

        return DashboardData(
            period=period,
            kpi=kpi,
            funnel=funnel,
            geo_efficiency=geo_efficiency,
            waiting_for_a7=bool(delta.get("waiting_for_a7")),
            todo="WAIT_FOR: A7" if delta.get("waiting_for_a7") else None,
            by_channel=by_channel,
            by_engine=by_engine,
            trend=trend,
            alerts=alerts,
        )

    @staticmethod
    def _build_funnel(
        db: Session,
        enterprise_id: int,
        *,
        kpi: DashboardKpi,
        n_published: int,
        start: datetime,
    ) -> DashboardFunnel:
        # exposure：有发布或有 T1 样本即视为曝光链路通
        exposure_ok = n_published > 0 or kpi.core_queries > 0 or kpi.mention_rate_t1 > 0
        # trust：平均信任或 T1 提及达标
        trust_ok = (kpi.avg_trust_score or 0) >= 0.4 or kpi.mention_rate_t1 >= 0.2
        form_submits = DashboardService._form_submits(db, enterprise_id, start)
        return DashboardFunnel(
            exposure={"ok": exposure_ok, "published": n_published},
            trust={"ok": trust_ok, "avg_trust_score": kpi.avg_trust_score},
            leads={"form_submits": form_submits},
            conversion={"manual_cost": None, "manual_revenue": None},
        )

    @staticmethod
    def _form_submits(db: Session, enterprise_id: int, start: datetime) -> int:
        try:
            from app.models import HostedPageEvent

            return (
                db.query(HostedPageEvent)
                .filter(
                    HostedPageEvent.enterprise_id == enterprise_id,
                    HostedPageEvent.created_at >= start,
                )
                .count()
            )
        except Exception:
            return 0

    @staticmethod
    def _geo_efficiency(kpi: DashboardKpi, funnel: DashboardFunnel) -> float:
        """简单效率分：Δ + 漏斗通过层。"""
        layers = 0
        if funnel.exposure.get("ok"):
            layers += 1
        if funnel.trust.get("ok"):
            layers += 1
        if (funnel.leads.get("form_submits") or 0) > 0:
            layers += 1
        base = max(0.0, min(1.0, abs(kpi.delta_mention) * 2 + layers * 0.15))
        return round(base, 2)

    @staticmethod
    def _kb_verified(db: Session, enterprise_id: int) -> int:
        try:
            from app.models.kb import KBFact

            return db.query(KBFact).filter(
                KBFact.enterprise_id == enterprise_id,
                KBFact.verified == True,  # noqa: E712
            ).count()
        except Exception:
            return 0

    @staticmethod
    def take_snapshot(db: Session, enterprise_id: int, period: str = "week") -> OutcomeSnapshot:
        d = DashboardService.compute(db, enterprise_id, period)
        snap = OutcomeSnapshot(
            enterprise_id=enterprise_id,
            period=period,
            period_start=datetime.utcnow()
            - timedelta(days={"week": 7, "day": 1, "month": 30, "quarter": 90}.get(period, 7)),
            period_end=datetime.utcnow(),
            snapshot_type="dashboard",
            metrics={
                **d.kpi.model_dump(),
                "geo_efficiency": d.geo_efficiency,
                "waiting_for_a7": d.waiting_for_a7,
            },
            breakdown={
                "funnel": d.funnel.model_dump(),
                "by_channel": [c.model_dump() for c in d.by_channel],
                "by_engine": [e.model_dump() for e in d.by_engine],
                "trend": d.trend,
            },
            notes=d.todo,
        )
        db.add(snap)
        db.commit()
        db.refresh(snap)
        return snap
