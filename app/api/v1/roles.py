import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import RequestUser, require_moderator
from app.db.session import get_db
from app.schemas.points import AssignRoleRequest, RoleResponse, UserRoleResponse
from app.services.gamification import GamificationService

router = APIRouter(tags=["roles"])


def get_service(db: AsyncSession = Depends(get_db)) -> GamificationService:
    return GamificationService(db)


@router.get("/roles", response_model=list[RoleResponse])
async def list_roles(
    _: RequestUser = Depends(require_moderator),
    svc: GamificationService = Depends(get_service),
):
    return await svc.list_roles()


@router.post("/users/{user_id}/roles", response_model=UserRoleResponse)
async def assign_role(
    user_id: uuid.UUID,
    body: AssignRoleRequest,
    actor: RequestUser = Depends(require_moderator),
    svc: GamificationService = Depends(get_service),
):
    return await svc.assign_role(actor.user_id, user_id, body.role_name)


@router.get("/users/{user_id}/roles", response_model=UserRoleResponse)
async def get_user_role(
    user_id: uuid.UUID,
    _: RequestUser = Depends(require_moderator),
    svc: GamificationService = Depends(get_service),
):
    return await svc.get_user_role(user_id)
