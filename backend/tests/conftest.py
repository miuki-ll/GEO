"""pytest fixtures — TestClient + SQLite 内存库共享夹具。"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.db import Base
from app import models  # noqa: F401 — register all tables
from app.models import Enterprise, User


@pytest.fixture
def client():
    """FastAPI TestClient（测试客户端）— 走真实路由 + 真实 DB。"""
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)
    db = Session()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture()
def two_tenants(db_session):
    """两个租户各一名 owner，用于隔离断言。"""
    e1 = Enterprise(name="Tenant A", industry_pack="beauty_local", status="active")
    e2 = Enterprise(name="Tenant B", industry_pack="beauty_local", status="active")
    db_session.add_all([e1, e2])
    db_session.flush()
    u1 = User(
        enterprise_id=e1.id,
        email="a@test.local",
        full_name="User A",
        hashed_password="x",
        role="owner",
        is_active=True,
    )
    u2 = User(
        enterprise_id=e2.id,
        email="b@test.local",
        full_name="User B",
        hashed_password="x",
        role="owner",
        is_active=True,
    )
    db_session.add_all([u1, u2])
    db_session.commit()
    db_session.refresh(e1)
    db_session.refresh(e2)
    db_session.refresh(u1)
    db_session.refresh(u2)
    return {"db": db_session, "e1": e1, "e2": e2, "u1": u1, "u2": u2}
