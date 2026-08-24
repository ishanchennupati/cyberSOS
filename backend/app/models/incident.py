import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, JSON, Numeric, String, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CrimeCategory(str, enum.Enum):
    women_children = "women_children"
    financial_fraud = "financial_fraud"
    other_cyber_crime = "other_cyber_crime"
    # Phase 0/1 placeholder values - kept so existing rows still load.
    phishing = "phishing"
    identity_theft = "identity_theft"
    social_media = "social_media"
    job_scam = "job_scam"
    other = "other"


IncidentType = CrimeCategory


class OtherCrimeSubCategory(str, enum.Enum):
    online_social_media = "online_social_media"
    ransomware = "ransomware"
    hacking = "hacking"
    cryptocurrency = "cryptocurrency"
    online_trafficking = "online_trafficking"
    online_gambling = "online_gambling"
    any_other = "any_other"


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
    transaction_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    is_fraud_ongoing: Mapped[bool | None] = mapped_column(nullable=True)
    is_account_compromised: Mapped[bool | None] = mapped_column(nullable=True)
    is_credentials_exposed: Mapped[bool | None] = mapped_column(nullable=True)
    is_otp_shared: Mapped[bool | None] = mapped_column(nullable=True)
    is_pin_shared: Mapped[bool | None] = mapped_column(nullable=True)
    is_password_shared: Mapped[bool | None] = mapped_column(nullable=True)
    is_remote_access_granted: Mapped[bool | None] = mapped_column(nullable=True)
    unauthorized_activity_continuing: Mapped[bool | None] = mapped_column(nullable=True)
    potential_additional_loss: Mapped[bool | None] = mapped_column(nullable=True)
    account_secured: Mapped[bool | None] = mapped_column(nullable=True)
    evidence_available: Mapped[bool | None] = mapped_column(nullable=True)

    incident_subtype: Mapped[str | None] = mapped_column(String(128), nullable=True)
    affected_person_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    platform: Mapped[str | None] = mapped_column(String(64), nullable=True)
    account_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    immediate_danger: Mapped[bool | None] = mapped_column(nullable=True)
    threat_or_blackmail: Mapped[bool | None] = mapped_column(nullable=True)
    content_still_online: Mapped[bool | None] = mapped_column(nullable=True)
    account_access: Mapped[str | None] = mapped_column(String(32), nullable=True)
    attacker_active: Mapped[bool | None] = mapped_column(nullable=True)
    sensitive_information_exposed: Mapped[bool | None] = mapped_column(nullable=True)
    evidence_types: Mapped[list | None] = mapped_column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    urgency_score: Mapped[int | None] = mapped_column(nullable=True)

    other_crime_sub_category: Mapped[OtherCrimeSubCategory | None] = mapped_column(
        Enum(OtherCrimeSubCategory, name="other_crime_sub_category_enum"),
        nullable=True,
    )

    details: Mapped[dict | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=True,
    )

    urgency: Mapped[Urgency] = mapped_column(
        Enum(Urgency, name="urgency_enum"),
        nullable=False,
        default=Urgency.medium,
    )

    urgency_computed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    severity: Mapped[Urgency | None] = mapped_column(nullable=True)
    ongoing_risk: Mapped[Urgency | None] = mapped_column(nullable=True)
    recovery_window: Mapped[str | None] = mapped_column(String(32), nullable=True)
    urgency_reasons: Mapped[list | None] = mapped_column(JSON().with_variant(JSONB, "postgresql"), nullable=True)

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


class Evidence(Base):
    __tablename__ = "evidence"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    incident_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    content_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    size_bytes: Mapped[int] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
