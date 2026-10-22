"""Assessments, marks (with correction history), publication and result views."""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Float, cast, func, select
from sqlalchemy.orm import Session

from app.core.errors import AppError, bad_request, not_found
from app.models import ApprovalRecord, Assessment, Enrollment, Mark, MarkHistory, Term
from app.schemas.academics import AssessmentCreate, MarksSubmission
from app.schemas.settings import SchoolSettingsModel
from app.services import audit
from app.services.auth_context import AuthContext
from app.services.lookups import pct, roster, subject_names
from app.services.school import current_year, grade_for, school_today
from app.services.teaching import assert_teaches


def percent_expr() -> Any:
    """SQL expression: marks obtained as a percentage of the assessment maximum."""
    return cast(Mark.marks_obtained, Float) * 100 / cast(Assessment.max_marks, Float)


def _assessment(db: Session, assessment_id: UUID) -> Assessment:
    a = db.get(Assessment, assessment_id)
    if a is None:
        raise not_found("Assessment")
    return a


def assessment_completion(db: Session, assessments: list[Assessment]) -> dict[UUID, tuple[int, int]]:
    """(entered, enrolled) per assessment in two grouped queries."""
    if not assessments:
        return {}
    ids = [a.id for a in assessments]
    entered = dict(
        db.execute(
            select(Mark.assessment_id, func.count())
            .where(Mark.assessment_id.in_(ids), (Mark.marks_obtained.is_not(None)) | Mark.is_absent)
            .group_by(Mark.assessment_id)
        )
        .tuples()
        .all()
    )
    sections = {a.section_id for a in assessments}
    enrolled = dict(
        db.execute(
            select(Enrollment.section_id, func.count())
            .where(Enrollment.section_id.in_(sections), Enrollment.status == "active")
            .group_by(Enrollment.section_id)
        )
        .tuples()
        .all()
    )
    return {a.id: (entered.get(a.id, 0), enrolled.get(a.section_id, 0)) for a in assessments}


def assessment_out(a: Assessment, completion: tuple[int, int], subjects: dict[UUID, str]) -> dict[str, Any]:
    return {
        "id": a.id,
        "name": a.name,
        "kind": a.kind,
        "max_marks": str(a.max_marks),
        "held_on": a.held_on,
        "section_id": a.section_id,
        "subject_id": a.subject_id,
        "subject": subjects.get(a.subject_id),
        "is_published": a.is_published,
        "published_at": a.published_at,
        "entered": completion[0],
        "enrolled": completion[1],
        "complete": completion[0] >= completion[1] > 0,
    }


def list_teacher_assessments(ctx: AuthContext, section_id: UUID, subject_id: UUID) -> list[dict[str, Any]]:
    assert_teaches(ctx, section_id, subject_id)
    rows = list(
        ctx.db.scalars(
            select(Assessment)
            .where(Assessment.section_id == section_id, Assessment.subject_id == subject_id)
            .order_by(Assessment.held_on)
        )
    )
    comp, subjects = assessment_completion(ctx.db, rows), subject_names(ctx.db)
    return [assessment_out(a, comp[a.id], subjects) for a in rows]


def create_assessment(ctx: AuthContext, body: AssessmentCreate) -> dict[str, Any]:
    assert_teaches(ctx, body.section_id, body.subject_id)
    db = ctx.db
    year = current_year(db)
    if not (year.starts_on <= body.held_on <= year.ends_on):
        raise bad_request("The assessment date must be within the current academic year.")
    term = db.scalar(
        select(Term).where(Term.academic_year_id == year.id, Term.starts_on <= body.held_on, Term.ends_on >= body.held_on)
    )
    if term is None:
        raise bad_request("No term covers that date.")
    if db.scalar(
        select(Assessment.id).where(
            Assessment.section_id == body.section_id, Assessment.subject_id == body.subject_id, Assessment.name == body.name
        )
    ):
        raise AppError(409, "duplicate", "An assessment with this name already exists for this class and subject.")
    a = Assessment(
        school_id=ctx.school_id,
        academic_year_id=year.id,
        term_id=term.id,
        section_id=body.section_id,
        subject_id=body.subject_id,
        name=body.name,
        kind=body.kind,
        max_marks=body.max_marks,
        held_on=body.held_on,
        created_by_user_id=ctx.user_id,
    )
    db.add(a)
    db.flush()
    audit.record(
        db,
        ctx.school_id,
        "assessment.created",
        actor_user_id=ctx.user_id,
        entity_type="assessment",
        entity_id=a.id,
        ip=ctx.ip,
        details={"name": a.name},
    )
    db.commit()
    return assessment_out(a, (0, len(roster(db, a.section_id))), subject_names(db))


