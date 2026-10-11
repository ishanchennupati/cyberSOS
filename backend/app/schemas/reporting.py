from datetime import datetime
from typing import Literal
from uuid import UUID
from pydantic import BaseModel,ConfigDict,Field


class DraftRequest(BaseModel):
    model_config=ConfigDict(extra='forbid')
    draft_id: UUID
    expected_revision: int=Field(ge=0)


class ReportReview(BaseModel):
    model_config=ConfigDict(extra='forbid')
    expected_revision: int=Field(ge=0)


class PacketFact(BaseModel):
    id: str
    label: str
    value: str | bool | list | dict
    statement: str
    source_refs: list[dict]=Field(default_factory=list)
    origin: Literal['citizen_reviewed_canonical']='citizen_reviewed_canonical'


class ReviewedCasePacket(BaseModel):
    model_config=ConfigDict(extra='forbid')
    version: Literal['1.0']='1.0'
    incident_id: UUID
    source_revision: int
    jurisdiction: Literal['India']='India'
    facts: list[PacketFact]
    unknowns: list[str]
    evidence: list[dict]
    recorded_actions: list[dict]
    mapping: dict
    handoff: dict=Field(default_factory=dict)
    meaning: Literal['Citizen account prepared by CyberSOS; not an official receipt']='Citizen account prepared by CyberSOS; not an official receipt'


class ReportingDraft(BaseModel):
    id: UUID
    source_revision: int
    source_digest: str
    packet: ReviewedCasePacket
    narrative: dict
    reviewed: bool
    reviewed_at: datetime | None
