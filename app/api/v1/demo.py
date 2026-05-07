from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.demo import (
    DemoLeaderboardEntry,
    DemoPlayerConnectRequest,
    DemoPlayerConnectResponse,
    DemoPlayerHeartbeatRequest,
)
from app.services.demo_leaderboard import (
    get_coin_leaderboard,
    mark_player_seen,
    register_player,
)
from app.services.gamification import GamificationService

router = APIRouter(prefix="/demo", tags=["demo"])


def get_service(db: AsyncSession = Depends(get_db)) -> GamificationService:
    return GamificationService(db)


@router.post("/players/connect", response_model=DemoPlayerConnectResponse)
async def connect_demo_player(
    body: DemoPlayerConnectRequest,
    svc: GamificationService = Depends(get_service),
):
    balance = await svc.get_balance(body.user_id)
    await register_player(body.user_id, body.display_name, balance.points, balance.coins)
    return {
        "balance": balance,
        "leaderboard": await get_coin_leaderboard(),
    }


@router.post("/players/heartbeat", status_code=204)
async def heartbeat_demo_player(body: DemoPlayerHeartbeatRequest):
    await mark_player_seen(body.user_id)


@router.get("/leaderboard", response_model=list[DemoLeaderboardEntry])
async def list_demo_leaderboard(
    limit: int = Query(default=10, ge=1, le=50),
):
    return await get_coin_leaderboard(limit)
