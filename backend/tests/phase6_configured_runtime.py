"""Synthetic configured persistence/control acceptance, fake AI only."""
import json
import uuid
from fastapi.testclient import TestClient
from app.main import app
from app.services import understanding, case_agent
from app.services.ai_provider import FakeProvider
from tests.test_phase3_understanding import candidate
from tests.test_phase3r_case_agent import move


def main():
    provider=FakeProvider(json.dumps({'language':'en','candidates':[
        candidate('signals',['harassment'],'harassed'),candidate('platform','Instagram','Instagram')]}),
        next_move=json.dumps(move('ACKNOWLEDGE_AND_WAIT',None,'I have recorded these details.')))
    understanding.get_provider=case_agent.get_provider=lambda:provider
    with TestClient(app,base_url='https://testserver') as client:
        created=client.post('/api/v1/incidents',json={'conversation_first':True})
        assert created.status_code==201
        path=f"/api/v1/incidents/{created.json()['id']}/conversation"
        state=client.get(path).json()
        def send(text):
            nonlocal state
            payload=dict(turn_id=str(uuid.uuid4()),expected_revision=state['revision'],type='message',text=text)
            response=client.post(path+'/turns',json=payload)
            assert response.status_code==200
            state=response.json()
            assert client.post(path+'/turns',json=payload).json()==state
        send('Someone harassed me on Instagram.')
        broken=FakeProvider(error=TimeoutError())
        understanding.get_provider=case_agent.get_provider=lambda:broken
        send('Stop asking questions. Give me the plan.')
        assert state['memory']['questions_paused'] is True and state['pending_question'] is None
        assert state['projection']['current_help']['known_facts']['platform']['value']=='Instagram'
        assert state['understanding_review']['reviewed'] is False
        correction=candidate('platform','Facebook','Facebook');correction['correction_source']='Correction'
        provider.output=json.dumps({'language':'en','candidates':[correction]})
        understanding.get_provider=case_agent.get_provider=lambda:provider
        send('Correction: this happened on Facebook.')
        restored=client.get(path).json()
        assert restored['memory']['questions_paused'] is True
        assert restored['projection']['current_help']['known_facts']['platform']['value']=='Facebook'
        assert restored['facts']['money_lost'] is None
        with TestClient(app,base_url='https://testserver') as outsider:
            assert outsider.get(path).status_code==404
        print(json.dumps({'configured_persistence':'passed','control_reload_replay_correction':'passed',
            'wrong_case_access':'denied','provider':'fake','synthetic_case_retained':True}))


if __name__=='__main__':main()
