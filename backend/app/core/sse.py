"""Redis pub/sub — SSE 进度事件推送。"""

import json
from typing import AsyncGenerator, Dict, Any, Optional

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)

# SSE pub/sub 使用独立的 Redis db（3），避免与 Celery broker(0)/backend(1)/result(2) 冲突
_SSE_REDIS_DB = 3


def _get_redis_url(db: int) -> str:
    """从 settings.REDIS_URL 替换 db 号。"""
    url = settings.REDIS_URL
    # redis://:password@host:port/db  → 替换 db 号
    if url.rstrip("/").endswith(f"/{db}"):
        return url
    # 去掉旧 db 号，拼新的
    base = url.rsplit("/", 1)[0]
    return f"{base}/{db}"


def channel_name(task_id: int) -> str:
    return f"onboarding:{task_id}"


def publish_progress(task_id: int, payload: Dict[str, Any]) -> None:
    """同步发布进度事件（供 nodes.py / runner.py 在 async 上下文外调用）。

    使用同步 redis 客户端，避免阻塞事件循环。
    """
    try:
        import redis
        r = redis.Redis.from_url(_get_redis_url(_SSE_REDIS_DB))
        msg = json.dumps(payload, ensure_ascii=False)
        r.publish(channel_name(task_id), msg)
        r.close()
    except Exception as e:
        logger.warning("[sse] publish failed task=%s: %s", task_id, e)


async def publish_progress_async(task_id: int, payload: Dict[str, Any]) -> None:
    """异步发布进度事件（供 async 函数使用）。"""
    try:
        import redis.asyncio as aioredis
        r = aioredis.Redis.from_url(_get_redis_url(_SSE_REDIS_DB))
        await r.publish(channel_name(task_id), json.dumps(payload, ensure_ascii=False))
        await r.close()
    except Exception as e:
        logger.warning("[sse] publish async failed task=%s: %s", task_id, e)


async def subscribe_progress(task_id: int) -> AsyncGenerator[str, None]:
    """订阅进度事件 → SSE 事件流生成器。

    用法（FastAPI StreamingResponse）：
        async def events():
            async for event in subscribe_progress(task_id):
                yield event
        return StreamingResponse(events(), media_type="text/event-stream")
    """
    try:
        import redis.asyncio as aioredis
        r = aioredis.Redis.from_url(_get_redis_url(_SSE_REDIS_DB))
        pubsub = r.pubsub()
        await pubsub.subscribe(channel_name(task_id))
        try:
            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=30.0)
                if message and message.get("type") == "message":
                    data = message["data"]
                    if isinstance(data, bytes):
                        data = data.decode("utf-8")
                    yield f"data: {data}\n\n"
                    # 如果收到 completed 或 failed，结束推送
                    try:
                        payload = json.loads(data)
                        if payload.get("status") in ("completed", "failed"):
                            break
                    except Exception:
                        pass
        finally:
            await pubsub.unsubscribe(channel_name(task_id))
            await r.close()
    except Exception as e:
        logger.warning("[sse] subscribe failed task=%s: %s", task_id, e)
        yield f"data: {json.dumps({'error': str(e)})}\n\n"


# 快捷构造
def build_event(
    progress_pct: int,
    progress_message: str,
    step: str = "",
    status: str = "running",
    next_route: Optional[str] = None,
) -> Dict[str, Any]:
    payload = {
        "progress_pct": progress_pct,
        "progress_message": progress_message,
        "step": step,
        "status": status,
    }
    if next_route:
        payload["next_route"] = next_route
    return payload
