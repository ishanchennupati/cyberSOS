"""Case-agent decisions use synthetic provider replies, never a real key."""
import json
import uuid
import pytest
from tests.test_phase3_understanding import candidate


def move(type='ASK_CLARIFICATION', field='occurred_at', message='About when did this happen?', **extra):
    return dict(dict(type=type, purpose='containment', message=message,
        related_field=field, quick_replies=[], evidence_kind=None, action_id=None,
        basis=['current_facts']), **extra)


def install(monkeypatch, candidates, decision):
    from app.services import understanding, case_agent
    from app.services.ai_provider import FakeProvider
    provider = FakeProvider(json.dumps({'language':'en','candidates':candidates}), next_move=json.dumps(decision))
    monkeypatch.setattr(understanding, 'get_provider', lambda: provider)
    monkeypatch.setattr(case_agent, 'get_provider', lambda: provider)
    return provider


def send(client, text, state=None):
    if state is None:
        ident=client.post('/api/v1/incidents', json={'conversation_first':True}).json()['id']
        state=client.get(f'/api/v1/incidents/{ident}/conversation').json()
    path=f"/api/v1/incidents/{state['incident_id']}/conversation"
    payload=dict(turn_id=str(uuid.uuid4()),expected_revision=state['revision'],type='message',text=text)
    response=client.post(path+'/turns',json=payload)
    assert response.status_code==200, response.text
    return response.json(), path, payload


def test_exact_reproduction_is_understood_before_ai_decides(client, monkeypatch):
    text='₹5,000 left my account without my approval.'
    provider=install(monkeypatch,[candidate('money_lost',True,'left my account'),
        candidate('amount','5000','₹5,000'),candidate('currency','INR','₹5,000'),
        candidate('authorization','unauthorized','without my approval')],move())
    state,path,payload=send(client,text)
    assert state['facts']['money_lost'] is True
    assert state['facts']['amount']=='5000' and state['facts']['currency']=='INR'
    assert state['facts']['authorization']=='unauthorized'
    assert state['pending_question'] is None
    assert state['next_move']['type']=='ASK_CLARIFICATION'
    assert state['next_move']['related_field']=='occurred_at'
    assert '₹5,000' in state['turns'][-1]['fact_changes']['acknowledgement']
    context=json.loads(provider.decision_contexts[-1])
    assert context['facts']['authorization']=='unauthorized'
    assert 'money_lost' not in context['unknown_fields']
    assert 'contact_bank_unauthorized' in [a['id'] for a in context['approved_actions']]
    assert state['facts']['transaction_id'] is state['facts']['occurred_at'] is None
    count=len(provider.decision_contexts)
    assert client.post(path+'/turns',json=payload).json()==state
    assert len(provider.decision_contexts)==count  # No new AI calls on replay/read.


def test_ai_can_request_relevant_evidence_or_ask_nothing(client, monkeypatch):
    install(monkeypatch,[candidate('money_lost',True,'gone'),candidate('amount','5000','₹5,000'),
        candidate('evidence_mentioned',['SMS'],'message')],
        move('REQUEST_EVIDENCE','evidence_available','Could you share the transaction message?',evidence_kind='transaction_message'))
    state,_,_=send(client,'₹5,000 is gone. I just got a message.')
    assert state['next_move']['type']=='REQUEST_EVIDENCE'
    assert 'extract' not in state['next_move']['message'].lower()
    assert state['facts']['authorization']=='unknown'
    install(monkeypatch,[],move('ACKNOWLEDGE_AND_WAIT',None,'Ready when you are.'))
    state,_,_=send(client,'I need a moment.',state)
    assert state['next_move']['type']=='ACKNOWLEDGE_AND_WAIT'
    assert state['pending_question'] is None


