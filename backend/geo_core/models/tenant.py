from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    ForeignKey,
    func,
)
from sqlalchemy.orm import relationship

from geo_core.core.db import Base


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


class Enterprise(Base, TimestampMixin):
    __tablename__ = "enterprises"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    industry = Column(String(50), default="beauty_local")
    license_no = Column(String(100))
    contact_name = Column(String(100))
    contact_phone = Column(String(50))
    contact_email = Column(String(200))
    status = Column(String(20), default="active", index=True)
    plan = Column(String(30), default="mvp")
    settings = Column(String, default="{}")
    kb_updated_at = Column(DateTime)

    members = relationship("User", back_populates="enterprise", cascade="all, delete-orphan")
    kb_facts = relationship("KBFact", back_populates="enterprise", cascade="all, delete-orphan")
    kb_faqs = relationship("KBFaq", back_populates="enterprise", cascade="all, delete-orphan")
    kb_signals = relationship("KBSignal", back_populates="enterprise", cascade="all, delete-orphan")
    kb_externals = relationship("KBExternal", back_populates="enterprise", cascade="all, delete-orphan")
    scenarios = relationship("Scenario", back_populates="enterprise", cascade="all, delete-orphan")
    content_drafts = relationship("ContentDraft", back_populates="enterprise", cascade="all, delete-orphan")
    publish_tasks = relationship("PublishTask", back_populates="enterprise", cascade="all, delete-orphan")
    monitor_results = relationship("MonitorResult", back_populates="enterprise", cascade="all, delete-orphan")
    agent_tasks = relationship("AgentTask", back_populates="enterprise", cascade="all, delete-orphan")
    outcome_snapshots = relationship("OutcomeSnapshot", back_populates="enterprise", cascade="all, delete-orphan")
    strategy_packs = relationship("StrategyPack", back_populates="enterprise", cascade="all, delete-orphan")

    @classmethod
    def touch_kb(cls, db, enterprise_id: int):
        db.query(cls).filter(cls.id == enterprise_id).update(
            {"kb_updated_at": datetime.utcnow(), "updated_at": datetime.utcnow()},
            synchronize_session=False,
        )
        db.commit()


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    enterprise_id = Column(
        Integer, ForeignKey("enterprises.id", ondelete="CASCADE"), nullable=False, index=True
    )
    email = Column(String(200), nullable=False, unique=True, index=True)
    phone = Column(String(50))
    full_name = Column(String(100), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(30), default="member", index=True)
    is_active = Column(Boolean, default=True)
    avatar = Column(String(500))
    last_login_at = Column(DateTime)

    enterprise = relationship("Enterprise", back_populates="members")


class RolePermission(Base):
    __tablename__ = "role_permissions"
    id = Column(Integer, primary_key=True, index=True)
    role = Column(String(30), nullable=False, index=True)
    permission = Column(String(100), nullable=False, index=True)
