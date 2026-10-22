"""Attendance rules: who may take which register, validation, corrections and summaries."""

from collections import Counter
from datetime import UTC, date, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import bad_request, forbidden
from app.models import (
    AttendanceRecord,
    AttendanceRecordHistory,
    AttendanceSession,
    ClassTeacherAssignment,
    TimetableEntry,
)
from app.schemas.attendance import AttendanceSubmission
from app.schemas.settings import SchoolSettingsModel
from app.services import audit
from app.services.auth_context import AuthContext
from app.services.lookups import pct, roster
from app.services.school import current_year, is_instructional, school_settings, school_today


def summarize(counts: Counter[str], policy: SchoolSettingsModel) -> dict[str, Any]:
    """Attendance percentage per school policy. Not-recorded days never count as absences."""
    attended = counts["present"] + (counts["late"] if policy.attendance.count_late_as_present else 0)
    authorised = counts["approved_leave"] + counts["excused"]
    denominator = sum(counts.values()) - (authorised if policy.attendance.exclude_authorised_absence else 0)
    return {
        "present": counts["present"],
        "late": counts["late"],
        "absent": counts["absent"],
        "approved_leave": counts["approved_leave"],
        "excused": counts["excused"],
        "recorded_days": sum(counts.values()),
        "percent": pct(attended, denominator),
    }


def _check_register_permission(
    ctx: AuthContext, section_id: UUID, day: date, period_no: int, policy: SchoolSettingsModel
) -> None:
    db = ctx.db
    if period_no == 0:
        is_ct = db.scalar(
            select(ClassTeacherAssignment.id).where(
                ClassTeacherAssignment.section_id == section_id, ClassTeacherAssignment.staff_id == ctx.staff_id
            )
        )
        if not is_ct:
            raise forbidden("Only the class teacher can take the daily register for this section.")
        return
    if not policy.attendance.period_attendance_enabled:
        raise forbidden("Period attendance is disabled for this school.")
    entry = db.scalar(
        select(TimetableEntry.id).where(
            TimetableEntry.section_id == section_id,
            TimetableEntry.day_of_week == day.weekday(),
            TimetableEntry.period_no == period_no,
            TimetableEntry.staff_id == ctx.staff_id,
        )
    )
    if not entry:
        raise forbidden("You are not timetabled to teach this section in that period.")


def _validate_day(ctx: AuthContext, day: date, policy: SchoolSettingsModel) -> None:
    year = current_year(ctx.db)
    if day > school_today(ctx.school):
        raise bad_request("Attendance cannot be recorded for a future date.", "future_date")
    if not (year.starts_on <= day <= year.ends_on):
        raise bad_request("The date is outside the current academic year.", "outside_year")
    if not is_instructional(ctx.db, policy, day):
        raise bad_request("This is a holiday or non-instructional day; no attendance is recorded.", "non_instructional")


def get_register(ctx: AuthContext, section_id: UUID, day: date, period_no: int) -> dict[str, Any]:
    db, policy = ctx.db, school_settings(ctx.db, ctx.school_id)
    _check_register_permission(ctx, section_id, day, period_no, policy)
    students = roster(db, section_id)
    session = db.scalar(
        select(AttendanceSession).where(
            AttendanceSession.section_id == section_id, AttendanceSession.day == day, AttendanceSession.period_no == period_no
        )
    )
    existing: dict[UUID, AttendanceRecord] = {}
    if session:
        existing = {
            r.student_id: r for r in db.scalars(select(AttendanceRecord).where(AttendanceRecord.session_id == session.id))
        }
    instructional = is_instructional(db, policy, day)
    window_open = (school_today(ctx.school) - day).days <= policy.attendance.correction_window_days
    return {
        "section_id": section_id,
        "day": day,
        "period_no": period_no,
        "instructional": instructional,
        "submitted": session is not None,
        "submitted_at": session.submitted_at if session else None,
        "editable": instructional and window_open and day <= school_today(ctx.school),
        "students": [
            {
                **s,
                "status": existing[s["student_id"]].status if s["student_id"] in existing else None,
                "remark": existing[s["student_id"]].remark if s["student_id"] in existing else None,
            }
            for s in students
        ],
    }


