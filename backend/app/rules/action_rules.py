from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.models.incident import IncidentType, Urgency
from app.rules.constants import AGE_BUCKETS, AMOUNT_THRESHOLDS

URGENCY_RANK = {
    Urgency.low: 0,
    Urgency.standard: 1,
    Urgency.medium_low: 2,
    Urgency.medium: 3,
    Urgency.high: 4,
    Urgency.critical: 5,
}


@dataclass(frozen=True)
class ActionPlan:
    priority: Urgency
    actions: list[str]
    severity: Urgency
    ongoing_risk: Urgency
    reasons: list[dict[str, str]]


def _reason(factor: str, rule_id: str, text: str, contribution: Urgency) -> dict[str, str]:
    return {
        "factor": factor,
        "rule_id": rule_id,
        "human_readable_reason": text,
        "severity_contribution": contribution.value,
    }


def _highest(current: Urgency, candidate: Urgency) -> Urgency:
    return max((current, candidate), key=URGENCY_RANK.get)


def _bool(details: dict[str, object], *keys: str) -> bool:
    return any(details.get(key) is True or str(details.get(key, "")).strip().lower() in {"yes", "true"} for key in keys)


def determine_women_children_plan(
    incident_subtype: str | None,
    affected_person_type: str | None,
    immediate_danger: bool | None,
    threat_or_blackmail: bool | None,
    content_still_online: bool | None,
    details: dict[str, object] | None = None,
) -> ActionPlan:
    values = details or {}
    subtype = (incident_subtype or str(values.get("incident_subtype", ""))).lower()
    affected = (affected_person_type or str(values.get("affected_person_type", ""))).lower()
    priority = Urgency.low
    reasons: list[dict[str, str]] = []

    def apply(factor: str, rule_id: str, text: str, level: Urgency) -> None:
        nonlocal priority
        reasons.append(_reason(factor, rule_id, text, level))
        priority = _highest(priority, level)

    danger = immediate_danger is True or _bool(values, "immediate_physical_danger", "immediate_danger")
    physical_threat = _bool(values, "threat_of_violence", "physical_harm_threat") or "threat" in subtype
    ongoing_threat = _bool(values, "ongoing_threat", "stalking_is_ongoing", "harassment_is_ongoing", "threat_is_ongoing")
    blackmail = threat_or_blackmail is True or _bool(values, "blackmail_or_extortion", "threat_or_blackmail")
    minor = "child" in affected or "minor" in affected or "child" in subtype
    escalating = _bool(values, "threats_are_escalating")
    offender_access = _bool(values, "offender_has_access_to_victim", "offender_knows_victim_location")
    published = content_still_online is True or _bool(values, "content_already_published")

    if danger:
        apply("physical_danger", "WC-DANGER-001", "The report indicates a potential immediate safety risk.", Urgency.critical)
    if physical_threat and (danger or escalating or ongoing_threat):
        apply("threat_of_violence", "WC-THREAT-001", "The report indicates a potentially escalating or ongoing threat of physical harm.", Urgency.critical)
    elif physical_threat or ongoing_threat or blackmail:
        apply("ongoing_threat", "WC-THREAT-002", "The report indicates an active threat, pressure, or harassment.", Urgency.high)
    if blackmail and (ongoing_threat or published):
        apply("blackmail_or_extortion", "WC-BLACKMAIL-001", "Blackmail or pressure may still be affecting the person involved.", Urgency.critical)
    if minor and (danger or ongoing_threat or blackmail or "sexual" in subtype or "exploitation" in subtype):
        apply("vulnerability", "WC-MINOR-001", "A child or minor may be involved in an active safeguarding risk.", Urgency.high)
    if "stalk" in subtype and (ongoing_threat or offender_access):
        apply("stalking", "WC-STALK-001", "The report indicates ongoing stalking or access to the person involved.", Urgency.high)
    if escalating:
        apply("escalation", "WC-ESCALATION-001", "Threats or harassment are reported to be escalating.", Urgency.high)
    if published:
        reasons.append(_reason("evidence_or_content", "WC-CONTENT-001", "The content or profile may still be available online; preserve it without redistribution.", Urgency.medium))
    if not reasons:
        reasons.append(_reason("baseline", "WC-BASELINE-001", "The report does not indicate an immediate or ongoing high-risk condition.", Urgency.low))
    return ActionPlan(priority, [], Urgency.high if minor else Urgency.low, priority if priority != Urgency.low else Urgency.low, reasons)


