import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Numeric, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class IncidentType(str, enum.Enum):
    financial_fraud = "financial_fraud"


class PaymentMethod(str, enum.Enum):
    upi = "upi"
    bank_transfer = "bank_transfer"
    card = "card"
    wallet = "wallet"
    unknown = "unknown"


class Urgency(str, enum.Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"


class IncidentStatus(str, enum.Enum):
    draft = "draft"
    triage_started = "triage_started"
    action_required = "action_required"
    report_prepared = "report_prepared"
    submitted = "submitted"
    closed = "closed"


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    incident_type: Mapped[IncidentType] = mapped_column(
        Enum(IncidentType, name="incident_type_enum"),
        nullable=False,
        default=IncidentType.financial_fraud,
    )

    payment_method: Mapped[PaymentMethod] = mapped_column(
        Enum(PaymentMethod, name="payment_method_enum"),
        nullable=False,
        default=PaymentMethod.unknown,
    )

    amount: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)

    incident_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    urgency: Mapped[Urgency] = mapped_column(
        Enum(Urgency, name="urgency_enum"),
        nullable=False,
        default=Urgency.medium,
    )

    status: Mapped[IncidentStatus] = mapped_column(
        Enum(IncidentStatus, name="incident_status_enum"),
        nullable=False,
        default=IncidentStatus.draft,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
