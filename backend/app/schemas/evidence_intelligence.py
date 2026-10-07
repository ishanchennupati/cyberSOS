"""Candidate extraction is document data, never action or instruction authority."""
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, StrictStr


EvidenceField = Literal['amount', 'currency', 'payment_method', 'transaction_id',
    'transaction_status', 'recipient', 'claimed_organization', 'platform',
    'timestamp_text', 'message_text', 'threat_text', 'identifiers']


class EvidenceCandidate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    field: EvidenceField
    value: StrictStr = Field(min_length=1, max_length=2000)
    source_text: StrictStr = Field(min_length=1, max_length=2000)
    page: int | None = Field(default=None, ge=1, le=100)
    confidence: float = Field(ge=0, le=1)
    uncertainty: StrictStr | None = Field(default=None, max_length=256)
    identifier_type: Literal['phone', 'email', 'upi', 'url', 'account'] | None = None


class EvidenceAnalysis(BaseModel):
    model_config = ConfigDict(extra='forbid')
    readable: bool
    candidates: list[EvidenceCandidate] = Field(max_length=24)


class AnalyzeRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    attempt_id: UUID
    expected_revision: int = Field(ge=0)


class ReviewDecision(BaseModel):
    model_config = ConfigDict(extra='forbid')
    candidate_id: str = Field(min_length=1, max_length=80)
    decision: Literal['accept', 'reject', 'correct']
    value: StrictStr | None = Field(default=None, max_length=2000)
    resolve_conflict: bool = False


class EvidenceReview(BaseModel):
    model_config = ConfigDict(extra='forbid')
    attempt_id: UUID
    decisions: list[ReviewDecision] = Field(min_length=1, max_length=24)


class NaturalEvidenceReview(EvidenceReview):
    source_text: str = Field(min_length=1, max_length=512)
    reference_text: str | None = Field(default=None, max_length=128)
