from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.clients.redis_client import close_redis
from app.core.config import settings
from app.db.session import AsyncSessionLocal, Base, engine

app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        from app.db.models import Role
        for name in ("player", "moderator"):
            exists = await session.execute(select(Role).where(Role.name == name))
            if not exists.scalar_one_or_none():
                session.add(Role(name=name))
        await session.commit()


@app.on_event("shutdown")
async def on_shutdown():
    await close_redis()


@app.get("/")
async def root():
    return {"message": settings.APP_NAME, "version": settings.APP_VERSION, "docs": "/docs"}


@app.get("/health")
async def health():
    return {"status": "ok", "service": "gamification"}
