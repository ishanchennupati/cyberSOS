"""Citizen control and fallback regressions through owned durable API turns."""
import json
import uuid
import pytest
from tests.test_phase3r_case_agent import install, move, send
from tests.test_phase3_understanding import candidate
from app.services import case_agent, understanding
from app.services.ai_provider import FakeProvider


def harassment(client, monkeypatch):
    install(monkeypatch, [candidate('signals', ['harassment'], 'harassed'),
        candidate('platform', 'Instagram', 'Instagram')], move('ACKNOWLEDGE_AND_WAIT', None, 'I am here.'))
    return send(client, 'Someone harassed me on Instagram.')[0]


def test_exact_harassment_fallback_help_conclusion(client, monkeypatch):
    state = harassment(client, monkeypatch)
    for text in ['Why are you asking about money?', 'Enough questions. Tell me what to do now.', 'Summarize and conclude.']:
        provider = install(monkeypatch, [], move())
        provider.output = json.dumps({'language':'en','candidates':[], 'intents':['question'], 'intent_source':text})
        monkeypatch.setattr(case_agent, 'get_provider', lambda: FakeProvider(error=TimeoutError()))
        state, path, payload = send(client, text, state)
        assert state['pending_question'] is None
        assert state['next_move'] is None or state['next_move']['related_field'] != 'money_lost'
    assert state['memory']['questions_paused'] is True
    assert state['turns'][-1]['fact_changes']['help_view']['action_ids']
    assert state['understanding_review']['reviewed'] is False
    assert client.get(path).json()['memory']['questions_paused'] is True
    assert client.post(path+'/turns', json=payload).json() == state


def test_current_help_does_not_require_redundant_followup_model(client, monkeypatch):
    state=harassment(client,monkeypatch)
    provider=install(monkeypatch,[],move())
    state, _, _ = send(client, 'Stop asking questions. Give me the plan.', state)
    assert provider.decision_contexts==[]
    assert state['turns'][-1]['fact_changes']['agent']['status']=='not_requested'
    assert state['turns'][-1]['fact_changes']['help_view']['action_ids']


@pytest.mark.parametrize('stage', ['understanding', 'follow_up'])
@pytest.mark.parametrize('failure', ['timeout', 'malformed', 'quota', 'rejected'])
def test_stop_and_plan_survive_provider_failure(client, monkeypatch, stage, failure):
    state = harassment(client, monkeypatch)
    class Quota(Exception):
        code = 429
    broken = FakeProvider(error=TimeoutError()) if failure == 'timeout' else (
        FakeProvider(error=Quota()) if failure == 'quota' else FakeProvider(
            output='{}', next_move=json.dumps(move(message='Call 99999 now?')) if failure == 'rejected' else '{}'))
    install(monkeypatch, [], move())
    monkeypatch.setattr(understanding if stage == 'understanding' else case_agent, 'get_provider', lambda: broken)
    state, path, _ = send(client, 'Stop asking questions. Give me the plan.', state)
    assert state['pending_question'] is None
    assert state['memory']['questions_paused'] is True
    assert state['turns'][-1]['fact_changes']['help_view']['action_ids']
    assert state['facts']['money_lost'] is None
    assert client.get(path).json()['memory']['questions_paused'] is True


def test_nonfinancial_fallback_never_starts_money_intake(client, monkeypatch):
    state = harassment(client, monkeypatch)
    install(monkeypatch, [], move())
    monkeypatch.setattr(case_agent, 'get_provider', lambda: FakeProvider(error=TimeoutError()))
    state, _, _ = send(client, 'I am worried.', state)
    assert state['pending_question'] is None or state['pending_question']['field'] != 'money_lost'


def test_harassment_does_not_accept_unrelated_device_question(client, monkeypatch):
    state = harassment(client, monkeypatch)
    install(monkeypatch, [], move(field='remote_access', message='Can someone still control your device?'))
    state, _, _ = send(client, 'I am worried.', state)
    assert state['next_move'] is None or state['next_move']['related_field'] != 'remote_access'


def test_open_story_nonanswers_do_not_loop(client, monkeypatch):
    install(monkeypatch, [], move('CONTINUE_OPEN_CONVERSATION','story','What happened online?'))
    state, _, _ = send(client, 'Something happened.')
    for text in ['I am worried.', 'I am still worried.']:
        install(monkeypatch, [], move('CONTINUE_OPEN_CONVERSATION','story','What happened online?'))
        state, _, _ = send(client, text, state)
    assert state['next_move'] is None
    assert state['pending_question'] is None


