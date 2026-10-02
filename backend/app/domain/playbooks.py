"""Versioned deterministic financial actions. No provider or network access."""
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from types import MappingProxyType

from app.domain.facts import FinancialFacts, FactField, IncidentFacts
from app.domain.response import ActionPhase, FactPriority, FactRequirement, ResponseAction, ResponsePlan
from app.domain.sources import source
from app.models.incident import Urgency

VERSION = "1.0.0"
FIELDS = (
    FactRequirement(field=FactField.authorization, priority=FactPriority.critical, question="Did you approve the payment, or did money move without your approval?"),
    FactRequirement(field=FactField.ongoing_loss, priority=FactPriority.critical, question="Is money still moving or are you being asked to pay more?"),
    FactRequirement(field=FactField.remote_access, priority=FactPriority.critical, question="Does someone still have remote access to your device?"),
    FactRequirement(field=FactField.account_compromised, priority=FactPriority.critical, question="Can someone else still access the account?"),
    FactRequirement(field=FactField.credentials_exposed, priority=FactPriority.critical, question="Were access credentials exposed? Do not enter the credentials themselves."),
    FactRequirement(field=FactField.occurred_at, priority=FactPriority.supporting, question="Approximately when did this happen?"),
    FactRequirement(field=FactField.payment_method, priority=FactPriority.supporting, question="How was the payment made, if you know?"),
    FactRequirement(field=FactField.transaction_status, priority=FactPriority.supporting, question="Does your payment record say pending or completed?"),
    FactRequirement(field=FactField.amount, priority=FactPriority.reporting, question="What amount should be included in the report, if known?"),
    FactRequirement(field=FactField.transaction_id, priority=FactPriority.reporting, question="Do you have a transaction reference? You can add it later."),
    FactRequirement(field=FactField.evidence_available, priority=FactPriority.optional, question="Would you like to preserve safe supporting records?"),
)


def next_unanswered_fact(facts: FinancialFacts) -> FactRequirement | None:
    return next((r for r in FIELDS if getattr(facts, r.field.value) in (None, "unknown")), None)


@dataclass(frozen=True)
class ResponsePlaybook:
    id: str
    version: str
    authorization: str
    bank_action_id: str
    bank_title: str
    bank_instruction: str
    bank_source: str
    fact_priorities: tuple[FactRequirement, ...] = FIELDS

    def evaluate(self, facts: IncidentFacts, *, as_of: datetime) -> ResponsePlan:
        if facts.authorization != self.authorization:
            raise ValueError("Facts do not match this playbook")
        clock = as_of.replace(tzinfo=timezone.utc) if as_of.tzinfo is None else as_of.astimezone(timezone.utc)
        reported_time = facts.occurred_at
        if self.version == '1.1.0' and reported_time is None and facts.time_window is not None:
            # Earliest supported time is conservative; no exact timestamp is invented.
            reported_time = facts.time_window.start
        age = None if reported_time is None else clock - (reported_time.replace(tzinfo=timezone.utc) if reported_time.tzinfo is None else reported_time.astimezone(timezone.utc))
        urgency = Urgency.high if age is None else Urgency.critical if age.total_seconds() < 86400 else Urgency.high if age.total_seconds() < 259200 else Urgency.medium if age.total_seconds() < 604800 else Urgency.low
        ongoing = facts.ongoing_loss is True or facts.remote_access is True
        exposed = facts.account_compromised is True or facts.credentials_exposed is True
        if ongoing or facts.transaction_status == "pending":
            urgency = Urgency.critical
        elif exposed and urgency in (Urgency.medium, Urgency.low):
            urgency = Urgency.high
        actions = []
        def add(ident, phase, title, instruction, why, minimum=("kind",), source_id=None, critical=False, phone=None, applicability="Reported financial incident"):
            reference = source(source_id) if source_id else None
            actions.append(ResponseAction(id=ident, phase=phase, priority=urgency, order=len(actions)+1,
                title=title, instruction=instruction, why=why, minimum_facts=minimum,
                official_source_id=source_id, critical=critical, phone=phone, applicability=applicability,
                url=reference.official_url if reference else None, url_label="External official source" if reference else None))
        if ongoing or exposed:
            add("report_ongoing_access", ActionPhase.contain, "Tell your bank about ongoing access or loss",
                "Explain the reported exposure and ask about steps to protect the affected account. Do not share passwords, PINs or OTPs.",
                "Protective steps should address the ongoing risk you reported.",
                minimum=tuple(name for name in ("ongoing_loss", "remote_access", "account_compromised", "credentials_exposed") if getattr(facts, name) is True),
                source_id="NPCI-BANK", critical=True, applicability="At least one recorded ongoing-risk fact is true")
        add(self.bank_action_id, ActionPhase.contain, self.bank_title, self.bank_instruction,
            "Tell the bank what actually happened; available procedures depend on the incident.",
            minimum=("kind", "authorization"), source_id=self.bank_source, critical=True)
        add("call_1930", ActionPhase.report, "Call 1930 to report financial cyber fraud",
            "Report promptly. Do not wait to find an exact amount, transaction ID or upload.",
            "1930 is an official reporting-assistance channel; CyberSOS does not place this call.",
            source_id="MHA-1930", critical=True, phone="1930")
        add("preserve_evidence", ActionPhase.preserve, "Preserve safe records",
            "Keep transaction references, non-sensitive messages and dates. Do not upload credentials, identity documents or explicit intimate material.",
            "Records help you describe the incident without recreating details later.")
        add("file_cybercrime", ActionPhase.report, "Report on cybercrime.gov.in",
            "Review your information and submit it yourself on the external official portal. Keep any reference you actually receive.",
            "A CyberSOS draft is preparation, not official submission or confirmation.", source_id="NCRP-REPORT")
        add("record_follow_up", ActionPhase.follow_up, "Record your own follow-up",
            "Record which steps you took and any reference or reply you received. A checked step means only that you say you completed it.",
            "Local completion records do not confirm bank, police or government action.")
        sources = tuple(source(ident) for ident in dict.fromkeys(a.official_source_id for a in actions if a.official_source_id))
        return ResponsePlan(playbook_id=self.id, playbook_version=self.version, fact_schema_version=facts.fact_schema_version,
            evaluated_at=clock, facts=facts, urgency=urgency,
            reasons=("Ongoing risk is reported." if ongoing or exposed else "Priority reflects reported timing; no recovery prediction is made.",),
            actions=tuple(actions), sources=sources)


