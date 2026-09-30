"""Complaint formatting and display labels; no persistence or action selection."""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from app.models.incident import IncidentType, OtherCrimeSubCategory, PaymentMethod, Urgency
from app.schemas.incident import ActionItem

try:
    IST = ZoneInfo("Asia/Kolkata")
except ZoneInfoNotFoundError:
    IST = timezone(timedelta(hours=5, minutes=30), name="IST")

MISSING_UTR_TEXT = "Not available — check bank SMS/statement"



URGENCY_BADGE: dict[Urgency, str] = {
    Urgency.critical: "ACT NOW",
    Urgency.high: "ACT TODAY",
    Urgency.medium: "ACT THIS WEEK",
    Urgency.medium_low: "FILE WHEN READY",
    Urgency.standard: "FILE WHEN READY",
    Urgency.low: "FILE WHEN READY",
}



CORE_MESSAGES: dict[Urgency, str] = {
    Urgency.critical: "Report promptly to your bank and 1930. Do not wait to finish this form.",
    Urgency.high: "Prompt reporting is important. Contact your bank and report the incident.",
    Urgency.medium: "Report the incident and preserve your records. CyberSOS cannot predict recovery.",
    Urgency.medium_low: "Report the incident and preserve your records. CyberSOS cannot predict recovery.",
    Urgency.standard: "You can still report the incident. CyberSOS cannot predict recovery.",
    Urgency.low: "You can still report the incident. CyberSOS cannot predict recovery.",
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



def _as_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)



def _as_float(amount: float | Decimal | None) -> float | None:
    if amount is None:
        return None
    return float(amount)



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

