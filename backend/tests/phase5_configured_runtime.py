"""Synthetic configured DB/storage acceptance; explicitly fake AI, no model calls."""
import json
import uuid
from fastapi.testclient import TestClient
from app.main import app
from app.services import understanding,case_agent,evidence_intelligence
from app.services.ai_provider import FakeProvider
from app.schemas.evidence_intelligence import EvidenceAnalysis
from tests.test_phase3_understanding import candidate
from tests.test_phase3r_case_agent import move
from tests.phase5_fixtures import image_bytes


def main():
    text='A synthetic scammer made me send INR 35000 via UPI.'
    provider=FakeProvider(json.dumps(dict(language='en',candidates=[candidate('money_lost',True,'send'),
        candidate('amount','35000','35000'),candidate('currency','INR','INR'),candidate('authorization','authorized','me send'),
        candidate('signals',['financial'],'scammer'),candidate('payment_method','upi','UPI')])),
        next_move=json.dumps(move('ACKNOWLEDGE_AND_WAIT',None,'I have recorded your synthetic case.')))
    understanding.get_provider=case_agent.get_provider=lambda:provider
    evidence_intelligence.analyze_bytes=lambda *args:EvidenceAnalysis(readable=True,candidates=[
        dict(field='amount',value='3500',source_text='INR 3500',confidence=.95)])
    evidence_id=None
    with TestClient(app,base_url='https://testserver') as client:
        try:
            result=client.post('/api/v1/incidents',json={'conversation_first':True})
            assert result.status_code==201
            case=result.json()['id']
            path=f'/api/v1/incidents/{case}/conversation'
            state=client.get(path).json()
            payload=dict(turn_id=str(uuid.uuid4()),expected_revision=state['revision'],type='message',text=text)
            sent=client.post(path+'/turns',json=payload)
            assert sent.status_code==200
            state=sent.json()
            assert state['facts']['amount']=='35000'
            upload=client.post(f'/api/v1/incidents/{case}/evidence',data={'staged_for_chat':'true','upload_id':str(uuid.uuid4())},
                files={'file':('phase5-synthetic.png',image_bytes(),'image/png')})
            assert upload.status_code==201, f'Upload HTTP {upload.status_code}'
            evidence_id=upload.json()['id']
            linked=client.post(path+'/turns',json=dict(turn_id=str(uuid.uuid4()),expected_revision=state['revision'],type='message',attachment_ids=[evidence_id]))
            assert linked.status_code==200
            state=linked.json()
            attempt=dict(attempt_id=str(uuid.uuid4()),expected_revision=state['revision'])
            analysis=client.post(f'/api/v1/evidence/{evidence_id}/analyze',json=attempt)
            assert analysis.status_code==200
            assert analysis.json()['candidates'][0]['conflict']
            payload=dict(turn_id=str(uuid.uuid4()),expected_revision=state['revision'],type='evidence_review',evidence_review=dict(
                attempt_id=attempt['attempt_id'],decisions=[dict(candidate_id=analysis.json()['candidates'][0]['id'],decision='accept',resolve_conflict=True)]))
            reviewed=client.post(path+'/turns',json=payload)
            assert reviewed.status_code==200
            assert reviewed.json()['facts']['amount']=='3500'
            assert client.post(path+'/turns',json=payload).json()==reviewed.json()
            assert client.get(path).json()['memory']['facts']['amount']['value']=='3500'
            assert client.get(f'/api/v1/evidence/{evidence_id}/file').status_code==200
            with TestClient(app,base_url='https://testserver') as outsider:
                assert outsider.get(f'/api/v1/evidence/{evidence_id}/file').status_code==404
            assert client.delete(f'/api/v1/evidence/{evidence_id}').status_code==204
            evidence_id=None
            assert client.get(path).json()['facts']['provenance'][-1]['source_deleted']
            print(json.dumps({'configured_database_storage':'passed','upload_link_analysis_review_reload_replay_deletion':'passed',
                'unauthorized_file_access':'denied','provider':'fake','synthetic_case_retained':True}),flush=True)
        finally:
            if evidence_id:
                client.delete(f'/api/v1/evidence/{evidence_id}')


if __name__=='__main__':main()
