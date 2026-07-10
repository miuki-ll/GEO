from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from app.core.db import Base
from app.models.base import TenantMixin, TimestampMixin


class ApprovalLog(Base, TenantMixin, TimestampMixin):
    """闸门② — 草稿审阅审计日志。"""

    __tablename__ = "approval_logs"

    id = Column(Integer, primary_key=True, index=True)
    content_asset_id = Column(Integer, ForeignKey("content_assets.id", ondelete="CASCADE"), nullable=False, index=True)
    action = Column(String(30), nullable=False, index=True)
    actor_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), index=True)
    note = Column(Text)
    machine_review_snapshot = Column(JSON, default=dict)
    metadata_ = Column("metadata_json", JSON, default=dict)

    enterprise = relationship("Enterprise", back_populates="approval_logs")
    content_asset = relationship("ContentAsset", back_populates="approval_logs")
    actor = relationship("User")


class AgentTrace(Base, TenantMixin, TimestampMixin):
    """LangGraph / ReAct Harness 审计 — 与 LangSmith 双写。"""

    __tablename__ = "agent_traces"

    id = Column(Integer, primary_key=True, index=True)
    agent_task_id = Column(Integer, ForeignKey("agent_tasks.id", ondelete="CASCADE"), index=True)
    graph_name = Column(String(100), index=True)
    step_idx = Column(Integer, default=0, index=True)
    step_name = Column(String(100))
    thought = Column(Text)
    action = Column(String(200))
    observation = Column(Text)
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    latency_ms = Column(Integer, default=0)
    langsmith_run_id = Column(String(100), index=True)
    metadata_ = Column("metadata_json", JSON, default=dict)

    enterprise = relationship("Enterprise", back_populates="agent_traces")
    agent_task = relationship("AgentTask", back_populates="agent_traces")
