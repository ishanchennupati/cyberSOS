from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.evidence import TimelineEvent
from app.schemas.evidence import TimelineEventCreate, TimelineEventUpdate
from app.domain.policy import check_values


def create_event(
    db: Session, incident_id: uuid.UUID, payload: TimelineEventCreate
) -> TimelineEvent:
    check_values(payload.model_dump(mode="json"))
    if payload.source_evidence_id is not None:
        from app.services.evidence_service import get_evidence
        source = get_evidence(db, payload.source_evidence_id)
        if source is None or source.incident_id != incident_id:
            raise ValueError("Source evidence does not belong to this incident.")
    event = TimelineEvent(
        incident_id=incident_id,
        event_time=payload.event_time,
        event_type=payload.event_type,
        description=payload.description,
        source_evidence_id=payload.source_evidence_id,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def list_events(db: Session, incident_id: uuid.UUID) -> list[TimelineEvent]:
    stmt = (
        select(TimelineEvent)
        .where(TimelineEvent.incident_id == incident_id)
        .order_by(TimelineEvent.event_time)
    )
    return list(db.scalars(stmt))


def get_event(db: Session, event_id: uuid.UUID) -> TimelineEvent | None:
    return db.get(TimelineEvent, event_id)


def update_event(db: Session, event: TimelineEvent, payload: TimelineEventUpdate) -> TimelineEvent:
    check_values(payload.model_dump(mode="json"))
    if payload.event_time is not None:
        event.event_time = payload.event_time
    if payload.event_type is not None:
        event.event_type = payload.event_type
    if payload.description is not None:
        event.description = payload.description
    db.commit()
    db.refresh(event)
    return event


def delete_event(db: Session, event: TimelineEvent) -> None:
    db.delete(event)
    db.commit()


def log_event(
    db: Session,
    incident_id: uuid.UUID,
    *,
    event_type: str,
    description: str,
    source_evidence_id: uuid.UUID | None = None,
) -> TimelineEvent:
    """Convenience helper other services call to auto-log system events
    (e.g. 'Evidence uploaded') without duplicating the create logic."""
    from datetime import datetime, timezone

    return create_event(
        db,
        incident_id,
        TimelineEventCreate(
            event_time=datetime.now(timezone.utc),
            event_type=event_type,
            description=description,
            source_evidence_id=source_evidence_id,
        ),
    )
