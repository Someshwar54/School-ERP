"""Management analytics computed from authoritative records (aggregates only, grouped in SQL)."""

from collections import Counter
from datetime import date, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    Assessment,
    AttendanceRecord,
    AttendanceSession,
    Complaint,
    Enrollment,
    Feedback,
    LeaveRequest,
    Mark,
    SchoolClass,
    Section,
    StaffAttendance,
    StaffProfile,
    Subject,
)
from app.schemas.common import PageParams
from app.schemas.settings import SchoolSettingsModel
from app.services import audit
from app.services.academics import assessment_completion, assessment_out, percent_expr
from app.services.attendance import missing_registers, section_daily_percent, summarize
from app.services.auth_context import AuthContext
from app.services.finance import get_school_summary
from app.services.lookups import paginate, pct, section_labels, subject_names
from app.services.school import current_year, demo_data_label, instructional_days, school_settings, school_today


def subject_performance(db: Session) -> list[dict[str, Any]]:
    rows = db.execute(
        select(Subject.name, func.avg(percent_expr()), func.count())
        .join(Assessment, Assessment.subject_id == Subject.id)
        .join(Mark, Mark.assessment_id == Assessment.id)
        .where(Assessment.is_published.is_(True), Mark.marks_obtained.is_not(None))
        .group_by(Subject.name)
        .order_by(Subject.name)
    )
    return [{"subject": s, "average_percent": round(a, 1), "marks": n} for s, a, n in rows]


def score_distribution(db: Session) -> list[dict[str, Any]]:
    bucket = func.least(func.floor(percent_expr() / 10), 9)
    rows: dict[int, int] = dict(
        db.execute(
            select(bucket, func.count())
            .select_from(Mark)
            .join(Assessment, Assessment.id == Mark.assessment_id)
            .where(Assessment.is_published.is_(True), Mark.marks_obtained.is_not(None))
            .group_by(bucket)
        )
        .tuples()
        .all()
    )
    return [{"range": f"{b * 10}-{b * 10 + 9 if b < 9 else 100}", "count": int(rows.get(b, 0))} for b in range(10)]


def _latest_register_day(db: Session, today: date) -> date | None:
    return db.scalar(
        select(func.max(AttendanceSession.day)).where(AttendanceSession.period_no == 0, AttendanceSession.day <= today)
    )


def _staff_percent(db: Session, day: date | None) -> float | None:
    if day is None:
        return None
    c = Counter(
        dict(
            db.execute(
                select(StaffAttendance.status, func.count()).where(StaffAttendance.day == day).group_by(StaffAttendance.status)
            )
            .tuples()
            .all()
        )
    )
    return pct(c["present"] + c["late"] + c["half_day"] * 0.5, sum(c.values()) - c["on_leave"])


def _missing_marks(db: Session, today: date) -> list[Assessment]:
    candidates = list(db.scalars(select(Assessment).where(Assessment.held_on <= today - timedelta(days=3))))
    comp = assessment_completion(db, candidates)
    return [a for a in candidates if comp[a.id][0] < comp[a.id][1]]


def _recent_school_days(db: Session, policy: SchoolSettingsModel, today: date, n: int) -> list[date]:
    days = instructional_days(db, policy, today - timedelta(days=n * 2 + 14), today - timedelta(days=1))
    return days[-n:]


