"""Pydantic data models for kodekloud-mcp tool responses.

All models represent structured JSON returned to AI clients (Claude Desktop,
ChatGPT, Cursor, etc.). Configured to tolerate extra fields gracefully.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class BaseResponseModel(BaseModel):
    """Base response model allowing extra fields to prevent failure on schema drift."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    error: str | None = Field(
        default=None,
        description="Error message if the operation or upstream request failed.",
    )
    warning: str | None = Field(
        default=None,
        description="Diagnostic warning or configuration guidance message.",
    )


# =============================================================================
# Tool 1: Course Progress
# =============================================================================
class CourseProgressItem(BaseResponseModel):
    """Detailed progress metrics for a single course."""

    course_id: str = Field(description="Unique identifier or slug of the course.")
    course_title: str = Field(description="Display title of the course.")
    category: str = Field(
        default="DevOps", description="Course category (e.g. Kubernetes, Cloud, Linux)."
    )
    percent_complete: float = Field(
        description="Percentage of the course completed (0.0 to 100.0)."
    )
    completed_labs: int = Field(
        default=0, description="Number of completed hands-on lab exercises."
    )
    total_labs: int = Field(
        default=0, description="Total number of hands-on lab exercises in the course."
    )
    completed_lessons: int = Field(default=0, description="Number of completed lessons/lectures.")
    total_lessons: int = Field(
        default=0, description="Total number of lessons/lectures in the course."
    )
    last_activity: str | None = Field(
        default=None,
        description="ISO timestamp or date string of the learner's last activity in this course.",
    )
    status: str = Field(
        default="In Progress",
        description="Status: 'Not Started', 'In Progress', or 'Completed'.",
    )


class CourseProgressResponse(BaseResponseModel):
    """Response returned by get_course_progress."""

    total_courses_enrolled: int = Field(description="Total number of enrolled courses.")
    average_progress_percent: float = Field(
        description="Overall completion percentage across all courses."
    )
    courses: list[CourseProgressItem] = Field(
        default_factory=list,
        description="List of course progress records matching the query.",
    )
    raw_data: dict[str, Any] | None = Field(
        default=None,
        description="Raw upstream payload if schema drift was detected.",
    )


# =============================================================================
# Tool 2: Enrolled Courses
# =============================================================================
class EnrolledCourseItem(BaseResponseModel):
    """Overview of an enrolled course."""

    course_id: str = Field(description="Unique identifier or slug for the course.")
    title: str = Field(description="Official title of the course.")
    category: str = Field(
        default="DevOps", description="Category or domain (e.g. Kubernetes, AWS, Terraform)."
    )
    status: str = Field(
        description="Enrollment or completion status (e.g., 'In Progress', 'Completed')."
    )
    difficulty: str = Field(
        default="Intermediate", description="Level: Beginner, Intermediate, or Advanced."
    )
    total_hours: float | None = Field(
        default=None, description="Estimated total hours to complete."
    )
    thumbnail_url: str | None = Field(
        default=None, description="Course cover image URL if available."
    )


class EnrolledCoursesResponse(BaseResponseModel):
    """Response returned by list_enrolled_courses."""

    count: int = Field(description="Total count of enrolled courses.")
    courses: list[EnrolledCourseItem] = Field(
        default_factory=list,
        description="List of enrolled courses.",
    )


# =============================================================================
# Tool 3: Course Outline
# =============================================================================
class LessonItem(BaseResponseModel):
    """An individual lesson, lecture, lab, or quiz."""

    lesson_id: str = Field(description="Unique identifier for the lesson.")
    title: str = Field(description="Title of the lesson.")
    type: str = Field(
        default="lecture",
        description="Type of item: 'lecture', 'lab', 'quiz', or 'mock_exam'.",
    )
    duration_minutes: int | None = Field(default=None, description="Estimated duration in minutes.")
    completed: bool = Field(
        default=False, description="Whether the learner has completed this lesson."
    )
    lab_id: str | None = Field(
        default=None,
        description="Associated lab environment ID if this lesson is an interactive lab.",
    )


class ModuleOutline(BaseResponseModel):
    """A module or section within a course."""

    module_id: str = Field(description="Identifier for the module.")
    module_title: str = Field(
        description="Title of the module (e.g., 'Cluster Architecture', 'Storage')."
    )
    order: int = Field(default=1, description="Order index of the module within the course.")
    lessons: list[LessonItem] = Field(
        default_factory=list, description="Ordered lessons in this module."
    )
    completed_lessons: int = Field(default=0, description="Completed items count in this module.")
    total_lessons: int = Field(default=0, description="Total items count in this module.")


