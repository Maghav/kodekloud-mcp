"""Tests for configuration parsing, credential auto-detection, and secret redaction."""

from kodekloud_mcp.config import Settings, redact_secrets


def test_default_settings() -> None:
    """Verify default security settings."""
    settings = Settings.from_env()
    assert settings.use_mock is True
    assert settings.enable_write_tools is False
    assert settings.transport == "stdio"
    assert settings.cache_ttl_seconds == 60


def test_auth_headers_bearer_prefix() -> None:
    """Auto-detect Authorization header when credential starts with 'Bearer'."""
    settings = Settings(session_credential="Bearer sample_jwt_token_xyz")
    headers = settings.get_auth_headers()
    assert headers == {"Authorization": "Bearer sample_jwt_token_xyz"}

    # Case-insensitive check
    settings_lower = Settings(session_credential="bearer lower_jwt_token_xyz")
    assert settings_lower.get_auth_headers() == {"Authorization": "Bearer lower_jwt_token_xyz"}


def test_auth_headers_bare_jwt() -> None:
    """Auto-detect Authorization header when credential is a bare JWT without Bearer prefix."""
    sample_jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4ifQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    settings = Settings(session_credential=sample_jwt)
    headers = settings.get_auth_headers()
    assert headers == {"Authorization": f"Bearer {sample_jwt}"}


def test_auth_headers_cookie_string() -> None:
    """Auto-detect Cookie header when credential is a standard browser cookie string."""
    raw_cookie = "_session_id=a1b2c3d4e5f6; remember_token=xyz789; kk_auth=active"
    settings = Settings(session_credential=raw_cookie)
    headers = settings.get_auth_headers()
    assert headers == {"Cookie": raw_cookie}


def test_auth_headers_empty() -> None:
    """Empty headers when no credential is provided."""
    settings = Settings(session_credential=None)
    assert settings.get_auth_headers() == {}


def test_redact_secrets_explicit() -> None:
    """Scrub explicit known secret from error messages."""
    secret = "secret_session_token_xyz123"
    error_msg = f"Failed to authenticate with token {secret} on server"
    sanitized = redact_secrets(error_msg, secret=secret)
    assert secret not in sanitized
    assert "[REDACTED]" in sanitized


def test_redact_secrets_jwt_pattern() -> None:
    """Automatically redact JWT patterns in text even if not explicitly passed."""
    jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    text = f"Connection failed to endpoint with header Authorization: Bearer {jwt}"
    sanitized = redact_secrets(text)
    assert jwt not in sanitized
    assert "[REDACTED_JWT]" in sanitized or "[REDACTED]" in sanitized


def test_redact_secrets_cookie_key_value() -> None:
    """Automatically scrub session and cookie parameters."""
    text = "Request headers contained _session_id=deadbeef123456; other=ok"
    sanitized = redact_secrets(text)
    assert "deadbeef123456" not in sanitized
    assert "[REDACTED]" in sanitized


def test_masked_credential() -> None:
    """Verify safe masking of credential for diagnostic logging."""
    assert Settings(session_credential=None).masked_credential() == "<none>"
    assert Settings(session_credential="short").masked_credential() == "***"
    masked = Settings(session_credential="superlongsessiontokenabcdef").masked_credential()
    assert masked.startswith("supe")
    assert masked.endswith("cdef")
    assert "..." in masked
