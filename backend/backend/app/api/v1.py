from fastapi import APIRouter

from app.api.routes import evidence, health, incidents, suspects, timeline

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(incidents.router)
api_router.include_router(evidence.router)
api_router.include_router(suspects.router)
api_router.include_router(timeline.router)
