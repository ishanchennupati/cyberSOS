from pathlib import Path
import ast

from app.core.config import Settings


def test_R6_settings_cover_code_and_example(tmp_path):
    root = Path(__file__).resolve().parents[1]
    # Defaults must work without external provider credentials or a .env file.
    settings = Settings(_env_file=None, DATABASE_URL="sqlite:///:memory:",
                        SUPABASE_URL=None, SUPABASE_SERVICE_ROLE_KEY=None,
                        ANTHROPIC_API_KEY=None, LOCAL_STORAGE_ROOT=str(tmp_path))
    unknown = []
    for source in (root / "app").rglob("*.py"):
        tree = ast.parse(source.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "settings":
                if not hasattr(settings, node.attr):
                    unknown.append((source.name, node.attr))
    assert not unknown, unknown
    example = (root / ".env.example").read_text()
    keys = {line.split("=", 1)[0] for line in example.splitlines() if "=" in line and not line.startswith("#")}
    assert set(Settings.model_fields) <= keys
    assert settings.supabase_configured is False
    assert settings.max_evidence_file_size_bytes == 10 * 1024 * 1024
    from app.services.storage_service import get_storage_backend
    backend = get_storage_backend()
    backend.upload("synthetic.txt", b"synthetic", "text/plain")
    assert backend.download("synthetic.txt") == b"synthetic"
    backend.delete("synthetic.txt")


def test_R5_session_database_is_not_a_repository_file():
    from app.core.config import get_settings
    assert not get_settings().DATABASE_URL.endswith("/./test.db")
    assert "/test.db" not in get_settings().DATABASE_URL


def test_dotenv_location_is_independent_of_launch_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert Path(Settings.model_config['env_file']).is_absolute()
    assert Path(Settings.model_config['env_file']).parent.name == 'backend'
    monkeypatch.setenv('DATABASE_URL', 'sqlite:///:memory:')
    assert Settings().DATABASE_URL == 'sqlite:///:memory:'


def test_local_launcher_selects_local_db_storage_and_preserves_backup(tmp_path, monkeypatch):
    import run_local
    import sqlite3
    import uvicorn
    from unittest.mock import MagicMock
    from alembic import command
    from app.core.config import get_settings
    backend = tmp_path / 'backend'
    backend.mkdir()
    database = backend / 'local.sqlite'
    with sqlite3.connect(database) as connection:
        connection.execute('create table synthetic (value text)')
        connection.execute("insert into synthetic values ('saved story')")
    monkeypatch.setattr(run_local, '__file__', str(backend / 'run_local.py'))
    monkeypatch.setattr(run_local.socket, 'socket', MagicMock())
    monkeypatch.setenv('SUPABASE_URL', 'https://synthetic.invalid')
    monkeypatch.setenv('SUPABASE_SERVICE_ROLE_KEY', 'synthetic-not-a-secret')
    # The launcher intentionally overrides these. Register them with monkeypatch
    # so local HTTP cookie settings/database do not leak into later API tests.
    monkeypatch.setenv('DATABASE_URL', get_settings().DATABASE_URL)
    monkeypatch.setenv('CASE_COOKIE_SECURE', 'true')
    migration = MagicMock()
    server = MagicMock()
    monkeypatch.setattr(command, 'upgrade', migration)
    monkeypatch.setattr(uvicorn, 'run', server)
    # Ensure chdir is restored by monkeypatch after exercising the launcher.
    monkeypatch.chdir(tmp_path)
    get_settings.cache_clear()
    run_local.main()
    settings = get_settings()
    assert settings.DATABASE_URL == 'sqlite:///' + database.as_posix()
    assert settings.LOCAL_STORAGE_ROOT == str(backend / 'evidence')
    assert not settings.supabase_configured
    assert not settings.CASE_COOKIE_SECURE
    assert migration.call_args.args[1] == 'head'
    assert server.call_args.kwargs['port'] == 8000
    assert server.call_args.kwargs['access_log'] is False
    backup = next((backend / 'tmp').glob('*.sqlite'))
    with sqlite3.connect(backup) as connection:
        assert connection.execute('select value from synthetic').fetchone()[0] == 'saved story'
