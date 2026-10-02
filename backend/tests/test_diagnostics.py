"""Diagnostics must locate failures without retaining case content or credentials."""
import json
import logging
import os
import uuid

from google.genai.errors import ServerError
from tests.test_phase3r_case_agent import install, move, send
from tests.test_phase3_understanding import candidate


def events(caplog):
    return [json.loads(record.message) for record in caplog.records
            if record.name == 'cybersos.diagnostics']


def test_request_id_and_safe_route_are_correlated(client, caplog):
    caplog.set_level(logging.INFO, logger='cybersos.diagnostics')
    request_id = str(uuid.uuid4())
    response = client.get('/api/v1/incidents/' + str(uuid.uuid4()) + '?private=synthetic-secret',
                          headers={'X-Request-ID': request_id})
    assert response.status_code == 404
    assert response.headers['X-Request-ID'] == request_id
    event = events(caplog)[-1]
    assert event['request_id'] == request_id
    assert event['route'] == '/api/v1/incidents/{incident_id}'
    assert event['status'] == 404
    assert 'synthetic-secret' not in caplog.text


def test_program_error_is_logged_without_exception_text(client, monkeypatch, caplog):
    from app.services import incident_service
    caplog.set_level(logging.INFO, logger='cybersos.diagnostics')
    def broken(*args):
        raise RuntimeError('synthetic-secret SQL parameters private conversation')
    monkeypatch.setattr(incident_service, 'create_incident', broken)
    response = client.post('/api/v1/incidents', json={'conversation_first': True})
    assert response.status_code == 500
    assert response.json()['request_id'] == response.headers['X-Request-ID']
    event = next(e for e in events(caplog) if e['event'] == 'request_error')
    assert event['category'] == 'APPLICATION_ERROR'
    assert event['error_type'] == 'RuntimeError'
    assert event['frames'][-1]['function'] == 'broken'
    assert 'synthetic-secret' not in caplog.text + response.text


def test_ai_stages_have_status_and_private_request_correlation(client, monkeypatch, caplog):
    caplog.set_level(logging.INFO, logger='cybersos.diagnostics')
    provider = install(monkeypatch, [candidate('money_lost', True, 'gone')], move())
    async def unavailable(context):
        raise ServerError(503, {'error': {'message': 'synthetic-secret provider payload'}})
    monkeypatch.setattr(provider, 'decide', unavailable)
    state, _, _ = send(client, 'Synthetic private story: money gone')
    stages = [e for e in events(caplog) if e['event'] == 'ai_stage']
    assert [e['stage'] for e in stages] == ['extraction', 'follow_up']
    assert stages[0]['status'] == 'understood'
    assert stages[1]['http_status'] == 503
    assert stages[1]['category'] == 'PROVIDER_5XX'
    assert stages[0]['request_id'] == stages[1]['request_id']
    assert all(e['duration_ms'] >= 0 for e in stages)
    assert 'synthetic-secret' not in caplog.text
    assert 'Synthetic private story' not in caplog.text
    assert state['facts']['money_lost'] is True


def test_quota_has_a_distinct_category():
    from app.services.case_agent import failure_category
    assert failure_category(ServerError(429, {'error': {'message': 'private'}})) == 'PROVIDER_QUOTA'


def test_both_ai_stages_retry_transient_errors_but_not_quota_or_authentication():
    import asyncio
    from types import SimpleNamespace
    from app.services.understanding import _extract
    from app.services.case_agent import _decide
    settings = SimpleNamespace(UNDERSTANDING_RETRIES=1, UNDERSTANDING_TIMEOUT_SECONDS=2)
    for status in (503, 429, 401, 404):
        for stage in ('extract', 'decide'):
            class Provider:
                calls = 0
                async def invoke(self, *args):
                    self.calls += 1
                    if self.calls == 1:
                        raise ServerError(status, {'error': {'message': 'synthetic-private'}})
                    return 'synthetic-result'
                extract = decide = invoke
            provider = Provider()
            async def run():
                return await (_extract(provider, 'synthetic', '{}', settings) if stage == 'extract'
                              else _decide(provider, '{}', settings))
            if status == 503:
                assert asyncio.run(run()) == 'synthetic-result'
                assert provider.calls == 2
            else:
                import pytest
                with pytest.raises(ServerError):
                    asyncio.run(run())
                assert provider.calls == 1


def test_request_id_cannot_inject_secrets(client, caplog):
    caplog.set_level(logging.INFO, logger='cybersos.diagnostics')
    response = client.get('/health', headers={'X-Request-ID': 'synthetic-secret'})
    uuid.UUID(response.headers['X-Request-ID'])
    assert 'synthetic-secret' not in caplog.text


def test_raw_server_access_logs_are_disabled():
    record = logging.LogRecord('uvicorn.access', logging.INFO, '', 0,
                               'synthetic-private-path?secret=private', (), None)
    assert not logging.getLogger('uvicorn.access').filter(record)


def test_file_log_is_bounded_and_safe(tmp_path):
    from app.core.diagnostics import configure_logging, log_event, logger
    folder = tmp_path / 'logs'
    configure_logging(folder)
    try:
        log_event('runtime_configuration', provider='disabled', model='synthetic-model', key_configured=False)
        path = folder / f'cybersos-{os.getpid()}.jsonl'
        record = json.loads(path.read_text().splitlines()[-1])
        assert record['event'] == 'runtime_configuration'
        handlers = [h for h in logger.handlers if getattr(h, 'baseFilename', None) == str(path)]
        assert handlers[0].maxBytes == 1_000_000 and handlers[0].backupCount == 2
    finally:
        for handler in list(logger.handlers):
            if getattr(handler, 'baseFilename', None) == str(path):
                logger.removeHandler(handler)
                handler.close()


def test_partial_response_aborts_without_private_exception_chain():
    import asyncio
    import traceback
    import pytest
    from app.core.diagnostics import DiagnosticsMiddleware
    async def broken(scope, receive, send):
        await send({'type': 'http.response.start', 'status': 200, 'headers': [(b'content-length', b'10')]})
        raise RuntimeError('synthetic-private-SQL-parameters')
    async def respond(message):
        if message['type'] == 'http.response.body':
            raise RuntimeError('fixed-length mismatch')
    with pytest.raises(RuntimeError) as raised:
        asyncio.run(DiagnosticsMiddleware(broken)({'type': 'http', 'method': 'GET'}, None, respond))
    formatted = ''.join(traceback.format_exception(raised.value))
    assert 'synthetic-private-SQL-parameters' not in formatted
    assert 'response stream failed' in str(raised.value)


def test_error_after_completed_response_never_sends_another_body():
    import asyncio
    from app.core.diagnostics import DiagnosticsMiddleware
    messages = []
    async def broken(scope, receive, send):
        await send({'type': 'http.response.start', 'status': 200, 'headers': []})
        await send({'type': 'http.response.body', 'body': b'ok', 'more_body': False})
        raise RuntimeError('synthetic-private-background-error')
    async def respond(message):
        messages.append(message)
    asyncio.run(DiagnosticsMiddleware(broken)({'type': 'http', 'method': 'GET'}, None, respond))
    assert len(messages) == 2
