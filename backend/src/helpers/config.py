import os
from pydantic_settings import BaseSettings
from pathlib import Path

# Get the project root directory (backend folder)
BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    # These will be loaded from .env
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_SERVER: str
    POSTGRES_PORT: str
    POSTGRES_DB: str

    # Use field name matching the key in .env if provided
    DATABASE_URL: str | None = None
    TEST_DATABASE_URL: str | None = None

    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int

    # Email
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int
    MAIL_SERVER: str
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False

    CORS_ORIGINS: str

    def get_database_url(self) -> str:
        # If DATABASE_URL is provided in .env, use it (and make sure it uses asyncpg)
        if self.DATABASE_URL:
            return self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

        # Otherwise, construct it from individual parts
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    def get_test_database_url(self) -> str:
        if not self.TEST_DATABASE_URL:
            raise RuntimeError("❌ TEST_DATABASE_URL is not set")

        return self.TEST_DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

    class Config:
        env_file = os.path.join(BASE_DIR, ".env")
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
