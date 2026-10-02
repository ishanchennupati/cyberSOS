"""Opt-in real Gemini follow-ups after a deterministic synthetic Not-sure fixture.

Run from backend: ../.venv/Scripts/python.exe -m tests.live_declined_followup
Extraction is a double to reproduce the exact stale-candidate condition reliably.
Only the two follow-up decisions use the live provider; no hosted case is modified.
"""
import json
import os
import tempfile
import uuid
from pathlib import Path
from unittest.mock import patch


def main():
    from app.core.config import get_settings
    from app.services.ai_provider import FakeProvider, get_provider
    live_provider = get_provider()
    if live_provider is None:
        print('LIVE FOLLOW-UP unavailable: provider not configured')
        return 1
    with tempfile.TemporaryDirectory(prefix='cybersos-declined-live-') as folder:
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
        provider = FakeProvider(json.dumps({'language': 'en', 'candidates': [candidate('money_lost', True, 'gone')]}),
            next_move=json.dumps(move(field='ongoing_loss', message='Is money still moving?')))
        results = []
        try:
            with TestClient(app, base_url='https://testserver') as client, \
                    patch.object(understanding, 'get_provider', return_value=provider):
                ident = client.post('/api/v1/incidents', json={'conversation_first': True}).json()['id']
                endpoint = f'/api/v1/incidents/{ident}/conversation/turns'
                def send(text, revision):
                    response = client.post(endpoint, json={'turn_id': str(uuid.uuid4()),
                        'expected_revision': revision, 'type': 'message', 'text': text})
                    if response.status_code != 200:
                        raise RuntimeError('synthetic turn failed')
                    return response.json()
                with patch.object(case_agent, 'get_provider', return_value=provider):
                    state = send('Money gone.', 0)
                uncertain = candidate('ongoing_loss', False, 'Not sure')
                uncertain.update(extraction='inference', uncertainty='Ongoing loss is unknown')
                provider.output = json.dumps({'language': 'en', 'candidates': [uncertain]})
                with patch.object(case_agent, 'get_provider', return_value=live_provider):
                    for text in ('Not sure', 'I need a moment.'):
                        state = send(text, state['revision'])
                        changes = state['turns'][-1]['fact_changes']
                        proposed = state.get('next_move') or {}
                        results.append({'revision': state['revision'],
                            'agent_status': changes['agent']['status'],
                            'category': changes['agent'].get('category'),
                            'rejection_reason': changes['agent'].get('rejection_reason'),
                            'next_move': proposed.get('type'), 'related_field': proposed.get('related_field'),
                            'declined_candidate_removed': not any(c['field'] == 'ongoing_loss'
                                for c in changes['unresolved_candidates']),
                            'unknown_preserved': state['facts']['ongoing_loss'] is None})
                        provider.output = json.dumps({'language': 'en', 'candidates': []})
                passed = all(r['agent_status'] == 'decided' and r['related_field'] != 'ongoing_loss'
                    and r['declined_candidate_removed'] and r['unknown_preserved'] for r in results)
                print(json.dumps({'live_follow_ups': results, 'extraction': 'synthetic double',
                    'result': 'LIVE FOLLOW-UP PASS' if passed else 'LIVE FOLLOW-UP FAIL'}))
                return 0 if passed else 1
        finally:
            engine.dispose()


if __name__ == '__main__':
    raise SystemExit(main())
