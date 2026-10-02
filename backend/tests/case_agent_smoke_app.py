"""Test-only ASGI entry point for real-browser/API tests with scripted AI replies."""
import json
from app.main import app
from app.services import understanding, case_agent
from app.services.ai_provider import FakeProvider
from tests.test_phase3_understanding import candidate
from tests.test_phase3r_case_agent import move


class BrowserProvider(FakeProvider):
    async def extract(self, message, context):
        fixtures = {
            '₹5,000 left my account without my approval.': [
                candidate('money_lost', True, 'left my account'), candidate('amount', '5000', '₹5,000'),
                candidate('currency', 'INR', '₹'), candidate('authorization', 'unauthorized', 'without my approval')],
            'It happened about an hour ago.': [candidate('time_window', 'about an hour ago', 'about an hour ago')],
            'Sorry, it was ₹4,500.': [dict(candidate('amount', '4500', '₹4,500'), correction_source='Sorry')],
            'I also installed AnyDesk.': [candidate('signals', ['device_compromise'], 'installed AnyDesk')],
            'I have an SMS screenshot.': [candidate('evidence_mentioned', ['SMS screenshot'], 'SMS screenshot')],
            '₹5,000 is gone from my account. I just got a message.': [
                candidate('money_lost', True, 'gone from my account'), candidate('amount', '5000', '₹5,000'),
                candidate('currency', 'INR', '₹'), candidate('evidence_mentioned', ['message'], 'message')],
            '5000 gone': [candidate('money_lost', True, 'gone'), candidate('amount', '5000', '5000')],
        }
        return json.dumps({'language': 'en', 'candidates': fixtures.get(message, [])})

    async def decide(self, encoded):
        context = json.loads(encoded)
        if context['current_message'] == '5000 gone':
            decision = move(field='authorization', message='Did you approve this payment yourself, or did it move without your approval?',
                quick_replies=['I approved it after deception', 'I did not approve it', 'Not sure'])
        elif context['current_message'] in {'I have an SMS screenshot.', '₹5,000 is gone from my account. I just got a message.'}:
            decision = move('REQUEST_EVIDENCE', 'evidence_available', 'Could you share the message?', evidence_kind='transaction_message')
        elif context['current_message'] == 'I also installed AnyDesk.':
            decision = move(field='remote_access', message='Does someone still have access to your device?', quick_replies=['Not sure'])
        elif context['facts']['time_window'] is None:
            decision = move(field='payment_method', message='Was the ₹5,000 debit shown as UPI, card, or something else?') if context['facts']['amount'] == '5000' else move()
        else:
            decision = move('ACKNOWLEDGE_AND_WAIT', None, 'Ready when you are.')
        return json.dumps(decision)


provider = BrowserProvider()
understanding.get_provider = lambda: provider
case_agent.get_provider = lambda: provider
