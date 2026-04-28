import uuid

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repository import UserRoleRepository
from app.db.session import get_db


class RequestUser:
    def __init__(self, user_id: uuid.UUID, role_name: str | None):
        self.user_id = user_id
        self.role_name = role_name 

    @property
    def is_moderator(self) -> bool:
        return self.role_name == "moderator"


async def get_current_user(
    x_user_id: str = Header(..., alias="x-user-id"),
    db: AsyncSession = Depends(get_db),
) -> RequestUser:
    try:
        user_id = uuid.UUID(x_user_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid x-user-id header")

    user_role = await UserRoleRepository(db).get_by_user_id(user_id)
    role_name = user_role.role.name if user_role else None
    return RequestUser(user_id=user_id, role_name=role_name)


async def require_moderator(
    current_user: RequestUser = Depends(get_current_user),
) -> RequestUser:
    if not current_user.is_moderator:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Moderator role required")
    return current_user
