import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import Any, List

class Settings(BaseSettings):
    # App General Settings
    ENV: str = "development"
    PROJECT_NAME: str = "Zenith Computational Biology API"
    VERSION: str = "1.0.0"
    DEBUG: bool = False

    # ESMFold Settings
    ESMFOLD_ENABLED: bool = True
    ESMFOLD_API_URL: str = "https://api.esmatlas.com/foldSequence/v1/pdb/"
    ESMFOLD_TIMEOUT_SECONDS: float = 30.0
    ESMFOLD_MAX_SEQUENCE_LENGTH: int = 1000
    ESMFOLD_FALLBACK_ENABLED: bool = True
    ESMFOLD_PROVIDER_NAME: str = "ESMFold"
    ESMFOLD_CACHE_ENABLED: bool = True

    # ── Boltz API (Native Complex Prediction) ─────────────────────────────────
    BOLTZ_API_ENABLED: bool = True
    BOLTZ_API_BASE_URL: str = "https://api.boltz.bio"
    BOLTZ_API_KEY: str = ""          # Set in Railway env only — NEVER commit
    BOLTZ_API_TIMEOUT_SECONDS: float = 120.0
    BOLTZ_API_MAX_PROTEIN_CHAINS: int = 5
    BOLTZ_API_MAX_DNA_CHAINS: int = 5
    BOLTZ_API_MAX_RNA_CHAINS: int = 5
    BOLTZ_API_MAX_LIGANDS: int = 10
    BOLTZ_API_MAX_JOBS_PER_USER_PER_DAY: int = 50
    BOLTZ_API_DATA_RETENTION_DAYS: int = 7
    # Safety rails — set both to false in production, always
    COMPLEX_ALLOW_MOCK: bool = False
    COMPLEX_REQUIRE_REAL_ENGINE: bool = True
    COMPLEX_SYNTHETIC_FALLBACK: bool = False  # MUST remain False in production

    # Database & Cache
    DATABASE_URL: str = "sqlite:///./zenith_api.db"
    REDIS_URL: str = "redis://localhost:6379/0"

    # Cryptography / Security
    SECRET_KEY: str = "CHANGE-ME-IN-PRODUCTION-OR-SET-ENV-VAR"
    API_KEY_HEADER: str = "X-API-Key"
    
    # CORS config - typed as Any to prevent Pydantic-settings complex decoding crash
    ALLOWED_ORIGINS: Any = ["*"]

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # Stripe Settings
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""

    # Celery configuration
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
