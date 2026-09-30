"""Phase 0C: prohibit financial outcome predictions and amount-gated actions."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
import json
import re

import pytest

from app.models.incident import IncidentType, PaymentMethod, Urgency
from app.rules.action_rules import determine_action_plan
from app.services import incident_service

ROOT = Path(__file__).resolve().parents[2]
NOW = datetime(2026, 9, 30, tzinfo=timezone.utc)
SCENARIO = json.loads((ROOT / "backend/tests/fixtures/scenarios.yaml").read_text())["0C_response_truth"]
PROHIBITED = re.compile(
    r"best chance|strong reversal|reversal (?:less likely|unlikely)|"
    r"usable reversal window|still reversible|banks (?:still reverse|rarely reverse)|"
    r"npci can.*reversal|escalate faster|recovery window:|"
    r"first hour.*getting the money back|much faster|"
    r"(?:bank|police) will (?:recover|refund|reverse)|"
    r"recovery (?:score|probability)|\d+\s*%.*recover", re.I | re.S,
)


@pytest.mark.parametrize("age", [0, 2, 6, 30])
@pytest.mark.parametrize("status", [None, "pending", "completed"])
def test_R1_no_recovery_prediction_or_amount_gated_police_action(age, status):
    plans = [determine_action_plan(IncidentType.financial_fraud,
             NOW - timedelta(days=age), amount, True, now=NOW,
             transaction_status=status) for amount in [None] + [Decimal(str(a)) for a in SCENARIO["amounts"]]]
    assert all(not hasattr(p, "recovery_window") for p in plans)
    assert all(p.actions == plans[0].actions for p in plans)
    assert "consider_fir" not in plans[0].actions


def test_R1_current_and_legacy_action_text_has_no_financial_promises():
    texts = list(incident_service.CORE_MESSAGES.values())
    for urgency in Urgency:
        for method in PaymentMethod:
            for large in (False, True):
                actions = incident_service.build_action_list(urgency, method, large_amount=large)
                texts.extend(a.title + " " + a.why for a in actions)
    texts.extend(a.title + " " + a.why for a in incident_service._RULE_ACTIONS.values())
    for text in texts:
        assert not PROHIBITED.search(text), text


def test_R1_frontend_and_summary_copy_has_no_financial_or_provider_promises():
    paths = [path for folder in ("components", "app", "features")
             for path in (ROOT / "frontend" / folder).rglob("*.ts*")]
    for path in paths:
        text = path.read_text(encoding="utf-8")
        assert not PROHIBITED.search(text), str(path)
    assert "plan.recovery_window" not in (ROOT / "frontend/components/result-screen.tsx").read_text(encoding="utf-8")
    assert "AI-generated draft" not in (ROOT / "frontend/components/evidence/summary-generator.tsx").read_text(encoding="utf-8")


def test_R1_legacy_amount_does_not_change_actions_or_urgency():
    occurred = NOW - timedelta(days=2)
    assert incident_service.compute_urgency(occurred, 100, now=NOW) == incident_service.compute_urgency(occurred, 200000, now=NOW)
    assert incident_service.build_action_list(Urgency.high, PaymentMethod.upi, large_amount=False) == incident_service.build_action_list(Urgency.high, PaymentMethod.upi, large_amount=True)


def test_R1_old_persisted_predictions_are_not_returned(client, db):
    from app.models.incident import Incident
    response = client.post("/api/v1/incidents", json={"incident_type": "financial_fraud"})
    ident = response.json()["id"]
    import uuid
    stored = db.get(Incident, uuid.UUID(ident))
    stored.recovery_window = "likely_expired"
    db.commit()
    assert "recovery_window" not in client.get(f"/api/v1/incidents/{ident}").json()
    db.refresh(stored)
    assert stored.recovery_window == "likely_expired"  # Suppress without destructive migration.


def test_R2_no_tracked_generated_artifacts_or_environment_secrets():
    import subprocess
    tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode().split("\0")
    for name in filter(None, tracked):
        path = Path(name)
        assert path.suffix not in {".db", ".sqlite", ".sqlite3", ".tsbuildinfo", ".log"}, name
        assert not (path.name.startswith(".env") and path.name != ".env.example"), name
        assert not name.startswith(("evidence/", "backend/evidence/", "uploads/", "backend/uploads/")), name
