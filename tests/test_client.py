"""Tests for KodeKloudClient covering mock mode and live mode via httpx.MockTransport."""

import json

import httpx
import pytest

from kodekloud_mcp.config import Settings
from kodekloud_mcp.exceptions import (
    AuthenticationMissingError,
    NetworkTimeoutError,
    NonJsonResponseError,
    RateLimitExceededError,
    SessionExpiredError,
    WriteOperationDisabledError,
)
from kodekloud_mcp.kodekloud_client import KodeKloudClient


# =============================================================================
# Mock Mode Tests
# =============================================================================
@pytest.mark.asyncio
async def test_mock_get_course_progress_all(mock_client: KodeKloudClient) -> None:
    """Verify get_course_progress in mock mode returns all courses."""
    res = await mock_client.get_course_progress()
    assert res.total_courses_enrolled > 0
    assert res.average_progress_percent > 0
    assert len(res.courses) > 0
    # Check CKA exists
    cka = next((c for c in res.courses if "CKA" in c.course_title), None)
    assert cka is not None
    assert cka.completed_labs > 0


@pytest.mark.asyncio
async def test_mock_get_course_progress_filtered(mock_client: KodeKloudClient) -> None:
    """Verify get_course_progress filters by course name."""
    res = await mock_client.get_course_progress("Docker")
    assert res.total_courses_enrolled == 1
    assert "Docker" in res.courses[0].course_title
    assert res.courses[0].percent_complete == 100.0


@pytest.mark.asyncio
async def test_mock_list_enrolled_courses(mock_client: KodeKloudClient) -> None:
    """Verify list_enrolled_courses returns enrolled course catalog."""
    res = await mock_client.list_enrolled_courses()
    assert res.count >= 5
    titles = [c.title for c in res.courses]
    assert any("Kubernetes" in t for t in titles)
    assert any("Terraform" in t for t in titles)


@pytest.mark.asyncio
async def test_mock_get_course_outline(mock_client: KodeKloudClient) -> None:
    """Verify get_course_outline returns syllabus and next suggested lesson."""
    res = await mock_client.get_course_outline("CKA")
    assert res.total_modules > 0
    assert res.total_lessons > 0
    assert res.next_suggested_lesson is not None
    assert not res.next_suggested_lesson.completed


@pytest.mark.asyncio
async def test_mock_get_active_labs(mock_client: KodeKloudClient) -> None:
    """Verify get_active_labs returns running/paused labs."""
    res = await mock_client.get_active_labs()
    assert res.count > 0
    lab = res.active_labs[0]
    assert lab.status in ("Running", "Paused", "Stopped")
    assert lab.remaining_time_minutes > 0


@pytest.mark.asyncio
async def test_mock_get_certifications(mock_client: KodeKloudClient) -> None:
    """Verify get_certifications returns certification milestones."""
    res = await mock_client.get_certifications()
    assert res.count > 0
    cert_ids = [c.cert_id for c in res.certifications]
    assert "CKA" in cert_ids


@pytest.mark.asyncio
async def test_mock_get_learning_summary(mock_client: KodeKloudClient) -> None:
    """Verify get_learning_summary returns study streak and activity digest."""
    res = await mock_client.get_learning_summary()
    assert res.total_hours_learned > 0
    assert res.streak.current_streak_days > 0
    assert len(res.recent_activities) > 0
    assert res.next_suggested_lesson is not None


@pytest.mark.asyncio
async def test_write_tools_disabled_by_default(mock_client: KodeKloudClient) -> None:
    """Verify state-modifying tools raise WriteOperationDisabledError when disabled."""
    with pytest.raises(WriteOperationDisabledError) as exc_info:
        await mock_client.start_lab("lab-cka-1")
    assert "start_lab is disabled by default" in str(exc_info.value)

    with pytest.raises(WriteOperationDisabledError) as exc_info:
        await mock_client.stop_lab("lab-cka-1")
    assert "stop_lab is disabled by default" in str(exc_info.value)


