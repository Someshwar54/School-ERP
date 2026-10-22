"""Student workspace views. Every query is keyed on the authenticated student's own id."""

from collections import Counter
from datetime import date, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import func, literal_column, select

from app.core.errors import AppError, forbidden, not_found
from app.models import (
    AttendanceRecord,
    AttendanceSession,
    BellPeriod,
    CalendarDay,
    Enrollment,
    Guardian,
    LessonTopic,
    StudentGuardian,
    StudentProfile,
    Term,
    TimetableEntry,
    TopicFeedback,
)
from app.schemas.academics import TopicFeedbackCreate
from app.schemas.common import PageParams
from app.services import announcements, finance
from app.services.academics import published_results, subject_performance
from app.services.attendance import student_status_counts, summarize
from app.services.auth_context import AuthContext
from app.services.documents import list_documents
from app.services.lookups import enrollment_for, month_bounds, section_labels, staff_names, subject_names
from app.services.school import current_year, school_settings, school_today


def _enrollment(ctx: AuthContext) -> Enrollment:
    enr = enrollment_for(ctx.db, ctx.student_id, current_year(ctx.db).id)  # type: ignore[arg-type]
    if enr is None:
        raise AppError(409, "not_enrolled", "You are not enrolled in a class for the current academic year.")
    return enr


def mask_phone(phone: str) -> str:
    return "•" * max(0, len(phone) - 4) + phone[-4:]


def get_profile(ctx: AuthContext) -> dict[str, Any]:
    db = ctx.db
    p = db.get(StudentProfile, ctx.student_id)
    if p is None:
        raise not_found("Student profile")
    enr = enrollment_for(db, p.id, current_year(db).id)
    guardians = db.execute(
        select(Guardian.full_name, StudentGuardian.relationship, StudentGuardian.verification_status, StudentGuardian.is_primary)
        .join(StudentGuardian, StudentGuardian.guardian_id == Guardian.id)
        .where(StudentGuardian.student_id == p.id)
    ).all()
    return {
        "student_code": p.student_code,
        "admission_no": p.admission_no,
        "name": f"{p.first_name} {p.last_name}",
        "date_of_birth": p.date_of_birth,
        "gender": p.gender,
        "admission_date": p.admission_date,
        "blood_group": p.blood_group,
        "address": p.address,
        "email": p.email,
        "phone_masked": mask_phone(p.phone),
        "section": section_labels(db, [enr.section_id])[enr.section_id] if enr else None,
        "roll_no": enr.roll_no if enr else None,
        "guardians": [{"name": n, "relationship": r, "verification": v, "is_primary": pr} for n, r, v, pr in guardians],
        "note": "To correct personal details, contact the school office. Profile edits are not self-service.",
    }


def get_attendance_month(ctx: AuthContext, month: str | None) -> dict[str, Any]:
    db, policy, today = ctx.db, school_settings(ctx.db, ctx.school_id), school_today(ctx.school)
    year = current_year(db)
    start, end = month_bounds(month, today)
    rows = db.execute(
        select(AttendanceSession.day, AttendanceSession.period_no, AttendanceRecord.status, AttendanceRecord.remark)
        .join(AttendanceRecord, AttendanceRecord.session_id == AttendanceSession.id)
        .where(AttendanceRecord.student_id == ctx.student_id, AttendanceSession.day >= start, AttendanceSession.day <= end)
    ).all()
    daily = {d: (s, r) for d, p, s, r in rows if p == 0}
    periods: dict[date, list[dict[str, Any]]] = {}
    for d, p, s, _r in rows:
        if p:
            periods.setdefault(d, []).append({"period_no": p, "status": s})
    closed = dict(
        db.execute(select(CalendarDay.day, CalendarDay.name).where(CalendarDay.day >= start, CalendarDay.day <= end))
        .tuples()
        .all()
    )
    days = []
    d = start
    while d <= end:
        if d < year.starts_on or d > year.ends_on:
            kind = "outside_year"
        elif d.weekday() in policy.attendance.weekly_off_days:
            kind = "weekly_off"
        elif d in closed:
            kind = "holiday"
        elif d > today:
            kind = "upcoming"
        elif d in daily:
            kind = daily[d][0]
        else:
            kind = "not_recorded"
        days.append(
            {
                "day": d,
                "status": kind,
                "holiday_name": closed.get(d),
                "remark": daily[d][1] if d in daily else None,
                "periods": sorted(periods.get(d, []), key=lambda x: x["period_no"]),
            }
        )
        d += timedelta(days=1)
    month_counts = Counter(s for s, _r in daily.values())
    ytd = student_status_counts(db, ctx.student_id, year.starts_on, today)  # type: ignore[arg-type]
    trend_rows = db.execute(
        select(func.to_char(AttendanceSession.day, literal_column("'YYYY-MM'")), AttendanceRecord.status, func.count())
        .join(AttendanceRecord, AttendanceRecord.session_id == AttendanceSession.id)
        .where(
            AttendanceRecord.student_id == ctx.student_id,
            AttendanceSession.period_no == 0,
            AttendanceSession.day >= year.starts_on,
        )
        .group_by(func.to_char(AttendanceSession.day, literal_column("'YYYY-MM'")), AttendanceRecord.status)
    ).all()
    by_month: dict[str, Counter[str]] = {}
    for mo, s, n in trend_rows:
        by_month.setdefault(mo, Counter())[s] = n
    return {
        "month": start.strftime("%Y-%m"),
        "days": days,
        "month_summary": summarize(month_counts, policy),
        "year_summary": summarize(ytd, policy),
        "not_recorded_days": sum(1 for x in days if x["status"] == "not_recorded"),
        "trend": [{"month": mo, **summarize(c, policy)} for mo, c in sorted(by_month.items())],
        "policy": {
            "late_counts_as_present": policy.attendance.count_late_as_present,
            "authorised_absence_excluded": policy.attendance.exclude_authorised_absence,
            "alert_below_percent": policy.academic.attendance_alert_percent,
        },
    }


