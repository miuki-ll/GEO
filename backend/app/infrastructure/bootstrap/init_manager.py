"""全局资源生命周期管理器（幂等）。"""
from __future__ import annotations

import asyncio
import inspect
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Optional, Union

from fastapi import FastAPI

logger = logging.getLogger(__name__)

InitFunc = Callable[..., Union[Any, Awaitable[Any]]]


@dataclass(order=True)
class _LifecycleItem:
    priority: int
    name: str = field(compare=False)
    func: InitFunc = field(compare=False)
    roles: tuple[str, ...] = field(compare=False, default=("api", "worker", "mcp"))
    critical: bool = field(compare=False, default=True)


class AutoInitManager:
    """注册并按角色/优先级执行 init/stop，支持同步与异步函数。"""

    def __init__(self) -> None:
        self._init_items: list[_LifecycleItem] = []
        self._stop_items: list[_LifecycleItem] = []
        self._started = False
        self._stopped = False
        self._app: Optional[FastAPI] = None
        self._status: dict[str, dict[str, Any]] = {}
        self._background_tasks: list[asyncio.Task] = []

    def register_init(
        self,
        func: InitFunc,
        *,
        name: Optional[str] = None,
        priority: int = 100,
        roles: tuple[str, ...] = ("api", "worker", "mcp"),
        critical: bool = True,
    ) -> None:
        self._init_items.append(
            _LifecycleItem(
                priority=priority,
                name=name or func.__name__,
                func=func,
                roles=roles,
                critical=critical,
            )
        )

    def register_stop(
        self,
        func: InitFunc,
        *,
        name: Optional[str] = None,
        priority: int = 100,
        roles: tuple[str, ...] = ("api", "worker", "mcp"),
        critical: bool = False,
    ) -> None:
        self._stop_items.append(
            _LifecycleItem(
                priority=priority,
                name=name or func.__name__,
                func=func,
                roles=roles,
                critical=critical,
            )
        )

    def _current_role(self) -> str:
        import os

        # 优先 Settings；单测可 monkeypatch settings 或环境变量
        try:
            from app.core.config import settings

            role = (settings.APP_PROCESS_ROLE or "api").strip().lower()
        except Exception:
            role = (os.getenv("APP_PROCESS_ROLE") or "api").strip().lower()
        return role or "api"

    def _filter_items(self, items: list[_LifecycleItem]) -> list[_LifecycleItem]:
        role = self._current_role()
        return [item for item in items if role in item.roles]

    async def _call(self, func: InitFunc, app: Optional[FastAPI]) -> Any:
        sig = inspect.signature(func)
        if "app" in sig.parameters:
            result = func(app)
        else:
            result = func()
        if asyncio.iscoroutine(result) or inspect.isawaitable(result):
            return await result
        return result

    async def start(self, app: Optional[FastAPI] = None) -> None:
        if self._started:
            logger.debug("AutoInitManager.start skipped (already started)")
            return

        self._app = app
        if app is not None:
            if not hasattr(app.state, "resources") or app.state.resources is None:
                app.state.resources = {}

        role = self._current_role()
        logger.info("AutoInitManager.start role=%s", role)

        for item in sorted(self._filter_items(self._init_items)):
            started = time.perf_counter()
            try:
                await self._call(item.func, app)
                duration_ms = int((time.perf_counter() - started) * 1000)
                self._status[item.name] = {
                    "status": "ok",
                    "duration_ms": duration_ms,
                    "role": role,
                }
                logger.info(
                    "init ok name=%s duration_ms=%s critical=%s",
                    item.name,
                    duration_ms,
                    item.critical,
                )
            except Exception as exc:
                duration_ms = int((time.perf_counter() - started) * 1000)
                self._status[item.name] = {
                    "status": "failed",
                    "duration_ms": duration_ms,
                    "error": str(exc),
                    "role": role,
                }
                logger.exception(
                    "init failed name=%s duration_ms=%s critical=%s",
                    item.name,
                    duration_ms,
                    item.critical,
                )
                if item.critical:
                    raise
                logger.warning("non-critical init failed, continuing: %s", item.name)

        self._started = True

    async def stop(self) -> None:
        if self._stopped:
            logger.debug("AutoInitManager.stop skipped (already stopped)")
            return

        role = self._current_role()
        for task in self._background_tasks:
            if not task.done():
                task.cancel()
        for task in self._background_tasks:
            if not task.done():
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        self._background_tasks.clear()

        for item in sorted(self._filter_items(self._stop_items), reverse=True):
            started = time.perf_counter()
            try:
                await self._call(item.func, self._app)
                duration_ms = int((time.perf_counter() - started) * 1000)
                logger.info("stop ok name=%s duration_ms=%s", item.name, duration_ms)
            except Exception:
                logger.exception("stop failed name=%s role=%s", item.name, role)
                if item.critical:
                    raise

        self._stopped = True
        self._started = False

    def schedule_background(self, coro: Awaitable[Any]) -> asyncio.Task:
        task = asyncio.create_task(coro)
        self._background_tasks.append(task)
        return task

    def get_status(self) -> dict[str, Any]:
        return {
            "started": self._started,
            "stopped": self._stopped,
            "role": self._current_role(),
            "items": dict(self._status),
        }

    def reset_for_tests(self) -> None:
        """仅测试使用：清空注册与状态。"""
        self._init_items.clear()
        self._stop_items.clear()
        self._started = False
        self._stopped = False
        self._app = None
        self._status.clear()
        self._background_tasks.clear()


auto_init = AutoInitManager()
