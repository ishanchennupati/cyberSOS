from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.models.incident import IncidentType, Urgency
from app.rules.constants import AGE_BUCKETS, AMOUNT_THRESHOLDS

ACTION_RULES = {
    (IncidentType.financial_fraud, "under_24_hours", True): (Urgency.critical, (
        "contact_bank_now", "call_1930", "preserve_evidence", "file_complaint",
    )),
    (IncidentType.financial_fraud, "under_24_hours", False): (Urgency.critical, (
        "contact_bank_now", "call_1930", "preserve_evidence", "file_complaint",
    )),
    (IncidentType.financial_fraud, "24_to_72_hours", True): (Urgency.high, (
        "contact_bank", "call_1930_or_file_online", "preserve_evidence",
    )),
    (IncidentType.financial_fraud, "24_to_72_hours", False): (Urgency.high, (
        "retrieve_transaction_id", "contact_bank", "call_1930_or_file_online", "preserve_evidence",
    )),
    (IncidentType.financial_fraud, "72_hours_to_7_days", True): (Urgency.medium, (
        "file_complaint", "contact_bank_if_not_already", "preserve_evidence",
    )),
    (IncidentType.financial_fraud, "72_hours_to_7_days", False): (Urgency.medium, (
        "retrieve_transaction_id", "file_complaint", "contact_bank", "preserve_evidence",
    )),
    (IncidentType.financial_fraud, "7_days_or_more", True): (Urgency.low, (
        "file_complaint", "preserve_evidence",
    )),
    (IncidentType.financial_fraud, "7_days_or_more", False): (Urgency.low, (
        "file_complaint", "preserve_evidence",
    )),
}

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
    recovery_window: str
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
    return ActionPlan(priority, [], Urgency.high if minor else Urgency.low, priority if priority != Urgency.low else Urgency.low, "not_applicable", reasons)


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
    return ActionPlan(priority, [], priority, priority if priority != Urgency.low else Urgency.low, "not_applicable", reasons)


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
    is_fraud_ongoing: bool = False,
    is_account_compromised: bool = False,
    is_credentials_exposed: bool = False,
    is_otp_shared: bool = False,
    is_pin_shared: bool = False,
    is_password_shared: bool = False,
    is_remote_access_granted: bool = False,
    unauthorized_activity_continuing: bool = False,
    potential_additional_loss: bool = False,
    account_secured: bool = False,
    evidence_available: bool | None = None,
) -> ActionPlan:
    incident_type = IncidentType(incident_type)
    age = _as_utc(now or datetime.now(timezone.utc)) - _as_utc(incident_datetime)
    key = (incident_type, _age_bucket(age), has_transaction_id)
    try:
        base_priority, action_keys = ACTION_RULES[key]
    except KeyError as exc:
        raise ValueError(f"No action rules configured for {incident_type}") from exc
    reasons = [_reason(
        "time_sensitivity",
        "FIN-AGE-001",
        f"The incident occurred {_age_description(age)}.",
        base_priority,
    )]
    priority = base_priority
    if age < timedelta(hours=24):
        recovery_window = "open"
    elif age < timedelta(days=7):
        recovery_window = "uncertain"
    else:
        recovery_window = "likely_expired"
    if transaction_status == "pending":
        recovery_window = "open"
        reasons.append(_reason("transaction_status", "FIN-PENDING-001", "The transaction is still pending and may require immediate intervention.", Urgency.critical))
        priority = max((priority, Urgency.critical), key=URGENCY_RANK.get)
    elif transaction_status == "completed":
        reasons.append(_reason("transaction_status", "FIN-COMPLETED-001", "The transaction is completed, so prompt reporting remains important.", Urgency.high if age < timedelta(days=1) else base_priority))
    risk_flags = (
        is_fraud_ongoing or unauthorized_activity_continuing or is_remote_access_granted
        or potential_additional_loss
    )
    if risk_flags:
        reasons.append(_reason("ongoing_risk", "FIN-ONGOING-001", "Unauthorized activity or additional loss may still be continuing.", Urgency.critical))
        priority = max((priority, Urgency.critical), key=URGENCY_RANK.get)
    elif is_account_compromised or is_credentials_exposed or is_otp_shared or is_pin_shared or is_password_shared:
        reasons.append(_reason("ongoing_risk", "FIN-COMPROMISE-001", "Account access or sensitive credentials may still be at risk.", Urgency.high))
        priority = max((priority, Urgency.high), key=URGENCY_RANK.get)
    ongoing_risk = Urgency.critical if risk_flags else Urgency.high if (is_account_compromised or is_credentials_exposed or is_otp_shared or is_pin_shared or is_password_shared) else Urgency.low
    amount_value = Decimal(str(amount)) if amount is not None else Decimal("0")
    severity = (Urgency.critical if amount_value >= AMOUNT_THRESHOLDS["very_high"] else Urgency.high if amount_value >= AMOUNT_THRESHOLDS["high"] else Urgency.medium if amount_value >= AMOUNT_THRESHOLDS["moderate"] else Urgency.low)
    if amount_value >= AMOUNT_THRESHOLDS["moderate"]:
        reasons.append(_reason("financial_impact", "FIN-AMOUNT-001", "The reported financial loss increases the incident's severity.", severity))
    if account_secured:
        reasons.append(_reason("account_security", "FIN-SECURED-001", "The account is reported as secured, reducing ongoing-loss risk.", Urgency.low))
    if evidence_available is False:
        reasons.append(_reason("evidence", "FIN-EVIDENCE-001", "Evidence has not yet been identified; preserve records before they are lost.", Urgency.medium))
    actions = list(action_keys)
    if amount is not None and Decimal(str(amount)) >= AMOUNT_THRESHOLDS["fir"]:
        actions.append("consider_fir")
    return ActionPlan(priority=priority, actions=actions, severity=severity, ongoing_risk=ongoing_risk, recovery_window=recovery_window, reasons=reasons)


def _age_description(age: timedelta) -> str:
    if age < timedelta(hours=1):
        return "less than 1 hour ago"
    if age < timedelta(days=1):
        return "within the last 24 hours"
    if age < timedelta(days=3):
        return "between 24 and 72 hours ago"
    if age < timedelta(days=7):
        return "within the last 7 days"
    return "7 or more days ago"