"""Centralized application configuration.

All runtime configuration is sourced from environment variables (see
`.env.example` at the repo root). Nothing here should contain real secrets —
defaults are safe-but-non-functional placeholders for local development.
"""
from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: Literal["development", "staging", "production"] = "development"
    secret_key: str = "dev-only-secret-change-me"
    log_level: str = "INFO"

    # Database
    database_url: str = "postgresql+asyncpg://kaimira:change-me@localhost:5432/kaimira"

    # Object storage
    storage_backend: Literal["s3", "local"] = "local"
    s3_endpoint_url: str = "http://localhost:9000"
    s3_access_key: str = "kaimira"
    s3_secret_key: str = "change-me"
    s3_bucket: str = "kaimira-media"
    s3_region: str = "us-east-1"
    local_storage_path: str = "/data/uploads"

    # Auth
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 14
    jwt_algorithm: str = "HS256"

    # ML services
    asr_provider: Literal["mock", "whisper_local", "custom_endpoint"] = "mock"
    asr_model_path: str = "/models/asr/default"
    asr_endpoint_url: str | None = None
    tts_provider: Literal["mock", "coqui_local", "custom_endpoint"] = "mock"

    # Archival integration
    elar_api_base_url: str = "https://elar.example-archive.org/api"
    elar_api_key: str | None = None
    elar_default_collection_id: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
