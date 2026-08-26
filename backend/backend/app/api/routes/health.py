from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db

router = APIRouter(prefix="/health", tags=["health"])

settings = get_settings()


@router.get("/database")
def database_health(db: Session = Depends(get_db)) -> dict:
    """
    Confirms the API can reach PostgreSQL. Never returns connection
    details or credentials — only a boolean-style status.
    """
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception:
        return {"status": "error", "database": "unreachable"}
