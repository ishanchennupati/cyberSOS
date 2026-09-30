import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.evidence import (
    SuspectIdentifierCreate,
    SuspectIdentifierRead,
    SuspectIdentifierUpdate,
)
from app.services import incident_service, suspect_service
from app.services.case_access import authorize_case_resource

router = APIRouter(tags=["suspects"], dependencies=[Depends(authorize_case_resource)])


@router.post(
    "/incidents/{incident_id}/suspects",
    response_model=SuspectIdentifierRead,
    status_code=201,
)
def create_suspect(
    incident_id: uuid.UUID, payload: SuspectIdentifierCreate, db: Session = Depends(get_db)
) -> SuspectIdentifierRead:
    incident = incident_service.get_incident(db, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    try:
        return suspect_service.create_suspect(db, incident_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/incidents/{incident_id}/suspects", response_model=list[SuspectIdentifierRead])
def list_suspects(incident_id: uuid.UUID, db: Session = Depends(get_db)) -> list[SuspectIdentifierRead]:
    incident = incident_service.get_incident(db, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return suspect_service.list_suspects(db, incident_id)


@router.patch("/suspects/{suspect_id}", response_model=SuspectIdentifierRead)
def update_suspect(
    suspect_id: uuid.UUID, payload: SuspectIdentifierUpdate, db: Session = Depends(get_db)
) -> SuspectIdentifierRead:
    suspect = suspect_service.get_suspect(db, suspect_id)
    if suspect is None:
        raise HTTPException(status_code=404, detail="Suspect identifier not found")
    return suspect_service.update_suspect(db, suspect, payload)


@router.delete("/suspects/{suspect_id}", status_code=204)
def delete_suspect(suspect_id: uuid.UUID, db: Session = Depends(get_db)) -> None:
    suspect = suspect_service.get_suspect(db, suspect_id)
    if suspect is None:
        raise HTTPException(status_code=404, detail="Suspect identifier not found")
    suspect_service.delete_suspect(db, suspect)