def get_overview(ctx: AuthContext) -> dict[str, Any]:
    db, policy, today = ctx.db, school_settings(ctx.db, ctx.school_id), school_today(ctx.school)
    year = current_year(db)
    enrolled = (
        db.scalar(
            select(func.count())
            .select_from(Enrollment)
            .where(Enrollment.academic_year_id == year.id, Enrollment.status == "active")
        )
        or 0
    )
    staff_count = db.scalar(select(func.count()).select_from(StaffProfile).where(StaffProfile.is_active.is_(True))) or 0
    as_of = _latest_register_day(db, today)
    student_pct = section_daily_percent(db, policy, None, as_of, as_of).get(as_of) if as_of else None
    trend_days = _recent_school_days(db, policy, today + timedelta(days=1), 30)
    trend = section_daily_percent(db, policy, None, trend_days[0], trend_days[-1]) if trend_days else {}
    sections = list(db.scalars(select(Section.id).where(Section.academic_year_id == year.id)))
    missing_att = missing_registers(db, policy, sections, _recent_school_days(db, policy, today, 10))
    missing_marks = _missing_marks(db, today)
    pending_leave = db.scalar(select(func.count()).select_from(LeaveRequest).where(LeaveRequest.status == "pending")) or 0
    unpublished = [a for a in db.scalars(select(Assessment).where(Assessment.is_published.is_(False)))]
    comp = assessment_completion(db, unpublished)
    ready_to_publish = sum(1 for a in unpublished if comp[a.id][1] and comp[a.id][0] >= comp[a.id][1])
    open_complaints = (
        db.scalar(select(func.count()).select_from(Complaint).where(Complaint.status.in_(("open", "in_review")))) or 0
    )
    fb_avg = db.scalar(select(func.avg(Feedback.rating)))
    subj = subject_performance(db)
    avg_score = round(sum(s["average_percent"] * s["marks"] for s in subj) / sum(s["marks"] for s in subj), 1) if subj else None
    finance = get_school_summary(db, today) if ctx.has("finance.view") or ctx.has("finance.view_summary") else None
    actions = []
    if missing_att:
        actions.append(
            {
                "severity": "high",
                "text": f"{len(missing_att)} daily register(s) missing in the last 10 school days",
                "href": "/erp/management/attendance",
            }
        )
    if missing_marks:
        actions.append(
            {
                "severity": "medium",
                "text": f"{len(missing_marks)} assessment(s) have incomplete marks",
                "href": "/erp/management/academics",
            }
        )
    if pending_leave:
        actions.append(
            {
                "severity": "medium",
                "text": f"{pending_leave} leave request(s) awaiting a decision",
                "href": "/erp/management/approvals",
            }
        )
    if ready_to_publish:
        actions.append(
            {
                "severity": "low",
                "text": f"{ready_to_publish} complete assessment(s) ready to publish",
                "href": "/erp/management/academics",
            }
        )
    if finance and finance["overdue_invoices"]:
        actions.append(
            {
                "severity": "medium",
                "text": f"{finance['overdue_invoices']} overdue invoice(s) totalling ₹{finance['overdue_amount']}",
                "href": "/erp/management/finance",
            }
        )
    recent = audit.recent_activity(db) if ctx.has("audit.view") else None
    return {
        "data_label": demo_data_label(),
        "as_of": as_of,
        "kpis": {
            "enrolled_students": enrolled,
            "active_staff": staff_count,
            "student_attendance_percent": student_pct,
            "staff_attendance_percent": _staff_percent(db, as_of),
            "average_score_percent": avg_score,
            "missing_attendance_registers": len(missing_att),
            "incomplete_assessments": len(missing_marks),
            "pending_leave_requests": pending_leave,
            "assessments_ready_to_publish": ready_to_publish,
            "open_complaints": open_complaints,
            "average_feedback_rating": round(float(fb_avg), 2) if fb_avg else None,
        },
        "finance": finance,
        "action_items": actions,
        "recent_activity": recent,
        "charts": {
            "attendance_trend": [{"day": d, "percent": p} for d, p in trend.items()],
            "subject_performance": subj,
            "score_distribution": score_distribution(db),
            "fee_collection": finance["monthly_collection"] if finance else None,
            "exceptions": [
                {"label": "Missing registers", "count": len(missing_att)},
                {"label": "Incomplete marks", "count": len(missing_marks)},
                {"label": "Pending leave", "count": pending_leave},
                {"label": "Open complaints", "count": open_complaints},
            ],
        },
    }


