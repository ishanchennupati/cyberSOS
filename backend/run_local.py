"""Explicit synthetic local runtime; never migrate the configured remote database.

From the repository root: .venv/Scripts/python.exe backend/run_local.py
"""
import os
import sqlite3
import socket
from datetime import datetime, timezone
from pathlib import Path


def main():
    backend = Path(__file__).resolve().parent
    # Fail before changing anything if another backend already owns this port.
    with socket.socket() as check:
        check.bind(('127.0.0.1', 8000))
    os.chdir(backend)
    database = backend / 'local.sqlite'
    os.environ['DATABASE_URL'] = 'sqlite:///' + database.as_posix()
    os.environ['LOCAL_STORAGE_ROOT'] = str(backend / 'evidence')
    os.environ['CASE_COOKIE_SECURE'] = 'false'
    os.environ['SUPABASE_URL'] = ''
    os.environ['SUPABASE_SERVICE_ROLE_KEY'] = ''
    # Snapshot the existing local case store before tracked migrations.
    if database.exists():
        backups = backend / 'tmp'
        backups.mkdir(exist_ok=True)
        destination = backups / ('local-before-migration-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f') + '.sqlite')
        with sqlite3.connect(database) as source, sqlite3.connect(destination) as target:
            source.backup(target)
    from alembic import command
    from alembic.config import Config
    command.upgrade(Config(str(backend / 'alembic.ini')), 'head')
    from app.core.config import get_settings
    settings = get_settings()
    print(f'Local runtime: SQLite {database}; dotenv: backend/.env; provider: '
          f'{settings.UNDERSTANDING_PROVIDER}; model: {settings.UNDERSTANDING_MODEL}; '
          f'AI enabled: {settings.UNDERSTANDING_ENABLED}; key configured: {bool(settings.GEMINI_API_KEY)}', flush=True)
    import uvicorn
    uvicorn.run('app.main:app', host='127.0.0.1', port=8000, reload=True, access_log=False)


if __name__ == '__main__':
    main()