def save_register(ctx: AuthContext, body: AttendanceSubmission) -> dict[str, Any]:
    db, policy = ctx.db, school_settings(ctx.db, ctx.school_id)
    _check_register_permission(ctx, body.section_id, body.day, body.period_no, policy)
    _validate_day(ctx, body.day, policy)
    if (school_today(ctx.school) - body.day).days > policy.attendance.correction_window_days:
        raise forbidden("The correction window for this date has closed. Ask an administrator to correct it.")

    enrolled = {s["student_id"] for s in roster(db, body.section_id)}
    submitted_ids = [r.student_id for r in body.records]
    if len(submitted_ids) != len(set(submitted_ids)):
        raise bad_request("A student appears more than once.", "duplicate_student")
    outsiders = set(submitted_ids) - enrolled
    if outsiders:
        raise bad_request("Some students are not enrolled in this section.", "not_enrolled")

    now = datetime.now(UTC)
    session = db.scalar(
        select(AttendanceSession)
        .where(
            AttendanceSession.section_id == body.section_id,
            AttendanceSession.day == body.day,
            AttendanceSession.period_no == body.period_no,
        )
        .with_for_update()
    )
    corrections = 0
    if session is None:
        if set(submitted_ids) != enrolled:
            raise bad_request("Mark every enrolled student before submitting the register.", "incomplete_register")
        session = AttendanceSession(
            school_id=ctx.school_id,
            section_id=body.section_id,
            day=body.day,
            kind="daily" if body.period_no == 0 else "period",
            period_no=body.period_no,
            taken_by_user_id=ctx.user_id,
            submitted_at=now,
        )
        db.add(session)
        db.flush()
        for r in body.records:
            db.add(
                AttendanceRecord(
                    school_id=ctx.school_id,
                    session_id=session.id,
                    student_id=r.student_id,
                    status=r.status,
                    remark=r.remark,
                    updated_by_user_id=ctx.user_id,
                )
            )
        action = "attendance.submitted"
    else:
        existing = {
            r.student_id: r for r in db.scalars(select(AttendanceRecord).where(AttendanceRecord.session_id == session.id))
        }
        changes = [
            r
            for r in body.records
            if r.student_id not in existing
            or existing[r.student_id].status != r.status
            or (existing[r.student_id].remark or None) != (r.remark or None)
        ]
        if changes and not (body.reason and len(body.reason.strip()) >= 5):
            raise bad_request("A reason (at least 5 characters) is required to correct a submitted register.", "reason_required")
        for r in changes:
            rec = existing.get(r.student_id)
            if rec is None:
                db.add(
                    AttendanceRecord(
                        school_id=ctx.school_id,
                        session_id=session.id,
                        student_id=r.student_id,
                        status=r.status,
                        remark=r.remark,
                        updated_by_user_id=ctx.user_id,
                    )
                )
                continue
            if rec.status != r.status:
                db.add(
                    AttendanceRecordHistory(
                        school_id=ctx.school_id,
                        record_id=rec.id,
                        old_status=rec.status,
                        new_status=r.status,
                        reason=body.reason,
                        changed_by_user_id=ctx.user_id,
                    )
                )
                corrections += 1
            rec.status, rec.remark, rec.updated_by_user_id, rec.updated_at = r.status, r.remark, ctx.user_id, now
        session.updated_at = now
        action = "attendance.corrected"
    audit.record(
        db,
        ctx.school_id,
        action,
        actor_user_id=ctx.user_id,
        entity_type="attendance_session",
        entity_id=session.id,
        ip=ctx.ip,
        details={
            "day": body.day.isoformat(),
            "period_no": body.period_no,
            "records": len(body.records),
            "corrections": corrections,
            "reason": body.reason,
        },
    )
    db.commit()
    return {"session_id": session.id, "corrections": corrections, "action": action}


def student_status_counts(db: Session, student_id: UUID, start: date, end: date) -> Counter[str]:
    rows = db.execute(
        select(AttendanceRecord.status, func.count())
        .join(AttendanceSession, AttendanceSession.id == AttendanceRecord.session_id)
        .where(
            AttendanceRecord.student_id == student_id,
            AttendanceSession.period_no == 0,
            AttendanceSession.day >= start,
            AttendanceSession.day <= end,
        )
        .group_by(AttendanceRecord.status)
    )
    return Counter({s: c for s, c in rows})


def section_daily_percent(
    db: Session, policy: SchoolSettingsModel, section_ids: list[UUID] | None, start: date, end: date
) -> dict[date, float | None]:
    stmt = (
        select(AttendanceSession.day, AttendanceRecord.status, func.count())
        .join(AttendanceRecord, AttendanceRecord.session_id == AttendanceSession.id)
        .where(AttendanceSession.period_no == 0, AttendanceSession.day >= start, AttendanceSession.day <= end)
        .group_by(AttendanceSession.day, AttendanceRecord.status)
    )
    if section_ids is not None:
        stmt = stmt.where(AttendanceSession.section_id.in_(section_ids))
    by_day: dict[date, Counter[str]] = {}
    for d, s, c in db.execute(stmt):
        by_day.setdefault(d, Counter())[s] = c
    return {d: summarize(c, policy)["percent"] for d, c in sorted(by_day.items())}


def missing_registers(
    db: Session, policy: SchoolSettingsModel, section_ids: list[UUID], days: list[date]
) -> list[tuple[UUID, date]]:
    if not days or not section_ids:
        return []
    taken = set(
        db.execute(
            select(AttendanceSession.section_id, AttendanceSession.day).where(
                AttendanceSession.period_no == 0,
                AttendanceSession.section_id.in_(section_ids),
                AttendanceSession.day >= min(days),
                AttendanceSession.day <= max(days),
            )
        ).tuples()
    )
    return [(s, d) for d in days for s in section_ids if (s, d) not in taken]
