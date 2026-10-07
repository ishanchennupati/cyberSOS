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
    if version == '1.2.0' or version is None and (facts.kind == 'incident_understanding' or facts.money_lost is not None):
        return evaluate_current(facts, as_of=as_of)
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


def evaluate_current(facts: IncidentFacts, *, as_of: datetime) -> ResponsePlan:
    """Shared Phase 5 policy. Hints, absent timing and candidates grant no action authority."""
    from app.domain.facts import UnknownFinancialAuthorizationFacts
    financial = facts.money_lost is True and 'financial' in facts.signals
    banking = financial and (facts.bank_involved is True or facts.payment_method.value in
        {'upi', 'bank_transfer', 'net_banking', 'debit_card', 'credit_card'})
    base_facts = facts if facts.kind != 'incident_understanding' else UnknownFinancialAuthorizationFacts(
        **facts.model_dump(exclude={'kind', 'authorization'}))
    base = PLAYBOOKS[(base_facts.kind, '1.1.0')].evaluate(base_facts, as_of=as_of)
    clock = base.evaluated_at
    reported = facts.occurred_at or (facts.time_window.start if facts.time_window else None)
    if reported and reported.tzinfo is None:
        reported = reported.replace(tzinfo=timezone.utc)
    recent = bool(reported and 0 <= (clock - reported).total_seconds() < 86400)
    active_financial = banking and (facts.ongoing_loss is True or facts.remote_access is True or facts.transaction_status == 'pending')
    urgency = Urgency.critical if facts.immediate_danger is True or active_financial or financial and recent else Urgency.high if facts.account_compromised is True or facts.remote_access is True else Urgency.medium
    relevant = bool(facts.signals) or facts.blackmail is True or facts.private_image_threat is True
    actions = []
    for action in base.actions:
        if action.id.startswith('contact_bank') or action.id == 'report_ongoing_access':
            if not banking:
                continue
        elif action.id == 'call_1930':
            if not financial:
                continue
        elif not relevant:
            continue
        instruction = action.instruction
        if action.id == 'contact_bank_unknown':
            instruction = 'Describe the reported payment and what you know about its approval. Ask your bank about applicable protective and complaint steps. Do not share passwords, PINs or OTPs.'
        actions.append(action.model_copy(update={'priority': urgency, 'instruction': instruction,
            'critical': bool(action.critical and (recent or active_financial or banking and (facts.account_compromised is True or facts.credentials_exposed is True))),
            'minimum_facts': ('money_lost', 'signals') if action.id == 'call_1930' else
                ('money_lost','signals','bank_involved' if facts.bank_involved is True else 'payment_method') if action.id.startswith('contact_bank') else action.minimum_facts}))

    def add(ident, phase, title, instruction, why, source_id, minimum, critical=False, phone=None):
        reference = source(source_id)
        actions.append(ResponseAction(id=ident, phase=phase, priority=urgency, order=len(actions)+1,
            title=title, instruction=instruction, why=why, minimum_facts=minimum,
            official_source_id=source_id, critical=critical, phone=phone,
            applicability='Supported current citizen facts: ' + ', '.join(minimum),
            url=reference.official_url, url_label='External official source'))

    if facts.immediate_danger is True:
        add('contact_112', ActionPhase.contain, 'Get emergency help for the danger you reported',
            "Call 112 for immediate physical danger in India. CyberSOS cannot contact emergency services for you.",
            'You reported immediate physical danger; this is separate from financial reporting.',
            'INDIA-EMERGENCY', ('immediate_danger',), True, '112')
    platform_reporting = (facts.platform or '').casefold() in {'instagram','facebook','youtube','twitter','x'}
    if platform_reporting and (set(facts.signals) & {'harassment', 'threats', 'impersonation'} or facts.blackmail is True or facts.private_image_threat is True):
        add('report_platform_abuse', ActionPhase.report, 'Report the abusive content or profile on the platform',
            'Use the affected platform’s reporting or flagging option for the content or profile. Keep safe identifiers and non-explicit threat text; do not upload intimate images or child abuse material here.',
            'Platform reporting can flag content for its own review; removal is not guaranteed.',
            'NCRP-SAFE-RECORDS', ('signals','platform'))
    if facts.account_compromised is True and (facts.platform or '').casefold() in {'google', 'gmail', 'google account'}:
        add('secure_google_account', ActionPhase.contain, 'Use Google’s account recovery and security guidance',
            'Open Google’s official account recovery and security guide. Review unfamiliar activity and devices there. Enter account credentials only on the official service, never in CyberSOS.',
            'You reported someone else accessing a Google account. Recovery and security checks belong on the account provider.',
            'GOOGLE-ACCOUNT', ('account_compromised', 'platform'), True)
    actions = tuple(a.model_copy(update={'order': i+1}) for i, a in enumerate(actions))
    return base.model_copy(update={'playbook_id': facts.kind, 'playbook_version': '1.2.0', 'facts': facts,
        'urgency': urgency, 'actions': actions,
        'reasons': ('Priority follows supported timing and current risks. Unknown timing does not establish urgency.',),
        'sources': tuple(source(s) for s in dict.fromkeys(a.official_source_id for a in actions if a.official_source_id))})
