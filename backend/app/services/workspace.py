"""Server-side workspace resolution. The frontend renders navigation from this; it never decides access."""

from typing import Any

from sqlalchemy import select

from app.models import Role, UserRole
from app.services.auth_context import AuthContext
from app.services.lookups import section_labels
from app.services.school import school_settings
from app.services.teaching import assignments, class_teacher_sections

STUDENT_MODULES = [
    ("dashboard", None),
    ("profile", None),
    ("attendance", "attendance"),
    ("performance", "academics"),
    ("results", "academics"),
    ("timetable", "timetable"),
    ("fees", "fees"),
    ("announcements", "announcements"),
    ("events", "events"),
    ("documents", "documents"),
    ("messages", "messaging"),
    ("complaints", "complaints"),
    ("feedback", "feedback"),
    ("settings", None),
]


def build(ctx: AuthContext) -> dict[str, Any]:
    db = ctx.db
    enabled = set(school_settings(db, ctx.school_id).enabled_modules)
    roles = list(db.scalars(select(Role.name).join(UserRole, UserRole.role_id == Role.id).where(UserRole.user_id == ctx.user_id)))
    base: dict[str, Any] = {"roles": sorted(roles), "permissions": sorted(ctx.permissions)}
    kind = ctx.user.account_type

    if kind == "student":
        modules = [key for key, needs in STUDENT_MODULES if needs is None or needs in enabled]
        return {**base, "kind": "student", "home": "/erp/student", "modules": modules}

    if kind == "staff":
        modules = ["dashboard"]
        teaching = assignments(db, ctx.staff_id) if ctx.staff_id and ctx.has("teaching.workspace") else []
        ct_sections = class_teacher_sections(db, ctx.staff_id) if ctx.staff_id and ctx.has("teaching.workspace") else []
        if teaching or ct_sections:
            modules += ["timetable", "classes", "attendance", "marks"]
            if "lesson_progress" in enabled:
                modules.append("topics")
            modules += ["support", "complaints"]
            if ct_sections:
                modules.append("class")
        if ctx.has("staff.self_service"):
            modules += ["my-attendance", "leave", "duties"]
        modules += ["announcements", "documents"]
        if ctx.has("finance.view"):
            modules.append("finance")
        if ctx.has("hr.view"):
            modules.append("hr")
        if ctx.has("library.manage"):
            modules.append("library")
        if ctx.has("transport.manage"):
            modules.append("transport")
        modules.append("profile")
        labels = section_labels(db, ct_sections)
        return {
            **base,
            "kind": "staff",
            "home": "/erp/staff",
            "modules": modules,
            "is_teacher": bool(teaching),
            "teaching_assignments": len(teaching),
            "class_teacher_of": [{"section_id": s, "section": labels[s]} for s in ct_sections],
        }

    rules = [
        ("overview", ("mgmt.dashboard.view",)),
        ("academics", ("mgmt.academics.view",)),
        ("staff-performance", ("evaluation.view",)),
        ("attendance", ("mgmt.attendance.view",)),
        ("finance", ("finance.view", "finance.view_summary")),
        ("hr", ("hr.view", "payroll.view")),
        (
            "complaints",
            ("complaints.view_summary", "complaints.view_all", "complaints.view_confidential", "feedback.view_aggregate"),
        ),
        ("reports", ("admissions.view", "mgmt.dashboard.view")),
        ("approvals", ("approvals.decide_leave", "marks.publish", "audit.view")),
        ("config", ("config.view", "config.manage")),
    ]
    modules = [key for key, perms in rules if any(ctx.has(p) for p in perms)] + ["settings"]
    home = "/erp/management" if "overview" in modules else f"/erp/management/{modules[0]}"
    return {**base, "kind": "management", "home": home, "modules": modules}


DEFAULT_HOME = {"student": "/erp/student", "staff": "/erp/staff", "management": "/erp/management"}
