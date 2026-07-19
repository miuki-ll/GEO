"""A7 诊断测试 — probes/search/analyze/source_map/T0。"""

import json

import pytest
from unittest.mock import AsyncMock, patch
from sqlalchemy.orm import Session


# ═══════════════════ Mock 工具 ═══════════════════

def _make_mock_chat_response(content: str):
    from app.core.llm.schemas import LLMResponse, LLMUsage
    return LLMResponse(engine="doubao", model="test", content=content, usage=LLMUsage())


def _make_mock_search_response(citations=None):
    from app.core.llm.schemas import SearchResponse, SearchCitation, LLMUsage
    cites = []
    for c in (citations or []):
        cites.append(SearchCitation(
            url=c.get("url", "https://example.com"),
            title=c.get("title", "测试"),
            summary=c.get("summary", "摘要内容"),
            site_name=c.get("site_name", "测试站"),
        ))
    return SearchResponse(
        engine="doubao", model="test", answer="模拟搜索回答",
        citations=cites, usage=LLMUsage(), latency_ms=1000,
    )


def _db_factory_from(db_session: Session):
    """从 fixture 的 engine 建新 session，供 batch_search 并发写入后 close。"""
    from sqlalchemy.orm import sessionmaker

    SessionLocal = sessionmaker(
        bind=db_session.get_bind(),
        autocommit=False,
        autoflush=False,
        future=True,
    )
    return SessionLocal


# ═══════════════════ T-A7-01 ═══════════════════

@pytest.mark.asyncio
async def test_generate_probes():
    """T-A7-01：generate_probes 返回探针列表。"""
    from app.service.diagnosis_service import DiagnosisService

    mock_probes = ["静安区皮肤管理推荐", "静安寺附近美容院哪个好", "敏感肌修护静安区哪家专业"]
    mock_resp = _make_mock_chat_response(json.dumps(mock_probes, ensure_ascii=False))

    with patch("app.service.diagnosis_service.chat", new=AsyncMock(return_value=mock_resp)):
        probes = await DiagnosisService.generate_probes("测试店", "上海", "静安区")
        assert isinstance(probes, list)
        assert len(probes) >= 3
        assert "静安区" in probes[0]


# ═══════════════════ T-A7-02 ═══════════════════

@pytest.mark.asyncio
async def test_batch_search_writes_search_results(db_session: Session):
    """T-A7-02：batch_search 写入 search_results 表。"""
    from app.service.diagnosis_service import DiagnosisService
    from app.models.strategy import SearchResult
    from app.models import Enterprise

    eid = 1
    ent = Enterprise(id=eid, name="测试企业", industry_pack="beauty_local", status="active")
    db_session.add(ent)
    db_session.flush()

    mock_citations = [
        {"url": "https://dp.com/1", "title": "门店A", "summary": "好评", "site_name": "大众点评"},
        {"url": "https://xhs.com/1", "title": "探店", "summary": "推荐", "site_name": "小红书"},
        {"url": "https://zh.com/1", "title": "问答", "summary": "讨论", "site_name": "知乎"},
    ]
    mock_resp = _make_mock_search_response(mock_citations)

    with patch("app.service.diagnosis_service.search", new=AsyncMock(return_value=mock_resp)):
        results = await DiagnosisService.batch_search(
            _db_factory_from(db_session), eid,
            probes=["探针1", "探针2"],
            engines=["doubao"],
            batch_no="test-batch-001",
        )

    assert len(results) == 2
    assert results[0]["ok"] is True

    # 验证 search_results 表
    rows = db_session.query(SearchResult).filter(
        SearchResult.enterprise_id == eid,
        SearchResult.diagnosis_batch_no == "test-batch-001",
    ).all()
    assert len(rows) == 2
    assert rows[0].citation_count == 3
    assert len(rows[0].citations) == 3

    db_session.rollback()


# ═══════════════════ T-A7-03 ═══════════════════