def build_timetable(ctx: AuthContext, section_id: UUID | None = None, staff_id: UUID | None = None) -> dict[str, Any]:
    db = ctx.db
    stmt = select(TimetableEntry).order_by(TimetableEntry.day_of_week, TimetableEntry.period_no)
    stmt = stmt.where(TimetableEntry.section_id == section_id) if section_id else stmt.where(TimetableEntry.staff_id == staff_id)
    entries = list(db.scalars(stmt))
    bells = list(db.scalars(select(BellPeriod).order_by(BellPeriod.period_no)))
    subjects, teachers = subject_names(db), staff_names(db, {e.staff_id for e in entries if e.staff_id})
    labels = section_labels(db, {e.section_id for e in entries})
    today = school_today(ctx.school)
    return {
        "periods": [
            {
                "period_no": b.period_no,
                "label": b.label,
                "starts_at": b.starts_at.strftime("%H:%M"),
                "ends_at": b.ends_at.strftime("%H:%M"),
            }
            for b in bells
        ],
        "entries": [
            {
                "id": e.id,
                "day_of_week": e.day_of_week,
                "period_no": e.period_no,
                "subject": subjects[e.subject_id],
                "subject_id": e.subject_id,
                "section": labels[e.section_id],
                "section_id": e.section_id,
                "teacher": teachers.get(e.staff_id) if e.staff_id else None,
                "room": e.room,
            }
            for e in entries
        ],
        "today_day_of_week": today.weekday(),
    }


def get_timetable(ctx: AuthContext) -> dict[str, Any]:
    return build_timetable(ctx, section_id=_enrollment(ctx).section_id)


def get_dashboard(ctx: AuthContext) -> dict[str, Any]:
    db, policy, today = ctx.db, school_settings(ctx.db, ctx.school_id), school_today(ctx.school)
    year = current_year(db)
    p = get_profile(ctx)
    results = published_results(db, policy, ctx.student_id)  # type: ignore[arg-type]
    tt = get_timetable(ctx)
    todays = [e for e in tt["entries"] if e["day_of_week"] == today.weekday()]
    ledger = finance.get_student_ledger(db, ctx.student_id, today)  # type: ignore[arg-type]
    return {
        "student": {k: p[k] for k in ("name", "student_code", "section", "roll_no")},
        "attendance": summarize(student_status_counts(db, ctx.student_id, year.starts_on, today), policy),  # type: ignore[arg-type]
        "recent_results": list(reversed(results))[:5],
        "today_classes": todays,
        "periods": tt["periods"],
        "fees": {"outstanding": ledger["totals"]["outstanding"], "next_due": ledger["next_due"]},
        "announcements": announcements.list_announcements(ctx, PageParams(page=1, page_size=3)).items,
        "events": announcements.list_events(ctx, include_past_days=0)[:3],
    }


