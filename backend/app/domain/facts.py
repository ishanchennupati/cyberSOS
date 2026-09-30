from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StrictBool, TypeAdapter, model_validator
from app.models.incident import PaymentMethod

FACT_SCHEMA_VERSION = "1.0"


class FactField(str, Enum):
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
    field: FactField
    origin: Literal["user_statement", "user_verification", "evidence_extraction", "inference", "legacy"]
    evidence_id: UUID | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    verified: StrictBool = False


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

    @model_validator(mode="after")
    def critical_inferences_require_review(self):
        critical = {"authorization", "account_compromised", "remote_access", "credentials_exposed", "ongoing_loss"}
        for p in self.provenance:
            if p.field.value in critical and p.origin in {"inference", "evidence_extraction"} and not p.verified and getattr(self, p.field.value, None) not in (None, "unknown"):
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


IncidentFacts = Annotated[
    FinancialScamTransferFacts | UnauthorizedFinancialTransactionFacts | UnknownFinancialAuthorizationFacts,
    Field(discriminator="kind"),
]
FACTS_ADAPTER = TypeAdapter(IncidentFacts)
