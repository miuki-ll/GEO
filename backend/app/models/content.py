"""舱2 内容 — 草稿生成、机器审、人工审（闸门②）。"""
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


class ContentAsset(Base, TenantMixin, TimestampMixin):
    """内容资产 — 草稿审阅 / 发布追踪（content_asset_id）。"""

    __tablename__ = "content_assets"

    id = Column(Integer, primary_key=True, index=True)
    scenario_id = Column(Integer, ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    skill = Column(String(50), index=True)
    channel = Column(String(50), index=True)
    fact_refs = Column(JSON, default=list)
    fact_verify_pass = Column(Boolean)
    fact_verify_report = Column(JSON, default=dict)
    compliance_pass = Column(Boolean)
    compliance_report = Column(JSON, default=dict)
    machine_review_pass = Column(Boolean)
    human_review_status = Column(String(20), default="pending", index=True)
    human_review_note = Column(Text)
    human_review_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), index=True)
    human_review_at = Column(DateTime)
    version = Column(Integer, default=1)
    status = Column(String(20), default="draft", index=True)
    metadata_ = Column("metadata_json", JSON, default=dict)

    enterprise = relationship("Enterprise", back_populates="content_assets")
    scenario = relationship("Scenario", back_populates="content_assets")
    reviewer = relationship("User", foreign_keys=[human_review_by])
    publish_tasks = relationship("PublishTask", back_populates="content_asset")
    approval_logs = relationship("ApprovalLog", back_populates="content_asset")
    hosted_page_events = relationship("HostedPageEvent", back_populates="content_asset")


ContentDraft = ContentAsset
