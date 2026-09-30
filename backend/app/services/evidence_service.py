from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi import UploadFile
from app.core.config import get_settings

from app.models.evidence import Evidence, EvidenceType, ExtractionStatus, VerificationStatus
from app.models.incident import Incident
from app.schemas.evidence import (
    ComparisonResult,
    EvidenceReadinessResponse,
    EvidenceUpdate,
    ExtractedFinancialData,
    FieldComparison,
    ReadinessItem,
    EvidenceRead,
    VerifyRequest,
    VerifyResponse,
)
from app.services import hash_service, storage_service
from app.services.evidence_extraction import extract_evidence
from app.services.file_validation import FileValidationError, validate_evidence_file
from app.domain.policy import EvidenceContentKind, EvidencePolicy, POLICIES, check_values
from app.services.incident_presentation import format_inr

MAX_DESCRIPTION_LEN = 2000


def to_read(evidence: Evidence) -> EvidenceRead:
    result = EvidenceRead.model_validate(evidence)
    result.preview_url = f"/api/v1/evidence/{evidence.id}/file"
    return result


def read_original(evidence: Evidence) -> tuple[bytes | None, str | None]:
    backend = storage_service.get_storage_backend()
    # Private originals stay behind the case-authenticated API, including cloud storage.
    return backend.download(evidence.storage_path), None


async def upload_evidence(db: Session, incident: Incident, upload: UploadFile, *,
                          evidence_type: EvidenceType, description: str | None,
                          content_kind: EvidenceContentKind = EvidenceContentKind.general_document) -> Evidence:
    # Bound the application read even for requests lacking Content-Length.
    data = await upload.read(get_settings().max_evidence_file_size_bytes + 1)
    policy = POLICIES.get(incident.playbook_id, EvidencePolicy())
    policy.check(content_kind, (description or "") + " " + (upload.filename or ""))
    if upload.content_type == "text/plain":
        policy.check(content_kind, data.decode("utf-8", errors="replace"))
    evidence = create_evidence(db, incident, filename=upload.filename or "evidence",
                              mime_type=upload.content_type or "application/octet-stream",
                              file_bytes=data, evidence_type=evidence_type, description=description)
    from app.services.timeline_service import log_event
    log_event(db, incident.id, event_type="evidence_uploaded",
              description=f"{evidence.original_filename} uploaded"[:500], source_evidence_id=evidence.id)
    return evidence


def verify_for_incident(db: Session, evidence: Evidence, incident: Incident,
                       payload: VerifyRequest) -> VerifyResponse:
    comparison = compare_with_incident(incident, payload.extracted_data.model_dump())
    status = payload.verification_status if comparison.all_match else VerificationStatus.needs_review
    updated = verify_evidence(db, evidence, payload.extracted_data, status)
    if status == VerificationStatus.verified:
        from app.services.timeline_service import log_event
        log_event(db, incident.id, event_type="evidence_verified",
                  description=f"{evidence.original_filename} verified"[:500], source_evidence_id=evidence.id)
    return VerifyResponse(evidence=to_read(updated), comparison=comparison)


def create_evidence(
    db: Session,
    incident: Incident,
    *,
    filename: str,
    mime_type: str,
    file_bytes: bytes,
    evidence_type: EvidenceType,
    description: str | None,
) -> Evidence:
    """
    Full upload pipeline (spec section 3), minus the client-side preview
    step which happens in the UI before this is called:
      validate -> hash -> store -> save metadata
    """
    validate_evidence_file(filename=filename, mime_type=mime_type, file_bytes=file_bytes)

    evidence_id = uuid.uuid4()
    digest = hash_service.sha256_hex(file_bytes)
    storage_path = storage_service.build_storage_path(incident.id, evidence_id, filename)

    backend = storage_service.get_storage_backend()
    backend.upload(storage_path, file_bytes, mime_type)

    evidence = Evidence(
        id=evidence_id,
        incident_id=incident.id,
        original_filename=filename,
        storage_path=storage_path,
        mime_type=mime_type,
        file_size=len(file_bytes),
        sha256_hash=digest,
        evidence_type=evidence_type,
        description=description,
        extraction_status=ExtractionStatus.pending,
        extracted_data=None,
        verification_status=VerificationStatus.unverified,
    )
    db.add(evidence)
    try:
        db.commit()
    except Exception:
        db.rollback()
        backend.delete(storage_path)
        raise
    db.refresh(evidence)
    return evidence