@pytest.mark.parametrize('decision',[
    move(field='money_lost',message='Did money leave your account?'),
    move(field='amount',message='How much money left?'),
    move(field='authorization',message='Did you approve it?'),
    move(field='story',message='Did you approve this transaction?'),
    move(message='Call 99999 now to recover your money?'),
    move(message='How can you transfer your savings to the caller?'),
    move(field='remote_access',message='Can you disable internet on your device?'),
    move('EXPLAIN_APPROVED_ACTION',None,'Guaranteed refund.',action_id='invented'),
    dict(move(),actions=['send_money']),
])
def test_repeated_known_or_malicious_moves_are_rejected_without_losing_actions(client,monkeypatch,decision):
    install(monkeypatch,[candidate('money_lost',True,'left'),candidate('amount','5000','₹5,000'),
        candidate('authorization','unauthorized','without approval')],decision)
    state,_,_=send(client,'₹5,000 left without approval.')
    assert state['turns'][-1]['fact_changes']['agent']['status']=='fallback'
    assert state['pending_question']['field'] not in {'money_lost','amount','authorization'}
    assert 'contact_bank_unauthorized' in [a['id'] for a in state['plan']['plan']['actions']]


def test_action_explanation_retains_wording_and_approved_policy(client,monkeypatch):
    install(monkeypatch,[candidate('money_lost',True,'Money left')],
        move('EXPLAIN_APPROVED_ACTION',None,'Model text cannot replace policy.',action_id='contact_bank_unknown'))
    state,_,_=send(client,'Money left.')
    approved=next(a for a in state['plan']['plan']['actions'] if a['id']=='contact_bank_unknown')
    assert state['next_move']['message']=='Model text cannot replace policy.'
    assert approved['instruction'] and approved['why']


def test_decision_failure_preserves_successful_understanding(client,monkeypatch):
    provider=install(monkeypatch,[candidate('money_lost',True,'Money left')],move())
    provider.next_move='not JSON'
    state,_,_=send(client,'Money left.')
    assert state['facts']['money_lost'] is True
    assert state['turns'][-1]['fact_changes']['understanding']['status']=='understood'
    assert state['turns'][-1]['fact_changes']['agent']['status']=='fallback'


def test_provider_sdk_deadline_meets_gemini_minimum(monkeypatch):
    # The service may use a shorter testing deadline, but HTTP must satisfy Gemini.
    import asyncio,httpx
    from google import genai
    from app.services.ai_provider import GeminiProvider
    from app.core.config import get_settings
    monkeypatch.setenv('GEMINI_API_KEY','synthetic-no-call')
    monkeypatch.setenv('UNDERSTANDING_TIMEOUT_SECONDS','8')
    get_settings.cache_clear()
    original=genai.Client
    deadlines=[]
    def factory(**kwargs):
        deadlines.append(kwargs['http_options'].timeout)
        kwargs['http_options'].async_client_args={'transport':httpx.MockTransport(lambda req:httpx.Response(200,json={'candidates':[{'content':{'parts':[{'text':'{}'}]}}]}))}
        return original(**kwargs)
    monkeypatch.setattr(genai,'Client',factory)
    asyncio.run(GeminiProvider().extract('Synthetic story','{}'))
    assert deadlines==[10000]


def test_provider_constrains_source_quotes_to_current_message(monkeypatch):
    import asyncio, httpx
    from google import genai
    from app.services.ai_provider import GeminiProvider
    from app.core.config import get_settings
    monkeypatch.setenv('GEMINI_API_KEY', 'synthetic-no-call')
    get_settings.cache_clear()
    original = genai.Client
    contents, schemas = [], []
    def respond(request):
        body = json.loads(request.content)
        contents.append(body['contents'][0]['parts'][0]['text'])
        schemas.append(body['generationConfig']['responseJsonSchema'])
        return httpx.Response(200, json={'candidates': [{'content': {'parts': [{'text': '{}'}]}}]})
    def factory(**kwargs):
        kwargs['http_options'].async_client_args = {'transport': httpx.MockTransport(respond)}
        return original(**kwargs)
    monkeypatch.setattr(genai, 'Client', factory)
    story = 'SBI made me send \u20b935,000 through GPay.'
    asyncio.run(GeminiProvider().extract(story, '{}'))
    assert json.loads(contents[0])['message'] == story
    for variant in schemas[0]['$defs']['Candidate']['anyOf']:
        assert variant['properties']['source_text']['$ref'] == '#/$defs/SourceQuote'
        quotes = schemas[0]['$defs']['SourceQuote']['enum']
        assert story in quotes
        assert all(quote in story for quote in quotes)
        assert all('\u2009' not in quote and '\u2031' not in quote for quote in quotes)


