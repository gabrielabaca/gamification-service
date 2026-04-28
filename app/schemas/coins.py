import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class CoinConfigCreate(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    symbol: str = Field(min_length=1, max_length=16)
    points_to_coins_rate: int = Field(gt=0, default=100)
    is_active: bool = True


class CoinConfigUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=64)
    symbol: str | None = Field(default=None, min_length=1, max_length=16)
    points_to_coins_rate: int | None = Field(default=None, gt=0)
    is_active: bool | None = None


class CoinConfigResponse(BaseModel):
    id: uuid.UUID
    name: str
    symbol: str
    points_to_coins_rate: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AuditLogResponse(BaseModel):
    id: uuid.UUID
    user_balance_id: uuid.UUID
    actor_id: uuid.UUID
    action: str
    target_role: str | None
    detail: str | None
    points_delta: int | None
    coins_delta: int | None
    created_at: datetime

    model_config = {"from_attributes": True}