def get_results(ctx: AuthContext) -> dict[str, Any]:
    policy = school_settings(ctx.db, ctx.school_id)
    rows = published_results(ctx.db, policy, ctx.student_id)  # type: ignore[arg-type]
    exams: dict[str, list[dict[str, Any]]] = {}
    for r in rows:
        exams.setdefault(r["assessment"], []).append(r)
    out = []
    for name, items in exams.items():
        scored = [i for i in items if i["marks_obtained"] is not None]
        total = sum(float(i["marks_obtained"]) for i in scored)
        maximum = sum(float(i["max_marks"]) for i in scored)
        out.append(
            {
                "assessment": name,
                "held_on": items[0]["held_on"],
                "subjects": items,
                "total": round(total, 2),
                "maximum": round(maximum, 2),
                "percent": round(total * 100 / maximum, 1) if maximum else None,
            }
        )
    return {"exams": out, "note": "Only results published by the school are shown."}


def get_performance(ctx: AuthContext) -> dict[str, Any]:
    policy = school_settings(ctx.db, ctx.school_id)
    rows = published_results(ctx.db, policy, ctx.student_id)  # type: ignore[arg-type]
    subjects = subject_performance(rows)
    scored = [s["average_percent"] for s in subjects if s["average_percent"] is not None]
    return {
        "subjects": subjects,
        "overall_percent": round(sum(scored) / len(scored), 1) if scored else None,
        "insufficient_data": len(rows) == 0,
    }


def get_report_card(ctx: AuthContext, term_id: UUID) -> dict[str, Any]:
    db, policy = ctx.db, school_settings(ctx.db, ctx.school_id)
    term = db.get(Term, term_id)
    if term is None:
        raise not_found("Term")
    rows = published_results(db, policy, ctx.student_id, term_id)  # type: ignore[arg-type]
    if not rows:
        raise AppError(404, "not_available", "No published results are available for this term yet.")
    p = get_profile(ctx)
    att = summarize(
        student_status_counts(db, ctx.student_id, term.starts_on, min(term.ends_on, school_today(ctx.school))),  # type: ignore[arg-type]
        policy,
    )
    return {
        "term": term.name,
        "student": {k: p[k] for k in ("name", "student_code", "section", "roll_no", "admission_no")},
        "subjects": subject_performance(rows),
        "results": rows,
        "attendance": att,
        "generated_note": "Generated from published results. Not an official signed document.",
    }


def get_documents(ctx: AuthContext) -> dict[str, Any]:
    db, policy = ctx.db, school_settings(ctx.db, ctx.school_id)
    year = current_year(db)
    terms = list(db.scalars(select(Term).where(Term.academic_year_id == year.id).order_by(Term.starts_on)))
    published_terms = {r["term_id"] for r in published_results(db, policy, ctx.student_id)}  # type: ignore[arg-type]
    return {
        "report_cards": [{"term_id": t.id, "term": t.name, "available": t.id in published_terms} for t in terms],
        "documents": list_documents(ctx, "student", ctx.student_id),
        "storage_note": "File storage is not connected in this prototype; uploaded files cannot be downloaded yet.",
    }


def list_topics(ctx: AuthContext) -> list[dict[str, Any]]:
    db = ctx.db
    enr = _enrollment(ctx)
    rows = list(
        db.scalars(
            select(LessonTopic)
            .where(LessonTopic.section_id == enr.section_id, LessonTopic.status.in_(("in_progress", "completed")))
            .order_by(LessonTopic.subject_id, LessonTopic.sequence)
        )
    )
    mine = {f.topic_id: f for f in db.scalars(select(TopicFeedback).where(TopicFeedback.student_id == ctx.student_id))}
    subjects = subject_names(db)
    return [
        {
            "id": t.id,
            "subject": subjects[t.subject_id],
            "title": t.title,
            "status": t.status,
            "my_feedback": {"understanding": mine[t.id].understanding, "comment": mine[t.id].comment} if t.id in mine else None,
        }
        for t in rows
    ]


def give_topic_feedback(ctx: AuthContext, topic_id: UUID, body: TopicFeedbackCreate) -> dict[str, Any]:
    db = ctx.db
    t = db.get(LessonTopic, topic_id)
    enr = _enrollment(ctx)
    if t is None or t.section_id != enr.section_id:
        raise not_found("Topic")
    if t.status not in ("in_progress", "completed"):
        raise forbidden("Feedback opens once a topic has been started.")
    fb = db.scalar(select(TopicFeedback).where(TopicFeedback.topic_id == t.id, TopicFeedback.student_id == ctx.student_id))
    if fb is None:
        db.add(
            TopicFeedback(
                school_id=ctx.school_id,
                topic_id=t.id,
                student_id=ctx.student_id,
                understanding=body.understanding,
                comment=body.comment,
                share_name=body.share_name,
            )
        )
    else:
        fb.understanding, fb.comment, fb.share_name = body.understanding, body.comment, body.share_name
    db.commit()
    return {"ok": True}
