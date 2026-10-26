"""Tests for pydantic-settings configuration and CORS fail-closed policies."""

import pytest
from pydantic import ValidationError
from backend.app.config import Settings


def test_production_wildcard_cors_raises():
    """Requirement: production plus '*' raises validation error."""
    with pytest.raises(ValidationError, match="Wildcard"):
        Settings(environment="production", cors_origins="*")

    with pytest.raises(ValidationError, match="Wildcard"):
        Settings(environment="production", cors_origins="https://example.com, *")


def test_production_empty_cors_gives_no_origins():
    """Requirement: production plus empty gives no origins ([])."""
    s = Settings(environment="production", cors_origins="")
    assert s.allowed_cors_origins == []


def test_development_empty_cors_defaults_to_localhost():
    """Verify development mode defaults to localhost origins."""
    s = Settings(environment="development", cors_origins="")
    assert "http://localhost:5173" in s.allowed_cors_origins


def test_config_out_of_range_raises():
    """Requirement: out-of-range values raise."""
    with pytest.raises(ValidationError):
        Settings(port=70000)  # > 65535

    with pytest.raises(ValidationError):
        Settings(rate_limit_per_minute=0)  # < 1

    with pytest.raises(ValidationError):
        Settings(trusted_proxy_hops=10)  # > 5


def test_repr_hides_secret_key():
    """Requirement: repr(settings) hides the key."""
    s = Settings(gemini_api_key="my-super-secret-key-12345")
    representation = repr(s)
    assert "my-super-secret-key-12345" not in representation
    assert "**********" in representation or "SecretStr('')" in representation or "SecretStr('**********')" in representation
