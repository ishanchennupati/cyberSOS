"""Phase 7 progression must not imply fact/report approval or evidence existence."""
import uuid
import pytest
from tests.test_phase3r_case_agent import install, move, send
from tests.test_phase3_understanding import candidate


@pytest.mark.parametrize('hint', ['financial', 'women_children', 'other'])
def test_ai_readiness_presents_without_citizen_approval(client, monkeypatch, hint):
    ident = client.post('/api/v1/incidents', json={'conversation_first': True}).json()['id']
    path = f'/api/v1/incidents/{ident}/conversation'
    state = client.get(path).json()
    state = client.post(path+'/turns', json={'turn_id': str(uuid.uuid4()),
        'expected_revision': state['revision'], 'type': 'route_hint', 'route_hint': hint}).json()
    install(monkeypatch, [candidate('signals', ['harassment'], 'harassed'),
        candidate('platform', 'Instagram', 'Instagram')],
        move('ACKNOWLEDGE_AND_WAIT', None, 'Your account is recorded.',
             companion_ready=True))
    state, path, _ = send(client, 'I was harassed on Instagram.', state)
    assert state['projection']['companion']['presented'] is True
    assert state['understanding_review']['reviewed'] is False
    assert state['pending_question'] is None
    install(monkeypatch, [], move(field='evidence_available', message='Do you have safe records?'))
    state, _, _ = send(client, 'Thanks.', state)
    assert state['next_move'] is None
    assert state['pending_question'] is None
    assert client.get(path).json()['projection']['companion']['presented'] is True


def test_active_evidence_yes_is_consent_not_canonical_fact(client, monkeypatch):
    install(monkeypatch, [candidate('signals', ['harassment'], 'harassed')],
        move('REQUEST_EVIDENCE', 'evidence_available', 'Would you like to share a safe screenshot?',
             evidence_kind='non_explicit_conversation'))
    state, path, _ = send(client, 'I was harassed online.')
    install(monkeypatch, [candidate('evidence_available', True, 'Yes')],
        move('REQUEST_EVIDENCE', 'evidence_available', 'Would you like to share a safe screenshot?',
             evidence_kind='non_explicit_conversation'))
    state, _, _ = send(client, 'Yes', state)
    assert state['facts']['evidence_available'] is None
    assert state['projection']['companion']['evidence_offer'] == 'accepted'
    assert state['next_move'] is None
    assert state['pending_question'] is None
    assert 'attach' in state['turns'][-1]['fact_changes']['acknowledgement'].lower()
    assert client.get(path).json()['projection']['companion']['evidence_offer'] == 'accepted'


def test_completion_does_not_replay_ai_question(client, monkeypatch):
    install(monkeypatch, [candidate('signals', ['harassment'], 'harassed')], move())
    state, path, _ = send(client, 'I was harassed online.')
    action = next(a for a in state['plan']['plan']['actions'] if a['can_mark_complete'])
    response = client.post(path+'/turns', json={'turn_id': str(uuid.uuid4()),
        'expected_revision': state['revision'], 'type': 'completion', 'action_id': action['id'], 'value': True})
    assert response.status_code == 200
    assert response.json()['next_move'] is None
    assert response.json()['pending_question'] is None


def test_note_and_external_reference_are_revision_owned_records(client, monkeypatch):
    install(monkeypatch, [], move('ACKNOWLEDGE_AND_WAIT', None, 'I am here.'))
    state, path, _ = send(client, 'Hello.')
    payload = {'turn_id': str(uuid.uuid4()), 'expected_revision': state['revision'],
        'type': 'case_update', 'case_update': {'kind': 'reference', 'text': 'SYNTHETIC-123', 'organization': 'Bank'}}
    result = client.post(path+'/turns', json=payload)
    assert result.status_code == 200
    updated = result.json()
    assert updated['projection']['records'][0]['text'] == 'SYNTHETIC-123'
    assert updated['projection']['records'][0]['meaning'] == 'Recorded by you'
    assert client.post(path+'/turns', json=payload).json() == updated
    assert client.post(path+'/turns', json={**payload, 'turn_id': str(uuid.uuid4())}).status_code == 409


def test_account_takeover_can_offer_useful_safe_records(client, monkeypatch):
    install(monkeypatch, [candidate('signals',['account_takeover'],'access'),candidate('platform','Google','Google')],
        move('REQUEST_EVIDENCE','evidence_available','Would you like to share a safe account screenshot?',evidence_kind='profile_identifier'))
    state,_,_=send(client,'Someone has access to my Google account.')
    assert state['next_move']['type']=='REQUEST_EVIDENCE'


