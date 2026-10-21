"""Provider output has no action, tool, workflow or official-status contract."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictStr, model_validator
from app.domain.facts import Identifier
from app.schemas.evidence_intelligence import NaturalEvidenceReview

CandidateField = Literal['money_lost', 'authorization', 'amount', 'currency', 'payment_app',
    'payment_method', 'transaction_id', 'transaction_status', 'claimed_organization', 'claimed_person',
    'identifiers', 'signals', 'remote_access', 'account_compromised', 'credentials_exposed',
    'ongoing_loss', 'evidence_available', 'evidence_mentioned', 'time_window', 'platform',
    'immediate_danger', 'blackmail', 'private_image_threat', 'bank_involved', 'message_text', 'threat_text', 'timestamp_text', 'recipient']

BOOLEAN_CANDIDATE_FIELDS = frozenset({'money_lost', 'remote_access', 'account_compromised',
    'credentials_exposed', 'ongoing_loss', 'evidence_available', 'immediate_danger', 'blackmail', 'private_image_threat', 'bank_involved'})
LIST_CANDIDATE_FIELDS = frozenset({'identifiers', 'signals', 'evidence_mentioned'})


class Candidate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    field: CandidateField
    value: StrictBool | StrictStr | list[StrictStr] | list[Identifier]
    source_text: str = Field(min_length=1, max_length=8000)
    extraction: Literal['explicit', 'inference']
    confidence: float = Field(ge=0, le=1)
    uncertainty: str | None = Field(max_length=256)
    correction_source: str | None = Field(max_length=128)
    # null = ordinary statement, true/false = accepts/rejects active rail review.
    confirms_pending: StrictBool | None = None

    @model_validator(mode='after')
    def typed_value(self):
        if self.confirms_pending is not None and self.field != 'payment_method':
            raise ValueError('Pending confirmation is supported for payment-method review only')
        booleans = BOOLEAN_CANDIDATE_FIELDS
        lists = LIST_CANDIDATE_FIELDS
        if self.field in booleans and type(self.value) is not bool:
            raise ValueError('Boolean fact requires a boolean')
        if self.field in lists and not isinstance(self.value, list):
            raise ValueError('List fact requires a list')
        if self.field not in booleans | lists and type(self.value) is not str:
            raise ValueError('Text fact requires a string')
        if isinstance(self.value, (str, list)) and len(self.value) > (256 if isinstance(self.value, str) else 16):
            raise ValueError('Candidate value exceeds limit')
        if self.field == 'identifiers' and not all(isinstance(v, Identifier) for v in self.value):
            raise ValueError('Identifier requires type and value')
        return self


class Understanding(BaseModel):
    model_config = ConfigDict(extra='forbid')
    language: Literal['en', 'te', 'hi', 'te-Latn', 'hi-Latn', 'mixed', 'unknown']
    candidates: list[Candidate] = Field(max_length=32)
    intents: list[Literal['skip','pause','resume','not_sure','question','distress','unrelated','feedback',
        'help','plan','summary','conclude','witness','separate_incident','same_incident']] = Field(default_factory=list, max_length=8)
    intent_source: str | None = Field(default=None, max_length=512)
    evidence_review: NaturalEvidenceReview | None = None
    case_records: list['NaturalCaseRecord'] = Field(default_factory=list, max_length=3)


class NaturalCaseRecord(BaseModel):
    model_config = ConfigDict(extra='forbid')
    kind: Literal['note', 'reference', 'completion']
    text: StrictStr = Field(min_length=1, max_length=500)
    source_text: StrictStr = Field(min_length=1, max_length=1000)
    organization: StrictStr | None = Field(default=None, max_length=100)
    action_id: StrictStr | None = Field(default=None, max_length=64)


Understanding.model_rebuild()
