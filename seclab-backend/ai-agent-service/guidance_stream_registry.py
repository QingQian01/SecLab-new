"""SSE 订阅广播注册表（单 worker 部署约束）。

设计约束：
- 仅支持单 uvicorn worker；多 worker 部署时需用 Redis Pub/Sub 替换（当前不做）。
- 每个 lab_session_id 维护一组 asyncio.Queue 订阅者。
- 信号触发时通过 :func:`publish` 向所有订阅者推送事件。
- 订阅者断开（取消迭代）时自动清理。

典型用法::

    # SSE 端点（main.py）
    async def event_stream():
        async for event in guidance_stream_registry.subscribe(lab_session_id):
            yield f"data: {json.dumps(event)}\\n\\n"

    # 信号处理（guidance_service.py）
    await guidance_stream_registry.publish(lab_session_id, {"type": "chunk", "content": "..."})
"""
import asyncio
import logging
from typing import Any, AsyncIterator

logger = logging.getLogger(__name__)

# lab_session_id -> set of subscriber queues
_queues: dict[str, set[asyncio.Queue[dict[str, Any]]]] = {}
_lock = asyncio.Lock()


async def subscribe(lab_session_id: str) -> AsyncIterator[dict[str, Any]]:
    """订阅指定 lab_session_id 的事件流。

    生成器会在取消时自动清理。当 :func:`close_all` 被调用时，会收到 ``None`` 哨兵并正常结束。
    """
    queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=100)
    async with _lock:
        _queues.setdefault(lab_session_id, set()).add(queue)
    logger.info(
        "guidance SSE subscriber added lab_session_id=%s total=%d",
        lab_session_id,
        len(_queues.get(lab_session_id, set())),
    )
    try:
        while True:
            event = await queue.get()
            # 哨兵事件：None 表示正常结束订阅
            if event is None:
                return
            yield event
    except asyncio.CancelledError:
        logger.info("guidance SSE subscriber cancelled lab_session_id=%s", lab_session_id)
        raise
    finally:
        async with _lock:
            subs = _queues.get(lab_session_id)
            if subs:
                subs.discard(queue)
                if not subs:
                    _queues.pop(lab_session_id, None)
        logger.info("guidance SSE subscriber removed lab_session_id=%s", lab_session_id)


async def publish(lab_session_id: str, event: dict[str, Any]) -> int:
    """向指定 lab_session_id 的所有订阅者推送事件。

    Returns: 成功推送的订阅者数（队列满时丢弃，避免一个慢订阅者拖累其他）。
    """
    async with _lock:
        subs = list(_queues.get(lab_session_id, set()))
    if not subs:
        return 0
    delivered = 0
    for queue in subs:
        try:
            # 非阻塞 put，队列满则丢弃（避免一个慢订阅者拖累其他）
            queue.put_nowait(event)
            delivered += 1
        except asyncio.QueueFull:
            logger.warning(
                "guidance SSE queue full lab_session_id=%s dropping event",
                lab_session_id,
            )
    return delivered


async def close_all(lab_session_id: str) -> None:
    """向指定 lab_session_id 的所有订阅者发送结束哨兵并清理。"""
    async with _lock:
        subs = _queues.pop(lab_session_id, set())
    for queue in subs:
        try:
            queue.put_nowait(None)
        except asyncio.QueueFull:
            pass


def subscriber_count(lab_session_id: str) -> int:
    """调试用：返回当前订阅者数。"""
    return len(_queues.get(lab_session_id, set()))
