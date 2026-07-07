from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, JSON, Float
from sqlalchemy.orm import relationship

from geo_core.core.db import Base
from geo_core.models import TenantMixin, TimestampMixin


class TargetEngine(Base):
    __tablename__ = "target_engines"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(30), nullable=False, unique=True, index=True)
    name = Column(String(100), nullable=False)
    base_url = Column(String(500))
    adapter = Column(String(100))
    default_model = Column(String(100))
    enabled = Column(Boolean, default=True)
    capabilities = Column(JSON, default=dict)


class Scenario(Base, TenantMixin, TimestampMixin):
    __tablename__ = "scenarios"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    user_query = Column(Text, nullable=False)
    intent = Column(String(200))
    channel = Column(String(50), index=True)
    skill = Column(String(50), index=True)
    priority = Column(Integer, default=5)
    status = Column(String(20), default="draft", index=True)
    target_engines = Column(String, default="[]")
    persona_ref = Column(String, default="{}")
    competitor_ref = Column(String, default="{}")
    fact_refs = Column(String, default="[]")
    gap_analysis = Column(Text)
    metadata_ = Column("metadata_json", JSON, default=dict)

    enterprise = relationship("Enterprise", back_populates="scenarios")
    content_drafts = relationship("ContentDraft", back_populates="scenario")


class StrategyPack(Base, TenantMixin, TimestampMixin):
    __tablename__ = "strategy_packs"
    id = Column(Integer, primary_key=True, index=True)
    version = Column(String(20), default="1.0")
    status = Column(String(20), default="draft", index=True)
    persona = Column(JSON, default=dict)
    competitors = Column(JSON, default=list)
    pain_points = Column(JSON, default=list)
    scenarios = Column(JSON, default=list)
    channels = Column(JSON, default=list)
    weights = Column(JSON, default=dict)
    confirmed_at = Column(DateTime)
    confirmed_by = Column(Integer)
    metadata_ = Column("metadata_json", JSON, default=dict)

    enterprise = relationship("Enterprise", back_populates="strategy_packs")


class ContentDraft(Base, TenantMixin, TimestampMixin):
    __tablename__ = "content_drafts"
    id = Column(Integer, primary_key=True, index=True)
    scenario_id = Column(Integer, ForeignKey("scenarios.id"), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    skill = Column(String(50), index=True)
    channel = Column(String(50), index=True)
    fact_refs = Column(String, default="[]")
    fact_verify_pass = Column(Boolean)
    fact_verify_report = Column(JSON, default=dict)
    compliance_pass = Column(Boolean)
    compliance_report = Column(JSON, default=dict)
    machine_review_pass = Column(Boolean)
    human_review_status = Column(String(20), default="pending", index=True)
    human_review_note = Column(Text)
    human_review_by = Column(Integer)
    human_review_at = Column(DateTime)
    version = Column(Integer, default=1)
    status = Column(String(20), default="draft", index=True)

    enterprise = relationship("Enterprise", back_populates="content_drafts")
    scenario = relationship("Scenario", back_populates="content_drafts")
    publish_tasks = relationship("PublishTask", back_populates="draft")


class PublishTask(Base, TenantMixin, TimestampMixin):
    __tablename__ = "publish_tasks"
    id = Column(Integer, primary_key=True, index=True)
    draft_id = Column(Integer, ForeignKey("content_drafts.id"), nullable=False, index=True)
    channel = Column(String(50), index=True)
    mode = Column(String(20), default="auto")
    target_url = Column(String(1000))
    published_url = Column(String(1000))
    published_id = Column(String(200))
    status = Column(String(20), default="pending", index=True)
    retry_count = Column(Integer, default=0)
    error_message = Column(Text)
    published_at = Column(DateTime)
    metadata_ = Column("metadata_json", JSON, default=dict)

    enterprise = relationship("Enterprise", back_populates="publish_tasks")
    draft = relationship("ContentDraft", back_populates="publish_tasks")


class MonitorResult(Base, TenantMixin, TimestampMixin):
    __tablename__ = "monitor_results"
    id = Column(Integer, primary_key=True, index=True)
    pool_type = Column(String(20), index=True)
    engine = Column(String(50), index=True)
    query = Column(String(500), nullable=False)
    scenario_id = Column(Integer, index=True)
    mentioned = Column(Boolean, default=False)
    mention_snippet = Column(Text)
    trust_score = Column(Float)
    position_rank = Column(Integer)
    response_text = Column(Text)
    competitor_mentions = Column(JSON, default=list)
    run_at = Column(DateTime, index=True)
    batch_no = Column(String(50), index=True)
    metadata_ = Column("metadata_json", JSON, default=dict)

    enterprise = relationship("Enterprise", back_populates="monitor_results")


class AgentTask(Base, TenantMixin, TimestampMixin):
    __tablename__ = "agent_tasks"
    id = Column(Integer, primary_key=True, index=True)
    task_type = Column(String(50), index=True)
    graph_name = Column(String(100), index=True)
    celery_task_id = Column(String(100), index=True)
    status = Column(String(20), default="pending", index=True)
    progress_pct = Column(Integer, default=0)
    progress_message = Column(String(500))
    input_data = Column(JSON, default=dict)
    output_data = Column(JSON, default=dict)
    trace_id = Column(String(100), index=True)
    error_message = Column(Text)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)

    enterprise = relationship("Enterprise", back_populates="agent_tasks")


class OutcomeSnapshot(Base, TenantMixin, TimestampMixin):
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
