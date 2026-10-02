"""Opt-in live confirmation after a synthetic uncertain-rail seed, private SQLite."""
import json
import os
import tempfile
import uuid
from pathlib import Path
from unittest.mock import patch


def main():
    from app.core.config import get_settings
    from app.services.ai_provider import FakeProvider, get_provider
    if get_provider() is None:
        print('LIVE PAYMENT CONFIRMATION unavailable')
        return 1
    with tempfile.TemporaryDirectory(prefix='cybersos-payment-live-') as folder:
        os.environ['DATABASE_URL'] = 'sqlite:///' + (Path(folder) / 'case.sqlite').as_posix()
        os.environ['LOCAL_STORAGE_ROOT'] = str(Path(folder) / 'evidence')
        get_settings.cache_clear()
        from app.db.session import engine
        from alembic import command
        from alembic.config import Config
        with engine.begin() as connection:
            config = Config('alembic.ini')
            config.attributes['connection'] = connection
            command.upgrade(config, 'head')
        from app.main import app
        from fastapi.testclient import TestClient
        from app.services import understanding, case_agent
        from tests.test_phase3_understanding import candidate
        from tests.test_phase3r_case_agent import move
        rail = candidate('payment_method', 'net banking', 'net banking')
        rail.update(extraction='inference', uncertainty='Citizen unsure')
        fixture = FakeProvider(json.dumps({'language': 'en', 'candidates': [
            candidate('money_lost', True, 'sent'), candidate('amount', '5000', '₹5,000'), rail]}),
            next_move=json.dumps(move('VERIFY_INFORMATION', 'payment_method', 'Was it net banking?',
                quick_replies=['Yes', 'No', 'Not sure'])))
        try:
            with TestClient(app, base_url='https://testserver') as client:
                ident = client.post('/api/v1/incidents', json={'conversation_first': True}).json()['id']
                endpoint = f'/api/v1/incidents/{ident}/conversation/turns'
                def send(text, revision):
                    response = client.post(endpoint, json={'turn_id': str(uuid.uuid4()),
                        'expected_revision': revision, 'type': 'message', 'text': text})
                    assert response.status_code == 200
                    return response.json()
                with patch.object(understanding, 'get_provider', return_value=fixture), patch.object(case_agent, 'get_provider', return_value=fixture):
                    state = send('I sent ₹5,000. I think it was net banking.', 0)
                assert state['next_move']['type'] == 'VERIFY_INFORMATION'
                stages = []
                for text in ('That is right, that was how I paid.', 'No more money has left since then.',
                             'Sorry, the amount was ₹4,500.'):
                    state = send(text, state['revision'])
                    changes = state['turns'][-1]['fact_changes']
                    stages.append({'revision': state['revision'], 'extraction': changes['understanding']['status'],
                        'agent': changes['agent'], 'payment_method': state['facts']['payment_method'],
                        'review_resolved': not any(c['field'] == 'payment_method' for c in changes['unresolved_candidates']),
                        'next_field': (state['next_move'] or {}).get('related_field')})
                provenance = next(p for p in state['facts']['provenance'] if p['field'] == 'payment_method')
                passed = all(r['extraction'] == 'understood' and r['agent']['status'] == 'decided'
                    and r['payment_method'] == 'net_banking' and r['review_resolved']
                    and r['next_field'] != 'payment_method' for r in stages)
                passed &= provenance['origin'] == 'user_verification' and provenance['verified']
                passed &= state['facts']['amount'] == '4500' and len(state['turns']) == 4
                print(json.dumps({'seed': 'synthetic double; subsequent extraction and reasoning are live Gemini',
                    'turns': stages, 'verified_confirmation': provenance['verified'],
                    'result': 'LIVE PAYMENT CONFIRMATION PASS' if passed else 'LIVE PAYMENT CONFIRMATION FAIL'}))
                return 0 if passed else 1
        finally:
            engine.dispose()


if __name__ == '__main__':
    raise SystemExit(main())
