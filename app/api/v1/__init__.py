from fastapi import APIRouter

from app.api.v1.coins import router as coins_router
from app.api.v1.demo import router as demo_router
from app.api.v1.points import router as points_router
from app.api.v1.roles import router as roles_router
from app.api.v1.websocket import router as ws_router

api_router = APIRouter()
api_router.include_router(points_router)
api_router.include_router(coins_router)
api_router.include_router(roles_router)
api_router.include_router(demo_router)
api_router.include_router(ws_router)
