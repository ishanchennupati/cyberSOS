"""Test-only synthetic browser provider/extraction. Never loaded in deployment."""
import asyncio
import json
from app.main import app
from app.services import understanding, case_agent, evidence_intelligence
from app.services.ai_provider import FakeProvider
from app.schemas.evidence_intelligence import EvidenceAnalysis
from tests.test_phase3_understanding import candidate
from tests.test_phase3r_case_agent import move


class BrowserProvider(FakeProvider):
    async def extract(self, message, context):
        await asyncio.sleep(.3)
        fixtures = {
            'I lost 5000': [candidate('amount','5000','5000'),candidate('money_lost',True,'lost')],
            'A scammer made me send INR 35000 via UPI today.': [candidate('amount','35000','35000'),
                candidate('money_lost',True,'send'),candidate('currency','INR','INR'),
                candidate('payment_method','upi','UPI'),candidate('authorization','authorized','me send'),
                candidate('signals',['financial'],'scammer')],
            'Someone on Instagram is threatening to share my private photos.': [
                candidate('signals',['threats','harassment'],'threatening'), candidate('platform','Instagram','Instagram'),
                candidate('private_image_threat',True,'threatening to share my private photos')],
            'Someone still has access to my Google account.': [candidate('signals',['account_takeover'],'access to my Google account'),
                candidate('platform','Google','Google'),candidate('account_compromised',True,'Someone still has access to my Google account')],
        }
        data = dict(language='en', candidates=fixtures.get(message, []))
        active = json.loads(context).get('evidence_review')
        if message == 'All details in this attachment are correct.' and active:
            data['evidence_review'] = dict(attempt_id=active['id'], source_text=message, reference_text='attachment',
                decisions=[dict(candidate_id=c['id'],decision='accept',resolve_conflict=c['conflict'] or c['changed_since_analysis'])
                    for c in active['candidates'] if not c['reviewed']])
        return json.dumps(data)

    async def decide(self, encoded):
        context = json.loads(encoded)
        if context['current_message'] == 'I lost 5000':
            return json.dumps(move('CONTINUE_OPEN_CONVERSATION','story','What happened to the money?',
                quick_replies=['It was an online payment','It was an unexplained debit','Not sure']))
        return json.dumps(move('ACKNOWLEDGE_AND_WAIT',None,'I have recorded what you told me. You can add or correct details whenever you want.'))


provider = BrowserProvider()
understanding.get_provider = lambda: provider
case_agent.get_provider = lambda: provider


def analyze_bytes(data, mime):
    import time
    time.sleep(2)
    return EvidenceAnalysis(readable=True,candidates=[dict(field='amount',value='3500',source_text='INR 3,500',confidence=.95),
        dict(field='currency',value='INR',source_text='INR 3,500',confidence=.95),
        dict(field='identifiers',value='sample-store@upi',source_text='sample-store@upi',confidence=.9,identifier_type='upi')])


evidence_intelligence.analyze_bytes = analyze_bytes
