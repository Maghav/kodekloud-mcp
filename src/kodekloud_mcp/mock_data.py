"""Realistic mock datasets for offline development, demonstration, and automated testing.

Provides authentic KodeKloud course titles, realistic progress percentages, outlines,
active labs, certification preparation trackers, and learning streaks.
"""

from kodekloud_mcp.models import (
    ActiveLabItem,
    ActiveLabsResponse,
    CertificationItem,
    CertificationsResponse,
    CourseOutlineResponse,
    CourseProgressItem,
    CourseProgressResponse,
    EnrolledCourseItem,
    EnrolledCoursesResponse,
    LabActionResponse,
    LearningStreak,
    LearningSummaryResponse,
    LessonItem,
    ModuleOutline,
    RecentActivityItem,
)

# -----------------------------------------------------------------------------
# Mock Enrolled Courses
# -----------------------------------------------------------------------------
MOCK_ENROLLED_COURSES: list[EnrolledCourseItem] = [
    EnrolledCourseItem(
        course_id="cka-certified-kubernetes-administrator",
        title="Certified Kubernetes Administrator (CKA)",
        category="Kubernetes",
        status="In Progress",
        difficulty="Intermediate",
        total_hours=22.5,
        thumbnail_url="https://assets.kodekloud.com/courses/cka.png",
    ),
    EnrolledCourseItem(
        course_id="docker-for-beginners",
        title="Docker Training Course for the Absolute Beginner",
        category="Containers",
        status="Completed",
        difficulty="Beginner",
        total_hours=8.0,
        thumbnail_url="https://assets.kodekloud.com/courses/docker.png",
    ),
    EnrolledCourseItem(
        course_id="terraform-associate-certification",
        title="HashiCorp Certified: Terraform Associate",
        category="Infrastructure as Code",
        status="In Progress",
        difficulty="Intermediate",
        total_hours=14.0,
        thumbnail_url="https://assets.kodekloud.com/courses/terraform.png",
    ),
    EnrolledCourseItem(
        course_id="ckad-kubernetes-application-developer",
        title="Certified Kubernetes Application Developer (CKAD)",
        category="Kubernetes",
        status="Not Started",
        difficulty="Intermediate",
        total_hours=18.0,
        thumbnail_url="https://assets.kodekloud.com/courses/ckad.png",
    ),
    EnrolledCourseItem(
        course_id="linux-basics",
        title="Linux Basics Course",
        category="Linux",
        status="Completed",
        difficulty="Beginner",
        total_hours=6.5,
        thumbnail_url="https://assets.kodekloud.com/courses/linux.png",
    ),
]

# -----------------------------------------------------------------------------
# Mock Course Progress
# -----------------------------------------------------------------------------
MOCK_COURSE_PROGRESS: dict[str, CourseProgressItem] = {
    "cka-certified-kubernetes-administrator": CourseProgressItem(
        course_id="cka-certified-kubernetes-administrator",
        course_title="Certified Kubernetes Administrator (CKA)",
        category="Kubernetes",
        percent_complete=68.5,
        completed_labs=24,
        total_labs=35,
        completed_lessons=74,
        total_lessons=108,
        last_activity="2026-09-29T18:42:00Z",
        status="In Progress",
    ),
    "docker-for-beginners": CourseProgressItem(
        course_id="docker-for-beginners",
        course_title="Docker Training Course for the Absolute Beginner",
        category="Containers",
        percent_complete=100.0,
        completed_labs=15,
        total_labs=15,
        completed_lessons=42,
        total_lessons=42,
        last_activity="2026-09-15T11:20:00Z",
        status="Completed",
    ),
    "terraform-associate-certification": CourseProgressItem(
        course_id="terraform-associate-certification",
        course_title="HashiCorp Certified: Terraform Associate",
        category="Infrastructure as Code",
        percent_complete=42.0,
        completed_labs=8,
        total_labs=20,
        completed_lessons=26,
        total_lessons=62,
        last_activity="2026-09-28T14:15:00Z",
        status="In Progress",
    ),
    "ckad-kubernetes-application-developer": CourseProgressItem(
        course_id="ckad-kubernetes-application-developer",
        course_title="Certified Kubernetes Application Developer (CKAD)",
        category="Kubernetes",
        percent_complete=0.0,
        completed_labs=0,
        total_labs=28,
        completed_lessons=0,
        total_lessons=85,
        last_activity=None,
        status="Not Started",
    ),
    "linux-basics": CourseProgressItem(
        course_id="linux-basics",
        course_title="Linux Basics Course",
        category="Linux",
        percent_complete=100.0,
        completed_labs=10,
        total_labs=10,
        completed_lessons=30,
        total_lessons=30,
        last_activity="2026-08-10T09:30:00Z",
        status="Completed",
    ),
}

