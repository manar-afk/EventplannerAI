"""Configuration management for EventPilot AI backend."""

import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "EventPilot AI"
    environment: str = os.getenv("ENVIRONMENT", "development")
    port: int = int(os.getenv("PORT", "8080"))

    # Gemini configuration
    # Default to Vertex AI with ADC; fall back to GEMINI_API_KEY if supplied
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    gemini_timeout_seconds: float = float(os.getenv("GEMINI_TIMEOUT_SECONDS", "18.0"))

    # CORS configuration
    cors_origins_raw: str = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://localhost:8080"
    )

    # Security limits
    max_body_bytes: int = int(os.getenv("MAX_BODY_BYTES", "1048576"))  # 1MB limit

    # Rate limiting
    rate_limit_per_minute: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "20"))

    @property
    def cors_origins(self) -> List[str]:
        if not self.cors_origins_raw or self.cors_origins_raw.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins_raw.split(",") if origin.strip()]


settings = Settings()
