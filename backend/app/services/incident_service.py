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
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy.orm import Session

from app.models.incident import (
    Incident,
    IncidentStatus,
    IncidentType,
    PaymentMethod,
    Urgency,
)
from app.schemas.incident import (
    ActionItem,
    ActionPlanResponse,
    ComplaintDraft,
    IncidentCreate,
    TriageRequest,
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
    IncidentType.financial_fraud: "UPI / financial fraud",
    IncidentType.phishing: "Phishing / fake website",
    IncidentType.identity_theft: "Identity theft",
    IncidentType.social_media: "Social media / impersonation",
    IncidentType.job_scam: "Job or investment scam",
    IncidentType.other: "Other cyber incident",
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


def render_complaint_draft(
    *,
    incident_type: IncidentType,
    occurred_at: datetime | None,
    amount: float | Decimal | None,
    payment_method: PaymentMethod,
    transaction_id: str | None,
    urgency: Urgency,
    actions: list[ActionItem],
) -> str:
    amount_text = f"₹{format_inr(amount)}" if amount is not None else "Not provided"
    txn = (transaction_id or "").strip() or MISSING_UTR_TEXT
    numbered = "\n".join(
        f"{index}. {item.title} — {item.why}"
        for index, item in enumerate(actions, start=1)
    )
    return (
        "COMPLAINT SUMMARY (draft — verify before submitting to cybercrime.gov.in)\n"
        "\n"
        f"Incident type: {INCIDENT_TYPE_LABELS[incident_type]}\n"
        f"Date & time of transaction: {format_occurred_at(occurred_at)}\n"
        f"Amount involved: {amount_text}\n"
        f"Payment method: {PAYMENT_METHOD_LABELS[payment_method]}\n"
        f"Transaction ID / UTR: {txn}\n"
        f"Urgency assessment: {URGENCY_BADGE[urgency]}\n"
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


# --- Persistence -------------------------------------------------------------


def create_incident(db: Session, payload: IncidentCreate) -> Incident:
    incident = Incident(
        incident_type=payload.incident_type,
        payment_method=payload.payment_method,
        amount=payload.amount,
        incident_time=payload.incident_time,
        occurred_at=payload.incident_time,
        urgency=Urgency.medium,
        status=IncidentStatus.draft,
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)
    return incident


def get_incident(db: Session, incident_id: uuid.UUID) -> Incident | None:
    return db.get(Incident, incident_id)


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
    incident.urgency = urgency
    incident.urgency_computed_at = clock
    incident.status = IncidentStatus.action_required

    db.commit()
    db.refresh(incident)
    return incident
