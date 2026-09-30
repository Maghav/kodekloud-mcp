"""FastMCP server implementation for kodekloud-mcp.

Registers all learner tools, conditionally exposes write tools based on security flags,
and provides the 'study_plan' prompt. Compatible with both MCP SDK v1 and v2.
"""

from __future__ import annotations

import logging
import sys

# Support both MCP SDK 2.x (MCPServer) and 1.x (FastMCP)
try:
    from mcp.server.mcpserver import MCPServer as FastMCP
except ImportError:
    from mcp.server.fastmcp import FastMCP  # type: ignore

from kodekloud_mcp.config import Settings
from kodekloud_mcp.kodekloud_client import KodeKloudClient
from kodekloud_mcp.models import (
    ActiveLabsResponse,
    CertificationsResponse,
    CourseOutlineResponse,
    CourseProgressResponse,
    EngineerHistoryResponse,
    EngineerProfileResponse,
    EngineerTaskResponse,
    EnrolledCoursesResponse,
    LabActionResponse,
    LearningStreak,
    LearningSummaryResponse,
)

logger = logging.getLogger("kodekloud_mcp.server")
if not logger.handlers:
    _stderr_handler = logging.StreamHandler(sys.stderr)
    _formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] [kodekloud-mcp] %(message)s")
    _stderr_handler.setFormatter(_formatter)
    logger.addHandler(_stderr_handler)
logger.propagate = False


