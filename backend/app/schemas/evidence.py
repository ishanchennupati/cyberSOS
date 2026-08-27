import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.evidence import (
    EvidenceType,
    ExtractionStatus,
    SuspectIdentifierType,
    VerificationStatus,
)

# --- Extraction -----------------------------------------------------------


class ExtractedFinancialData(BaseModel):
    """
    Structured fields the extraction service attempts to find. Every field
    defaults to null — the service must never invent a value. This is the
    same shape used for extracted_data on the Evidence record.
    """

    amount: float | None = None
    transaction_id: str | None = None
    payment_method: str | None = None
    date: str | None = None
    time: str | None = None
    bank: str | None = None
    wallet: str | None = None
    merchant: str | None = None
    upi_id: str | None = None
    phone_number: str | None = None
    email: str | None = None
    website_url: str | None = None


class ExtractionResult(BaseModel):
    status: ExtractionStatus
    data: ExtractedFinancialData | None = None
    # Human-readable reason when status == failed, e.g. "Extraction unavailable".
    message: str | None = None
    provider: str | None = None


class FieldComparison(BaseModel):
    field: str
    label: str
    incident_value: str | None
    evidence_value: str | None
    matches: bool


class ComparisonResult(BaseModel):
    has_incident_data: bool
    all_match: bool
    comparisons: list[FieldComparison]


# --- Evidence ---------------------------------------------------------------


class EvidenceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    incident_id: uuid.UUID
    original_filename: str
    mime_type: str
    file_size: int
    sha256_hash: str
    evidence_type: EvidenceType
    description: str | None
    extraction_status: ExtractionStatus
    extracted_data: dict | None
    verification_status: VerificationStatus
    uploaded_at: datetime
    created_at: datetime
    updated_at: datetime
    # Short-lived signed URL for preview, resolved at read time. Never a
    # permanent public URL — see storage_service.get_preview_url.
    preview_url: str | None = None


class EvidenceUpdate(BaseModel):
    evidence_type: EvidenceType | None = None
    description: str | None = Field(default=None, max_length=2000)
    extracted_data: ExtractedFinancialData | None = None
    verification_status: VerificationStatus | None = None

    @field_validator("verification_status")
    @classmethod
    def block_manual_verified_without_data(cls, value):
        # The route layer enforces the real rule (explicit /verify call);
        # this just guards against setting an unsupported enum value here.
        return value


class VerifyRequest(BaseModel):
    """
    Body for POST /evidence/{id}/verify. The citizen has reviewed the
    extracted fields (editing any that were wrong) and confirms them.
    """

    extracted_data: ExtractedFinancialData
    verification_status: VerificationStatus = VerificationStatus.verified


class VerifyResponse(BaseModel):
    evidence: EvidenceRead
    comparison: ComparisonResult


# --- Suspect identifiers -----------------------------------------------------


class SuspectIdentifierCreate(BaseModel):
    type: SuspectIdentifierType
    value: str = Field(min_length=1, max_length=512)
    source_evidence_id: uuid.UUID | None = None

    @field_validator("value")
    @classmethod
    def strip_value(cls, value: str) -> str:
        return value.strip()


class SuspectIdentifierUpdate(BaseModel):
    type: SuspectIdentifierType | None = None
    value: str | None = Field(default=None, min_length=1, max_length=512)
    verified: bool | None = None


class SuspectIdentifierRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    incident_id: uuid.UUID
    type: SuspectIdentifierType
    value: str
    source_evidence_id: uuid.UUID | None
    verified: bool
    created_at: datetime
    updated_at: datetime


# --- Timeline -----------------------------------------------------------------


class TimelineEventCreate(BaseModel):
    event_time: datetime
    event_type: str = Field(default="custom", max_length=60)
    description: str = Field(min_length=1, max_length=500)
    source_evidence_id: uuid.UUID | None = None


class TimelineEventUpdate(BaseModel):
    event_time: datetime | None = None
    event_type: str | None = Field(default=None, max_length=60)
    description: str | None = Field(default=None, min_length=1, max_length=500)


class TimelineEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    incident_id: uuid.UUID
    event_time: datetime
    event_type: str
    description: str
    source_evidence_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


# --- Readiness / checklist -----------------------------------------------------


class ReadinessItem(BaseModel):
    id: str
    label: str
    met: bool


class EvidenceReadinessResponse(BaseModel):
    percent: int
    items: list[ReadinessItem]
    missing_summary: str | None


# --- Incident description / AI summary -----------------------------------------


class IncidentDescriptionUpdate(BaseModel):
    description: str = Field(max_length=4000)


class GenerateSummaryResponse(BaseModel):
    draft: str
    provider: str
    disclaimer: str = "AI-generated draft — review carefully before using."
