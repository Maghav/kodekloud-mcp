"""Configuration and credential management for kodekloud-mcp.

Handles environment variable parsing, authentication auto-detection (Bearer JWT vs.
Cookie string), and secret redaction to prevent accidental credential leakage in logs.
"""

from __future__ import annotations

import os
import re
from typing import Any

from pydantic import BaseModel, Field


def _is_bare_jwt(token: str) -> bool:
    """Check if a string matches the format of a bare JSON Web Token (JWT).

    JWTs consist of three Base64URL-encoded parts separated by dots, typically
    beginning with 'eyJ'.
    """
    cleaned = token.strip()
    if cleaned.startswith("eyJ"):
        parts = cleaned.split(".")
        return len(parts) == 3 and all(bool(p) for p in parts)
    parts = cleaned.split(".")
    return len(parts) == 3 and all(bool(p) and re.match(r"^[A-Za-z0-9_-]+$", p) for p in parts)


def redact_secrets(text: str, secret: str | list[str] | None = None) -> str:
    """Scrub sensitive credentials, JWTs, and cookie tokens from text.

    Args:
        text: Input string (e.g. an error message, URL, or log line).
        secret: Optional known secret or list of secrets to explicitly replace.

    Returns:
        Sanitized string with sensitive tokens replaced by '[REDACTED]'.
    """
    if not text:
        return text

    sanitized = text

    # If explicit secrets are provided, scrub them directly
    secrets_to_scrub: list[str] = []
    if isinstance(secret, str):
        secrets_to_scrub.append(secret)
    elif isinstance(secret, (list, tuple)):
        secrets_to_scrub.extend([s for s in secret if isinstance(s, str)])

    for s in secrets_to_scrub:
        if len(s.strip()) > 3:
            clean_secret = s.strip()
            sanitized = sanitized.replace(clean_secret, "[REDACTED]")
            # Also redact if secret had Bearer prefix stripped
            if clean_secret.lower().startswith("bearer "):
                token_part = clean_secret[7:].strip()
                if token_part:
                    sanitized = sanitized.replace(token_part, "[REDACTED]")

    # Scrub common JWT patterns (eyJ...)
    sanitized = re.sub(
        r"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+", "[REDACTED_JWT]", sanitized
    )

    # Scrub Bearer authorization headers
    sanitized = re.sub(
        r"(Bearer\s+)[A-Za-z0-9_\-\.=]+", r"\1[REDACTED]", sanitized, flags=re.IGNORECASE
    )

    # Scrub Cookie headers or session IDs
    sanitized = re.sub(
        r"((?:session|token|auth|cookie|remember_token|_session_id)=)[^;\s&]+",
        r"\1[REDACTED]",
        sanitized,
        flags=re.IGNORECASE,
    )

    return sanitized


