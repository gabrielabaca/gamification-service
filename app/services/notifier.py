import json
import logging
import uuid

from app.clients.redis_client import get_redis

logger = logging.getLogger(__name__)

CHANNEL_PREFIX = "gamification:user:"


async def notify_balance_update(
    user_id: uuid.UUID,
    points: int,
    coins: int,
    action: str,
) -> None:
    try:
        redis = await get_redis()
        channel = f"{CHANNEL_PREFIX}{user_id}"
        message = json.dumps({
            "user_id": str(user_id),
            "points": points,
            "coins": coins,
            "action": action,
        })
        await redis.publish(channel, message)
        logger.debug("Published balance update to %s: %s", channel, message)
    except Exception:
        logger.exception("Failed to publish balance update for user %s", user_id)
