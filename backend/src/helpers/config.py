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

    # Supabase (used for Auth + Storage)
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_KEY: str = ""

    # Document Storage (SPEC-02)
    STORAGE_BUCKET: str = "documents"
    MAX_FILE_SIZE_MB: int = 50

    # ── Provider Config (OpenAI-compatible) ─────────────────────────────
    # Default/fallback keys — used if LLM_* or EMBEDDING_* aren't set.
    # Works with: OpenRouter, OpenAI, Gemini, DeepSeek, Groq, etc.
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"

    # LLM Provider — for chat completions (generate_answer, streaming)
    # Set these to override the default OpenRouter provider.
    # Examples:
    #   OpenAI:    LLM_BASE_URL=https://api.openai.com/v1
    #   Gemini:    LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai
    #   DeepSeek:  LLM_BASE_URL=https://api.deepseek.com/v1
    #   Groq:      LLM_BASE_URL=https://api.groq.com/openai/v1
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = ""
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_TITLE_MODEL: str = "gpt-4o-mini"
    LLM_MAX_TOKENS: int = 2000
    LLM_TEMPERATURE: float = 0.3

    # Embedding Provider — for vector embeddings
    # Set these to override the default OpenRouter provider.
    # Examples:
    #   OpenAI:    EMBEDDING_BASE_URL=https://api.openai.com/v1
    #   Gemini:    EMBEDDING_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai
    EMBEDDING_API_KEY: str = ""
    EMBEDDING_BASE_URL: str = ""
    EMBEDDING_MODEL: str = "openai/text-embedding-3-small"
    EMBEDDING_DIMENSIONS: int = 1536

    # PDF Safety Limits (SPEC-03)
    MAX_PDF_PAGES: int = 1000
    MAX_PDF_SIZE_MB: int = 20

    # Chunking (SPEC-03)
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 120
    MIN_CHUNK_LENGTH: int = 50

    def get_llm_api_key(self) -> str:
        """Get LLM API key — falls back to OPENROUTER_API_KEY."""
        return self.LLM_API_KEY or self.OPENROUTER_API_KEY

    def get_llm_base_url(self) -> str:
        """Get LLM base URL — falls back to OPENROUTER_BASE_URL."""
        return self.LLM_BASE_URL or self.OPENROUTER_BASE_URL

    def get_embedding_api_key(self) -> str:
        """Get Embedding API key — falls back to OPENROUTER_API_KEY."""
        return self.EMBEDDING_API_KEY or self.OPENROUTER_API_KEY

    def get_embedding_base_url(self) -> str:
        """Get Embedding base URL — falls back to OPENROUTER_BASE_URL."""
        return self.EMBEDDING_BASE_URL or self.OPENROUTER_BASE_URL

    # Redis / Celery (SPEC-08)
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

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
