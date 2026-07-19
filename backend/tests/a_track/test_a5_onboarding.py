"""A5 开店向导测试 — schema / API / LLM 节点 / 副作用写入 / KB 建库

用例对照 G-L3-开发者A任务手册.md §11.3：
  T-A5-01 ~ T-A5-06
"""
import json
import uuid
import asyncio

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.agents.state import AgentGraphState


# ═══════════════════ Mock 工具 ═══════════════════

def _make_mock_search_response(citations=None):
    """构造 mock gateway.search() 返回值。"""
    from app.core.llm.schemas import SearchResponse, SearchCitation, LLMUsage
    cites = []
    for c in (citations or []):
        cites.append(SearchCitation(
            url=c.get("url", "https://example.com"),
            title=c.get("title", "测试"),
            summary=c.get("summary", "摘要"),
            site_name=c.get("site_name", "测试站"),
        ))
    return SearchResponse(
        engine="doubao",
        model="test",
        answer="模拟搜索回答",
        citations=cites,
        usage=LLMUsage(),
    )


def _make_mock_chat_response(content: str):
    """构造 mock gateway.chat() 返回值。"""
    from app.core.llm.schemas import LLMResponse, LLMUsage
    return LLMResponse(
        engine="doubao",
        model="test",
        content=content,
        usage=LLMUsage(),
    )


# ═══════════════════ T-A5-01 ═══════════════════

def test_onboarding_schema_valid():
    """T-A5-01：schema 验证 — 最小合法 body；缺少 name → ValidationError。"""
    from pydantic import ValidationError
    from app.schemas.onboarding import OnboardingRunRequest

    body = OnboardingRunRequest(
        enterprise={"name": "测试企业"},
    )
    d = body.model_dump()
    assert d["enterprise"]["name"] == "测试企业"
    assert d["search_enabled"] is True
    assert d["stores"] == []
    assert d["services"] == []

    with pytest.raises(ValidationError):
        OnboardingRunRequest(enterprise={})


# ═══════════════════ fixtures ═══════════════════

@pytest.fixture
def kb_user(client):
    """注册一个新企业用户，返回 token + email + password。"""
    unique = uuid.uuid4().hex[:8]
    email = f"a5-test-{unique}@example.com"
    password = "Test@12345"
    resp = client.post("/api/v1/auth/register", json={
        "email": email,
        "password": password,
        "full_name": "A5测试用户",
        "enterprise_name": f"A5测试企业-{unique}",
    })
    assert resp.status_code == 200, f"fixture register 失败: {resp.status_code} {resp.text}"
    token = resp.json()["data"]["access_token"]
    return {"email": email, "password": password, "token": token}


# ═══════════════════ T-A5-02 ═══════════════════

@pytest.mark.integration
def test_run_returns_task_id(client: TestClient, kb_user: dict):
    """T-A5-02：POST /run → 200，返回 task_id。"""
    # Mock runner.run_graph 避免真实 LLM（_bg 内 from app.agents.runner import）
    async def _fake_run(*args, **kwargs):
        return AgentGraphState(
            enterprise_id=kb_user.get("eid", 1),
            step="done",
            progress_pct=100,
            progress_message="完成",
            output_data={"probes": [], "pain_points": [], "persona": {}, "competitors": []},
            errors=[],
        )

    with patch("app.agents.runner.run_graph", side_effect=_fake_run), \
         patch("app.tasks.faiss_tasks.faiss_sync_item.delay", MagicMock()):
        resp = client.post(
            "/api/v1/user/onboarding/run",
            json={
                "enterprise": {"name": "入驻测试企业"},
                "stores": [{"name": "测试门店", "city": "上海", "district": "静安区"}],
                "services": [{"name": "补水"}],
                "search_enabled": False,
            },
            headers={"Authorization": f"Bearer {kb_user['token']}"},
        )
        assert resp.status_code == 200, f"POST /run 应 200，实际 {resp.status_code}: {resp.text}"
        data = resp.json().get("data", resp.json())
        assert data.get("id") is not None
        assert data.get("task_type") == "onboarding_pipeline"


# ═══════════════════ T-A5-03 ═══════════════════

