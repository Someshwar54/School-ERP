"""Teacher workspace composition: dashboard and the class-teacher overview."""

from collections import Counter
from datetime import timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import func, select

from app.models import Assessment, AttendanceRecord, AttendanceSession, Mark, StaffDuty, Subject
from app.schemas.common import PageParams
from app.services import announcements, complaints
from app.services.academics import assessment_completion, percent_expr
from app.services.attendance import missing_registers, summarize
from app.services.auth_context import AuthContext
from app.services.lessons import list_lesson_prompts
from app.services.lookups import roster, section_labels
from app.services.school import current_year, instructional_days, school_settings, school_today
from app.services.teaching import assert_class_teacher, assignments, class_teacher_sections


def _incomplete_assessments(ctx: AuthContext, pairs: list[tuple[UUID, UUID]]) -> list[dict[str, Any]]:
    if not pairs:
        return []
    today = school_today(ctx.school)
    rows = [
        a
        for a in ctx.db.scalars(
            select(Assessment).where(Assessment.held_on <= today, Assessment.section_id.in_({p[0] for p in pairs}))
        )
        if (a.section_id, a.subject_id) in set(pairs)
    ]
    comp = assessment_completion(ctx.db, rows)
    labels = section_labels(ctx.db, {a.section_id for a in rows})
    return [
        {
            "assessment_id": a.id,
            "name": a.name,
            "section": labels[a.section_id],
            "section_id": a.section_id,
            "subject_id": a.subject_id,
            "missing": comp[a.id][1] - comp[a.id][0],
        }
        for a in rows
        if comp[a.id][0] < comp[a.id][1]
    ]


def get_dashboard(ctx: AuthContext) -> dict[str, Any]:
    db, policy, today = ctx.db, school_settings(ctx.db, ctx.school_id), school_today(ctx.school)
    mine = assignments(db, ctx.staff_id)  # type: ignore[arg-type]
    ct = class_teacher_sections(db, ctx.staff_id)  # type: ignore[arg-type]
    labels = section_labels(db, ct)
    recent = instructional_days(db, policy, today - timedelta(days=14), today)
    missing = missing_registers(db, policy, ct, recent)
    duties = list(
        db.scalars(
            select(StaffDuty)
            .where(StaffDuty.staff_id == ctx.staff_id, StaffDuty.status == "assigned", StaffDuty.duty_date >= today)
            .order_by(StaffDuty.duty_date)
            .limit(5)
        )
    )
    return {
        "assignments": mine,
        "class_teacher_of": [{"section_id": s, "section": labels[s]} for s in ct],
        "today_periods": list_lesson_prompts(ctx),
        "pending": {
            "missing_registers": [{"section": labels[s], "section_id": s, "day": d} for s, d in missing],
            "incomplete_assessments": _incomplete_assessments(ctx, [(a["section_id"], a["subject_id"]) for a in mine]),
            "assigned_complaints": sum(
                1 for c in complaints.list_teacher_complaints(ctx) if c["status"] in ("open", "in_review")
            ),
        },
        "duties": [{"title": d.title, "duty_date": d.duty_date} for d in duties],
        "announcements": announcements.list_announcements(ctx, PageParams(page=1, page_size=3)).items,
    }


def get_class_overview(ctx: AuthContext, section_id: UUID) -> dict[str, Any]:
    assert_class_teacher(ctx, section_id)
    db, policy, today = ctx.db, school_settings(ctx.db, ctx.school_id), school_today(ctx.school)
    year = current_year(db)
    students = roster(db, section_id)
    att_rows = db.execute(
        select(AttendanceRecord.student_id, AttendanceRecord.status, func.count())
        .join(AttendanceSession, AttendanceSession.id == AttendanceRecord.session_id)
        .where(
            AttendanceSession.section_id == section_id, AttendanceSession.period_no == 0, AttendanceSession.day >= year.starts_on
        )
        .group_by(AttendanceRecord.student_id, AttendanceRecord.status)
    )
    att: dict[UUID, Counter[str]] = {}
    for sid, st, n in att_rows:
        att.setdefault(sid, Counter())[st] = n
    percent = percent_expr()
    perf_rows = db.execute(
        select(Mark.student_id, Subject.name, func.avg(percent))
        .join(Assessment, Assessment.id == Mark.assessment_id)
        .join(Subject, Subject.id == Assessment.subject_id)
        .where(Assessment.section_id == section_id, Assessment.is_published.is_(True), Mark.marks_obtained.is_not(None))
        .group_by(Mark.student_id, Subject.name)
    )
    perf: dict[UUID, dict[str, float]] = {}
    for sid, subj, avg in perf_rows:
        perf.setdefault(sid, {})[subj] = round(avg, 1)
    subjects = sorted({subj for d in perf.values() for subj in d})
    rows: list[dict[str, Any]] = []
    follow_up: list[dict[str, Any]] = []
    for s in students:
        a = summarize(att.get(s["student_id"], Counter()), policy)
        scores = perf.get(s["student_id"], {})
        overall = round(sum(scores.values()) / len(scores), 1) if scores else None
        reasons = []
        if a["percent"] is not None and a["percent"] < policy.academic.attendance_alert_percent:
            reasons.append(f"Attendance {a['percent']}%")
        low = [subj for subj, v in scores.items() if v < policy.academic.low_performance_percent]
        if low:
            reasons.append("Low scores: " + ", ".join(low))
        row = {
            **s,
            "attendance_percent": a["percent"],
            "absences": a["absent"],
            "subject_averages": scores,
            "overall_percent": overall,
        }
        rows.append(row)
        if reasons:
            follow_up.append({"student_id": s["student_id"], "name": s["name"], "roll_no": s["roll_no"], "reasons": reasons})
    recent = instructional_days(db, policy, today - timedelta(days=21), today - timedelta(days=1))
    all_pairs = [
        (section_id, sid)
        for sid in db.scalars(select(Assessment.subject_id).where(Assessment.section_id == section_id).distinct())
    ]
    return {
        "section": section_labels(db, [section_id])[section_id],
        "students": rows,
        "subjects": subjects,
        "follow_up": follow_up,
        "missing": {
            "registers": [d for _s, d in missing_registers(db, policy, [section_id], recent)],
            "assessments": _incomplete_assessments(ctx, all_pairs),
        },
        "thresholds": {
            "attendance": policy.academic.attendance_alert_percent,
            "performance": policy.academic.low_performance_percent,
        },
    }
