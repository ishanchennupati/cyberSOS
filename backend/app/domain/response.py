from datetime import date, datetime
from enum import Enum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StrictBool
from app.domain.facts import FactField, IncidentFacts
from app.models.incident import Urgency


class ActionPhase(str, Enum):
    contain = "CONTAIN"
    preserve = "PRESERVE"
    report = "REPORT"
    follow_up = "FOLLOW_UP"


class FactPriority(str, Enum):
    critical = "CRITICAL"
    supporting = "SUPPORTING"
    reporting = "REPORTING"
    optional = "OPTIONAL"


class OfficialSource(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    id: str
    authority: str
    display_name: str
    official_url: str
    purpose: str
    supported_guidance: tuple[str, ...]
    reviewed_on: date
    notes: str


class FactRequirement(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    field: FactField | None
    priority: FactPriority
    question: str


class ResponseAction(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    id: str
    phase: ActionPhase
    priority: Urgency
    order: int = Field(ge=1)
    title: str
    instruction: str
    why: str
    minimum_facts: tuple[str, ...]
    applicability: str
    official_source_id: str | None = None
    can_mark_complete: bool = True
    critical: bool = False
    phone: str | None = None
    url: str | None = None
    url_label: str | None = None


class ResponsePlan(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    playbook_id: str
    playbook_version: str
    fact_schema_version: str
    evaluated_at: datetime
    facts: IncidentFacts
    urgency: Urgency
    reasons: tuple[str, ...]
    actions: tuple[ResponseAction, ...]
    sources: tuple[OfficialSource, ...]


class ActionCompletionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    completed: StrictBool
    user_note: str | None = Field(default=None, max_length=512)
    user_recorded_reference: str | None = Field(default=None, max_length=128)


class ActionCompletion(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")
    id: UUID
    incident_id: UUID
    plan_id: UUID
    action_id: str
    completed: bool
    user_note: str | None
    user_recorded_reference: str | None
    updated_at: datetime
    meaning: Literal["user_self_report"] = "user_self_report"


class PlanRevision(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    incident_id: UUID
    revision: int
    plan: ResponsePlan
