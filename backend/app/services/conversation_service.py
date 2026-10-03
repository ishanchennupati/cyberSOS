"""Progression and durable turns only. Safety actions belong to Phase 1."""
from datetime import datetime, timezone
from time import perf_counter
from app.core.diagnostics import log_ai_stage
from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError, OperationalError
from app.domain.facts import FACTS_ADAPTER, FactProvenance
from app.domain.playbooks import FIELDS
from app.domain.policy import check_values
from app.models.conversation import ConversationState, ConversationTurn
from app.models.response import ActionCompletionRecord
from app.schemas.conversation import ConversationRead, TurnRead, TurnRequest
from app.services import response_service
from app.services import understanding
from app.services import case_agent
from app.domain.playbooks import evaluate
from app.domain.response import FactRequirement, FactPriority


def question(facts, answered, conflicts=()):
    from app.domain.facts import FactField
    if conflicts:
        conflict = next((f for f in conflicts if f in {r.field.value for r in FIELDS} | {'money_lost'}), None)
        if conflict:
            return FactRequirement(field=conflict, priority=FactPriority.critical,
                question='Your statements differ. Which value should we use for ' + conflict.replace('_', ' ') + '?').model_dump(mode='json')
        return FactRequirement(field=None, priority=FactPriority.supporting,
            question='Your statements differ about ' + conflicts[0].replace('_', ' ') +
                '. Please clarify in your own words, starting with “Correction:”.').model_dump(mode='json')
    if facts.kind == 'incident_understanding':
        relevant = set()
        if 'device_compromise' in facts.signals:
            relevant.add('remote_access')
        if 'account_takeover' in facts.signals:
            relevant.add('account_compromised')
        priorities = [r for r in FIELDS if r.field.value in relevant]
        priorities.append(FactRequirement(field=FactField.money_lost, priority=FactPriority.critical,
            question='Has any money left your account or been sent because of this incident?'))
        priorities += [r for r in FIELDS if r.field.value == 'evidence_available']
    else:
        priorities = FIELDS
    return next((r.model_dump(mode='json') for r in priorities
                 if r.field.value not in answered and getattr(facts, r.field.value) in (None, 'unknown')
                 and not (r.field.value == 'occurred_at' and facts.time_window is not None)), None)


def read(db, incident):
    if incident.facts is None:
        raise HTTPException(409, 'This legacy case does not have canonical conversation facts yet.')
    state = db.get(ConversationState, incident.id)
    if state is None:
        facts = FACTS_ADAPTER.validate_python(incident.facts)
        state = ConversationState(incident_id=incident.id, revision=0, version='1.0', answered=[],
            pending_question=None if facts.kind == 'incident_understanding' else question(facts, []))
        db.add(state)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
        state = db.get(ConversationState, incident.id)
    plan = response_service.latest(db, incident.id)
    turns = list(db.scalars(select(ConversationTurn).where(ConversationTurn.incident_id == incident.id).order_by(ConversationTurn.revision)))
    from app.models.evidence import Evidence
    from app.services.case_memory import derive_memory
    evidence = list(db.scalars(select(Evidence).where(Evidence.incident_id == incident.id)))
    files = {str(item.id): item for item in evidence}
    history = []
    for turn in turns:
        item = TurnRead.model_validate(turn)
        item.attachments = [dict(metadata, deleted=metadata['id'] not in files,
            preview_url=f"/api/v1/evidence/{metadata['id']}/file" if metadata['id'] in files else None)
            for metadata in turn.fact_changes.get('attachments', [])]
        history.append(item)
    facts = FACTS_ADAPTER.validate_python(plan.plan['facts'])
    memory = derive_memory(facts, turns, turns[-1].fact_changes.get('conflicts', []) if turns else [])
    completions = response_service.completions(db, incident.id)
    projection = {'reference': str(incident.id), 'revision': state.revision, 'plan_revision': plan.revision,
        'status': 'In progress' if turns else 'Draft', 'working_understanding': facts.signals,
        'known_facts': memory['facts'], 'evidence_count': len(evidence),
        'completed_actions': sum(item.completed for item in completions),
        'completion_meaning': 'Recorded by you'}
    return ConversationRead(incident_id=incident.id, revision=state.revision, version=state.version,
        answered=state.answered, facts=plan.plan['facts'], pending_question=state.pending_question,
        turns=history, next_move=turns[-1].fact_changes.get('next_move') if turns else None,
        plan=plan, completions=completions, projection=projection, memory=memory)