@pytest.mark.asyncio
async def test_write_tools_when_enabled() -> None:
    """Verify state-modifying tools succeed when KODEKLOUD_ENABLE_WRITE_TOOLS=true."""
    settings = Settings(
        session_credential="mock_token",
        use_mock=True,
        enable_write_tools=True,
    )
    client = KodeKloudClient(settings=settings)

    start_res = await client.start_lab("lab-cka-1")
    assert start_res.success is True
    assert start_res.status == "Running"
    assert start_res.lab_url is not None

    stop_res = await client.stop_lab("lab-cka-1")
    assert stop_res.success is True
    assert stop_res.status == "Terminated"


# =============================================================================
# Live Mode Simulation via httpx.MockTransport Tests
# =============================================================================
@pytest.mark.asyncio
async def test_live_missing_credential_raises_auth_error() -> None:
    """Verify missing credential in live mode raises AuthenticationMissingError."""
    settings = Settings(session_credential=None, use_mock=False)
    client = KodeKloudClient(settings=settings)

    with pytest.raises(AuthenticationMissingError) as exc_info:
        await client.get_course_progress()
    assert "Authentication credential missing" in str(exc_info.value)


@pytest.mark.asyncio
async def test_live_200_ok_response() -> None:
    """Verify successful 200 response with MockTransport."""
    payload = {
        "total_courses_enrolled": 1,
        "average_progress_percent": 75.0,
        "courses": [
            {
                "course_id": "cka-101",
                "course_title": "Live CKA Course",
                "category": "Kubernetes",
                "percent_complete": 75.0,
                "completed_labs": 15,
                "total_labs": 20,
                "completed_lessons": 45,
                "total_lessons": 60,
                "last_activity": "2026-09-29T12:00:00Z",
                "status": "In Progress",
            }
        ],
    }

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers.get("Authorization") == "Bearer valid_live_token"
        return httpx.Response(
            status_code=200,
            headers={"Content-Type": "application/json"},
            content=json.dumps(payload).encode("utf-8"),
        )

    transport = httpx.MockTransport(handler)
    http_client = httpx.AsyncClient(
        transport=transport, base_url="https://api.kodekloud.com/api/v1"
    )

    settings = Settings(session_credential="Bearer valid_live_token", use_mock=False)
    client = KodeKloudClient(settings=settings, http_client=http_client)

    result = await client.get_course_progress()
    assert result.total_courses_enrolled == 1
    assert result.courses[0].course_title == "Live CKA Course"
    assert result.courses[0].percent_complete == 75.0


@pytest.mark.asyncio
async def test_live_401_session_expired() -> None:
    """Verify HTTP 401 returns user-friendly SessionExpiredError."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=401,
            headers={"Content-Type": "application/json"},
            json={"error": "Unauthorized token expired"},
        )

    transport = httpx.MockTransport(handler)
    http_client = httpx.AsyncClient(
        transport=transport, base_url="https://api.kodekloud.com/api/v1"
    )

    settings = Settings(session_credential="expired_cookie_val", use_mock=False)
    client = KodeKloudClient(settings=settings, http_client=http_client)

    with pytest.raises(SessionExpiredError) as exc_info:
        await client.list_enrolled_courses()

    assert "KodeKloud session expired or rejected (HTTP 401)" in str(exc_info.value)
    assert "Please log in to your KodeKloud account" in str(exc_info.value)
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_live_403_session_forbidden() -> None:
    """Verify HTTP 403 returns user-friendly SessionExpiredError."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=403,
            headers={"Content-Type": "application/json"},
            json={"error": "Forbidden"},
        )

    transport = httpx.MockTransport(handler)
    http_client = httpx.AsyncClient(
        transport=transport, base_url="https://api.kodekloud.com/api/v1"
    )

    settings = Settings(session_credential="forbidden_cookie_val", use_mock=False)
    client = KodeKloudClient(settings=settings, http_client=http_client)

    with pytest.raises(SessionExpiredError) as exc_info:
        await client.get_active_labs()

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_live_429_rate_limiting_retry_and_exhaustion() -> None:
    """Verify HTTP 429 retries with backoff and raises RateLimitExceededError when exhausted."""
    call_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        return httpx.Response(
            status_code=429,
            headers={"Content-Type": "application/json", "Retry-After": "1"},
            json={"error": "Too Many Requests"},
        )

    transport = httpx.MockTransport(handler)
    http_client = httpx.AsyncClient(
        transport=transport, base_url="https://api.kodekloud.com/api/v1"
    )

    settings = Settings(session_credential="valid_token", use_mock=False)
    client = KodeKloudClient(settings=settings, http_client=http_client)

    with pytest.raises(RateLimitExceededError) as exc_info:
        # Patch client to use tiny backoff to avoid test delays
        await client._request("GET", "/users/me/progress", max_retries=2, backoff_base=0.01)

    assert call_count == 3  # initial attempt + 2 retries
    assert "KodeKloud API rate limit exceeded (HTTP 429)" in str(exc_info.value)


