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
    EnrolledCoursesResponse,
    LabActionResponse,
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
            "This MCP server connects to the user's KodeKloud learner account. "
            "Use it to review course progress, retrieve module outlines, check active hands-on labs, "
            "track certification milestones (e.g., CKA, CKAD, Terraform), and generate personalized "
            "study schedules. By default, it operates in safe read-only mode."
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
        return await kk_client.get_course_progress(course_name)

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
        return await kk_client.list_enrolled_courses()

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
        return await kk_client.get_course_outline(course_name)

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
        return await kk_client.get_active_labs()

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
        return await kk_client.get_certifications()

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
        return await kk_client.get_learning_summary()

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
            return await kk_client.start_lab(lab_id)

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
            return await kk_client.stop_lab(lab_id)
    else:
        logger.info("Write tools disabled (read-only mode active).")

    # =========================================================================
    # MCP Prompt: study_plan
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

    return server


# Default server instances for MCP development tools (e.g. 'mcp dev src/kodekloud_mcp/server.py')
mcp = create_server()
server = mcp
