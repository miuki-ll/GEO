"""A3 LLM Gateway 测试 — mock 搜索/cite解析/fallback/重试

用例对照 G-L3-开发者A任务手册.md §11.3：
  T-A3-01 ~ T-A3-06
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.core.llm.schemas import (
    SearchRequest,
    SearchResponse,
    SearchCitation,
    LLMUsage,
    LLMResponse,
)
from app.core.llm import simple_search, simple_prompt, chat, search


# ── T-A3-01：simple_search() 构造正确 ──
def test_simple_search_constructs_correctly():
    req = simple_search("静安寺皮肤管理推荐")
    assert req.query == "静安寺皮肤管理推荐"
    assert req.timeout == 200
    assert req.max_keywords == 3
    assert req.limit == 10


# ── T-A3-02：DoubaoAdapter.search() 正确解析 citations ──
@pytest.mark.asyncio
async def test_doubao_search_parses_citations():
    from app.core.llm.adapters import DoubaoAdapter

    mock_payload = {
        "id": "test123",
        "model": "doubao-seed-2-1-pro-260628",
        "output": [{
            "content": [{
                "text": "根据搜索结果，静安寺附近有多家皮肤管理门店...",
                "annotations": [
                    {
                        "type": "url_citation",
                        "url": "https://www.dianping.com/shop/123",
                        "title": "XX皮肤管理中心",
                        "summary": "这家店位于静安寺附近，主打韩式皮肤管理..." * 10,
                        "site_name": "大众点评",
                    },
                    {
                        "type": "url_citation",
                        "url": "https://www.xiaohongshu.com/note/456",
                        "title": "静安寺皮肤管理探店",
                        "summary": "上周去了静安寺的一家皮肤管理店..." * 10,
                        "site_name": "小红书",
                    },
                ],
            }]
        }],
        "usage": {"input_tokens": 150, "output_tokens": 500, "total_tokens": 650},
    }

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_payload

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    adapter = DoubaoAdapter()
    with patch("httpx.AsyncClient", return_value=mock_client):
        resp = await adapter.search(SearchRequest(query="静安寺皮肤管理推荐"))

    assert resp.ok is True
    assert len(resp.citations) == 2
    assert resp.citations[0].url == "https://www.dianping.com/shop/123"
    assert resp.citations[0].site_name == "大众点评"
    assert len(resp.answer) > 0
    assert resp.usage.prompt_tokens == 150


# ── T-A3-03：gateway.search() — 豆包成功时立即返回 ──
@pytest.mark.asyncio
async def test_gateway_search_doubao_success():
    mock_resp = SearchResponse(
        engine="doubao",
        model="doubao-seed-2-1-pro-260628",
        answer="静安寺附近有多家皮肤管理门店...",
        citations=[SearchCitation(url="https://example.com", title="测试", summary="摘要", site_name="测试站")],
        usage=LLMUsage(prompt_tokens=100, completion_tokens=200, total_tokens=300),
    )

    with patch("app.core.llm.gateway.get_adapter") as mock_get:
        mock_adapter = MagicMock()
        mock_adapter.api_key = "fake-key"
        mock_adapter.search = AsyncMock(return_value=mock_resp)
        mock_get.return_value = mock_adapter

        resp = await search(simple_search("测试查询", engine="doubao"))

    assert resp.ok is True
    assert resp.engine == "doubao"
    assert "静安寺" in resp.answer


# ── T-A3-04：有 Key + search 不支持 → chat 模拟（决策 2B）──
@pytest.mark.asyncio
async def test_gateway_search_fallback_to_chat():
    mock_chat_resp = LLMResponse(
        engine="kimi",
        model="moonshot-v1-32k",
        content="## AI 回答\n模拟搜索回答内容...\n## 品牌提及\nXX皮肤管理",
        usage=LLMUsage(prompt_tokens=50, completion_tokens=300, total_tokens=350),
    )

    with patch("app.core.llm.gateway.get_adapter") as mock_get:
        mock_adapter = MagicMock()
        mock_adapter.api_key = "fake-kimi-key"  # 有 Key，但 search 不支持
        mock_adapter.search = AsyncMock(return_value=SearchResponse(
            engine="kimi", model="", error="[kimi] 不支持联网搜索"
        ))
        mock_adapter.chat = AsyncMock(return_value=mock_chat_resp)
        mock_get.return_value = mock_adapter

        resp = await search(simple_search("测试查询", engine="kimi"))

    assert resp.ok is True
    assert resp.extra.get("simulated") is True


# ── T-A3-05：gateway.search() — 全部失败时返回 error ──
@pytest.mark.asyncio
async def test_gateway_search_all_fail():
    with patch("app.core.llm.gateway.get_adapter") as mock_get:
        mock_adapter = MagicMock()
        mock_adapter.api_key = ""  # 无 API Key
        mock_adapter.search = AsyncMock(return_value=SearchResponse(
            engine="none", model="", error="not configured"
        ))
        mock_adapter.chat = AsyncMock(return_value=LLMResponse(
            engine="none", model="", content="", usage=LLMUsage(), error="chat failed"
        ))
        mock_get.return_value = mock_adapter

        resp = await search(simple_search("测试"))

    assert resp.ok is False
    assert resp.error is not None
    assert len(resp.error) > 0


# ── T-A3-06：gateway.chat() — fallback 链验证 ──
@pytest.mark.asyncio
async def test_gateway_chat_fallback():
    fail_resp = LLMResponse(
        engine="doubao", model="doubao-pro-32k", content="",
        usage=LLMUsage(), error="HTTP 500", retry_count=0,
    )
    success_resp = LLMResponse(
        engine="deepseek", model="deepseek-chat", content="你好！",
        usage=LLMUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
        retry_count=1,
    )

    def mock_get_adapter(engine):
        mock = MagicMock()
        if engine == "doubao":
            mock.api_key = "fake-doubao-key"
            mock.chat = AsyncMock(return_value=fail_resp)
        else:
            mock.api_key = "fake-deepseek-key"
            mock.chat = AsyncMock(return_value=success_resp)
        return mock

    with patch("app.core.llm.gateway.get_adapter", side_effect=mock_get_adapter):
        resp = await chat(simple_prompt("你好", engine="doubao"))

    assert resp.ok is True
    assert resp.engine == "deepseek"
    assert resp.retry_count > 0
