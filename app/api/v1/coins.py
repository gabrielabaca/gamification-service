import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import RequestUser, require_moderator
from app.db.session import get_db
from app.schemas.coins import CoinConfigCreate, CoinConfigResponse, CoinConfigUpdate
from app.services.gamification import GamificationService

router = APIRouter(prefix="/coins", tags=["coins"])


def get_service(db: AsyncSession = Depends(get_db)) -> GamificationService:
    return GamificationService(db)


@router.get("", response_model=list[CoinConfigResponse])
async def list_coins(
    _: RequestUser = Depends(require_moderator),
    svc: GamificationService = Depends(get_service),
):
    return await svc.list_coin_configs()


@router.post("", response_model=CoinConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_coin(
    body: CoinConfigCreate,
    _: RequestUser = Depends(require_moderator),
    svc: GamificationService = Depends(get_service),
):
    return await svc.create_coin_config(body)


@router.get("/{coin_id}", response_model=CoinConfigResponse)
async def get_coin(
    coin_id: uuid.UUID,
    _: RequestUser = Depends(require_moderator),
    svc: GamificationService = Depends(get_service),
):
    return await svc.get_coin_config(coin_id)


@router.put("/{coin_id}", response_model=CoinConfigResponse)
async def update_coin(
    coin_id: uuid.UUID,
    body: CoinConfigUpdate,
    _: RequestUser = Depends(require_moderator),
    svc: GamificationService = Depends(get_service),
):
    return await svc.update_coin_config(coin_id, body)


@router.delete("/{coin_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_coin(
    coin_id: uuid.UUID,
    _: RequestUser = Depends(require_moderator),
    svc: GamificationService = Depends(get_service),
):
    await svc.delete_coin_config(coin_id)
