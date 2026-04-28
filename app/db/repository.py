import uuid
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.db.models import AuditLog, CoinConfig, Role, UserBalance, UserRole


class RoleRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self) -> Sequence[Role]:
        result = await self.db.execute(select(Role))
        return result.scalars().all()

    async def get_by_name(self, name: str) -> Role | None:
        result = await self.db.execute(select(Role).where(Role.name == name))
        return result.scalar_one_or_none()

    async def get_by_id(self, role_id: uuid.UUID) -> Role | None:
        result = await self.db.execute(select(Role).where(Role.id == role_id))
        return result.scalar_one_or_none()


class UserRoleRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_user_id(self, user_id: uuid.UUID) -> UserRole | None:
        result = await self.db.execute(
            select(UserRole)
            .options(joinedload(UserRole.role))
            .where(UserRole.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def assign(self, user_id: uuid.UUID, role_id: uuid.UUID, assigned_by: uuid.UUID) -> UserRole:
        user_role = await self.get_by_user_id(user_id)
        if user_role:
            user_role.role_id = role_id
            user_role.assigned_by = assigned_by
            self.db.add(user_role)
        else:
            user_role = UserRole(user_id=user_id, role_id=role_id, assigned_by=assigned_by)
            self.db.add(user_role)
        await self.db.flush()
        await self.db.refresh(user_role)
        result = await self.db.execute(
            select(UserRole)
            .options(joinedload(UserRole.role))
            .where(UserRole.user_id == user_id)
        )
        return result.scalar_one()


class UserBalanceRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_user_id(self, user_id: uuid.UUID) -> UserBalance | None:
        result = await self.db.execute(select(UserBalance).where(UserBalance.user_id == user_id))
        return result.scalar_one_or_none()

    async def get_or_create(self, user_id: uuid.UUID) -> UserBalance:
        balance = await self.get_by_user_id(user_id)
        if not balance:
            balance = UserBalance(user_id=user_id)
            self.db.add(balance)
            await self.db.flush()
        return balance

    async def save(self, balance: UserBalance) -> UserBalance:
        self.db.add(balance)
        await self.db.flush()
        return balance


class CoinConfigRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self) -> Sequence[CoinConfig]:
        result = await self.db.execute(select(CoinConfig))
        return result.scalars().all()

    async def get_by_id(self, config_id: uuid.UUID) -> CoinConfig | None:
        result = await self.db.execute(select(CoinConfig).where(CoinConfig.id == config_id))
        return result.scalar_one_or_none()

    async def get_active(self) -> CoinConfig | None:
        result = await self.db.execute(select(CoinConfig).where(CoinConfig.is_active == True))
        return result.scalar_one_or_none()

    async def create(self, coin_config: CoinConfig) -> CoinConfig:
        self.db.add(coin_config)
        await self.db.flush()
        return coin_config

    async def save(self, coin_config: CoinConfig) -> CoinConfig:
        self.db.add(coin_config)
        await self.db.flush()
        return coin_config

    async def delete(self, coin_config: CoinConfig) -> None:
        await self.db.delete(coin_config)
        await self.db.flush()


class AuditLogRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, log: AuditLog) -> AuditLog:
        self.db.add(log)
        await self.db.flush()
        return log

    async def get_by_user_balance_id(self, user_balance_id: uuid.UUID) -> Sequence[AuditLog]:
        result = await self.db.execute(
            select(AuditLog)
            .where(AuditLog.user_balance_id == user_balance_id)
            .order_by(AuditLog.created_at.desc())
        )
        return result.scalars().all()
