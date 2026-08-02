"""Application configuration using pydantic-settings."""

from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://platform_user:platform_pass@localhost:5432/platform"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # MinIO
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "platform-files"

    # JWT
    JWT_SECRET: str = "change-me-to-a-random-secret-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Credential encryption
    CONNECTION_ENCRYPTION_KEY: str = "change-me-generate-a-real-fernet-key"

    # LLM
    ANTHROPIC_API_KEY: str = ""

    # Embeddings
    EMBEDDING_MODEL: str = "BAAI/bge-m3"

    # SQL safety
    SQL_STATEMENT_TIMEOUT_MS: int = 5000
    SQL_MAX_ROWS: int = 1000

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