@pytest.mark.asyncio
async def test_diagnose_node_probes_and_search():
    """T-A5-03：diagnose_node 生成探针 + 搜索。"""
    from app.agents.graphs.onboarding.nodes import diagnose_node

    mock_probes = [
        "静安区皮肤管理推荐哪家好",
        "静安寺附近美容院哪个靠谱",
        "敏感肌修护静安区哪家专业",
        "静安区补水保湿项目推荐",
    ]

    mock_citations = [
        {"url": "https://dp.com/1", "title": "XX皮肤管理", "summary": "摘要1", "site_name": "大众点评"},
        {"url": "https://xhs.com/2", "title": "探店笔记", "summary": "摘要2", "site_name": "小红书"},
    ]

    # 注意：mock_path 对齐 nodes.py 的 import 路径
    with patch("app.agents.graphs.onboarding.nodes.chat",
               new=AsyncMock(return_value=_make_mock_chat_response(json.dumps(mock_probes, ensure_ascii=False)))):
        with patch("app.agents.graphs.onboarding.nodes.search",
                   new=AsyncMock(return_value=_make_mock_search_response(mock_citations))):

            state: AgentGraphState = {
                "enterprise_id": 1,
                "input_data": {
                    "enterprise": {"name": "测试皮肤管理"},
                    "stores": [{"city": "上海", "district": "静安区"}],
                    "services": [{"name": "补水"}],
                    "search_enabled": True,
                },
                "output_data": {},
                "errors": [],
            }

            result = await diagnose_node(state)
            assert len(result.get("probes", [])) >= 3
            assert result.get("search_used") is True
            assert len(result.get("citations", [])) >= 1


# ═══════════════════ T-A5-04 ═══════════════════

@pytest.mark.asyncio
async def test_pain_persona_competitor_chain():
    """T-A5-04：pain → persona → competitor 节点链。"""
    from app.agents.graphs.onboarding.nodes import pain_node, persona_node, competitor_node

    pain_json = json.dumps([
        {"point": "口碑不足", "severity": 8, "evidence": "搜索无提及"},
        {"point": "竞品强势", "severity": 6, "evidence": "竞品A出现频次高"},
    ], ensure_ascii=False)

    persona_json = json.dumps({
        "age_range": [25, 40],
        "genders": ["女性"],
        "cities": ["上海静安区"],
        "core_needs": ["补水", "抗衰"],
        "decision_factors": ["口碑", "距离", "价格"],
        "typical_queries": ["静安区皮肤管理推荐"],
    }, ensure_ascii=False)

    comp_json = json.dumps([
        {"name": "竞品A", "type": "chain", "ai_mention_rate": 60,
         "strengths": ["品牌大"], "weaknesses": ["客制化差"], "differentiator": "我们客制化好"},
    ], ensure_ascii=False)

    call_count = {"count": 0}

    async def _mock_chat(request):
        call_count["count"] += 1
        if call_count["count"] == 1:
            return _make_mock_chat_response(pain_json)
        elif call_count["count"] == 2:
            return _make_mock_chat_response(persona_json)
        else:
            return _make_mock_chat_response(comp_json)

    with patch("app.agents.graphs.onboarding.nodes.chat", new=_mock_chat):
        state: AgentGraphState = {
            "enterprise_id": 1,
            "input_data": {
                "enterprise": {"name": "测试"},
                "raw_inputs": "想提升口碑",
                "services": [{"name": "补水"}],
            },
            "probes": ["探针1", "探针2"],
            "citations": [],
            "search_used": False,
            "output_data": {},
            "errors": [],
        }

        # PAIN
        state = await pain_node(state)
        assert len(state.get("pain_points", [])) == 2
        assert state["step"] == "PERSONA"

        # PERSONA
        state = await persona_node(state)
        assert "age_range" in state.get("persona", {})
        assert state["step"] == "COMPETITOR"

        # COMPETITOR
        state = await competitor_node(state)
        assert len(state.get("competitors", [])) >= 1
        assert state["step"] == "done"


# ═══════════════════ T-A5-05 ═══════════════════

