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
    CORS_ORIGINS: str = "http://localhost:3000"

    SERVICE_NAME: str = "cybersos-api"
    API_V1_PREFIX: str = "/api/v1"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> "Settings":
    """Cached settings instance so we only parse the environment once."""
    return Settings()