def test_repeated_nonanswer_does_not_reask_same_question(client, monkeypatch):
    install(monkeypatch, [candidate('signals', ['account_takeover'], 'account')],
        move(field='account_compromised', message='Can someone else still access your account?'))
    state, _, _ = send(client, 'My account has a problem.')
    for text in ['I am worried.', 'I am still worried.']:
        install(monkeypatch, [], move(field='account_compromised', message='Can someone else still access your account?'))
        state, _, _ = send(client, text, state)
    assert state['next_move'] is None or state['next_move']['related_field'] != 'account_compromised'
    assert state['pending_question'] is None or state['pending_question']['field'] != 'account_compromised'
    assert state['facts']['account_compromised'] is None
    assert state['memory']['question_dispositions']['account_compromised']['status'] == 'nonanswer'


def test_witness_does_not_mix_another_incident_into_case(client, monkeypatch):
    state = harassment(client, monkeypatch)
    provider = install(monkeypatch, [candidate('immediate_danger', True, 'harassed')], move())
    text = 'Someone just got harassed in front of me; what should I do?'
    provider.output = json.dumps({'language':'en','candidates':[candidate('immediate_danger', True, 'harassed')],
        'intents':['witness','question'], 'intent_source':text})
    state, _, _ = send(client, text, state)
    assert state['facts']['immediate_danger'] is None
    assert state['facts']['platform'] == 'Instagram'
    assert state['pending_question'] is None
    assert 'separate' in state['turns'][-1]['fact_changes']['acknowledgement'].lower()
    assert 'physical' in state['turns'][-1]['fact_changes']['acknowledgement'].lower()


def test_unresolved_incident_scope_stays_isolated_on_next_turn(client, monkeypatch):
    state = harassment(client, monkeypatch)
    provider = install(monkeypatch, [], move())
    text = 'Someone just got harassed in front of me; what should I do?'
    provider.output = json.dumps({'language':'en','candidates':[], 'intents':['witness'], 'intent_source':text})
    state, _, _ = send(client, text, state)
    install(monkeypatch, [candidate('immediate_danger', True, 'danger')], move())
    state, _, _ = send(client, 'They are in physical danger.', state)
    assert state['facts']['immediate_danger'] is None
    assert state['memory']['incident_scope_pending'] is True
    assert '?' not in state['turns'][-1]['fact_changes']['acknowledgement']


def test_declined_evidence_request_does_not_repeat(client, monkeypatch):
    state = harassment(client, monkeypatch)
    provider = install(monkeypatch, [], move('REQUEST_EVIDENCE','evidence_available',
        'A safe screenshot could help clarify this, if you want to attach one.', evidence_kind='non_explicit_conversation'))
    state, _, _ = send(client, 'I am worried.', state)
    provider.output=json.dumps({'language':'en','candidates':[], 'intents':['skip'], 'intent_source':'skip'})
    state, _, _ = send(client, 'Please skip.', state)
    assert state['next_move'] is None or state['next_move']['type'] != 'REQUEST_EVIDENCE'
    assert state['facts']['evidence_available'] is None


def test_help_correction_keeps_investigation_paused(client, monkeypatch):
    state = harassment(client, monkeypatch)
    install(monkeypatch, [], move())
    state, _, _ = send(client, 'Give me the plan.', state)
    revised = candidate('platform','Facebook','Facebook')
    revised['correction_source'] = 'Correction'
    install(monkeypatch, [revised], move(field='evidence_available', message='Do you have a screenshot?'))
    state, _, _ = send(client, 'Correction: this was on Facebook.', state)
    assert state['facts']['platform'] == 'Facebook'
    assert state['memory']['questions_paused'] is True
    assert state['pending_question'] is None
    assert state['next_move'] is None
    assert state['projection']['current_help']['known_facts']['platform']['value'] == 'Facebook'


@pytest.mark.parametrize('proposal', [
    move('REQUEST_EVIDENCE','evidence_available','Could you share a non-explicit screenshot?',evidence_kind='non_explicit_conversation'),
    move('ANSWER_RELEVANT_QUESTION',None,'CyberSOS organizes the details and prepares the information you need to report the incident.'),
])
def test_safe_synthetic_proposals_not_rejected_as_instructions(client, monkeypatch, proposal):
    state = harassment(client, monkeypatch)
    install(monkeypatch, [], proposal)
    state, _, _ = send(client, 'What can CyberSOS help with?', state)
    assert state['turns'][-1]['fact_changes']['agent']['status'] == 'decided'


def test_reporting_purpose_is_not_a_new_instruction(client, monkeypatch):
    state = harassment(client, monkeypatch)
    install(monkeypatch, [], move('ANSWER_RELEVANT_QUESTION',None,
        'CyberSOS helps you organize your notes and records of what happened on Instagram so you can review them and report abuse safely.'))
    state, _, _ = send(client, 'What can CyberSOS help with?', state)
    assert state['turns'][-1]['fact_changes']['agent']['status'] == 'decided'


