import uuid
import pytest
from tests.test_phase3r_case_agent import install,move
from tests.test_phase3_understanding import candidate


@pytest.mark.parametrize('hint',[None,'women_children','financial','other','not_sure'])
@pytest.mark.parametrize('story,candidates,signal',[
    ('A scammer made me send INR 5000 via UPI.',[candidate('money_lost',True,'send'),candidate('amount','5000','5000'),
        candidate('currency','INR','INR'),candidate('payment_method','upi','UPI'),candidate('authorization','authorized','me send'),
        candidate('signals',['financial'],'scammer')],'financial'),
    ('Someone on Instagram is threatening to share my private photos.',[candidate('signals',['threats','harassment'],'threatening'),
        candidate('platform','Instagram','Instagram'),candidate('private_image_threat',True,'threatening to share my private photos')],'threats'),
    ('Someone still has access to my Google account.',[candidate('signals',['account_takeover'],'access to my Google account'),
        candidate('platform','Google','Google'),candidate('account_compromised',True,'Someone still has access to my Google account')],'account_takeover'),
])
def test_every_hint_and_direct_story_use_the_same_canonical_system(client,monkeypatch,hint,story,candidates,signal):
    case=client.post('/api/v1/incidents',json={'conversation_first':True}).json()['id']
    path=f'/api/v1/incidents/{case}/conversation'
    state=client.get(path).json()
    if hint:
        payload=dict(turn_id=str(uuid.uuid4()),expected_revision=state['revision'],type='route_hint',route_hint=hint)
        state=client.post(path+'/turns',json=payload).json()
        assert state['route_hint']==hint
        assert state['facts']['signals']==[] and state['facts']['money_lost'] is None
        assert client.post(path+'/turns',json=payload).json()==state
    install(monkeypatch,candidates,move('ACKNOWLEDGE_AND_WAIT',None,'I have recorded what you told me.'))
    payload=dict(turn_id=str(uuid.uuid4()),expected_revision=state['revision'],type='message',text=story)
    response=client.post(path+'/turns',json=payload)
    assert response.status_code==200,response.text
    state=response.json()
    assert signal in state['facts']['signals']
    assert state['route_hint']==hint
    assert state['understanding_review']['available']
    assert client.get(path).json()==state
    if signal!='financial':
        assert not any(a['id']=='call_1930' or a['id'].startswith('contact_bank') for a in state['plan']['plan']['actions'])


def test_hint_change_does_not_restart_or_reclassify_case(client):
    case=client.post('/api/v1/incidents',json={'conversation_first':True}).json()['id']
    path=f'/api/v1/incidents/{case}/conversation'
    for revision,hint in enumerate(['financial','women_children','other','not_sure']):
        response=client.post(path+'/turns',json=dict(turn_id=str(uuid.uuid4()),expected_revision=revision,type='route_hint',route_hint=hint))
        assert response.status_code==200
        assert response.json()['facts']['signals']==[]
        assert response.json()['plan']['plan']['actions']==[]
    assert len(client.get(path).json()['turns'])==4
