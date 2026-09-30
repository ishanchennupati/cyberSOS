"""Existing nonfinancial category behavior, separate from versioned playbooks."""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from app.models.incident import Incident, IncidentType, PaymentMethod, Urgency
from app.schemas.incident import ActionItem, ActionPlanResponse, ComplaintDraft
from app.domain.response import ActionPhase
from app.domain.sources import source
from app.rules.action_rules import determine_other_cyber_plan, determine_women_children_plan
from app.services.incident_presentation import URGENCY_BADGE, _as_utc, render_complaint_draft

CYBERCRIME_PORTAL_URL = source("NCRP-REPORT").official_url

WOMEN_CHILDREN_THRESHOLDS = {"medium": 2, "high": 4, "critical": 7}



OTHER_CYBER_THRESHOLDS = {"medium": 3, "high": 5, "critical": 7}



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
        instruction=title, phase=ActionPhase.report, priority=Urgency.medium, order=1,
        minimum_facts=("incident_type",), applicability="Existing legacy category guidance",
        official_source_id=next((key for key in ("NCRP-REPORT", "INDIA-EMERGENCY") if source(key).official_url == url), None),
        phone=phone,
        url=url,
        url_label=url_label,
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
            actions.append(_action("safety_first", "Prioritize immediate personal safety", "Move to a safe place and contact trusted local help. CyberSOS is not an emergency service.", url=source("INDIA-EMERGENCY").official_url, url_label="Official emergency information"))
        if incident.threat_or_blackmail:
            actions.append(_action("do_not_send", "Do not send more money, images, passwords, or personal information", "Do not share more sensitive information in response to threats. Seek trusted support."))
        actions.extend([
            _action("preserve_evidence", "Preserve screenshots, messages, and account details", "Keep original messages, URLs, timestamps, and profile identifiers without redistributing sensitive content."),
            _action("report_platform", "Report the account or content through the platform", "Use the platform's report and block tools when doing so is safe."),
            _action("official_report", "File through the official cybercrime reporting channel", "Submit the report yourself and keep any reference you receive. CyberSOS does not confirm official receipt.", url=CYBERCRIME_PORTAL_URL, url_label="cybercrime.gov.in"),
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
    actions.append(_action("official_report", "Report the incident through the official channel", "Submit the report yourself and keep any reference you receive. CyberSOS does not confirm official receipt.", url=CYBERCRIME_PORTAL_URL, url_label="cybercrime.gov.in"))
    return actions



def build_category_action_plan(incident: Incident) -> ActionPlanResponse:
    if incident.urgency_reasons:
        urgency = incident.urgency
        score = incident.urgency_score
        reasons = incident.urgency_reasons
        severity = incident.severity or urgency
        ongoing_risk = incident.ongoing_risk or urgency
    elif incident.incident_type == IncidentType.women_children:
        category_plan = determine_women_children_plan(incident.incident_subtype, incident.affected_person_type, incident.immediate_danger, incident.threat_or_blackmail, incident.content_still_online, incident.details)
        urgency, score, reasons, severity, ongoing_risk = category_plan.priority, None, category_plan.reasons, category_plan.severity, category_plan.ongoing_risk
    else:
        category_plan = determine_other_cyber_plan(incident.incident_subtype, incident.account_access, incident.attacker_active, incident.sensitive_information_exposed, incident.details)
        urgency, score, reasons, severity, ongoing_risk = category_plan.priority, None, category_plan.reasons, category_plan.severity, category_plan.ongoing_risk
    actions = _category_actions(incident)
    message = "Your immediate safety comes first." if incident.immediate_danger else "Based on the information provided, this incident may require prompt action."
    return ActionPlanResponse(urgency=urgency, urgency_label=URGENCY_BADGE[urgency], core_message=message, large_amount=False, actions=actions, complaint_draft=ComplaintDraft(body=render_complaint_draft(incident_type=incident.incident_type, occurred_at=incident.occurred_at or incident.incident_time, amount=None, payment_method=PaymentMethod.unknown, transaction_id=None, other_crime_sub_category=incident.other_crime_sub_category, details=incident.details, urgency=urgency, actions=actions)), severity=severity, ongoing_risk=ongoing_risk, urgency_reasons=reasons)

