"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/incident_warroom"
    database_url_sync: str = "postgresql+psycopg://postgres:postgres@localhost:5432/incident_warroom"

    # JWT
    jwt_secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 480

    # Server
    backend_host: str = "127.0.0.1"
    backend_port: int = 8000


@lru_cache()
def get_settings() -> Settings:
    return Settings()
