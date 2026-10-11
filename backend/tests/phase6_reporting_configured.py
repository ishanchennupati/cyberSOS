"""Synthetic configured-PostgreSQL reporting check; fake AI only."""
import json
import uuid
from fastapi.testclient import TestClient
from app.main import app
from app.services import understanding,case_agent,reporting_narrative
from app.services.ai_provider import FakeProvider
from tests.test_phase3_understanding import candidate
from tests.test_phase3r_case_agent import move


def main():
    class Provider(FakeProvider):
        name='fake'
        async def draft(self,packet):
            return json.dumps({'claims':[{'fact_id':f['id'],'text':f['statement']} for f in json.loads(packet)['facts']]})
    provider=Provider(json.dumps({'language':'en','candidates':[candidate('signals',['harassment'],'harassed'),
        candidate('platform','Instagram','Instagram')]}),next_move=json.dumps(move('ACKNOWLEDGE_AND_WAIT',None,'I have recorded this.')))
    understanding.get_provider=case_agent.get_provider=reporting_narrative.get_provider=lambda:provider
    with TestClient(app,base_url='https://testserver') as client:
        case=client.post('/api/v1/incidents',json={'conversation_first':True}).json()['id']
        path=f'/api/v1/incidents/{case}/conversation';report=f'/api/v1/incidents/{case}/reporting'
        state=client.get(path).json()
        response=client.post(path+'/turns',json={'turn_id':str(uuid.uuid4()),'expected_revision':state['revision'],'type':'message','text':'I was harassed on Instagram.'})
        assert response.status_code==200;state=response.json()
        state=client.post(path+'/turns',json={'turn_id':str(uuid.uuid4()),'expected_revision':state['revision'],'type':'case_review'}).json()
        payload={'draft_id':str(uuid.uuid4()),'expected_revision':state['revision']}
        draft=client.post(report+'/drafts',json=payload);assert draft.status_code==200
        assert client.post(report+'/drafts',json=payload).json()==draft.json()
        assert client.post(report+f"/drafts/{payload['draft_id']}/review",json={'expected_revision':state['revision']}).status_code==200
        assert client.get(report).json()['state']=='ready_for_handoff'
        pdf=client.get(report+f"/drafts/{payload['draft_id']}/export?format=pdf");assert pdf.status_code==200 and pdf.content.startswith(b'%PDF-')
        corrected=candidate('platform','Facebook','Facebook');corrected['correction_source']='Correction'
        provider.output=json.dumps({'language':'en','candidates':[corrected]})
        assert client.post(path+'/turns',json={'turn_id':str(uuid.uuid4()),'expected_revision':state['revision'],'type':'message','text':'Correction: this was on Facebook.'}).status_code==200
        assert client.get(report+f"/drafts/{payload['draft_id']}/export").status_code==409
        with TestClient(app,base_url='https://testserver') as outsider:assert outsider.get(report).status_code==404
        print(json.dumps({'configured_reporting':'passed','review_replay_reload_pdf_correction':'passed','ownership':'denied_without_cookie',
            'provider':'fake','synthetic_case_retained':True}))


if __name__=='__main__':main()
