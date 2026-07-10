"""效果舱 Dashboard — 对齐 models/monitor.py OutcomeSnapshot。"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import Field

from app.schemas.common import BaseSchema, IDModel, TimestampResponse


class DashboardKpi(BaseSchema):
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


class DashboardData(BaseSchema):
    period: str = "week"
    kpi: DashboardKpi = Field(default_factory=DashboardKpi)
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
