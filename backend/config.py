"""
AC Agent — Configuration
All environment variables and constants.
"""

import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    APP_NAME: str = "AC Agent — Associate Consultant AI"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # API Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "CHANGE_THIS_IN_PRODUCTION_USE_256BIT_RANDOM")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8-hour shift

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://acagent:acagent@localhost:5432/acagent"
    )

    # Anthropic
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    CLAUDE_SONNET_MODEL: str = "claude-sonnet-4-6"   # Briefing + notes
    CLAUDE_HAIKU_MODEL: str  = "claude-haiku-4-5-20251001"  # Fast checks
    CLAUDE_MAX_TOKENS: int = 4096
    CLAUDE_TIMEOUT_SECONDS: int = 60

    # AWS (Phase 2 — S3 storage)
    AWS_REGION: str = "ap-south-1"
    S3_BUCKET: str = os.getenv("S3_BUCKET", "acagent-documents-mumbai")

    # Clinical thresholds
    BRIEFING_OVERDUE_HOURS_CRITICAL: int = 6
    BRIEFING_OVERDUE_HOURS_GUARDED:  int = 12
    BRIEFING_OVERDUE_HOURS_STABLE:   int = 24
    NOTE_OVERDUE_HOURS: int = 4

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
