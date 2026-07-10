"""舱3 发布 — 分渠道发布任务与状态追踪。"""
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


class PublishTask(Base, TenantMixin, TimestampMixin):
    """发布任务 — AUTO / SEMI / GUIDED，必关联 content_asset_id。"""

    __tablename__ = "publish_tasks"

    id = Column(Integer, primary_key=True, index=True)
    content_asset_id = Column(Integer, ForeignKey("content_assets.id", ondelete="CASCADE"), nullable=False, index=True)
    channel = Column(String(50), index=True)
    mode = Column(String(20), default="auto")
    target_url = Column(String(1000))
    published_url = Column(String(1000))
    published_id = Column(String(200))
    status = Column(String(20), default="pending", index=True)
    fallback_semi = Column(Boolean, default=False)
    retry_count = Column(Integer, default=0)
    error_message = Column(Text)
    published_at = Column(DateTime)
    utm_content = Column(String(200), index=True)
    metadata_ = Column("metadata_json", JSON, default=dict)

    enterprise = relationship("Enterprise", back_populates="publish_tasks")
    content_asset = relationship("ContentAsset", back_populates="publish_tasks")
