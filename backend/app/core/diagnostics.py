"""Content-free diagnostics shared by HTTP requests and the two AI stages."""
import json
import logging
import os
import sys
import traceback
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
from time import perf_counter

from starlette.responses import JSONResponse

logger = logging.getLogger('cybersos.diagnostics')
request_id_context = ContextVar('cybersos_request_id', default=None)


class SuppressRawAccess(logging.Filter):
    def filter(self, record):
        return False


def configure_logging(folder=None):
    # Cover direct CLI starts as well as run_local.py. A filter survives logging
    # reconfiguration by Alembic; our HTTP events replace raw request-target logs.
    access = logging.getLogger('uvicorn.access')
    if not any(isinstance(f, SuppressRawAccess) for f in access.filters):
        access.addFilter(SuppressRawAccess())
    logger.setLevel(logging.INFO)
    logger.disabled = False
    # Uvicorn does not normally configure the root logger. Alembic/pytest may.
    if not logging.getLogger().handlers and not any(type(h) is logging.StreamHandler for h in logger.handlers):
        console = logging.StreamHandler(sys.stderr)
        console.setFormatter(logging.Formatter('%(message)s'))
        logger.addHandler(console)
    if folder:
        # Reload workers and isolated smoke servers can run concurrently. Sharing
        # a RotatingFileHandler target causes Windows rename/locking failures.
        path = Path(folder).resolve() / f'cybersos-{os.getpid()}.jsonl'
        if not any(getattr(h, 'baseFilename', None) == str(path) for h in logger.handlers):
            path.parent.mkdir(parents=True, exist_ok=True)
            handler = RotatingFileHandler(path, maxBytes=1_000_000, backupCount=2, encoding='utf-8')
            handler.setFormatter(logging.Formatter('%(message)s'))
            logger.addHandler(handler)


def log_event(event, *, level=logging.INFO, **fields):
    # Callers supply only controlled metadata. Never pass exception messages,
    # request bodies, URLs/queries, cookies, facts, prompts or model output here.
    if logging.getLogger().handlers:
        for handler in list(logger.handlers):
            if type(handler) is logging.StreamHandler:
                logger.removeHandler(handler)
                handler.close()
    logger.log(level, json.dumps(dict(timestamp=datetime.now(timezone.utc).isoformat(),
        event=event, request_id=request_id_context.get(), **fields), ensure_ascii=True))


def exception_metadata(exc):
    frames = [{'file': Path(frame.filename).name, 'line': frame.lineno, 'function': frame.name}
              for frame in traceback.extract_tb(exc.__traceback__)[-12:]]
    # SQLAlchemy exceptions include SQL parameters in str(exc); never render them.
    return dict(error_type=type(exc).__name__, frames=frames)


def log_ai_stage(stage, diagnostic, duration_ms):
    fields = {key: diagnostic[key] for key in (
        'status', 'reason', 'category', 'provider', 'model', 'provider_initialized',
        'invocation_succeeded', 'parsing_succeeded', 'validation_succeeded',
        'http_status', 'error_type', 'proposed_type', 'rejection_reason', 'skipped') if key in diagnostic}
    # Validation locations can contain arbitrary extra-field names from model
    # output. Allow only schema field names and numeric positions.
    from app.schemas.understanding import Candidate, Understanding
    from app.schemas.next_move import NextMove
    from app.domain.facts import Identifier
    known = set(Candidate.model_fields) | set(Understanding.model_fields) | set(NextMove.model_fields) | set(Identifier.model_fields)
    fields['validation_errors'] = [{'loc': [p if (isinstance(p, int) or p in known) else '<field>'
        for p in e['loc']], 'type': e['type']} for e in diagnostic.get('validation_errors', [])[:8]]
    log_event('ai_stage', stage=stage, duration_ms=round(duration_ms, 1),
              level=logging.WARNING if diagnostic.get('status') == 'fallback' else logging.INFO, **fields)


class DiagnosticsMiddleware:
    """Catch errors before Starlette/Uvicorn can print sensitive exception text."""
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        header = dict(scope.get('headers', [])).get(b'x-request-id', b'').decode('ascii', errors='ignore')
        try:
            request_id = str(uuid.UUID(header))
        except ValueError:
            request_id = str(uuid.uuid4())
        token = request_id_context.set(request_id)
        started = perf_counter()
        status, response_started, response_complete, response_failed = 500, False, False, False

        async def respond(message):
            nonlocal status, response_started, response_complete
            if message['type'] == 'http.response.start':
                response_started = True
                status = message['status']
                message['headers'] = list(message.get('headers', [])) + [(b'x-request-id', request_id.encode())]
            await send(message)
            if message['type'] == 'http.response.body' and not message.get('more_body', False):
                response_complete = True

        try:
            await self.app(scope, receive, respond)
        except Exception as exc:
            response_failed = True
            log_event('request_error', level=logging.ERROR, category='APPLICATION_ERROR',
                      route=getattr(scope.get('route'), 'path', '<unmatched>'), **exception_metadata(exc))
            if not response_started:
                await JSONResponse(status_code=500, content={
                    'detail': 'CyberSOS could not complete this request. Please try again.',
                    'request_id': request_id}, headers={'Cache-Control': 'no-store'})(scope, receive, respond)
            elif not response_complete:
                # Abort the transport without a private exception chain. Sending
                # an empty final body can violate the original Content-Length.
                raise RuntimeError('CyberSOS response stream failed; see request diagnostics') from None
        finally:
            log_event('http_request', level=logging.WARNING if status >= 400 else logging.INFO,
                      method=scope.get('method'), route=getattr(scope.get('route'), 'path', '<unmatched>'),
                      status=status, response_failed=response_failed,
                      duration_ms=round((perf_counter() - started) * 1000, 1))
            request_id_context.reset(token)
