"""A6 SSE 进度推送测试。"""

import json
import uuid

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient


# ═══════════════════ fixtures ═══════════════════

@pytest.fixture
def kb_user(client):
    """注册企业用户，返回 token + enterprise_id。"""
    unique = uuid.uuid4().hex[:8]
    email = f"a6-test-{unique}@example.com"
    password = "Test@12345"
    resp = client.post("/api/v1/auth/register", json={
        "email": email,
        "password": password,
        "full_name": "A6测试用户",
        "enterprise_name": f"A6测试企业-{unique}",
    })
    assert resp.status_code == 200, f"fixture register 失败: {resp.status_code} {resp.text}"
    data = resp.json()["data"]
    return {
        "email": email,
        "password": password,
        "token": data["access_token"],
        "eid": data["user"]["enterprise_id"],
    }


# ═══════════════════ T-A6-01 ═══════════════════

def test_build_event_format():
    """T-A6-01：build_event 输出格式正确。"""
    from app.core.sse import build_event

    # 基本字段
    e = build_event(25, "分析痛点中…", step="PAIN")
    assert e["progress_pct"] == 25
    assert e["progress_message"] == "分析痛点中…"
    assert e["step"] == "PAIN"
    assert e["status"] == "running"
    assert "next_route" not in e

    # 完成事件带 next_route
    e2 = build_event(100, "完成", step="done", status="completed", next_route="/strategy-pack")
    assert e2["status"] == "completed"
    assert e2["next_route"] == "/strategy-pack"


# ═══════════════════ T-A6-02 ═══════════════════

@pytest.mark.asyncio
async def test_publish_called_after_node():
    """T-A6-02：diagnose_node 完成后 publish_progress 被调用。"""
    from app.agents.state import AgentGraphState

    mock_probes = ["探针1", "探针2", "探针3"]
    mock_json = json.dumps(mock_probes, ensure_ascii=False)

    mock_chat_resp = MagicMock()
    mock_chat_resp.ok = True
    mock_chat_resp.content = mock_json

    # Mock chat（避免真实 LLM）+ Mock publish_progress
    with patch("app.agents.graphs.onboarding.nodes.chat",
               new=AsyncMock(return_value=mock_chat_resp)):
        with patch("app.agents.graphs.onboarding.nodes.publish_progress") as mock_pub:
            from app.agents.graphs.onboarding.nodes import diagnose_node

            state: AgentGraphState = {
                "enterprise_id": 1,
                "task_id": 123,
                "graph_name": "onboarding",
                "step": "start",
                "progress_pct": 0,
                "progress_message": "",
                "input_data": {
                    "enterprise": {"name": "测试"},
                    "stores": [{"city": "上海", "district": "静安区"}],
                    "services": [{"name": "补水"}],
                    "search_enabled": False,
                },
                "output_data": {},
                "errors": [],
            }

            await diagnose_node(state)

            # 断言 publish_progress 被调用
            assert mock_pub.call_count >= 1
            # 取第一次调用的参数
            args = mock_pub.call_args_list[0][0]
            task_id = args[0]
            payload = args[1]
            assert task_id == 123
            assert payload["step"] == "PAIN"
            assert payload["progress_pct"] > 0


# ═══════════════════ T-A6-03 ═══════════════════

@pytest.mark.asyncio
async def test_subscribe_progress_yields_sse():
    """T-A6-03：subscribe_progress 产出正确 SSE 格式。"""
    from app.core.sse import subscribe_progress

    # 模拟 Redis pubsub 消息流
    events = [
        {"type": "message", "data": json.dumps({"progress_pct": 10, "step": "DIAGNOSE", "status": "running"}).encode()},
        {"type": "message", "data": json.dumps({"progress_pct": 50, "step": "PERSONA", "status": "running"}).encode()},
        {"type": "message", "data": json.dumps({"progress_pct": 100, "step": "done", "status": "completed", "next_route": "/strategy-pack"}).encode()},
    ]

    class FakePubSub:
        def __init__(self):
            self._idx = 0

        async def subscribe(self, channel):
            pass

        async def unsubscribe(self, channel):
            pass

        async def get_message(self, ignore_subscribe_messages=True, timeout=30.0):
            if self._idx < len(events):
                msg = events[self._idx]
                self._idx += 1
                return msg
            return None

    class FakeRedis:
        def __init__(self, url=""):
            pass

        def pubsub(self):
            return FakePubSub()

        async def close(self):
            pass

    with patch("redis.asyncio.Redis.from_url", return_value=FakeRedis()):
        results = []
        async for event in subscribe_progress(999):
            results.append(event)

        assert len(results) >= 1
        assert results[0].startswith("data: ")
        assert results[0].endswith("\n\n")
        assert '"status"' in results[0]

        # 最后一条含 completed → 生成器应在此停止
        last = results[-1]
        assert "completed" in last


# ═══════════════════ T-A6-04 ═══════════════════

@pytest.mark.integration
def test_sse_endpoint_returns_event_stream(client: TestClient, kb_user: dict):
    """T-A6-04：GET /events/{task_id} → 200 + text/event-stream。"""
    from app.models import AgentTask
    from app.core.db import SessionLocal

    eid = kb_user["eid"]
    token = kb_user["token"]

    # 先创建一个 AgentTask（真实 DB，与 TestClient 同一库）
    db = SessionLocal()
    try:
        task = AgentTask(
            enterprise_id=eid,
            task_type="onboarding_pipeline",
            graph_name="onboarding",
            status="running",
            progress_pct=0,
        )
        db.add(task)
        db.commit()
        task_id = task.id
    finally:
        db.close()

    # Mock subscribe_progress（端点内 from app.core.sse import）
    async def _fake_events(tid):
        yield "data: {}\n\n".format(json.dumps({"progress_pct": 50, "status": "running", "step": "test"}))

    with patch("app.core.sse.subscribe_progress", side_effect=_fake_events):
        with client.stream(
            "GET",
            f"/api/v1/user/onboarding/events/{task_id}",
            headers={"Authorization": f"Bearer {token}"},
        ) as resp:
            assert resp.status_code == 200, f"SSE 应 200，实际 {resp.status_code}"
            content_type = resp.headers.get("content-type", "")
            assert "text/event-stream" in content_type, f"Content-Type 应为 text/event-stream，实际 {content_type}"
            body = "".join(resp.iter_text())
            assert "data: {" in body
