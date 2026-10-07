"""
Application configuration.

All configuration is read from environment variables (via a .env file in
local development). Nothing here should ever contain a hardcoded secret.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Dotenv location is stable across launch directories. OS environment still
    # takes precedence (including an explicit local DATABASE_URL override).
    model_config = SettingsConfigDict(env_file=Path(__file__).resolve().parents[2] / '.env', extra="ignore")

    # Required: PostgreSQL connection string (e.g. Supabase or local Postgres).
    DATABASE_URL: str

    # Comma-separated origins the frontend is served from.
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    SERVICE_NAME: str = "cybersos-api"
    DIAGNOSTICS_LOG_DIR: str | None = str(Path(__file__).resolve().parents[2] / 'tmp' / 'logs')
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
    UNDERSTANDING_ENABLED: bool = True
    UNDERSTANDING_PROVIDER: Literal['gemini', 'disabled'] = 'gemini'
    GEMINI_API_KEY: str | None = None
    UNDERSTANDING_MODEL: str = 'gemini-3.5-flash-lite'
    UNDERSTANDING_TIMEOUT_SECONDS: float = Field(default=20, ge=0.1, le=30)
    EVIDENCE_REVIEW_TIMEOUT_SECONDS: float = Field(default=30, ge=0.1, le=30)
    UNDERSTANDING_RETRIES: int = Field(default=1, ge=0, le=2)
    UNDERSTANDING_MAX_INPUT_CHARS: int = Field(default=8000, ge=256, le=8000)
    UNDERSTANDING_MAX_OUTPUT_CHARS: int = Field(default=24000, ge=256, le=48000)
    UNDERSTANDING_MAX_OUTPUT_TOKENS: int = Field(default=4096, ge=256, le=8192)
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
