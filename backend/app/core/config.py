"""
Application configuration.

All configuration is read from environment variables (via a .env file in
local development). Nothing here should ever contain a hardcoded secret.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Required: PostgreSQL connection string (e.g. Supabase or local Postgres).
    DATABASE_URL: str

    # Comma-separated origins the frontend is served from.
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    SERVICE_NAME: str = "cybersos-api"
    API_V1_PREFIX: str = "/api/v1"
    EVIDENCE_STORAGE_DIR: str = "./evidence"
    # If unset, retain the previous evidence directory during upgrades.
    LOCAL_STORAGE_ROOT: str | None = None
    MAX_EVIDENCE_FILE_SIZE_MB: int = Field(default=10, ge=1, le=100)
    SUPABASE_URL: str | None = None
    SUPABASE_SERVICE_ROLE_KEY: str | None = None
    SUPABASE_EVIDENCE_BUCKET: str = "cybersos-evidence"
    EXTRACTION_PROVIDER: Literal["heuristic", "anthropic"] = "heuristic"
    SUMMARY_PROVIDER: Literal["template", "anthropic"] = "template"
    ANTHROPIC_API_KEY: str | None = None
    ANTHROPIC_MODEL: str | None = None
    CASE_COOKIE_SECURE: bool = True
    CASE_ACCESS_TTL_SECONDS: int = Field(default=604800, ge=600, le=2592000)

    @property
    def supabase_configured(self) -> bool:
        return bool(self.SUPABASE_URL and self.SUPABASE_SERVICE_ROLE_KEY)

    @property
    def max_evidence_file_size_bytes(self) -> int:
        return self.MAX_EVIDENCE_FILE_SIZE_MB * 1024 * 1024

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> "Settings":
    """Cached settings instance so we only parse the environment once."""
    return Settings()