def test_relevant_answer_may_offer_open_conversation(client, monkeypatch):
    state=harassment(client,monkeypatch)
    install(monkeypatch,[],move('ANSWER_RELEVANT_QUESTION','story',
        'CyberSOS helps organize what happened. Would you like to continue or share more details?',
        quick_replies=["Let's continue",'I want to share more details']))
    state, _, _ = send(client, 'What can CyberSOS help with?', state)
    assert state['turns'][-1]['fact_changes']['agent']['status']=='decided'


@pytest.mark.parametrize('kind', ['ANSWER_RELEVANT_QUESTION','CONTINUE_OPEN_CONVERSATION'])
def test_story_tag_cannot_hide_irrelevant_money_question(client, monkeypatch, kind):
    state=harassment(client,monkeypatch)
    install(monkeypatch,[],move(kind,'story','Did any money leave your account?'))
    state, _, _ = send(client, 'Why are you asking about money?', state)
    assert state['next_move'] is None
    assert state['pending_question'] is None
    assert state['facts']['money_lost'] is None


def test_reporting_preparation_purpose_survives_validation(client, monkeypatch):
    state=harassment(client,monkeypatch)
    install(monkeypatch,[],move('ANSWER_RELEVANT_QUESTION',None,
        'CyberSOS helps organize your details and prepare information so you can report the incident safely.'))
    state, _, _ = send(client, 'What can CyberSOS help with?', state)
    assert state['turns'][-1]['fact_changes']['agent']['status']=='decided'


def test_consent_to_continue_does_not_target_a_device_fact(client, monkeypatch):
    state=harassment(client,monkeypatch)
    install(monkeypatch,[],move('ANSWER_RELEVANT_QUESTION','remote_access',
        'CyberSOS helps organize your case. Would you like to continue checking whether your device or account is secure?'))
    state, _, _ = send(client, 'What can CyberSOS help with?', state)
    assert state['next_move']['related_field']=='story'
    install(monkeypatch,[candidate('remote_access',False,'No')],move('ACKNOWLEDGE_AND_WAIT',None,'We can leave that unknown.'))
    state, _, _ = send(client, 'No', state)
    assert state['facts']['remote_access'] is None


def test_honest_application_limitation_is_not_recovery_promise(client, monkeypatch):
    state=harassment(client,monkeypatch)
    install(monkeypatch,[],move('ANSWER_RELEVANT_QUESTION',None,
        'CyberSOS helps organize your case, but it does not submit reports or recover accounts directly for you.'))
    state, _, _ = send(client, 'What can CyberSOS help with?', state)
    assert state['turns'][-1]['fact_changes']['agent']['status']=='decided'


def test_first_person_application_limitation_is_grounded(client, monkeypatch):
    state=harassment(client,monkeypatch)
    install(monkeypatch,[],move('ANSWER_RELEVANT_QUESTION',None,
        'CyberSOS helps organize your information, though we cannot submit reports or recover funds directly.'))
    state, _, _ = send(client, 'What can CyberSOS help with?', state)
    assert state['turns'][-1]['fact_changes']['agent']['status']=='decided'


def test_reviewed_understanding_does_not_restart_questions_after_correction(client, monkeypatch):
    state=harassment(client,monkeypatch)
    path=f"/api/v1/incidents/{state['incident_id']}/conversation"
    response=client.post(path+'/turns',json={'turn_id':str(uuid.uuid4()),'expected_revision':state['revision'],'type':'case_review'})
    assert response.status_code==200
    state=response.json()
    assert state['memory']['questions_paused'] is True
    corrected=candidate('platform','Facebook','Facebook');corrected['correction_source']='Correction'
    install(monkeypatch,[corrected],move())
    monkeypatch.setattr(case_agent,'get_provider',lambda:FakeProvider(error=TimeoutError()))
    state, _, _ = send(client, 'Correction: this was on Facebook.', state)
    assert state['facts']['platform']=='Facebook'
    assert state['pending_question'] is None


def test_provider_grammar_cannot_choose_declined_open_story():
    from datetime import datetime, timezone
    from app.domain.facts import FACTS_ADAPTER
    from app.domain.playbooks import evaluate
    from app.schemas.next_move import NextMove
    from app.services.ai_provider import provider_schema
    facts=FACTS_ADAPTER.validate_python({'kind':'incident_understanding','signals':['harassment'],'platform':'Instagram'})
    context=case_agent.build_context(facts,{},[],[],'Skip that question.',evaluate(facts,as_of=datetime.now(timezone.utc)),[],['story'])
    schema=provider_schema(NextMove,context)
    kinds={kind for variant in schema['properties']['interaction']['anyOf'] for kind in variant['properties']['type']['enum']}
    assert 'CONTINUE_OPEN_CONVERSATION' not in kinds
    assert 'ASK_CLARIFICATION' in kinds and 'ACKNOWLEDGE_AND_WAIT' in kinds


