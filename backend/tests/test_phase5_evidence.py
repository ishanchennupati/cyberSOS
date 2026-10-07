import uuid
from app.schemas.evidence_intelligence import EvidenceAnalysis
from tests.test_phase4_durability import create, upload


def setup(client, monkeypatch, candidates=None):
    from app.services import evidence_intelligence as intelligence
    calls = []
    def analyze(*args, **kwargs):
        calls.append(1)
        return EvidenceAnalysis(readable=True, candidates=candidates or [dict(field='amount', value='3500',
            source_text='INR 3,500', confidence=.95), dict(field='currency', value='INR',
            source_text='INR 3,500', confidence=.95)])
    monkeypatch.setattr(intelligence, 'analyze_bytes', analyze)
    case = create(client)
    evidence = upload(client, case, uuid.uuid4()).json()['id']
    client.post(f'/api/v1/incidents/{case}/conversation/turns', json=dict(turn_id=str(uuid.uuid4()),
        expected_revision=0, type='message', attachment_ids=[evidence]))
    request = dict(attempt_id=str(uuid.uuid4()), expected_revision=1)
    response = client.post(f'/api/v1/evidence/{evidence}/analyze', json=request)
    assert response.status_code == 200, response.text
    return case, evidence, request, response.json(), calls


def review(client, case, revision, attempt, decisions, key=None):
    payload = dict(turn_id=key or str(uuid.uuid4()), expected_revision=revision, type='evidence_review',
        evidence_review=dict(attempt_id=attempt, decisions=decisions))
    response = client.post(f'/api/v1/incidents/{case}/conversation/turns', json=payload)
    return response, payload


def test_extraction_is_candidate_only_replay_never_calls_provider_and_partial_merge_is_atomic(client, monkeypatch):
    case, evidence, request, analysis, calls = setup(client, monkeypatch)
    path = f'/api/v1/incidents/{case}/conversation'
    assert client.get(path).json()['facts']['amount'] is None
    assert client.post(f'/api/v1/evidence/{evidence}/analyze', json=request).json() == analysis
    assert len(calls) == 1
    amount = analysis['candidates'][0]['id']
    response, payload = review(client, case, 1, request['attempt_id'], [dict(candidate_id=amount, decision='accept')])
    assert response.status_code == 200, response.text
    state = response.json()
    assert state['facts']['amount'] == '3500'
    assert state['facts']['currency'] is None
    assert state['facts']['provenance'][-1]['evidence_id'] == evidence
    assert state['facts']['provenance'][-1]['verified'] is True
    assert state['memory']['facts']['amount']['value'] == '3500'
    assert client.post(path+'/turns', json=payload).json() == state
    assert len(calls) == 1
    assert client.get(path).json()['evidence_reviews'][0]['candidates'][1]['reviewed'] is False


def test_review_wrong_case_and_stale_revision_rejected(client, monkeypatch):
    case, _, request, analysis, _ = setup(client, monkeypatch)
    decision = [dict(candidate_id=analysis['candidates'][0]['id'], decision='accept')]
    other = create(client)
    assert review(client, other, 0, request['attempt_id'], decision)[0].status_code == 404
    assert review(client, case, 0, request['attempt_id'], decision)[0].status_code == 409


def test_conflicting_amount_requires_explicit_resolution_and_does_not_promote_currency(client, monkeypatch):
    case, _, request, analysis, _ = setup(client, monkeypatch)
    from tests.test_phase3r_case_agent import install, move
    from tests.test_phase3_understanding import candidate
    install(monkeypatch, [candidate('amount', '35000', '35000')], move('ACKNOWLEDGE_AND_WAIT', None, 'I have recorded that.'))
    path = f'/api/v1/incidents/{case}/conversation'
    assert client.post(path+'/turns', json=dict(turn_id=str(uuid.uuid4()), expected_revision=1,
        type='message', text='Correction: 35000')).status_code == 200
    decisions = [dict(candidate_id=analysis['candidates'][0]['id'], decision='accept')]
    assert review(client, case, 2, request['attempt_id'], decisions)[0].status_code == 409
    decisions[0]['resolve_conflict'] = True
    response, _ = review(client, case, 2, request['attempt_id'], decisions)
    assert response.status_code == 200, response.text
    assert response.json()['facts']['amount'] == '3500'
    assert response.json()['facts']['currency'] is None


def test_deletion_removes_candidates_and_tombstones_verified_provenance(client, monkeypatch, db):
    case, evidence, request, analysis, _ = setup(client, monkeypatch)
    response, _ = review(client, case, 1, request['attempt_id'], [dict(candidate_id=analysis['candidates'][0]['id'], decision='accept')])
    assert response.status_code == 200
    assert client.delete(f'/api/v1/evidence/{evidence}').status_code == 204
    state = client.get(f'/api/v1/incidents/{case}/conversation').json()
    assert state['evidence_reviews'] == []
    assert state['facts']['amount'] == '3500'
    assert state['facts']['provenance'][-1]['source_deleted'] is True
    from app.models.evidence import EvidenceAttempt
    assert db.get(EvidenceAttempt, uuid.UUID(request['attempt_id'])) is None
    assert review(client, case, state['revision'], request['attempt_id'], [dict(candidate_id=analysis['candidates'][0]['id'], decision='accept')])[0].status_code == 404


