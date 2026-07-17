"""A1 鉴权测试 — 注册/登录/JWT/401/403/租户隔离/唯一约束。

用例:
  T-A1-01  注册新企业 → 200 + access_token
  T-A1-02  JSON 登录 → 200 + access_token
  T-A1-03  无 token 访问受保护端点 → 401
  T-A1-04  跨租户隔离
  T-A1-05  更新 settings.target_engines
  T-A1-06  重复企业名注册 → 400
"""
import uuid

import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
def test_register_returns_token(client: TestClient):
    unique = uuid.uuid4().hex[:8]
    resp = client.post("/api/v1/auth/register", json={
        "email": f"a1test-{unique}@example.com",
        "password": "Test@12345",
        "full_name": "测试用户",
        "enterprise_name": f"A1测试企业-{unique}",
    })
    assert resp.status_code == 200, f"register 应 200，实际 {resp.status_code}: {resp.text}"
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["access_token"]
    assert body["data"]["token_type"] == "bearer"
    assert body["data"]["user"]["role"] == "owner"
    assert body["data"]["user"]["email"].startswith("a1test-")


@pytest.mark.integration
def test_login_returns_token(client: TestClient, registered_user: dict):
    resp = client.post("/api/v1/auth/login", json={
        "email": registered_user["email"],
        "password": registered_user["password"],
    })
    assert resp.status_code == 200, f"login 应 200，实际 {resp.status_code}: {resp.text}"
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["access_token"]


@pytest.mark.integration
def test_no_token_returns_401(client: TestClient):
    resp = client.get("/api/v1/user/enterprise/profile")
    assert resp.status_code == 401, f"应 401，实际 {resp.status_code}: {resp.text}"


@pytest.mark.integration
def test_tenant_isolation(client: TestClient, two_enterprises: tuple):
    token_a, token_b = two_enterprises

    # A 创建 fact（API 声明 status_code=201）
    resp = client.post("/api/v1/user/kb/facts", json={
        "title": "A的秘密Fact", "content": "只有A能看到", "category": "test",
    }, headers={"Authorization": f"Bearer {token_a}"})
    assert resp.status_code in (200, 201), \
        f"创建 fact 应 200/201，实际 {resp.status_code}: {resp.text}"
    fact_id = resp.json()["data"]["id"]

    # B 尝试读 A 的 fact → 404
    resp = client.get(f"/api/v1/user/kb/facts/{fact_id}",
                      headers={"Authorization": f"Bearer {token_b}"})
    assert resp.status_code in (404, 403), \
        f"跨租户应 404/403，实际 {resp.status_code}: {resp.text}"

    # B 的列表不含 A 的 fact（ListResponse 的 items 在顶层，不在 data 下）
    resp = client.get("/api/v1/user/kb/facts?page_size=100",
                      headers={"Authorization": f"Bearer {token_b}"})
    assert resp.status_code == 200, f"list facts 应 200，实际 {resp.status_code}: {resp.text}"
    body = resp.json()
    items = body.get("items") or (body.get("data") or {}).get("items") or []
    assert fact_id not in {f["id"] for f in items}, "B 的列表不应含 A 的 fact"


@pytest.mark.integration
def test_update_target_engines(client: TestClient, registered_user: dict):
    token = registered_user["token"]
    resp = client.put("/api/v1/user/enterprise/profile", json={
        "settings": {"target_engines": ["doubao", "kimi"]},
    }, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200, f"PUT profile 应 200，实际 {resp.status_code}: {resp.text}"

    resp = client.get("/api/v1/user/enterprise/profile",
                      headers={"Authorization": f"Bearer {token}"})
    settings = resp.json()["data"].get("settings", {})
    assert settings.get("target_engines") == ["doubao", "kimi"]


@pytest.mark.integration
def test_duplicate_enterprise_name_rejected(client: TestClient, registered_user: dict):
    """用已注册的企业名再次注册 → 400。"""
    token = registered_user["token"]
    resp = client.get("/api/v1/user/enterprise/profile",
                      headers={"Authorization": f"Bearer {token}"})
    existing_name = resp.json()["data"]["name"]

    resp = client.post("/api/v1/auth/register", json={
        "email": f"dup-{uuid.uuid4().hex[:6]}@test.com",
        "password": "Test@12345",
        "full_name": "重复企业",
        "enterprise_name": existing_name,
    })
    assert resp.status_code == 400
    assert "企业名称" in resp.json()["detail"]


# ── fixtures ──

@pytest.fixture
def registered_user(client):
    unique = uuid.uuid4().hex[:8]
    email = f"a1-fixture-{unique}@example.com"
    password = "Test@12345"
    resp = client.post("/api/v1/auth/register", json={
        "email": email,
        "password": password,
        "full_name": "Fixture用户",
        "enterprise_name": f"Fixture企业-{unique}",
    })
    assert resp.status_code == 200, f"fixture register 失败: {resp.status_code} {resp.text}"
    token = resp.json()["data"]["access_token"]
    return {"email": email, "password": password, "token": token}


@pytest.fixture
def two_enterprises(client):
    u1, u2 = uuid.uuid4().hex[:6], uuid.uuid4().hex[:6]

    resp = client.post("/api/v1/auth/register", json={
        "email": f"iso-a-{u1}@test.com", "password": "Test@12345",
        "full_name": "A", "enterprise_name": f"TenantA-{u1}",
    })
    assert resp.status_code == 200, f"tenant A register 失败: {resp.text}"
    token_a = resp.json()["data"]["access_token"]

    resp = client.post("/api/v1/auth/register", json={
        "email": f"iso-b-{u2}@test.com", "password": "Test@12345",
        "full_name": "B", "enterprise_name": f"TenantB-{u2}",
    })
    assert resp.status_code == 200, f"tenant B register 失败: {resp.text}"
    token_b = resp.json()["data"]["access_token"]

    return token_a, token_b
