"""KodeKloud API Client module.

ISOLATION GUARANTEE:
All API endpoint paths, HTTP request orchestration, retry logic, credential handling,
and response parsing are strictly centralized in this file.

To connect to live KodeKloud endpoints:
1. Update the ENDPOINTS dictionary below with verified paths from browser DevTools.
2. Adjust the parser methods (_parse_*) to match your account's exact JSON response schema.
3. Provide your session cookie or JWT in KODEKLOUD_SESSION_COOKIE and set KODEKLOUD_USE_MOCK=false.
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
from typing import Any

import httpx
from pydantic import ValidationError

from kodekloud_mcp import mock_data
from kodekloud_mcp.cache import TTLCache
from kodekloud_mcp.config import Settings, redact_secrets
from kodekloud_mcp.exceptions import (
    AuthenticationMissingError,
    KodeKloudMCPError,
    NetworkTimeoutError,
    NonJsonResponseError,
    RateLimitExceededError,
    SessionExpiredError,
    WriteOperationDisabledError,
)
from kodekloud_mcp.models import (
    ActiveLabItem,
    ActiveLabsResponse,
    CertificationsResponse,
    CourseOutlineResponse,
    CourseProgressItem,
    CourseProgressResponse,
    EnrolledCourseItem,
    EnrolledCoursesResponse,
    LabActionResponse,
    LearningStreak,
    LearningSummaryResponse,
)

# Configure logger strictly to stderr to keep stdout clean for stdio protocol
logger = logging.getLogger("kodekloud_mcp.client")
if not logger.handlers:
    _stderr_handler = logging.StreamHandler(sys.stderr)
    _formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] [kodekloud-mcp] %(message)s")
    _stderr_handler.setFormatter(_formatter)
    logger.addHandler(_stderr_handler)
logger.propagate = False


# =============================================================================
# ENDPOINT DEFINITIONS TABLE
# -----------------------------------------------------------------------------
# TODO: Replace placeholder paths below with verified KodeKloud API endpoints.
# Inspect network calls in Chrome/Firefox DevTools (F12 -> Network -> Fetch/XHR)
# when navigating https://learn.kodekloud.com or https://kodekloud.com.
# =============================================================================
ENDPOINTS: dict[str, str] = {
    # TODO: Verify the endpoint that returns user course progress and completion %
    "user_progress": "/users/me/progress",
    # TODO: Verify the endpoint that returns user's enrolled course catalog
    "enrolled_courses": "/users/me/courses/enrolled",
    # TODO: Verify the endpoint that returns lesson outline/syllabus for a given course ID
    "course_outline": "/courses/{course_id}/outline",
    # TODO: Verify the endpoint that returns currently running/active interactive labs
    "active_labs": "/users/me/labs/active",
    # TODO: Verify the endpoint that returns certification track milestones & mock exams
    "certifications": "/users/me/certifications",
    # TODO: Verify the endpoint that returns daily streak, study hours, and recent activity
    "learning_summary": "/users/me/learning-summary",
    # TODO: Verify the endpoint used to launch/start an interactive lab (write tool)
    "start_lab": "/labs/{lab_id}/start",
    # TODO: Verify the endpoint used to terminate/stop an interactive lab (write tool)
    "stop_lab": "/labs/{lab_id}/stop",
}


class KodeKloudClient:
    """Asynchronous client for KodeKloud.

    Supports both offline mock mode (default) and live authenticated HTTP mode with
    in-memory caching, exponential backoff for rate limits, schema drift tolerance,
    and credential protection.
    """

    def __init__(
        self,
        settings: Settings | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self.settings = settings or Settings.from_env()
        self.cache = TTLCache(default_ttl_seconds=self.settings.cache_ttl_seconds)
        self._custom_http_client = http_client
        self._client: httpx.AsyncClient | None = None

        # Set logger level
        try:
            logger.setLevel(self.settings.log_level.upper())
        except (ValueError, AttributeError):
            logger.setLevel(logging.INFO)

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the underlying httpx.AsyncClient."""
        if self._custom_http_client is not None:
            return self._custom_http_client

        if self._client is None or self._client.is_closed:
            headers = {
                "User-Agent": self.settings.user_agent,
                "Accept": "application/json",
            }
            # Attach auto-detected authentication header
            auth_headers = self.settings.get_auth_headers()
            headers.update(auth_headers)

            self._client = httpx.AsyncClient(
                base_url=self.settings.api_base_url,
                headers=headers,
                timeout=httpx.Timeout(15.0, connect=5.0),
                follow_redirects=False,  # Prevent silently following redirects to login HTML
            )
        return self._client

    async def close(self) -> None:
        """Close underlying HTTP client and release connections."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    def _sanitize_error(self, message: str) -> str:
        """Scrub any credentials from error messages."""
        return redact_secrets(message, self.settings.session_credential)

    # =========================================================================
    # HTTP Request & Resilience Logic
    # =========================================================================
    async def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
        max_retries: int = 3,
        backoff_base: float = 1.0,
    ) -> Any:
        """Execute an HTTP request with exponential backoff on 429 and error mapping.

        Handles:
        - 401 / 403: SessionExpiredError
        - 429: Rate limit backoff (honoring Retry-After)
        - Timeouts: NetworkTimeoutError
        - Non-JSON: NonJsonResponseError
        """
        # In mock mode, this method should not be reached
        if self.settings.use_mock:
            raise RuntimeError("Internal error: _request called while in mock mode.")

        # Ensure credentials are present in live mode
        if not self.settings.session_credential:
            raise AuthenticationMissingError()

        client = await self._get_client()
        attempt = 0

        while True:
            attempt += 1
            try:
                logger.debug("Request: %s %s (attempt %d/%d)", method, path, attempt, max_retries)
                auth_headers = self.settings.get_auth_headers()
                response = await client.request(
                    method=method,
                    url=path,
                    params=params,
                    json=json_body,
                    headers=auth_headers if auth_headers else None,
                )

                # 1. Handle Rate Limiting (HTTP 429)
                if response.status_code == 429:
                    if attempt <= max_retries:
                        retry_after_str = response.headers.get("Retry-After")
                        delay = backoff_base * (2 ** (attempt - 1))
                        if retry_after_str:
                            try:
                                delay = max(delay, float(retry_after_str))
                            except ValueError:
                                pass
                        logger.warning(
                            "HTTP 429 Rate limited by KodeKloud on %s. Retrying in %.1fs (attempt %d/%d)...",
                            path,
                            delay,
                            attempt,
                            max_retries,
                        )
                        await asyncio.sleep(delay)
                        continue
                    else:
                        retry_after_val = None
                        if response.headers.get("Retry-After"):
                            try:
                                retry_after_val = int(response.headers["Retry-After"])
                            except ValueError:
                                pass
                        raise RateLimitExceededError(
                            attempts=max_retries, retry_after=retry_after_val
                        )

                # 2. Handle Session Expiration (HTTP 401 / 403)
                if response.status_code in (401, 403):
                    logger.error(
                        "Session rejected by KodeKloud (HTTP %d). Credential has expired.",
                        response.status_code,
                    )
                    raise SessionExpiredError(status_code=response.status_code)

                # 3. Handle Other HTTP Errors
                if response.is_error:
                    msg = f"KodeKloud API error: HTTP {response.status_code}"
                    logger.error(msg)
                    raise KodeKloudMCPError(self._sanitize_error(f"{msg}: {response.text[:200]}"))

                # 4. Handle Non-JSON Responses (Redirects, Cloudflare pages, HTML)
                content_type = response.headers.get("content-type", "")
                if "application/json" not in content_type.lower():
                    # Attempt JSON parse anyway in case header was omitted
                    try:
                        return response.json()
                    except json.JSONDecodeError:
                        preview = self._sanitize_error(
                            response.text[:200].replace("\n", " ").strip()
                        )
                        raise NonJsonResponseError(
                            status_code=response.status_code,
                            content_type=content_type,
                            preview=preview,
                        ) from None

                try:
                    return response.json()
                except json.JSONDecodeError:
                    preview = self._sanitize_error(response.text[:200].replace("\n", " ").strip())
                    raise NonJsonResponseError(
                        status_code=response.status_code,
                        content_type=content_type,
                        preview=preview,
                    ) from None

            except httpx.TimeoutException:
                if attempt <= max_retries:
                    logger.warning(
                        "Request to %s timed out. Retrying (attempt %d/%d)...",
                        path,
                        attempt,
                        max_retries,
                    )
                    await asyncio.sleep(backoff_base * attempt)
                    continue
                raise NetworkTimeoutError(timeout_seconds=15.0) from None

            except httpx.RequestError as exc:
                sanitized_msg = self._sanitize_error(str(exc))
                raise KodeKloudMCPError(f"Network communication failure: {sanitized_msg}") from exc

    # =========================================================================
    # Tool 1: Course Progress
    # =========================================================================
    async def get_course_progress(self, course_name: str | None = None) -> CourseProgressResponse:
        """Retrieve progress metrics for a course or all enrolled courses."""
        if self.settings.use_mock:
            return mock_data.get_mock_course_progress(course_name)

        cache_key = TTLCache.make_key("get_course_progress", course_name=course_name or "")
        cached = await self.cache.get(cache_key)
        if isinstance(cached, CourseProgressResponse):
            return cached

        path = ENDPOINTS["user_progress"]
        params = {"course_name": course_name} if course_name else None
        data = await self._request("GET", path, params=params)

        # Parse with schema drift tolerance
        result = self._parse_course_progress(data, course_name=course_name)
        await self.cache.set(cache_key, result)
        return result

    def _parse_course_progress(
        self, data: Any, course_name: str | None = None
    ) -> CourseProgressResponse:
        """Parse raw progress data with graceful schema degradation.

        TODO: When the real JSON structure from KodeKloud's endpoint is confirmed,
        adjust this parser to map real field names to CourseProgressResponse.
        """
        try:
            return CourseProgressResponse.model_validate(data)
        except ValidationError as err:
            logger.warning(
                "Schema drift detected in get_course_progress response: %s. Degrading gracefully.",
                err,
            )
            # Graceful fallback: synthesize response or populate raw_data
            items = []
            if isinstance(data, list):
                for raw_item in data:
                    if isinstance(raw_item, dict):
                        items.append(
                            CourseProgressItem(
                                course_id=str(
                                    raw_item.get("id") or raw_item.get("course_id") or "unknown"
                                ),
                                course_title=str(
                                    raw_item.get("title")
                                    or raw_item.get("course_title")
                                    or "Unknown Course"
                                ),
                                percent_complete=float(
                                    raw_item.get("progress")
                                    or raw_item.get("percent_complete")
                                    or 0.0
                                ),
                                completed_labs=int(raw_item.get("completed_labs") or 0),
                                total_labs=int(raw_item.get("total_labs") or 0),
                            )
                        )
            avg = sum(i.percent_complete for i in items) / len(items) if items else 0.0
            return CourseProgressResponse(
                total_courses_enrolled=len(items),
                average_progress_percent=round(avg, 1),
                courses=items,
                raw_data=data if isinstance(data, dict) else {"items": data},
            )

    # =========================================================================
    # Tool 2: Enrolled Courses
    # =========================================================================
    async def list_enrolled_courses(self) -> EnrolledCoursesResponse:
        """Retrieve list of enrolled courses."""
        if self.settings.use_mock:
            return mock_data.get_mock_enrolled_courses()

        cache_key = "list_enrolled_courses"
        cached = await self.cache.get(cache_key)
        if isinstance(cached, EnrolledCoursesResponse):
            return cached

        path = ENDPOINTS["enrolled_courses"]
        data = await self._request("GET", path)

        result = self._parse_enrolled_courses(data)
        await self.cache.set(cache_key, result)
        return result

    def _parse_enrolled_courses(self, data: Any) -> EnrolledCoursesResponse:
        """Parse enrolled courses list with schema drift tolerance.

        TODO: Update field mappings when real endpoint response is verified.
        """
        try:
            return EnrolledCoursesResponse.model_validate(data)
        except ValidationError as err:
            logger.warning("Schema drift detected in list_enrolled_courses response: %s", err)
            raw_courses = data if isinstance(data, list) else data.get("courses", [])
            parsed_list = []
            for item in raw_courses:
                if isinstance(item, dict):
                    parsed_list.append(
                        EnrolledCourseItem(
                            course_id=str(item.get("id") or item.get("course_id") or "unknown"),
                            title=str(item.get("title") or item.get("name") or "Course"),
                            category=str(item.get("category") or "General"),
                            status=str(item.get("status") or "Enrolled"),
                        )
                    )
            return EnrolledCoursesResponse(count=len(parsed_list), courses=parsed_list)

    # =========================================================================
    # Tool 3: Course Outline
    # =========================================================================
    async def get_course_outline(self, course_name: str) -> CourseOutlineResponse:
        """Retrieve syllabus outline and lesson completion status for a course."""
        if self.settings.use_mock:
            return mock_data.get_mock_course_outline(course_name)

        cache_key = TTLCache.make_key("get_course_outline", course_name=course_name)
        cached = await self.cache.get(cache_key)
        if isinstance(cached, CourseOutlineResponse):
            return cached

        path = ENDPOINTS["course_outline"].format(course_id=course_name)
        data = await self._request("GET", path)

        result = self._parse_course_outline(data, course_name)
        await self.cache.set(cache_key, result)
        return result

    def _parse_course_outline(self, data: Any, course_name: str) -> CourseOutlineResponse:
        """Parse course outline with schema drift tolerance.

        TODO: Update field mappings when real outline schema is known.
        """
        try:
            return CourseOutlineResponse.model_validate(data)
        except ValidationError as err:
            logger.warning("Schema drift detected in get_course_outline response: %s", err)
            return CourseOutlineResponse(
                course_id=course_name,
                course_title=course_name,
                total_modules=0,
                total_lessons=0,
                completed_lessons=0,
                modules=[],
            )

    # =========================================================================
    # Tool 4: Active Labs
    # =========================================================================
    async def get_active_labs(self) -> ActiveLabsResponse:
        """Retrieve active or provisioned lab environments."""
        if self.settings.use_mock:
            return mock_data.get_mock_active_labs()

        # Shorter cache for dynamic lab states (max 15 seconds)
        cache_key = "get_active_labs"
        cached = await self.cache.get(cache_key)
        if isinstance(cached, ActiveLabsResponse):
            return cached

        path = ENDPOINTS["active_labs"]
        data = await self._request("GET", path)

        result = self._parse_active_labs(data)
        await self.cache.set(cache_key, result, ttl_seconds=15)
        return result

    def _parse_active_labs(self, data: Any) -> ActiveLabsResponse:
        """Parse active labs with schema drift tolerance.

        TODO: Update field mappings when real lab session schema is known.
        """
        try:
            return ActiveLabsResponse.model_validate(data)
        except ValidationError as err:
            logger.warning("Schema drift detected in get_active_labs response: %s", err)
            labs = []
            raw_labs = data if isinstance(data, list) else data.get("labs", [])
            for item in raw_labs:
                if isinstance(item, dict):
                    labs.append(
                        ActiveLabItem(
                            lab_id=str(item.get("id") or item.get("lab_id") or "lab"),
                            lab_title=str(
                                item.get("title") or item.get("name") or "Interactive Lab"
                            ),
                            course_name=str(item.get("course") or "Course"),
                            status=str(item.get("status") or "Running"),
                            remaining_time_minutes=int(item.get("remaining_time_minutes") or 0),
                        )
                    )
            return ActiveLabsResponse(count=len(labs), active_labs=labs)

    # =========================================================================
    # Tool 5: Certifications
    # =========================================================================
    async def get_certifications(self) -> CertificationsResponse:
        """Retrieve certification tracks, exam readiness, and target milestones."""
        if self.settings.use_mock:
            return mock_data.get_mock_certifications()

        cache_key = "get_certifications"
        cached = await self.cache.get(cache_key)
        if isinstance(cached, CertificationsResponse):
            return cached

        path = ENDPOINTS["certifications"]
        data = await self._request("GET", path)

        result = self._parse_certifications(data)
        await self.cache.set(cache_key, result)
        return result

    def _parse_certifications(self, data: Any) -> CertificationsResponse:
        """Parse certification tracks with schema drift tolerance.

        TODO: Update field mappings when real certification track response is known.
        """
        try:
            return CertificationsResponse.model_validate(data)
        except ValidationError as err:
            logger.warning("Schema drift detected in get_certifications response: %s", err)
            return CertificationsResponse(count=0, certifications=[])

    # =========================================================================
    # Tool 6: Learning Summary
    # =========================================================================
    async def get_learning_summary(self) -> LearningSummaryResponse:
        """Retrieve compact learner digest with streaks and next suggested lesson."""
        if self.settings.use_mock:
            return mock_data.get_mock_learning_summary()

        cache_key = "get_learning_summary"
        cached = await self.cache.get(cache_key)
        if isinstance(cached, LearningSummaryResponse):
            return cached

        path = ENDPOINTS["learning_summary"]
        data = await self._request("GET", path)

        result = self._parse_learning_summary(data)
        await self.cache.set(cache_key, result)
        return result

    def _parse_learning_summary(self, data: Any) -> LearningSummaryResponse:
        """Parse learning summary with schema drift tolerance.

        TODO: Update field mappings when real learning summary schema is known.
        """
        try:
            return LearningSummaryResponse.model_validate(data)
        except ValidationError as err:
            logger.warning("Schema drift detected in get_learning_summary response: %s", err)
            return LearningSummaryResponse(
                learner_name="KodeKloud Learner",
                total_hours_learned=0.0,
                total_completed_labs=0,
                streak=LearningStreak(current_streak_days=0, longest_streak_days=0),
                recent_activities=[],
            )

    # =========================================================================
    # Write Tools: Start & Stop Lab (Disabled unless KODEKLOUD_ENABLE_WRITE_TOOLS=true)
    # =========================================================================
    async def start_lab(self, lab_id: str) -> LabActionResponse:
        """Start or provision an interactive lab environment.

        Requires KODEKLOUD_ENABLE_WRITE_TOOLS=true.
        """
        if not self.settings.enable_write_tools:
            raise WriteOperationDisabledError("start_lab")

        if self.settings.use_mock:
            return mock_data.mock_start_lab(lab_id)

        # Clear cached active labs so next query fetches fresh state
        await self.cache.invalidate("get_active_labs")

        path = ENDPOINTS["start_lab"].format(lab_id=lab_id)
        data = await self._request("POST", path)

        try:
            return LabActionResponse.model_validate(data)
        except ValidationError:
            return LabActionResponse(
                success=True,
                lab_id=lab_id,
                status="Provisioning",
                message=f"Lab '{lab_id}' startup request initiated.",
            )

    async def stop_lab(self, lab_id: str) -> LabActionResponse:
        """Stop or terminate an active interactive lab environment.

        Requires KODEKLOUD_ENABLE_WRITE_TOOLS=true.
        """
        if not self.settings.enable_write_tools:
            raise WriteOperationDisabledError("stop_lab")

        if self.settings.use_mock:
            return mock_data.mock_stop_lab(lab_id)

        # Clear cached active labs so next query fetches fresh state
        await self.cache.invalidate("get_active_labs")

        path = ENDPOINTS["stop_lab"].format(lab_id=lab_id)
        data = await self._request("POST", path)

        try:
            return LabActionResponse.model_validate(data)
        except ValidationError:
            return LabActionResponse(
                success=True,
                lab_id=lab_id,
                status="Terminated",
                message=f"Lab '{lab_id}' stop request completed.",
            )
