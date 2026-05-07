import uuid

from pydantic import BaseModel, Field

from app.schemas.points import UserBalanceResponse


class DemoPlayerConnectRequest(BaseModel):
    user_id: uuid.UUID
    display_name: str = Field(min_length=1, max_length=64)


class DemoPlayerHeartbeatRequest(BaseModel):
    user_id: uuid.UUID


class DemoLeaderboardEntry(BaseModel):
    position: int
    user_id: uuid.UUID
    display_name: str
    points: int
    coins: int
    connected: bool


class DemoPlayerConnectResponse(BaseModel):
    balance: UserBalanceResponse
    leaderboard: list[DemoLeaderboardEntry]
