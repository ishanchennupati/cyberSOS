import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

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
    urgency: Urgency
    status: IncidentStatus
    created_at: datetime
    updated_at: datetime
