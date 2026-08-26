from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.services.incident_service import LARGE_AMOUNT_THRESHOLD, MISSING_UTR_TEXT

NOW = datetime(2026, 8, 24, 12, 0, 0, tzinfo=timezone.utc)


def _create(client: TestClient) -> str:
    response = client.post(
        "/api/v1/incidents",
        json={"incident_type": "financial_fraud", "payment_method": "unknown"},
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def _triage_body(**overrides: object) -> dict:
    body: dict = {
        "incident_type": "financial_fraud",
        "occurred_at": (NOW - timedelta(minutes=20)).isoformat(),
        "amount": 2500,
        "payment_method": "upi",
        "transaction_id": "UTR123456789",
    }
    body.update(overrides)
    return body


def test_create_and_get_incident(client: TestClient) -> None:
    incident_id = _create(client)
    response = client.get(f"/api/v1/incidents/{incident_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == incident_id
    assert data["status"] == "draft"
    assert data["transaction_id"] is None


def test_get_missing_incident(client: TestClient) -> None:
    response = client.get("/api/v1/incidents/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_triage_without_transaction_id_succeeds(client: TestClient) -> None:
    incident_id = _create(client)
    response = client.post(
        f"/api/v1/incidents/{incident_id}/triage",
        json=_triage_body(transaction_id=None),
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["transaction_id"] is None
    assert data["urgency"] == "critical"
    assert data["urgency_computed_at"] is not None
    assert data["status"] == "action_required"
    assert data["payment_method"] == "upi"
    assert data["occurred_at"] is not None


def test_triage_empty_transaction_id_stored_as_null(client: TestClient) -> None:
    incident_id = _create(client)
    response = client.post(
        f"/api/v1/incidents/{incident_id}/triage",
        json=_triage_body(transaction_id="  "),
    )
    assert response.status_code == 200
    assert response.json()["transaction_id"] is None


def test_action_plan_before_triage_is_conflict(client: TestClient) -> None:
    incident_id = _create(client)
    response = client.get(f"/api/v1/incidents/{incident_id}/action-plan")
    assert response.status_code == 409


def test_action_plan_includes_draft_and_actions(client: TestClient) -> None:
    incident_id = _create(client)
    client.post(
        f"/api/v1/incidents/{incident_id}/triage",
        json=_triage_body(transaction_id=None, amount=LARGE_AMOUNT_THRESHOLD),
    )
    response = client.get(f"/api/v1/incidents/{incident_id}/action-plan")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["urgency"] == "critical"
    assert data["urgency_label"] == "ACT NOW"
    assert data["large_amount"] is True
    assert len(data["actions"]) >= 1
    assert any(item["phone"] == "1930" for item in data["actions"])
    assert any(item["id"] == "bank_fraud_desk" for item in data["actions"])
    draft = data["complaint_draft"]["body"]
    assert MISSING_UTR_TEXT in draft
    assert "₹1,00,000.00" in draft
    assert "cybercrime.gov.in" in draft


def test_triage_rejects_zero_amount(client: TestClient) -> None:
    incident_id = _create(client)
    response = client.post(
        f"/api/v1/incidents/{incident_id}/triage",
        json=_triage_body(amount=0),
    )
    assert response.status_code == 422


def test_triage_missing_incident(client: TestClient) -> None:
    response = client.post(
        "/api/v1/incidents/00000000-0000-0000-0000-000000000000/triage",
        json=_triage_body(),
    )
    assert response.status_code == 404
