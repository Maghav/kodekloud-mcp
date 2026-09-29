"""Exception classes for the kodekloud-mcp server.

All exceptions provide user-friendly error messages that guide the learner
on how to resolve the issue (e.g., re-copying an expired session cookie),
while strictly ensuring that sensitive credentials are never leaked.
"""


class KodeKloudMCPError(Exception):
    """Base exception for all kodekloud-mcp errors."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class AuthenticationMissingError(KodeKloudMCPError):
    """Raised when KODEKLOUD_SESSION_COOKIE is not provided and mock mode is disabled."""

    def __init__(
        self,
        message: str = (
            "Authentication credential missing. Please set the KODEKLOUD_SESSION_COOKIE "
            "environment variable with your session cookie or JWT token copied from browser "
            "DevTools, or enable mock mode by setting KODEKLOUD_USE_MOCK=true."
        ),
    ) -> None:
        super().__init__(message)


class SessionExpiredError(KodeKloudMCPError):
    """Raised when KodeKloud returns HTTP 401 or 403, indicating an expired or invalid session."""

    def __init__(
        self,
        status_code: int = 401,
        message: str | None = None,
    ) -> None:
        if message is None:
            message = (
                f"KodeKloud session expired or rejected (HTTP {status_code}). "
                "Your browser session credential is no longer valid. Please log in to your "
                "KodeKloud account in your web browser, copy a fresh session cookie or JWT token "
                "from DevTools, and update your KODEKLOUD_SESSION_COOKIE configuration."
            )
        super().__init__(message)
        self.status_code = status_code


class RateLimitExceededError(KodeKloudMCPError):
    """Raised when KodeKloud rate limits requests (HTTP 429) after retry attempts."""

    def __init__(
        self,
        attempts: int = 3,
        retry_after: int | None = None,
        message: str | None = None,
    ) -> None:
        if message is None:
            delay_hint = f" Retry-After suggests waiting {retry_after}s." if retry_after else ""
            message = (
                f"KodeKloud API rate limit exceeded (HTTP 429). The request was automatically "
                f"retried {attempts} times with exponential backoff, but rate limiting persists.{delay_hint} "
                "Please wait a few minutes before trying again to avoid hammering KodeKloud servers."
            )
        super().__init__(message)
        self.attempts = attempts
        self.retry_after = retry_after


class NetworkTimeoutError(KodeKloudMCPError):
    """Raised when an HTTP request to KodeKloud times out."""

    def __init__(
        self,
        timeout_seconds: float,
        message: str | None = None,
    ) -> None:
        if message is None:
            message = (
                f"Request to KodeKloud timed out after {timeout_seconds:.1f} seconds. "
                "KodeKloud may be experiencing high latency, connectivity issues, or a temporary outage. "
                "Please check your network connection and try again."
            )
        super().__init__(message)
        self.timeout_seconds = timeout_seconds


class NonJsonResponseError(KodeKloudMCPError):
    """Raised when KodeKloud returns non-JSON content (such as an HTML error or Cloudflare challenge)."""

    def __init__(
        self,
        status_code: int,
        content_type: str,
        preview: str,
        message: str | None = None,
    ) -> None:
        if message is None:
            message = (
                f"Received unexpected non-JSON response from KodeKloud (HTTP {status_code}, "
                f"Content-Type: '{content_type}'). The endpoint path may have changed or the session "
                f"may have been redirected to an HTML login/challenge page. Preview: {preview}"
            )
        super().__init__(message)
        self.status_code = status_code
        self.content_type = content_type
        self.preview = preview


class WriteOperationDisabledError(KodeKloudMCPError):
    """Raised when a state-modifying action is attempted while write tools are disabled."""

    def __init__(
        self,
        action: str = "This state-modifying action",
        message: str | None = None,
    ) -> None:
        if message is None:
            message = (
                f"{action} is disabled by default to protect your KodeKloud account. "
                "To enable lab start/stop operations, set KODEKLOUD_ENABLE_WRITE_TOOLS=true "
                "in your environment variables or config."
            )
        super().__init__(message)
        self.action = action
