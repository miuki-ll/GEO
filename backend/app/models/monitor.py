"""舱3 效果 — AI 监测、效果舱快照。"""
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.core.db import Base
from app.models.base import TenantMixin, TimestampMixin


class MonitorProfile(Base, TenantMixin, TimestampMixin):
    """监测配置 — Core + Probe prompts 与阈值。"""

    __tablename__ = "monitor_profiles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), default="default")
    target_engines = Column(JSON, default=list)
    core_prompts = Column(JSON, default=list)
    probe_prompts = Column(JSON, default=list)
    thresholds = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True, index=True)
    metadata_ = Column("metadata_json", JSON, default=dict)

    enterprise = relationship("Enterprise", back_populates="monitor_profiles")


class MonitorResult(Base, TenantMixin, TimestampMixin):
    """单次监测采样结果。"""

    __tablename__ = "monitor_results"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("monitor_profiles.id", ondelete="SET NULL"), index=True)
    pool_type = Column(String(20), index=True)
    engine = Column(String(50), index=True)
    query = Column(String(500), nullable=False)
    scenario_id = Column(Integer, ForeignKey("scenarios.id", ondelete="SET NULL"), index=True)
    mentioned = Column(Boolean, default=False)
    mention_snippet = Column(Text)
    trust_score = Column(Float)
    position_rank = Column(Integer)
    response_text = Column(Text)
    competitor_mentions = Column(JSON, default=list)
    metrics = Column(JSON, default=dict)
    run_at = Column(DateTime, index=True)
    batch_no = Column(String(50), index=True)
    metadata_ = Column("metadata_json", JSON, default=dict)

    enterprise = relationship("Enterprise", back_populates="monitor_results")
    profile = relationship("MonitorProfile")
    scenario = relationship("Scenario", back_populates="monitor_results")


class OutcomeSnapshot(Base, TenantMixin, TimestampMixin):
    """效果舱周期性 KPI 快照。"""

    __tablename__ = "outcome_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    period = Column(String(20), index=True)
    period_start = Column(DateTime, index=True)
    period_end = Column(DateTime)
    snapshot_type = Column(String(30), index=True)
    metrics = Column(JSON, default=dict)
    breakdown = Column(JSON, default=dict)
    notes = Column(Text)

    enterprise = relationship("Enterprise", back_populates="outcome_snapshots")
