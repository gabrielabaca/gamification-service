import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import RequestUser, get_current_user, require_moderator
from app.db.session import get_db
from app.schemas.coins import AuditLogResponse
from app.schemas.points import (
    AssignCoinsRequest,
    AssignPointsRequest,
    ConvertPointsRequest,
    DeductCoinsRequest,
    DeductPointsRequest,
    UserBalanceResponse,
)
from app.services.gamification import GamificationService

router = APIRouter(prefix="/users", tags=["users"])

SYSTEM_ACTOR_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")

def get_service(db: AsyncSession = Depends(get_db)) -> GamificationService:
    return GamificationService(db)


@router.get("/me/balance", response_model=UserBalanceResponse)
async def get_my_balance(
    actor: RequestUser = Depends(get_current_user),
    svc: GamificationService = Depends(get_service),
):
    return await svc.get_balance(actor.user_id)


@router.get("/{user_id}/balance", response_model=UserBalanceResponse)
async def get_user_balance(
    user_id: uuid.UUID,
    actor: RequestUser = Depends(require_moderator),
    svc: GamificationService = Depends(get_service),
):
    return await svc.get_balance(user_id)


@router.post("/{user_id}/points", response_model=UserBalanceResponse)
async def assign_points(
    user_id: uuid.UUID,
    body: AssignPointsRequest,
    actor: RequestUser = Depends(require_moderator),
    svc: GamificationService = Depends(get_service),
):
    return await svc.assign_points(actor.user_id, user_id, body.amount)


@router.post("/{user_id}/coins", response_model=UserBalanceResponse)
async def assign_coins(
    user_id: uuid.UUID,
    body: AssignCoinsRequest,
    actor: RequestUser = Depends(require_moderator),
    svc: GamificationService = Depends(get_service),
):
    return await svc.assign_coins(actor.user_id, user_id, body.amount)


@router.post("/me/convert", response_model=UserBalanceResponse)
async def convert_my_points(
    body: ConvertPointsRequest,
    actor: RequestUser = Depends(get_current_user),
    svc: GamificationService = Depends(get_service),
):
    return await svc.convert_points_to_coins(actor.user_id, actor.user_id, body.points)


@router.get("/{user_id}/audit", response_model=list[AuditLogResponse])
async def get_audit_logs(
    user_id: uuid.UUID,
    _: RequestUser = Depends(require_moderator),
    svc: GamificationService = Depends(get_service),
):
    return await svc.get_audit_logs(user_id)


@router.post("/{user_id}/points/auto", response_model=UserBalanceResponse)
async def auto_assign_points(
    user_id: uuid.UUID,
    body: AssignPointsRequest,
    svc: GamificationService = Depends(get_service),
):
    return await svc.assign_points(SYSTEM_ACTOR_ID, user_id, body.amount)


@router.post("/{user_id}/points/deduct", response_model=UserBalanceResponse)
async def deduct_points(
    user_id: uuid.UUID,
    body: DeductPointsRequest,
    actor: RequestUser = Depends(require_moderator),
    svc: GamificationService = Depends(get_service),
):
    return await svc.deduct_points(actor.user_id, user_id, body.amount)


@router.post("/{user_id}/coins/deduct", response_model=UserBalanceResponse)
async def deduct_coins(
    user_id: uuid.UUID,
    body: DeductCoinsRequest,
    actor: RequestUser = Depends(require_moderator),
    svc: GamificationService = Depends(get_service),
):
    return await svc.deduct_coins(actor.user_id, user_id, body.amount)
