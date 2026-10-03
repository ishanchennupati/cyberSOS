import uuid
from fastapi.testclient import TestClient
from app.main import app


def create(client, **extra):
    response = client.post('/api/v1/incidents', json={'conversation_first':True, **extra})
    assert response.status_code == 201, response.text
    return response.json()['id']


def test_creation_replay_requires_creation_secret_and_keeps_one_case(client):
    payload = {'creation_id':str(uuid.uuid4()),'creation_secret':'synthetic-private-creation-secret-12345'}
    first = create(client, **payload)
    assert create(client, **payload) == first
    assert client.post('/api/v1/incidents', json={'conversation_first':True, **dict(payload, creation_secret='wrong-secret-that-is-long-enough')}).status_code == 404


def upload(client, case, key):
    # Signature-valid synthetic PDF; no real citizen data.
    return client.post(f'/api/v1/incidents/{case}/evidence',
        data={'upload_id':str(key), 'staged_for_chat':'true'},
        files={'file':('synthetic.pdf', b'%PDF-1.4\nsynthetic\n%%EOF', 'application/pdf')})


def test_attachment_only_send_is_owned_durable_and_replay_safe(client):
    case = create(client)
    key = uuid.uuid4()
    first = upload(client, case, key)
    assert first.status_code == 201, first.text
    assert upload(client, case, key).json()['id'] == first.json()['id']
    payload = {'turn_id':str(uuid.uuid4()),'expected_revision':0,'type':'message','attachment_ids':[first.json()['id']]}
    path = f'/api/v1/incidents/{case}/conversation'
    response = client.post(path+'/turns', json=payload)
    assert response.status_code == 200, response.text
    state = response.json()
    assert state['turns'][0]['attachments'][0]['original_filename'] == 'synthetic.pdf'
    assert state['turns'][0]['text'] == ''
    assert state['facts']['amount'] is None
    assert client.post(path+'/turns', json=payload).json() == state
    assert client.get(path).json() == state
    assert state['projection']['evidence_count'] == 1
    assert client.delete('/api/v1/evidence/'+first.json()['id']).status_code == 204
    after = client.get(path).json()
    assert after['turns'][0]['attachments'][0]['deleted'] is True
    assert after['projection']['evidence_count'] == 0


def test_cross_case_attachment_link_rejected_even_if_both_cases_owned(client):
    case = create(client)
    other = create(client)
    file = upload(client, other, uuid.uuid4()).json()
    response = client.post(f'/api/v1/incidents/{case}/conversation/turns', json={
        'turn_id':str(uuid.uuid4()),'expected_revision':0,'type':'message', 'text':'A synthetic file', 'attachment_ids':[file['id']]})
    assert response.status_code == 404
    assert client.get(f'/api/v1/incidents/{case}/conversation').json()['revision'] == 0


def test_text_file_stale_cancel_and_lazy_orphan_cleanup(client,db):
    from datetime import datetime,timedelta,timezone
    from app.models.evidence import Evidence
    case=create(client)
    linked=upload(client,case,uuid.uuid4()).json()['id']
    path=f'/api/v1/incidents/{case}/conversation'
    response=client.post(path+'/turns',json={'turn_id':str(uuid.uuid4()),'expected_revision':0,
        'type':'message','text':'A synthetic receipt for my case.','attachment_ids':[linked]})
    assert response.status_code==200
    assert response.json()['turns'][0]['text']=='A synthetic receipt for my case.'
    assert client.post(path+'/turns',json={'turn_id':str(uuid.uuid4()),'expected_revision':0,'type':'message','text':'stale'}).status_code==409
    cancelled=upload(client,case,uuid.uuid4()).json()['id']
    assert client.delete('/api/v1/evidence/'+cancelled).status_code==204
    assert client.get('/api/v1/evidence/'+cancelled).status_code==404
    orphan=upload(client,case,uuid.uuid4()).json()['id']
    for key in [linked,orphan]:db.get(Evidence,uuid.UUID(key)).uploaded_at=datetime.now(timezone.utc)-timedelta(hours=25)
    db.commit()
    assert upload(client,case,uuid.uuid4()).status_code==201
    assert client.get('/api/v1/evidence/'+orphan).status_code==404
    assert client.get('/api/v1/evidence/'+linked).status_code==200