def get_marks_sheet(ctx: AuthContext, assessment_id: UUID) -> dict[str, Any]:
    db = ctx.db
    a = _assessment(db, assessment_id)
    assert_teaches(ctx, a.section_id, a.subject_id)
    marks = {m.student_id: m for m in db.scalars(select(Mark).where(Mark.assessment_id == a.id))}
    students = [
        {
            **s,
            "marks_obtained": str(marks[s["student_id"]].marks_obtained)
            if s["student_id"] in marks and marks[s["student_id"]].marks_obtained is not None
            else None,
            "is_absent": marks[s["student_id"]].is_absent if s["student_id"] in marks else False,
            "remarks": marks[s["student_id"]].remarks if s["student_id"] in marks else None,
        }
        for s in roster(db, a.section_id)
    ]
    comp = assessment_completion(db, [a])[a.id]
    return {"assessment": assessment_out(a, comp, subject_names(db)), "students": students}


def save_marks(ctx: AuthContext, assessment_id: UUID, body: MarksSubmission) -> dict[str, Any]:
    db = ctx.db
    a = db.scalar(select(Assessment).where(Assessment.id == assessment_id).with_for_update())
    if a is None:
        raise not_found("Assessment")
    assert_teaches(ctx, a.section_id, a.subject_id)
    if a.held_on > school_today(ctx.school):
        raise bad_request("Marks cannot be entered before the assessment date.")
    enrolled = {s["student_id"] for s in roster(db, a.section_id)}
    ids = [m.student_id for m in body.marks]
    if len(ids) != len(set(ids)):
        raise bad_request("A student appears more than once.", "duplicate_student")
    if set(ids) - enrolled:
        raise bad_request("Some students are not enrolled in this section.", "not_enrolled")
    over = [m for m in body.marks if m.marks_obtained is not None and m.marks_obtained > a.max_marks]
    if over:
        raise bad_request(f"Marks cannot exceed the maximum of {a.max_marks}.", "exceeds_max")

    existing = {m.student_id: m for m in db.scalars(select(Mark).where(Mark.assessment_id == a.id))}
    changed = [
        m
        for m in body.marks
        if m.student_id in existing
        and (existing[m.student_id].marks_obtained != m.marks_obtained or existing[m.student_id].is_absent != m.is_absent)
    ]
    if a.is_published and changed and not (body.reason and len(body.reason.strip()) >= 5):
        raise bad_request(
            "These results are published. A reason (at least 5 characters) is required for corrections.", "reason_required"
        )
    now = datetime.now(UTC)
    for entry in body.marks:
        m = existing.get(entry.student_id)
        if m is None:
            db.add(
                Mark(
                    school_id=ctx.school_id,
                    assessment_id=a.id,
                    student_id=entry.student_id,
                    marks_obtained=entry.marks_obtained,
                    is_absent=entry.is_absent,
                    remarks=entry.remarks,
                    entered_by_user_id=ctx.user_id,
                    updated_at=now,
                )
            )
            continue
        if m.marks_obtained != entry.marks_obtained or m.is_absent != entry.is_absent:
            db.add(
                MarkHistory(
                    school_id=ctx.school_id,
                    mark_id=m.id,
                    old_marks=m.marks_obtained,
                    new_marks=entry.marks_obtained,
                    old_absent=m.is_absent,
                    new_absent=entry.is_absent,
                    reason=body.reason,
                    changed_by_user_id=ctx.user_id,
                )
            )
        m.marks_obtained, m.is_absent, m.remarks = entry.marks_obtained, entry.is_absent, entry.remarks
        m.entered_by_user_id, m.updated_at = ctx.user_id, now
    audit.record(
        db,
        ctx.school_id,
        "marks.corrected" if changed else "marks.entered",
        actor_user_id=ctx.user_id,
        entity_type="assessment",
        entity_id=a.id,
        ip=ctx.ip,
        details={"count": len(body.marks), "corrections": len(changed), "published": a.is_published, "reason": body.reason},
    )
    db.commit()
    return {"saved": len(body.marks), "corrections": len(changed)}