def test_long_story_does_not_force_repeated_whole_message_quotes():
    from app.services.ai_provider import provider_schema
    from app.schemas.understanding import Understanding
    story = 'Background detail ' * 400 + 'Someone made me send \u20b935,000 through GPay'
    schema = provider_schema(Understanding, message=story)
    assert 'SourceQuote' not in schema['$defs']
    for variant in schema['$defs']['Candidate']['anyOf']:
        assert 'enum' not in variant['properties']['source_text']


def test_provider_signal_grammar_uses_domain_vocabulary():
    from typing import get_args
    from app.domain.facts import Signal
    from app.services.ai_provider import provider_schema
    from app.schemas.understanding import Understanding
    variants = provider_schema(Understanding)['$defs']['Candidate']['anyOf']
    signal = next(v for v in variants if v['properties']['field']['enum'] == ['signals'])
    assert set(signal['properties']['value']['items']['enum']) == set(get_args(Signal))


def test_provider_schema_is_compact_but_application_remains_strict():
    from app.services.ai_provider import provider_schema
    from app.schemas.understanding import Understanding
    from pydantic import ValidationError
    schema=provider_schema(Understanding)
    variants=schema['$defs']['Candidate']['anyOf']
    for field, kind in [('amount','string'),('authorization','string'),('money_lost','boolean'),
                        ('signals','array'),('identifiers','array')]:
        variants_for_field=[v for v in variants if field in v['properties']['field']['enum']]
        assert len(variants_for_field)==1
        assert variants_for_field[0]['properties']['value']['type']==kind
    assert 'maxLength' not in json.dumps(schema)
    assert schema['additionalProperties'] is False
    malformed=candidate('amount',True,'Money left')
    with pytest.raises(ValidationError):
        Understanding.model_validate({'language':'en','candidates':[malformed]})


@pytest.mark.parametrize('text,language',[
    ('SBI nunchi ani cheppi 35k GPay lo send cheyincharu.','te-Latn'),
    ('బ్యాంకు అని చెప్పి ₹35,000 పంపించారు.','te'),
    ('Bank se bol rahe the aur 35k transfer karwa diye.','hi-Latn'),
    ('बैंक से बोलकर ₹35,000 भेजने को कहा और मैंने भेजे।','hi'),
    ('SBI nunchi call, I sent 35k via GPay.','mixed'),
])
def test_languages_share_live_case_context(client,monkeypatch,text,language):
    span='₹35,000' if '₹35,000' in text else '35k'
    provider=install(monkeypatch,[candidate('money_lost',True,text),candidate('amount','35000',span),
        candidate('authorization','authorized',text)],move(field='ongoing_loss',message='Are further transactions appearing?'))
    provider.output=json.dumps({'language':language,'candidates':json.loads(provider.output)['candidates']})
    state,_,_=send(client,text)
    assert state['next_move']['related_field']=='ongoing_loss'
    assert json.loads(provider.decision_contexts[-1])['facts']['detected_language']==language


def test_mixed_signals_corrections_and_relative_time_reassess_one_case(client,monkeypatch):
    provider=install(monkeypatch,[candidate('money_lost',True,'money left'),
        candidate('signals',['financial','device_compromise'],'installed AnyDesk and money left'),
        candidate('amount','35000','₹35,000')],move(field='remote_access',message='Does the caller still have access to your device?'))
    state,_,_=send(client,'I installed AnyDesk and money left: ₹35,000.')
    assert state['next_move']['related_field']=='remote_access'
    correction=candidate('amount','3500','₹3,500'); correction['correction_source']='Sorry'
    install(monkeypatch,[correction,candidate('time_window','about an hour ago','about an hour ago')],
        move('CONTINUE_OPEN_CONVERSATION','story','What else would you like to tell me?'))
    state,_,_=send(client,'Sorry, I checked: ₹3,500, about an hour ago.',state)
    assert state['facts']['amount']=='3500'
    assert state['facts']['time_window']['approximate']
    assert state['turns'][-1]['fact_changes']['updates'][0]['before']=='35000'
    assert state['plan']['revision']==3
    assert state['next_move']['type']=='CONTINUE_OPEN_CONVERSATION'


