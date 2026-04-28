import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class AssignPointsRequest(BaseModel):
    amount: int = Field(gt=0)


class DeductPointsRequest(BaseModel):
    amount: int = Field(gt=0)


class AssignCoinsRequest(BaseModel):
    amount: int = Field(gt=0)


class DeductCoinsRequest(BaseModel):
    amount: int = Field(gt=0)


class ConvertPointsRequest(BaseModel):
    points: int = Field(gt=0)


class UserBalanceResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    points: int
    coins: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RoleResponse(BaseModel):
    id: uuid.UUID
    name: str

    model_config = {"from_attributes": True}


class UserRoleResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    role: RoleResponse
    assigned_by: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AssignRoleRequest(BaseModel):
    role_name: str = Field(pattern="^(player|moderator)$")
