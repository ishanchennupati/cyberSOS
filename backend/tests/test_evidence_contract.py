"""0B regression contracts. Each R name identifies the requirement it protects."""
import hashlib
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
PNG = b"\x89PNG\r\n\x1a\n" + b"synthetic screenshot"


def incident(client):
    response = client.post("/api/v1/incidents", json={"incident_type": "financial_fraud"})
    assert response.status_code == 201, response.text
    return response.json()["id"]


def upload(client, incident_id, name="proof.txt", data=b"synthetic evidence", mime="text/plain"):
    response = client.post(
        f"/api/v1/incidents/{incident_id}/evidence",
        data={"evidence_type": "other_document", "description": "Synthetic proof"},
        files={"file": (name, data, mime)},
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_R1_models_register_without_duplicate_table():
    result = subprocess.run(
        [sys.executable, "-c", "from app.main import app; from app.models.evidence import Evidence; from app.models.incident import Incident; assert Evidence.__table__.metadata is Incident.__table__.metadata"],
        cwd=BACKEND, env={**os.environ, "DATABASE_URL": "sqlite:///:memory:"},
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr


def test_R2_every_frontend_operation_is_mounted_once(client):
    import re
    from app.main import app
    source = (ROOT / "frontend/lib/api.ts").read_text(encoding="utf-8")
    mounted = {(m.upper(), re.sub(r"\{[^}]+\}", "{}", p)) for p, ops in app.openapi()["paths"].items() for m in ops}
    calls = []
    for name, block in re.findall(r"export function (\w+)\((.*?)(?=\nexport function|\Z)", source, re.S):
        match = re.search(r'/(?:api/v1/|health)[^"' + chr(96) + r']*', block)
        if not match:
            continue
        path = re.sub(r"\$\{[^}]+\}", "{}", match.group())
        method = re.search(r'method: "(\w+)', block)
        calls.append((method.group(1) if method else "GET", path))
    assert len(calls) == 25
    assert set(calls) <= mounted, set(calls) - mounted
    routes = [(r.path, m) for r in app.routes if hasattr(r, "methods") for m in r.methods]
    assert len(routes) == len(set(routes)), "Duplicate registered method/path"


def test_R3_startup_performs_no_schema_ddl(client, monkeypatch):
    from app.db.base import Base
    def forbidden(*args, **kwargs):
        pytest.fail("Application startup called create_all")
    monkeypatch.setattr(Base.metadata, "create_all", forbidden)
    from app.main import app
    from fastapi.testclient import TestClient
    with TestClient(app) as check:
        assert check.get("/health").status_code == 200


def test_R1_R2_R7_evidence_roundtrip_and_delete(client):
    from app.core.config import get_settings
    item = upload(client, incident(client))
    assert item["mime_type"] == "text/plain"
    assert item["file_size"] == 18
    assert item["sha256_hash"] == hashlib.sha256(b"synthetic evidence").hexdigest()
    assert item["description"] == "Synthetic proof"
    assert item["evidence_type"] == "other_document"
    assert item["extraction_status"] == "pending"
    assert item["verification_status"] == "unverified"
    assert all(item[key] for key in ("created_at", "updated_at", "uploaded_at"))
    assert "storage_path" not in item
    path = f"/api/v1/evidence/{item['id']}"
    assert client.get(path).json()["sha256_hash"] == item["sha256_hash"]
    listed = client.get(f"/api/v1/incidents/{item['incident_id']}/evidence").json()
    assert len(listed) == 1
    file_response = client.get(item["preview_url"])
    assert file_response.status_code == 200
    assert file_response.content == b"synthetic evidence"
    assert file_response.headers["x-content-type-options"] == "nosniff"
    patched = client.patch(path, json={"description": "Reviewed description"})
    assert patched.json()["description"] == "Reviewed description"
    assert client.delete(path).status_code == 204
    assert client.get(path).status_code == 404
    assert client.get(f"/api/v1/incidents/{item['incident_id']}/evidence").json() == []
    assert not list(Path(get_settings().LOCAL_STORAGE_ROOT).rglob("proof.txt"))


@pytest.mark.parametrize("name,data,mime", [
    ("proof.exe", b"MZbad", "application/octet-stream"),
    ("proof.png", b"not png", "image/png"),
    ("proof.png", PNG, "application/pdf"),
    ("proof.txt", b"", "text/plain"),
])
def test_R2_upload_rejects_invalid_files(client, name, data, mime):
    ident = incident(client)
    response = client.post(f"/api/v1/incidents/{ident}/evidence", files={"file": (name, data, mime)})
    assert response.status_code == 422
    assert client.get(f"/api/v1/incidents/{ident}/evidence").json() == []


def test_R6_upload_rejects_size_limit(client, monkeypatch):
    from app.core.config import get_settings
    monkeypatch.setattr(get_settings(), "MAX_EVIDENCE_FILE_SIZE_MB", 1)
    ident = incident(client)
    response = client.post(f"/api/v1/incidents/{ident}/evidence", files={"file": ("large.txt", b"x" * (1024 * 1024 + 1), "text/plain")})
    assert response.status_code in (413, 422)
    assert client.get(f"/api/v1/incidents/{ident}/evidence").json() == []


def test_R2_R6_extraction_fallback_and_manual_verification(client, monkeypatch):
    from app.core.config import get_settings
    monkeypatch.setattr(get_settings(), "EXTRACTION_PROVIDER", "anthropic")
    monkeypatch.setattr(get_settings(), "ANTHROPIC_API_KEY", None)
    item = upload(client, incident(client), "proof.png", PNG, "image/png")
    path = f"/api/v1/evidence/{item['id']}"
    extracted = client.post(path + "/extract")
    assert extracted.status_code == 200, extracted.text
    assert extracted.json()["extraction_status"] == "failed"
    assert extracted.json()["extracted_data"] is None
    assert extracted.json()["verification_status"] == "unverified"
    verified = client.post(path + "/verify", json={"extracted_data": {"transaction_id": "SYNTH12345"}})
    assert verified.status_code == 200, verified.text
    assert verified.json()["evidence"]["verification_status"] == "verified"
    assert client.get(path).json()["extracted_data"]["transaction_id"] == "SYNTH12345"


def test_R2_verification_conflict_does_not_change_incident(client):
    ident = incident(client)
    from datetime import timedelta
    triage = client.post(f"/api/v1/incidents/{ident}/triage", json={
        "incident_type": "financial_fraud", "occurred_at": datetime.now(timezone.utc).isoformat(),
        "amount": 2500, "payment_method": "upi",
    })
    assert triage.status_code == 200
    item = upload(client, ident)
    response = client.post(f"/api/v1/evidence/{item['id']}/verify", json={"extracted_data": {"amount": 3000}})
    assert response.status_code == 200, response.text
    assert response.json()["evidence"]["verification_status"] == "needs_review"
    assert client.get(f"/api/v1/incidents/{ident}").json()["amount"] == 2500


def test_R2_R7_suspect_and_timeline_crud(client):
    ident = incident(client)
    evidence = upload(client, ident)
    suspect = client.post(f"/api/v1/incidents/{ident}/suspects", json={"type": "phone", "value": "9999900000", "source_evidence_id": evidence["id"]})
    assert suspect.status_code == 201, suspect.text
    suspect = suspect.json()
    assert suspect["verified"] is False
    path = f"/api/v1/suspects/{suspect['id']}"
    assert client.patch(path, json={"value": "9999900001", "verified": True}).json()["verified"] is True
    assert client.get(f"/api/v1/incidents/{ident}/suspects").json()[0]["value"] == "9999900001"
    event = client.post(f"/api/v1/incidents/{ident}/timeline", json={
        "event_time": "2026-09-30T12:00:00Z", "description": "Synthetic call",
        "source_evidence_id": evidence["id"],
    })
    assert event.status_code == 201, event.text
    event = event.json()
    event_path = f"/api/v1/timeline/{event['id']}"
    assert client.patch(event_path, json={"description": "Corrected call"}).json()["description"] == "Corrected call"
    assert any(e["id"] == event["id"] for e in client.get(f"/api/v1/incidents/{ident}/timeline").json())
    assert client.delete(f"/api/v1/evidence/{evidence['id']}").status_code == 204
    assert client.get(f"/api/v1/incidents/{ident}/suspects").json()[0]["source_evidence_id"] is None
    assert client.delete(path).status_code == 204
    assert client.patch(path, json={"value": "gone"}).status_code == 404
    assert client.delete(event_path).status_code == 204
    assert client.patch(event_path, json={"description": "gone"}).status_code == 404


@pytest.mark.parametrize("resource,payload", [
    ("suspects", {"type": "phone", "value": "9999900000"}),
    ("timeline", {"event_time": "2026-09-30T12:00:00Z", "description": "Synthetic"}),
])
def test_R2_source_evidence_is_incident_scoped(client, resource, payload):
    source = upload(client, incident(client))
    other = incident(client)
    response = client.post(f"/api/v1/incidents/{other}/{resource}", json={**payload, "source_evidence_id": source["id"]})
    assert response.status_code == 422


def test_R2_missing_incident_resources_are_not_success(client):
    ident = "00000000-0000-0000-0000-000000000000"
    for suffix in ("evidence", "suspects", "timeline", "evidence-readiness"):
        assert client.get(f"/api/v1/incidents/{ident}/{suffix}").status_code == 404
    assert client.patch(f"/api/v1/incidents/{ident}/description", json={"description": "Synthetic"}).status_code == 404
    assert client.post(f"/api/v1/incidents/{ident}/generate-summary").status_code == 404


def test_R2_R7_description_readiness_and_template_summary(client):
    ident = incident(client)
    response = client.patch(f"/api/v1/incidents/{ident}/description", json={"description": "A synthetic suspicious payment request."})
    assert response.status_code == 200, response.text
    assert client.get(f"/api/v1/incidents/{ident}").json()["description"] == "A synthetic suspicious payment request."
    ready = client.get(f"/api/v1/incidents/{ident}/evidence-readiness")
    assert ready.status_code == 200, ready.text
    assert next(i for i in ready.json()["items"] if i["id"] == "description")["met"] is True
    summary = client.post(f"/api/v1/incidents/{ident}/generate-summary")
    assert summary.status_code == 200, summary.text
    assert summary.json()["provider"] == "template"
    assert "A synthetic suspicious payment request." in summary.json()["draft"]
    assert client.patch(f"/api/v1/incidents/{ident}/description", json={"description": "x" * 4001}).status_code == 422


@pytest.mark.parametrize("name,data,mime", [
    ("proof.txt", b"UTR: SYNTHNEW123 INR 2500", "text/plain"),
    ("proof.png", PNG, "image/png"),
])
def test_R1_R7_reextraction_preserves_verified_manual_corrections(client, name, data, mime):
    item = upload(client, incident(client), name, data, mime)
    path = f"/api/v1/evidence/{item['id']}"
    confirmed = client.post(path + "/verify", json={"extracted_data": {"transaction_id": "SYNTH-CORRECTED"}})
    assert confirmed.status_code == 200
    before = client.get(path).json()
    response = client.post(path + "/extract")
    assert response.status_code == 409
    after = client.get(path).json()
    assert after["extracted_data"] == before["extracted_data"]
    assert after["extraction_status"] == before["extraction_status"]
    assert after["verification_status"] == "verified"

