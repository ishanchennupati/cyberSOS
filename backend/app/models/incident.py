import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Numeric, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class IncidentType(str, enum.Enum):
    financial_fraud = "financial_fraud"
    phishing = "phishing"
    identity_theft = "identity_theft"
    social_media = "social_media"
    job_scam = "job_scam"
    other = "other"


class PaymentMethod(str, enum.Enum):
    upi = "upi"
    debit_card = "debit_card"
    credit_card = "credit_card"
    net_banking = "net_banking"
    wallet = "wallet"
    unknown = "unknown"
    # Phase 0 values — kept so existing Postgres enum labels still load.
    bank_transfer = "bank_transfer"
    card = "card"


class Urgency(str, enum.Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    medium_low = "medium_low"
    standard = "standard"
    # Phase 0 leftover — treated as standard by the rule engine.
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
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
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

    # Phase 0 column. Triage also writes occurred_at; both are kept in sync.
    incident_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    occurred_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    transaction_id: Mapped[str | None] = mapped_column(String(128), nullable=True)

    urgency: Mapped[Urgency] = mapped_column(
        Enum(Urgency, name="urgency_enum"),
        nullable=False,
        default=Urgency.medium,
    )

    urgency_computed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
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
