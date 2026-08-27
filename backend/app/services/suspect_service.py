from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.evidence import SuspectIdentifier
from app.schemas.evidence import SuspectIdentifierCreate, SuspectIdentifierUpdate


def create_suspect(
    db: Session, incident_id: uuid.UUID, payload: SuspectIdentifierCreate
) -> SuspectIdentifier:
    suspect = SuspectIdentifier(
        incident_id=incident_id,
        type=payload.type,
        value=payload.value,
        source_evidence_id=payload.source_evidence_id,
        verified=False,  # never auto-verified — spec section 19
    )
    db.add(suspect)
    db.commit()
    db.refresh(suspect)
    return suspect


def list_suspects(db: Session, incident_id: uuid.UUID) -> list[SuspectIdentifier]:
    stmt = (
        select(SuspectIdentifier)
        .where(SuspectIdentifier.incident_id == incident_id)
        .order_by(SuspectIdentifier.created_at)
    )
    return list(db.scalars(stmt))


def get_suspect(db: Session, suspect_id: uuid.UUID) -> SuspectIdentifier | None:
    return db.get(SuspectIdentifier, suspect_id)


def update_suspect(
    db: Session, suspect: SuspectIdentifier, payload: SuspectIdentifierUpdate
) -> SuspectIdentifier:
    if payload.type is not None:
        suspect.type = payload.type
    if payload.value is not None:
        suspect.value = payload.value.strip()
    if payload.verified is not None:
        suspect.verified = payload.verified
    db.commit()
    db.refresh(suspect)
    return suspect


def delete_suspect(db: Session, suspect: SuspectIdentifier) -> None:
    db.delete(suspect)
    db.commit()