# -----------------------------------------------------------------------------
# Mock Outlines
# -----------------------------------------------------------------------------
MOCK_CKA_MODULES: list[ModuleOutline] = [
    ModuleOutline(
        module_id="mod-1",
        module_title="Core Concepts & Architecture",
        order=1,
        completed_lessons=6,
        total_lessons=6,
        lessons=[
            LessonItem(
                lesson_id="les-101",
                title="Kubernetes Cluster Architecture",
                type="lecture",
                duration_minutes=15,
                completed=True,
            ),
            LessonItem(
                lesson_id="les-102",
                title="ETCD in Depth",
                type="lecture",
                duration_minutes=12,
                completed=True,
            ),
            LessonItem(
                lesson_id="les-103",
                title="Kube-API Server",
                type="lecture",
                duration_minutes=14,
                completed=True,
            ),
            LessonItem(
                lesson_id="les-104",
                title="Kube Controller Manager & Scheduler",
                type="lecture",
                duration_minutes=10,
                completed=True,
            ),
            LessonItem(
                lesson_id="les-105",
                title="Kubelet and Kube-proxy",
                type="lecture",
                duration_minutes=11,
                completed=True,
            ),
            LessonItem(
                lesson_id="les-106",
                title="Lab - Architecture Inspection",
                type="lab",
                duration_minutes=30,
                completed=True,
                lab_id="lab-arch-1",
            ),
        ],
    ),
    ModuleOutline(
        module_id="mod-2",
        module_title="Scheduling & Node Selection",
        order=2,
        completed_lessons=5,
        total_lessons=5,
        lessons=[
            LessonItem(
                lesson_id="les-201",
                title="Manual Scheduling",
                type="lecture",
                duration_minutes=10,
                completed=True,
            ),
            LessonItem(
                lesson_id="les-202",
                title="Labels and Selectors",
                type="lecture",
                duration_minutes=8,
                completed=True,
            ),
            LessonItem(
                lesson_id="les-203",
                title="Taints and Tolerations",
                type="lecture",
                duration_minutes=12,
                completed=True,
            ),
            LessonItem(
                lesson_id="les-204",
                title="Node Affinity",
                type="lecture",
                duration_minutes=14,
                completed=True,
            ),
            LessonItem(
                lesson_id="les-205",
                title="Lab - Node Affinity & Taints",
                type="lab",
                duration_minutes=35,
                completed=True,
                lab_id="lab-sched-1",
            ),
        ],
    ),
    ModuleOutline(
        module_id="mod-3",
        module_title="Cluster Maintenance & Upgrades",
        order=3,
        completed_lessons=3,
        total_lessons=5,
        lessons=[
            LessonItem(
                lesson_id="les-301",
                title="OS Upgrades and Node Drain",
                type="lecture",
                duration_minutes=12,
                completed=True,
            ),
            LessonItem(
                lesson_id="les-302",
                title="Kubernetes Software Versions",
                type="lecture",
                duration_minutes=8,
                completed=True,
            ),
            LessonItem(
                lesson_id="les-303",
                title="Cluster Upgrade Process",
                type="lecture",
                duration_minutes=18,
                completed=True,
            ),
            LessonItem(
                lesson_id="les-304",
                title="Lab - Cluster Upgrade with Kubeadm",
                type="lab",
                duration_minutes=45,
                completed=False,
                lab_id="lab-upgrade-1",
            ),
            LessonItem(
                lesson_id="les-305",
                title="Lab - Backup and Restore etcd",
                type="lab",
                duration_minutes=40,
                completed=False,
                lab_id="lab-etcd-restore",
            ),
        ],
    ),
    ModuleOutline(
        module_id="mod-4",
        module_title="Security & RBAC",
        order=4,
        completed_lessons=0,
        total_lessons=6,
        lessons=[
            LessonItem(
                lesson_id="les-401",
                title="Authentication & TLS in K8s",
                type="lecture",
                duration_minutes=20,
                completed=False,
            ),
            LessonItem(
                lesson_id="les-402",
                title="TLS Certificates API",
                type="lecture",
                duration_minutes=15,
                completed=False,
            ),
            LessonItem(
                lesson_id="les-403",
                title="Kubeconfig Management",
                type="lecture",
                duration_minutes=12,
                completed=False,
            ),
            LessonItem(
                lesson_id="les-404",
                title="Role-Based Access Control (RBAC)",
                type="lecture",
                duration_minutes=16,
                completed=False,
            ),
            LessonItem(
                lesson_id="les-405",
                title="Lab - RBAC Roles and RoleBindings",
                type="lab",
                duration_minutes=40,
                completed=False,
                lab_id="lab-rbac-1",
            ),
            LessonItem(
                lesson_id="les-406",
                title="Lab - Certificates API",
                type="lab",
                duration_minutes=35,
                completed=False,
                lab_id="lab-cert-1",
            ),
        ],
    ),
    ModuleOutline(
        module_id="mod-5",
        module_title="Mock Exams & Final Preparation",
        order=5,
        completed_lessons=0,
        total_lessons=3,
        lessons=[
            LessonItem(
                lesson_id="les-501",
                title="CKA Ultimate Mock Exam 1",
                type="mock_exam",
                duration_minutes=120,
                completed=False,
                lab_id="lab-mock-1",
            ),
            LessonItem(
                lesson_id="les-502",
                title="CKA Ultimate Mock Exam 2",
                type="mock_exam",
                duration_minutes=120,
                completed=False,
                lab_id="lab-mock-2",
            ),
            LessonItem(
                lesson_id="les-503",
                title="CKA Ultimate Mock Exam 3",
                type="mock_exam",
                duration_minutes=120,
                completed=False,
                lab_id="lab-mock-3",
            ),
        ],
    ),
]

