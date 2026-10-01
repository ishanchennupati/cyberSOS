from datetime import datetime
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictStr
from app.domain.facts import FactField, IncidentFacts
from app.domain.response import ActionCompletion, FactRequirement, PlanRevision


class TurnRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    turn_id: UUID  # Also the idempotency key; retained across retries.
    expected_revision: int = Field(ge=0)
    type: Literal['shortcut', 'answer', 'correction', 'completion'] = 'answer'
    field: FactField | None = None
    value: StrictBool | StrictStr | None = None
    action_id: str | None = Field(default=None, max_length=64)


class TurnRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    incident_id: UUID
    role: Literal['user']
    type: Literal['shortcut', 'answer', 'correction', 'completion']
    text: str
    structured_reply: TurnRequest
    fact_changes: dict
    pending_question: FactRequirement | None
    revision: int
    created_at: datetime


class ConversationRead(BaseModel):
    incident_id: UUID
    revision: int
    version: Literal['1.0']
    answered: list[FactField]
    facts: IncidentFacts
    pending_question: FactRequirement | None
    turns: list[TurnRead]
    plan: PlanRevision
    completions: list[ActionCompletion]
