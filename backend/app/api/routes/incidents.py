import uuid

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.incident import (
    ActionPlanResponse,
    IncidentCreate,
    IncidentDetailsUpdate,
    IncidentRead,
    TriageRequest,
)
from app.services import incident_service
from app.schemas.evidence import EvidenceReadinessResponse, IncidentDescriptionUpdate, GenerateSummaryResponse
from app.services.case_access import authorize_case_resource, set_cookie
from app.services import response_service
from app.domain.facts import IncidentFacts
from app.domain.response import ActionCompletion, ActionCompletionRequest, PlanRevision
from datetime import datetime, timezone

router = APIRouter(prefix="/incidents", tags=["incidents"], dependencies=[Depends(authorize_case_resource)])


def _get_incident(db: Session, incident_id: uuid.UUID):
    incident = incident_service.get_incident(db, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.get("/{incident_id}/evidence-readiness", response_model=EvidenceReadinessResponse)
def get_readiness(incident_id: uuid.UUID, db: Session = Depends(get_db)):
    from app.services.evidence_service import compute_readiness
    return compute_readiness(db, _get_incident(db, incident_id))


@router.patch("/{incident_id}/description", response_model=IncidentRead)
def update_description(incident_id: uuid.UUID, payload: IncidentDescriptionUpdate,
                       db: Session = Depends(get_db)):
    return incident_service.update_description(db, _get_incident(db, incident_id), payload.description)


@router.post("/{incident_id}/generate-summary", response_model=GenerateSummaryResponse)
def generate_summary(incident_id: uuid.UUID, db: Session = Depends(get_db)):
    return incident_service.generate_summary(_get_incident(db, incident_id))


@router.post("", response_model=IncidentRead, status_code=201)
def create_incident(payload: IncidentCreate, response: Response, db: Session = Depends(get_db)) -> IncidentRead:
    incident, token = incident_service.create_incident(db, payload)
    set_cookie(response, incident, token)
    return incident


@router.get("/{incident_id}", response_model=IncidentRead)
def get_incident(incident_id: uuid.UUID, db: Session = Depends(get_db)) -> IncidentRead:
    incident = incident_service.get_incident(db, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.post("/{incident_id}/triage", response_model=IncidentRead)
def triage_incident(
    incident_id: uuid.UUID,
    payload: TriageRequest,
    db: Session = Depends(get_db),
) -> IncidentRead:
    incident = incident_service.get_incident(db, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident_service.triage_incident(db, incident, payload)


@router.patch("/{incident_id}/details", response_model=IncidentRead)
def update_incident_details(
    incident_id: uuid.UUID,
    payload: IncidentDetailsUpdate,
    db: Session = Depends(get_db),
) -> IncidentRead:
    incident = incident_service.get_incident(db, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident_service.update_incident_details(db, incident, payload)


@router.get("/{incident_id}/action-plan", response_model=ActionPlanResponse)
def get_action_plan(
    incident_id: uuid.UUID, db: Session = Depends(get_db)
) -> ActionPlanResponse:
    incident = incident_service.get_incident(db, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    if incident.urgency_computed_at is None and incident.facts is None:
        raise HTTPException(
            status_code=409,
            detail="This incident has not been triaged yet.",
        )
    return incident_service.build_action_plan(incident, db=db)


@router.put("/{incident_id}/facts", response_model=PlanRevision)
def update_facts(incident_id: uuid.UUID, facts: IncidentFacts, db: Session = Depends(get_db)):
    incident = _get_incident(db, incident_id)
    if incident.incident_type.value != "financial_fraud":
        raise HTTPException(status_code=409, detail="No new playbook is implemented for this category")
    try:
        row = response_service.record_plan(db, incident, facts, as_of=datetime.now(timezone.utc))
        db.commit()
        db.refresh(row)
        return row
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/{incident_id}/response-plan", response_model=PlanRevision)
def get_response_plan(incident_id: uuid.UUID, db: Session = Depends(get_db)):
    row = response_service.latest(db, incident_id)
    if row is None:
        raise HTTPException(status_code=409, detail="No typed response plan is recorded")
    return row


@router.get("/{incident_id}/plans", response_model=list[PlanRevision])
def plan_history(incident_id: uuid.UUID, db: Session = Depends(get_db)):
    return response_service.revisions(db, incident_id)


@router.get("/{incident_id}/completions", response_model=list[ActionCompletion])
def completions(incident_id: uuid.UUID, db: Session = Depends(get_db)):
    return response_service.completions(db, incident_id)


@router.post("/{incident_id}/plans/{plan_id}/actions/{action_id}/completion", response_model=ActionCompletion)
def mark_complete(incident_id: uuid.UUID, plan_id: uuid.UUID, action_id: str, payload: ActionCompletionRequest, db: Session = Depends(get_db)):
    try:
        return response_service.complete(db, _get_incident(db, incident_id), plan_id, action_id, payload)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Action not available for this case plan") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