def test_claimed_bank_is_not_victim_bank(client,monkeypatch):
    install(monkeypatch,[candidate('money_lost',True,'made me send'),candidate('amount','35000','₹35,000'),
        candidate('authorization','authorized','made me send'),candidate('claimed_organization','SBI','SBI'),
        candidate('payment_app','GPay','GPay')],move(field='occurred_at',message='About when did this happen?'))
    state,_,_=send(client,'Someone claiming to be SBI made me send ₹35,000 through GPay.')
    assert state['facts']['claimed_organization']=='SBI'
    assert 'victim_bank' not in state['facts'] and state['facts']['payment_method']=='unknown'
    assert state['next_move'] is not None


def test_actual_conflict_is_resolved_conversationally(client,monkeypatch):
    install(monkeypatch,[candidate('money_lost',True,'lost'),candidate('amount','35000','₹35,000')],move())
    state,_,_=send(client,'I lost ₹35,000.')
    install(monkeypatch,[candidate('amount','3500','₹3,500')],
        move('RESOLVE_CONFLICT','amount','Which amount should we use?',basis=['conflict']))
    state,_,_=send(client,'₹3,500.',state)
    assert state['next_move']['type']=='RESOLVE_CONFLICT'
    assert state['facts']['amount']=='35000'
    assert state['turns'][-1]['fact_changes']['conflicts']==['amount']


def test_evidence_and_recent_conversation_context_are_scoped(client,monkeypatch,db):
    from app.models.evidence import Evidence,EvidenceType,VerificationStatus
    install(monkeypatch,[candidate('money_lost',True,'Money left')],move())
    state,_,_=send(client,'Money left.')
    other=client.post('/api/v1/incidents',json={'conversation_first':True}).json()['id']
    for ident in (state['incident_id'],other):
        db.add(Evidence(incident_id=uuid.UUID(ident),original_filename='synthetic.png',storage_path=str(uuid.uuid4()),
            mime_type='image/png',file_size=10,evidence_type=EvidenceType.sms_message,verification_status=VerificationStatus.unverified))
    db.commit()
    provider=install(monkeypatch,[],move('REQUEST_EVIDENCE','evidence_available','Could you share the message?',evidence_kind='transaction_message'))
    state,_,_=send(client,'I have a screenshot.',state)
    context=json.loads(provider.decision_contexts[-1])
    assert len(context['evidence'])==1
    assert context['recent_conversation'][0]['user']=='Money left.'
    assert context['capabilities']['ai_evidence_extraction'] is False
    assert state['next_move'] is None  # Never request an already uploaded record again.


def test_plain_answer_to_conflict_preserves_correction_history(client,monkeypatch):
    install(monkeypatch,[candidate('money_lost',True,'lost'),candidate('amount','35000','₹35,000')],move())
    state,_,_=send(client,'I lost ₹35,000.')
    install(monkeypatch,[candidate('amount','3500','₹3,500')],move('RESOLVE_CONFLICT','amount','Which amount should we use?'))
    state,_,_=send(client,'₹3,500.',state)
    install(monkeypatch,[candidate('amount','3500','₹3,500')],move('ACKNOWLEDGE_AND_WAIT',None,'Ready when you are.'))
    state,_,_=send(client,'The amount was ₹3,500.',state)
    assert state['facts']['amount']=='3500'
    assert state['turns'][-1]['fact_changes']['updates'][0]['correction'] is True
    assert state['turns'][-1]['fact_changes']['updates'][0]['before']=='35000'
    assert state['turns'][-1]['fact_changes']['conflicts']==[]


def test_unresolved_candidates_survive_intervening_turn(client,monkeypatch):
    uncertain=candidate('authorization','unauthorized','Money left')
    uncertain.update(extraction='inference',uncertainty='Approval is not stated')
    install(monkeypatch,[candidate('money_lost',True,'Money left'),uncertain],move('ACKNOWLEDGE_AND_WAIT',None,'Ready when you are.'))
    state,_,_=send(client,'Money left.')
    install(monkeypatch,[],move('VERIFY_INFORMATION','authorization','Did you approve the transaction?',basis=['candidate']))
    state,_,_=send(client,'I just received a message.',state)
    assert state['next_move']['type']=='VERIFY_INFORMATION'
    assert state['facts']['authorization']=='unknown'


