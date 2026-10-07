from datetime import datetime
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictStr, model_validator
from app.domain.facts import FactField, IncidentFacts
from app.domain.response import ActionCompletion, FactRequirement, PlanRevision
from app.schemas.next_move import NextMove
from app.schemas.evidence_intelligence import EvidenceReview


class TurnRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    turn_id: UUID  # Also the idempotency key; retained across retries.
    expected_revision: int = Field(ge=0)
    type: Literal['shortcut', 'answer', 'correction', 'completion', 'message', 'evidence_review', 'route_hint', 'case_review'] = 'answer'
    field: FactField | None = None
    value: StrictBool | StrictStr | None = None
    action_id: str | None = Field(default=None, max_length=64)
    text: StrictStr | None = Field(default=None, min_length=1, max_length=8000)
    timezone: str = Field(default='Asia/Kolkata', max_length=64)
    attachment_ids: list[UUID] = Field(default_factory=list, max_length=5)
    evidence_review: EvidenceReview | None = None
    review_context_id: UUID | None = None
    route_hint: Literal['women_children', 'financial', 'other', 'not_sure'] | None = None

    @model_validator(mode='after')
    def message_shape(self):
        from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
        from app.domain.policy import check_values
        try:
            ZoneInfo(self.timezone)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise ValueError('Unsupported timezone') from exc
        if self.type == 'message':
            if (not self.text or not self.text.strip()) and not self.attachment_ids or any(x is not None for x in (self.field, self.value, self.action_id)):
                raise ValueError('A message contains text or attachments')
            if len(set(self.attachment_ids)) != len(self.attachment_ids):
                raise ValueError('Duplicate attachment references')
            check_values(self.text)
        elif self.text is not None or self.attachment_ids:
            raise ValueError('Text is only supported for message turns')
        if (self.type == 'evidence_review') != (self.evidence_review is not None):
            raise ValueError('Evidence review requires an explicit bounded selection')
        if (self.type == 'route_hint') != (self.route_hint is not None):
            raise ValueError('Routing hints are separate from facts')
        if self.review_context_id is not None and self.type != 'message':
            raise ValueError('Natural review context belongs to messages')
        return self


class TurnRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    incident_id: UUID
    role: Literal['user']
    type: Literal['shortcut', 'answer', 'correction', 'completion', 'message', 'evidence_review', 'route_hint', 'case_review']
    text: str
    structured_reply: TurnRequest
    fact_changes: dict
    pending_question: FactRequirement | None
    revision: int
    created_at: datetime
    attachments: list[dict] = Field(default_factory=list)


class ConversationRead(BaseModel):
    incident_id: UUID
    revision: int
    version: Literal['1.0']
    answered: list[FactField]
    facts: IncidentFacts
    pending_question: FactRequirement | None
    turns: list[TurnRead]
    next_move: NextMove | None = None
    plan: PlanRevision
    completions: list[ActionCompletion]
    projection: dict = Field(default_factory=dict)
    memory: dict = Field(default_factory=dict)
    evidence_reviews: list[dict] = Field(default_factory=list)
    route_hint: str | None = None
    understanding_review: dict = Field(default_factory=dict)