def test_approved_financial_phone_reference_uses_current_case_scope(client, monkeypatch):
    install(monkeypatch,[candidate('signals',['financial'],'scammer'),candidate('money_lost',True,'sent'),
        candidate('payment_method','upi','UPI')],move('ACKNOWLEDGE_AND_WAIT',None,'I have recorded those details.'))
    state, _, _ = send(client, 'I sent money via UPI to a scammer.')
    install(monkeypatch,[],move('ANSWER_RELEVANT_QUESTION',None,
        'CyberSOS helps organize what happened and prepares information for 1930.'))
    state, _, _ = send(client, 'What can CyberSOS help with?', state)
    assert state['turns'][-1]['fact_changes']['agent']['status']=='decided'


def test_changed_context_allows_consequential_reask(client, monkeypatch):
    install(monkeypatch,[candidate('signals',['account_takeover'],'account'),candidate('platform','Google','Google')],
        move(field='account_compromised',message='Can someone else still access your account?'))
    state, _, _ = send(client, 'There is a problem with my Google account.')
    provider=install(monkeypatch,[],move('ACKNOWLEDGE_AND_WAIT',None,'We can leave that unknown.'))
    provider.output=json.dumps({'language':'en','candidates':[], 'intents':['skip'], 'intent_source':'skip'})
    state, _, _ = send(client, 'Please skip.', state)
    corrected=candidate('platform','Microsoft','Microsoft');corrected['correction_source']='Correction'
    install(monkeypatch,[corrected],move(field='account_compromised',message='Can someone else still access your account?'))
    state, _, _ = send(client, 'Correction: I meant my Microsoft account.', state)
    assert state['next_move']['related_field']=='account_compromised'


def test_initial_witness_pause_never_asks(client, monkeypatch):
    state=harassment(client,monkeypatch)
    text='Someone was harassed in front of me. Pause questions.'
    provider=install(monkeypatch,[],move())
    provider.output=json.dumps({'language':'en','candidates':[], 'intents':['witness','pause'], 'intent_source':text})
    state, _, _ = send(client, text, state)
    assert '?' not in state['turns'][-1]['fact_changes']['acknowledgement']
    assert state['memory']['incident_scope_pending'] is True


@pytest.mark.parametrize('text', ['Please share explicit images.', 'Could you share a non-explicit screenshot and your password?',
    'CyberSOS prepares the information you need to report the incident. Call 99999.',
    'CyberSOS guarantees a refund, but it does not submit reports or recover accounts directly for you.',
    'You need to report this to an invented authority.'])
def test_safe_wording_exception_still_rejects_unsafe_prose(client, monkeypatch, text):
    state = harassment(client, monkeypatch)
    install(monkeypatch, [], move('ANSWER_RELEVANT_QUESTION',None,text))
    state, _, _ = send(client, 'What can CyberSOS help with?', state)
    assert state['turns'][-1]['fact_changes']['agent']['status'] == 'fallback'


@pytest.mark.parametrize('text', ['What does "stop asking questions" mean?', 'Should I stop asking questions?', 'The attacker said "give me the plan".'])
def test_quoted_or_hypothetical_control_does_not_pause(client, monkeypatch, text):
    state = harassment(client, monkeypatch)
    install(monkeypatch, [], move('ACKNOWLEDGE_AND_WAIT', None, 'I am here.'))
    state, _, _ = send(client, text, state)
    assert state['memory']['questions_paused'] is False


def test_generation_schema_obeys_every_move_shape():
    from datetime import datetime, timezone
    from app.domain.facts import FACTS_ADAPTER
    from app.domain.playbooks import evaluate
    from app.schemas.next_move import NextMove
    from app.services.ai_provider import provider_schema
    facts=FACTS_ADAPTER.validate_python({'kind':'incident_understanding','signals':['account_takeover'],'platform':'Google','account_compromised':True})
    context=case_agent.build_context(facts,{},[],[],'Why are you asking that?',evaluate(facts,as_of=datetime.now(timezone.utc)),[],[])
    schema=provider_schema(NextMove,context)
    for variant in schema['properties']['interaction']['anyOf']:
        props=variant['properties']
        assert len(props['type']['enum'])==1
        kind=props['type']['enum'][0]
        if kind=='CONTINUE_OPEN_CONVERSATION':
            assert props['related_field']=={'type':'string','enum':['story']}
        if kind=='EXPLAIN_APPROVED_ACTION':
            assert props['action_id']['enum']==[a['id'] for a in context['approved_actions']]
            assert props['related_field']=={'type':'null'}
            assert props['quick_replies']['maxItems']==0
        else:
            assert props['action_id']=={'type':'null'}
        if kind!='REQUEST_EVIDENCE':
            assert props['evidence_kind']=={'type':'null'}