def test_write_side_effects(db_session: Session):
    """T-A5-05：副作用写入 — Brand/Store/Service 落库。"""
    from app.api.v1.user.onboarding import _write_side_effects
    from app.schemas.onboarding import OnboardingRunRequest
    from app.models.auth import Brand, Store, Service, Enterprise

    eid = 1
    # 创建 Enterprise
    ent = Enterprise(id=eid, name="测试企业", industry_pack="beauty_local", status="active")
    db_session.add(ent)
    db_session.flush()

    body = OnboardingRunRequest(
        enterprise={"name": "测试企业", "industry": "beauty_local"},
        brand={"name": "测试品牌", "differentiator": "差异化"},
        stores=[{"name": "静安寺店", "city": "上海", "district": "静安区", "address": "南京西路"}],
        services=[{"name": "补水"}, {"name": "抗衰"}],
        target_engines=["doubao", "deepseek"],
    )

    _write_side_effects(db_session, eid, body)

    # 验证 Brand
    brand = db_session.query(Brand).filter(Brand.enterprise_id == eid).first()
    assert brand is not None
    assert brand.name == "测试品牌"
    assert brand.differentiator == "差异化"

    # 验证 Store
    stores = db_session.query(Store).filter(Store.enterprise_id == eid).all()
    assert len(stores) == 1
    assert stores[0].name == "静安寺店"

    # 验证 Service
    services = db_session.query(Service).filter(Service.enterprise_id == eid).all()
    assert len(services) == 2

    # 验证 target_engines 在 settings 中
    ent2 = db_session.query(Enterprise).filter(Enterprise.id == eid).first()
    assert "doubao" in (ent2.settings or {}).get("target_engines", [])

    db_session.rollback()


# ═══════════════════ T-A5-06 ═══════════════════

def test_bootstrap_kb(db_session: Session):
    """T-A5-06：KB 自动建库 + thin_kb_check。"""
    from app.api.v1.user.onboarding import _bootstrap_kb
    from app.schemas.onboarding import OnboardingRunRequest, SeedFact
    from app.models.kb import KBFact, KBSignal, KBFaq
    from app.models.auth import Enterprise, Service
    from app.service.kb_freshness_service import thin_kb_check

    eid = 2
    ent = Enterprise(id=eid, name="测试企业2", industry_pack="beauty_local", status="active")
    db_session.add(ent)
    # thin_kb_check 需要 ≥2 active services + ≥3 FAQs
    db_session.add_all([
        Service(enterprise_id=eid, name="补水", status="active"),
        Service(enterprise_id=eid, name="抗衰", status="active"),
        KBFaq(enterprise_id=eid, question="Q1", answer="A1"),
        KBFaq(enterprise_id=eid, question="Q2", answer="A2"),
        KBFaq(enterprise_id=eid, question="Q3", answer="A3"),
    ])
    db_session.flush()

    body = OnboardingRunRequest(
        enterprise={"name": "测试企业2", "industry": "beauty_local"},
        brand={"name": "品牌A"},
        stores=[{"name": "门店A", "city": "上海", "district": "静安区"}],
        services=[{"name": "补水"}, {"name": "抗衰"}],
        seed_facts=[
            SeedFact(title="资质认证", content="本机构持有卫生许可证"),
            SeedFact(title="敏感肌项目", content="采用植物萃取，0过敏率"),
        ],
        raw_inputs="我们店在静安寺商圈，主打敏感肌护理，最近想提升口碑排名",
    )

    graph_state = {
        "pain_points": [
            {"point": "口碑不足", "severity": 7, "evidence": "搜索无提及"},
            {"point": "竞品强势", "severity": 5, "evidence": "竞品A频率高"},
        ],
    }

    with patch("app.tasks.faiss_tasks.faiss_sync_item.delay", MagicMock()):
        _bootstrap_kb(db_session, eid, body, graph_state)

    # 验证 KBFact
    facts = db_session.query(KBFact).filter(KBFact.enterprise_id == eid).all()
    assert len(facts) == 2
    assert facts[0].source_type == "onboarding"

    # 验证 KBSignal
    signals = db_session.query(KBSignal).filter(KBSignal.enterprise_id == eid).all()
    assert len(signals) >= 1  # raw_input 至少一条

    # 验证 llms.txt
    ent2 = db_session.query(Enterprise).filter(Enterprise.id == eid).first()
    llms = (ent2.settings or {}).get("llms_txt", "")
    assert "品牌A" in llms
    assert "补水" in llms
    assert "静安区" in llms

    # 验证 onboarding 元数据 + thin_kb 达标
    onboarding_meta = (ent2.settings or {}).get("onboarding", {})
    assert onboarding_meta.get("fact_count") == 2
    assert onboarding_meta.get("signal_count") >= 1
    assert "thin_kb" in onboarding_meta
    assert thin_kb_check(db_session, eid).get("passed") is True

    db_session.rollback()
