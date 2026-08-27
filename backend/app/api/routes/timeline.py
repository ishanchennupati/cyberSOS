import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.evidence import TimelineEventCreate, TimelineEventRead, TimelineEventUpdate
from app.services import incident_service, timeline_service

router = APIRouter(tags=["timeline"])


@router.post(
    "/incidents/{incident_id}/timeline",
    response_model=TimelineEventRead,
    status_code=201,
)
def create_event(
    incident_id: uuid.UUID, payload: TimelineEventCreate, db: Session = Depends(get_db)
) -> TimelineEventRead:
    incident = incident_service.get_incident(db, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return timeline_service.create_event(db, incident_id, payload)


@router.get("/incidents/{incident_id}/timeline", response_model=list[TimelineEventRead])
def list_events(incident_id: uuid.UUID, db: Session = Depends(get_db)) -> list[TimelineEventRead]:
    incident = incident_service.get_incident(db, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return timeline_service.list_events(db, incident_id)


@router.patch("/timeline/{event_id}", response_model=TimelineEventRead)
def update_event(
    event_id: uuid.UUID, payload: TimelineEventUpdate, db: Session = Depends(get_db)
) -> TimelineEventRead:
    event = timeline_service.get_event(db, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Timeline event not found")
    return timeline_service.update_event(db, event, payload)


@router.delete("/timeline/{event_id}", status_code=204)
def delete_event(event_id: uuid.UUID, db: Session = Depends(get_db)) -> None:
    event = timeline_service.get_event(db, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Timeline event not found")
    timeline_service.delete_event(db, event)
