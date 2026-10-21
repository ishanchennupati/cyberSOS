import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, Request, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.incident import (
    ActionPlanResponse,
    IncidentCreate,
    IncidentDetailsUpdate,
    IncidentRead,
    TriageRequest,
)
from app.services import incident_service
from app.core.config import get_settings
from app.schemas.return_access import DeleteRequest
from app.schemas.evidence import EvidenceReadinessResponse, IncidentDescriptionUpdate, GenerateSummaryResponse
from app.services.case_access import authorize_case_resource, set_cookie
from app.services import response_service
from app.domain.facts import IncidentFacts
from app.domain.response import ActionCompletion, ActionCompletionRequest, PlanRevision
from datetime import datetime, timezone

router = APIRouter(prefix="/incidents", tags=["incidents"], dependencies=[Depends(authorize_case_resource)])


@router.post('/{incident_id}/save')
def save_case(incident_id: uuid.UUID, request: Request, db: Session = Depends(get_db)):
    from app.models.return_access import CaseOwner
    from app.services.return_access import session
    from app.services.lifecycle import touch, lock_active
    current = session(db, request, required=True, fresh=True)
    incident = lock_active(db, incident_id)
    owner = db.get(CaseOwner, incident_id)
    if owner and owner.account_id != current.account_id:
        raise HTTPException(409, 'This case is already saved to another account.')
    if not owner:
        db.add(CaseOwner(incident_id=incident_id, account_id=current.account_id))
    touch(incident)
    db.commit()
    return {'saved': True}


@router.post('/{incident_id}/recovery-code')
def recovery_code(incident_id: uuid.UUID, request: Request, db: Session = Depends(get_db)):
    from app.services.return_access import set_recovery, session
    from app.models.return_access import CaseOwner
    if db.get(CaseOwner, incident_id):
        session(db, request, required=True, fresh=True)
    return set_recovery(db, _get_incident(db, incident_id))


@router.delete('/{incident_id}')
def delete_case(incident_id: uuid.UUID, payload: DeleteRequest, response: Response, db: Session = Depends(get_db)):
    from app.services.lifecycle import request_deletion
    done = request_deletion(db, _get_incident(db, incident_id))
    response.delete_cookie('cybersos_case_'+str(incident_id), path=get_settings().API_V1_PREFIX)
    response.status_code = 200 if done else 202
    return {'deleted': done, 'access_revoked': True, 'cleanup_pending': not done}

from app.schemas.conversation import ConversationRead, TurnRequest
from app.services import conversation_service
from app.schemas.reporting import DraftRequest,ReportReview,ReportingDraft
from app.services import reporting


@router.get('/{incident_id}/reporting')
def reporting_preview(incident_id:uuid.UUID,response:Response,db:Session=Depends(get_db)):
    response.headers['Cache-Control']='private, no-store'
    return reporting.preview(db,_get_incident(db,incident_id))


@router.post('/{incident_id}/reporting/drafts',response_model=ReportingDraft)
def reporting_prepare(incident_id:uuid.UUID,payload:DraftRequest,response:Response,db:Session=Depends(get_db)):
    response.headers['Cache-Control']='private, no-store'
    return reporting.prepare(db,_get_incident(db,incident_id),payload)


@router.post('/{incident_id}/reporting/drafts/{draft_id}/review',response_model=ReportingDraft)
def reporting_review(incident_id:uuid.UUID,draft_id:uuid.UUID,payload:ReportReview,response:Response,db:Session=Depends(get_db)):
    response.headers['Cache-Control']='private, no-store'
    return reporting.review(db,_get_incident(db,incident_id),draft_id,payload)


@router.get('/{incident_id}/reporting/drafts/{draft_id}/export')
def reporting_export(incident_id:uuid.UUID,draft_id:uuid.UUID,format:str=Query('json',pattern='^(json|pdf|html)$'),db:Session=Depends(get_db)):
    from app.services import reporting_export as renderer
    data=reporting.export(db,_get_incident(db,incident_id),draft_id)
    headers={'Cache-Control':'private, no-store','X-Content-Type-Options':'nosniff',
        'Content-Security-Policy':"default-src 'none'; style-src 'unsafe-inline'; frame-ancestors 'none'"}
    if format=='pdf':
        headers['Content-Disposition']=f'attachment; filename="CyberSOS-{draft_id}.pdf"'
        return Response(renderer.pdf(data),media_type='application/pdf',headers=headers)
    if format=='html':return Response(renderer.printable(data),media_type='text/html',headers=headers)
    from fastapi.responses import JSONResponse
    headers['Content-Disposition']=f'attachment; filename="CyberSOS-{draft_id}.json"'
    return JSONResponse(data,headers=headers)