@pytest.mark.asyncio
async def test_live_non_json_response() -> None:
    """Verify HTML response (e.g. login redirect or Cloudflare challenge) raises NonJsonResponseError."""
    html_content = "<!DOCTYPE html><html><head><title>Login</title></head><body>Redirecting to login...</body></html>"

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            headers={"Content-Type": "text/html; charset=utf-8"},
            content=html_content.encode("utf-8"),
        )

    transport = httpx.MockTransport(handler)
    http_client = httpx.AsyncClient(
        transport=transport, base_url="https://api.kodekloud.com/api/v1"
    )

    settings = Settings(session_credential="valid_token", use_mock=False)
    client = KodeKloudClient(settings=settings, http_client=http_client)

    with pytest.raises(NonJsonResponseError) as exc_info:
        await client.list_enrolled_courses()

    assert "Received unexpected non-JSON response from KodeKloud" in str(exc_info.value)
    assert exc_info.value.status_code == 200
    assert "text/html" in exc_info.value.content_type


@pytest.mark.asyncio
async def test_live_schema_drift_graceful_degradation() -> None:
    """Verify response with drifted schema does not crash, but degrades gracefully."""
    drifted_payload = [
        {"id": "course-99", "title": "New Platform Course", "progress": 85.0, "completed_labs": 3},
    ]

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            headers={"Content-Type": "application/json"},
            json=drifted_payload,
        )

    transport = httpx.MockTransport(handler)
    http_client = httpx.AsyncClient(
        transport=transport, base_url="https://api.kodekloud.com/api/v1"
    )

    settings = Settings(session_credential="valid_token", use_mock=False)
    client = KodeKloudClient(settings=settings, http_client=http_client)

    result = await client.get_course_progress()
    # Should not throw exception, but gracefully parse the list of items
    assert result.total_courses_enrolled == 1
    assert result.courses[0].course_id == "course-99"
    assert result.courses[0].course_title == "New Platform Course"
    assert result.courses[0].percent_complete == 85.0


@pytest.mark.asyncio
async def test_live_timeout_raises_network_timeout_error() -> None:
    """Verify httpx.TimeoutException raises NetworkTimeoutError after retries."""

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("Read timed out")

    transport = httpx.MockTransport(handler)
    http_client = httpx.AsyncClient(
        transport=transport, base_url="https://api.kodekloud.com/api/v1"
    )

    settings = Settings(session_credential="valid_token", use_mock=False)
    client = KodeKloudClient(settings=settings, http_client=http_client)

    with pytest.raises(NetworkTimeoutError) as exc_info:
        await client._request("GET", "/users/me/progress", max_retries=1, backoff_base=0.01)

    assert "Request to KodeKloud timed out" in str(exc_info.value)
