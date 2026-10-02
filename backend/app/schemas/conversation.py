from datetime import datetime
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictStr, model_validator
from app.domain.facts import FactField, IncidentFacts
from app.domain.response import ActionCompletion, FactRequirement, PlanRevision
from app.schemas.next_move import NextMove


class TurnRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    turn_id: UUID  # Also the idempotency key; retained across retries.
    expected_revision: int = Field(ge=0)
    type: Literal['shortcut', 'answer', 'correction', 'completion', 'message'] = 'answer'
    field: FactField | None = None
    value: StrictBool | StrictStr | None = None
    action_id: str | None = Field(default=None, max_length=64)
    text: StrictStr | None = Field(default=None, min_length=1, max_length=8000)
    timezone: str = Field(default='Asia/Kolkata', max_length=64)

    @model_validator(mode='after')
    def message_shape(self):
        from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
        from app.domain.policy import check_values
        try:
            ZoneInfo(self.timezone)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise ValueError('Unsupported timezone') from exc
        if self.type == 'message':
            if self.text is None or not self.text.strip() or any(x is not None for x in (self.field, self.value, self.action_id)):
                raise ValueError('A message contains text only')
            check_values(self.text)
        elif self.text is not None:
            raise ValueError('Text is only supported for message turns')
        return self


class TurnRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    incident_id: UUID
    role: Literal['user']
    type: Literal['shortcut', 'answer', 'correction', 'completion', 'message']
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
    next_move: NextMove | None = None
    plan: PlanRevision
    completions: list[ActionCompletion]
