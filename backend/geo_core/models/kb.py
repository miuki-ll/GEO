from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship

from geo_core.core.db import Base
from geo_core.models import TenantMixin, TimestampMixin


class KBFact(Base, TenantMixin, TimestampMixin):
    __tablename__ = "kb_facts"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    source_type = Column(String(30), default="manual")
    source_ref = Column(String(500))
    category = Column(String(100), index=True)
    tags = Column(String, default="[]")
    verified = Column(Boolean, default=False)
    embedding_id = Column(String(100))
    metadata_ = Column("metadata_json", JSON, default=dict)

    enterprise = relationship("Enterprise", back_populates="kb_facts")


class KBFaq(Base, TenantMixin, TimestampMixin):
    __tablename__ = "kb_faqs"
    id = Column(Integer, primary_key=True, index=True)
    question = Column(String(500), nullable=False)
    answer = Column(Text, nullable=False)
    category = Column(String(100), index=True)
    tags = Column(String, default="[]")
    fact_refs = Column(String, default="[]")
    verified = Column(Boolean, default=False)
    embedding_id = Column(String(100))
    metadata_ = Column("metadata_json", JSON, default=dict)

    enterprise = relationship("Enterprise", back_populates="kb_faqs")


class KBSignal(Base, TenantMixin, TimestampMixin):
    __tablename__ = "kb_signals"
    id = Column(Integer, primary_key=True, index=True)
    signal_type = Column(String(50), index=True)
    content = Column(Text, nullable=False)
    source = Column(String(200))
    confidence = Column(Integer, default=0)
    fact_refs = Column(String, default="[]")
    status = Column(String(20), default="pending", index=True)
    metadata_ = Column("metadata_json", JSON, default=dict)

    enterprise = relationship("Enterprise", back_populates="kb_signals")


class KBExternal(Base, TenantMixin, TimestampMixin):
    __tablename__ = "kb_externals"
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(1000))
    title = Column(String(500))
    source_platform = Column(String(50), index=True)
    content = Column(Text)
    summary = Column(Text)
    status = Column(String(20), default="fetched", index=True)
    last_fetched_at = Column(DateTime)
    fact_refs = Column(String, default="[]")
    metadata_ = Column("metadata_json", JSON, default=dict)

    enterprise = relationship("Enterprise", back_populates="kb_externals")