def test_account_access_cannot_be_reasked_as_device_fact(client, monkeypatch):
    install(monkeypatch,[candidate('signals',['account_takeover'],'account'),candidate('platform','Google','Google'),
        candidate('account_compromised',True,'Someone else still has access')],move('ACKNOWLEDGE_AND_WAIT',None,'I have recorded this.'))
    state, _, _=send(client,'Someone else still has access to my Google account.')
    provider=install(monkeypatch,[],move(field='remote_access',message='Can someone else still access your device or account right now?'))
    state, _, _=send(client,'I am worried.',state)
    assert 'remote_access' not in json.loads(provider.decision_contexts[-1])['unknown_fields']
    assert 'immediate_danger' not in json.loads(provider.decision_contexts[-1])['unknown_fields']
    assert state['turns'][-1]['fact_changes']['agent']['status']=='fallback'
    assert state['next_move'] is None or state['next_move']['related_field']!='remote_access'


def test_capability_reporting_purpose_with_generic_destination(client, monkeypatch):
    state=harassment(client,monkeypatch)
    install(monkeypatch,[],move('ANSWER_RELEVANT_QUESTION',None,
        'CyberSOS helps you organize what happened, guides you on preserving safe records, and prepares details so you can report the incident to official channels.'))
    state, _, _=send(client,'What can CyberSOS help with?',state)
    assert state['turns'][-1]['fact_changes']['agent']['status']=='decided'


@pytest.mark.parametrize('text', [
    'CyberSOS helps you organize what happened and prepares details so you can report it properly.',
    'CyberSOS helps prepare your case so you can report this safely.',
    'CyberSOS guides you on how to secure your account and report it officially.',
])
def test_application_capability_purpose_is_not_a_citizen_instruction(client, monkeypatch, text):
    install(monkeypatch,[candidate('signals',['account_takeover'],'account'),
        candidate('platform','Google','Google'),candidate('account_compromised',True,'Someone else has access')],
        move('ACKNOWLEDGE_AND_WAIT',None,'I have recorded this.'))
    state,_,_=send(client,'Someone else has access to my Google account.')
    install(monkeypatch,[],move('ANSWER_RELEVANT_QUESTION',None,text))
    state,_,_=send(client,'What can CyberSOS help with?',state)
    assert state['turns'][-1]['fact_changes']['agent']['status']=='decided'
    assert state['next_move']['message']==text


@pytest.mark.parametrize('text', [
    'CyberSOS helps prepare details so you can report it properly. You should reset your password now.',
    'CyberSOS guides you on how to secure your account and contact your bank.',
    'CyberSOS helps prepare details so you can report it by visiting an unverified website.',
    'CyberSOS helps you organize your case and submit it automatically.',
])
def test_capability_clause_cannot_hide_extra_instructions(client, monkeypatch, text):
    state=harassment(client,monkeypatch)
    install(monkeypatch,[],move('ANSWER_RELEVANT_QUESTION',None,text))
    state,_,_=send(client,'What can CyberSOS help with?',state)
    assert state['turns'][-1]['fact_changes']['agent']['status']=='fallback'


def test_citizen_approval_is_not_external_approval_but_procedure_is_rejected(client, monkeypatch):
    install(monkeypatch,[candidate('signals',['financial'],'scam'),candidate('money_lost',True,'send'),
        candidate('authorization','authorized','made me send'),candidate('payment_method','upi','UPI')],
        move('EXPLAIN_APPROVED_ACTION',None,
            'You can contact your bank immediately to report that you approved a payment after deception.',
            action_id='contact_bank_scam'))
    state,_,_=send(client,'A scam made me send money via UPI.')
    assert state['turns'][-1]['fact_changes']['agent']['rejection_reason']=='ACTION_IN_INVESTIGATION'


def test_adequate_story_cannot_receive_generic_repeat_request(client, monkeypatch):
    state=harassment(client,monkeypatch)
    provider=install(monkeypatch,[],move('CONTINUE_OPEN_CONVERSATION','story',
        'Could you share a bit more about what happened?'))
    state,_,_=send(client,'I am worried.',state)
    assert state['next_move'] is None or state['next_move']['message']!='Could you share a bit more about what happened?'
    context=json.loads(provider.decision_contexts[-1])
    assert context['case_state']['story_established'] is True
    from app.schemas.next_move import NextMove
    from app.services.ai_provider import provider_schema
    assert all(v['properties']['type']['enum']!=['CONTINUE_OPEN_CONVERSATION'] for v in provider_schema(NextMove,context)['properties']['interaction']['anyOf'])


@pytest.mark.parametrize('text', [
    'Financial details are unnecessary for the known story, as no payment or financial loss was involved.',
    'There was no financial loss.',
    'You have not lost any money.',
])
def test_no_payment_or_loss_cannot_be_asserted_from_nonfinancial_story(client, monkeypatch, text):
    state=harassment(client,monkeypatch)
    install(monkeypatch,[],move('ANSWER_RELEVANT_QUESTION',None,
        text))
    state,_,_=send(client,'Why are you asking about money?',state)
    assert state['facts']['money_lost'] is None
    assert state['turns'][-1]['fact_changes']['agent']['rejection_reason']=='UNSUPPORTED_LOSS_CLAIM'