def test_affirmative_to_current_access_question_establishes_access(client,monkeypatch):
    install(monkeypatch,[candidate('signals',['device_compromise'],'installed AnyDesk')],
        move(field='remote_access',message='Can someone else still access your device?',quick_replies=['Yes','No','Not sure']))
    state,_,_=send(client,'I installed AnyDesk.')
    install(monkeypatch,[candidate('remote_access',True,'Yes')],move('ACKNOWLEDGE_AND_WAIT',None,'Ready when you are.'))
    state,_,_=send(client,'Yes',state)
    assert state['facts']['remote_access'] is True
    assert state['turns'][-1]['fact_changes']['understanding']['candidates'][0]['status']=='accepted'


def test_unsure_extended_fact_is_not_verified_repeatedly(client,monkeypatch):
    uncertain=candidate('payment_app','GPay','payment app')
    uncertain.update(extraction='inference',uncertainty='App not stated')
    install(monkeypatch,[uncertain],move('VERIFY_INFORMATION','payment_app','Which app was involved?',basis=['candidate']))
    state,_,_=send(client,'A payment app was involved.')
    install(monkeypatch,[],move('ACKNOWLEDGE_AND_WAIT',None,'Ready when you are.'))
    state,_,_=send(client,'Not sure',state)
    provider=install(monkeypatch,[],move('VERIFY_INFORMATION','payment_app','Which app was involved?',basis=['candidate']))
    state,_,_=send(client,'I need a moment.',state)
    assert 'payment_app' in json.loads(provider.decision_contexts[-1])['answered_fields']
    assert state['next_move'] is None


def test_unsure_candidate_does_not_trigger_repeated_verification_on_next_two_turns(client, monkeypatch):
    install(monkeypatch, [candidate('money_lost', True, 'gone')],
            move(field='ongoing_loss', message='Is money still moving?'))
    state, _, _ = send(client, 'Money gone')
    uncertain = candidate('ongoing_loss', False, 'Not sure')
    uncertain.update(extraction='inference', uncertainty='Ongoing loss is unknown')
    provider = install(monkeypatch, [uncertain], move())
    contexts = []
    async def investigate(context):
        context = json.loads(context)
        contexts.append(context)
        if any(c['field'] == 'ongoing_loss' and c['status'] == 'needs_review'
               for c in context['candidates']):
            return json.dumps(move('VERIFY_INFORMATION', 'ongoing_loss', 'Is money still moving?'))
        return json.dumps(move(field='remote_access', message='Does someone still have remote access to your device?'))
    monkeypatch.setattr(provider, 'decide', investigate)
    state, _, _ = send(client, 'Not sure', state)
    assert state['turns'][-1]['fact_changes']['agent']['status'] == 'decided'
    assert state['facts']['ongoing_loss'] is None
    assert not state['turns'][-1]['fact_changes']['unresolved_candidates']
    # The original uncertain interpretation remains in historical provenance.
    assert state['turns'][-1]['fact_changes']['understanding']['candidates'][0]['status'] == 'needs_review'
    provider.output = json.dumps({'language': 'en', 'candidates': []})
    state, _, _ = send(client, 'I need a moment.', state)
    assert state['turns'][-1]['fact_changes']['agent']['status'] == 'decided'
    assert all('ongoing_loss' in c['answered_fields'] for c in contexts)
    assert all(not any(v['field'] == 'ongoing_loss' for v in c['candidates']) for c in contexts)


