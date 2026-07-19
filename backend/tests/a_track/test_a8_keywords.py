"""A8 词库测试 — CRUD / 四源汇聚 / LLM 分类 / 四层汇总

用例对照 G-L3-开发者A任务手册.md §11.3：
  T-A8-01 ~ T-A8-06
"""
import json

import pytest
from unittest.mock import AsyncMock, patch
from sqlalchemy.orm import Session


# ═══════════════════ Mock 工具 ═══════════════════

def _make_mock_chat_response(content: str):
    from app.core.llm.schemas import LLMResponse, LLMUsage
    return LLMResponse(engine="doubao", model="test", content=content, usage=LLMUsage())


class _SessionProxy:
    """包装 db_session：close() 空操作，避免 generate_keywords 关掉 fixture session。"""

    def __init__(self, real: Session):
        self._real = real

    def __getattr__(self, name):
        return getattr(self._real, name)

    def close(self):
        return None


def _prompt_text(req) -> str:
    """从 LLMRequest / 任意参数抽出 prompt 文本。"""
    if req is None:
        return ""
    if hasattr(req, "messages"):
        return " ".join(getattr(m, "content", "") or "" for m in (req.messages or []))
    return str(req)


# ═══════════════════ T-A8-01 ═══════════════════

def test_crud_and_tenant_isolation(two_tenants):
    """T-A8-01：CRUD + 租户隔离。"""
    from app.service.keyword_service import KeywordService

    db = two_tenants["db"]
    e1_id = two_tenants["e1"].id
    e2_id = two_tenants["e2"].id

    # Create
    kw1 = KeywordService.create_keyword(db, e1_id, {"phrase": "皮肤管理", "layer": "认知层", "source": "手动"})
    kw2 = KeywordService.create_keyword(db, e1_id, {"phrase": "敏感肌护理", "layer": "认知层", "source": "SEO API"})
    assert kw1.id is not None
    assert kw2.id is not None

    # List
    result = KeywordService.list_keywords(db, e1_id)
    assert result["total"] == 2

    # Update
    updated = KeywordService.update_keyword(db, e1_id, kw1.id, {"layer": "选型层"})
    assert updated.layer == "选型层"

    # Delete
    ok = KeywordService.delete_keyword(db, e1_id, kw1.id)
    assert ok is True
    result = KeywordService.list_keywords(db, e1_id)
    assert result["total"] == 1

    # 租户隔离：tenant B 看不到 tenant A 的关键词
    result_b = KeywordService.list_keywords(db, e2_id)
    assert result_b["total"] == 0

    db.rollback()


# ═══════════════════ T-A8-02 ═══════════════════

def test_from_raw_inputs(db_session: Session):
    """T-A8-02：_from_raw_inputs 拆词。"""
    from app.service.keyword_service import KeywordService
    from app.models import Enterprise

    eid = 101
    ent = Enterprise(id=eid, name="测试店", industry_pack="beauty_local", status="active",
                     raw_inputs="静安寺附近皮肤管理推荐，敏感肌修护价格怎么样")
    db_session.add(ent)
    db_session.flush()

    words = KeywordService._from_raw_inputs(db_session, eid)
    assert isinstance(words, list)
    assert len(words) >= 2
    # 应包含拆出的词
    assert any("皮肤管理" in w for w in words) or any("皮肤" in w for w in words)

    db_session.rollback()


# ═══════════════════ T-A8-03 ═══════════════════

def test_from_probes(db_session: Session):
    """T-A8-03：_from_probes 从探针提取关键词。"""
    from app.service.keyword_service import KeywordService
    from app.models.strategy import SearchResult
    from app.models import Enterprise

    eid = 102
    ent = Enterprise(id=eid, name="测试店2", industry_pack="beauty_local", status="active")
    db_session.add(ent)
    db_session.flush()

    db_session.add_all([
        SearchResult(enterprise_id=eid, probe_query="静安寺皮肤管理推荐哪家好", engine="doubao",
                     citations=[], citation_count=0, diagnosis_batch_no="batch-001"),
        SearchResult(enterprise_id=eid, probe_query="敏感肌修护价格多少", engine="doubao",
                     citations=[], citation_count=0, diagnosis_batch_no="batch-001"),
    ])
    db_session.commit()

    words = KeywordService._from_probes(db_session, eid)
    assert isinstance(words, list)
    assert len(words) >= 2
    # 应包含探针中的关键词
    assert any("皮肤管理" in w for w in words)

    db_session.rollback()


# ═══════════════════ T-A8-04 ═══════════════════

