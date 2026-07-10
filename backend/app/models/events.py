from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import relationship

from app.core.db import Base
from app.models.base import TenantMixin, TimestampMixin


class HostedPageEvent(Base, TenantMixin, TimestampMixin):
    """托管页第一方事件 — PV / 表单提交。"""

    __tablename__ = "hosted_page_events"

    id = Column(Integer, primary_key=True, index=True)
    content_asset_id = Column(Integer, ForeignKey("content_assets.id", ondelete="SET NULL"), index=True)
    event_type = Column(String(30), nullable=False, index=True)
    event_at = Column(DateTime, index=True)
    session_id = Column(String(100), index=True)
    payload = Column(JSON, default=dict)

    enterprise = relationship("Enterprise", back_populates="hosted_page_events")
    content_asset = relationship("ContentAsset", back_populates="hosted_page_events")
