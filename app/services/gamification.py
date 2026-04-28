import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models import AuditLog, CoinConfig, UserBalance
from app.services.notifier import notify_balance_update
from app.db.repository import (
    AuditLogRepository,
    CoinConfigRepository,
    RoleRepository,
    UserBalanceRepository,
    UserRoleRepository,
)
from app.schemas.coins import CoinConfigCreate, CoinConfigUpdate


class GamificationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.balances = UserBalanceRepository(db)
        self.coins = CoinConfigRepository(db)
        self.audit = AuditLogRepository(db)
        self.roles = RoleRepository(db)
        self.user_roles = UserRoleRepository(db)

    async def get_balance(self, user_id: uuid.UUID) -> UserBalance:
        return await self.balances.get_or_create(user_id)

    async def assign_points(self, actor_id: uuid.UUID, user_id: uuid.UUID, amount: int) -> UserBalance:
        balance = await self.balances.get_or_create(user_id)
        target_role = await self._get_role_name(user_id)
        balance.points += amount
        balance.updated_at = datetime.now(timezone.utc)
        await self.balances.save(balance)
        await self._log(actor_id, balance, "assign_points", points_delta=amount, target_role=target_role)
        await notify_balance_update(user_id, balance.points, balance.coins, "assign_points")
        return balance

    async def assign_coins(self, actor_id: uuid.UUID, user_id: uuid.UUID, amount: int) -> UserBalance:
        balance = await self.balances.get_or_create(user_id)
        target_role = await self._get_role_name(user_id)
        balance.coins += amount
        balance.updated_at = datetime.now(timezone.utc)
        await self.balances.save(balance)
        await self._log(actor_id, balance, "assign_coins", coins_delta=amount, target_role=target_role)
        await notify_balance_update(user_id, balance.points, balance.coins, "assign_coins")
        return balance

    async def deduct_points(self, actor_id: uuid.UUID, user_id: uuid.UUID, amount: int) -> UserBalance:
        balance = await self.balances.get_or_create(user_id)
        target_role = await self._get_role_name(user_id)
        if balance.points < amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient points: has {balance.points}, needs {amount}",
            )
        balance.points -= amount
        balance.updated_at = datetime.now(timezone.utc)
        await self.balances.save(balance)
        await self._log(actor_id, balance, "deduct_points", points_delta=-amount, target_role=target_role)
        await notify_balance_update(user_id, balance.points, balance.coins, "deduct_points")
        return balance

    async def deduct_coins(self, actor_id: uuid.UUID, user_id: uuid.UUID, amount: int) -> UserBalance:
        balance = await self.balances.get_or_create(user_id)
        target_role = await self._get_role_name(user_id)
        if balance.coins < amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient coins: has {balance.coins}, needs {amount}",
            )
        balance.coins -= amount
        balance.updated_at = datetime.now(timezone.utc)
        await self.balances.save(balance)
        await self._log(actor_id, balance, "deduct_coins", coins_delta=-amount, target_role=target_role)
        await notify_balance_update(user_id, balance.points, balance.coins, "deduct_coins")
        return balance

    async def convert_points_to_coins(self, actor_id: uuid.UUID, user_id: uuid.UUID, points: int) -> UserBalance:
        balance = await self.balances.get_or_create(user_id)
        target_role = await self._get_role_name(user_id)

        if balance.points < points:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient points: has {balance.points}, needs {points}",
            )

        coin_config = await self.coins.get_active()
        rate = coin_config.points_to_coins_rate if coin_config else settings.POINTS_TO_COINS_RATE

        coins_earned = points // rate
        if coins_earned == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Not enough points to earn at least 1 coin (rate: {rate} points = 1 coin)",
            )

        balance.points -= points
        balance.coins += coins_earned
        balance.updated_at = datetime.now(timezone.utc)
        await self.balances.save(balance)
        await self._log(
            actor_id, balance, "convert_points_to_coins",
            detail=f"rate={rate}",
            points_delta=-points,
            coins_delta=coins_earned,
            target_role=target_role,
        )
        await notify_balance_update(user_id, balance.points, balance.coins, "convert_points_to_coins")
        return balance

    async def list_roles(self):
        return await self.roles.get_all()

    async def assign_role(self, actor_id: uuid.UUID, user_id: uuid.UUID, role_name: str):
        role = await self.roles.get_by_name(role_name)
        if not role:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Role '{role_name}' not found")
        old_role = await self._get_role_name(user_id)
        user_role = await self.user_roles.assign(user_id, role.id, actor_id)
        balance = await self.balances.get_or_create(user_id)
        await self._log(actor_id, balance, "set_role", detail=f"{old_role} -> {role_name}", target_role=old_role)
        return user_role

    async def get_user_role(self, user_id: uuid.UUID):
        user_role = await self.user_roles.get_by_user_id(user_id)
        if not user_role:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User has no role assigned")
        return user_role

    async def list_coin_configs(self):
        return await self.coins.get_all()

    async def create_coin_config(self, data: CoinConfigCreate) -> CoinConfig:
        return await self.coins.create(CoinConfig(**data.model_dump()))

    async def get_coin_config(self, config_id: uuid.UUID) -> CoinConfig:
        config = await self.coins.get_by_id(config_id)
        if not config:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CoinConfig not found")
        return config

    async def update_coin_config(self, config_id: uuid.UUID, data: CoinConfigUpdate) -> CoinConfig:
        config = await self.get_coin_config(config_id)
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(config, field, value)
        config.updated_at = datetime.now(timezone.utc)
        return await self.coins.save(config)

    async def delete_coin_config(self, config_id: uuid.UUID) -> None:
        await self.coins.delete(await self.get_coin_config(config_id))

    async def get_audit_logs(self, user_id: uuid.UUID):
        balance = await self.balances.get_by_user_id(user_id)
        if not balance:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return await self.audit.get_by_user_balance_id(balance.id)

    async def _get_role_name(self, user_id: uuid.UUID) -> str | None:
        user_role = await self.user_roles.get_by_user_id(user_id)
        return user_role.role.name if user_role else None

    async def _log(
        self,
        actor_id: uuid.UUID,
        balance: UserBalance,
        action: str,
        detail: str | None = None,
        points_delta: int | None = None,
        coins_delta: int | None = None,
        target_role: str | None = None,
    ) -> None:
        await self.audit.create(AuditLog(
            user_balance_id=balance.id,
            actor_id=actor_id,
            action=action,
            target_role=target_role,
            detail=detail,
            points_delta=points_delta,
            coins_delta=coins_delta,
        ))