def test_device_answer_does_not_make_an_unknown_account_question_repetitive(client, monkeypatch):
    install(monkeypatch,[candidate('signals',['financial'],'scam'),candidate('money_lost',True,'sent'),
        candidate('remote_access',False,'No one can control my device')],
        move('ACKNOWLEDGE_AND_WAIT',None,'I have recorded this.'))
    state,_,_=send(client,'I sent money in a scam. No one can control my device.')
    install(monkeypatch,[],move('ASK_CLARIFICATION','account_compromised',
        'Can someone else still access your accounts now?'))
    state,_,_=send(client,'I am worried.',state)
    assert state['turns'][-1]['fact_changes']['agent']['status']=='decided'
    assert state['next_move']['related_field']=='account_compromised'


def test_answer_cannot_reask_deferred_evidence_as_a_story_question(client, monkeypatch):
    state=harassment(client,monkeypatch)
    install(monkeypatch,[],move('REQUEST_EVIDENCE','evidence_available',
        'Do you have screenshots of the messages?',evidence_kind='non_explicit_conversation'))
    state,_,_=send(client,'I am worried.',state)
    provider=install(monkeypatch,[],move('ANSWER_RELEVANT_QUESTION','story',
        'The current story concerns harassment, so financial questions are unnecessary. Do you happen to have any screenshots or text of the messages they sent?'))
    state,_,_=send(client,'Why are you asking about money?',state)
    assert state['next_move'] is None or '?' not in state['next_move']['message']
    context=json.loads(provider.decision_contexts[-1])
    assert 'evidence_available' in context['answered_fields']


def test_application_denial_of_guarantees_is_not_an_outcome_prediction(client, monkeypatch):
    state=harassment(client,monkeypatch)
    text='CyberSOS helps organize your facts and prepare a reviewed report draft. We do not guarantee outcomes or make procedural promises.'
    install(monkeypatch,[],move('ANSWER_RELEVANT_QUESTION',None,text))
    state,_,_=send(client,'What can CyberSOS help with?',state)
    assert state['turns'][-1]['fact_changes']['agent']['status']=='decided'
    assert state['next_move']['message']==text


def test_denial_clause_does_not_hide_a_positive_recovery_prediction(client, monkeypatch):
    state=harassment(client,monkeypatch)
    install(monkeypatch,[],move('ANSWER_RELEVANT_QUESTION',None,
        'We do not guarantee outcomes, but you will recover your money.'))
    state,_,_=send(client,'What can CyberSOS help with?',state)
    assert state['turns'][-1]['fact_changes']['agent']['status']=='fallback'


def test_deferred_time_cannot_reappear_as_timestamp_field(client, monkeypatch):
    install(monkeypatch,[candidate('signals',['account_takeover'],'account'),candidate('platform','Google','Google'),
        candidate('account_compromised',True,'Someone else has access')],move('ASK_CLARIFICATION','occurred_at','When did this happen?'))
    state,_,_=send(client,'Someone else has access to my Google account.')
    body='A time question helps organize the timeline and understand which support is relevant.'
    provider=install(monkeypatch,[],move('ANSWER_RELEVANT_QUESTION','timestamp_text',body+' When did this happen?'))
    state,_,_=send(client,'Why are you asking that?',state)
    assert state['turns'][-1]['fact_changes']['agent']['status']=='decided'
    assert state['next_move']['message']==body
    context=json.loads(provider.decision_contexts[-1])
    assert not {'occurred_at','time_window','timestamp_text'}&set(context['unknown_fields'])
    assert {'occurred_at','time_window','timestamp_text'}<=set(context['answered_fields'])


def test_unsafe_optional_buttons_do_not_discard_safe_answer(client, monkeypatch):
    state=harassment(client,monkeypatch)
    install(monkeypatch,[],move('ANSWER_RELEVANT_QUESTION','story',
        'CyberSOS helps organize your details and safe records for reporting.',
        quick_replies=['Report profile on platform','How can I add a screenshot?']))
    state, _, _=send(client,'What can CyberSOS help with?',state)
    assert state['next_move']['message']=='CyberSOS helps organize your details and safe records for reporting.'
    assert state['next_move']['quick_replies']==['How can I add a screenshot?']
    assert state['turns'][-1]['fact_changes']['agent']['omitted_quick_replies']==1


def test_service_account_suffix_does_not_change_supported_ownership(client, monkeypatch):
    install(monkeypatch,[candidate('signals',['account_takeover'],'account'),candidate('platform','Google account','Google account'),
        candidate('account_compromised',True,'Someone else still has access')],move('ACKNOWLEDGE_AND_WAIT',None,'I have recorded this.'))
    state, _, _=send(client,'Someone else still has access to my Google account.')
    install(monkeypatch,[],move(message='I understand someone else accessed your Google account. About when did this happen?',
        fact_refs=[{'field':'platform','value':'Google account'},{'field':'account_compromised','value':True}]))
    state, _, _=send(client,'I am worried.',state)
    assert state['turns'][-1]['fact_changes']['agent']['status']=='decided'


