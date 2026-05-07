import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import select

from app.db.models import Role
from app.db.session import AsyncSessionLocal, Base, engine


async def create_tables() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def seed_base_roles() -> None:
    async with AsyncSessionLocal() as session:
        for name in ("player", "moderator"):
            exists = await session.execute(select(Role).where(Role.name == name))
            if not exists.scalar_one_or_none():
                session.add(Role(name=name))
        await session.commit()


async def main() -> None:
    await create_tables()
    await seed_base_roles()
    await engine.dispose()
    print("Tables created successfully.")


if __name__ == "__main__":
    asyncio.run(main())
