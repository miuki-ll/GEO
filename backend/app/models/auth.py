"""租户 / 用户 / 企业结构 ORM — 对齐 schemas/auth。"""

from datetime import datetime

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


class Enterprise(Base, TimestampMixin):
    __tablename__ = "enterprises"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, unique=True, index=True)
    industry = Column(String(50), default="beauty_local", index=True)
    industry_pack = Column(String(50), default="beauty_local", index=True)
    license_no = Column(String(100))
    contact_name = Column(String(100))
    contact_phone = Column(String(50))
    contact_email = Column(String(200))
    status = Column(String(20), default="active", index=True)
    plan = Column(String(30), default="mvp")
    settings = Column(JSON, default=dict)
    kb_updated_at = Column(DateTime)
    raw_inputs = Column(Text, default="")  # A5 入驻时用户填的原始输入，A8 词库汇聚用

    members = relationship("User", back_populates="enterprise", cascade="all, delete-orphan")
    brand = relationship("Brand", back_populates="enterprise", uselist=False, cascade="all, delete-orphan")
    stores = relationship("Store", back_populates="enterprise", cascade="all, delete-orphan")
    services = relationship("Service", back_populates="enterprise", cascade="all, delete-orphan")
    kb_facts = relationship("KBFact", back_populates="enterprise", cascade="all, delete-orphan")
    kb_faqs = relationship("KBFaq", back_populates="enterprise", cascade="all, delete-orphan")
    kb_signals = relationship("KBSignal", back_populates="enterprise", cascade="all, delete-orphan")
    kb_externals = relationship("KBExternal", back_populates="enterprise", cascade="all, delete-orphan")
    keywords = relationship("Keyword", back_populates="enterprise", cascade="all, delete-orphan")
    scenarios = relationship("Scenario", back_populates="enterprise", cascade="all, delete-orphan")
    strategy_pack_drafts = relationship("StrategyPackDraft", back_populates="enterprise", cascade="all, delete-orphan")
    strategy_packs = relationship("StrategyPack", back_populates="enterprise", cascade="all, delete-orphan")
    content_assets = relationship("ContentAsset", back_populates="enterprise", cascade="all, delete-orphan")
    publish_tasks = relationship("PublishTask", back_populates="enterprise", cascade="all, delete-orphan")
    monitor_profiles = relationship("MonitorProfile", back_populates="enterprise", cascade="all, delete-orphan")
    monitor_results = relationship("MonitorResult", back_populates="enterprise", cascade="all, delete-orphan")
    source_diagnoses = relationship("SourceDiagnosis", back_populates="enterprise", cascade="all, delete-orphan")
    agent_tasks = relationship("AgentTask", back_populates="enterprise", cascade="all, delete-orphan")
    outcome_snapshots = relationship("OutcomeSnapshot", back_populates="enterprise", cascade="all, delete-orphan")
    approval_logs = relationship("ApprovalLog", back_populates="enterprise", cascade="all, delete-orphan")
    agent_traces = relationship("AgentTrace", back_populates="enterprise", cascade="all, delete-orphan")
    hosted_page_events = relationship("HostedPageEvent", back_populates="enterprise", cascade="all, delete-orphan")
    search_results = relationship("SearchResult", back_populates="enterprise", cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        kwargs.setdefault("raw_inputs", "")
        super().__init__(**kwargs)

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


class Brand(Base, TenantMixin, TimestampMixin):
    __tablename__ = "brands"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    differentiator = Column(Text)
    slogan = Column(String(500))
    metadata_ = Column("metadata_json", JSON, default=dict)

    enterprise = relationship("Enterprise", back_populates="brand")


class Store(Base, TenantMixin, TimestampMixin):
    __tablename__ = "stores"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    city = Column(String(100), index=True)
    district = Column(String(100), index=True)
    address = Column(String(500))
    phone = Column(String(50))
    business_hours = Column(String(200))
    is_primary = Column(Boolean, default=True, index=True)
    metadata_ = Column("metadata_json", JSON, default=dict)

    enterprise = relationship("Enterprise", back_populates="stores")


class Service(Base, TenantMixin, TimestampMixin):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    category = Column(String(100), index=True)
    price_hint = Column(String(100))
    duration_minutes = Column(Integer)
    status = Column(String(20), default="active", index=True)
    metadata_ = Column("metadata_json", JSON, default=dict)

    enterprise = relationship("Enterprise", back_populates="services")
