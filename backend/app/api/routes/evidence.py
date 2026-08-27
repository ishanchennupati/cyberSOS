import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import RedirectResponse, Response
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.evidence import EvidenceType, VerificationStatus
from app.schemas.evidence import (
    ComparisonResult,
    EvidenceRead,
    EvidenceUpdate,
    VerifyRequest,
    VerifyResponse,
)
from app.services import evidence_service, incident_service, storage_service, timeline_service
from app.services.file_validation import FileValidationError

router = APIRouter(tags=["evidence"])


def _to_read(db: Session, evidence) -> EvidenceRead:
    read = EvidenceRead.model_validate(evidence)
    backend = storage_service.get_storage_backend()
    signed = backend.signed_url(evidence.storage_path)
    read.preview_url = signed or f"/api/v1/evidence/{evidence.id}/file"
    return read


def _get_incident_or_404(db: Session, incident_id: uuid.UUID):
    incident = incident_service.get_incident(db, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


def _get_evidence_or_404(db: Session, evidence_id: uuid.UUID):
    evidence = evidence_service.get_evidence(db, evidence_id)
    if evidence is None:
        raise HTTPException(status_code=404, detail="Evidence not found")
    return evidence


@router.post(
    "/incidents/{incident_id}/evidence",
    response_model=EvidenceRead,
    status_code=201,
)
async def upload_evidence(
    incident_id: uuid.UUID,
    file: UploadFile = File(...),
    evidence_type: EvidenceType = Form(...),
    description: str | None = Form(default=None),
    db: Session = Depends(get_db),
) -> EvidenceRead:
    incident = _get_incident_or_404(db, incident_id)

    file_bytes = await file.read()
    try:
        evidence = evidence_service.create_evidence(
            db,
            incident,
            filename=file.filename or "evidence",
            mime_type=file.content_type or "application/octet-stream",
            file_bytes=file_bytes,
            evidence_type=evidence_type,
            description=description,
        )
    except FileValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except storage_service.StorageError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    timeline_service.log_event(
        db,
        incident_id,
        event_type="evidence_uploaded",
        description=f"{evidence.original_filename} uploaded",
        source_evidence_id=evidence.id,
    )
    return _to_read(db, evidence)


@router.get("/incidents/{incident_id}/evidence", response_model=list[EvidenceRead])
def list_incident_evidence(incident_id: uuid.UUID, db: Session = Depends(get_db)) -> list[EvidenceRead]:
    _get_incident_or_404(db, incident_id)
    items = evidence_service.list_evidence(db, incident_id)
    return [_to_read(db, e) for e in items]


@router.get("/evidence/{evidence_id}", response_model=EvidenceRead)
def get_evidence(evidence_id: uuid.UUID, db: Session = Depends(get_db)) -> EvidenceRead:
    evidence = _get_evidence_or_404(db, evidence_id)
    return _to_read(db, evidence)


@router.get("/evidence/{evidence_id}/file")
def get_evidence_file(evidence_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Serves the original file. If Supabase Storage is configured, redirects
    to a freshly minted signed URL (short-lived, private bucket). Otherwise
    streams from local disk. Never exposes a permanent public URL.
    """
    evidence = _get_evidence_or_404(db, evidence_id)
    backend = storage_service.get_storage_backend()
    signed = backend.signed_url(evidence.storage_path)
    if signed:
        return RedirectResponse(signed)
    try:
        data = backend.download(evidence.storage_path)
    except storage_service.StorageError as exc:
        raise HTTPException(status_code=404, detail="File not available") from exc
    return Response(content=data, media_type=evidence.mime_type)


@router.patch("/evidence/{evidence_id}", response_model=EvidenceRead)
def patch_evidence(
    evidence_id: uuid.UUID, payload: EvidenceUpdate, db: Session = Depends(get_db)
) -> EvidenceRead:
    evidence = _get_evidence_or_404(db, evidence_id)
    updated = evidence_service.update_evidence(db, evidence, payload)
    return _to_read(db, updated)


@router.delete("/evidence/{evidence_id}", status_code=204)
def delete_evidence(evidence_id: uuid.UUID, db: Session = Depends(get_db)) -> None:
    evidence = _get_evidence_or_404(db, evidence_id)
    evidence_service.delete_evidence(db, evidence)


@router.post("/evidence/{evidence_id}/extract", response_model=EvidenceRead)
def extract_evidence(evidence_id: uuid.UUID, db: Session = Depends(get_db)) -> EvidenceRead:
    evidence = _get_evidence_or_404(db, evidence_id)
    updated = evidence_service.run_extraction(db, evidence)
    return _to_read(db, updated)


@router.post("/evidence/{evidence_id}/verify", response_model=VerifyResponse)
def verify_evidence(
    evidence_id: uuid.UUID, payload: VerifyRequest, db: Session = Depends(get_db)
) -> VerifyResponse:
    evidence = _get_evidence_or_404(db, evidence_id)
    incident = incident_service.get_incident(db, evidence.incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")

    comparison = evidence_service.compare_with_incident(incident, payload.extracted_data.model_dump())

    status = payload.verification_status
    if not comparison.all_match:
        status = VerificationStatus.needs_review

    updated = evidence_service.verify_evidence(db, evidence, payload.extracted_data, status)

    if status == VerificationStatus.verified:
        timeline_service.log_event(
            db,
            evidence.incident_id,
            event_type="evidence_verified",
            description=f"{evidence.original_filename} verified",
            source_evidence_id=evidence.id,
        )

    return VerifyResponse(evidence=_to_read(db, updated), comparison=comparison)


@router.get("/evidence/{evidence_id}/compare", response_model=ComparisonResult)
def compare_evidence(evidence_id: uuid.UUID, db: Session = Depends(get_db)) -> ComparisonResult:
    evidence = _get_evidence_or_404(db, evidence_id)
    incident = incident_service.get_incident(db, evidence.incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return evidence_service.compare_with_incident(incident, evidence.extracted_data)
