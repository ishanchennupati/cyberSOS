import pytest

from app.models.incident import PaymentMethod, Urgency
from app.services.incident_service import (
    ACTION_PLAN_RULES,
    LARGE_VALUE_ACTION,
    build_action_list,
)


@pytest.mark.parametrize("urgency", list(Urgency))
@pytest.mark.parametrize("method", list(PaymentMethod))
def test_every_urgency_payment_combo_is_non_empty(
    urgency: Urgency, method: PaymentMethod
) -> None:
    assert (urgency, method) in ACTION_PLAN_RULES
    actions = build_action_list(urgency, method, large_amount=False)
    assert len(actions) >= 1
    assert all(item.title and item.why for item in actions)


@pytest.mark.parametrize("urgency", list(Urgency))
@pytest.mark.parametrize("method", list(PaymentMethod))
def test_large_amount_appends_bank_desk_action(
    urgency: Urgency, method: PaymentMethod
) -> None:
    base = build_action_list(urgency, method, large_amount=False)
    large = build_action_list(urgency, method, large_amount=True)
    assert len(large) == len(base) + 1
    assert large[-1].id == LARGE_VALUE_ACTION.id
    assert "fraud/dispute desk" in large[-1].title.lower()


def test_critical_upi_includes_1930_and_upi_app() -> None:
    actions = build_action_list(Urgency.critical, PaymentMethod.upi)
    ids = [item.id for item in actions]
    phones = [item.phone for item in actions]
    assert "call_1930" in ids
    assert "upi_in_app" in ids
    assert "1930" in phones


def test_credit_card_plan_mentions_chargeback() -> None:
    actions = build_action_list(Urgency.high, PaymentMethod.credit_card)
    blob = " ".join(item.title + item.why for item in actions).lower()
    assert "chargeback" in blob
    assert "credit" in blob