def create_server(
    settings: Settings | None = None,
    client: KodeKloudClient | None = None,
) -> FastMCP:
    """Instantiate and configure the KodeKloud FastMCP server.

    Args:
        settings: Server configuration settings (defaults to environment variables).
        client: Pre-configured KodeKloudClient instance (optional, created if omitted).

    Returns:
        Configured FastMCP server instance ready for execution.
    """
    cfg = settings or Settings.from_env()
    kk_client = client or KodeKloudClient(settings=cfg)

    server = FastMCP(
        "kodekloud-mcp",
        instructions=(
            "This MCP server connects to the user's KodeKloud learner account and KodeKloud "
            "Engineer simulation platform. Use it to review course progress, retrieve module outlines, "
            "check active hands-on labs, track certification milestones (CKA, CKAD, etc.), as well as "
            "inspect assigned real-world SysAdmin/DevOps tasks, XP standings, and task histories on "
            "KodeKloud Engineer. By default, it operates in safe read-only mode."
        ),
    )

    # =========================================================================
    # Tool 1: Course Progress
    # =========================================================================
    @server.tool()
    async def get_course_progress(
        course_name: str | None = None,
    ) -> CourseProgressResponse:
        """Get completion percentage, completed vs total labs, and last activity.

        Fetches overall progress metrics across all enrolled courses or filters
        specifically for a given course name or ID (e.g. 'CKA' or 'Kubernetes').

        Args:
            course_name: Optional course title or slug to filter progress for.
                         If omitted, returns progress for all enrolled courses.

        Returns:
            CourseProgressResponse with completion percentages and lab counts.
        """
        try:
            return await kk_client.get_course_progress(course_name)
        except Exception as exc:
            logger.error("Error in get_course_progress: %s", exc)
            return CourseProgressResponse(
                total_courses_enrolled=0,
                average_progress_percent=0.0,
                courses=[],
                error=str(exc),
            )

    # =========================================================================
    # Tool 2: Enrolled Courses
    # =========================================================================
    @server.tool()
    async def list_enrolled_courses() -> EnrolledCoursesResponse:
        """List all courses the user is currently enrolled in on KodeKloud.

        Returns titles, categories (Kubernetes, Cloud, Linux, IaC), difficulty
        levels, and current enrollment status (In Progress, Completed, Not Started).

        Returns:
            EnrolledCoursesResponse containing the list of enrolled courses.
        """
        try:
            return await kk_client.list_enrolled_courses()
        except Exception as exc:
            logger.error("Error in list_enrolled_courses: %s", exc)
            return EnrolledCoursesResponse(count=0, courses=[], error=str(exc))

    # =========================================================================
    # Tool 3: Course Outline
    # =========================================================================
    @server.tool()
    async def get_course_outline(course_name: str) -> CourseOutlineResponse:
        """Retrieve course modules, lessons, and labs with completion status.

        Provides a detailed syllabus breakdown showing which lectures and hands-on
        labs have been completed, and indicates the next suggested lesson to help
        the learner identify exactly what to study next.

        Args:
            course_name: Title, slug, or ID of the course (e.g. 'CKA', 'Docker').

        Returns:
            CourseOutlineResponse with modules, lessons, and next suggested item.
        """
        try:
            return await kk_client.get_course_outline(course_name)
        except Exception as exc:
            logger.error("Error in get_course_outline: %s", exc)
            return CourseOutlineResponse(
                course_id=course_name,
                course_title=course_name,
                total_modules=0,
                total_lessons=0,
                completed_lessons=0,
                modules=[],
                error=str(exc),
            )

    # =========================================================================
    # Tool 4: Active Labs
    # =========================================================================
    @server.tool()
    async def get_active_labs() -> ActiveLabsResponse:
        """List active interactive hands-on labs with status and remaining lease time.

        Inspects currently provisioned or running lab sessions (Running, Paused,
        Stopped), remaining time before automatic expiration, and access URLs.

        Returns:
            ActiveLabsResponse with active lab session details.
        """
        try:
            return await kk_client.get_active_labs()
        except Exception as exc:
            logger.error("Error in get_active_labs: %s", exc)
            return ActiveLabsResponse(count=0, active_labs=[], error=str(exc))

    # =========================================================================
    # Tool 5: Certifications
    # =========================================================================
    @server.tool()
    async def get_certifications() -> CertificationsResponse:
        """Track active certification paths, mock exams, and exam readiness scores.

        Provides exam preparation progress for certifications like CKA, CKAD, CKS,
        HashiCorp Terraform Associate, and AWS, including mock exam completion
        rates and target exam dates.

        Returns:
            CertificationsResponse with tracked certifications and readiness.
        """
        try:
            return await kk_client.get_certifications()
        except Exception as exc:
            logger.error("Error in get_certifications: %s", exc)
            return CertificationsResponse(count=0, certifications=[], error=str(exc))

    # =========================================================================
    # Tool 6: Learning Summary
    # =========================================================================
    @server.tool()
    async def get_learning_summary() -> LearningSummaryResponse:
        """Get a compact digest of learning streaks, recent activity, and study stats.

        Designed specifically for constructing personalized study schedules.
        Includes current consecutive study streak in days, total hours learned,
        recent activity history, count of pending labs, and next suggested lesson.

        Returns:
            LearningSummaryResponse compact learner profile digest.
        """
        try:
            return await kk_client.get_learning_summary()
        except Exception as exc:
            logger.error("Error in get_learning_summary: %s", exc)
            return LearningSummaryResponse(
                learner_name="KodeKloud Learner",
                total_hours_learned=0.0,
                total_completed_labs=0,
                streak=LearningStreak(current_streak_days=0, longest_streak_days=0),
                recent_activities=[],
                error=str(exc),
            )

    # =========================================================================
    # Tool 7: KodeKloud Engineer Task (KKE / Project Nautilus)
    # =========================================================================
    @server.tool()
    async def get_engineer_task() -> EngineerTaskResponse:
        """Fetch the current active assigned task/ticket on KodeKloud Engineer.

        Retrieves the active ticket scenario (SysAdmin, DevOps, Cloud, Kubernetes),
        including task description, acceptance criteria, target servers (e.g. stapp01, jump_host),
        assigned credentials/usernames, points, and remaining deadline hours.

        Returns:
            EngineerTaskResponse with active task details or empty notification.
        """
        try:
            return await kk_client.get_engineer_task()
        except Exception as exc:
            logger.error("Error in get_engineer_task: %s", exc)
            return EngineerTaskResponse(
                has_active_task=False,
                task=None,
                message=str(exc),
                error=str(exc),
            )

    # =========================================================================
    # Tool 8: KodeKloud Engineer Profile
    # =========================================================================
    @server.tool()
    async def get_engineer_profile() -> EngineerProfileResponse:
        """Retrieve user profile, career track level, XP, and rank on KodeKloud Engineer.

        Returns current engineering role (e.g. 'DevOps Engineer', 'System Administrator'),
        total points/XP, global leaderboard rank, tasks completed, tasks failed,
        success rate, and promotion eligibility.

        Returns:
            EngineerProfileResponse with standing and career metrics.
        """
        try:
            return await kk_client.get_engineer_profile()
        except Exception as exc:
            logger.error("Error in get_engineer_profile: %s", exc)
            return EngineerProfileResponse(
                username="engineer",
                current_level="DevOps Engineer",
                total_points=0,
                error=str(exc),
            )

    # =========================================================================
    # Tool 9: KodeKloud Engineer Task History
    # =========================================================================
    @server.tool()
    async def list_engineer_history(
        limit: int = 10,
        status: str | None = None,
    ) -> EngineerHistoryResponse:
        """List historical tasks, tickets, and results on KodeKloud Engineer.

        Inspects past completed, failed, or expired tasks, tracks, points awarded,
        and completion timestamps.

        Args:
            limit: Maximum number of historical task records to return (default: 10).
            status: Optional filter by status: 'Success', 'Failed', or 'Expired'.

        Returns:
            EngineerHistoryResponse with historical task records.
        """
        try:
            return await kk_client.list_engineer_history(limit=limit, status=status)
        except Exception as exc:
            logger.error("Error in list_engineer_history: %s", exc)
            return EngineerHistoryResponse(count=0, tasks=[], error=str(exc))

    # =========================================================================
    # Write Tools: Conditionally Registered (Disabled unless enabled)
    # =========================================================================
    if cfg.enable_write_tools:
        logger.info(
            "Registering write tools (start_lab, stop_lab) as KODEKLOUD_ENABLE_WRITE_TOOLS=true"
        )

        @server.tool()
        async def start_lab(lab_id: str) -> LabActionResponse:
            """Launch and provision an interactive hands-on lab environment.

            NOTE: This tool changes state on KodeKloud and is only available when
            KODEKLOUD_ENABLE_WRITE_TOOLS is enabled.

            Args:
                lab_id: Identifier of the lab to launch.

            Returns:
                LabActionResponse confirming startup status and web terminal URL.
            """
            try:
                return await kk_client.start_lab(lab_id)
            except Exception as exc:
                logger.error("Error in start_lab: %s", exc)
                return LabActionResponse(
                    success=False,
                    lab_id=lab_id,
                    status="Failed",
                    message=str(exc),
                    error=str(exc),
                )

        @server.tool()
        async def stop_lab(lab_id: str) -> LabActionResponse:
            """Stop and clean up an active interactive hands-on lab environment.

            NOTE: This tool changes state on KodeKloud and is only available when
            KODEKLOUD_ENABLE_WRITE_TOOLS is enabled.

            Args:
                lab_id: Identifier of the active lab to terminate.

            Returns:
                LabActionResponse confirming lab termination.
            """
            try:
                return await kk_client.stop_lab(lab_id)
            except Exception as exc:
                logger.error("Error in stop_lab: %s", exc)
                return LabActionResponse(
                    success=False,
                    lab_id=lab_id,
                    status="Failed",
                    message=str(exc),
                    error=str(exc),
                )
    else:
        logger.info("Write tools disabled (read-only mode active).")

    # =========================================================================
    # MCP Prompt 1: study_plan
    # =========================================================================
    @server.prompt()
    def study_plan(goal: str) -> str:
        """Generate a personalized, milestone-driven KodeKloud study plan.

        Instructs the AI assistant to inspect the learner's progress across courses,
        certifications, outlines, and active labs, and produce a structured weekly plan.

        Args:
            goal: The learner's target goal (e.g. 'CKA in 8 weeks', 'Terraform in 1 month').
        """
        return (
            f"You are a dedicated KodeKloud learning mentor and DevOps coach.\n"
            f"The learner's objective is: '{goal}'.\n\n"
            f"Please take the following steps to construct a tailored, realistic study plan:\n"
            f"1. Call `get_learning_summary()` to inspect the learner's current streak, total hours, and recent activity.\n"
            f"2. Call `get_course_progress()` and `get_certifications()` to determine current completion percentages and exam readiness.\n"
            f"3. Call `get_course_outline(course_name=...)` for the relevant target courses to identify remaining modules and pending labs.\n"
            f"4. Call `get_active_labs()` to see if any lab is currently running.\n"
            f"5. Produce a comprehensive, week-by-week study roadmap that includes:\n"
            f"   - Target weekly milestone and core concepts.\n"
            f"   - Specific video lecture topics and hands-on lab exercises.\n"
            f"   - Dedicated time for mock exams, troubleshooting drills, and review.\n"
            f"   - Tips for keeping their study streak active.\n"
            f"Present the plan in a clear, encouraging markdown table or weekly breakdown."
        )

    # =========================================================================
    # MCP Prompt 2: troubleshoot_engineer_task
    # =========================================================================
    @server.prompt()
    def troubleshoot_engineer_task() -> str:
        """Act as a Senior DevOps Tech Lead to guide troubleshooting for an active Engineer task.

        Instructs the AI assistant to inspect the current assigned KodeKloud Engineer
        ticket via get_engineer_task and guide the learner through investigative steps
        without giving away the complete solution directly.
        """
        return (
            "You are a Senior DevOps Lead and mentor at xFusionCorp Industries guiding a junior engineer.\n"
            "Your goal is to help them successfully solve their active KodeKloud Engineer ticket while building "
            "deep, lasting troubleshooting skills.\n\n"
            "Please follow these pedagogical guidelines:\n"
            "1. Call `get_engineer_task()` to inspect the active ticket, scenario description, target servers, "
            "and acceptance criteria.\n"
            "2. Break down the task into logical phases: Exploration & Diagnosis -> Implementation -> Verification.\n"
            "3. Provide targeted diagnostic commands (e.g., `systemctl status`, `journalctl -u`, `curl`, `netstat`, "
            "`kubectl describe pod`) so the learner can inspect server state themselves.\n"
            "4. Do NOT simply dump the final answer or configuration file; explain the rationale, configuration syntax, "
            "and gotchas (such as firewalls, SELinux, permissions, or port bindings).\n"
            "5. Walk through verification steps to ensure all acceptance criteria pass before they click 'Finish' or 'Confirm'."
        )

    return server


