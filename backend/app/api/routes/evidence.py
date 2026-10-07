"""Evidence HTTP boundary; validation, storage and verification live in services."""
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import RedirectResponse, Response
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.evidence import EvidenceType
from app.schemas.evidence import ComparisonResult, EvidenceRead, EvidenceUpdate, VerifyRequest, VerifyResponse
from app.services import evidence_service, incident_service, storage_service
from app.services.file_validation import FileValidationError
from app.services.case_access import authorize_case_resource
from app.domain.policy import EvidenceContentKind
from app.schemas.evidence_intelligence import AnalyzeRequest

router = APIRouter(tags=["evidence"], dependencies=[Depends(authorize_case_resource)])


def _incident(db, incident_id):
    incident = incident_service.get_incident(db, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


def _evidence(db, evidence_id):
    evidence = evidence_service.get_evidence(db, evidence_id)
    if evidence is None:
        raise HTTPException(status_code=404, detail="Evidence not found")
    return evidence


@router.post("/incidents/{incident_id}/evidence", response_model=EvidenceRead, status_code=201)
async def upload_evidence(
    incident_id: uuid.UUID,
    file: UploadFile = File(...),
    evidence_type: EvidenceType = Form(default=EvidenceType.other_document),
    description: str | None = Form(default=None, max_length=2000),
    content_kind: EvidenceContentKind = Form(default=EvidenceContentKind.general_document),
    upload_id: uuid.UUID | None = Form(default=None),
    staged_for_chat: bool = Form(default=False),
    db: Session = Depends(get_db),
) -> EvidenceRead:
    incident = _incident(db, incident_id)
    try:
        return evidence_service.to_read(await evidence_service.upload_evidence(
            db, incident, file, evidence_type=evidence_type, description=description, content_kind=content_kind,
            upload_id=upload_id, staged_for_chat=staged_for_chat,
        ))
    except (FileValidationError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except storage_service.StorageError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/incidents/{incident_id}/evidence", response_model=list[EvidenceRead])
def list_incident_evidence(incident_id: uuid.UUID, db: Session = Depends(get_db)):
    _incident(db, incident_id)
    return [evidence_service.to_read(e) for e in evidence_service.list_evidence(db, incident_id)]


@router.get("/evidence/{evidence_id}", response_model=EvidenceRead)
def get_evidence(evidence_id: uuid.UUID, db: Session = Depends(get_db)):
    return evidence_service.to_read(_evidence(db, evidence_id))


@router.get("/evidence/{evidence_id}/file")
def get_evidence_file(evidence_id: uuid.UUID, db: Session = Depends(get_db)):
    evidence = _evidence(db, evidence_id)
    try:
        data, signed_url = evidence_service.read_original(evidence)
    except storage_service.StorageError as exc:
        raise HTTPException(status_code=404, detail="File not available") from exc
    if signed_url:
        return RedirectResponse(signed_url)
    return Response(content=data, media_type=evidence.mime_type or "application/octet-stream",
                    headers={"X-Content-Type-Options": "nosniff", "Content-Disposition": "inline", "Cache-Control": "no-store"})


@router.patch("/evidence/{evidence_id}", response_model=EvidenceRead)
def patch_evidence(evidence_id: uuid.UUID, payload: EvidenceUpdate, db: Session = Depends(get_db)):
    return evidence_service.to_read(evidence_service.update_evidence(db, _evidence(db, evidence_id), payload))


@router.delete("/evidence/{evidence_id}", status_code=204)
def delete_evidence(evidence_id: uuid.UUID, db: Session = Depends(get_db)):
    evidence_service.delete_evidence(db, _evidence(db, evidence_id))


@router.post("/evidence/{evidence_id}/extract", response_model=EvidenceRead)
def extract_evidence(evidence_id: uuid.UUID, db: Session = Depends(get_db)):
    evidence = _evidence(db, evidence_id)
    from app.services.conversation_service import require_conversation_turn
    require_conversation_turn(db, evidence.incident_id)
    try:
        return evidence_service.to_read(evidence_service.run_extraction(db, evidence))
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/evidence/{evidence_id}/verify", response_model=VerifyResponse)
def verify_evidence(evidence_id: uuid.UUID, payload: VerifyRequest, db: Session = Depends(get_db)):
    evidence = _evidence(db, evidence_id)
    from app.services.conversation_service import require_conversation_turn
    require_conversation_turn(db, evidence.incident_id)
    return evidence_service.verify_for_incident(db, evidence, _incident(db, evidence.incident_id), payload)


@router.post('/evidence/{evidence_id}/analyze')
def analyze_evidence(evidence_id: uuid.UUID, payload: AnalyzeRequest, db: Session = Depends(get_db)):
    from app.services.evidence_intelligence import analyze
    return analyze(db, _evidence(db, evidence_id), payload)


@router.get("/evidence/{evidence_id}/compare", response_model=ComparisonResult)
def compare_evidence(evidence_id: uuid.UUID, db: Session = Depends(get_db)):
    evidence = _evidence(db, evidence_id)
    return evidence_service.compare_with_incident(_incident(db, evidence.incident_id), evidence.extracted_data)