def get_academics(ctx: AuthContext, status: str | None, params: PageParams) -> dict[str, Any]:
    db = ctx.db
    grade_rows = db.execute(
        select(SchoolClass.grade_number, Subject.name, func.avg(percent_expr()))
        .join(Section, Section.class_id == SchoolClass.id)
        .join(Assessment, Assessment.section_id == Section.id)
        .join(Subject, Subject.id == Assessment.subject_id)
        .join(Mark, Mark.assessment_id == Assessment.id)
        .where(Assessment.is_published.is_(True), Mark.marks_obtained.is_not(None))
        .group_by(SchoolClass.grade_number, Subject.name)
        .order_by(SchoolClass.grade_number)
    )
    stmt = select(Assessment).order_by(Assessment.held_on.desc(), Assessment.name)
    if status == "unpublished":
        stmt = stmt.where(Assessment.is_published.is_(False))
    elif status == "published":
        stmt = stmt.where(Assessment.is_published.is_(True))
    page = paginate(db, stmt, params, lambda r: r[0])
    comp, subjects, labels = assessment_completion(db, page.items), subject_names(db), section_labels(db)
    items = [{**assessment_out(a, comp[a.id], subjects), "section": labels.get(a.section_id)} for a in page.items]
    return {
        "data_label": demo_data_label(),
        "subject_performance": subject_performance(db),
        "score_distribution": score_distribution(db),
        "grade_subject": [{"grade": g, "subject": s, "average_percent": round(a, 1)} for g, s, a in grade_rows],
        "assessments": {**page.model_dump(), "items": items},
        "can_publish": ctx.has("marks.publish"),
    }


def get_attendance(ctx: AuthContext) -> dict[str, Any]:
    db, policy, today = ctx.db, school_settings(ctx.db, ctx.school_id), school_today(ctx.school)
    year = current_year(db)
    days = _recent_school_days(db, policy, today + timedelta(days=1), 30)
    trend = section_daily_percent(db, policy, None, days[0], days[-1]) if days else {}
    rows = db.execute(
        select(AttendanceSession.section_id, AttendanceRecord.status, func.count())
        .join(AttendanceRecord, AttendanceRecord.session_id == AttendanceSession.id)
        .where(AttendanceSession.period_no == 0, AttendanceSession.day >= year.starts_on)
        .group_by(AttendanceSession.section_id, AttendanceRecord.status)
    )
    per_section: dict[UUID, Counter[str]] = {}
    for s, st, n in rows:
        per_section.setdefault(s, Counter())[st] = n
    labels = section_labels(db)
    sections = list(db.scalars(select(Section.id).where(Section.academic_year_id == year.id)))
    missing = missing_registers(db, policy, sections, _recent_school_days(db, policy, today, 10))
    # Student-level counts below threshold (aggregate only; individual follow-up is the class teacher's view).
    stu_rows = db.execute(
        select(AttendanceRecord.student_id, AttendanceRecord.status, func.count())
        .join(AttendanceSession, AttendanceSession.id == AttendanceRecord.session_id)
        .where(AttendanceSession.period_no == 0, AttendanceSession.day >= year.starts_on)
        .group_by(AttendanceRecord.student_id, AttendanceRecord.status)
    )
    per_student: dict[UUID, Counter[str]] = {}
    for s, st, n in stu_rows:
        per_student.setdefault(s, Counter())[st] = n
    threshold = policy.academic.attendance_alert_percent
    below = sum(1 for c in per_student.values() if (summarize(c, policy)["percent"] or 100) < threshold)
    staff_trend = []
    for d in days[-15:]:
        staff_trend.append({"day": d, "percent": _staff_percent(db, d)})
    return {
        "data_label": demo_data_label(),
        "trend": [{"day": d, "percent": p} for d, p in trend.items()],
        "by_section": sorted(
            [{"section": labels[s], **summarize(c, policy)} for s, c in per_section.items()], key=lambda r: r["section"]
        ),
        "missing_registers": [{"section": labels[s], "day": d} for s, d in missing],
        "students_below_threshold": below,
        "threshold_percent": threshold,
        "staff_trend": staff_trend,
    }