def test_natural_partial_review_and_broad_yes_never_promotes_unrelated_fields(client, monkeypatch):
    case, _, request, analysis, _ = setup(client, monkeypatch)
    import json
    from app.services import understanding, case_agent
    from app.services.ai_provider import FakeProvider
    from tests.test_phase3r_case_agent import move
    path = f'/api/v1/incidents/{case}/conversation'
    def send(text, revision):
        proposal = dict(attempt_id=request['attempt_id'], source_text=text, reference_text='attachment' if 'attachment' in text else None,
            decisions=[dict(candidate_id=c['id'], decision='accept') for c in analysis['candidates']])
        provider = FakeProvider(json.dumps(dict(language='en', candidates=[], evidence_review=proposal)),
            next_move=json.dumps(move('ACKNOWLEDGE_AND_WAIT', None, 'Your review is recorded.')))
        monkeypatch.setattr(understanding, 'get_provider', lambda: provider)
        monkeypatch.setattr(case_agent, 'get_provider', lambda: provider)
        return client.post(path+'/turns', json=dict(turn_id=str(uuid.uuid4()), expected_revision=revision,
            type='message', text=text, review_context_id=request['attempt_id']))
    assert send('Yes', 1).json()['facts']['amount'] is None
    response = send('All details in this attachment are correct.', 2)
    assert response.status_code == 200, response.text
    assert response.json()['facts']['amount'] == '3500'
    assert response.json()['facts']['currency'] == 'INR'


def test_provider_number_and_status_normalization_preserves_visible_source(client, monkeypatch):
    case, _, request, analysis, _ = setup(client, monkeypatch, [dict(field='amount', value='3,500.00',
        source_text='INR 3,500.00', confidence=.95), dict(field='transaction_status', value='Completed',
        source_text='Completed', confidence=.95)])
    assert len(analysis['candidates']) == 2
    response, _ = review(client, case, 1, request['attempt_id'], [dict(candidate_id=c['id'], decision='accept') for c in analysis['candidates']])
    assert response.status_code == 200, response.text
    assert response.json()['facts']['amount'] == '3500.00'
    assert response.json()['facts']['transaction_status'] == 'completed'


def test_result_after_deletion_does_not_resurrect_private_data(client, monkeypatch):
    from app.services import evidence_intelligence as intelligence
    case = create(client)
    evidence = upload(client, case, uuid.uuid4()).json()['id']
    client.post(f'/api/v1/incidents/{case}/conversation/turns', json=dict(turn_id=str(uuid.uuid4()),
        expected_revision=0, type='message', attachment_ids=[evidence]))
    def analyze(*args):
        assert client.delete(f'/api/v1/evidence/{evidence}').status_code == 204
        return EvidenceAnalysis(readable=True, candidates=[dict(field='amount', value='3500',source_text='3500',confidence=1)])
    monkeypatch.setattr(intelligence, 'analyze_bytes', analyze)
    response = client.post(f'/api/v1/evidence/{evidence}/analyze', json=dict(attempt_id=str(uuid.uuid4()), expected_revision=1))
    assert response.status_code == 404
    assert client.get(f'/api/v1/incidents/{case}/conversation').json()['evidence_reviews'] == []


def test_two_reviewed_identifiers_keep_their_own_evidence_sources(client, monkeypatch):
    from app.services import evidence_intelligence as intelligence
    case, first_file, request, analysis, _ = setup(client, monkeypatch, [dict(field='identifiers',
        value='first@upi',source_text='first@upi',confidence=.9,identifier_type='upi')])
    response, _ = review(client, case, 1, request['attempt_id'],[dict(candidate_id=analysis['candidates'][0]['id'],decision='accept')])
    second_file = upload(client, case, uuid.uuid4()).json()['id']
    client.post(f'/api/v1/incidents/{case}/conversation/turns',json=dict(turn_id=str(uuid.uuid4()),
        expected_revision=2,type='message',attachment_ids=[second_file]))
    monkeypatch.setattr(intelligence,'analyze_bytes',lambda *a:EvidenceAnalysis(readable=True,candidates=[dict(field='identifiers',
        value='second@upi',source_text='second@upi',confidence=.9,identifier_type='upi')]))
    second_request = dict(attempt_id=str(uuid.uuid4()),expected_revision=3)
    second = client.post(f'/api/v1/evidence/{second_file}/analyze',json=second_request).json()
    response,_ = review(client,case,3,second_request['attempt_id'],[dict(candidate_id=second['candidates'][0]['id'],decision='accept')])
    sources = {p['identifier_value']:p['evidence_id'] for p in response.json()['facts']['provenance'] if p['field']=='identifiers'}
    assert sources == {'first@upi':first_file,'second@upi':second_file}


