"""pytest fixtures — TestClient 等共享夹具。"""
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """FastAPI TestClient（测试客户端）— 走真实路由 + 真实 DB。"""
    with TestClient(app) as c:
        yield c
