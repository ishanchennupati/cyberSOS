from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.core.config import get_settings
from app.db.base import Base
from app.db.session import engine

# Import models so they're registered on Base.metadata before create_all runs.
from app.models import incident  # noqa: F401

settings = get_settings()

app = FastAPI(
    title="CyberSOS API",
    description="Citizen-support layer for responding to cyber/financial fraud incidents.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    # Phase 0: create tables directly. Once the schema stabilizes, replace
    # this with Alembic migrations (scaffolding for that is already in
    # requirements.txt).
    Base.metadata.create_all(bind=engine)


@app.get("/health", tags=["health"])
def health() -> dict:
    return {"status": "ok", "service": settings.SERVICE_NAME}


app.include_router(api_router, prefix=settings.API_V1_PREFIX)
