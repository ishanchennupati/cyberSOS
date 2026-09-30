import uuid
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from tests.test_migrations import upgrade


def test_R2_phase0_to_phase1_preserves_legacy_data_and_locks_case(tmp_path, monkeypatch):
    database = tmp_path / "phase0.sqlite"
    upgrade(database, tmp_path / "evidence", monkeypatch, revision="20260930_evidence_contract")
    engine = create_engine("sqlite:///" + database.as_posix())
    ident = uuid.uuid4()
    with engine.begin() as connection:
        connection.execute(text("INSERT INTO incidents (id,incident_type,payment_method,urgency,status,amount,description,recovery_window) VALUES (:id,'financial_fraud','upi','high','action_required',2500,'Synthetic legacy','likely_expired')"), {"id": ident.hex})
    engine.dispose()
    upgrade(database, tmp_path / "evidence", monkeypatch)
    from app.models.incident import Incident
    from app.models.response import ResponsePlanRecord, ActionCompletionRecord
    engine = create_engine("sqlite:///" + database.as_posix())
    with Session(engine) as db:
        incident = db.get(Incident, ident)
        assert incident.amount == 2500 and incident.description == "Synthetic legacy"
        assert incident.recovery_window == "likely_expired"
        assert incident.playbook_id == "legacy_unversioned"
        assert incident.case_secret_hash is None
        assert incident.facts is None  # Do not invent authorization/provenance.
        assert ResponsePlanRecord.__tablename__ == "response_plans"
        assert ActionCompletionRecord.__tablename__ == "action_completions"
    engine.dispose()
