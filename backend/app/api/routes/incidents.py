import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.schemas.incident import (
    ActionPlanResponse,
    IncidentCreate,
    IncidentDetailsUpdate,
    EvidenceRead,
    IncidentRead,
    TriageRequest,
)
from app.services import incident_service

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


@router.post("/{incident_id}/evidence", response_model=EvidenceRead, status_code=201)
def upload_evidence(
    incident_id: uuid.UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> EvidenceRead:
    incident = incident_service.get_incident(db, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    try:
        return incident_service.save_evidence(db, incident, file, get_settings().EVIDENCE_STORAGE_DIR)
    except ValueError as exc:
        raise HTTPException(status_code=413, detail=str(exc)) from exc


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