def test_provider_question_grammar_excludes_answered_verification_but_allows_conflicts():
    from app.services.ai_provider import provider_schema
    from app.schemas.next_move import NextMove
    context = {'unknown_fields': ['ongoing_loss', 'remote_access'], 'answered_fields': ['ongoing_loss', 'amount'],
        'candidates': [{'field': 'ongoing_loss', 'status': 'needs_review'},
                       {'field': 'payment_app', 'status': 'needs_review'}], 'conflicts': ['amount']}
    variants = provider_schema(NextMove, context=context)['anyOf']
    by_type = {kind: variant for variant in variants for kind in variant['properties']['type']['enum']}
    assert by_type['ASK_CLARIFICATION']['properties']['related_field']['enum'] == ['remote_access']
    assert by_type['VERIFY_INFORMATION']['properties']['related_field']['enum'] == ['payment_app']
    assert by_type['RESOLVE_CONFLICT']['properties']['related_field']['enum'] == ['amount']
    assert 'REQUEST_EVIDENCE' in by_type and 'ACKNOWLEDGE_AND_WAIT' in by_type
    context['candidates'] = [{'field': 'ongoing_loss', 'status': 'needs_review'}]
    variants = provider_schema(NextMove, context=context)['anyOf']
    assert not any('VERIFY_INFORMATION' in v['properties']['type']['enum'] for v in variants)


def test_grounded_amount_question_keeps_ai_wording(client, monkeypatch):
    wording = 'Was the ₹5,000 debit shown as UPI, card, or something else?'
    install(monkeypatch, [candidate('money_lost', True, 'left'), candidate('amount', '5000', '₹5,000'),
        candidate('currency', 'INR', '₹5,000'), candidate('authorization', 'unauthorized', 'without approval')],
        move(field='payment_method', message=wording))
    state, _, _ = send(client, '₹5,000 left without approval.')
    assert state['next_move'] is not None
    assert state['next_move']['message'] == wording


@pytest.mark.parametrize('correction_text', ['Sorry, the amount was \u20b94,500.', 'Correction: \u20b94,500.'])
def test_explicit_amount_correction_does_not_depend_on_provider_marker(client, monkeypatch, correction_text):
    install(monkeypatch, [candidate('money_lost', True, 'left'),
        candidate('amount', '5000', '\u20b95,000')], move())
    state, _, _ = send(client, '\u20b95,000 left.')
    original = state['turns'][0]['text']
    install(monkeypatch, [candidate('amount', '4500', '\u20b94,500')], move())
    state, _, _ = send(client, correction_text, state)
    assert state['facts']['amount'] == '4500'
    assert state['turns'][0]['text'] == original
    assert any(u['field'] == 'amount' and u['before'] == '5000' and u['after'] == '4500'
        and u['correction'] for u in state['turns'][-1]['fact_changes']['updates'])


def test_apology_about_another_detail_does_not_authorize_amount_overwrite(client, monkeypatch):
    install(monkeypatch, [candidate('money_lost', True, 'left'),
        candidate('amount', '5000', '\u20b95,000')], move())
    state, _, _ = send(client, '\u20b95,000 left.')
    install(monkeypatch, [candidate('amount', '4500', '\u20b94,500')],
        move('RESOLVE_CONFLICT', 'amount', 'Was the amount 5000 or 4500?'))
    state, _, _ = send(client, 'Sorry about the delay. Another message says \u20b94,500.', state)
    assert state['facts']['amount'] == '5000'
    assert 'amount' in state['turns'][-1]['fact_changes']['conflicts']



def test_legitimate_authorization_quick_replies_survive(client, monkeypatch):
    wording = 'Did you approve this payment yourself, or did it move without your approval?'
    replies = ['I approved it after deception', 'I did not approve it', 'Not sure']
    install(monkeypatch, [candidate('money_lost', True, 'gone'), candidate('amount', '5000', '5000')],
        move(field='authorization', message=wording, quick_replies=replies))
    state, _, _ = send(client, '5000 gone')
    assert state['next_move'] is not None
    assert state['next_move']['message'] == wording
    assert state['next_move']['quick_replies'] == replies
    assert '5,000' in state['turns'][-1]['fact_changes']['acknowledgement']
    assert 'account' not in state['turns'][-1]['fact_changes']['acknowledgement']
    assert '₹' not in state['turns'][-1]['fact_changes']['acknowledgement']