@pytest.mark.asyncio
async def test_analyze_from_citations(db_session: Session):
    """T-A7-03：从 search_results 分析 citations。"""
    from app.service.diagnosis_service import DiagnosisService
    from app.models.strategy import SearchResult
    from app.models import Enterprise

    eid = 2
    batch_no = "test-batch-002"
    ent = Enterprise(id=eid, name="测试企业2", industry_pack="beauty_local", status="active")
    db_session.add(ent)
    db_session.flush()

    # 插入假 search_results
    db_session.add(SearchResult(
        enterprise_id=eid, probe_query="探针1", engine="doubao",
        answer="测试回答", citations=[
            {"url": "https://x.com", "title": "竞品A", "summary": "竞品A口碑好", "site_name": "小红书"},
        ],
        citation_count=1, diagnosis_batch_no=batch_no,
    ))
    db_session.commit()

    mock_analysis = {
        "brand_mentioned": True,
        "mention_context": "正面评价",
        "rank_estimate": 3,
        "competitor_occupancy": [{"name": "竞品A", "count": 5, "platforms": ["小红书"]}],
        "pain_points": [{"point": "口碑不足", "severity": 7, "evidence": "竞品A提及更多"}],
    }
    mock_resp = _make_mock_chat_response(json.dumps(mock_analysis, ensure_ascii=False))

    with patch("app.service.diagnosis_service.chat", new=AsyncMock(return_value=mock_resp)):
        result = await DiagnosisService.analyze_from_citations(db_session, eid, batch_no, "测试店")

    assert result.get("brand_mentioned") is True
    assert len(result.get("competitor_occupancy", [])) >= 1
    assert len(result.get("pain_points", [])) >= 1

    db_session.rollback()


# ═══════════════════ T-A7-04 ═══════════════════

def test_build_source_map(db_session: Session):
    """T-A7-04：build_source_map 聚合平台分布。"""
    from app.service.diagnosis_service import DiagnosisService
    from app.models.strategy import SearchResult
    from app.models import Enterprise

    eid = 3
    batch_no = "test-batch-003"
    ent = Enterprise(id=eid, name="测试企业3", industry_pack="beauty_local", status="active")
    db_session.add(ent)
    db_session.flush()

    # 插入 3 条，citations 来自不同平台
    db_session.add_all([
        SearchResult(enterprise_id=eid, probe_query="p1", engine="doubao",
                     citations=[{"site_name": "大众点评", "url": "x", "title": "t", "summary": "s"}],
                     citation_count=1, diagnosis_batch_no=batch_no),
        SearchResult(enterprise_id=eid, probe_query="p2", engine="doubao",
                     citations=[{"site_name": "小红书", "url": "x", "title": "t", "summary": "s"}],
                     citation_count=1, diagnosis_batch_no=batch_no),
        SearchResult(enterprise_id=eid, probe_query="p3", engine="doubao",
                     citations=[{"site_name": "知乎", "url": "x", "title": "t", "summary": "s"}],
                     citation_count=1, diagnosis_batch_no=batch_no),
    ])
    db_session.commit()

    result = DiagnosisService.build_source_map(db_session, eid, batch_no)

    assert result["total_citations"] == 3
    assert result["total_probes"] == 3
    assert len(result["platforms"]) == 3
    # 权重和应为 1.0
    total_weight = sum(p["weight"] for p in result["platforms"])
    assert abs(total_weight - 1.0) < 0.01

    db_session.rollback()


# ═══════════════════ T-A7-05 ═══════════════════

def test_write_t0_baseline(db_session: Session):
    """T-A7-05：write_t0_baseline 写入 monitor_results。"""
    from app.service.diagnosis_service import DiagnosisService
    from app.models.strategy import SearchResult
    from app.models.monitor import MonitorResult
    from app.models import Enterprise

    eid = 4
    batch_no = "test-batch-004"
    ent = Enterprise(id=eid, name="测试企业4", industry_pack="beauty_local", status="active")
    db_session.add(ent)
    db_session.flush()

    db_session.add(SearchResult(
        enterprise_id=eid, probe_query="探针T0", engine="doubao",
        answer="回答内容", citations=[{"url": "x", "title": "t", "summary": "s", "site_name": "大众点评"}],
        citation_count=1, diagnosis_batch_no=batch_no,
    ))
    db_session.commit()

    analysis = {"brand_mentioned": True, "mention_context": "正面", "rank_estimate": 5,
                "competitor_occupancy": [], "pain_points": []}
    source_map = {"total_citations": 1, "total_probes": 1, "platforms": [], "top_domains": []}

    count = DiagnosisService.write_t0_baseline(db_session, eid, batch_no, analysis, source_map)
    assert count == 1

    # 验证 monitor_results
    mr = db_session.query(MonitorResult).filter(
        MonitorResult.enterprise_id == eid,
        MonitorResult.batch_no == batch_no,
    ).first()
    assert mr is not None
    assert mr.baseline is True
    assert mr.mentioned is True
    assert mr.position_rank == 5

    db_session.rollback()
