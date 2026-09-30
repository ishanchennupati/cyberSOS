from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.v1 import api_router
from app.core.config import get_settings

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


@app.get("/health", tags=["health"])
def health() -> dict:
    return {"status": "ok", "service": settings.SERVICE_NAME}


app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.exception_handler(ValueError)
async def domain_rejection(_request, exc):
    # Domain errors contain only controlled messages; never return raw file/text data.
    return JSONResponse(status_code=422, content={"detail": "Submitted information violates the case policy or domain contract"})


@app.exception_handler(RequestValidationError)
async def validation_rejection(_request, exc):
    # Pydantic's default 'input' payload can echo credentials accidentally submitted.
    return JSONResponse(status_code=422, content={"detail": [
        {"loc": error["loc"], "type": error["type"], "msg": error["msg"]}
        for error in exc.errors()
    ]})
