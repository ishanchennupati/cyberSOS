"""Synthetic configured PostgreSQL round trip; providers/email are explicitly fake."""
import json
import uuid
from datetime import timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.models.incident import Incident
from app.models.return_access import AccountSession
from app.services import understanding, case_agent, reporting_narrative, return_access
from app.services.ai_provider import FakeProvider
from sqlalchemy import delete
from tests.test_phase3_understanding import candidate
from tests.test_phase3r_case_agent import move


def main():
    class Provider(FakeProvider):
        async def draft(self, packet):
            return json.dumps({'claims':[{'fact_id':f['id'],'text':f['statement']} for f in json.loads(packet)['facts']]})
    provider=Provider(json.dumps({'language':'en','candidates':[candidate('signals',['harassment'],'harassed'),candidate('platform','Instagram','Instagram')]}),
        next_move=json.dumps(move('ACKNOWLEDGE_AND_WAIT',None,'Your details are saved.',companion_ready=True)))
    understanding.get_provider=case_agent.get_provider=reporting_narrative.get_provider=lambda:provider
    messages=[]
    return_access.send_sign_in=lambda email,token:messages.append(token)
    with TestClient(app,base_url='https://testserver') as client:
        response=client.post('/api/v1/incidents',json={'conversation_first':True})
        assert response.status_code==201,response.text
        ident=response.json()['id'];path=f'/api/v1/incidents/{ident}'
        try:
            state=client.get(path+'/conversation').json()
            def turn(kind,**kwargs):
                nonlocal state
                response=client.post(path+'/conversation/turns',json={'turn_id':str(uuid.uuid4()),'expected_revision':state['revision'],'type':kind,**kwargs})
                assert response.status_code==200,response.text
                state=response.json();return state
            turn('message',text='I was harassed on Instagram.')
            assert state['projection']['companion']['presented'] and not state['understanding_review']['reviewed']
            turn('case_review')
            draft=client.post(path+'/reporting/drafts',json={'draft_id':str(uuid.uuid4()),'expected_revision':state['revision']})
            assert draft.status_code==200,draft.text
            draft_id=draft.json()['id']
            assert client.post(path+f'/reporting/drafts/{draft_id}/review',json={'expected_revision':state['revision']}).status_code==200
            before=client.get(path+'/conversation').json()
            code=client.post(path+'/recovery-code').json()['code']
            assert client.post('/api/v1/auth/email',json={'email':f'synthetic-{uuid.uuid4().hex}@example.test'}).status_code==202
            assert client.post('/api/v1/auth/confirm',json={'token':messages[-1]}).status_code==200
            assert client.post(path+'/save').status_code==200
            assert any(row['id']==ident for row in client.get('/api/v1/auth/cases').json()['cases'])
            with SessionLocal() as db:
                row=db.get(Incident,uuid.UUID(ident));row.case_secret_expires_at=return_access.now()-timedelta(seconds=1)
                # Only revoke the synthetic session created by this script.
                db.execute(delete(AccountSession).where(AccountSession.secret_hash==return_access.digest(client.cookies.get('cybersos_account'))))
                db.commit()
            assert client.get(path+'/conversation').status_code==404
            with TestClient(app,base_url='https://testserver') as resumed:
                recovered=resumed.post('/api/v1/auth/recover',json={'case_id':ident,'code':code})
                assert recovered.status_code==200,recovered.text
                after=resumed.get(path+'/conversation').json()
                assert after['facts']==before['facts'] and after['turns']==before['turns'] and after['memory']==before['memory']
                pdf=resumed.get(path+f'/reporting/drafts/{draft_id}/export?format=pdf')
                assert pdf.status_code==200 and pdf.content.startswith(b'%PDF-')
                state=after
                provider.output=json.dumps({'language':'en','candidates':[]})
                updated=resumed.post(path+'/conversation/turns',json={'turn_id':str(uuid.uuid4()),'expected_revision':state['revision'],'type':'case_update','case_update':{'kind':'reference','text':'SYNTHETIC-PG-123'}})
                assert updated.status_code==200,updated.text
                removed=resumed.request('DELETE',path,json={'confirmation':'DELETE'})
                assert removed.status_code==200,removed.text
                assert resumed.get(path+'/conversation').status_code==404
                assert resumed.get(path+f'/reporting/drafts/{draft_id}/export').status_code==404
            print(json.dumps({'configured_postgresql':'passed','providers':'fake','email':'captured_test_adapter',
                'readiness_review_packet_return_memory_update_delete':'passed','synthetic_case_deleted':True}))
        finally:
            with SessionLocal() as db:
                row=db.get(Incident,uuid.UUID(ident))
                if row:
                    from app.services.lifecycle import request_deletion
                    request_deletion(db,row)


if __name__=='__main__':main()