def list_evidence(db: Session, incident_id: uuid.UUID) -> list[Evidence]:
    stmt = select(Evidence).where(Evidence.incident_id == incident_id).order_by(Evidence.uploaded_at)
    return list(db.scalars(stmt))


def get_evidence(db: Session, evidence_id: uuid.UUID) -> Evidence | None:
    return db.get(Evidence, evidence_id)


def update_evidence(db: Session, evidence: Evidence, payload: EvidenceUpdate) -> Evidence:
    check_values(payload.model_dump(mode="json"))
    if payload.evidence_type is not None:
        evidence.evidence_type = payload.evidence_type
    if payload.description is not None:
        evidence.description = payload.description[:MAX_DESCRIPTION_LEN]
    if payload.extracted_data is not None:
        # Citizen editing extracted fields — this alone does not mark the
        # evidence verified. Verification is only set via /verify.
        evidence.extracted_data = payload.extracted_data.model_dump()
        if evidence.verification_status == VerificationStatus.verified:
            evidence.verification_status = VerificationStatus.needs_review
    db.commit()
    db.refresh(evidence)
    return evidence


def delete_evidence(db: Session, evidence: Evidence) -> None:
    backend = storage_service.get_storage_backend()
    backend.delete(evidence.storage_path)
    db.delete(evidence)
    db.commit()


def run_extraction(db: Session, evidence: Evidence) -> Evidence:
    if evidence.verification_status == VerificationStatus.verified:
        raise ValueError("Verified evidence cannot be re-extracted. Edit the reviewed details explicitly.")
    evidence.extraction_status = ExtractionStatus.processing
    db.commit()

    backend = storage_service.get_storage_backend()
    try:
        file_bytes = backend.download(evidence.storage_path)
    except storage_service.StorageError:
        evidence.extraction_status = ExtractionStatus.failed
        db.commit()
        db.refresh(evidence)
        return evidence

    result = extract_evidence(
        file_bytes=file_bytes,
        mime_type=evidence.mime_type,
        filename=evidence.original_filename,
        evidence_type=evidence.evidence_type,
    )
    try:
        check_values(result.data.model_dump() if result.data else None)
    except ValueError:
        evidence.extraction_status = ExtractionStatus.failed
        evidence.extracted_data = None
        db.commit()
        db.refresh(evidence)
        return evidence
    evidence.extraction_status = result.status
    evidence.extracted_data = result.data.model_dump() if result.data else None
    # Extraction never verifies anything on its own.
    if evidence.verification_status == VerificationStatus.unverified and result.data:
        evidence.verification_status = VerificationStatus.needs_review

    db.commit()
    db.refresh(evidence)
    return evidence


def verify_evidence(
    db: Session, evidence: Evidence, data: ExtractedFinancialData, status: VerificationStatus
) -> Evidence:
    """The citizen has reviewed (and possibly corrected) the extracted
    fields and explicitly confirmed them. This is the ONLY path that can
    set verification_status to verified."""
    check_values(data.model_dump(mode="json"))
    evidence.extracted_data = data.model_dump()
    evidence.verification_status = status
    db.commit()
    db.refresh(evidence)
    return evidence


# --- Comparison with incident (Section 11) -----------------------------------

_COMPARABLE_FIELDS: tuple[tuple[str, str], ...] = (
    ("amount", "Amount"),
    ("payment_method", "Payment method"),
    ("transaction_id", "Transaction ID"),
    ("bank", "Bank"),
)


def _incident_field_value(incident: Incident, field: str) -> str | None:
    if field == "amount":
        return f"₹{format_inr(incident.amount)}" if incident.amount is not None else None
    if field == "payment_method":
        value = incident.payment_method.value if incident.payment_method else None
        return value.replace("_", " ").title() if value else None
    if field == "transaction_id":
        return incident.transaction_id
    if field == "bank":
        return incident.bank
    return None


