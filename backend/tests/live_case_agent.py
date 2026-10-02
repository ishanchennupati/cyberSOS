"""Explicit opt-in synthetic live smoke. No real case DB, no secret/error text output.

Run from backend: ../.venv/Scripts/python.exe -m tests.live_case_agent
This is intentionally not collected by pytest (which must never call a live provider).
"""
import json
import os
import tempfile
import uuid
from pathlib import Path


def main():
    from app.core.config import get_settings
    from app.services.ai_provider import get_provider
    settings = get_settings()
    print(json.dumps({'provider': settings.UNDERSTANDING_PROVIDER,
        'model': settings.UNDERSTANDING_MODEL, 'key_configured': bool(settings.GEMINI_API_KEY),
        'provider_initialized': get_provider() is not None}))
    if get_provider() is None:
        print('LIVE GEMINI FAIL: provider unavailable')
        return 1
    with tempfile.TemporaryDirectory(prefix='cybersos-live-synthetic-') as folder:
        os.environ['DATABASE_URL'] = 'sqlite:///' + (Path(folder) / 'case.sqlite').as_posix()
        os.environ['LOCAL_STORAGE_ROOT'] = str(Path(folder) / 'evidence')
        os.environ['UNDERSTANDING_RETRIES'] = str(settings.UNDERSTANDING_RETRIES)
        get_settings.cache_clear()
        from app.db.session import engine
        from alembic import command
        from alembic.config import Config
        config = Config('alembic.ini')
        with engine.begin() as connection:
            config.attributes['connection'] = connection
            command.upgrade(config, 'head')
        from app.main import app
        from fastapi.testclient import TestClient
        with TestClient(app, base_url='https://testserver') as client:
            ident = client.post('/api/v1/incidents', json={'conversation_first': True}).json()['id']
            response = client.post(f'/api/v1/incidents/{ident}/conversation/turns', json={
                'turn_id': str(uuid.uuid4()), 'expected_revision': 0, 'type': 'message',
                'text': '₹5,000 left my account without my approval.'})
            if response.status_code != 200:
                print(json.dumps({'api_status': response.status_code, 'result': 'LIVE GEMINI FAIL'}))
                engine.dispose()
                return 1
            state = response.json()
            changes = state['turns'][-1]['fact_changes']
            facts = state['facts']
            summary = {'understanding_status': changes['understanding']['status'],
                'provider_stages': {key: changes['understanding'].get(key) for key in
                    ('provider_initialized','invocation_succeeded','parsing_succeeded','error_type','http_status')},
                'understanding_failure': changes['understanding'].get('reason'),
                'candidates': [{key: c[key] for key in ('field','value','source_text','status')}
                    for c in changes['understanding']['candidates']],
                'canonical_facts': {key: facts[key] for key in ('kind','money_lost','amount','currency',
                    'authorization','occurred_at','payment_method','transaction_id','signals')},
                'agent_status': changes['agent'], 'next_move': state['next_move'],
                'fallback_question': state['pending_question'],
                'acknowledgement': changes['acknowledgement'],
                'deterministic_action_ids': [a['id'] for a in state['plan']['plan']['actions']]}
            success = (changes['understanding']['status'] == 'understood' and facts['money_lost'] is True
                and facts['amount'] == '5000' and facts['currency'] == 'INR'
                and facts['authorization'] == 'unauthorized' and state['next_move'] is not None
                and changes['agent']['status'] == 'decided')
            summary['result'] = 'LIVE GEMINI PASS' if success else 'LIVE GEMINI FAIL'
            print(json.dumps(summary, ensure_ascii=True, indent=2))
            if success:
                correction = client.post(f'/api/v1/incidents/{ident}/conversation/turns', json={
                    'turn_id': str(uuid.uuid4()), 'expected_revision': state['revision'],
                    'type': 'message', 'text': 'Sorry, the amount was \u20b94,500.'})
                corrected = correction.json()
                change = corrected.get('turns', [{}])[-1].get('fact_changes', {})
                updates = change.get('updates', [])
                success = (correction.status_code == 200
                    and corrected['facts']['amount'] == '4500'
                    and change['understanding']['status'] == 'understood'
                    and change['agent']['status'] == 'decided'
                    and any(u['field'] == 'amount' and u['before'] == '5000'
                        and u['after'] == '4500' and u['correction'] for u in updates)
                    and len(corrected['turns']) == 2
                    and corrected['turns'][0]['text'] == state['turns'][0]['text'])
                print(json.dumps({'correction_result': 'LIVE CORRECTION PASS' if success else 'LIVE CORRECTION FAIL',
                    'api_status': correction.status_code, 'amount': corrected.get('facts', {}).get('amount'),
                    'understanding': change.get('understanding', {}).get('status'),
                    'agent': change.get('agent'), 'history_preserved': len(corrected.get('turns', [])) == 2},
                    ensure_ascii=True))
        engine.dispose()
        return 0 if success else 1


if __name__ == '__main__':
    raise SystemExit(main())