# -----------------------------------------------------------------------------
# Mock Active Labs
# -----------------------------------------------------------------------------
MOCK_ACTIVE_LABS: list[ActiveLabItem] = [
    ActiveLabItem(
        lab_id="lab-upgrade-1",
        lab_title="Lab - Cluster Upgrade with Kubeadm",
        course_name="Certified Kubernetes Administrator (CKA)",
        status="Running",
        remaining_time_minutes=42,
        lab_url="https://labs.kodekloud.com/session/cka-upgrade-node-a7x9",
        started_at="2026-09-29T18:00:00Z",
        expires_at="2026-09-29T19:00:00Z",
    ),
    ActiveLabItem(
        lab_id="lab-tf-vpc-1",
        lab_title="Lab - AWS VPC and Subnets Provisioning",
        course_name="HashiCorp Certified: Terraform Associate",
        status="Paused",
        remaining_time_minutes=25,
        lab_url=None,
        started_at="2026-09-28T14:00:00Z",
        expires_at="2026-09-28T15:00:00Z",
    ),
]

# -----------------------------------------------------------------------------
# Mock Certifications
# -----------------------------------------------------------------------------
MOCK_CERTIFICATIONS: list[CertificationItem] = [
    CertificationItem(
        cert_id="CKA",
        title="Certified Kubernetes Administrator (CKA)",
        issuing_body="Linux Foundation / CNCF",
        readiness_percent=72.0,
        mock_exams_completed=1,
        total_mock_exams=3,
        status="In Preparation",
        target_date="2026-10-31",
    ),
    CertificationItem(
        cert_id="TERRAFORM-ASSOC",
        title="HashiCorp Certified: Terraform Associate (003)",
        issuing_body="HashiCorp",
        readiness_percent=45.0,
        mock_exams_completed=0,
        total_mock_exams=2,
        status="In Preparation",
        target_date="2026-11-30",
    ),
    CertificationItem(
        cert_id="CKAD",
        title="Certified Kubernetes Application Developer (CKAD)",
        issuing_body="Linux Foundation / CNCF",
        readiness_percent=10.0,
        mock_exams_completed=0,
        total_mock_exams=3,
        status="Not Started",
        target_date="2026-12-31",
    ),
]

# -----------------------------------------------------------------------------
# Mock Learning Summary
# -----------------------------------------------------------------------------
MOCK_LEARNING_SUMMARY = LearningSummaryResponse(
    learner_name="KodeKloud Pioneer",
    total_hours_learned=52.5,
    total_completed_labs=49,
    streak=LearningStreak(
        current_streak_days=6,
        longest_streak_days=18,
        last_study_date="2026-09-29",
    ),
    recent_activities=[
        RecentActivityItem(
            activity_type="Lab Completed",
            title="Manual Scheduling and Node Selectors",
            course_name="Certified Kubernetes Administrator (CKA)",
            timestamp="2026-09-29T18:42:00Z",
        ),
        RecentActivityItem(
            activity_type="Lecture Finished",
            title="Cluster Upgrade Process",
            course_name="Certified Kubernetes Administrator (CKA)",
            timestamp="2026-09-29T17:55:00Z",
        ),
        RecentActivityItem(
            activity_type="Lab Completed",
            title="Terraform Remote State with S3 and DynamoDB",
            course_name="HashiCorp Certified: Terraform Associate",
            timestamp="2026-09-28T14:15:00Z",
        ),
        RecentActivityItem(
            activity_type="Quiz Passed",
            title="Terraform State Management Quiz (Score: 100%)",
            course_name="HashiCorp Certified: Terraform Associate",
            timestamp="2026-09-28T13:40:00Z",
        ),
        RecentActivityItem(
            activity_type="Lab Completed",
            title="Taints and Tolerations Deep Dive",
            course_name="Certified Kubernetes Administrator (CKA)",
            timestamp="2026-09-27T20:10:00Z",
        ),
    ],
    next_suggested_lesson=LessonItem(
        lesson_id="les-304",
        title="Lab - Cluster Upgrade with Kubeadm",
        type="lab",
        duration_minutes=45,
        completed=False,
        lab_id="lab-upgrade-1",
    ),
    next_suggested_course="Certified Kubernetes Administrator (CKA)",
    pending_labs_count=23,
)