@pytest.mark.parametrize('decision', [
    move(field='payment_method', message='Was the ₹9,000 debit shown as UPI or card?'),
    move(field='remote_access', message='Can you disable internet on your device?'),
    move(field='authorization', message='What is your OTP?'),
    move('ACKNOWLEDGE_AND_WAIT', None, 'Your bank has frozen the funds.'),
    move('ACKNOWLEDGE_AND_WAIT', None, 'Your money will be recovered.'),
    move('ACKNOWLEDGE_AND_WAIT', None, 'You can continue knowing your bank has accepted your complaint.'),
    move('REQUEST_EVIDENCE', 'evidence_available', 'Attach your passport so I can check this transaction.', evidence_kind='transaction_receipt'),
    move(field='remote_access', message='How can you wipe your device?'),
    move(field='payment_method', message='Was your SBI bank account debited via UPI?'),
])
def test_rejection_has_distinct_validation_diagnostics(client, monkeypatch, decision):
    install(monkeypatch, [candidate('money_lost', True, 'gone'), candidate('amount', '5000', '5000')], decision)
    state, _, _ = send(client, '5000 gone')
    agent = state['turns'][-1]['fact_changes']['agent']
    assert agent['category'] == 'VALIDATION_REJECTED'
    assert agent['invocation_succeeded'] and agent['parsing_succeeded']
    assert agent['rejection_reason']
    assert agent['proposed_type'] == decision['type']


@pytest.mark.parametrize('error, category', [(TimeoutError(), 'TIMEOUT'), (RuntimeError(), 'APPLICATION_ERROR')])
def test_decision_exception_category(client, monkeypatch, error, category):
    provider = install(monkeypatch, [candidate('money_lost', True, 'gone')], move())
    async def broken(context):
        raise error
    monkeypatch.setattr(provider, 'decide', broken)
    state, _, _ = send(client, 'Money gone')
    assert state['turns'][-1]['fact_changes']['agent']['category'] == category


def test_acknowledgement_ai_wording_is_retained(client, monkeypatch):
    wording = 'Take your time. You can keep telling me what happened when you are ready.'
    install(monkeypatch, [], move('ACKNOWLEDGE_AND_WAIT', None, wording))
    state, _, _ = send(client, 'I need a moment.')
    assert state['next_move']['message'] == wording


def test_canonical_ai_acknowledgement_survives(client, monkeypatch):
    wording = 'I understand. ₹5,000 left and you did not approve the transaction.'
    install(monkeypatch, [candidate('money_lost', True, 'left'), candidate('amount', '5000', '₹5,000'),
        candidate('currency', 'INR', '₹'), candidate('authorization', 'unauthorized', 'without approval')],
        move('ACKNOWLEDGE_AND_WAIT', None, wording))
    state, _, _ = send(client, '₹5,000 left without approval.')
    assert state['next_move']['message'] == wording
    assert state['turns'][-1]['fact_changes']['acknowledgement'] == ''


def test_provider_503_is_not_validation_rejection(client, monkeypatch):
    from google.genai.errors import ServerError
    provider = install(monkeypatch, [candidate('money_lost', True, 'gone')], move())
    async def unavailable(context):
        raise ServerError(503, {'error': {'message': 'Synthetic high demand', 'status': 'UNAVAILABLE'}})
    monkeypatch.setattr(provider, 'decide', unavailable)
    state, _, _ = send(client, 'Money gone')
    diagnostic = state['turns'][-1]['fact_changes']['agent']
    assert diagnostic['category'] == 'PROVIDER_5XX' and diagnostic['http_status'] == 503
    assert not diagnostic['invocation_succeeded'] and not diagnostic['parsing_succeeded']
    assert diagnostic['rejection_reason'] is None
    assert state['facts']['money_lost'] is True


def test_malformed_decision_category(client, monkeypatch):
    provider = install(monkeypatch, [candidate('money_lost', True, 'gone')], move())
    provider.next_move = '{broken'
    state, _, _ = send(client, 'Money gone')
    diagnostic = state['turns'][-1]['fact_changes']['agent']
    assert diagnostic['category'] == 'MALFORMED_OUTPUT'
    assert diagnostic['invocation_succeeded'] and not diagnostic['parsing_succeeded']
    assert diagnostic['validation_errors'][0]['type'] == 'json_invalid'
    assert 'input' not in diagnostic['validation_errors'][0]
