import pytest

from app.models.incident import PaymentMethod, Urgency
from app.services.incident_service import (
    ACTION_PLAN_RULES,
    build_action_list,
)


@pytest.mark.parametrize("urgency", list(Urgency))
@pytest.mark.parametrize("method", list(PaymentMethod))
def test_legacy_compatibility_matrix(
    urgency: Urgency, method: PaymentMethod
) -> None:
    assert (urgency, method) in ACTION_PLAN_RULES
    actions = build_action_list(urgency, method, large_amount=False)
    assert len(actions) >= 1
    assert all(item.title and item.why for item in actions)
    large = build_action_list(urgency, method, large_amount=True)
    assert large == actions


def test_critical_upi_includes_bank_and_1930() -> None:
    actions = build_action_list(Urgency.critical, PaymentMethod.upi)
    ids = [item.id for item in actions]
    phones = [item.phone for item in actions]
    assert "call_1930" in ids
    assert "contact_bank_unknown" in ids
    assert "1930" in phones


def test_credit_card_plan_asks_bank_about_applicable_steps() -> None:
    actions = build_action_list(Urgency.high, PaymentMethod.credit_card)
    blob = " ".join(item.title + item.instruction + item.why for item in actions).lower()
    assert "without assuming refund eligibility" in blob
    assert "bank" in blob