def test_unrelated_correction_does_not_repeat_unanswered_question(client, monkeypatch):
    install(monkeypatch,[candidate('signals',['financial'],'scammer'),candidate('money_lost',True,'sent'),
        candidate('amount','35000','35000')],move(field='remote_access',message='Can someone else still access your device?'))
    state, _, _=send(client,'I sent 35000 to a scammer.')
    corrected=candidate('amount','3500','3500');corrected['correction_source']='Correction'
    install(monkeypatch,[corrected],move(field='remote_access',message='Can someone else still access your device?'))
    state, _, _=send(client,'Correction: the amount was 3500.',state)
    assert state['facts']['amount']=='3500'
    assert state['next_move'] is None or state['next_move']['related_field']!='remote_access'
    assert state['pending_question'] is None or state['pending_question']['field']!='remote_access'


def test_unknown_loss_cannot_be_described_as_no_loss(client, monkeypatch):
    state=harassment(client,monkeypatch)
    install(monkeypatch,[],move('ANSWER_RELEVANT_QUESTION',None,
        'Money details are unnecessary for this harassment case, as no financial loss was involved.'))
    state, _, _=send(client,'Why are you asking about money?',state)
    assert state['facts']['money_lost'] is None
    assert state['turns'][-1]['fact_changes']['agent']['rejection_reason']=='UNSUPPORTED_LOSS_CLAIM'


def test_harassment_does_not_offer_unrelated_claimed_identity_questions(client, monkeypatch):
    state=harassment(client,monkeypatch)
    provider=install(monkeypatch,[],move('ACKNOWLEDGE_AND_WAIT',None,'Ready when you are.'))
    send(client,'I do not remember the username.',state)
    context=json.loads(provider.decision_contexts[-1])
    assert not {'claimed_person','claimed_organization'}&set(context['unknown_fields'])
    assert 'recipient' not in context['unknown_fields']
    assert 'identifiers' in context['unknown_fields']


def test_profile_question_cannot_target_a_claimed_identity(client, monkeypatch):
    state=harassment(client,monkeypatch)
    install(monkeypatch,[],move('ASK_CLARIFICATION','claimed_person',
        'What was the username or profile of the person who sent these messages?'))
    state,_,_=send(client,'I am worried.',state)
    assert state['next_move'] is None or state['next_move']['related_field']!='claimed_person'


def test_repeat_acknowledgement_offers_existing_review_without_approving_facts(client, monkeypatch):
    text='I note harassment on Instagram, and that you do not have screenshots available.'
    refs=[{'field':'platform','value':'Instagram'},{'field':'evidence_available','value':False}]
    install(monkeypatch,[candidate('signals',['harassment'],'harassed'),candidate('platform','Instagram','Instagram'),
        candidate('evidence_available',False,'no screenshots')],
        move('ACKNOWLEDGE_AND_WAIT',None,text,fact_refs=refs))
    state,_,_=send(client,'I was harassed on Instagram. I have no screenshots.')
    for reply in ['no','yes']:
        install(monkeypatch,[],move('ACKNOWLEDGE_AND_WAIT',None,text,fact_refs=refs))
        state,_,_=send(client,reply,state)
        assert state['turns'][-1]['fact_changes'].get('review_prompt') is True
        assert text not in state['turns'][-1]['fact_changes']['acknowledgement']
        assert state['next_move'] is None
        assert state['facts']['evidence_available'] is False
        assert state['understanding_review']['reviewed'] is False


def test_native_intent_source_is_bound_to_the_current_message():
    from app.services.ai_provider import provider_schema
    from app.schemas.understanding import Understanding
    schema=provider_schema(Understanding,context={},message='hi')
    prop=schema['properties']['intent_source']
    assert prop=={'anyOf':[{'$ref':'#/$defs/SourceQuote'},{'type':'null'}]}
    assert schema['$defs']['SourceQuote']['enum']==['hi']


def test_unmatched_intent_quote_has_bounded_validation_diagnostics(client, monkeypatch):
    state=harassment(client,monkeypatch)
    provider=install(monkeypatch,[],move('ACKNOWLEDGE_AND_WAIT',None,'Hello.'))
    provider.output=json.dumps({'language':'en','candidates':[],'intents':['question'],'intent_source':'Hi'})
    state,_,_=send(client,'hi',state)
    result=state['turns'][-1]['fact_changes']['understanding']
    assert result['parsing_succeeded'] is True
    assert result['category']=='VALIDATION_REJECTED'
    assert result['rejection_reason']=='INTENT_SOURCE_MISMATCH'
    assert state['facts']['platform']=='Instagram'