def test_yes_to_an_unrelated_question_does_not_verify_a_single_remaining_candidate(client, monkeypatch):
    import json
    from app.services import understanding,case_agent
    from app.services.ai_provider import FakeProvider
    from tests.test_phase3r_case_agent import move
    case,_,request,analysis,_ = setup(client,monkeypatch,[dict(field='amount',value='3500',source_text='3500',confidence=.9)])
    for revision,text in [(1,'Yes'),(2,'Yes, thanks')]:
        output = dict(language='en',candidates=[],evidence_review=dict(attempt_id=request['attempt_id'],source_text=text,
            decisions=[dict(candidate_id=analysis['candidates'][0]['id'],decision='accept')]))
        provider = FakeProvider(json.dumps(output),next_move=json.dumps(move('ACKNOWLEDGE_AND_WAIT',None,'I have recorded your reply.')))
        monkeypatch.setattr(understanding,'get_provider',lambda:provider)
        monkeypatch.setattr(case_agent,'get_provider',lambda:provider)
        response=client.post(f'/api/v1/incidents/{case}/conversation/turns',json=dict(turn_id=str(uuid.uuid4()),expected_revision=revision,type='message',text=text))
        assert response.status_code==200,response.text
        assert response.json()['facts']['amount'] is None


def test_deleted_source_flag_cannot_bypass_case_ownership(client):
    own=client.post('/api/v1/incidents',json={'incident_type':'financial_fraud'}).json()['id']
    other=create(client)
    foreign=upload(client,other,uuid.uuid4()).json()['id']
    response=client.put(f'/api/v1/incidents/{own}/facts',json={'kind':'financial_authorization_unknown',
        'amount':'3500','provenance':[{'field':'amount','origin':'user_verification','verified':True,
            'evidence_id':foreign,'source_deleted':True}]})
    assert response.status_code==422,response.text


def test_named_amount_review_cannot_verify_unmentioned_currency(client,monkeypatch):
    import json
    from app.services import understanding,case_agent
    from app.services.ai_provider import FakeProvider
    from tests.test_phase3r_case_agent import move
    case,_,request,analysis,_=setup(client,monkeypatch)
    text='The amount 3500 is correct.'
    provider=FakeProvider(json.dumps(dict(language='en',candidates=[],evidence_review=dict(attempt_id=request['attempt_id'],
        source_text=text,reference_text='amount 3500',decisions=[dict(candidate_id=c['id'],decision='accept') for c in analysis['candidates']]))),
        next_move=json.dumps(move('ACKNOWLEDGE_AND_WAIT',None,'Your reply is recorded.')))
    monkeypatch.setattr(understanding,'get_provider',lambda:provider)
    monkeypatch.setattr(case_agent,'get_provider',lambda:provider)
    response=client.post(f'/api/v1/incidents/{case}/conversation/turns',json=dict(turn_id=str(uuid.uuid4()),expected_revision=1,type='message',text=text))
    assert response.status_code==200,response.text
    assert response.json()['facts']['currency'] is None


def test_abandoned_processing_attempt_can_be_explicitly_retried(client,monkeypatch,db):
    from datetime import datetime,timedelta,timezone
    from app.models.evidence import EvidenceAttempt,Evidence,ExtractionStatus
    from app.services import evidence_intelligence as intelligence
    case,evidence,request,analysis,_=setup(client,monkeypatch)
    attempt=db.get(EvidenceAttempt,uuid.UUID(request['attempt_id']))
    attempt.status='processing'
    attempt.created_at=datetime.now(timezone.utc)-timedelta(minutes=3)
    db.get(Evidence,uuid.UUID(evidence)).extraction_status=ExtractionStatus.processing
    db.commit()
    state=client.get(f'/api/v1/incidents/{case}/conversation').json()
    assert state['evidence_reviews'][0]['status']=='failed'
    assert state['evidence_reviews'][0]['failure']=='INTERRUPTED'
    next_request=dict(attempt_id=str(uuid.uuid4()),expected_revision=state['revision'])
    response=client.post(f'/api/v1/evidence/{evidence}/analyze',json=next_request)
    assert response.status_code==200,response.text
    assert response.json()['status']=='review_needed'


def test_replacement_cannot_resurrect_a_deleted_attachment_in_old_messages(client,monkeypatch):
    case,evidence,_,_,_=setup(client,monkeypatch)
    assert client.delete(f'/api/v1/evidence/{evidence}').status_code==204
    assert upload(client,case,uuid.UUID(evidence)).status_code==409
    state=client.get(f'/api/v1/incidents/{case}/conversation').json()
    assert state['turns'][0]['attachments'][0]['deleted'] is True
