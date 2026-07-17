"""AutoInitManager 单元测试。"""
from __future__ import annotations

import asyncio

import pytest
from fastapi import FastAPI

from app.infrastructure.bootstrap.init_manager import AutoInitManager


@pytest.fixture
def manager() -> AutoInitManager:
    m = AutoInitManager()
    yield m
    m.reset_for_tests()


@pytest.mark.asyncio
async def test_sync_and_async_init(manager: AutoInitManager):
    calls: list[str] = []

    def sync_init():
        calls.append("sync")

    async def async_init():
        calls.append("async")
        await asyncio.sleep(0)

    manager.register_init(sync_init, name="sync", priority=10)
    manager.register_init(async_init, name="async", priority=20)

    app = FastAPI()
    await manager.start(app)

    assert calls == ["sync", "async"]


@pytest.mark.asyncio
async def test_start_is_idempotent(manager: AutoInitManager):
    count = 0

    def inc():
        nonlocal count
        count += 1

    manager.register_init(inc, name="inc")
    app = FastAPI()
    await manager.start(app)
    await manager.start(app)
    assert count == 1


@pytest.mark.asyncio
async def test_stop_is_idempotent(manager: AutoInitManager):
    count = 0

    def on_stop():
        nonlocal count
        count += 1

    manager.register_stop(on_stop, name="stop")
    await manager.stop()
    await manager.stop()
    assert count == 1


@pytest.mark.asyncio
async def test_roles_filter_skips_worker_only_on_api(manager: AutoInitManager, monkeypatch):
    monkeypatch.setenv("APP_PROCESS_ROLE", "api")
    # 若 Settings 可导入则一并覆盖，保证与生产路径一致
    try:
        from app.core.config import settings

        monkeypatch.setattr(settings, "APP_PROCESS_ROLE", "api")
    except Exception:
        pass

    calls: list[str] = []

    manager.register_init(lambda: calls.append("api"), name="api_item", roles=("api",))
    manager.register_init(lambda: calls.append("worker"), name="worker_item", roles=("worker",))

    await manager.start(FastAPI())
    assert calls == ["api"]


@pytest.mark.asyncio
async def test_critical_init_failure_blocks(manager: AutoInitManager):
    def boom():
        raise RuntimeError("db down")

    manager.register_init(boom, name="db", critical=True)

    with pytest.raises(RuntimeError):
        await manager.start(FastAPI())


@pytest.mark.asyncio
async def test_non_critical_init_failure_continues(manager: AutoInitManager):
    calls: list[str] = []

    def boom():
        raise RuntimeError("warmup failed")

    def ok():
        calls.append("ok")

    manager.register_init(boom, name="warmup", critical=False, priority=10)
    manager.register_init(ok, name="ok", priority=20)

    await manager.start(FastAPI())
    assert calls == ["ok"]
    status = manager.get_status()
    assert status["items"]["warmup"]["status"] == "failed"


@pytest.mark.asyncio
async def test_app_state_resources(manager: AutoInitManager):
    app = FastAPI()

    def mark_db(app: FastAPI):
        app.state.resources["database"] = {"status": "ok"}

    manager.register_init(mark_db, name="database")
    await manager.start(app)
    assert app.state.resources["database"]["status"] == "ok"
