"""Shared ORM mixins."""
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer


class TimestampMixin:
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class TenantMixin:
    enterprise_id = Column(
        Integer,
        ForeignKey("enterprises.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
