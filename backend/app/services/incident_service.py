"""
Business logic for incidents, kept out of the API route handlers.

Phase 0 keeps this intentionally simple: create, fetch. Urgency is set with
a placeholder rule (not an AI system) so the field is meaningful for the
UI to render even before the real triage logic exists.
"""

import uuid

from sqlalchemy.orm import Session

from app.models.incident import Incident, IncidentStatus, Urgency
from app.schemas.incident import IncidentCreate


def _placeholder_urgency(payload: IncidentCreate) -> Urgency:
    """
    Very simple placeholder heuristic, NOT the real triage engine.
    Larger amounts are treated as more urgent so the field isn't always
    the same value. This will be replaced by real triage logic later.
    """
    if payload.amount is None:
        return Urgency.medium
    if payload.amount >= 50000:
        return Urgency.critical
    if payload.amount >= 10000:
        return Urgency.high
    if payload.amount > 0:
        return Urgency.medium
    return Urgency.low


def create_incident(db: Session, payload: IncidentCreate) -> Incident:
    incident = Incident(
        incident_type=payload.incident_type,
        payment_method=payload.payment_method,
        amount=payload.amount,
        incident_time=payload.incident_time,
        urgency=_placeholder_urgency(payload),
        status=IncidentStatus.draft,
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)
    return incident


def get_incident(db: Session, incident_id: uuid.UUID) -> Incident | None:
    return db.get(Incident, incident_id)