def test_greeting_and_isolated_yes_cannot_present_or_approve_case(client, monkeypatch):
    install(monkeypatch, [], move('ACKNOWLEDGE_AND_WAIT',None,'I am here.',companion_ready=True))
    state,_,_=send(client,'Hello.')
    assert not state['projection']['companion']['presented']
    state,_,_=send(client,'Yes',state)
    assert not state['projection']['companion']['presented']
    assert not state['understanding_review']['reviewed']


def test_process_answer_evidence_offer_yes_does_not_repeat(client, monkeypatch):
    install(monkeypatch,[candidate('signals',['harassment'],'harassed')],
        move('ANSWER_RELEVANT_QUESTION','story','CyberSOS organizes your records. Would you like help preserving safe screenshots?',offers_evidence=True))
    state,_,_=send(client,'I was harassed. What does CyberSOS do?')
    assert state['projection']['companion']['evidence_offer']=='offered'
    state,_,_=send(client,'Yes please',state)
    assert state['projection']['companion']['evidence_offer']=='accepted'
    assert state['facts']['evidence_available'] is None
    assert state['next_move'] is None


def test_provider_grammar_does_not_offer_material_reintake_before_companion():
    from app.services.ai_provider import provider_schema
    from app.schemas.next_move import NextMove
    context={'facts':{'signals':['financial'],'amount':'3500'},'unknown_fields':['authorization','occurred_at'],
        'answered_fields':[],'candidates':[],'conflicts':[],'memory':{},'approved_actions':[],
        'case_state':{'companion':{'presented':False}},'evidence':[]}
    grammar=provider_schema(NextMove,context=context)
    assert grammar['properties']['response']['properties']['material_follow_up']=={'type':'null'}
    variants=grammar['properties']['interaction']['anyOf']
    assert all(next(iter(variant['properties']))=='type' for variant in variants)
    assert 'fact_refs' in grammar['properties']['response']['properties']
    assert all('fact_refs' not in variant['properties'] for variant in variants)


def test_native_envelope_decodes_to_existing_bounded_move():
    import json
    from app.services.ai_provider import decode_next_move
    raw={'response':{'purpose':'understanding','message':'Your details are saved.','basis':['current_facts'],
        'companion_ready':True},'interaction':{'type':'ACKNOWLEDGE_AND_WAIT','related_field':None,
        'quick_replies':[],'evidence_kind':None,'action_id':None}}
    result=json.loads(decode_next_move(json.dumps(raw)))
    assert result['type']=='ACKNOWLEDGE_AND_WAIT' and result['companion_ready'] is True
    assert result['fact_refs']==[]
    # A type in the prose payload cannot override the typed interaction.
    raw['response']['type']='ASK_CLARIFICATION'
    from app.services.case_agent import MoveRejected
    with pytest.raises(MoveRejected):decode_next_move(json.dumps(raw))


def test_today_is_kept_as_an_approximate_day_not_repeated_as_unknown():
    from datetime import datetime, timezone
    from app.services.understanding import resolve_time
    actual=resolve_time('today',datetime(2026,10,16,8,0,tzinfo=timezone.utc),'Asia/Kolkata')
    assert actual is not None
    assert actual.start==datetime(2026,10,15,18,30,tzinfo=timezone.utc)
    assert actual.end==datetime(2026,10,16,8,0,tzinfo=timezone.utc)
    assert actual.approximate is True and actual.original=='today'


def test_grounded_threat_context_can_present_without_classification_gate(client, monkeypatch):
    # Classification remains uncertain; quoted case content still supports a draft.
    signal=candidate('signals',['harassment'],'posting');signal['extraction']='inference'
    install(monkeypatch,[signal,candidate('threat_text','I will keep posting about you','I will keep posting about you')],
        move('ACKNOWLEDGE_AND_WAIT',None,'Your reported message is recorded.',companion_ready=True))
    state,_,_=send(client,'They wrote I will keep posting about you.')
    assert state['facts']['signals']==[]
    assert state['projection']['companion']['presented'] is True
    assert state['understanding_review']['available'] is True
    assert state['understanding_review']['reviewed'] is False


def test_natural_reference_cannot_invent_its_organization(client, monkeypatch):
    import json
    from tests.test_phase3_understanding import story
    text='My reference is SYNTHETIC-123.'
    _,state,_=story(client,monkeypatch,text,output=json.dumps({'language':'en','candidates':[],
        'case_records':[{'kind':'reference','text':'SYNTHETIC-123','organization':'Police',
            'source_text':text}]}))
    record=state['projection']['records'][0]
    assert record['text']=='SYNTHETIC-123'
    assert record['organization'] is None