def determine_other_cyber_plan(
    incident_subtype: str | None,
    account_access: str | None,
    attacker_active: bool | None,
    sensitive_information_exposed: bool | None,
    details: dict[str, object] | None = None,
) -> ActionPlan:
    values = details or {}
    subtype = (incident_subtype or str(values.get("incident_subtype", ""))).lower()
    priority = Urgency.low
    reasons: list[dict[str, str]] = []

    def apply(factor: str, rule_id: str, text: str, level: Urgency) -> None:
        nonlocal priority
        reasons.append(_reason(factor, rule_id, text, level))
        priority = _highest(priority, level)

    account_compromised = "hack" in subtype or account_access == "No" or _bool(values, "account_compromised", "email_compromised", "social_media_compromised")
    attacker_access = attacker_active is True or _bool(values, "attacker_still_has_access", "attacker_active")
    unauthorized = _bool(values, "unauthorized_activity_continuing")
    remote = _bool(values, "remote_access_granted")
    credentials = _bool(values, "credentials_exposed", "password_exposed", "otp_exposed", "credentials_entered")
    sensitive = sensitive_information_exposed is True or _bool(values, "sensitive_data_exposed", "personal_information_exposed", "data_exfiltration_suspected")
    ransomware = "ransomware" in subtype or _bool(values, "ransomware_detected")

    if unauthorized:
        apply("ongoing_activity", "CYBER-ACTIVE-001", "Unauthorized activity is reported to be continuing.", Urgency.critical)
    if account_compromised and attacker_access:
        apply("account_compromise", "CYBER-ACCOUNT-001", "The attacker may still have access to the affected account.", Urgency.critical)
    elif attacker_access and (credentials or sensitive):
        apply("active_control", "CYBER-ACTIVE-002", "Someone may still control the account while sensitive information is exposed.", Urgency.critical)
    elif remote and attacker_access:
        apply("remote_access", "CYBER-REMOTE-001", "Remote access may still be available to another person.", Urgency.critical)
    elif account_compromised or remote or credentials:
        apply("credential_risk", "CYBER-CREDENTIAL-001", "An account, device, or credential may still be at risk.", Urgency.high)
    if sensitive:
        apply("sensitive_data", "CYBER-DATA-001", "Personal or sensitive information may have been exposed.", Urgency.high)
    if ransomware:
        apply("ransomware", "CYBER-RANSOMWARE-001", "Ransomware may be affecting files or systems.", Urgency.critical if unauthorized else Urgency.high)
    if not reasons:
        reasons.append(_reason("baseline", "CYBER-BASELINE-001", "The report does not indicate an active high-risk compromise.", Urgency.low))
    return ActionPlan(priority, [], priority, priority if priority != Urgency.low else Urgency.low, reasons)


def _as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def _age_bucket(age) -> str:
    if age < AGE_BUCKETS["under_24_hours"]:
        return "under_24_hours"
    if age < AGE_BUCKETS["24_to_72_hours"]:
        return "24_to_72_hours"
    if age < AGE_BUCKETS["72_hours_to_7_days"]:
        return "72_hours_to_7_days"
    return "7_days_or_more"


def determine_action_plan(
    incident_type: IncidentType | str,
    incident_datetime: datetime,
    amount: Decimal | float | None,
    has_transaction_id: bool,
    now: datetime | None = None,
    transaction_status: str | None = None,
    is_fraud_ongoing: bool | None = None,
    is_account_compromised: bool | None = None,
    is_credentials_exposed: bool | None = None,
    is_otp_shared: bool | None = None,
    is_pin_shared: bool | None = None,
    is_password_shared: bool | None = None,
    is_remote_access_granted: bool | None = None,
    unauthorized_activity_continuing: bool | None = None,
    potential_additional_loss: bool | None = None,
    account_secured: bool | None = None,
    evidence_available: bool | None = None,
) -> ActionPlan:
    """Deprecated Phase 0 adapter. Critical selection delegates to the versioned engine."""
    from app.domain.facts import FACTS_ADAPTER
    from app.domain.playbooks import evaluate
    if IncidentType(incident_type) != IncidentType.financial_fraud:
        raise ValueError("No financial playbook configured for this incident type")
    def known_any(*values):
        return True if any(v is True for v in values) else None if any(v is None for v in values) else False
    facts = FACTS_ADAPTER.validate_python({"kind": "financial_authorization_unknown",
        "occurred_at": incident_datetime, "amount": amount, "transaction_status": transaction_status,
        "account_compromised": is_account_compromised, "remote_access": is_remote_access_granted,
        "credentials_exposed": known_any(is_credentials_exposed, is_otp_shared, is_pin_shared, is_password_shared),
        "ongoing_loss": known_any(is_fraud_ongoing, unauthorized_activity_continuing, potential_additional_loss),
        "evidence_available": evidence_available})
    plan = evaluate(facts, as_of=now or datetime.now(timezone.utc))
    severity = None if amount is None else (Urgency.critical if Decimal(str(amount)) >= AMOUNT_THRESHOLDS["very_high"] else Urgency.high if Decimal(str(amount)) >= AMOUNT_THRESHOLDS["high"] else Urgency.medium if Decimal(str(amount)) >= AMOUNT_THRESHOLDS["moderate"] else Urgency.low)
    risk = Urgency.critical if facts.ongoing_loss is True or facts.remote_access is True else Urgency.high if facts.account_compromised is True or facts.credentials_exposed is True else None
    reasons = [_reason("playbook", "FIN-ONGOING-001" if risk == Urgency.critical else "FIN-PLAYBOOK-001", reason, plan.urgency) for reason in plan.reasons]
    return ActionPlan(priority=plan.urgency, actions=[a.id for a in plan.actions], severity=severity, ongoing_risk=risk, reasons=reasons)
