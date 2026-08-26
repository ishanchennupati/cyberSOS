import os

os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["CORS_ORIGINS"] = "http://testserver"

from app.core.config import get_settings

get_settings.cache_clear()

from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.schema import ensure_schema
from app.db.session import SessionLocal, engine, get_db
from app.main import app
from app.models.incident import Incident  # noqa: F401 — register metadata


@pytest.fixture(autouse=True)
def _fresh_schema() -> Generator[None, None, None]:
    from app.db.base import Base

    Base.metadata.drop_all(bind=engine)
    ensure_schema(engine)
    yield
    Base.metadata.drop_all(bind=engine)
    db_path = Path("test.db")
    if db_path.exists():
        try:
            db_path.unlink()
        except OSError:
            pass


@pytest.fixture
def db() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    def _override_db() -> Generator[Session, None, None]:
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = _override_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
