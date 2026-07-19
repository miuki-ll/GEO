"""效果舱 Dashboard — 对齐手册 B7 + OutcomeSnapshot。"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import Field

from app.schemas.common import BaseSchema, IDModel, TimestampResponse


class DashboardKpi(BaseSchema):
    # 手册 B7 核心四键
    mention_rate_t0: float = 0.0
    mention_rate_t1: float = 0.0
    delta_mention: float = 0.0
    hallucination_rate: float = 0.0
    # 运营辅助（保留旧字段）
    total_scenarios: int = 0
    total_drafts_published: int = 0
    avg_mention_rate: float = 0.0
    avg_trust_score: float = 0.0
    core_queries: int = 0
    probe_discoveries: int = 0
    pending_review: int = 0
    kb_facts_verified: int = 0


class ChannelBreakdown(BaseSchema):
    channel: str
    published: int = 0
    mention_rate: float = 0.0
    avg_trust: float = 0.0


class EngineBreakdown(BaseSchema):
    engine: str
    mention_rate: float = 0.0
    avg_trust: float = 0.0
    sample_size: int = 0


class DashboardFunnel(BaseSchema):
    exposure: Dict[str, Any] = Field(default_factory=lambda: {"ok": False})
    trust: Dict[str, Any] = Field(default_factory=lambda: {"ok": False})
    leads: Dict[str, Any] = Field(default_factory=lambda: {"form_submits": 0})
    conversion: Dict[str, Any] = Field(
        default_factory=lambda: {"manual_cost": None, "manual_revenue": None}
    )


class DashboardData(BaseSchema):
    period: str = "week"
    kpi: DashboardKpi = Field(default_factory=DashboardKpi)
    funnel: DashboardFunnel = Field(default_factory=DashboardFunnel)
    geo_efficiency: float = 0.0
    waiting_for_a7: bool = False
    todo: Optional[str] = None  # TODO(WAIT_FOR: A7)
    by_channel: List[ChannelBreakdown] = Field(default_factory=list)
    by_engine: List[EngineBreakdown] = Field(default_factory=list)
    trend: List[Dict[str, Any]] = Field(default_factory=list)
    alerts: List[Dict[str, Any]] = Field(default_factory=list)


class OutcomeSnapshotBase(BaseSchema):
    period: str = "week"
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    snapshot_type: str = "dashboard"
    metrics: Dict[str, Any] = Field(default_factory=dict)
    breakdown: Dict[str, Any] = Field(default_factory=dict)
    notes: Optional[str] = None


class OutcomeSnapshotResponse(OutcomeSnapshotBase, IDModel, TimestampResponse):
    enterprise_id: int
