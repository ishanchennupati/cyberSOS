"""Persist validated facts and immutable, source-snapshotted plan revisions."""
from datetime import datetime, timezone
import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.domain.facts import IncidentFacts
from app.domain.playbooks import evaluate
from app.domain.policy import check_values
from app.domain.response import ActionCompletionRequest, PlanRevision, ResponsePlan
from app.models.incident import Incident, IncidentStatus, IncidentType
from app.models.response import ResponsePlanRecord, ActionCompletionRecord


def record_plan(db: Session, incident: Incident, facts: IncidentFacts, *, as_of: datetime) -> ResponsePlanRecord:
    check_values(facts.model_dump(mode="json"))
    # SessionLocal disables autoflush. Preserve legacy triage edits before the
    # lock refreshes the current row/revision from the database.
    db.flush()
    # Lock the case while assigning revisions (PostgreSQL); unique constraint also
    # protects against duplicate revisions on SQLite/concurrent writes.
    incident = db.scalars(select(Incident).where(Incident.id == incident.id)
        .with_for_update().execution_options(populate_existing=True)).one()
    from app.models.evidence import Evidence
    for provenance in facts.provenance:
        if provenance.evidence_id is not None:
            evidence = db.get(Evidence, provenance.evidence_id)
            tombstone = provenance.source_deleted and any(p.get('evidence_id')==str(provenance.evidence_id) and
                p.get('field')==provenance.field and p.get('source_deleted') and p.get('identifier_value')==provenance.identifier_value
                for p in (incident.facts or {}).get('provenance',[]))
            if evidence is not None and evidence.incident_id != incident.id or evidence is None and not tombstone:
                raise ValueError("Fact source evidence does not belong to this case")
    plan = evaluate(facts, as_of=as_of)
    incident.plan_revision += 1
    incident.facts = facts.model_dump(mode="json")
    incident.incident_type = IncidentType.other if facts.kind == 'incident_understanding' else IncidentType.financial_fraud
    incident.playbook_id = plan.playbook_id
    incident.playbook_version = plan.playbook_version
    incident.fact_schema_version = plan.fact_schema_version
    incident.urgency = plan.urgency
    incident.urgency_computed_at = plan.evaluated_at
    incident.recovery_window = None
    incident.urgency_score = None
    incident.amount = facts.amount
    incident.occurred_at = facts.occurred_at
    incident.incident_time = facts.occurred_at
    incident.payment_method = facts.payment_method
    incident.transaction_id = facts.transaction_id
    incident.transaction_status = facts.transaction_status
    incident.is_account_compromised = facts.account_compromised
    incident.is_remote_access_granted = facts.remote_access
    incident.is_credentials_exposed = facts.credentials_exposed
    incident.unauthorized_activity_continuing = facts.ongoing_loss
    incident.evidence_available = facts.evidence_available
    incident.status = IncidentStatus.action_required
    row = ResponsePlanRecord(incident_id=incident.id, revision=incident.plan_revision, plan=plan.model_dump(mode="json"))
    db.add(row)
    db.flush()
    return row


def revisions(db: Session, incident_id: uuid.UUID) -> list[ResponsePlanRecord]:
    return list(db.scalars(select(ResponsePlanRecord).where(ResponsePlanRecord.incident_id == incident_id).order_by(ResponsePlanRecord.revision)))


def latest(db: Session, incident_id: uuid.UUID) -> ResponsePlanRecord | None:
    return db.scalar(select(ResponsePlanRecord).where(ResponsePlanRecord.incident_id == incident_id).order_by(ResponsePlanRecord.revision.desc()).limit(1))


def completions(db: Session, incident_id: uuid.UUID) -> list[ActionCompletionRecord]:
    return list(db.scalars(select(ActionCompletionRecord).where(
        ActionCompletionRecord.incident_id == incident_id).order_by(ActionCompletionRecord.updated_at)))


def complete(db: Session, incident: Incident, plan_id: uuid.UUID, action_id: str, payload: ActionCompletionRequest) -> ActionCompletionRecord:
    plan = db.get(ResponsePlanRecord, plan_id)
    if plan is None or plan.incident_id != incident.id:
        raise LookupError()
    snapshot = ResponsePlan.model_validate(plan.plan)
    if not any(a.id == action_id and a.can_mark_complete for a in snapshot.actions):
        raise LookupError()
    check_values(payload.model_dump())
    row = db.scalar(select(ActionCompletionRecord).where(ActionCompletionRecord.plan_id == plan_id, ActionCompletionRecord.action_id == action_id))
    if row is None:
        row = ActionCompletionRecord(incident_id=incident.id, plan_id=plan_id, action_id=action_id, completed=payload.completed)
        db.add(row)
    row.completed = payload.completed
    row.user_note = payload.user_note
    row.user_recorded_reference = payload.user_recorded_reference
    row.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(row)
    return row
