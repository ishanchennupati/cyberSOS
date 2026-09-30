"""A session-private, migrated database and evidence store; no repository data."""
import os
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest

_TEMP = tempfile.TemporaryDirectory(prefix="cybersos-tests-")
ROOT = Path(_TEMP.name)
DATABASE = ROOT / "session.sqlite"
STORAGE = ROOT / "evidence"
os.environ.update({
    "DATABASE_URL": "sqlite:///" + DATABASE.as_posix(),
    "CORS_ORIGINS": "http://testserver",
    "EVIDENCE_STORAGE_DIR": str(STORAGE),
    "LOCAL_STORAGE_ROOT": str(STORAGE),
    "EXTRACTION_PROVIDER": "heuristic",
    "SUMMARY_PROVIDER": "template",
    "SUPABASE_URL": "",
    "SUPABASE_SERVICE_ROLE_KEY": "",
    "ANTHROPIC_API_KEY": "",
    "ANTHROPIC_MODEL": "",
})

from app.core.config import get_settings
get_settings.cache_clear()
from app.db.base import Base
from app.db.session import SessionLocal, engine, get_db
from app.main import app
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from alembic import command
from alembic.config import Config


@pytest.fixture(scope="session", autouse=True)
def _migrated_database():
    backend = Path(__file__).resolve().parents[1]
    config = Config(str(backend / "alembic.ini"))
    config.set_main_option("script_location", str(backend / "alembic"))
    with engine.begin() as connection:
        config.attributes["connection"] = connection
        command.upgrade(config, "head")
    yield
    engine.dispose()
    _TEMP.cleanup()


@pytest.fixture(autouse=True)
def _fresh_data(_migrated_database, monkeypatch, tmp_path):
    monkeypatch.setenv("LOCAL_STORAGE_ROOT", str(tmp_path / "evidence"))
    monkeypatch.setenv("EVIDENCE_STORAGE_DIR", str(tmp_path / "evidence"))
    get_settings.cache_clear()
    with engine.begin() as connection:
        for table in reversed(Base.metadata.sorted_tables):
            connection.execute(table.delete())
    yield
    get_settings.cache_clear()


@pytest.fixture
def db() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        yield session


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    def _override_db():
        with SessionLocal() as session:
            yield session
    app.dependency_overrides[get_db] = _override_db
    try:
        with TestClient(app, base_url="https://testserver") as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
