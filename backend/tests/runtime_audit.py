"""Read-only runtime audit. Never print credentials or citizen data."""
import json
import os
from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url
from app.core.config import get_settings


def main():
    settings = get_settings()
    url = make_url(settings.DATABASE_URL)
    print(json.dumps({
        'backend_directory': str(Path(__file__).resolve().parents[1]),
        'dotenv': str(settings.model_config['env_file']),
        'database_environment_override': 'DATABASE_URL' in os.environ,
        'database_url_redacted': f'{url.drivername}://<credentials>@{url.host}:{url.port}/{url.database}'
            if url.host else str(url),
        'provider': settings.UNDERSTANDING_PROVIDER,
        'model': settings.UNDERSTANDING_MODEL,
        'enabled': settings.UNDERSTANDING_ENABLED,
        'key_configured': bool(settings.GEMINI_API_KEY),
        'timeout_seconds': settings.UNDERSTANDING_TIMEOUT_SECONDS,
        'retries': settings.UNDERSTANDING_RETRIES,
    }))
    engine = create_engine(settings.DATABASE_URL, connect_args={'connect_timeout': 5}
        if url.drivername.startswith('postgresql') else {})
    try:
        with engine.connect() as connection:
            tables = inspect(connection).get_table_names()
            print(json.dumps({'migration_revision': connection.execute(text(
                'select version_num from alembic_version')).scalars().all(),
                'conversation_tables': [t for t in tables if t.startswith('conversation')],
                'incident_columns': [c['name'] for c in inspect(connection).get_columns('incidents')]}))
    except Exception as exc:
        print(json.dumps({'database_error_type': type(exc).__name__}))
        return 1
    finally:
        engine.dispose()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
