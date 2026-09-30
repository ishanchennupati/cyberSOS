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

