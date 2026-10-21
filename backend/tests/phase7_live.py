"""Explicit live synthetic Phase 7 acceptance in a disposable migrated SQLite DB."""
import json
import os
from pathlib import Path
import tempfile
import time
import uuid
from datetime import timedelta


def main():
    if os.environ.get('PHASE7_LIVE') != '1':
        raise SystemExit('Set PHASE7_LIVE=1 for explicit synthetic provider calls.')
    from app.core.config import get_settings
    configured=get_settings()
    assert configured.GEMINI_API_KEY and configured.UNDERSTANDING_ENABLED
    output=Path(__file__).resolve().parents[2]/'tmp'/'phase7-live.json'
    results=[]
    with tempfile.TemporaryDirectory(prefix='cybersos-phase7-live-',ignore_cleanup_errors=True) as directory:
        os.environ.update(DATABASE_URL='sqlite:///'+(Path(directory)/'live.sqlite').as_posix(),
            LOCAL_STORAGE_ROOT=str(Path(directory)/'evidence'),SUPABASE_URL='',SUPABASE_SERVICE_ROLE_KEY='',
            CASE_DELETION_JOURNAL=str(Path(directory)/'deletions.jsonl'),CASE_COOKIE_SECURE='true')
        get_settings.cache_clear()
        from alembic import command
        from alembic.config import Config
        command.upgrade(Config(str(Path(__file__).resolve().parents[1]/'alembic.ini')),'head')
        from fastapi.testclient import TestClient
        from app.main import app
        from app.db.session import SessionLocal,engine
        from app.models.incident import Incident
        from app.services.return_access import now
        from app.services import case_agent
        original_provider=case_agent.get_provider
        class DiagnosticProvider:
            async def decide(self, context):
                (output.parent/'phase7-decision-context.json').write_text(context,encoding='utf-8')
                try:
                    return await original_provider().decide(context)
                except Exception as exc:
                    message=str(getattr(exc,'message','')).replace(configured.GEMINI_API_KEY,'<redacted>')
                    print(json.dumps({'synthetic_provider_error':message[:1500]}),flush=True)
                    raise
        case_agent.get_provider=lambda:DiagnosticProvider()
        fixtures=[
            ('women_children', [
                'Someone on Instagram is repeatedly harassing me. They wrote "I will keep posting about you" today. Their profile is https://instagram.com/synthetic_phase7. I am safe with no immediate physical danger. I have non-explicit screenshots but prefer not to upload them.',
                'I do not know any other identifying details. I can keep the screenshots privately.',
                'What does CyberSOS help me prepare?']),
            ('financial',[
                'A scammer tricked me into sending INR 3500 from my bank account through UPI today. I approved it myself. No further money is leaving and nobody can access my phone or accounts. The UPI reference is SYNTHETIC123. I have a receipt but prefer not to upload it.',
                'The recipient UPI ID was synthetic-store@upi. I do not know their real identity.',
                'What does CyberSOS help me prepare?']),
            ('other',[
                'Someone else still has access to my Google account, synthetic@example.test. I discovered it today. No money is involved, nobody controls my device, and I am not in physical danger. I have a sign-in alert screenshot but prefer not to upload it.',
                'The alert says "New sign-in". I do not know who it was or have any more identifiers.',
                'What does CyberSOS help me prepare?'])]
        with TestClient(app,base_url='https://testserver') as client:
            for hint,messages in fixtures:
                if os.environ.get('PHASE7_HINT') and hint!=os.environ['PHASE7_HINT']:
                    continue
                ident=client.post('/api/v1/incidents',json={'conversation_first':True}).json()['id']
                path=f'/api/v1/incidents/{ident}'
                state=client.get(path+'/conversation').json()
                records=[]
                resumed_record=None
                def send(kind,**kwargs):
                    nonlocal state
                    started=time.perf_counter()
                    response=client.post(path+'/conversation/turns',json={'turn_id':str(uuid.uuid4()),'expected_revision':state['revision'],'type':kind,**kwargs})
                    assert response.status_code==200,response.text
                    state=response.json()
                    records.append({'elapsed_ms':round((time.perf_counter()-started)*1000,1),'turn':state['turns'][-1],
                        'companion':state['projection']['companion']})
                    (output.parent/'phase7-live-last-state.json').write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf-8')
                send('route_hint',route_hint=hint)
                for message in messages[:int(os.environ.get('PHASE7_TURNS','3'))]:
                    send('message',text=message)
                    time.sleep(8)
                assert state['projection']['known_facts'],hint
                assert state['projection']['companion']['presented'],f'{hint}: no autonomous fuller outcome'
                assert not state['understanding_review']['reviewed'],hint
                code=client.post(path+'/recovery-code').json()['code']
                before=client.get(path+'/conversation').json()
                with SessionLocal() as db:
                    row=db.get(Incident,uuid.UUID(ident));row.case_secret_expires_at=now()-timedelta(seconds=1);db.commit()
                assert client.get(path+'/conversation').status_code==404
                with TestClient(app,base_url='https://testserver') as returned:
                    assert returned.post('/api/v1/auth/recover',json={'case_id':ident,'code':code}).status_code==200
                    resumed=returned.get(path+'/conversation').json()
                    assert resumed['turns']==before['turns'] and resumed['facts']==before['facts'] and resumed['memory']==before['memory']
                    started=time.perf_counter()
                    response=returned.post(path+'/conversation/turns',json={'turn_id':str(uuid.uuid4()),
                        'expected_revision':resumed['revision'],'type':'message',
                        'text':'Can I continue adding information here without restarting?'})
                    assert response.status_code==200,response.text
                    updated=response.json()
                    changes=updated['turns'][-1]['fact_changes']
                    assert changes['agent']['status']=='decided',changes['agent']
                    assert changes['next_move']['type']=='ANSWER_RELEVANT_QUESTION'
                    assert updated['pending_question'] is None
                    resumed_record={'elapsed_ms':round((time.perf_counter()-started)*1000,1),
                        'response':changes['next_move'],'agent':changes['agent']}
                    assert returned.request('DELETE',path,json={'confirmation':'DELETE'}).status_code==200
                results.append({'hint':hint,'records':records,'secure_resume':'passed','resumed_conversation':resumed_record})
                output.parent.mkdir(exist_ok=True)
                output.write_text(json.dumps({'provider':configured.UNDERSTANDING_PROVIDER,'model':configured.UNDERSTANDING_MODEL,
                    'results':results},ensure_ascii=False,indent=2),encoding='utf-8')
                print(json.dumps({'hint':hint,'autonomous_companion':True,'secure_resume':'passed'}),flush=True)
        engine.dispose()


if __name__=='__main__':main()
