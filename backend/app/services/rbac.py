"""Permission catalogue and the default role templates a new school starts with.

Roles are school-owned rows, so each school can adjust them; the codes below are
what the backend checks. Nothing here is trusted from the browser.
"""

from dataclasses import dataclass

PERMISSIONS: dict[str, tuple[str, str]] = {
    # code: (category, description)
    "teaching.workspace": ("academics", "Use the teacher workspace for assigned classes"),
    "staff.self_service": ("staff", "Own attendance, leave, duties and documents"),
    "finance.view": ("finance", "View individual invoices, payments and balances"),
    "finance.view_summary": ("finance", "View aggregated fee collection figures only"),
    "finance.record_payment": ("finance", "Record fee payments against invoices"),
    "hr.view": ("hr", "View the staff directory and leave requests (no salaries)"),
    "payroll.view": ("hr", "View salaries and compensation"),
    "approvals.decide_leave": ("hr", "Approve or reject staff leave"),
    "library.manage": ("operations", "Library module"),
    "transport.manage": ("operations", "Transport module"),
    "mgmt.portal": ("management", "Sign in through the Director / management portal"),
    "mgmt.dashboard.view": ("management", "Executive overview (aggregated)"),
    "mgmt.academics.view": ("academics", "School-wide academic performance"),
    "mgmt.attendance.view": ("academics", "School-wide student and staff attendance"),
    "marks.publish": ("academics", "Publish assessment results to students"),
    "evaluation.view": ("hr", "View teacher evaluation evidence and records"),
    "evaluation.manage": ("hr", "Create and finalise teacher evaluations"),
    "complaints.view_summary": ("complaints", "Complaint counts and categories only"),
    "complaints.view_all": ("complaints", "View non-confidential complaints"),
    "complaints.view_confidential": ("complaints", "View confidential complaints"),
    "complaints.manage": ("complaints", "Assign and update complaints"),
    "feedback.view_aggregate": ("feedback", "Aggregated feedback summaries"),
    "admissions.view": ("admissions", "View admission enquiries"),
    "audit.view": ("governance", "View the audit log"),
    "config.view": ("governance", "View school configuration"),
    "config.manage": ("governance", "Change school configuration"),
}


@dataclass(frozen=True)
class RoleTemplate:
    code: str
    name: str
    kind: str
    permissions: tuple[str, ...]
    description: str = ""


_STAFF = ("staff.self_service",)
_MGMT_BASE = ("mgmt.portal", "mgmt.dashboard.view")

ROLE_TEMPLATES: tuple[RoleTemplate, ...] = (
    # Staff roles (Staff Login). Class-teacher duties come from assignments, not a role.
    RoleTemplate("teacher", "Teacher", "staff", (*_STAFF, "teaching.workspace")),
    RoleTemplate("non_teaching_staff", "Non-teaching Staff", "staff", _STAFF),
    RoleTemplate("finance_staff", "Finance Staff", "staff", (*_STAFF, "finance.view", "finance.record_payment")),
    RoleTemplate("hr_staff", "HR Staff", "staff", (*_STAFF, "hr.view")),
    RoleTemplate("librarian", "Librarian", "staff", (*_STAFF, "library.manage")),
    RoleTemplate("transport_staff", "Transport Staff", "staff", (*_STAFF, "transport.manage")),
    # Management roles (Director Login). Deliberately NOT a single all-powerful role.
    RoleTemplate(
        "owner",
        "Owner",
        "management",
        (
            *_MGMT_BASE,
            "mgmt.academics.view",
            "mgmt.attendance.view",
            "finance.view",
            "finance.view_summary",
            "hr.view",
            "payroll.view",
            "approvals.decide_leave",
            "evaluation.view",
            "evaluation.manage",
            "complaints.view_all",
            "complaints.view_confidential",
            "complaints.manage",
            "complaints.view_summary",
            "feedback.view_aggregate",
            "admissions.view",
            "audit.view",
            "config.view",
        ),
    ),
    RoleTemplate(
        "director",
        "Director",
        "management",
        (
            *_MGMT_BASE,
            "mgmt.academics.view",
            "mgmt.attendance.view",
            "finance.view",
            "finance.view_summary",
            "hr.view",
            "payroll.view",
            "approvals.decide_leave",
            "evaluation.view",
            "evaluation.manage",
            "marks.publish",
            "complaints.view_all",
            "complaints.view_confidential",
            "complaints.manage",
            "complaints.view_summary",
            "feedback.view_aggregate",
            "admissions.view",
            "audit.view",
            "config.view",
        ),
    ),
    RoleTemplate(
        "principal",
        "Principal",
        "management",
        (
            *_MGMT_BASE,
            "mgmt.academics.view",
            "mgmt.attendance.view",
            "finance.view_summary",
            "hr.view",
            "approvals.decide_leave",
            "evaluation.view",
            "evaluation.manage",
            "marks.publish",
            "complaints.view_all",
            "complaints.view_confidential",
            "complaints.manage",
            "complaints.view_summary",
            "feedback.view_aggregate",
            "admissions.view",
            "audit.view",
            "config.view",
        ),
    ),
    RoleTemplate(
        "board_member",
        "Board Member",
        "management",
        (
            *_MGMT_BASE,
            "mgmt.academics.view",
            "mgmt.attendance.view",
            "finance.view_summary",
            "complaints.view_summary",
            "feedback.view_aggregate",
        ),
        "Aggregated oversight only: no salaries, confidential complaints or individual records.",
    ),
    RoleTemplate(
        "academic_coordinator",
        "Academic Coordinator",
        "management",
        (
            *_MGMT_BASE,
            "mgmt.academics.view",
            "mgmt.attendance.view",
            "marks.publish",
            "evaluation.view",
            "complaints.view_summary",
            "feedback.view_aggregate",
        ),
    ),
    RoleTemplate(
        "finance_manager",
        "Finance Manager",
        "management",
        (*_MGMT_BASE, "finance.view", "finance.view_summary", "finance.record_payment", "payroll.view", "admissions.view"),
    ),
    RoleTemplate(
        "hr_manager",
        "HR Manager",
        "management",
        (*_MGMT_BASE, "mgmt.attendance.view", "hr.view", "payroll.view", "approvals.decide_leave", "evaluation.view"),
    ),
    RoleTemplate(
        "tech_admin",
        "Technical Administrator",
        "management",
        ("mgmt.portal", "config.view", "config.manage", "audit.view"),
        "Configuration and audit only; no access to academic, financial or HR records.",
    ),
)

# Which account types may sign in through which portal.
PORTAL_ACCOUNT_TYPE = {"student": "student", "staff": "staff", "director": "management"}