class Settings(BaseModel):
    """Runtime configuration settings for the kodekloud-mcp server."""

    session_credential: str | None = Field(
        default=None,
        description="Session cookie string or Bearer JWT token from browser DevTools.",
    )
    use_mock: bool = Field(
        default=True,
        description="Run in mock mode using realistic offline data (default: True).",
    )
    enable_write_tools: bool = Field(
        default=False,
        description="Enable state-changing tools like start_lab and stop_lab.",
    )
    cache_ttl_seconds: int = Field(
        default=60,
        description="In-memory response TTL cache in seconds.",
    )
    api_base_url: str = Field(
        default="https://api.kodekloud.com/api/v1",
        description="Base URL for KodeKloud endpoints (used when use_mock=False).",
    )
    transport: str = Field(
        default="stdio",
        description="MCP transport: 'stdio' or 'sse' / 'streamable-http'.",
    )
    host: str = Field(
        default="127.0.0.1",
        description="Host address for HTTP/SSE transport.",
    )
    port: int = Field(
        default=8000,
        description="Port for HTTP/SSE transport.",
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR).",
    )
    user_agent: str = Field(
        default="kodekloud-mcp/0.1.0 (+https://github.com/Maghav/kodekloud-mcp; educational/personal use)",
        description="Honest User-Agent identifying the client.",
    )
    engineer_session_credential: str | None = Field(
        default=None,
        description="Dedicated session cookie or JWT for engineer.kodekloud.com (falls back to session_credential).",
    )
    engineer_api_base_url: str = Field(
        default="https://engineer.kodekloud.com/api",
        description="Base URL for KodeKloud Engineer endpoints (used when use_mock=False).",
    )

    @classmethod
    def from_env(cls, **overrides: Any) -> Settings:
        """Construct Settings from environment variables with optional explicit overrides."""
        raw_cookie = os.getenv("KODEKLOUD_SESSION_COOKIE")
        raw_engineer_cookie = os.getenv("KODEKLOUD_ENGINEER_SESSION_COOKIE")
        use_mock_raw = os.getenv("KODEKLOUD_USE_MOCK")
        write_tools_raw = os.getenv("KODEKLOUD_ENABLE_WRITE_TOOLS")
        cache_ttl_raw = os.getenv("KODEKLOUD_CACHE_TTL_SECONDS")
        base_url = os.getenv("KODEKLOUD_API_BASE_URL", "https://api.kodekloud.com/api/v1")
        engineer_base_url = os.getenv(
            "KODEKLOUD_ENGINEER_BASE_URL", "https://engineer.kodekloud.com/api"
        )
        transport = os.getenv("KODEKLOUD_MCP_TRANSPORT", "stdio").lower()
        host = os.getenv("KODEKLOUD_MCP_HOST", "127.0.0.1")
        port_raw = os.getenv("KODEKLOUD_MCP_PORT", "8000")
        log_level = os.getenv("KODEKLOUD_LOG_LEVEL", "INFO").upper()

        # Defaults
        use_mock = True
        if use_mock_raw is not None:
            use_mock = use_mock_raw.lower() in ("1", "true", "yes", "on")

        enable_write_tools = False
        if write_tools_raw is not None:
            enable_write_tools = write_tools_raw.lower() in ("1", "true", "yes", "on")

        cache_ttl = 60
        if cache_ttl_raw:
            try:
                cache_ttl = int(cache_ttl_raw)
            except ValueError:
                cache_ttl = 60

        port = 8000
        if port_raw:
            try:
                port = int(port_raw)
            except ValueError:
                port = 8000

        data: dict[str, Any] = {
            "session_credential": raw_cookie.strip() if raw_cookie else None,
            "engineer_session_credential": raw_engineer_cookie.strip()
            if raw_engineer_cookie
            else None,
            "use_mock": use_mock,
            "enable_write_tools": enable_write_tools,
            "cache_ttl_seconds": cache_ttl,
            "api_base_url": base_url.rstrip("/"),
            "engineer_api_base_url": engineer_base_url.rstrip("/"),
            "transport": transport,
            "host": host,
            "port": port,
            "log_level": log_level,
        }

        # Apply programmatic overrides
        data.update(overrides)

        return cls(**data)

    def _headers_for_credential(self, credential: str | None) -> dict[str, str]:
        """Auto-detect credential format and construct appropriate HTTP request headers."""
        if not credential:
            return {}

        cred = credential.strip()
        if cred.lower().startswith("bearer "):
            token = cred[7:].strip()
            return {"Authorization": f"Bearer {token}"}
        if _is_bare_jwt(cred):
            return {"Authorization": f"Bearer {cred}"}
        return {"Cookie": cred}

    def get_auth_headers(self) -> dict[str, str]:
        """Auto-detect credential format and construct appropriate HTTP request headers.

        Logic:
        - Starts with 'Bearer ' (case-insensitive) -> Authorization: Bearer <token>
        - Bare JWT format (starts with eyJ or 3 base64url parts) -> Authorization: Bearer <token>
        - Otherwise -> Cookie: <credential_string>
        """
        return self._headers_for_credential(self.session_credential)

    def get_engineer_auth_headers(self) -> dict[str, str]:
        """Get auth headers for engineer.kodekloud.com.

        Uses engineer_session_credential if provided, otherwise falls back to
        the primary session_credential.
        """
        if self.engineer_session_credential:
            return self._headers_for_credential(self.engineer_session_credential)
        return self.get_auth_headers()

    def masked_credential(self) -> str:
        """Return a safely masked preview of the credential for diagnostics."""
        if not self.session_credential:
            return "<none>"
        cred = self.session_credential.strip()
        if len(cred) <= 8:
            return "***"
        return f"{cred[:4]}...{cred[-4:]}"

    def masked_engineer_credential(self) -> str:
        """Return a safely masked preview of the engineer credential for diagnostics."""
        cred = self.engineer_session_credential or self.session_credential
        if not cred:
            return "<none>"
        clean = cred.strip()
        if len(clean) <= 8:
            return "***"
        return f"{clean[:4]}...{clean[-4:]}"
