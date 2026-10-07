"""
Phase 3 — Evidence Vault database models.

Three tables, all scoped to an incident by foreign key:
  * evidence            — uploaded files + extracted/verified metadata
  * suspect_identifiers — phone/email/UPI/etc. tied to the suspected party
  * timeline_events      — the chronological story of the incident

Nothing here submits anything anywhere. These are storage models only.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    String,
    Uuid,
    func,
    Index,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON, TypeDecorator

from app.db.base import Base


class _JSONBOrJSON(TypeDecorator):
    """JSONB on Postgres, plain JSON on SQLite (used by tests/local dev)."""

    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB())
        return dialect.type_descriptor(JSON())


class EvidenceType(str, enum.Enum):
    bank_statement = "bank_statement"
    transaction_receipt = "transaction_receipt"
    payment_screenshot = "payment_screenshot"
    sms_message = "sms_message"
    email = "email"
    chat_conversation = "chat_conversation"
    website_url = "website_url"
    suspect_information = "suspect_information"
    photo_video = "photo_video"
    other_document = "other_document"


class ExtractionStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class VerificationStatus(str, enum.Enum):
    unverified = "unverified"
    verified = "verified"
    needs_review = "needs_review"


class SuspectIdentifierType(str, enum.Enum):
    phone = "phone"
    email = "email"
    upi_id = "upi_id"
    bank_account = "bank_account"
    website = "website"
    social_media = "social_media"
    other = "other"


class Evidence(Base):
    __tablename__ = "evidence"
    staged_for_chat: Mapped[bool] = mapped_column(Boolean, default=False, server_default='false')

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    incident_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("incidents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    original_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    # Path inside the storage bucket (Supabase) or local storage root.
    # Never a public/permanent URL — see storage_service.
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False, unique=True)

    mime_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)

    # Legacy rows whose original bytes are unavailable have an unknown hash.
    # New uploads always compute it before saving.
    sha256_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    evidence_type: Mapped[EvidenceType] = mapped_column(
        Enum(EvidenceType, name="evidence_type_enum"),
        nullable=False,
        default=EvidenceType.other_document,
    )
    description: Mapped[str | None] = mapped_column(String(2000), nullable=True)

    extraction_status: Mapped[ExtractionStatus] = mapped_column(
        Enum(ExtractionStatus, name="extraction_status_enum"),
        nullable=False,
        default=ExtractionStatus.pending,
    )
    # AI-extracted fields, always shown to the user as "please verify" —
    # never treated as ground truth. See app/schemas/evidence.py for shape.
    extracted_data: Mapped[dict | None] = mapped_column(_JSONBOrJSON, nullable=True)

    verification_status: Mapped[VerificationStatus] = mapped_column(
        Enum(VerificationStatus, name="verification_status_enum"),
        nullable=False,
        default=VerificationStatus.unverified,
    )

    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
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


class SuspectIdentifier(Base):
    __tablename__ = "suspect_identifiers"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    incident_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("incidents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    type: Mapped[SuspectIdentifierType] = mapped_column(
        Enum(SuspectIdentifierType, name="suspect_identifier_type_enum"),
        nullable=False,
    )
    value: Mapped[str] = mapped_column(String(512), nullable=False)

    # Set when this identifier came from AI extraction of an evidence file,
    # so the UI can show "found in {evidence}". Null for manual entries.
    source_evidence_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("evidence.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Never defaults to True — extracted identifiers start unverified, same
    # as extracted evidence fields (see product principle in the spec).
    verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class TimelineEvent(Base):
    __tablename__ = "timeline_events"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    incident_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("incidents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    event_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    # Free text, not an enum: the citizen can add their own events
    # ("Suspicious call received") that don't map to a fixed system action.
    event_type: Mapped[str] = mapped_column(String(60), nullable=False, default="custom")
    description: Mapped[str] = mapped_column(String(500), nullable=False)

    source_evidence_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("evidence.id", ondelete="SET NULL"),
        nullable=True,
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


class EvidenceAttempt(Base):
    __tablename__ = 'evidence_attempts'
    __table_args__ = (Index('uq_evidence_active_analysis', 'evidence_id', unique=True,
        sqlite_where=text("status = 'processing'"), postgresql_where=text("status = 'processing'")),)
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    evidence_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey('evidence.id', ondelete='CASCADE'), index=True)
    incident_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey('incidents.id', ondelete='CASCADE'), index=True)
    base_revision: Mapped[int] = mapped_column()
    base_facts: Mapped[dict] = mapped_column(_JSONBOrJSON)
    status: Mapped[str] = mapped_column(String(24), default='processing')
    provider: Mapped[str] = mapped_column(String(64))
    model: Mapped[str] = mapped_column(String(128))
    candidates: Mapped[list] = mapped_column(_JSONBOrJSON, default=list)
    failure: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EvidenceReviewRecord(Base):
    __tablename__ = 'evidence_reviews'
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    attempt_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey('evidence_attempts.id', ondelete='CASCADE'), index=True)
    turn_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey('conversation_turns.id', ondelete='CASCADE'), index=True)
    decisions: Mapped[list] = mapped_column(_JSONBOrJSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
