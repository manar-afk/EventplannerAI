"""Configuration management for EventPilot AI backend using pydantic-settings.

Loads environment variables from <repo root>/.env.
Enforces strict typing, range checks, and fail-closed CORS policies.
"""

from pathlib import Path
from typing import List, Literal, Optional
import os
from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
ENV_FILE = REPO_ROOT / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    environment: Literal["development", "production"] = "development"
    port: int = Field(default=8080, ge=1, le=65535)

    # Gemini configuration
    # Precedence: Vertex AI ADC if google_cloud_project is set or K_SERVICE is present.
    # gemini_api_key is an optional local-dev fallback only.
    gemini_api_key: SecretStr = SecretStr("")
    gemini_model: str = "gemini-2.5-flash"
    google_cloud_project: Optional[str] = None
    google_cloud_location: str = "us-central1"
    gemini_timeout_seconds: float = Field(default=20.0, ge=0.0, le=60.0)

    # Proxy and Rate Limiting
    trusted_proxy_hops: int = Field(default=1, ge=1, le=5)
    rate_limit_per_minute: int = Field(default=10, ge=1, le=600)
    rate_limit_global_per_minute: int = Field(default=120, ge=1, le=10000)

    # Security limits
    max_body_bytes: int = Field(default=1048576, ge=1024, le=10485760)

    # CORS configuration
    cors_origins: str = ""

    @model_validator(mode="after")
    def validate_cors_policy(self) -> "Settings":
        raw = self.cors_origins.strip()
        origins = [o.strip() for o in raw.split(",") if o.strip()]
        if self.environment == "production":
            if raw == "*" or "*" in origins:
                raise ValueError("Wildcard '*' CORS origin is strictly forbidden in production.")
        return self

    @property
    def allowed_cors_origins(self) -> List[str]:
        raw = self.cors_origins.strip()
        if not raw:
            if self.environment == "development":
                return [
                    "http://localhost:5173",
                    "http://127.0.0.1:5173",
                    "http://localhost:8080",
                ]
            return []
        if raw == "*":
            return ["*"]
        return [o.strip() for o in raw.split(",") if o.strip()]

    @property
    def is_gemini_configured(self) -> bool:
        """Single source of truth for Gemini availability across client and healthcheck."""
        if bool(self.google_cloud_project) or bool(os.getenv("K_SERVICE")):
            return True
        if bool(self.gemini_api_key.get_secret_value().strip()):
            return True
        return False


settings = Settings()