PLAYBOOKS = MappingProxyType({(p.id, p.version): p for p in (
    ResponsePlaybook("financial_scam_transfer", VERSION, "authorized", "contact_bank_scam",
        "Tell your bank you approved a payment after deception",
        "Explain that you made the payment because of deception. Ask about applicable fraud-reporting and protective steps; do not describe it as an unauthorized debit.", "NPCI-BANK"),
    ResponsePlaybook("unauthorized_financial_transaction", VERSION, "unauthorized", "contact_bank_unauthorized",
        "Report the unauthorized transaction to your bank",
        "Tell your bank promptly that you did not authorize the transaction. Ask about protecting the account and the complaint process.", "RBI-UNAUTHORIZED"),
    ResponsePlaybook("financial_authorization_unknown", VERSION, "unknown", "contact_bank_unknown",
        "Contact your bank about the reported payment",
        "Describe what you know and say you are unsure whether the payment was authorized. Ask about protective steps without assuming refund eligibility.", "NPCI-BANK"),
)})


PLAYBOOKS = MappingProxyType({**PLAYBOOKS,
    **{(p.id, '1.1.0'): replace(p, version='1.1.0') for p in PLAYBOOKS.values()}})


def evaluate(facts: IncidentFacts, *, as_of: datetime, version: str | None = None) -> ResponsePlan:
    version = version or ('1.1.0' if facts.time_window is not None or facts.kind == 'incident_understanding' else VERSION)
    if facts.kind == 'incident_understanding':
        # Reuse approved general preservation/report/follow-up text and sources.
        # No bank action or financial helpline without an established loss.
        from app.domain.facts import UnknownFinancialAuthorizationFacts
        base = PLAYBOOKS[('financial_authorization_unknown', version)].evaluate(
            UnknownFinancialAuthorizationFacts(), as_of=as_of)
        applicable = bool(facts.signals) or facts.money_lost is False
        actions = tuple(a.model_copy(update={'order': i + 1, 'minimum_facts': ('kind',),
            'applicability': 'Reported non-financial incident or scam attempt'}) for i, a in enumerate(
                a for a in base.actions if applicable and a.id in {'preserve_evidence', 'file_cybercrime', 'record_follow_up'}))
        return base.model_copy(update={'playbook_id': 'incident_understanding', 'facts': facts,
            'urgency': Urgency.medium, 'actions': actions, 'reasons': ('Working incident understanding; financial loss is not established.',),
            'sources': tuple(s for s in base.sources if any(a.official_source_id == s.id for a in actions))})
    return PLAYBOOKS[(facts.kind, version)].evaluate(facts, as_of=as_of)
