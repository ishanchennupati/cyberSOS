"""
Application configuration.

All configuration is read from environment variables (via a .env file in
local development). Nothing here should ever contain a hardcoded secret.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Required: PostgreSQL connection string (e.g. Supabase or local Postgres).
    DATABASE_URL: str

    # Comma-separated origins the frontend is served from.
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    SERVICE_NAME: str = "cybersos-api"
    API_V1_PREFIX: str = "/api/v1"

    # --- Phase 3: Evidence Vault -------------------------------------------

    # Supabase project (leave blank in local/dev to fall back to on-disk
    # storage under ./var/evidence-storage — useful for tests and demos
    # that don't have a Supabase project configured).
    SUPABASE_URL: str | None = None
    SUPABASE_SERVICE_ROLE_KEY: str | None = None
    SUPABASE_EVIDENCE_BUCKET: str = "cybersos-evidence"

    # Local fallback storage root, only used when SUPABASE_URL is not set.
    LOCAL_STORAGE_ROOT: str = "./var/evidence-storage"

    # File-size limits (megabytes). Kept as env vars, not hardcoded, so a
    # deployment can tune them without a code change.
    MAX_EVIDENCE_FILE_SIZE_MB: float = 10.0
    MAX_ID_DOCUMENT_SIZE_MB: float = 5.0

    # Evidence extraction / AI summary provider selection. "heuristic" needs
    # no API key and always works; "anthropic" uses the Claude API when a
    # key is configured. Either can be swapped without touching callers.
    EXTRACTION_PROVIDER: str = "heuristic"
    SUMMARY_PROVIDER: str = "template"
    ANTHROPIC_API_KEY: str | None = None
    ANTHROPIC_MODEL: str = "claude-sonnet-4-5"

    # Demo-mode flag. When true, the UI shows the "synthetic data only"
    # banner. Does not affect backend behaviour.
    DEMO_MODE: bool = True

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def max_evidence_file_size_bytes(self) -> int:
        return int(self.MAX_EVIDENCE_FILE_SIZE_MB * 1024 * 1024)

    @property
    def max_id_document_size_bytes(self) -> int:
        return int(self.MAX_ID_DOCUMENT_SIZE_MB * 1024 * 1024)

    @property
    def supabase_configured(self) -> bool:
        return bool(self.SUPABASE_URL and self.SUPABASE_SERVICE_ROLE_KEY)


@lru_cache
def get_settings() -> "Settings":
    """Cached settings instance so we only parse the environment once."""
    return Settings()
