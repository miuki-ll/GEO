from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from app.core.db import Base
from app.models.base import TenantMixin, TimestampMixin


class FaissIndex(Base, TenantMixin, TimestampMixin):
    """向量索引元数据 — Faiss 运维。"""

    __tablename__ = "faiss_indexes"

    id = Column(Integer, primary_key=True, index=True)
    index_name = Column(String(100), nullable=False, index=True)
    index_type = Column(String(50), default="kb_facts", index=True)
    version = Column(String(30), default="v1")
    vector_count = Column(Integer, default=0)
    storage_path = Column(String(500))
    status = Column(String(20), default="ready", index=True)
    last_built_at = Column(DateTime)
    metadata_ = Column("metadata_json", JSON, default=dict)

    enterprise = relationship("Enterprise")
