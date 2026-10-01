"""Progression and durable turns only. Safety actions belong to Phase 1."""
from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError, OperationalError
from app.domain.facts import FACTS_ADAPTER, FactProvenance
from app.domain.playbooks import FIELDS
from app.domain.policy import check_values
from app.models.conversation import ConversationState, ConversationTurn
from app.models.response import ActionCompletionRecord
from app.schemas.conversation import ConversationRead
from app.services import response_service


def question(facts, answered):
    return next((r.model_dump(mode='json') for r in FIELDS
                 if r.field.value not in answered and getattr(facts, r.field.value) in (None, 'unknown')), None)


def read(db, incident):
    if incident.incident_type.value != 'financial_fraud' or incident.facts is None:
        raise HTTPException(409, 'Structured conversation currently supports financial incidents only.')
    state = db.get(ConversationState, incident.id)
    if state is None:
        facts = FACTS_ADAPTER.validate_python(incident.facts)
        state = ConversationState(incident_id=incident.id, revision=0, version='1.0', answered=[], pending_question=question(facts, []))
        db.add(state)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
        state = db.get(ConversationState, incident.id)
    plan = response_service.latest(db, incident.id)
    return ConversationRead(incident_id=incident.id, revision=state.revision, version=state.version,
        answered=state.answered, facts=plan.plan['facts'], pending_question=state.pending_question,
        turns=list(db.scalars(select(ConversationTurn).where(ConversationTurn.incident_id == incident.id).order_by(ConversationTurn.revision))),
        plan=plan, completions=response_service.completions(db, incident.id))


def submit(db, incident, payload):
    snapshot = read(db, incident)
    serialized = payload.model_dump(mode='json')
    existing = db.get(ConversationTurn, payload.turn_id)
    if existing:
        if existing.incident_id != incident.id or existing.structured_reply != serialized:
            raise HTTPException(409, 'This turn ID was already used for a different reply.')
        return snapshot
    if payload.expected_revision != snapshot.revision:
        raise HTTPException(409, 'Conversation changed. Reload and review the latest question before sending.')
    facts = snapshot.facts
    answered = list(snapshot.answered)
    changes = {}
    if payload.type == 'shortcut':
        if payload.value != 'money_gone' or payload.field is not None or payload.action_id is not None or snapshot.turns:
            raise ValueError('Choose a supported shortcut at the start of the conversation.')
        text = 'Money is gone.'
    elif payload.type != 'completion':
        field = payload.field
        if field is None:
            raise ValueError('An answer field is required.')
        if payload.action_id is not None:
            raise ValueError('Action ID is only supported for completion.')
        if payload.type == 'answer' and (snapshot.pending_question is None or field != snapshot.pending_question.field):
            raise HTTPException(409, 'Answer the pending question, or explicitly correct an earlier answer.')
        if payload.type == 'correction' and field not in answered and getattr(facts, field.value) in (None, 'unknown'):
            raise HTTPException(409, 'There is no established answer to correct.')
        value = payload.value
        boolean_fields = {'ongoing_loss', 'remote_access', 'account_compromised', 'credentials_exposed', 'evidence_available'}
        if field.value in boolean_fields and value is not None and type(value) is not bool:
            raise ValueError('Choose Yes, No or Not sure.')
        if field.value not in boolean_fields and value is not None and type(value) is not str:
            raise ValueError('A structured text value is required.')
        data = facts.model_dump(mode='json')
        before = data[field.value]
        if field.value == 'authorization':
            value = value or 'unknown'
            kinds = {'authorized': 'financial_scam_transfer', 'unauthorized': 'unauthorized_financial_transaction', 'unknown': 'financial_authorization_unknown'}
            if value not in kinds:
                raise ValueError('Choose a supported authorization answer.')
            data['kind'] = kinds[value]
        elif field.value == 'payment_method':
            value = value or 'unknown'
        data[field.value] = value
        data['provenance'] = [p for p in data['provenance'] if p['field'] != field.value] + [FactProvenance(field=field, origin='user_statement', verified=True).model_dump(mode='json')]
        check_values(data)
        facts = FACTS_ADAPTER.validate_python(data)
        changes = {'field': field.value, 'before': before, 'after': facts.model_dump(mode='json')[field.value]}
        if field not in answered:
            answered.append(field)
        text = ('Correction: ' if payload.type == 'correction' else '') + field.value.replace('_', ' ') + ': ' + ('Not sure' if payload.value is None else str(payload.value))
    else:
        if payload.field is not None:
            raise ValueError('Completion cannot change a fact.')
        if type(payload.value) is not bool:
            raise ValueError('Completion must be true or false.')
        if not any(a.id == payload.action_id and a.can_mark_complete for a in snapshot.plan.plan.actions):
            raise ValueError('Action is not applicable to this conversation.')
        text = ('Completed: ' if payload.value else 'Reopened: ') + payload.action_id
    pending = question(facts, answered)
    try:
        # Atomic compare-and-swap protects SQLite and PostgreSQL alike. All writes
        # including plan and completion are in the same transaction as this claim.
        result = db.execute(update(ConversationState).where(ConversationState.incident_id == incident.id,
            ConversationState.revision == payload.expected_revision).values(revision=payload.expected_revision + 1,
            answered=[f.value for f in answered], pending_question=pending))
        if result.rowcount != 1:
            db.rollback()
            raise HTTPException(409, 'Conversation changed. Reload before sending.')
        if payload.type in {'answer', 'correction'}:
            response_service.record_plan(db, incident, facts, as_of=datetime.now(timezone.utc))
        elif payload.type == 'completion':
            row = db.scalar(select(ActionCompletionRecord).where(ActionCompletionRecord.plan_id == snapshot.plan.id,
                ActionCompletionRecord.action_id == payload.action_id))
            if row is None:
                row = ActionCompletionRecord(incident_id=incident.id, plan_id=snapshot.plan.id, action_id=payload.action_id)
                db.add(row)
            row.completed = payload.value
            row.updated_at = datetime.now(timezone.utc)
        db.add(ConversationTurn(id=payload.turn_id, incident_id=incident.id, role='user', type=payload.type,
            text=text, structured_reply=serialized, fact_changes=changes, pending_question=pending,
            revision=payload.expected_revision + 1))
        db.commit()
    except (IntegrityError, OperationalError) as exc:
        db.rollback()
        duplicate = db.get(ConversationTurn, payload.turn_id)
        if duplicate and duplicate.incident_id == incident.id and duplicate.structured_reply == serialized:
            return read(db, incident)
        raise HTTPException(409, 'Concurrent update or save conflict. Reload and retry.') from exc
    except Exception:
        db.rollback()
        raise
    db.expire_all()
    return read(db, db.get(type(incident), incident.id))


def require_conversation_turn(db, incident_id):
    if db.get(ConversationState, incident_id) is not None:
        raise HTTPException(409, 'Use a versioned conversation correction to change these facts.')