def submit(db, incident, payload):
    snapshot = read(db, incident)
    serialized = payload.model_dump(mode='json')
    existing = db.get(ConversationTurn, payload.turn_id)
    if existing:
        if existing.incident_id != incident.id or TurnRequest.model_validate(existing.structured_reply).model_dump(mode='json') != serialized:
            raise HTTPException(409, 'This turn ID was already used for a different reply.')
        return snapshot
    if payload.expected_revision != snapshot.revision:
        raise HTTPException(409, 'Conversation changed. Reload and review the latest question before sending.')
    from app.models.evidence import Evidence
    from app.models.conversation import ConversationAttachment
    attachments = []
    for evidence_id in payload.attachment_ids:
        item = db.get(Evidence, evidence_id)
        if item is None or item.incident_id != incident.id:
            raise HTTPException(404, 'Private attachment not available')
        if db.get(ConversationAttachment, evidence_id):
            raise HTTPException(409, 'Attachment already belongs to a saved message')
        attachments.append(item)
    facts = snapshot.facts
    answered = list(snapshot.answered)
    changes = {}
    timestamp = datetime.now(timezone.utc)
    conflicts = snapshot.turns[-1].fact_changes.get('conflicts', []) if snapshot.turns else []
    if payload.type == 'message':
        text = payload.text or ''
        stage_started = perf_counter()
        facts, updates, result = understanding.interpret(text, facts, payload.turn_id, timestamp, payload.timezone,
            (snapshot.next_move.model_dump(mode='json') if snapshot.next_move else
                snapshot.pending_question.model_dump(mode='json') if snapshot.pending_question else None),
            recent_turns=snapshot.turns) if text.strip() else (facts, [], {'status':'understood', 'candidates':[], 'conflicts':[], 'attachment_only':True})
        log_ai_stage('extraction', result, (perf_counter() - stage_started) * 1000)
        resolved = {u['field'] for u in updates}
        conflicts = list(dict.fromkeys([f for f in conflicts if f not in resolved] + result['conflicts']))
        changes = {'updates': updates, 'understanding': result}
        if set(result.get('intents', [])) & {'skip','not_sure'}:
            target = None
            for previous in reversed(snapshot.turns):
                previous_move = previous.fact_changes.get('next_move') or {}
                if '?' in previous_move.get('message', ''):
                    target = previous_move.get('related_field')
                    break
            if snapshot.pending_question and snapshot.pending_question.field:
                target = snapshot.pending_question.field.value
            if target:
                changes['answered_unknown'] = target
        # A new story may establish a fact previously answered as Not sure.
        answered = [f for f in answered if f not in resolved or getattr(facts, f) not in (None, 'unknown')]
        if snapshot.next_move and snapshot.next_move.type in {'ASK_CLARIFICATION','VERIFY_INFORMATION'} and text.strip().casefold() in {
            'not sure', "i don't know", 'i do not know', 'తెలియదు', 'నాకు తెలియదు', 'पता नहीं', 'pata nahi', 'teliyadu'}:
            changes['answered_unknown'] = snapshot.next_move.related_field
            from app.domain.facts import FactField
            if snapshot.next_move.related_field in {f.value for f in FactField}:
                field = FactField(snapshot.next_move.related_field)
                if field not in answered:
                    answered.append(field)
    elif payload.type == 'shortcut':
        if payload.value != 'money_gone' or payload.field is not None or payload.action_id is not None or snapshot.turns:
            raise ValueError('Choose a supported shortcut at the start of the conversation.')
        text = 'Money is gone.'
        if facts.kind == 'incident_understanding':
            data = facts.model_dump(mode='json')
            data.update(kind='financial_authorization_unknown', money_lost=True)
            facts = FACTS_ADAPTER.validate_python(data)
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
        boolean_fields = {'money_lost', 'ongoing_loss', 'remote_access', 'account_compromised', 'credentials_exposed', 'evidence_available'}
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
        if field.value == 'money_lost' and value is not None:
            data['kind'] = understanding.KINDS[data['authorization']] if value else 'incident_understanding'
            if not value:
                data['authorization'] = 'unknown'
        data['provenance'] = [p for p in data['provenance'] if p['field'] != field.value] + [FactProvenance(field=field, origin='user_statement', verified=True).model_dump(mode='json')]
        check_values(data)
        facts = FACTS_ADAPTER.validate_python(data)
        changes = {'field': field.value, 'before': before, 'after': facts.model_dump(mode='json')[field.value]}
        if field not in answered:
            answered.append(field)
        conflicts = [f for f in conflicts if f != field.value]
        text = ('Correction: ' if payload.type == 'correction' else '') + field.value.replace('_', ' ') + ': ' + ('Not sure' if payload.value is None else str(payload.value))
    else:
        if payload.field is not None:
            raise ValueError('Completion cannot change a fact.')
        if type(payload.value) is not bool:
            raise ValueError('Completion must be true or false.')
        if not any(a.id == payload.action_id and a.can_mark_complete for a in snapshot.plan.plan.actions):
            raise ValueError('Action is not applicable to this conversation.')
        text = ('Completed: ' if payload.value else 'Reopened: ') + payload.action_id
    # Facts and deterministic actions exist BEFORE AI chooses any conversational move.
    # No provider calls on read/replay, and no model-generated action enters the plan.
    if payload.type == 'completion':
        pending = snapshot.pending_question.model_dump(mode='json') if snapshot.pending_question else None
        changes['next_move'] = snapshot.next_move.model_dump(mode='json') if snapshot.next_move else None
        changes['acknowledgement'] = 'Your action update is saved.'
    else:
        plan = evaluate(facts, as_of=timestamp)
        from app.models.evidence import Evidence
        evidence = [{'type': row.evidence_type.value, 'verification': row.verification_status.value}
            for row in db.scalars(select(Evidence).where(Evidence.incident_id == incident.id).limit(20))]
        result = changes.get('understanding', {})
        declined = case_agent.declined_fields(snapshot.turns) - {u['field'] for u in changes.get('updates', [])}
        if changes.get('answered_unknown'):
            declined.add(changes['answered_unknown'])
        if declined & {'occurred_at','time_window'}: declined.update({'occurred_at','time_window'})
        decision_answered = list(dict.fromkeys([f.value for f in answered] + sorted(declined)))
        unresolved = case_agent.unresolved_candidates(snapshot.turns, result, changes.get('updates', []), decision_answered)
        if changes.get('field'):
            unresolved = [c for c in unresolved if c['field'] != changes['field']]
        changes['unresolved_candidates'] = unresolved
        if result.get('status') == 'fallback':
            move, agent = None, {'status': 'fallback', 'reason': 'understanding_unavailable',
                'category': result.get('category', 'PROVIDER_UNAVAILABLE'), 'skipped': True}
            stage_duration_ms = 0
        else:
            decision_understanding = dict(result, candidates=[c for c in result.get('candidates', []) if c['status'] == 'accepted'] + unresolved)
            context = case_agent.build_context(facts, decision_understanding, conflicts, snapshot.turns, text, plan,
                evidence, decision_answered,
                snapshot.next_move.model_dump(mode='json') if snapshot.next_move else None)
            context['user_intents'] = result.get('intents', [])
            if 'pause' in context['user_intents']: context['memory']['questions_paused'] = True
            if 'resume' in context['user_intents']: context['memory']['questions_paused'] = False
            stage_started = perf_counter()
            move, agent = case_agent.decide(context)
            if move:
                cited = {reference.id for reference in move.knowledge_refs}
                changes['knowledge_sources'] = [item for item in context.get('knowledge', []) if item['id'] in cited]
            stage_duration_ms = (perf_counter() - stage_started) * 1000
        log_ai_stage('follow_up', agent, stage_duration_ms)
        from app.domain.facts import FactField
        fallback_answered = [FactField(field) for field in decision_answered if field in {item.value for item in FactField}]
        from app.services.case_memory import derive_memory
        paused = derive_memory(facts, snapshot.turns, conflicts)['questions_paused']
        if 'pause' in result.get('intents', []): paused = True
        if 'resume' in result.get('intents', []): paused = False
        pending = None if move or paused else question(facts, fallback_answered, conflicts)
        changes['next_move'] = move.model_dump(mode='json') if move else None
        changes['agent'] = agent
        acknowledgement = '' if move and (move.fact_refs or move.type in {'ACKNOWLEDGE_AND_WAIT','ANSWER_RELEVANT_QUESTION','EXPLAIN_APPROVED_ACTION'}) else case_agent.acknowledge(facts, changes.get('updates', []))
        if move and move.type == 'ACKNOWLEDGE_AND_WAIT' and move.message == acknowledgement:
            acknowledgement = ''  # The same grounded acknowledgement is rendered once.
        if result.get('status') == 'fallback':
            acknowledgement = "Your message is saved. AI understanding is temporarily unavailable. I'll guide you with a focused question instead."
        elif move is None and not paused:
            acknowledgement += " Automatic follow-up is temporarily unavailable. We can continue with a focused question."
        elif move is None:
            acknowledgement = 'Your message is saved. Questions remain paused. You can ask to continue whenever you are ready.'
        changes['acknowledgement'] = acknowledgement
    changes['conflicts'] = conflicts
    from app.services.case_memory import derive_memory
    changes['memory'] = dict(derive_memory(facts, snapshot.turns, conflicts), revision=payload.expected_revision + 1)
    changes['attachments'] = [{'id':str(item.id), 'original_filename':item.original_filename,
        'mime_type':item.mime_type, 'file_size':item.file_size} for item in attachments]
    try:
        # Atomic compare-and-swap protects SQLite and PostgreSQL alike. All writes
        # including plan and completion are in the same transaction as this claim.
        result = db.execute(update(ConversationState).where(ConversationState.incident_id == incident.id,
            ConversationState.revision == payload.expected_revision).values(revision=payload.expected_revision + 1,
            answered=[f.value for f in answered], pending_question=pending))
        if result.rowcount != 1:
            db.rollback()
            raise HTTPException(409, 'Conversation changed. Reload before sending.')
        if payload.type in {'answer', 'correction', 'message', 'shortcut'}:
            response_service.record_plan(db, incident, facts, as_of=timestamp)
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
            revision=payload.expected_revision + 1, created_at=timestamp))
        db.flush()
        for item in attachments:
            db.add(ConversationAttachment(evidence_id=item.id, turn_id=payload.turn_id))
            item.staged_for_chat = False
        db.commit()
    except (IntegrityError, OperationalError) as exc:
        db.rollback()
        duplicate = db.get(ConversationTurn, payload.turn_id)
        if duplicate and duplicate.incident_id == incident.id and TurnRequest.model_validate(duplicate.structured_reply).model_dump(mode='json') == serialized:
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