def test_from_seo(db_session: Session):
    """T-A8-04：_from_seo mock 数据。"""
    from app.service.keyword_service import KeywordService
    from app.models import Enterprise

    eid = 103
    ent = Enterprise(id=eid, name="测试店3", industry_pack="beauty_local", status="active",
                     settings={"city": "上海"})
    db_session.add(ent)
    db_session.flush()

    words = KeywordService._from_seo(db_session, eid)
    assert isinstance(words, list)
    assert len(words) >= 5
    # 应包含美容通用词
    assert "皮肤管理" in words
    # 应包含地域词
    assert any("上海" in w for w in words)

    db_session.rollback()


# ═══════════════════ T-A8-05 ═══════════════════

@pytest.mark.asyncio
async def test_generate_keywords_full_pipeline(db_session: Session):
    """T-A8-05：generate_keywords 全流程（mock LLM）。"""
    from app.service.keyword_service import KeywordService
    from app.models.strategy import SearchResult, Keyword
    from app.models import Enterprise

    eid = 104
    ent = Enterprise(id=eid, name="测试美容店", industry_pack="beauty_local", status="active",
                     raw_inputs="静安寺皮肤管理推荐，敏感肌修护",
                     settings={"city": "上海"})
    db_session.add(ent)
    db_session.flush()

    # 插入探针
    db_session.add(SearchResult(
        enterprise_id=eid, probe_query="上海皮肤管理哪家好", engine="doubao",
        citations=[], citation_count=0, diagnosis_batch_no="batch-002",
    ))
    db_session.commit()

    llm_words = ["白领午休护肤", "换季敏感肌急救"]

    async def mock_chat_side_effect(*args, **kwargs):
        """根据 prompt 内容返回不同 mock。"""
        prompt = _prompt_text(args[0] if args else None)
        # _from_llm 的 prompt 含"补充 10-15 个遗漏的长尾关键词"
        if "遗漏的长尾关键词" in prompt:
            return _make_mock_chat_response(json.dumps(llm_words, ensure_ascii=False))
        # _classify_by_llm：按输入词逐条分类（覆盖汇聚后的全部 phrase）
        # 从 prompt 里无法可靠解析全部词，返回固定子集 + seo/raw 常见词
        classified = [
            {"phrase": "皮肤管理", "layer": "认知层", "lbs_tags": []},
            {"phrase": "敏感肌", "layer": "认知层", "lbs_tags": []},
            {"phrase": "静安寺", "layer": "选型层", "lbs_tags": ["静安区"]},
            {"phrase": "上海皮肤管理哪家好", "layer": "选型层", "lbs_tags": ["上海"]},
            {"phrase": "白领午休护肤", "layer": "场景层", "lbs_tags": []},
            {"phrase": "换季敏感肌急救", "layer": "场景层", "lbs_tags": []},
        ]
        return _make_mock_chat_response(json.dumps(classified, ensure_ascii=False))

    with patch("app.service.keyword_service.chat", new=AsyncMock(side_effect=mock_chat_side_effect)):
        result = await KeywordService.generate_keywords(
            db_factory=lambda: _SessionProxy(db_session),
            enterprise_id=eid,
            enterprise_name="测试美容店",
            city="上海",
        )

    assert result["inserted"] > 0
    assert result["total_sources"] > 0

    # 验证 keywords 表
    rows = db_session.query(Keyword).filter(Keyword.enterprise_id == eid).all()
    assert len(rows) == result["inserted"]
    # 至少有一条 layer 不为空
    layers = {r.layer for r in rows}
    assert len(layers) >= 2  # 至少有认知层和选型层

    db_session.rollback()


# ═══════════════════ T-A8-06 ═══════════════════

def test_layer_summary(db_session: Session):
    """T-A8-06：get_layer_summary 四层汇总。"""
    from app.service.keyword_service import KeywordService
    from app.models.strategy import Keyword
    from app.models import Enterprise

    eid = 105
    ent = Enterprise(id=eid, name="测试店5", industry_pack="beauty_local", status="active")
    db_session.add(ent)
    db_session.flush()

    db_session.add_all([
        Keyword(enterprise_id=eid, phrase="皮肤管理", layer="认知层", source="SEO API"),
        Keyword(enterprise_id=eid, phrase="VISIA检测", layer="认知层", source="手动"),
        Keyword(enterprise_id=eid, phrase="静安寺皮肤管理推荐", layer="选型层", source="LLM生成"),
        Keyword(enterprise_id=eid, phrase="皮肤管理会不会越做越敏感", layer="痛点层", source="RawInputs"),
        Keyword(enterprise_id=eid, phrase="白领午休皮肤管理", layer="场景层", source="LLM生成"),
    ])
    db_session.commit()

    summary = KeywordService.get_layer_summary(db_session, eid)
    assert len(summary) == 4  # 四个层

    layer_counts = {s["layer"]: s["count"] for s in summary}
    assert layer_counts.get("认知层") == 2
    assert layer_counts.get("选型层") == 1
    assert layer_counts.get("痛点层") == 1
    assert layer_counts.get("场景层") == 1

    db_session.rollback()
