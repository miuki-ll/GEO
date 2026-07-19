"""A2 KB CRUD 测试 — Fact/FAQ/Signal/External + Summary + Freshness + 租户隔离

用例对照 G-L3-开发者A任务手册.md §11.3：
  T-A2-01 ~ T-A2-06  API 级别（TestClient + JWT）
  T-A2-07 ~ T-A2-08  Service 级别（直接调 service）
"""
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


# ═══════════════════ API 级别（TestClient + JWT）═══════════════════

@pytest.mark.integration
def test_list_facts_empty(client: TestClient, kb_user: dict):
    """T-A2-01：新用户查 facts 列表 → 200，空列表。"""
    resp = client.get("/api/v1/user/kb/facts",
                      headers={"Authorization": f"Bearer {kb_user['token']}"})
    assert resp.status_code == 200, f"list facts 应 200，实际 {resp.status_code}: {resp.text}"
    body = resp.json()
    assert body.get("items") is not None or body.get("data") is not None
    # 取 items（兼容 ListResponse 结构）
    items = body.get("items") or (body.get("data") or {}).get("items") or []
    assert len(items) == 0
    total = body.get("total") if "total" in body else (body.get("data") or {}).get("total")
    if total is not None:
        assert total == 0


@pytest.mark.integration
def test_create_and_get_fact(client: TestClient, kb_user: dict):
    """T-A2-02：创建 fact → 201，GET → 200 字段一致。"""
    token = kb_user["token"]
    payload = {
        "title": "测试Fact标题",
        "content": "这是一条测试Fact的详细内容，包含产品成分说明。",
        "category": "产品成分",
        "tags": ["补水", "敏感肌"],
        "source_type": "manual",
    }
    # 创建
    resp = client.post("/api/v1/user/kb/facts", json=payload,
                       headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code in (200, 201), \
        f"create fact 应 200/201，实际 {resp.status_code}: {resp.text}"
    data = resp.json()["data"]
    fact_id = data["id"]
    assert data["title"] == payload["title"]
    assert data["content"] == payload["content"]
    assert data["category"] == payload["category"]
    assert data["tags"] == payload["tags"]

    # 查询
    resp = client.get(f"/api/v1/user/kb/facts/{fact_id}",
                      headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200, f"get fact 应 200，实际 {resp.status_code}: {resp.text}"
    assert resp.json()["data"]["id"] == fact_id
    assert resp.json()["data"]["title"] == payload["title"]


@pytest.mark.integration
def test_update_and_delete_fact(client: TestClient, kb_user: dict):
    """T-A2-03：创建 → PUT 更新 → GET 验证 → DELETE → GET 404。"""
    token = kb_user["token"]
    # 创建
    resp = client.post("/api/v1/user/kb/facts", json={
        "title": "待更新的Fact", "content": "原始内容",
    }, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code in (200, 201)
    fact_id = resp.json()["data"]["id"]

    # 更新
    resp = client.put(f"/api/v1/user/kb/facts/{fact_id}", json={
        "title": "已更新的Fact", "content": "新内容",
    }, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200, f"update fact 应 200，实际 {resp.status_code}: {resp.text}"
    assert resp.json()["data"]["title"] == "已更新的Fact"
    assert resp.json()["data"]["content"] == "新内容"

    # 验证更新
    resp = client.get(f"/api/v1/user/kb/facts/{fact_id}",
                      headers={"Authorization": f"Bearer {token}"})
    assert resp.json()["data"]["title"] == "已更新的Fact"

    # 删除
    resp = client.delete(f"/api/v1/user/kb/facts/{fact_id}",
                         headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200, f"delete fact 应 200，实际 {resp.status_code}: {resp.text}"

    # 验证删除
    resp = client.get(f"/api/v1/user/kb/facts/{fact_id}",
                      headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 404, f"get 已删除的 fact 应 404，实际 {resp.status_code}"


@pytest.mark.integration
def test_fact_pagination(client: TestClient, kb_user: dict):
    """T-A2-04：创建 5 条 fact → 分页验证 page/page_size。"""
    token = kb_user["token"]
    # 批量创建 5 条
    for i in range(5):
        resp = client.post("/api/v1/user/kb/facts", json={
            "title": f"分页测试-{i+1}", "content": f"内容{i+1}",
        }, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code in (200, 201), f"create #{i} 失败: {resp.status_code}"

    # page=1, page_size=2 → 2 条，total=5
    resp = client.get("/api/v1/user/kb/facts?page=1&page_size=2",
                      headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    body = resp.json()
    items = body.get("items") or (body.get("data") or {}).get("items") or []
    total = body.get("total") or (body.get("data") or {}).get("total") or 0
    assert len(items) == 2, f"page=1 page_size=2 应返回 2 条，实际 {len(items)}"
    assert total == 5, f"total 应为 5，实际 {total}"

    # page=3, page_size=2 → 1 条
    resp = client.get("/api/v1/user/kb/facts?page=3&page_size=2",
                      headers={"Authorization": f"Bearer {token}"})
    items = resp.json().get("items") or (resp.json().get("data") or {}).get("items") or []
    assert len(items) == 1, f"page=3 page_size=2 应返回 1 条，实际 {len(items)}"


@pytest.mark.integration
def test_tenant_isolation_fact(client: TestClient, two_kb_tenants: tuple):
    """T-A2-05：租户隔离 — B 读不到 A 的 fact。"""
    token_a, token_b = two_kb_tenants
    # A 创建 fact
    resp = client.post("/api/v1/user/kb/facts", json={
        "title": "A独有Fact", "content": "只有 Tenant A 能看到",
    }, headers={"Authorization": f"Bearer {token_a}"})
    assert resp.status_code in (200, 201), \
        f"create fact 应 200/201，实际 {resp.status_code}: {resp.text}"
    fact_id = resp.json()["data"]["id"]

    # B 尝试读 A 的 fact → 404
    resp = client.get(f"/api/v1/user/kb/facts/{fact_id}",
                      headers={"Authorization": f"Bearer {token_b}"})
    assert resp.status_code in (404, 403), \
        f"跨租户应 404/403，实际 {resp.status_code}"

    # B 自己的列表不含 A 的 fact
    resp = client.get("/api/v1/user/kb/facts?page_size=100",
                      headers={"Authorization": f"Bearer {token_b}"})
    items = resp.json().get("items") or (resp.json().get("data") or {}).get("items") or []
    assert fact_id not in {f["id"] for f in items}, "B 的列表不应含 A 的 fact"


@pytest.mark.integration
def test_kb_summary_and_freshness(client: TestClient, kb_user: dict):
    """T-A2-06：创建 fact+faq → summary 计数正确 + freshness 返回正常。"""
    token = kb_user["token"]
    # 创建 2 fact + 3 faq
    for i in range(2):
        client.post("/api/v1/user/kb/facts", json={
            "title": f"Summary测试-{i}", "content": f"内容{i}",
        }, headers={"Authorization": f"Bearer {token}"})
    for i in range(3):
        client.post("/api/v1/user/kb/faqs", json={
            "question": f"FAQ测试-{i}?", "answer": f"答案{i}",
        }, headers={"Authorization": f"Bearer {token}"})

    # GET /summary
    resp = client.get("/api/v1/user/kb/summary",
                      headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200, f"summary 应 200，实际 {resp.status_code}: {resp.text}"
    s = resp.json()["data"]
    assert s["facts"] >= 2, f"facts 应 ≥2，实际 {s['facts']}"
    assert s["faqs"] >= 3, f"faqs 应 ≥3，实际 {s['faqs']}"

    # GET /freshness
    resp = client.get("/api/v1/user/kb/freshness",
                      headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200, f"freshness 应 200，实际 {resp.status_code}: {resp.text}"
    f_data = resp.json()["data"]
    assert "freshness" in f_data, "freshness 应含 freshness 字段"
    assert "thin_kb" in f_data, "freshness 应含 thin_kb 字段"
    assert isinstance(f_data["thin_kb"], dict)
    assert "passed" in f_data["thin_kb"]


# ═══════════════════ Service 级别（直接调 service）═══════════════════

def test_fact_service_crud(db_session: Session):
    """T-A2-07：Service 层 CRUD — 绕过 HTTP 直接验证 FactService。"""
    from app.service.kb_service import FactService
    from app.schemas.kb import KBFactCreate, KBFactUpdate

    eid = 1  # 直接用 enterprise_id（不走租户表，service 不过滤）

    # Create
    data = KBFactCreate(title="Service测试", content="Service层内容", category="测试",
                        tags=["tag1", "tag2"])
    fact = FactService.create(db_session, eid, data)
    assert fact.id is not None
    assert fact.enterprise_id == eid
    assert fact.title == "Service测试"
    assert fact.tags == ["tag1", "tag2"]

    # Get
    retrieved = FactService.get(db_session, eid, fact.id)
    assert retrieved is not None
    assert retrieved.id == fact.id

    # Update
    update = KBFactUpdate(title="Service更新后", content="新内容")
    updated = FactService.update(db_session, eid, fact.id, update)
    assert updated.title == "Service更新后"
    assert updated.content == "新内容"

    # Delete
    FactService.delete(db_session, eid, fact.id)
    assert FactService.get(db_session, eid, fact.id) is None


def test_keyword_search(db_session: Session):
    """T-A2-08：关键词搜索 — 按 title/content 模糊匹配。"""
    from app.service.kb_service import FactService
    from app.schemas.kb import KBFactCreate, KBFactListParams

    eid = 2
    # 创建 3 条不同关键词的 fact
    FactService.create(db_session, eid, KBFactCreate(
        title="敏感肌护理指南", content="重点在于补水和修复屏障"))
    FactService.create(db_session, eid, KBFactCreate(
        title="油皮控油方法", content="选择清爽型产品，避免过度清洁"))
    FactService.create(db_session, eid, KBFactCreate(
        title="混合肌分区护理", content="T区控油U区补水是核心"))

    # 搜索 "敏感肌"
    params = KBFactListParams(keyword="敏感肌", page=1, page_size=20)
    items, total = FactService.list(db_session, eid, params)
    assert total == 1, f"搜索'敏感肌'应 1 条，实际 {total}"
    assert items[0].title == "敏感肌护理指南"

    # 搜索 "补水"
    params = KBFactListParams(keyword="补水", page=1, page_size=20)
    items, total = FactService.list(db_session, eid, params)
    assert total == 2, f"搜索'补水'应匹配 2 条（title+content），实际 {total}"

    # 搜索不存在的词
    params = KBFactListParams(keyword="不存在的词xyz", page=1, page_size=20)
    items, total = FactService.list(db_session, eid, params)
    assert total == 0


# ═══════════════════ fixtures ═══════════════════

@pytest.fixture
def kb_user(client):
    """注册一个新企业用户，返回 token + email + password。"""
    unique = uuid.uuid4().hex[:8]
    email = f"a2-test-{unique}@example.com"
    password = "Test@12345"
    resp = client.post("/api/v1/auth/register", json={
        "email": email,
        "password": password,
        "full_name": "KB测试用户",
        "enterprise_name": f"KB测试企业-{unique}",
    })
    assert resp.status_code == 200, f"fixture register 失败: {resp.status_code} {resp.text}"
    token = resp.json()["data"]["access_token"]
    return {"email": email, "password": password, "token": token}


@pytest.fixture
def two_kb_tenants(client):
    """注册两个不同企业，返回 (token_a, token_b)。"""
    ua, ub = uuid.uuid4().hex[:6], uuid.uuid4().hex[:6]
    def _reg(email, enterprise_name):
        resp = client.post("/api/v1/auth/register", json={
            "email": email, "password": "Test@12345",
            "full_name": "KB租户测试", "enterprise_name": enterprise_name,
        })
        assert resp.status_code == 200, f"register 失败: {resp.status_code} {resp.text}"
        return resp.json()["data"]["access_token"]
    return _reg(f"a2-iso-a-{ua}@test.com", f"TenantKB-A-{ua}"), \
           _reg(f"a2-iso-b-{ub}@test.com", f"TenantKB-B-{ub}")