def publish_assessment(ctx: AuthContext, assessment_id: UUID) -> dict[str, Any]:
    db = ctx.db
    a = db.scalar(select(Assessment).where(Assessment.id == assessment_id).with_for_update())
    if a is None:
        raise not_found("Assessment")
    if a.is_published:
        raise AppError(409, "already_published", "These results are already published.")
    entered, enrolled = assessment_completion(db, [a])[a.id]
    if entered < enrolled:
        raise AppError(409, "incomplete_marks", f"{enrolled - entered} student(s) still have no marks or absence recorded.")
    a.is_published, a.published_at, a.published_by_user_id = True, datetime.now(UTC), ctx.user_id
    db.add(
        ApprovalRecord(
            school_id=ctx.school_id,
            entity_type="assessment",
            entity_id=a.id,
            decision="published",
            decided_by_user_id=ctx.user_id,
        )
    )
    audit.record(
        db, ctx.school_id, "marks.published", actor_user_id=ctx.user_id, entity_type="assessment", entity_id=a.id, ip=ctx.ip
    )
    db.commit()
    return {"published": True}


def published_results(
    db: Session, policy: SchoolSettingsModel, student_id: UUID, term_id: UUID | None = None
) -> list[dict[str, Any]]:
    """Only published assessments are ever returned to students."""
    stmt = (
        select(Assessment, Mark)
        .outerjoin(Mark, (Mark.assessment_id == Assessment.id) & (Mark.student_id == student_id))
        .join(Enrollment, (Enrollment.section_id == Assessment.section_id) & (Enrollment.student_id == student_id))
        .where(Assessment.is_published.is_(True))
        .order_by(Assessment.held_on)
    )
    if term_id:
        stmt = stmt.where(Assessment.term_id == term_id)
    subjects = subject_names(db)
    out = []
    for a, m in db.execute(stmt).tuples():
        obtained = m.marks_obtained if m else None
        percent = pct(obtained, a.max_marks) if obtained is not None else None
        out.append(
            {
                "assessment_id": a.id,
                "assessment": a.name,
                "kind": a.kind,
                "held_on": a.held_on,
                "term_id": a.term_id,
                "subject_id": a.subject_id,
                "subject": subjects[a.subject_id],
                "max_marks": str(a.max_marks),
                "marks_obtained": str(obtained) if obtained is not None else None,
                "is_absent": bool(m and m.is_absent),
                "status": "absent" if m and m.is_absent else "recorded" if obtained is not None else "not_recorded",
                "percent": percent,
                "grade": grade_for(policy, percent) if percent is not None else None,
                "remarks": m.remarks if m else None,
            }
        )
    return out


def subject_performance(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_subject: dict[str, list[dict[str, Any]]] = {}
    for r in results:
        by_subject.setdefault(r["subject"], []).append(r)
    out = []
    for subject, rows in sorted(by_subject.items()):
        scored = [r for r in rows if r["percent"] is not None]
        out.append(
            {
                "subject": subject,
                "assessments": len(rows),
                "scored": len(scored),
                "average_percent": round(sum(r["percent"] for r in scored) / len(scored), 1) if scored else None,
                "insufficient_data": len(scored) < 2,
                "trend": [{"assessment": r["assessment"], "percent": r["percent"]} for r in rows],
            }
        )
    return out
