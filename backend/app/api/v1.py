from fastapi import APIRouter

from app.api.routes import health, incidents

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(incidents.router)