def create_mcp_asgi_app(
    server: FastMCP,
    settings: Settings | None = None,
):
    """Create a unified Starlette ASGI application supporting both Streamable HTTP and SSE transports.

    Endpoints:
    - GET /: Returns server status and available transport endpoints.
    - POST /: Routes directly to Streamable HTTP handler (for root-configured clients).
    - GET /health: Health check endpoint.
    - GET /sse: MCP Server-Sent Events stream (for ChatGPT and legacy SSE clients).
    - POST /messages: SSE session message receiver.
    - POST /mcp & GET /mcp: MCP Streamable HTTP endpoint (for Claude and Gemini).
    """
    from starlette.applications import Starlette
    from starlette.middleware import Middleware
    from starlette.middleware.cors import CORSMiddleware
    from starlette.requests import Request
    from starlette.responses import JSONResponse, Response
    from starlette.routing import Route

    cfg = settings or Settings.from_env()

    # Configure transport security if supported by the MCP SDK
    sec_settings = None
    try:
        from mcp.server.transport_security import TransportSecuritySettings

        sec_settings = TransportSecuritySettings(
            enable_dns_rebinding_protection=False,
            allowed_hosts=["*"],
            allowed_origins=["*"],
        )
    except ImportError:
        pass

    ts = getattr(server.settings, "transport_security", None)
    if ts is not None:
        if hasattr(ts, "enable_dns_rebinding_protection"):
            ts.enable_dns_rebinding_protection = False
        if hasattr(ts, "allowed_hosts"):
            ts.allowed_hosts = ["*"]
        if hasattr(ts, "allowed_origins"):
            ts.allowed_origins = ["*"]

    import inspect

    stream_kwargs: dict[str, object] = {}
    sse_kwargs: dict[str, object] = {}

    try:
        sig_stream = inspect.signature(server.streamable_http_app)
        if "transport_security" in sig_stream.parameters and sec_settings is not None:
            stream_kwargs["transport_security"] = sec_settings
        if "host" in sig_stream.parameters:
            stream_kwargs["host"] = "0.0.0.0"
    except Exception:
        pass

    try:
        sig_sse = inspect.signature(server.sse_app)
        if "transport_security" in sig_sse.parameters and sec_settings is not None:
            sse_kwargs["transport_security"] = sec_settings
        if "host" in sig_sse.parameters:
            sse_kwargs["host"] = "0.0.0.0"
    except Exception:
        pass

    stream_app = server.streamable_http_app(**stream_kwargs)
    sse_app = server.sse_app(**sse_kwargs)

    routes: list[Route] = []

    # Find the Streamable HTTP ASGI endpoint handler
    stream_asgi = None
    for r in stream_app.routes:
        if getattr(r, "path", None) == "/mcp":
            stream_asgi = r.endpoint
            break

    async def root_info(request: Request) -> Response:
        return JSONResponse({
            "name": "kodekloud-mcp",
            "status": "healthy",
            "version": "0.1.0",
            "endpoints": {
                "streamable_http": "/mcp",
                "sse": "/sse",
                "messages": "/messages",
                "health": "/health",
            },
            "connectors": {
                "claude": "Use Streamable HTTP at /mcp (e.g. https://your-domain/mcp)",
                "gemini": "Use Streamable HTTP at /mcp (e.g. https://your-domain/mcp)",
                "chatgpt": "Use https://your-domain/mcp or https://your-domain/sse",
            },
        })

    async def health_handler(request: Request) -> Response:
        return JSONResponse({"status": "ok"})

    routes.append(Route("/", endpoint=root_info, methods=["GET", "HEAD"]))
    if stream_asgi:
        # Route POST / to Streamable HTTP (for clients configured with root URL)
        routes.append(Route("/", endpoint=stream_asgi, methods=["POST"]))
        # Route POST /sse to Streamable HTTP (for modern MCP clients like ChatGPT sending POST /sse)
        routes.append(Route("/sse", endpoint=stream_asgi, methods=["POST"]))
    routes.append(Route("/health", endpoint=health_handler, methods=["GET", "HEAD"]))

    # Mount SSE routes (GET /sse, /messages)
    for r in sse_app.routes:
        routes.append(r)

    # Mount Streamable HTTP routes (/mcp)
    for r in stream_app.routes:
        if getattr(r, "path", None) not in [getattr(existing, "path", None) for existing in routes]:
            routes.append(r)

    lifespan_ctx = None
    if hasattr(stream_app, "router") and hasattr(stream_app.router, "lifespan_context"):
        lifespan_ctx = stream_app.router.lifespan_context

    middleware = [
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
        )
    ]

    return Starlette(
        debug=cfg.log_level.upper() == "DEBUG",
        routes=routes,
        middleware=middleware,
        lifespan=lifespan_ctx,
    )


# Default server instances for MCP development tools (e.g. 'mcp dev src/kodekloud_mcp/server.py')
mcp = create_server()
server = mcp
