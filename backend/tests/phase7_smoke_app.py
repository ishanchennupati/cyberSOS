"""Disposable Phase 7 browser harness ONLY; never mount these routes in app.main."""
import json
import os
from datetime import timedelta
from fastapi import Depends
from sqlalchemy import delete
from app.core.config import get_settings
from app.db.session import get_db
from app.services import return_access
from app.models.return_access import AccountSession, AuthThrottle
from app.services.case_access import authorize_case_resource
from tests.phase5_smoke_app import app, BrowserProvider
from tests.test_phase3r_case_agent import move
from app.services import understanding, case_agent

os.environ.update(EMAIL_PROVIDER='resend', RESEND_API_KEY='synthetic-test-only')
get_settings.cache_clear()
mail = []
return_access.send_sign_in = lambda email, token: mail.append({'email':email,'token':token})


class CompanionProvider(BrowserProvider):
    async def decide(self, encoded):
        context = json.loads(encoded)
        if context['current_message'] == 'I have no more useful details.':
            return json.dumps(move('ACKNOWLEDGE_AND_WAIT',None,'Your current details are recorded. You can add or correct information whenever you want.',companion_ready=True))
        if not context['case_state']['companion']['presented']:
            return json.dumps(move('REQUEST_EVIDENCE','evidence_available','Would you like to share a safe supporting screenshot?',evidence_kind='non_explicit_conversation'))
        return json.dumps(move('ACKNOWLEDGE_AND_WAIT',None,'Your update is saved.'))


provider=CompanionProvider()
understanding.get_provider=lambda:provider
case_agent.get_provider=lambda:provider


@app.get('/__phase7/mail')
def test_mail():
    return mail[-1] if mail else {}


@app.post('/api/v1/__phase7/{incident_id}/expire',dependencies=[Depends(authorize_case_resource)])
def test_expire(incident_id:str,db=Depends(get_db)):
    import uuid
    from app.models.incident import Incident
    row=db.get(Incident,uuid.UUID(incident_id))
    row.case_secret_expires_at=return_access.now()-timedelta(seconds=1)
    db.execute(delete(AccountSession))
    db.commit()
    return {'expired':True}


@app.post('/api/v1/__phase7/{incident_id}/age-verification',dependencies=[Depends(authorize_case_resource)])
def test_age_verification(incident_id:str,db=Depends(get_db)):
    from sqlalchemy import select
    for row in db.scalars(select(AccountSession)):
        row.verified_at=return_access.now()-timedelta(minutes=16)
    # This harness captures mail locally; allow the immediate test reverify.
    db.execute(delete(AuthThrottle))
    db.commit()
    return {'aged':True}