@router.get('/{incident_id}/conversation', response_model=ConversationRead)
def conversation(incident_id: uuid.UUID, db: Session = Depends(get_db)):
    return conversation_service.read(db, _get_incident(db, incident_id))


@router.post('/{incident_id}/resume', response_model=ConversationRead)
def resume_case(incident_id: uuid.UUID, db: Session = Depends(get_db)):
    from app.services.lifecycle import lock_active, touch
    incident = lock_active(db, incident_id)
    touch(incident)
    db.commit()
    return conversation_service.read(db, incident)


@router.post('/{incident_id}/conversation/turns', response_model=ConversationRead)
def conversation_turn(incident_id: uuid.UUID, payload: TurnRequest, db: Session = Depends(get_db)):
    try:
        return conversation_service.submit(db, _get_incident(db, incident_id), payload)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(422, 'Reply could not be saved. Check the structured answer and try again.') from exc


def _get_incident(db: Session, incident_id: uuid.UUID):
    incident = incident_service.get_incident(db, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.get("/{incident_id}/evidence-readiness", response_model=EvidenceReadinessResponse)
def get_readiness(incident_id: uuid.UUID, db: Session = Depends(get_db)):
    from app.services.evidence_service import compute_readiness
    return compute_readiness(db, _get_incident(db, incident_id))


@router.patch("/{incident_id}/description", response_model=IncidentRead)
def update_description(incident_id: uuid.UUID, payload: IncidentDescriptionUpdate,
                       db: Session = Depends(get_db)):
    return incident_service.update_description(db, _get_incident(db, incident_id), payload.description)


@router.post("/{incident_id}/generate-summary", response_model=GenerateSummaryResponse)
def generate_summary(incident_id: uuid.UUID, db: Session = Depends(get_db)):
    from app.models.conversation import ConversationState
    incident=_get_incident(db, incident_id)
    if db.get(ConversationState,incident.id) is not None or (incident.facts or {}).get('kind')=='incident_understanding':
        raise HTTPException(409,'Review the reporting packet in chat instead of generating a legacy summary.')
    return incident_service.generate_summary(incident)


@router.post("", response_model=IncidentRead, status_code=201)
def create_incident(payload: IncidentCreate, response: Response, db: Session = Depends(get_db)) -> IncidentRead:
    from sqlalchemy.exc import IntegrityError
    try:
        incident, token = incident_service.create_incident(db, payload)
    except IntegrityError:
        db.rollback()
        if not payload.creation_id:
            raise
        incident, token = incident_service.create_incident(db, payload)
    set_cookie(response, incident, token)
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
    conversation_service.require_conversation_turn(db, incident_id)
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


@router.get("/{incident_id}/action-plan", response_model=ActionPlanResponse)
def get_action_plan(
    incident_id: uuid.UUID, db: Session = Depends(get_db)
) -> ActionPlanResponse:
    incident = incident_service.get_incident(db, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    if incident.urgency_computed_at is None and incident.facts is None:
        raise HTTPException(
            status_code=409,
            detail="This incident has not been triaged yet.",
        )
    return incident_service.build_action_plan(incident, db=db)


@router.put("/{incident_id}/facts", response_model=PlanRevision)
def update_facts(incident_id: uuid.UUID, facts: IncidentFacts, db: Session = Depends(get_db)):
    conversation_service.require_conversation_turn(db, incident_id)
    incident = _get_incident(db, incident_id)
    if incident.incident_type.value != "financial_fraud":
        raise HTTPException(status_code=409, detail="No new playbook is implemented for this category")
    try:
        row = response_service.record_plan(db, incident, facts, as_of=datetime.now(timezone.utc))
        db.commit()
        db.refresh(row)
        return row
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/{incident_id}/response-plan", response_model=PlanRevision)
def get_response_plan(incident_id: uuid.UUID, db: Session = Depends(get_db)):
    row = response_service.latest(db, incident_id)
    if row is None:
        raise HTTPException(status_code=409, detail="No typed response plan is recorded")
    return row


@router.get("/{incident_id}/plans", response_model=list[PlanRevision])
def plan_history(incident_id: uuid.UUID, db: Session = Depends(get_db)):
    return response_service.revisions(db, incident_id)


@router.get("/{incident_id}/completions", response_model=list[ActionCompletion])
def completions(incident_id: uuid.UUID, db: Session = Depends(get_db)):
    return response_service.completions(db, incident_id)


@router.post("/{incident_id}/plans/{plan_id}/actions/{action_id}/completion", response_model=ActionCompletion)
def mark_complete(incident_id: uuid.UUID, plan_id: uuid.UUID, action_id: str, payload: ActionCompletionRequest, db: Session = Depends(get_db)):
    conversation_service.require_conversation_turn(db, incident_id)
    try:
        return response_service.complete(db, _get_incident(db, incident_id), plan_id, action_id, payload)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Action not available for this case plan") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
