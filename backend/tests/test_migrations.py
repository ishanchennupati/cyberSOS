import hashlib
import sqlite3
import uuid
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, inspect, text

BACKEND = Path(__file__).resolve().parents[1]


def upgrade(database, root, monkeypatch, revision="head"):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///" + database.as_posix())
    monkeypatch.setenv("EVIDENCE_STORAGE_DIR", str(root))
    monkeypatch.setenv("LOCAL_STORAGE_ROOT", str(root))
    from app.core.config import get_settings
    get_settings.cache_clear()
    config = Config(str(BACKEND / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND / "alembic"))
    command.upgrade(config, revision)


def test_R3_R4_fresh_migrations_match_canonical_schema(tmp_path, monkeypatch):
    database = tmp_path / "fresh.sqlite"
    upgrade(database, tmp_path / "files", monkeypatch)
    from app.db.base import Base
    from app.models import evidence, incident
    engine = create_engine("sqlite:///" + database.as_posix())
    with engine.connect() as connection:
        assert set(inspect(connection).get_table_names()) == {
            "alembic_version", "incidents", "evidence", "suspect_identifiers", "timeline_events",
            "response_plans", "action_completions",
            "conversation_states", "conversation_turns", "conversation_attachments",
            "evidence_attempts", "evidence_reviews",
        }
        differences = compare_metadata(MigrationContext.configure(connection), Base.metadata)
        assert differences == [], differences
    engine.dispose()


@pytest.mark.parametrize("stamp", [None, "20260824_phase2", "20260824_urgency_metadata"])
def test_R3_R4_current_schema_upgrade_preserves_incidents_and_evidence(tmp_path, monkeypatch, stamp):
    database = tmp_path / "legacy.sqlite"
    storage = tmp_path / "files"
    storage.mkdir()
    (storage / "synthetic.txt").write_bytes(b"original synthetic bytes")
    incident_id, evidence_id = uuid.uuid4(), uuid.uuid4()
    with sqlite3.connect(database) as connection:
        connection.executescript((BACKEND / "tests/fixtures/legacy_schema.sql").read_text())
        connection.execute(
            "INSERT INTO incidents (id,incident_type,payment_method,amount,transaction_id,urgency,status,details) VALUES (?,?,?,?,?,?,?,?)",
            (incident_id.hex, "financial_fraud", "upi", 2500, "SYNTH-UTR", "high", "action_required", '{"synthetic":true}'),
        )
        connection.execute(
            "INSERT INTO evidence (id,incident_id,original_filename,stored_filename,content_type,size_bytes) VALUES (?,?,?,?,?,?)",
            (evidence_id.hex, incident_id.hex, "original.txt", "synthetic.txt", "text/plain", 24),
        )
        if stamp:
            connection.execute("CREATE TABLE alembic_version (version_num VARCHAR(32) PRIMARY KEY)")
            connection.execute("INSERT INTO alembic_version VALUES (?)", (stamp,))
    upgrade(database, storage, monkeypatch)
    from sqlalchemy.orm import Session
    from app.models.incident import Incident
    from app.models.evidence import Evidence
    engine = create_engine("sqlite:///" + database.as_posix())
    with Session(engine) as session:
        saved = session.get(Incident, incident_id)
        assert saved.amount == 2500
        assert saved.transaction_id == "SYNTH-UTR"
        assert saved.details == {"synthetic": True}
        assert saved.status.value == "action_required"
        proof = session.get(Evidence, evidence_id)
        assert proof.original_filename == "original.txt"
        assert proof.storage_path == "synthetic.txt"
        assert proof.mime_type == "text/plain"
        assert proof.file_size == 24
        assert proof.sha256_hash == hashlib.sha256(b"original synthetic bytes").hexdigest()
        assert proof.uploaded_at == proof.created_at == proof.updated_at
        assert proof.verification_status.value == "unverified"
        assert proof.extracted_data is None
        from app.services.storage_service import LocalDiskStorageBackend
        assert LocalDiskStorageBackend().download(proof.storage_path) == b"original synthetic bytes"
    engine.dispose()


def test_R4_missing_legacy_bytes_leave_hash_unknown(tmp_path, monkeypatch):
    database = tmp_path / "missing.sqlite"
    with sqlite3.connect(database) as connection:
        connection.executescript((BACKEND / "tests/fixtures/legacy_schema.sql").read_text())
        connection.execute("INSERT INTO incidents (id,incident_type,payment_method,urgency,status) VALUES ('" + "1"*32 + "','financial_fraud','unknown','medium','draft')")
        connection.execute("INSERT INTO evidence (id,incident_id,original_filename,stored_filename,content_type,size_bytes) VALUES ('" + "2"*32 + "','" + "1"*32 + "','original.png','missing.png','image/png',42)")
    upgrade(database, tmp_path / "unavailable", monkeypatch)
    engine = create_engine("sqlite:///" + database.as_posix())
    with engine.connect() as connection:
        row = connection.execute(text("SELECT sha256_hash,original_filename,storage_path,file_size FROM evidence")).one()
        assert row == (None, "original.png", "missing.png", 42)
    engine.dispose()
