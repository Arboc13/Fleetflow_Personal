from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, loaded from environment / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    PROJECT_NAME: str = "FleetFlow"
    API_V1_PREFIX: str = "/api"

    # Database
    DATABASE_URL: str = (
        "postgresql+psycopg://fleetflow:fleetflow@localhost:5432/fleetflow"
    )

    # Security
    SECRET_KEY: str = "change-me-in-.env"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8  # 8 hours

    # Fernet key for encrypting CNP at rest (NFR-1). MUST be overridden in .env
    # in production. Generate one: python -c "from cryptography.fernet import
    # Fernet; print(Fernet.generate_key().decode())"
    ENCRYPTION_KEY: str = "yZ4wylYaDUtSqNdeIpNWVzm2Vlr4hGBaJLDFJ7LV15Y="

    # CORS — Vite dev server + LAN phone access are added in .env when needed
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:5173"]

    # Where uploaded fuel-import files are stored before parsing (F-402)
    UPLOAD_DIR: str = "uploads"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