class CourseOutlineResponse(BaseResponseModel):
    """Response returned by get_course_outline."""

    course_id: str = Field(description="Identifier of the course.")
    course_title: str = Field(description="Title of the course.")
    total_modules: int = Field(description="Total number of modules.")
    total_lessons: int = Field(description="Total number of lessons across all modules.")
    completed_lessons: int = Field(description="Number of completed lessons.")
    next_suggested_lesson: LessonItem | None = Field(
        default=None,
        description="The immediate next uncompleted lesson to guide the learner's study plan.",
    )
    modules: list[ModuleOutline] = Field(
        default_factory=list,
        description="List of modules with lesson breakdowns.",
    )


# =============================================================================
# Tool 4: Active Labs
# =============================================================================
class ActiveLabItem(BaseResponseModel):
    """Details of a running, paused, or stopped interactive lab."""

    lab_id: str = Field(description="Identifier of the lab.")
    lab_title: str = Field(description="Human-readable title of the hands-on lab.")
    course_name: str = Field(description="Associated course name.")
    status: str = Field(description="Lab state: 'Running', 'Paused', or 'Stopped'.")
    remaining_time_minutes: int = Field(
        default=0,
        description="Remaining time before lab auto-termination (in minutes).",
    )
    lab_url: str | None = Field(
        default=None,
        description="Web terminal URL to access the running lab environment.",
    )
    started_at: str | None = Field(default=None, description="ISO timestamp when lab was started.")
    expires_at: str | None = Field(
        default=None, description="ISO timestamp when lab lease expires."
    )


class ActiveLabsResponse(BaseResponseModel):
    """Response returned by get_active_labs."""

    count: int = Field(description="Count of currently active or provisioned labs.")
    active_labs: list[ActiveLabItem] = Field(
        default_factory=list,
        description="List of active lab sessions.",
    )


# =============================================================================
# Tool 5: Certifications
# =============================================================================
class CertificationItem(BaseResponseModel):
    """A certification track or learning path."""

    cert_id: str = Field(
        description="Identifier for the certification (e.g., 'CKA', 'CKAD', 'TERRAFORM')."
    )
    title: str = Field(description="Full name of the certification.")
    issuing_body: str = Field(
        default="Linux Foundation",
        description="Vendor/Body (e.g. Linux Foundation, HashiCorp, AWS).",
    )
    readiness_percent: float = Field(
        description="Exam readiness score (0.0 to 100.0) calculated from lecture + lab completion.",
    )
    mock_exams_completed: int = Field(default=0, description="Completed mock exam attempts.")
    total_mock_exams: int = Field(default=0, description="Total mock exams available in path.")
    status: str = Field(
        default="In Preparation",
        description="Status: 'Not Started', 'In Preparation', or 'Exam Ready'.",
    )
    target_date: str | None = Field(
        default=None, description="Learner's target exam completion date."
    )


class CertificationsResponse(BaseResponseModel):
    """Response returned by get_certifications."""

    count: int = Field(description="Number of certification tracks tracked.")
    certifications: list[CertificationItem] = Field(
        default_factory=list,
        description="List of tracked certifications and learning paths.",
    )


# =============================================================================
# Tool 6: Learning Summary
# =============================================================================
class LearningStreak(BaseResponseModel):
    """Learner's daily study streak information."""

    current_streak_days: int = Field(default=0, description="Consecutive days studied.")
    longest_streak_days: int = Field(default=0, description="Longest recorded streak in days.")
    last_study_date: str | None = Field(default=None, description="Date of last study session.")


class RecentActivityItem(BaseResponseModel):
    """Recent learning event (lesson finished, lab passed, quiz attempt)."""

    activity_type: str = Field(
        description="Type: 'Lab Completed', 'Lecture Finished', or 'Quiz Passed'."
    )
    title: str = Field(description="Name of the lesson or lab.")
    course_name: str = Field(description="Course the activity belongs to.")
    timestamp: str = Field(description="ISO timestamp of activity.")


class LearningSummaryResponse(BaseResponseModel):
    """A compact digest designed for the chatbot to construct an actionable study plan."""

    learner_name: str = Field(default="Learner", description="Display name of the learner.")
    total_hours_learned: float = Field(
        description="Total cumulative hours spent learning on KodeKloud."
    )
    total_completed_labs: int = Field(description="Total hands-on labs successfully completed.")
    streak: LearningStreak = Field(description="Current and best study streak metrics.")
    recent_activities: list[RecentActivityItem] = Field(
        default_factory=list,
        description="List of recent learning actions (up to 5).",
    )
    next_suggested_lesson: LessonItem | None = Field(
        default=None,
        description="Recommended next lesson or lab to continue with.",
    )
    next_suggested_course: str | None = Field(
        default=None,
        description="Recommended course for the next study session.",
    )
    pending_labs_count: int = Field(
        default=0,
        description="Number of unfinished labs in active in-progress courses.",
    )


