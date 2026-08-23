import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.incident import IncidentStatus, IncidentType, PaymentMethod, Urgency


class IncidentCreate(BaseModel):
    incident_type: IncidentType = IncidentType.financial_fraud
    payment_method: PaymentMethod = PaymentMethod.unknown
    amount: float | None = Field(default=None, ge=0)
    incident_time: datetime | None = None


class IncidentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    incident_type: IncidentType
    payment_method: PaymentMethod
    amount: float | None
    incident_time: datetime | None
    occurred_at: datetime | None = None
    transaction_id: str | None = None
    urgency: Urgency
    urgency_computed_at: datetime | None = None
    status: IncidentStatus
    created_at: datetime
    updated_at: datetime

    @field_validator("amount", mode="before")
    @classmethod
    def coerce_amount(cls, value: object) -> float | None:
        if value is None:
            return None
        return float(value)


class TriageRequest(BaseModel):
    incident_type: IncidentType
    occurred_at: datetime
    amount: float = Field(gt=0)
    payment_method: PaymentMethod
    transaction_id: str | None = Field(default=None, max_length=128)

    @field_validator("transaction_id", mode="before")
    @classmethod
    def empty_txn_id_as_none(cls, value: object) -> str | None:
        if value is None:
            return None
        if isinstance(value, str) and not value.strip():
            return None
        return str(value).strip()


class ActionItem(BaseModel):
    id: str
    title: str
    why: str
    phone: str | None = None
    url: str | None = None
    url_label: str | None = None


class ComplaintDraft(BaseModel):
    body: str


class ActionPlanResponse(BaseModel):
    urgency: Urgency
    urgency_label: str
    core_message: str
    large_amount: bool
    actions: list[ActionItem]
    complaint_draft: ComplaintDraft
