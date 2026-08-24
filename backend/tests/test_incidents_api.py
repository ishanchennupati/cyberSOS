from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi.testclient import TestClient

from app.services.incident_service import LARGE_AMOUNT_THRESHOLD, MISSING_UTR_TEXT
from app.core.config import get_settings

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


def test_other_cyber_crime_triage_keeps_sub_category_and_details(client: TestClient) -> None:
    response = client.post(
        "/api/v1/incidents",
        json={
            "incident_type": "other_cyber_crime",
            "other_crime_sub_category": "ransomware",
            "payment_method": "unknown",
            "details": {
                "incident_date_time": "24 Aug 2026, 10:30 AM",
                "occurred_on": "Website",
                "bitcoin_details": "bc1-test-wallet",
            },
        },
    )
    assert response.status_code == 201, response.text
    incident_id = response.json()["id"]

    response = client.post(
        f"/api/v1/incidents/{incident_id}/triage",
        json={
            "incident_type": "other_cyber_crime",
            "other_crime_sub_category": "ransomware",
            "occurred_at": (NOW - timedelta(hours=2)).isoformat(),
            "payment_method": "unknown",
            "details": {
                "incident_date_time": "24 Aug 2026, 10:30 AM",
                "occurred_on": "Website",
                "bitcoin_details": "bc1-test-wallet",
            },
        },
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["incident_type"] == "other_cyber_crime"
    assert data["other_crime_sub_category"] == "ransomware"
    assert data["details"]["bitcoin_details"] == "bc1-test-wallet"

    response = client.get(f"/api/v1/incidents/{incident_id}/action-plan")
    assert response.status_code == 200, response.text
    draft = response.json()["complaint_draft"]["body"]
    assert "Other cyber crime category: Ransomware" in draft
    assert "Bitcoin Details: bc1-test-wallet" in draft


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


def test_other_crime_details_update_validates_and_persists(client: TestClient) -> None:
    incident_id = client.post(
        "/api/v1/incidents",
        json={
            "incident_type": "other_cyber_crime",
            "other_crime_sub_category": "any_other",
            "payment_method": "unknown",
            "details": {
                "incident_date_time": "24 Aug 2026, 10:30 AM",
                "occurred_on": "Website",
                "other_crime_details": "Initial details",
            },
        },
    ).json()["id"]
    response = client.patch(
        f"/api/v1/incidents/{incident_id}/details",
        json={
            "other_crime_sub_category": "any_other",
            "details": {
                "incident_date_time": "24 Aug 2026, 10:30 AM",
                "occurred_on": "Website",
                "other_crime_details": "Credential theft",
            },
        },
    )
    assert response.status_code == 200, response.text
    assert response.json()["details"]["other_crime_details"] == "Credential theft"

    response = client.patch(
        f"/api/v1/incidents/{incident_id}/details",
        json={"other_crime_sub_category": "any_other", "details": {}},
    )
    assert response.status_code == 422


def test_evidence_upload_persists_metadata_and_file(
    client: TestClient, tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(get_settings(), "EVIDENCE_STORAGE_DIR", str(tmp_path))
    incident_id = _create(client)
    response = client.post(
        f"/api/v1/incidents/{incident_id}/evidence",
        files={"file": ("proof.txt", b"evidence contents", "text/plain")},
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["original_filename"] == "proof.txt"
    assert data["content_type"] == "text/plain"
    assert data["size_bytes"] == len(b"evidence contents")
    assert list(tmp_path.iterdir())[0].read_bytes() == b"evidence contents"


def test_women_children_immediate_danger_is_critical_and_safety_first(client: TestClient) -> None:
    response = client.post("/api/v1/incidents", json={"incident_type": "women_children", "payment_method": "unknown", "incident_subtype": "Threats or blackmail"})
    assert response.status_code == 201, response.text
    incident_id = response.json()["id"]
    response = client.post(f"/api/v1/incidents/{incident_id}/triage", json={
        "incident_type": "women_children", "incident_subtype": "Threats or blackmail", "occurred_at": NOW.isoformat(),
        "payment_method": "unknown", "immediate_danger": True, "threat_or_blackmail": True,
        "affected_person_type": "Me", "platform": "WhatsApp", "evidence_types": [],
    })
    assert response.status_code == 200, response.text
    assert response.json()["urgency"] == "critical"
    plan = client.get(f"/api/v1/incidents/{incident_id}/action-plan").json()
    assert plan["core_message"] == "Your immediate safety comes first."
    assert plan["actions"][0]["id"] == "safety_first"


def test_women_children_child_blackmail_and_online_content_raise_urgency(client: TestClient) -> None:
    response = client.post("/api/v1/incidents", json={"incident_type": "women_children", "payment_method": "unknown", "incident_subtype": "Intimate/private content shared or threatened"})
    incident_id = response.json()["id"]
    response = client.post(f"/api/v1/incidents/{incident_id}/triage", json={
        "incident_type": "women_children", "incident_subtype": "Intimate/private content shared or threatened", "occurred_at": NOW.isoformat(),
        "payment_method": "unknown", "affected_person_type": "A child", "threat_or_blackmail": True,
        "content_still_online": True, "evidence_types": ["Screenshots"],
    })
    assert response.status_code == 200
    assert response.json()["urgency"] == "critical"
    assert response.json()["urgency_score"] >= 4


def test_other_cyber_phishing_credentials_and_active_attacker_is_high(client: TestClient) -> None:
    response = client.post("/api/v1/incidents", json={"incident_type": "other_cyber_crime", "payment_method": "unknown", "incident_subtype": "Phishing / suspicious link"})
    incident_id = response.json()["id"]
    response = client.post(f"/api/v1/incidents/{incident_id}/triage", json={
        "incident_type": "other_cyber_crime", "incident_subtype": "Phishing / suspicious link", "occurred_at": NOW.isoformat(),
        "payment_method": "unknown", "attacker_active": True, "sensitive_information_exposed": True,
        "details": {"credentials_entered": "Yes"}, "evidence_types": ["URLs"],
    })
    assert response.status_code == 200, response.text
    assert response.json()["urgency"] == "critical"
    plan = client.get(f"/api/v1/incidents/{incident_id}/action-plan").json()
    assert plan["actions"][0]["id"] == "secure_account"


def test_other_cyber_malware_uses_device_safety_actions(client: TestClient) -> None:
    response = client.post("/api/v1/incidents", json={"incident_type": "other_cyber_crime", "payment_method": "unknown", "incident_subtype": "Malware / suspicious software"})
    incident_id = response.json()["id"]
    response = client.post(f"/api/v1/incidents/{incident_id}/triage", json={
        "incident_type": "other_cyber_crime", "incident_subtype": "Malware / suspicious software", "occurred_at": NOW.isoformat(),
        "payment_method": "unknown", "account_type": "Device", "sensitive_information_exposed": True,
    })
    assert response.status_code == 200
    plan = client.get(f"/api/v1/incidents/{incident_id}/action-plan").json()
    assert any(item["id"] == "disconnect_device" for item in plan["actions"])
