from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.models.incident import IncidentType, Urgency
from app.rules.action_rules import determine_action_plan


NOW = datetime(2026, 8, 24, 12, tzinfo=timezone.utc)


@pytest.mark.parametrize(
    ("age", "has_transaction_id", "priority", "actions"),
    [
        (timedelta(hours=1), True, Urgency.critical, ["contact_bank_now", "call_1930", "preserve_evidence", "file_complaint"]),
        (timedelta(hours=24), True, Urgency.high, ["contact_bank", "call_1930_or_file_online", "preserve_evidence"]),
        (timedelta(hours=24), False, Urgency.high, ["retrieve_transaction_id", "contact_bank", "call_1930_or_file_online", "preserve_evidence"]),
        (timedelta(hours=72), True, Urgency.medium, ["file_complaint", "contact_bank_if_not_already", "preserve_evidence"]),
        (timedelta(hours=72), False, Urgency.medium, ["retrieve_transaction_id", "file_complaint", "contact_bank", "preserve_evidence"]),
        (timedelta(days=7), True, Urgency.low, ["file_complaint", "preserve_evidence"]),
    ],
)
def test_financial_fraud_matrix(age, has_transaction_id, priority, actions) -> None:
    plan = determine_action_plan(
        IncidentType.financial_fraud,
        NOW - age,
        Decimal("2500"),
        has_transaction_id,
        now=NOW,
    )
    assert plan.priority == priority
    assert plan.actions == actions


@pytest.mark.parametrize(
    ("age", "priority"),
    [
        (timedelta(hours=23, minutes=59), Urgency.critical),
        (timedelta(hours=24, minutes=1), Urgency.high),
        (timedelta(hours=71, minutes=59), Urgency.high),
        (timedelta(hours=72, minutes=1), Urgency.medium),
        (timedelta(days=6, hours=23, minutes=59), Urgency.medium),
        (timedelta(days=7, minutes=1), Urgency.low),
    ],
)
def test_age_cutoffs(age, priority) -> None:
    assert determine_action_plan(IncidentType.financial_fraud, NOW - age, None, True, now=NOW).priority == priority


def test_large_amount_adds_fir_without_changing_priority() -> None:
    plan = determine_action_plan(
        IncidentType.financial_fraud,
        NOW - timedelta(days=2),
        Decimal("100000"),
        True,
        now=NOW,
    )
    assert plan.priority == Urgency.high
    assert plan.actions[-1] == "consider_fir"


def test_small_recent_pending_fraud_has_open_recovery_window() -> None:
    plan = determine_action_plan(
        IncidentType.financial_fraud, NOW - timedelta(minutes=20), Decimal("2000"),
        True, now=NOW, transaction_status="pending"
    )
    assert plan.priority == Urgency.critical
    assert plan.recovery_window == "open"


def test_large_old_fraud_is_not_automatically_critical() -> None:
    plan = determine_action_plan(
        IncidentType.financial_fraud, NOW - timedelta(weeks=3), Decimal("200000"),
        True, now=NOW, account_secured=True
    )
    assert plan.priority == Urgency.low
    assert plan.severity == Urgency.critical
    assert plan.ongoing_risk == Urgency.low


def test_ongoing_compromise_overrides_small_amount_and_age() -> None:
    plan = determine_action_plan(
        IncidentType.financial_fraud, NOW - timedelta(hours=2), Decimal("1500"),
        True, now=NOW, unauthorized_activity_continuing=True
    )
    assert plan.priority == Urgency.critical
    assert any(reason["rule_id"] == "FIN-ONGOING-001" for reason in plan.reasons)


def test_credentials_exposed_means_at_least_high() -> None:
    plan = determine_action_plan(
        IncidentType.financial_fraud, NOW - timedelta(days=10), Decimal("1500"),
        True, now=NOW, is_credentials_exposed=True, potential_additional_loss=True
    )
    assert plan.priority == Urgency.critical
    assert plan.ongoing_risk == Urgency.critical


def test_completed_low_value_old_incident_is_low() -> None:
    plan = determine_action_plan(
        IncidentType.financial_fraud, NOW - timedelta(days=30), Decimal("500"),
        True, now=NOW, transaction_status="completed", account_secured=True
    )
    assert plan.priority == Urgency.low
    assert plan.recovery_window == "likely_expired"


def test_women_children_physical_danger_is_critical() -> None:
    from app.rules.action_rules import determine_women_children_plan

    plan = determine_women_children_plan("Threats or blackmail", "Me", True, True, True)
    assert plan.priority == Urgency.critical
    assert any(reason["rule_id"] == "WC-DANGER-001" for reason in plan.reasons)


def test_women_children_stalking_with_access_is_high() -> None:
    from app.rules.action_rules import determine_women_children_plan

    plan = determine_women_children_plan("Cyberstalking", "Me", False, False, False, {"stalking_is_ongoing": "Yes", "offender_knows_victim_location": "Yes"})
    assert plan.priority == Urgency.high


def test_other_cyber_active_takeover_is_critical() -> None:
    from app.rules.action_rules import determine_other_cyber_plan

    plan = determine_other_cyber_plan("My account was hacked", "No", True, False)
    assert plan.priority == Urgency.critical


def test_other_cyber_resolved_compromise_is_not_critical() -> None:
    from app.rules.action_rules import determine_other_cyber_plan

    plan = determine_other_cyber_plan("My account was hacked", "Yes", False, False, {"account_secured": True})
    assert plan.priority == Urgency.high