"""舱1 诊断延伸 + 舱2 策略 — scenario / 方案包 / Agent job。"""
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.core.db import Base
from app.models.base import TenantMixin, TimestampMixin


class TargetEngine(Base):
    """全局 AI 引擎注册表（非租户表）。"""

    __tablename__ = "target_engines"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(30), nullable=False, unique=True, index=True)
    name = Column(String(100), nullable=False)
    base_url = Column(String(500))
    adapter = Column(String(100))
    default_model = Column(String(100))
    enabled = Column(Boolean, default=True)
    capabilities = Column(JSON, default=dict)


class SourceDiagnosis(Base, TenantMixin, TimestampMixin):
    """信源诊断结果 — 舱1 onboarding 产出。"""

    __tablename__ = "source_diagnoses"

    id = Column(Integer, primary_key=True, index=True)
    engine = Column(String(50), nullable=False, index=True)
    batch_no = Column(String(50), index=True)
    payload = Column(JSON, default=dict)
    platform_stats = Column(JSON, default=dict)
    map_gap = Column(JSON, default=dict)
    status = Column(String(20), default="completed", index=True)
    agent_task_id = Column(Integer, ForeignKey("agent_tasks.id", ondelete="SET NULL"), index=True)
    metadata_ = Column("metadata_json", JSON, default=dict)

    enterprise = relationship("Enterprise", back_populates="source_diagnoses")
    agent_task = relationship("AgentTask", back_populates="source_diagnoses")
    external_candidates = relationship("KBExternal", back_populates="source_diagnosis")


class Keyword(Base, TenantMixin, TimestampMixin):
    """词库 — 监测辅助，非生产起点。"""

    __tablename__ = "keywords"

    id = Column(Integer, primary_key=True, index=True)
    phrase = Column(String(500), nullable=False, index=True)
    keyword_type = Column(String(30), default="exact", index=True)
    pool_hint = Column(String(20), default="core", index=True)
    status = Column(String(20), default="draft", index=True)
    pain_cluster_id = Column(String(100))
    metadata_ = Column("metadata_json", JSON, default=dict)

    enterprise = relationship("Enterprise", back_populates="keywords")


class Scenario(Base, TenantMixin, TimestampMixin):
    """最小生产单元 — 1 scenario × 1 渠道 × 1 Skill。"""

    __tablename__ = "scenarios"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    user_query = Column(Text, nullable=False)
    intent = Column(String(200))
    channel = Column(String(50), index=True)
    skill = Column(String(50), index=True)
    priority = Column(Integer, default=5)
    status = Column(String(20), default="draft", index=True)
    target_engines = Column(JSON, default=list)
    persona_ref = Column(JSON, default=dict)
    competitor_ref = Column(JSON, default=dict)
    fact_refs = Column(JSON, default=list)
    gap_analysis = Column(Text)
    metadata_ = Column("metadata_json", JSON, default=dict)

    enterprise = relationship("Enterprise", back_populates="scenarios")
    content_assets = relationship("ContentAsset", back_populates="scenario")
    monitor_results = relationship("MonitorResult", back_populates="scenario")


class StrategyPackDraft(Base, TenantMixin, TimestampMixin):
    """方案包临时草案（job 产出，待确认）。"""

    __tablename__ = "strategy_pack_drafts"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("agent_tasks.id", ondelete="SET NULL"), index=True)
    payload = Column(JSON, default=dict)
    status = Column(String(20), default="draft", index=True)
    expires_at = Column(DateTime, index=True)
    metadata_ = Column("metadata_json", JSON, default=dict)

    enterprise = relationship("Enterprise", back_populates="strategy_pack_drafts")
    job = relationship("AgentTask", back_populates="strategy_pack_drafts")


class StrategyPack(Base, TenantMixin, TimestampMixin):
    """方案包 — 闸门①确认后的策略快照。"""

    __tablename__ = "strategy_packs"

    id = Column(Integer, primary_key=True, index=True)
    draft_id = Column(Integer, ForeignKey("strategy_pack_drafts.id", ondelete="SET NULL"), index=True)
    version = Column(String(20), default="1.0")
    status = Column(String(20), default="draft", index=True)
    persona = Column(JSON, default=dict)
    competitors = Column(JSON, default=list)
    pain_points = Column(JSON, default=list)
    scenarios = Column(JSON, default=list)
    channels = Column(JSON, default=list)
    weights = Column(JSON, default=dict)
    confirmed_at = Column(DateTime)
    confirmed_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), index=True)
    metadata_ = Column("metadata_json", JSON, default=dict)

    enterprise = relationship("Enterprise", back_populates="strategy_packs")
    draft = relationship("StrategyPackDraft", foreign_keys=[draft_id])
    confirmer = relationship("User", foreign_keys=[confirmed_by])


class AgentTask(Base, TenantMixin, TimestampMixin):
    """L2 异步任务 — onboarding / 诊断 / 迭代 job 状态机。"""

    __tablename__ = "agent_tasks"

    id = Column(Integer, primary_key=True, index=True)
    task_type = Column(String(50), index=True)
    graph_name = Column(String(100), index=True)
    celery_task_id = Column(String(100), index=True)
    status = Column(String(20), default="pending", index=True)
    gate_status = Column(String(30), index=True)
    progress_pct = Column(Integer, default=0)
    progress_message = Column(String(500))
    input_data = Column(JSON, default=dict)
    output_data = Column(JSON, default=dict)
    trace_id = Column(String(100), index=True)
    error_message = Column(Text)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)

    enterprise = relationship("Enterprise", back_populates="agent_tasks")
    strategy_pack_drafts = relationship("StrategyPackDraft", back_populates="job")
    source_diagnoses = relationship("SourceDiagnosis", back_populates="agent_task")
    agent_traces = relationship("AgentTrace", back_populates="agent_task")