# =============================================================================
# Write Tools: Start/Stop Lab
# =============================================================================
class LabActionResponse(BaseResponseModel):
    """Response returned when starting or stopping a lab."""

    success: bool = Field(description="Whether the requested lab action succeeded.")
    lab_id: str = Field(description="ID of the lab.")
    status: str = Field(
        description="Current lab status ('Provisioning', 'Running', or 'Terminated')."
    )
    message: str = Field(description="Human-readable result message.")
    lab_url: str | None = Field(default=None, description="Access URL if lab is running.")
    remaining_time_minutes: int | None = Field(
        default=None, description="Initial lease time in minutes."
    )


# =============================================================================
# KodeKloud Engineer (KKE / Project Nautilus) Models
# =============================================================================
class EngineerServerTarget(BaseResponseModel):
    """Server/host information for an assigned KodeKloud Engineer ticket."""

    hostname: str = Field(description="Target host name (e.g., 'stapp01', 'jump_host', 'stdb01').")
    ip: str | None = Field(default=None, description="Internal IP address of the target host.")
    user: str | None = Field(
        default=None, description="Default SSH/sudo username (e.g. 'steve', 'tony')."
    )
    role: str | None = Field(
        default=None, description="Server role description (e.g. 'App Server 1')."
    )


class EngineerTask(BaseResponseModel):
    """An assigned real-world SysAdmin/DevOps scenario ticket."""

    task_id: str = Field(description="Unique identifier of the task/ticket.")
    title: str = Field(description="Task title (e.g., 'Deploy Nginx as Reverse Proxy').")
    track: str = Field(
        default="DevOps",
        description="Engineering track: 'System Administrator', 'DevOps', 'Cloud', 'Kubernetes'.",
    )
    description: str = Field(description="Full scenario briefing and problem description.")
    acceptance_criteria: list[str] = Field(
        default_factory=list,
        description="List of verification requirements to pass the task.",
    )
    target_servers: list[EngineerServerTarget] = Field(
        default_factory=list,
        description="List of target infrastructure nodes involved in this task.",
    )
    status: str = Field(
        default="In Progress",
        description="Task lifecycle status: 'Assigned', 'In Progress', 'Success', 'Failed', 'Expired'.",
    )
    points: int = Field(default=0, description="XP or points awarded upon successful completion.")
    assigned_at: str | None = Field(
        default=None, description="ISO timestamp when task was assigned."
    )
    deadline: str | None = Field(
        default=None, description="ISO timestamp of task completion deadline."
    )
    time_remaining_hours: float | None = Field(
        default=None, description="Remaining hours before deadline expiration."
    )


class EngineerTaskResponse(BaseResponseModel):
    """Response returned by get_engineer_task."""

    has_active_task: bool = Field(description="True if an active ticket is currently assigned.")
    task: EngineerTask | None = Field(default=None, description="Active task details if present.")
    message: str | None = Field(
        default=None, description="Informational message if no task is active."
    )


class EngineerProfileResponse(BaseResponseModel):
    """Response returned by get_engineer_profile."""

    username: str = Field(description="KodeKloud Engineer username or handle.")
    current_level: str = Field(
        description="Current engineering role/level (e.g. 'DevOps Engineer', 'System Administrator')."
    )
    total_points: int = Field(description="Total cumulative XP/points earned.")
    global_rank: int | None = Field(default=None, description="Position on the global leaderboard.")
    tasks_completed: int = Field(default=0, description="Total successfully validated tasks.")
    tasks_failed: int = Field(default=0, description="Total failed or expired tasks.")
    success_rate_percent: float = Field(
        default=0.0, description="Success rate percentage (0.0 to 100.0)."
    )
    streak_days: int = Field(default=0, description="Consecutive daily task completion streak.")
    eligible_for_promotion: bool = Field(
        default=False, description="Whether learner meets criteria to advance to the next level."
    )
    next_level: str | None = Field(
        default=None,
        description="Next role in career progression path (e.g. 'Senior DevOps Engineer').",
    )


class EngineerHistoryItem(BaseResponseModel):
    """Record of a previously completed, failed, or expired engineer task."""

    task_id: str = Field(description="Identifier of the task.")
    title: str = Field(description="Title of the completed/attempted task.")
    track: str = Field(default="DevOps", description="Engineering track or role.")
    status: str = Field(description="Result status: 'Success', 'Failed', or 'Expired'.")
    points_awarded: int = Field(default=0, description="Points earned for this task.")
    completed_at: str | None = Field(
        default=None, description="ISO timestamp of completion/verification."
    )


class EngineerHistoryResponse(BaseResponseModel):
    """Response returned by list_engineer_history."""

    count: int = Field(description="Total count of historical tasks returned.")
    tasks: list[EngineerHistoryItem] = Field(
        default_factory=list, description="Historical task records."
    )
