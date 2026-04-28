import asyncio
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.clients.redis_client import get_redis
from app.services.notifier import CHANNEL_PREFIX

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/{user_id}")
async def websocket_balance(websocket: WebSocket, user_id: str):
    await websocket.accept()
    redis = await get_redis()
    pubsub = redis.pubsub()
    channel = f"{CHANNEL_PREFIX}{user_id}"

    await pubsub.subscribe(channel)
    logger.info("WebSocket connected: user=%s channel=%s", user_id, channel)

    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                await websocket.send_text(message["data"])
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected: user=%s", user_id)
    except asyncio.CancelledError:
        pass
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.aclose()
