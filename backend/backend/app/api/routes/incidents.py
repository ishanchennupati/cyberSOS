import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.evidence import EvidenceReadinessResponse, GenerateSummaryResponse, IncidentDescriptionUpdate
from app.schemas.incident import (
    ActionPlanResponse,
    IncidentCreate,
    IncidentDetailsUpdate,
    IncidentRead,
    TriageRequest,
)
from app.services import evidence_service, incident_service
from app.services.incident_summary import generate_incident_summary

router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.post("", response_model=IncidentRead, status_code=201)
def create_incident(payload: IncidentCreate, db: Session = Depends(get_db)) -> IncidentRead:
    incident = incident_service.create_incident(db, payload)
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


@router.get("/{incident_id}/action-plan", response_model=ActionPlanResponse)
def get_action_plan(
    incident_id: uuid.UUID, db: Session = Depends(get_db)
) -> ActionPlanResponse:
    incident = incident_service.get_incident(db, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    if incident.urgency_computed_at is None:
        raise HTTPException(
            status_code=409,
            detail="This incident has not been triaged yet.",
        )
    return incident_service.build_action_plan(incident)


@router.patch("/{incident_id}/details", response_model=IncidentRead)
def update_incident_details(
    incident_id: uuid.UUID, payload: IncidentDetailsUpdate, db: Session = Depends(get_db)
) -> IncidentRead:
    incident = incident_service.get_incident(db, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    fields = payload.model_dump(exclude_unset=True)
    return incident_service.update_incident_details(db, incident, **fields)


@router.patch("/{incident_id}/description", response_model=IncidentRead)
def update_incident_description(
    incident_id: uuid.UUID, payload: IncidentDescriptionUpdate, db: Session = Depends(get_db)
) -> IncidentRead:
    incident = incident_service.get_incident(db, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident_service.update_incident_description(db, incident, payload.description)


@router.get("/{incident_id}/evidence-readiness", response_model=EvidenceReadinessResponse)
def get_evidence_readiness(
    incident_id: uuid.UUID, db: Session = Depends(get_db)
) -> EvidenceReadinessResponse:
    incident = incident_service.get_incident(db, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return evidence_service.compute_readiness(db, incident)


@router.post("/{incident_id}/generate-summary", response_model=GenerateSummaryResponse)
def generate_summary(
    incident_id: uuid.UUID, db: Session = Depends(get_db)
) -> GenerateSummaryResponse:
    incident = incident_service.get_incident(db, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    draft, provider = generate_incident_summary(
        incident=incident, user_description=incident.description or ""
    )
    return GenerateSummaryResponse(draft=draft, provider=provider)
