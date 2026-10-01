"""Every current private resource must resolve the owning case capability."""
import pytest

OPERATIONS = [
    ("GET", "incidents/{case}/conversation", None),
    ("POST", "incidents/{case}/conversation/turns", {"turn_id": "11111111-1111-4111-8111-111111111111", "expected_revision": 0, "field": "authorization", "value": "authorized"}),
    ("GET", "incidents/{case}", None),
    ("POST", "incidents/{case}/triage", {"occurred_at": "2026-10-01T12:00:00Z", "amount": 100, "payment_method": "upi"}),
    ("PATCH", "incidents/{case}/details", {}),
    ("GET", "incidents/{case}/action-plan", None),
    ("GET", "incidents/{case}/evidence-readiness", None),
    ("PATCH", "incidents/{case}/description", {"description": "Synthetic"}),
    ("POST", "incidents/{case}/generate-summary", None),
    ("GET", "incidents/{case}/evidence", None),
    ("POST", "incidents/{case}/evidence", "upload"),
    ("GET", "evidence/{proof}", None),
    ("GET", "evidence/{proof}/file", None),
    ("PATCH", "evidence/{proof}", {"description": "Synthetic"}),
    ("DELETE", "evidence/{proof}", None),
    ("POST", "evidence/{proof}/extract", None),
    ("POST", "evidence/{proof}/verify", {"extracted_data": {}}),
    ("GET", "evidence/{proof}/compare", None),
    ("POST", "incidents/{case}/suspects", {"type": "phone", "value": "9999900000"}),
    ("GET", "incidents/{case}/suspects", None),
    ("PATCH", "suspects/{suspect}", {"value": "9999900001"}),
    ("DELETE", "suspects/{suspect}", None),
    ("POST", "incidents/{case}/timeline", {"event_time": "2026-10-01T12:00:00Z", "description": "Synthetic"}),
    ("GET", "incidents/{case}/timeline", None),
    ("PATCH", "timeline/{event}", {"description": "Synthetic"}),
    ("DELETE", "timeline/{event}", None),
    ("PUT", "incidents/{case}/facts", {"kind": "financial_scam_transfer"}),
    ("GET", "incidents/{case}/response-plan", None),
    ("GET", "incidents/{case}/plans", None),
    ("GET", "incidents/{case}/completions", None),
    ("POST", "incidents/{case}/plans/{plan}/actions/contact_bank_unknown/completion", {"completed": True}),
]


@pytest.mark.parametrize("method,path,payload", OPERATIONS)
@pytest.mark.parametrize("credential", ["missing", "case_a"])
def test_R3_case_a_cannot_access_case_b(client, method, path, payload, credential):
    a = client.post("/api/v1/incidents", json={"incident_type": "financial_fraud"}).json()["id"]
    token_a = client.cookies.get("cybersos_case_" + a, "synthetic-wrong-secret")
    b = client.post("/api/v1/incidents", json={"incident_type": "financial_fraud"}).json()["id"]
    plan = client.get(f"/api/v1/incidents/{b}/response-plan").json()["id"]
    proof = client.post(f"/api/v1/incidents/{b}/evidence", files={"file": ("proof.txt", b"synthetic", "text/plain")}).json()["id"]
    suspect = client.post(f"/api/v1/incidents/{b}/suspects", json={"type": "phone", "value": "9999900000"}).json()["id"]
    event = client.post(f"/api/v1/incidents/{b}/timeline", json={"event_time": "2026-10-01T12:00:00Z", "description": "Synthetic"}).json()["id"]
    client.cookies.clear()
    headers = {"X-Case-Secret": token_a} if credential == "case_a" else {}
    kwargs = {"files": {"file": ("proof.txt", b"synthetic", "text/plain")}} if payload == "upload" else {"json": payload} if payload is not None else {}
    result = client.request(method, "/api/v1/" + path.format(case=b, proof=proof, suspect=suspect, event=event, plan=plan), headers=headers, **kwargs)
    assert result.status_code == 404


def test_R3_every_private_route_has_owner_gate():
    from app.main import app
    from app.services.case_access import authorize_case_resource
    private = [r for r in app.routes if r.path.startswith("/api/v1/") and not r.path.startswith("/api/v1/health/")
        and getattr(r, "dependant", None) and not (r.path == "/api/v1/incidents" and "POST" in r.methods)]
    assert len(private) == len(OPERATIONS)
    assert all(any(d.call is authorize_case_resource for d in r.dependant.dependencies) for r in private)
