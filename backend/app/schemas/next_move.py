"""One bounded conversational proposal; deliberately has no action-plan field."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, StrictStr, model_validator
from app.schemas.understanding import CandidateField


class FactReference(BaseModel):
    model_config = ConfigDict(extra='forbid')
    field: CandidateField | Literal['occurred_at']
    value: StrictStr | bool | list | dict | None


class KnowledgeReference(BaseModel):
    model_config = ConfigDict(extra='forbid')
    id: StrictStr = Field(max_length=80)
    claim: StrictStr = Field(min_length=1, max_length=500)


class NextMove(BaseModel):
    model_config = ConfigDict(extra='forbid')
    type: Literal['ASK_CLARIFICATION', 'REQUEST_EVIDENCE', 'VERIFY_INFORMATION',
        'RESOLVE_CONFLICT', 'ACKNOWLEDGE_AND_WAIT', 'EXPLAIN_APPROVED_ACTION', 'CONTINUE_OPEN_CONVERSATION', 'ANSWER_RELEVANT_QUESTION']
    purpose: Literal['containment', 'understanding', 'preservation', 'reporting', 'conflict', 'support']
    message: StrictStr = Field(min_length=1, max_length=1400)
    fact_refs: list[FactReference] = Field(default_factory=list, max_length=12)
    knowledge_refs: list[KnowledgeReference] = Field(default_factory=list, max_length=3)
    related_field: CandidateField | Literal['occurred_at', 'story'] | None
    quick_replies: list[StrictStr] = Field(max_length=4)
    evidence_kind: Literal['transaction_message', 'transaction_receipt', 'non_explicit_conversation', 'profile_identifier'] | None
    action_id: StrictStr | None = Field(max_length=64)
    # Short checkable context references, never private chain-of-thought.
    basis: list[Literal['current_facts', 'unknown_fact', 'conflict', 'candidate', 'recent_message', 'approved_action', 'evidence']] = Field(min_length=1, max_length=7)

    @model_validator(mode='after')
    def shape(self):
        if any(not reply.strip() or len(reply) > 100 for reply in self.quick_replies):
            raise ValueError('Bounded quick replies required')
        if (self.type == 'REQUEST_EVIDENCE') != (self.evidence_kind is not None):
            raise ValueError('Evidence intent belongs to evidence moves only')
        if (self.type == 'EXPLAIN_APPROVED_ACTION') != (self.action_id is not None):
            raise ValueError('Explanation requires an approved action reference')
        if self.type in {'ASK_CLARIFICATION', 'VERIFY_INFORMATION', 'RESOLVE_CONFLICT'} and self.related_field in (None, 'story'):
            raise ValueError('Focused investigation requires a related fact')
        if self.type in {'ACKNOWLEDGE_AND_WAIT', 'EXPLAIN_APPROVED_ACTION'} and (self.related_field is not None or self.quick_replies):
            raise ValueError('No question attached to a waiting/explanation move')
        if self.type == 'CONTINUE_OPEN_CONVERSATION' and self.related_field != 'story':
            raise ValueError('Open conversation relates to the story')
        return self