def get_mock_course_progress(course_name: str | None = None) -> CourseProgressResponse:
    """Retrieve mock progress for a specific course or summary of all enrolled courses."""
    if course_name:
        query_lower = course_name.lower().strip()
        matched = [
            item
            for item in MOCK_COURSE_PROGRESS.values()
            if query_lower in item.course_title.lower() or query_lower in item.course_id.lower()
        ]
        if matched:
            avg_pct = sum(m.percent_complete for m in matched) / len(matched)
            return CourseProgressResponse(
                total_courses_enrolled=len(matched),
                average_progress_percent=round(avg_pct, 1),
                courses=matched,
            )
        # If no exact match, return all with hint or empty
        return CourseProgressResponse(
            total_courses_enrolled=0,
            average_progress_percent=0.0,
            courses=[],
        )

    all_items = list(MOCK_COURSE_PROGRESS.values())
    avg_pct = sum(m.percent_complete for m in all_items) / len(all_items) if all_items else 0.0
    return CourseProgressResponse(
        total_courses_enrolled=len(all_items),
        average_progress_percent=round(avg_pct, 1),
        courses=all_items,
    )


def get_mock_enrolled_courses() -> EnrolledCoursesResponse:
    """Retrieve mock list of enrolled courses."""
    return EnrolledCoursesResponse(
        count=len(MOCK_ENROLLED_COURSES),
        courses=MOCK_ENROLLED_COURSES,
    )


def get_mock_course_outline(course_name: str) -> CourseOutlineResponse:
    """Retrieve mock outline for the requested course."""
    query_lower = course_name.lower().strip()
    title = "Certified Kubernetes Administrator (CKA)"
    cid = "cka-certified-kubernetes-administrator"
    modules = MOCK_CKA_MODULES

    # Find matching course title if possible
    for course in MOCK_ENROLLED_COURSES:
        if query_lower in course.title.lower() or query_lower in course.course_id.lower():
            title = course.title
            cid = course.course_id
            break

    total_lessons = sum(m.total_lessons for m in modules)
    completed_lessons = sum(m.completed_lessons for m in modules)

    # Find first uncompleted lesson
    next_lesson: LessonItem | None = None
    for mod in modules:
        for les in mod.lessons:
            if not les.completed:
                next_lesson = les
                break
        if next_lesson:
            break

    return CourseOutlineResponse(
        course_id=cid,
        course_title=title,
        total_modules=len(modules),
        total_lessons=total_lessons,
        completed_lessons=completed_lessons,
        next_suggested_lesson=next_lesson,
        modules=modules,
    )


def get_mock_active_labs() -> ActiveLabsResponse:
    """Retrieve mock active lab instances."""
    return ActiveLabsResponse(
        count=len(MOCK_ACTIVE_LABS),
        active_labs=MOCK_ACTIVE_LABS,
    )


def get_mock_certifications() -> CertificationsResponse:
    """Retrieve mock certifications and exam readiness milestones."""
    return CertificationsResponse(
        count=len(MOCK_CERTIFICATIONS),
        certifications=MOCK_CERTIFICATIONS,
    )


def get_mock_learning_summary() -> LearningSummaryResponse:
    """Retrieve mock learning summary and streak digest."""
    return MOCK_LEARNING_SUMMARY


def mock_start_lab(lab_id: str) -> LabActionResponse:
    """Simulate starting a lab environment."""
    return LabActionResponse(
        success=True,
        lab_id=lab_id,
        status="Running",
        message=f"Lab '{lab_id}' has been launched and provisioned successfully.",
        lab_url=f"https://labs.kodekloud.com/session/{lab_id}-session-live",
        remaining_time_minutes=60,
    )


def mock_stop_lab(lab_id: str) -> LabActionResponse:
    """Simulate stopping a lab environment."""
    return LabActionResponse(
        success=True,
        lab_id=lab_id,
        status="Terminated",
        message=f"Lab '{lab_id}' has been gracefully stopped and resources cleaned up.",
        lab_url=None,
        remaining_time_minutes=0,
    )
