import uuid


def start(client):
    incident = client.post('/api/v1/incidents', json={'incident_type': 'financial_fraud', 'payment_method': 'unknown'}).json()
    path = f"/api/v1/incidents/{incident['id']}/conversation"
    response = client.get(path)
    assert response.status_code == 200
    return path, response.json()


def send(client, path, state, field=None, value=None, kind='answer', **extra):
    payload = dict(turn_id=str(uuid.uuid4()), expected_revision=state['revision'], type=kind,
                   field=None if kind in {'completion', 'shortcut'} else field or state['pending_question']['field'], value=value, **extra)
    return client.post(path + '/turns', json=payload), payload


def test_progress_unknown_correction_early_actions_resume(client):
    path, state = start(client)
    assert state['pending_question']['field'] == 'authorization'
    assert 'call_1930' in [a['id'] for a in state['plan']['plan']['actions']]
    response, _ = send(client, path, state, value='authorized')
    state = response.json()
    assert state['pending_question']['field'] == 'ongoing_loss'
    response, _ = send(client, path, state, value=None)
    state = response.json()
    assert state['facts']['ongoing_loss'] is None
    assert state['pending_question']['field'] == 'remote_access'
    response, _ = send(client, path, state, field='authorization', value='unauthorized', kind='correction')
    state = response.json()
    assert state['turns'][-1]['fact_changes']['before'] == 'authorized'
    assert 'contact_bank_unauthorized' in [a['id'] for a in state['plan']['plan']['actions']]
    assert state['pending_question']['field'] == 'remote_access'
    assert client.get(path).json() == state


def test_duplicate_stale_conflict_and_authority(client):
    path, initial = start(client)
    response, payload = send(client, path, initial, value='authorized')
    state = response.json()
    assert client.post(path + '/turns', json=payload).json() == state
    assert len(state['turns']) == 1
    payload['value'] = 'unauthorized'
    assert client.post(path + '/turns', json=payload).status_code == 409
    assert send(client, path, initial, value='unauthorized')[0].status_code == 409
    assert send(client, path, state, field='authorization', value='unauthorized')[0].status_code == 409
    client.cookies.clear()
    assert client.get(path).status_code == 404
    assert client.post(path + '/turns', json=payload).status_code == 404


def test_completion_retry_and_correction_preserve_completion(client):
    path, state = start(client)
    response, payload = send(client, path, state, field=None, kind='completion', value=True, action_id='call_1930')
    assert response.status_code == 200
    state = response.json()
    assert len(state['completions']) == 1
    assert client.post(path + '/turns', json=payload).json() == state
    state = send(client, path, state, value='authorized')[0].json()
    assert state['completions'][0]['completed'] is True


def test_failed_save_rolls_back_and_same_request_retries(client, monkeypatch):
    from app.services import response_service
    path, state = start(client)
    original = response_service.record_plan
    def fail(*args, **kwargs):
        raise ValueError('Synthetic save failure')
    monkeypatch.setattr(response_service, 'record_plan', fail)
    response, payload = send(client, path, state, value='authorized')
    assert response.status_code == 422
    assert client.get(path).json() == state
    monkeypatch.setattr(response_service, 'record_plan', original)
    assert client.post(path + '/turns', json=payload).status_code == 200


def test_all_questions_once_and_strict_validation(client):
    path, state = start(client)
    seen = []
    while state['pending_question']:
        field = state['pending_question']['field']
        assert field not in seen
        seen.append(field)
        state = send(client, path, state, value=None)[0].json()
    assert len(seen) == 11
    assert state['facts']['authorization'] == 'unknown'
    assert send(client, path, state, field='remote_access', value='yes', kind='correction')[0].status_code == 422


def test_concurrent_replies_only_one_mutates(client):
    from concurrent.futures import ThreadPoolExecutor
    path, state = start(client)
    payloads = [dict(turn_id=str(uuid.uuid4()), expected_revision=0, type='answer', field='authorization', value=value)
                for value in ['authorized', 'unauthorized']]
    with ThreadPoolExecutor(2) as pool:
        results = list(pool.map(lambda p: client.post(path + '/turns', json=p).status_code, payloads))
    assert sorted(results) == [200, 409]
    saved = client.get(path).json()
    assert saved['revision'] == 1 and len(saved['turns']) == 1


def test_supported_prior_schema_upgrade(tmp_path, monkeypatch):
    from tests.test_migrations import upgrade
    from sqlalchemy import create_engine, inspect
    database = tmp_path / 'phase1.sqlite'
    upgrade(database, tmp_path / 'files', monkeypatch, revision='20261001_response_foundation')
    upgrade(database, tmp_path / 'files', monkeypatch)
    engine = create_engine('sqlite:///' + database.as_posix())
    with engine.connect() as connection:
        assert {'conversation_states', 'conversation_turns'} <= set(inspect(connection).get_table_names())
    engine.dispose()


def test_shortcut_is_durable_and_legacy_facts_cannot_bypass_version(client):
    path, state = start(client)
    response, payload = send(client, path, state, value='money_gone', kind='shortcut')
    state = response.json()
    assert state['turns'][0]['type'] == 'shortcut'
    assert state['pending_question']['field'] == 'authorization'
    assert client.post(path + '/turns', json=payload).json() == state
    assert client.put(path.removesuffix('/conversation') + '/facts', json=state['facts']).status_code == 409


def test_known_facts_are_suppressed_and_unsupported_inputs_rejected(client):
    ident = client.post('/api/v1/incidents', json={'incident_type': 'financial_fraud', 'payment_method': 'upi', 'amount': '2500'}).json()['id']
    path = f'/api/v1/incidents/{ident}/conversation'
    state = client.get(path).json()
    while state['pending_question']:
        assert state['pending_question']['field'] not in {'payment_method', 'amount'}
        state = send(client, path, state, value=None)[0].json()
    from decimal import Decimal
    assert Decimal(state['facts']['amount']) == Decimal('2500')
    ident = client.post('/api/v1/incidents', json={'incident_type': 'women_children'}).json()['id']
    assert client.get(f'/api/v1/incidents/{ident}/conversation').status_code == 409
    assert send(client, path, state, field='transaction_id', value='password: synthetic', kind='correction')[0].status_code == 422
    assert 'synthetic' not in client.get(path).text


def test_conversation_frontend_backend_contract(client):
    import re
    from pathlib import Path
    from app.domain.facts import FactField
    from app.main import app
    source = (Path(__file__).parents[2] / 'frontend/types/conversation.ts').read_text()
    fields = re.search(r'export type FactField = (.*?);', source).group(1)
    assert set(re.findall(r"'([^']+)'", fields)) == {f.value for f in FactField}
    schema = app.openapi()['components']['schemas']
    assert schema['TurnRequest']['properties']['type']['enum'] == ['shortcut', 'answer', 'correction', 'completion', 'message']
    _, state = start(client)
    assert set(state) == {'incident_id', 'revision', 'version', 'answered', 'facts', 'pending_question', 'next_move', 'turns', 'plan', 'completions', 'memory', 'projection'}
    assert state['plan']['plan']['facts'] == state['facts']