def test_new_threat_does_not_restart_a_declined_profile_question(client, monkeypatch):
    state=harassment(client,monkeypatch)
    install(monkeypatch,[],move('ASK_CLARIFICATION','identifiers','Which profile sent the messages?'))
    state,_,_=send(client,'I am worried.',state)
    provider=install(monkeypatch,[],move('ACKNOWLEDGE_AND_WAIT',None,'We can leave that unknown.'))
    provider.output=json.dumps({'language':'en','candidates':[],'intents':['not_sure'],'intent_source':'I do not remember'})
    state,_,_=send(client,'I do not remember',state)
    provider=install(monkeypatch,[candidate('signals',['threats'],'threatened'),
        candidate('threat_text','leak stories about me','leak stories about me')],
        move('ACKNOWLEDGE_AND_WAIT',None,'I have added the threat.'))
    send(client,'They threatened to leak stories about me.',state)
    assert 'identifiers' not in json.loads(provider.decision_contexts[-1])['unknown_fields']


def test_unconditional_threat_does_not_establish_coercive_blackmail(client, monkeypatch):
    state=harassment(client,monkeypatch)
    install(monkeypatch,[candidate('signals',['threats'],'threatened'),
        candidate('threat_text','he will leak stories about me online','he will leak stories about me online'),
        candidate('blackmail',True,'he will leak stories about me online')],
        move('ACKNOWLEDGE_AND_WAIT',None,'I have recorded the reported threat.'))
    state,_,_=send(client,'The guy threatened me by saying he will leak stories about me online.',state)
    assert state['facts']['blackmail'] is None
    assert state['facts']['threat_text']=='he will leak stories about me online'


def test_native_confirmation_flag_is_payment_review_only():
    from app.services.ai_provider import provider_schema
    from app.schemas.understanding import Understanding
    schema=provider_schema(Understanding,context={},message='no')
    for variant in schema['$defs']['Candidate']['anyOf']:
        if 'payment_method' not in variant['properties']['field']['enum']:
            assert variant['properties']['confirms_pending']=={'type':'null'}


def test_danger_question_cannot_invert_boolean_answer_polarity(client, monkeypatch):
    install(monkeypatch,[candidate('signals',['threats'],'threatened'),
        candidate('threat_text','threatened me','threatened me')],
        move('ASK_CLARIFICATION','immediate_danger','Are you currently safe from any immediate physical danger?'))
    state,_,_=send(client,'They threatened me.',None)
    assert state['turns'][-1]['fact_changes']['agent']['rejection_reason']=='INVERTED_DANGER_QUESTION'
    assert state['facts']['immediate_danger'] is None


def test_username_inquiry_is_a_valid_identifier_question(client, monkeypatch):
    state=harassment(client,monkeypatch)
    install(monkeypatch,[],move('ASK_CLARIFICATION','identifiers',
        'Do you have any identifying details or usernames for the person who sent them?'))
    state,_,_=send(client,'I am worried.',state)
    assert state['turns'][-1]['fact_changes']['agent']['status']=='decided'
    assert state['next_move']['related_field']=='identifiers'


def test_declining_combined_text_identifier_request_defers_identifiers_too(client, monkeypatch):
    state=harassment(client,monkeypatch)
    install(monkeypatch,[],move('ASK_CLARIFICATION','message_text',
        'Do you have any message text or identifiers you can share?'))
    state,_,_=send(client,'I am worried.',state)
    provider=install(monkeypatch,[],move('ACKNOWLEDGE_AND_WAIT',None,'We can leave those details unknown.'))
    provider.output=json.dumps({'language':'en','candidates':[],'intents':['not_sure'],'intent_source':'i dont remember'})
    send(client,'i dont remember',state)
    assert 'identifiers' not in json.loads(provider.decision_contexts[-1])['unknown_fields']


def test_greeting_retains_safe_acknowledgement_without_optional_open_question(client, monkeypatch):
    state=harassment(client,monkeypatch)
    install(monkeypatch,[],move('ACKNOWLEDGE_AND_WAIT',None,
        'Hello! How can I help you further with the Instagram incident?'))
    state,_,_=send(client,'hi',state)
    assert state['turns'][-1]['fact_changes']['agent']['status']=='decided'
    assert state['next_move']['message']=='Hello!'
    assert state['pending_question'] is None
    assert state['understanding_review']['reviewed'] is False


def test_greeting_may_reference_the_known_platform_after_review_is_offered(client, monkeypatch):
    state=harassment(client,monkeypatch)
    text='Hello! I am here to help you organize your details regarding the Instagram harassment incident. Let me know how you would like to proceed.'
    install(monkeypatch,[],move('ACKNOWLEDGE_AND_WAIT',None,text,
        fact_refs=[{'field':'platform','value':'Instagram'}]))
    state,_,_=send(client,'hi',state)
    assert state['turns'][-1]['fact_changes']['agent']['status']=='decided'
    assert state['next_move']['message']==text