def _evidence_field_value(data: dict, field: str) -> str | None:
    value = data.get(field)
    if value is None:
        return None
    if field == "amount":
        try:
            return f"₹{format_inr(float(value))}"
        except (TypeError, ValueError):
            return str(value)
    if field == "payment_method":
        return str(value).replace("_", " ").title()
    return str(value)


def _values_match(field: str, incident_value: str | None, evidence_value: str | None) -> bool:
    if incident_value is None or evidence_value is None:
        return True  # nothing to disagree on
    a = incident_value.strip().lower().replace(",", "")
    b = evidence_value.strip().lower().replace(",", "")
    return a == b


def compare_with_incident(incident: Incident, extracted_data: dict | None) -> ComparisonResult:
    if not extracted_data:
        return ComparisonResult(has_incident_data=True, all_match=True, comparisons=[])

    comparisons: list[FieldComparison] = []
    for field, label in _COMPARABLE_FIELDS:
        incident_value = _incident_field_value(incident, field)
        evidence_value = _evidence_field_value(extracted_data, field)
        if incident_value is None and evidence_value is None:
            continue
        matches = _values_match(field, incident_value, evidence_value)
        comparisons.append(
            FieldComparison(
                field=field,
                label=label,
                incident_value=incident_value,
                evidence_value=evidence_value,
                matches=matches,
            )
        )

    all_match = all(c.matches for c in comparisons)
    return ComparisonResult(
        has_incident_data=len(comparisons) > 0, all_match=all_match, comparisons=comparisons
    )


# --- Readiness (Section 24/25) ------------------------------------------------


def compute_readiness(
    db: Session, incident: Incident
) -> EvidenceReadinessResponse:
    evidence_items = list_evidence(db, incident.id)
    has_transaction_evidence = any(
        e.evidence_type
        in (
            EvidenceType.bank_statement,
            EvidenceType.transaction_receipt,
            EvidenceType.payment_screenshot,
        )
        for e in evidence_items
    )
    has_bank_statement = any(e.evidence_type == EvidenceType.bank_statement for e in evidence_items)
    has_sms = any(e.evidence_type == EvidenceType.sms_message for e in evidence_items)
    has_chat_or_email = any(
        e.evidence_type in (EvidenceType.chat_conversation, EvidenceType.email)
        for e in evidence_items
    )
    has_url = any(e.evidence_type == EvidenceType.website_url for e in evidence_items)

    from app.services.suspect_service import list_suspects

    suspects = list_suspects(db, incident.id)
    has_suspect_phone = any(s.type.value == "phone" for s in suspects)

    items = [
        ReadinessItem(id="transaction_evidence", label="Transaction evidence", met=has_transaction_evidence),
        ReadinessItem(
            id="transaction_id", label="Transaction ID", met=bool(incident.transaction_id)
        ),
        ReadinessItem(id="amount", label="Amount", met=incident.amount is not None),
        ReadinessItem(
            id="payment_method",
            label="Payment method",
            met=incident.payment_method is not None and incident.payment_method.value != "unknown",
        ),
        ReadinessItem(
            id="incident_date", label="Incident date", met=bool(incident.occurred_at or incident.incident_time)
        ),
        ReadinessItem(id="bank_statement", label="Bank statement", met=has_bank_statement),
        ReadinessItem(id="sms_message", label="SMS / message", met=has_sms),
        ReadinessItem(id="chat_or_email", label="Chat / email evidence", met=has_chat_or_email),
        ReadinessItem(id="suspicious_url", label="Suspicious URL", met=has_url),
        ReadinessItem(id="suspect_phone", label="Suspect phone number", met=has_suspect_phone),
        ReadinessItem(
            id="description", label="Incident description", met=bool(incident.description and incident.description.strip())
        ),
    ]

    percent = round(100 * sum(1 for i in items if i.met) / len(items))
    missing = [i.label for i in items if not i.met]
    missing_summary = (
        None if not missing else "Still missing: " + ", ".join(missing[:4]) + (" and more" if len(missing) > 4 else "")
    )

    return EvidenceReadinessResponse(percent=percent, items=items, missing_summary=missing_summary)
