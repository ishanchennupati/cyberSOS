from datetime import timedelta, datetime, timezone
import pytest


def create(client):
    return client.post("/api/v1/incidents", json={"incident_type": "financial_fraud"}).json()["id"]


def test_R2_R4_versioned_snapshots_corrections_and_early_actions(client):
    ident = create(client)
    early = client.get(f"/api/v1/incidents/{ident}/response-plan")
    assert early.status_code == 200
    assert early.json()["plan"]["facts"]["authorization"] == "unknown"
    first = client.put(f"/api/v1/incidents/{ident}/facts", json={"kind": "financial_scam_transfer"})
    assert first.status_code == 200, first.text
    revision = first.json()
    assert revision["plan"]["playbook_id"] == "financial_scam_transfer"
    assert revision["plan"]["facts"]["amount"] is None
    assert revision["plan"]["actions"][0]["id"] == "contact_bank_scam"
    assert client.get(f"/api/v1/incidents/{ident}").json()["authorization"] == "authorized"
    second = client.put(f"/api/v1/incidents/{ident}/facts", json={"kind": "unauthorized_financial_transaction", "account_compromised": True})
    assert second.status_code == 200
    history = client.get(f"/api/v1/incidents/{ident}/plans").json()
    assert len(history) == 3
    assert history[1] == revision  # Old facts, actions, source snapshots remain intact.
    assert client.get(f"/api/v1/incidents/{ident}/action-plan").json()["playbook_version"] == "1.0.0"


def test_R3_completion_is_only_user_self_report_and_scoped_to_plan(client):
    ident = create(client)
    revision = client.get(f"/api/v1/incidents/{ident}/response-plan").json()
    path = f"/api/v1/incidents/{ident}/plans/{revision['id']}/actions/{revision['plan']['actions'][0]['id']}/completion"
    response = client.post(path, json={"completed": True, "user_recorded_reference": "SYNTH-REF"})
    assert response.status_code == 200, response.text
    assert response.json()["meaning"] == "user_self_report"
    assert "official_status" not in response.json()
    assert client.post(path, json={"completed": True, "government_confirmed": True}).status_code == 422
    assert len(client.get(f"/api/v1/incidents/{ident}/completions").json()) == 1
    other = create(client)
    assert client.post(path.replace(ident, other), json={"completed": True}).status_code == 404
    client.cookies.clear()
    assert client.post(path, json={"completed": True}).status_code == 404


def test_R3_capability_is_hashed_hidden_and_expires(client, db):
    import uuid, hashlib
    from app.models.incident import Incident
    ident = create(client)
    secret = client.cookies.get("cybersos_case_" + ident)
    assert secret and len(secret) >= 43
    stored = db.get(Incident, uuid.UUID(ident))
    assert stored.case_secret_hash == hashlib.sha256(secret.encode()).hexdigest()
    data = client.get(f"/api/v1/incidents/{ident}").json()
    assert secret not in str(data) and "case_secret_hash" not in data
    stored.case_secret_expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    db.commit()
    assert client.get(f"/api/v1/incidents/{ident}").status_code == 404


@pytest.mark.parametrize("kind", ["credentials", "explicit_intimate_media", "child_sexual_abuse_material", "identity_document"])
def test_R3_evidence_policy_rejects_declared_prohibited_content(client, kind):
    ident = create(client)
    response = client.post(f"/api/v1/incidents/{ident}/evidence", data={"content_kind": kind}, files={"file": ("synthetic.txt", b"synthetic", "text/plain")})
    assert response.status_code == 422
    assert client.get(f"/api/v1/incidents/{ident}/evidence").json() == []


def test_R3_credentials_not_stored_or_echoed(client):
    ident = create(client)
    response = client.post(f"/api/v1/incidents/{ident}/evidence", files={"file": ("synthetic.txt", b"OTP: 123456", "text/plain")})
    assert response.status_code == 422 and "123456" not in response.text
    assert client.patch(f"/api/v1/incidents/{ident}/description", json={"description": "password: synthetic-secret"}).status_code == 422
    assert client.get(f"/api/v1/incidents/{ident}/evidence").json() == []


def test_R3_header_cookie_csrf_and_legacy_access(client, db):
    import uuid
    from app.models.incident import Incident
    response = client.post("/api/v1/incidents", json={"incident_type": "financial_fraud"})
    cookie = response.headers["set-cookie"].lower()
    assert "httponly" in cookie and "secure" in cookie and "samesite=strict" in cookie
    ident = response.json()["id"]
    secret = client.cookies.get("cybersos_case_" + ident)
    client.cookies.clear()
    path = f"/api/v1/incidents/{ident}"
    assert client.get(path, params={"case_secret": secret}).status_code == 404
    owner = {"X-Case-Secret": secret}
    assert client.get(path, headers=owner).status_code == 200
    assert client.patch(path + "/description", headers={**owner, "Origin": "https://foreign.example"}, json={"description": "Changed"}).status_code == 404
    assert client.get(path, headers=owner).json()["description"] is None
    db.get(Incident, uuid.UUID(ident)).case_secret_hash = None
    db.commit()
    assert client.get(path, headers=owner).status_code == 404


def test_R2_R3_history_never_recomputes_and_provenance_is_case_scoped(client, monkeypatch):
    import app.services.response_service as service
    ident = create(client)
    other = create(client)
    proof = client.post(f"/api/v1/incidents/{other}/evidence", files={"file": ("safe.txt", b"synthetic", "text/plain")}).json()["id"]
    assert client.put(f"/api/v1/incidents/{ident}/facts", json={"kind": "financial_scam_transfer", "provenance": [
        {"field": "amount", "origin": "evidence_extraction", "evidence_id": proof}]}).status_code == 422
    monkeypatch.setattr(service, "evaluate", lambda *a, **kw: pytest.fail("History was recomputed"))
    assert client.get(f"/api/v1/incidents/{ident}/plans").status_code == 200
    assert client.get(f"/api/v1/incidents/{ident}/action-plan").status_code == 200


@pytest.mark.parametrize("initial_type", ["financial_fraud", "other_cyber_crime"])
def test_R4_triage_preserves_financial_legacy_fields(client, initial_type):
    payload = {"incident_type": initial_type}
    if initial_type == "other_cyber_crime":
        payload["other_crime_sub_category"] = "any_other"
        payload["details"] = {"other_crime_details": "Synthetic narrative", "incident_date_time": "1 Oct 2026", "occurred_on": "Website"}
    created = client.post("/api/v1/incidents", json=payload)
    assert created.status_code == 201, created.text
    ident = created.json()["id"]
    result = client.post(f"/api/v1/incidents/{ident}/triage", json={
        "incident_type": "financial_fraud", "authorization": "authorized", "transaction_status": "pending",
        "is_fraud_ongoing": True, "is_otp_shared": True,
        "incident_subtype": "synthetic_transfer", "details": {"note": "Synthetic narrative"}})
    assert result.status_code == 200, result.text
    data = result.json()
    assert data["transaction_status"] == "pending"
    assert data["is_fraud_ongoing"] is True and data["is_otp_shared"] is True
    assert data["incident_subtype"] == "synthetic_transfer"
    assert data["details"] == {"note": "Synthetic narrative"}
    assert data["incident_type"] == "financial_fraud"
    assert client.get(f"/api/v1/incidents/{ident}/action-plan").json()["playbook_id"] == "financial_scam_transfer"
