"""
Incident business logic: create, triage, action plan, complaint draft.

Urgency and action lists are data tables, not nested if/else in the route
handlers. Thresholds live at the top of this module so they can be tuned
without touching flow logic.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.models.incident import (
    Evidence,
    Incident,
    IncidentStatus,
    IncidentType,
    OtherCrimeSubCategory,
    PaymentMethod,
    Urgency,
)
from app.schemas.incident import (
    ActionItem,
    ActionPlanResponse,
    ComplaintDraft,
    IncidentCreate,
    TriageRequest,
    IncidentDetailsUpdate,
)

try:
    IST = ZoneInfo("Asia/Kolkata")
except ZoneInfoNotFoundError:
    IST = timezone(timedelta(hours=5, minutes=30), name="IST")

HELPLINE_1930 = "1930"
CYBERCRIME_PORTAL_URL = "https://cybercrime.gov.in"
BANK_HELPLINE_PLACEHOLDER = "the number on the back of your card / in your bank app"

# Amount at or above this (₹) bumps urgency one tier and adds a bank-desk action.
LARGE_AMOUNT_THRESHOLD = 100_000.0

# Product heuristics, intentionally separate from the financial-fraud clock.
WOMEN_CHILDREN_THRESHOLDS = {"medium": 2, "high": 4, "critical": 7}
OTHER_CYBER_THRESHOLDS = {"medium": 3, "high": 5, "critical": 7}

MISSING_UTR_TEXT = "Not available — check bank SMS/statement"

# Ordered tightest → widest. First row whose elapsed <= duration wins.
# Table from the Phase 1 spec (≤ 1 hour / 24 hours / 3 days / 30 days).
URGENCY_BY_ELAPSED: tuple[tuple[timedelta, Urgency], ...] = (
    (timedelta(hours=1), Urgency.critical),
    (timedelta(hours=24), Urgency.high),
    (timedelta(days=3), Urgency.medium),
    (timedelta(days=30), Urgency.medium_low),
)
FALLBACK_URGENCY = Urgency.standard

URGENCY_RANK: dict[Urgency, int] = {
    Urgency.standard: 0,
    Urgency.low: 0,  # Phase 0 leftover; same floor as standard
    Urgency.medium_low: 1,
    Urgency.medium: 2,
    Urgency.high: 3,
    Urgency.critical: 4,
}
RANK_TO_URGENCY: dict[int, Urgency] = {
    0: Urgency.standard,
    1: Urgency.medium_low,
    2: Urgency.medium,
    3: Urgency.high,
    4: Urgency.critical,
}

URGENCY_BADGE: dict[Urgency, str] = {
    Urgency.critical: "ACT NOW",
    Urgency.high: "ACT TODAY",
    Urgency.medium: "ACT THIS WEEK",
    Urgency.medium_low: "FILE WHEN READY",
    Urgency.standard: "FILE WHEN READY",
    Urgency.low: "FILE WHEN READY",
}

CORE_MESSAGES: dict[Urgency, str] = {
    Urgency.critical: (
        "Best chance of reversal — call 1930 or bank helpline immediately, "
        "don't wait to finish this form"
    ),
    Urgency.high: "Still a strong reversal window — act today",
    Urgency.medium: "Reversal less likely but still possible — file now",
    Urgency.medium_low: "Focus shifts to filing complaint/FIR over reversal",
    Urgency.standard: (
        "Reversal unlikely — complaint filing is still worthwhile and often "
        "required for insurance/dispute claims"
    ),
    Urgency.low: (
        "Reversal unlikely — complaint filing is still worthwhile and often "
        "required for insurance/dispute claims"
    ),
}

INCIDENT_TYPE_LABELS: dict[IncidentType, str] = {
    IncidentType.women_children: "Women/children related cyber crime",
    IncidentType.financial_fraud: "UPI / financial fraud",
    IncidentType.other_cyber_crime: "Other cyber crime",
    IncidentType.phishing: "Phishing / fake website",
    IncidentType.identity_theft: "Identity theft",
    IncidentType.social_media: "Social media / impersonation",
    IncidentType.job_scam: "Job or investment scam",
    IncidentType.other: "Other cyber incident",
}

OTHER_CRIME_SUB_CATEGORY_LABELS: dict[OtherCrimeSubCategory, str] = {
    OtherCrimeSubCategory.online_social_media: "Online and social media related crime",
    OtherCrimeSubCategory.ransomware: "Ransomware",
    OtherCrimeSubCategory.hacking: "Hacking",
    OtherCrimeSubCategory.cryptocurrency: "Cryptocurrency related crime",
    OtherCrimeSubCategory.online_trafficking: "Online trafficking",
    OtherCrimeSubCategory.online_gambling: "Online gambling",
    OtherCrimeSubCategory.any_other: "Any other cyber crime",
}

PAYMENT_METHOD_LABELS: dict[PaymentMethod, str] = {
    PaymentMethod.upi: "UPI app",
    PaymentMethod.debit_card: "Debit card",
    PaymentMethod.credit_card: "Credit card",
    PaymentMethod.net_banking: "Net banking",
    PaymentMethod.wallet: "Wallet",
    PaymentMethod.unknown: "Not specified",
    PaymentMethod.bank_transfer: "Bank transfer",
    PaymentMethod.card: "Card",
}


def _action(
    action_id: str,
    title: str,
    why: str,
    *,
    phone: str | None = None,
    url: str | None = None,
    url_label: str | None = None,
) -> ActionItem:
    return ActionItem(
        id=action_id,
        title=title,
        why=why,
        phone=phone,
        url=url,
        url_label=url_label,
    )


# --- Action building blocks (data, not per-request branching) -----------------

_CALL_1930_NOW = _action(
    "call_1930",
    "Call 1930 now",
    "The 1930 financial cyber fraud helpline can alert your bank while a UPI "
    "or card debit is still reversible. Do this before you finish any form.",
    phone=HELPLINE_1930,
)

_CALL_1930_TODAY = _action(
    "call_1930",
    "Call 1930 today",
    "Reporting today keeps you inside a usable reversal window. 1930 is the "
    "official 24×7 financial cyber fraud helpline.",
    phone=HELPLINE_1930,
)

_CALL_1930_RECORD = _action(
    "call_1930",
    "Call 1930 to get a case on record",
    "Even when reversal is unlikely, a 1930 report creates an official trail "
    "that banks, insurers, and cybercrime.gov.in all recognise.",
    phone=HELPLINE_1930,
)

_BANK_NOW = _action(
    "call_bank",
    f"Call your bank helpline ({BANK_HELPLINE_PLACEHOLDER})",
    "Your bank can freeze the debit, block the beneficiary, and start a "
    "chargeback. Don't wait to finish this form — the first hour is the "
    "best chance of getting the money back.",
)

_BANK_TODAY = _action(
    "call_bank",
    f"Report this to your bank today ({BANK_HELPLINE_PLACEHOLDER})",
    "Banks still reverse many fraud debits reported within 24 hours. Use the "
    "number on the back of your card or the fraud option in your bank app.",
)

_BANK_DISPUTE = _action(
    "call_bank",
    f"Raise a dispute with your bank ({BANK_HELPLINE_PLACEHOLDER})",
    "Ask for a written complaint/chargeback reference. You will need it for "
    "cybercrime.gov.in and for any insurance claim.",
)

_FILE_PORTAL_AFTER_CALLS = _action(
    "file_cybercrime",
    "File on cybercrime.gov.in after you have called",
    "The portal complaint is important, but it is slower than a phone alert. "
    "Call 1930 and your bank first, then file so the case is in writing.",
    url=CYBERCRIME_PORTAL_URL,
    url_label="cybercrime.gov.in",
)

_FILE_PORTAL_TODAY = _action(
    "file_cybercrime",
    "File a complaint on cybercrime.gov.in today",
    "A same-day written complaint supports the 1930 report and gives the "
    "cybercrime coordinator something to act on.",
    url=CYBERCRIME_PORTAL_URL,
    url_label="cybercrime.gov.in",
)

_FILE_PORTAL_NOW = _action(
    "file_cybercrime",
    "File a complaint on cybercrime.gov.in now",
    "Reversal is less likely after a few days, so the written complaint is "
    "now the main path. You can paste the draft CyberSOS prepares.",
    url=CYBERCRIME_PORTAL_URL,
    url_label="cybercrime.gov.in",
)

_FILE_PORTAL_FIR = _action(
    "file_cybercrime",
    "File a complaint / FIR — focus on the record, not reversal",
    "After a few weeks, banks rarely reverse the debit. A cybercrime.gov.in "
    "complaint (and an FIR if the amount is large) is what insurers and "
    "dispute desks ask for.",
    url=CYBERCRIME_PORTAL_URL,
    url_label="cybercrime.gov.in",
)

_FILE_PORTAL_INSURANCE = _action(
    "file_cybercrime",
    "File a complaint — still needed for insurance and disputes",
    "Reversal is unlikely this long after the debit, but a complaint is often "
    "required before a bank, wallet, or insurer will even look at a claim.",
    url=CYBERCRIME_PORTAL_URL,
    url_label="cybercrime.gov.in",
)

_PRESERVE_EVIDENCE = _action(
    "preserve_evidence",
    "Save screenshots, SMS, and the transaction SMS/email now",
    "Do not delete the debit SMS, UPI chat, or call log. Photograph the "
    "screen if you cannot screenshot. Evidence is harder to reconstruct later.",
)

_DONT_SEND_MORE = _action(
    "do_not_pay_again",
    "Do not send more money to 'recover' this",
    "Anyone who calls back asking for a fee, OTP, or remote-access app to "
    "reverse the transaction is continuing the scam.",
)

URGENCY_ACTIONS: dict[Urgency, tuple[ActionItem, ...]] = {
    Urgency.critical: (
        _CALL_1930_NOW,
        _BANK_NOW,
        _FILE_PORTAL_AFTER_CALLS,
        _PRESERVE_EVIDENCE,
        _DONT_SEND_MORE,
    ),
    Urgency.high: (
        _CALL_1930_TODAY,
        _BANK_TODAY,
        _FILE_PORTAL_TODAY,
        _PRESERVE_EVIDENCE,
        _DONT_SEND_MORE,
    ),
    Urgency.medium: (
        _FILE_PORTAL_NOW,
        _CALL_1930_TODAY,
        _BANK_DISPUTE,
        _PRESERVE_EVIDENCE,
        _DONT_SEND_MORE,
    ),
    Urgency.medium_low: (
        _FILE_PORTAL_FIR,
        _BANK_DISPUTE,
        _CALL_1930_RECORD,
        _PRESERVE_EVIDENCE,
        _DONT_SEND_MORE,
    ),
    Urgency.standard: (
        _FILE_PORTAL_INSURANCE,
        _BANK_DISPUTE,
        _CALL_1930_RECORD,
        _PRESERVE_EVIDENCE,
        _DONT_SEND_MORE,
    ),
    Urgency.low: (
        _FILE_PORTAL_INSURANCE,
        _BANK_DISPUTE,
        _CALL_1930_RECORD,
        _PRESERVE_EVIDENCE,
        _DONT_SEND_MORE,
    ),
}

_UPI_ACTION = _action(
    "upi_in_app",
    "Open your UPI app and raise a complaint on this debit",
    "In GPay, PhonePe, Paytm, or BHIM: transaction history → this payment → "
    "help/report. NPCI can still attempt a UPI reversal when the report is fast.",
)

_DEBIT_CARD_ACTION = _action(
    "block_debit_card",
    "Block the debit card and ask for a chargeback",
    "Use your bank app or the helpline on the back of the card. A blocked "
    "card stops follow-on debits while the chargeback is filed.",
)

_CREDIT_CARD_ACTION = _action(
    "block_credit_card",
    "Block the credit card and start a chargeback",
    "Credit-card chargebacks have a clearer consumer path than UPI. Call the "
    "number on the back of the card and say it is a fraud dispute.",
)

_NET_BANKING_ACTION = _action(
    "freeze_net_banking",
    "Freeze net banking and change your password and transaction PIN",
    "Ask the bank to flag the beneficiary account. Then change login password, "
    "transaction PIN, and any linked UPI PIN from a device you trust.",
)

_WALLET_ACTION = _action(
    "wallet_dispute",
    "Raise a dispute in the wallet app",
    "Open Paytm / Amazon Pay / other wallet → help → this transaction. Also "
    "call 1930 so the debit is on the cybercrime record, not only with the wallet.",
)

_GENERIC_BANK_ACTION = _action(
    "generic_bank_report",
    f"Report the debit through your bank app ({BANK_HELPLINE_PLACEHOLDER})",
    "Use the fraud/dispute option in the app or the helpline printed on your "
    "card. Ask for a complaint reference number and keep it.",
)

PAYMENT_ACTIONS: dict[PaymentMethod, tuple[ActionItem, ...]] = {
    PaymentMethod.upi: (_UPI_ACTION,),
    PaymentMethod.debit_card: (_DEBIT_CARD_ACTION,),
    PaymentMethod.credit_card: (_CREDIT_CARD_ACTION,),
    PaymentMethod.net_banking: (_NET_BANKING_ACTION,),
    PaymentMethod.wallet: (_WALLET_ACTION,),
    PaymentMethod.unknown: (_GENERIC_BANK_ACTION,),
    PaymentMethod.bank_transfer: (_GENERIC_BANK_ACTION,),
    PaymentMethod.card: (_DEBIT_CARD_ACTION,),
}

LARGE_VALUE_ACTION = _action(
    "bank_fraud_desk",
    "Also call your bank's fraud/dispute desk directly",
    "For amounts of ₹1,00,000 or more, banks often escalate faster through "
    "the fraud desk than through the general helpline queue. Ask to speak to "
    "the fraud/dispute team and note the reference they give you.",
)

# Full rules table keyed on (urgency, payment_method) — no silent fallthrough.
ACTION_PLAN_RULES: dict[tuple[Urgency, PaymentMethod], tuple[ActionItem, ...]] = {
    (urgency, method): URGENCY_ACTIONS[urgency] + PAYMENT_ACTIONS[method]
    for urgency in Urgency
    for method in PaymentMethod
}


# --- Pure functions (unit-tested) --------------------------------------------


def _as_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _as_float(amount: float | Decimal | None) -> float | None:
    if amount is None:
        return None
    return float(amount)


def _time_urgency(elapsed: timedelta) -> Urgency:
    if elapsed < timedelta(0):
        return Urgency.critical
    for duration, urgency in URGENCY_BY_ELAPSED:
        if elapsed <= duration:
            return urgency
    return FALLBACK_URGENCY


def _bump_urgency(urgency: Urgency) -> Urgency:
    rank = URGENCY_RANK[urgency]
    ceiling = max(RANK_TO_URGENCY)
    return RANK_TO_URGENCY[min(rank + 1, ceiling)]


def is_large_amount(amount: float | Decimal | None) -> bool:
    value = _as_float(amount)
    if value is None:
        return False
    return value >= LARGE_AMOUNT_THRESHOLD


def compute_urgency(
    occurred_at: datetime,
    amount: float | Decimal | None,
    *,
    now: datetime | None = None,
) -> Urgency:
    """
    Time since the transaction is the primary signal. Amount is a secondary
    modifier: at/above LARGE_AMOUNT_THRESHOLD, bump one tier.
    """
    clock = _as_utc(now or datetime.now(timezone.utc))
    elapsed = clock - _as_utc(occurred_at)
    urgency = _time_urgency(elapsed)
    if is_large_amount(amount):
        urgency = _bump_urgency(urgency)
    return urgency


def build_action_list(
    urgency: Urgency,
    payment_method: PaymentMethod,
    *,
    large_amount: bool = False,
) -> list[ActionItem]:
    key = (urgency, payment_method)
    actions = list(ACTION_PLAN_RULES[key])
    if large_amount:
        actions.append(LARGE_VALUE_ACTION)
    if not actions:
        raise RuntimeError(f"Empty action plan for {key}")
    return actions


def format_inr(amount: float | Decimal) -> str:
    value = _as_float(amount)
    assert value is not None
    sign = "-" if value < 0 else ""
    rupees, paise = f"{abs(value):.2f}".split(".")
    if len(rupees) <= 3:
        grouped = rupees
    else:
        last3 = rupees[-3:]
        rest = rupees[:-3]
        parts: list[str] = []
        while rest:
            parts.append(rest[-2:])
            rest = rest[:-2]
        grouped = ",".join(reversed(parts)) + "," + last3
    return f"{sign}{grouped}.{paise}"


def format_occurred_at(occurred_at: datetime | None) -> str:
    if occurred_at is None:
        return "Not provided"
    local = _as_utc(occurred_at).astimezone(IST)
    return local.strftime("%d %b %Y, %I:%M %p IST")


def _format_detail_key(key: str) -> str:
    return key.replace("_", " ").strip().title()


def _format_detail_value(value: object) -> str:
    if value is None:
        return "Not provided"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, list):
        values = [str(item).strip() for item in value if str(item).strip()]
        return ", ".join(values) if values else "Not provided"
    text = str(value).strip()
    return text or "Not provided"


def render_complaint_draft(
    *,
    incident_type: IncidentType,
    occurred_at: datetime | None,
    amount: float | Decimal | None,
    payment_method: PaymentMethod,
    transaction_id: str | None,
    other_crime_sub_category: OtherCrimeSubCategory | None = None,
    details: dict | None = None,
    urgency: Urgency,
    actions: list[ActionItem],
) -> str:
    amount_text = f"₹{format_inr(amount)}" if amount is not None else "Not provided"
    txn = (transaction_id or "").strip() or MISSING_UTR_TEXT
    detail_lines: list[str] = []
    if other_crime_sub_category is not None:
        detail_lines.append(
            f"Other cyber crime category: {OTHER_CRIME_SUB_CATEGORY_LABELS[other_crime_sub_category]}"
        )
    if details:
        for key, value in details.items():
            detail_lines.append(f"{_format_detail_key(key)}: {_format_detail_value(value)}")
    numbered = "\n".join(
        f"{index}. {item.title} — {item.why}"
        for index, item in enumerate(actions, start=1)
    )
    summary = (
        "COMPLAINT SUMMARY (draft — verify before submitting to cybercrime.gov.in)\n"
        "\n"
        f"Incident type: {INCIDENT_TYPE_LABELS[incident_type]}\n"
        f"Date & time of transaction: {format_occurred_at(occurred_at)}\n"
        f"Amount involved: {amount_text}\n"
        f"Payment method: {PAYMENT_METHOD_LABELS[payment_method]}\n"
        f"Transaction ID / UTR: {txn}\n"
        f"Urgency assessment: {URGENCY_BADGE[urgency]}\n"
    )
    if detail_lines:
        summary += "\n".join(detail_lines) + "\n"
    return summary + (
        "\n"
        "Recommended immediate actions:\n"
        f"{numbered}\n"
        "\n"
        "---\n"
        "This summary is generated from the details you provided and is meant to help you\n"
        "file a complaint faster at cybercrime.gov.in or via the 1930 helpline. It is not a\n"
        "legal document and has not been submitted anywhere on your behalf.\n"
    )


def build_action_plan(incident: Incident) -> ActionPlanResponse:
    if incident.incident_type in {IncidentType.women_children, IncidentType.other_cyber_crime}:
        return build_category_action_plan(incident)
    urgency = incident.urgency
    large = is_large_amount(incident.amount)
    actions = build_action_list(
        urgency, incident.payment_method, large_amount=large
    )
    body = render_complaint_draft(
        incident_type=incident.incident_type,
        occurred_at=incident.occurred_at or incident.incident_time,
        amount=incident.amount,
        payment_method=incident.payment_method,
        transaction_id=incident.transaction_id,
        other_crime_sub_category=incident.other_crime_sub_category,
        details=incident.details,
        urgency=urgency,
        actions=actions,
    )
    return ActionPlanResponse(
        urgency=urgency,
        urgency_label=URGENCY_BADGE[urgency],
        core_message=CORE_MESSAGES[urgency],
        large_amount=large,
        actions=actions,
        complaint_draft=ComplaintDraft(body=body),
    )


def _yes(value: object) -> bool:
    return value is True or str(value).strip().lower() in {"yes", "true"}


def _recent(occurred_at: datetime | None, now: datetime | None = None) -> bool:
    return occurred_at is not None and _as_utc(now or datetime.now(timezone.utc)) - _as_utc(occurred_at) <= timedelta(days=7)


def _level(score: int, thresholds: dict[str, int]) -> Urgency:
    if score >= thresholds["critical"]:
        return Urgency.critical
    if score >= thresholds["high"]:
        return Urgency.high
    if score >= thresholds["medium"]:
        return Urgency.medium
    return Urgency.low


def compute_women_children_urgency(incident: Incident, *, now: datetime | None = None) -> tuple[Urgency, int]:
    details = incident.details or {}
    subtype = (incident.incident_subtype or details.get("incident_subtype") or "").lower()
    affected = (incident.affected_person_type or details.get("affected_person_type") or "").lower()
    score = 0
    score += 5 if _yes(incident.immediate_danger or details.get("immediate_danger")) else 0
    score += 3 if "child" in affected or "child" in subtype else 0
    score += 3 if _yes(incident.threat_or_blackmail or details.get("threat_or_blackmail")) else 0
    score += 2 if "intimate" in subtype or "private" in subtype else 0
    score += 2 if _yes(incident.content_still_online or details.get("content_still_online")) else 0
    score += 1 if _recent(incident.occurred_at or incident.incident_time, now) else 0
    return _level(score, WOMEN_CHILDREN_THRESHOLDS), score


def compute_other_cyber_urgency(incident: Incident, *, now: datetime | None = None) -> tuple[Urgency, int]:
    details = incident.details or {}
    subtype = (incident.incident_subtype or details.get("incident_subtype") or "").lower()
    score = 0
    score += 3 if "hack" in subtype or "impersonat" in subtype or (incident.account_access or "").lower() == "no" else 0
    score += 4 if _yes(incident.attacker_active or details.get("attacker_active")) else 0
    score += 2 if _yes(incident.sensitive_information_exposed or details.get("sensitive_information_exposed")) else 0
    score += 3 if "phishing" in subtype and _yes(details.get("credentials_entered")) else 0
    score += 3 if "threat" in subtype else 0
    score += 2 if "malware" in subtype or "device" in (incident.account_type or "").lower() else 0
    score += 1 if _recent(incident.occurred_at or incident.incident_time, now) else 0
    return _level(score, OTHER_CYBER_THRESHOLDS), score


def _category_actions(incident: Incident) -> list[ActionItem]:
    subtype = (incident.incident_subtype or "").lower()
    actions: list[ActionItem] = []
    if incident.incident_type == IncidentType.women_children:
        if incident.immediate_danger:
            actions.append(_action("safety_first", "Prioritize immediate personal safety", "Move to a safe place and contact trusted local help. CyberSOS is not an emergency service.", url="https://112.gov.in", url_label="Official emergency information"))
        if incident.threat_or_blackmail:
            actions.append(_action("do_not_send", "Do not send more money, images, passwords, or personal information", "Additional responses can increase risk and rarely resolve threats."))
        actions.extend([
            _action("preserve_evidence", "Preserve screenshots, messages, and account details", "Keep original messages, URLs, timestamps, and profile identifiers without redistributing sensitive content."),
            _action("report_platform", "Report the account or content through the platform", "Use the platform's report and block tools when doing so is safe."),
            _action("official_report", "File through the official cybercrime reporting channel", "This creates a record for appropriate authorities.", url=CYBERCRIME_PORTAL_URL, url_label="cybercrime.gov.in"),
        ])
        return actions
    if "hack" in subtype:
        actions.extend([_action("secure_account", "Secure the affected account from a trusted device", "Change the password and enable MFA; never share the password with CyberSOS."), _action("review_sessions", "Review active sessions and devices", "Sign out unfamiliar sessions and preserve evidence of unauthorized access."), _action("official_report", "Report the compromise", "Use the official cybercrime channel for a formal record.", url=CYBERCRIME_PORTAL_URL, url_label="cybercrime.gov.in")])
    elif "phishing" in subtype:
        actions.append(_action("secure_account", "Secure the affected account from a trusted device", "Do this immediately if any credentials were entered." ) if _yes((incident.details or {}).get("credentials_entered")) else _action("avoid_link", "Do not open the link again", "Preserve the message and URL, then report the phishing site or message."))
        actions.extend([_action("preserve_evidence", "Preserve the phishing message and URL", "Keep the sender, URL, and timestamps without interacting further."), _action("official_report", "Report the incident", "Use the official cybercrime reporting channel.", url=CYBERCRIME_PORTAL_URL, url_label="cybercrime.gov.in")])
    elif "malware" in subtype:
        actions.extend([_action("disconnect_device", "Disconnect the device from the network if appropriate", "Avoid entering sensitive credentials on a potentially compromised device."), _action("trusted_scan", "Run trusted security checks", "Use your device's established security tools; avoid unverified removal instructions."), _action("preserve_evidence", "Preserve relevant evidence", "Keep suspicious messages, files, and timestamps." )])
    elif "impersonat" in subtype:
        actions.extend([_action("preserve_profile", "Save the impersonating profile URL and details", "Capture identifiers before the profile changes."), _action("report_profile", "Report the account to the platform", "Use the platform's impersonation report flow."), _action("warn_contacts", "Warn relevant contacts if necessary", "Use a trusted channel and avoid engaging the impersonator." )])
    else:
        actions.append(_action("preserve_evidence", "Preserve messages, screenshots, URLs, and account details", "Keep the original evidence without sharing secrets."))
    actions.append(_action("official_report", "Report the incident through the official channel", "This creates a formal record.", url=CYBERCRIME_PORTAL_URL, url_label="cybercrime.gov.in"))
    return actions


def build_category_action_plan(incident: Incident) -> ActionPlanResponse:
    urgency, score = (compute_women_children_urgency(incident) if incident.incident_type == IncidentType.women_children else compute_other_cyber_urgency(incident))
    actions = _category_actions(incident)
    message = "Your immediate safety comes first." if incident.immediate_danger else "Your answers indicate that this situation may require prompt action."
    return ActionPlanResponse(urgency=urgency, urgency_label=URGENCY_BADGE[urgency], core_message=message, large_amount=False, actions=actions, complaint_draft=ComplaintDraft(body=render_complaint_draft(incident_type=incident.incident_type, occurred_at=incident.occurred_at or incident.incident_time, amount=None, payment_method=PaymentMethod.unknown, transaction_id=None, other_crime_sub_category=incident.other_crime_sub_category, details=incident.details, urgency=urgency, actions=actions)))


# --- Persistence -------------------------------------------------------------


def create_incident(db: Session, payload: IncidentCreate) -> Incident:
    incident = Incident(
        incident_type=payload.incident_type,
        payment_method=payload.payment_method,
        amount=payload.amount,
        incident_time=payload.incident_time,
        occurred_at=payload.incident_time,
        other_crime_sub_category=payload.other_crime_sub_category,
        details=payload.details,
        incident_subtype=payload.incident_subtype,
        affected_person_type=payload.affected_person_type,
        platform=payload.platform,
        account_type=payload.account_type,
        immediate_danger=payload.immediate_danger,
        threat_or_blackmail=payload.threat_or_blackmail,
        content_still_online=payload.content_still_online,
        account_access=payload.account_access,
        attacker_active=payload.attacker_active,
        sensitive_information_exposed=payload.sensitive_information_exposed,
        evidence_types=payload.evidence_types,
        urgency=Urgency.medium,
        status=IncidentStatus.draft,
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)
    return incident


def get_incident(db: Session, incident_id: uuid.UUID) -> Incident | None:
    return db.get(Incident, incident_id)


def update_incident_details(
    db: Session, incident: Incident, payload: IncidentDetailsUpdate
) -> Incident:
    incident.other_crime_sub_category = payload.other_crime_sub_category
    incident.details = payload.details
    db.commit()
    db.refresh(incident)
    return incident


def save_evidence(
    db: Session,
    incident: Incident,
    upload: UploadFile,
    storage_dir: str,
) -> Evidence:
    original_filename = Path(upload.filename or "evidence").name[:255]
    stored_filename = f"{uuid.uuid4().hex}{Path(original_filename).suffix[:20]}"
    directory = Path(storage_dir)
    directory.mkdir(parents=True, exist_ok=True)
    destination = directory / stored_filename
    size_bytes = 0
    try:
        with destination.open("wb") as target:
            while chunk := upload.file.read(1024 * 1024):
                size_bytes += len(chunk)
                if size_bytes > 10 * 1024 * 1024:
                    raise ValueError("Evidence files must be 10 MB or smaller.")
                target.write(chunk)
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    evidence = Evidence(
        incident_id=incident.id,
        original_filename=original_filename,
        stored_filename=stored_filename,
        content_type=upload.content_type,
        size_bytes=size_bytes,
    )
    db.add(evidence)
    db.commit()
    db.refresh(evidence)
    return evidence


def triage_incident(
    db: Session,
    incident: Incident,
    payload: TriageRequest,
    *,
    now: datetime | None = None,
) -> Incident:
    clock = _as_utc(now or datetime.now(timezone.utc))
    occurred_at = _as_utc(payload.occurred_at)
    urgency = compute_urgency(occurred_at, payload.amount, now=clock)

    incident.incident_type = payload.incident_type
    incident.occurred_at = occurred_at
    incident.incident_time = occurred_at
    incident.amount = payload.amount
    incident.payment_method = payload.payment_method
    incident.transaction_id = payload.transaction_id
    incident.other_crime_sub_category = payload.other_crime_sub_category
    incident.details = payload.details
    incident.incident_subtype = payload.incident_subtype
    incident.affected_person_type = payload.affected_person_type
    incident.platform = payload.platform
    incident.account_type = payload.account_type
    incident.immediate_danger = payload.immediate_danger
    incident.threat_or_blackmail = payload.threat_or_blackmail
    incident.content_still_online = payload.content_still_online
    incident.account_access = payload.account_access
    incident.attacker_active = payload.attacker_active
    incident.sensitive_information_exposed = payload.sensitive_information_exposed
    incident.evidence_types = payload.evidence_types
    if payload.incident_type == IncidentType.women_children:
        urgency, score = compute_women_children_urgency(incident, now=clock)
    elif payload.incident_type == IncidentType.other_cyber_crime and payload.incident_subtype:
        urgency, score = compute_other_cyber_urgency(incident, now=clock)
    else:
        urgency, score = urgency, None
    incident.urgency = urgency
    incident.urgency_score = score
    incident.urgency_computed_at = clock
    incident.status = IncidentStatus.action_required

    db.commit()
    db.refresh(incident)
    return incident
