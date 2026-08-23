from datetime import datetime, timezone

from app.models.incident import IncidentType, PaymentMethod, Urgency
from app.services.incident_service import (
    LARGE_AMOUNT_THRESHOLD,
    MISSING_UTR_TEXT,
    build_action_list,
    render_complaint_draft,
)

OCCURRED = datetime(2026, 8, 20, 9, 30, tzinfo=timezone.utc)


def _draft(*, amount: float, transaction_id: str | None, urgency: Urgency) -> str:
    actions = build_action_list(
        urgency,
        PaymentMethod.upi,
        large_amount=amount >= LARGE_AMOUNT_THRESHOLD,
    )
    return render_complaint_draft(
        incident_type=IncidentType.financial_fraud,
        occurred_at=OCCURRED,
        amount=amount,
        payment_method=PaymentMethod.upi,
        transaction_id=transaction_id,
        urgency=urgency,
        actions=actions,
    )


def test_null_transaction_id_is_explicit() -> None:
    body = _draft(amount=5_000, transaction_id=None, urgency=Urgency.high)
    assert MISSING_UTR_TEXT in body
    assert "Transaction ID / UTR:" in body
    assert "Incident type: UPI / financial fraud" in body
    assert "Payment method: UPI app" in body
    assert "not a\nlegal document" in body.lower() or "not a legal document" in body.lower()


def test_blank_transaction_id_is_treated_as_missing() -> None:
    body = _draft(amount=5_000, transaction_id="   ", urgency=Urgency.high)
    assert MISSING_UTR_TEXT in body


def test_present_transaction_id_is_used() -> None:
    body = _draft(amount=5_000, transaction_id="123456789012", urgency=Urgency.high)
    assert "123456789012" in body
    assert MISSING_UTR_TEXT not in body


def test_large_amount_boundary_includes_desk_action() -> None:
    at_threshold = _draft(
        amount=LARGE_AMOUNT_THRESHOLD,
        transaction_id=None,
        urgency=Urgency.medium,
    )
    just_under = _draft(
        amount=LARGE_AMOUNT_THRESHOLD - 0.01,
        transaction_id=None,
        urgency=Urgency.medium_low,
    )
    assert "₹1,00,000.00" in at_threshold
    assert "fraud/dispute desk" in at_threshold.lower()
    assert "fraud/dispute desk" not in just_under.lower()


def test_amount_and_actions_are_numbered() -> None:
    body = _draft(amount=1_500.5, transaction_id=None, urgency=Urgency.critical)
    assert "Amount involved: ₹1,500.50" in body
    assert "Recommended immediate actions:" in body
    assert "1. " in body
    assert "2. " in body
