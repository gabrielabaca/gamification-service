import uuid
from datetime import datetime, timezone

from redis.asyncio import Redis

from app.clients.redis_client import get_redis

PLAYER_KEY_PREFIX = "demo:players:"
PRESENCE_KEY_PREFIX = "demo:presence:"
LEADERBOARD_KEY = "demo:leaderboard:coins"
PRESENCE_TTL_SECONDS = 45


async def register_player(
    user_id: uuid.UUID,
    display_name: str,
    points: int,
    coins: int,
) -> None:
    redis = await get_redis()
    await _save_player(redis, user_id, display_name, points, coins)
    await mark_player_seen(user_id)


async def mark_player_seen(user_id: uuid.UUID) -> None:
    redis = await get_redis()
    await redis.setex(f"{PRESENCE_KEY_PREFIX}{user_id}", PRESENCE_TTL_SECONDS, "1")


async def update_registered_player_balance(
    user_id: uuid.UUID,
    points: int,
    coins: int,
) -> None:
    redis = await get_redis()
    player_key = f"{PLAYER_KEY_PREFIX}{user_id}"

    if not await redis.exists(player_key):
        return

    await redis.hset(
        player_key,
        mapping={
            "points": points,
            "coins": coins,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    await redis.zadd(LEADERBOARD_KEY, {str(user_id): coins})


async def get_coin_leaderboard(limit: int = 10) -> list[dict]:
    redis = await get_redis()
    rows = await redis.zrevrange(LEADERBOARD_KEY, 0, max(0, limit - 1), withscores=True)
    leaderboard = []

    for position, (user_id, score) in enumerate(rows, start=1):
        player = await redis.hgetall(f"{PLAYER_KEY_PREFIX}{user_id}")
        if not player:
            await redis.zrem(LEADERBOARD_KEY, user_id)
            continue

        leaderboard.append({
            "position": position,
            "user_id": user_id,
            "display_name": player.get("display_name", "Jugador"),
            "points": int(player.get("points", 0)),
            "coins": int(score),
            "connected": bool(await redis.exists(f"{PRESENCE_KEY_PREFIX}{user_id}")),
        })

    return leaderboard


async def _save_player(
    redis: Redis,
    user_id: uuid.UUID,
    display_name: str,
    points: int,
    coins: int,
) -> None:
    await redis.hset(
        f"{PLAYER_KEY_PREFIX}{user_id}",
        mapping={
            "display_name": display_name,
            "points": points,
            "coins": coins,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    await redis.zadd(LEADERBOARD_KEY, {str(user_id): coins})
