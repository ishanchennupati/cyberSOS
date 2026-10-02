from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StrictBool, TypeAdapter, model_validator
from app.models.incident import PaymentMethod

FACT_SCHEMA_VERSION = "1.0"


class FactField(str, Enum):
    money_lost = "money_lost"
    authorization = "authorization"
    occurred_at = "occurred_at"
    amount = "amount"
    payment_method = "payment_method"
    transaction_id = "transaction_id"
    transaction_status = "transaction_status"
    account_compromised = "account_compromised"
    remote_access = "remote_access"
    credentials_exposed = "credentials_exposed"
    ongoing_loss = "ongoing_loss"
    evidence_available = "evidence_available"


class FactProvenance(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    field: FactField | Literal['currency', 'payment_app', 'claimed_organization', 'claimed_person', 'identifiers', 'signals', 'evidence_mentioned', 'time_window', 'detected_language']
    origin: Literal["user_statement", "user_verification", "evidence_extraction", "inference", "legacy", "ai_extraction"]
    evidence_id: UUID | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    verified: StrictBool = False
    source_turn: UUID | None = None
    source_text: str | None = Field(default=None, max_length=8000)
    source_start: int | None = Field(default=None, ge=0)
    source_end: int | None = Field(default=None, ge=0)
    uncertainty: str | None = Field(default=None, max_length=256)


Signal = Literal['financial', 'device_compromise', 'account_takeover', 'threats', 'harassment', 'impersonation', 'scam_attempt']


def normalize_payment_method(value: str) -> str | None:
    """Normalize names, never infer a rail from an app or generic card."""
    import re
    normalized = re.sub(r'[\s-]+', '_', value.strip().casefold())
    normalized = {'internet_banking': 'net_banking', 'online_banking': 'net_banking',
        'neft': 'bank_transfer', 'imps': 'bank_transfer', 'rtgs': 'bank_transfer'}.get(normalized, normalized)
    return normalized if normalized in {p.value for p in PaymentMethod} else None


def names_payment_verification_target(question: str, value: str) -> bool:
    """A confirmation must name exactly its supported rail, including aliases."""
    import re
    target = normalize_payment_method(value)
    names = {p.value for p in PaymentMethod if p != PaymentMethod.unknown}
    names.update({'internet_banking', 'online_banking', 'neft', 'imps', 'rtgs'})
    mentioned = {normalize_payment_method(name) for name in names
        if re.search(r'\b' + re.escape(name).replace('_', r'[\s_-]+') + r'\b', question, re.I)}
    return target not in (None, 'unknown') and mentioned == {target}


class Identifier(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)
    type: Literal['phone', 'email', 'upi', 'url', 'account']
    value: str = Field(min_length=1, max_length=256)


class ApproximateTime(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)
    start: datetime
    end: datetime
    approximate: Literal[True] = True
    original: str = Field(max_length=256)
    timezone: str = Field(max_length=64)


class FinancialFacts(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    fact_schema_version: Literal["1.0"] = "1.0"
    occurred_at: datetime | None = None
    amount: Decimal | None = Field(default=None, gt=0, le=9999999999.99, max_digits=12, decimal_places=2)
    payment_method: PaymentMethod = PaymentMethod.unknown
    transaction_id: str | None = Field(default=None, max_length=128)
    transaction_status: Literal["pending", "completed", "unknown"] | None = None
    account_compromised: StrictBool | None = None
    remote_access: StrictBool | None = None
    credentials_exposed: StrictBool | None = None
    ongoing_loss: StrictBool | None = None
    evidence_available: StrictBool | None = None
    provenance: tuple[FactProvenance, ...] = ()
    money_lost: StrictBool | None = None
    currency: str | None = Field(default=None, pattern=r'^[A-Z]{3}$')
    payment_app: str | None = Field(default=None, max_length=128)
    claimed_organization: str | None = Field(default=None, max_length=128)
    claimed_person: str | None = Field(default=None, max_length=128)
    identifiers: tuple[Identifier, ...] = ()
    signals: tuple[Signal, ...] = ()
    evidence_mentioned: tuple[str, ...] = ()
    time_window: ApproximateTime | None = None
    detected_language: Literal['en', 'te', 'hi', 'te-Latn', 'hi-Latn', 'mixed', 'unknown'] = 'unknown'

    @model_validator(mode="after")
    def critical_inferences_require_review(self):
        critical = {"authorization", "account_compromised", "remote_access", "credentials_exposed", "ongoing_loss"}
        for p in self.provenance:
            if p.field in critical and p.origin in {"inference", "evidence_extraction"} and not p.verified and getattr(self, p.field, None) not in (None, "unknown"):
                raise ValueError("Critical inferred facts require user verification")
        return self


class FinancialScamTransferFacts(FinancialFacts):
    kind: Literal["financial_scam_transfer"] = "financial_scam_transfer"
    authorization: Literal["authorized"] = "authorized"


class UnauthorizedFinancialTransactionFacts(FinancialFacts):
    kind: Literal["unauthorized_financial_transaction"] = "unauthorized_financial_transaction"
    authorization: Literal["unauthorized"] = "unauthorized"


class UnknownFinancialAuthorizationFacts(FinancialFacts):
    kind: Literal["financial_authorization_unknown"] = "financial_authorization_unknown"
    authorization: Literal["unknown"] = "unknown"


class GeneralIncidentFacts(FinancialFacts):
    kind: Literal['incident_understanding'] = 'incident_understanding'
    authorization: Literal['unknown'] = 'unknown'


IncidentFacts = Annotated[
    FinancialScamTransferFacts | UnauthorizedFinancialTransactionFacts | UnknownFinancialAuthorizationFacts | GeneralIncidentFacts,
    Field(discriminator="kind"),
]
FACTS_ADAPTER = TypeAdapter(IncidentFacts)
