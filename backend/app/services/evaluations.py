"""Evidence-based teacher evaluation. The system never assigns a final rating on its own."""

from collections import Counter
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import AppError, bad_request, forbidden, not_found
from app.models import (
    Assessment,
    EvaluationRubric,
    LessonTopic,
    Mark,
    StaffProfile,
    TeacherEvaluation,
    TeachingAssignment,
    TopicFeedback,
)
from app.schemas.management import EvaluationCreate, EvaluationFinalize
from app.services import audit
from app.services.academics import percent_expr
from app.services.auth_context import AuthContext
from app.services.lookups import pct, staff_names
from app.services.school import current_year, demo_data_label, school_today


def get_teacher_evidence(ctx: AuthContext) -> dict[str, Any]:
    db, today = ctx.db, school_today(ctx.school)
    year = current_year(db)
    teachers = list(
        db.scalars(select(StaffProfile).where(StaffProfile.staff_type == "teaching").order_by(StaffProfile.staff_code))
    )
    assigns = (
        db.execute(select(TeachingAssignment.staff_id, TeachingAssignment.section_id, TeachingAssignment.subject_id))
        .tuples()
        .all()
    )
    topics = (
        db.execute(
            select(LessonTopic.section_id, LessonTopic.subject_id, LessonTopic.status, func.count()).group_by(
                LessonTopic.section_id, LessonTopic.subject_id, LessonTopic.status
            )
        )
        .tuples()
        .all()
    )
    topic_map: dict[tuple[UUID, UUID], Counter[str]] = {}
    for s, sub, st, n in topics:
        topic_map.setdefault((s, sub), Counter())[st] = n
    scores = dict(
        ((s, sub), (a, n))
        for s, sub, a, n in db.execute(
            select(Assessment.section_id, Assessment.subject_id, func.avg(percent_expr()), func.count())
            .join(Mark, Mark.assessment_id == Assessment.id)
            .where(Assessment.is_published.is_(True), Mark.marks_obtained.is_not(None))
            .group_by(Assessment.section_id, Assessment.subject_id)
        ).tuples()
    )
    fb = dict(
        ((s, sub), (a, n))
        for s, sub, a, n in db.execute(
            select(LessonTopic.section_id, LessonTopic.subject_id, func.avg(TopicFeedback.understanding), func.count())
            .join(TopicFeedback, TopicFeedback.topic_id == LessonTopic.id)
            .group_by(LessonTopic.section_id, LessonTopic.subject_id)
        ).tuples()
    )
    evals = Counter(
        dict(db.execute(select(TeacherEvaluation.staff_id, func.count()).group_by(TeacherEvaluation.staff_id)).tuples().all())
    )
    elapsed = pct((today - year.starts_on).days, (year.ends_on - year.starts_on).days)
    out = []
    for t in teachers:
        mine = [(s, sub) for st, s, sub in assigns if st == t.id]
        tc = sum((topic_map.get(k, Counter()) for k in mine), Counter())
        sc = [scores[k] for k in mine if k in scores]
        fbs = [fb[k] for k in mine if k in fb]
        fb_n = sum(n for _a, n in fbs)
        out.append(
            {
                "staff_id": t.id,
                "staff_code": t.staff_code,
                "name": f"{t.first_name} {t.last_name}",
                "department": t.department,
                "assignments": len(mine),
                "curriculum_delivery_percent": pct(tc["completed"], sum(tc.values())),
                "topics_pending": tc["pending"],
                "class_average_percent_context": round(sum(a * n for a, n in sc) / sum(n for _a, n in sc), 1) if sc else None,
                "topic_feedback_average": round(float(sum(a * n for a, n in fbs) / fb_n), 2) if fb_n >= 5 else None,
                "topic_feedback_responses": fb_n,
                "evaluations": evals.get(t.id, 0),
            }
        )
    return {
        "data_label": demo_data_label(),
        "year_elapsed_percent": elapsed,
        "teachers": out,
        "guidance": (
            "Evidence to inform a human review. Marks and attendance are context, not ratings; "
            "final evaluations require a reviewer, rubric scores and written evidence."
        ),
    }


def _rubric(db: Session) -> EvaluationRubric:
    r = db.scalar(select(EvaluationRubric).where(EvaluationRubric.is_active.is_(True)))
    if r is None:
        raise AppError(409, "no_rubric", "No active evaluation rubric is configured.")
    return r


def _validate_scores(rubric: EvaluationRubric, scores: dict[str, int]) -> None:
    criteria = {c["key"]: c for c in rubric.criteria}
    for k, v in scores.items():
        if k not in criteria:
            raise bad_request(f"Unknown criterion '{k}'.")
        if not (0 <= v <= int(criteria[k]["max_score"])):
            raise bad_request(f"Score for '{criteria[k]['label']}' must be between 0 and {criteria[k]['max_score']}.")


def list_evaluations(ctx: AuthContext) -> dict[str, Any]:
    db = ctx.db
    rubric = _rubric(db)
    rows = list(db.scalars(select(TeacherEvaluation).order_by(TeacherEvaluation.created_at.desc())))
    names = staff_names(db, {r.staff_id for r in rows})
    return {
        "rubric": {"id": rubric.id, "name": rubric.name, "criteria": rubric.criteria},
        "items": [
            {
                "id": r.id,
                "staff_id": r.staff_id,
                "staff_name": names.get(r.staff_id),
                "period_label": r.period_label,
                "status": r.status,
                "scores": r.scores,
                "evidence_notes": r.evidence_notes,
                "reviewer_comment": r.reviewer_comment,
                "finalized_at": r.finalized_at,
            }
            for r in rows
        ],
        "can_manage": ctx.has("evaluation.manage"),
    }


def create_evaluation(ctx: AuthContext, body: EvaluationCreate) -> dict[str, Any]:
    db = ctx.db
    rubric = _rubric(db)
    staff = db.get(StaffProfile, body.staff_id)
    if staff is None or staff.staff_type != "teaching":
        raise bad_request("Evaluations can only be created for teaching staff.")
    _validate_scores(rubric, body.scores)
    ev = TeacherEvaluation(
        school_id=ctx.school_id,
        staff_id=body.staff_id,
        rubric_id=rubric.id,
        period_label=body.period_label,
        scores=body.scores,
        evidence_notes=body.evidence_notes,
        created_by_user_id=ctx.user_id,
    )
    db.add(ev)
    db.flush()
    audit.record(
        db,
        ctx.school_id,
        "evaluation.created",
        actor_user_id=ctx.user_id,
        entity_type="teacher_evaluation",
        entity_id=ev.id,
        ip=ctx.ip,
    )
    db.commit()
    return {"id": ev.id}


def finalize_evaluation(ctx: AuthContext, evaluation_id: UUID, body: EvaluationFinalize) -> dict[str, Any]:
    from datetime import UTC, datetime

    db = ctx.db
    ev = db.scalar(select(TeacherEvaluation).where(TeacherEvaluation.id == evaluation_id).with_for_update())
    if ev is None:
        raise not_found("Evaluation")
    if ev.staff_id == ctx.staff_id:
        raise forbidden("You cannot finalise your own evaluation.")
    if ev.status == "finalized":
        raise AppError(409, "already_finalized", "This evaluation is already finalised.")
    rubric = db.get(EvaluationRubric, ev.rubric_id)
    missing = [c["label"] for c in rubric.criteria if c["key"] not in ev.scores] if rubric else []
    if missing:
        raise bad_request("Score every rubric criterion before finalising: " + ", ".join(missing), "incomplete_scores")
    ev.status, ev.reviewer_comment, ev.finalized_by_user_id = "finalized", body.reviewer_comment, ctx.user_id
    ev.finalized_at = ev.updated_at = datetime.now(UTC)
    audit.record(
        db,
        ctx.school_id,
        "evaluation.finalized",
        actor_user_id=ctx.user_id,
        entity_type="teacher_evaluation",
        entity_id=ev.id,
        ip=ctx.ip,
    )
    db.commit()
    return {"ok": True}


def update_evaluation_scores(ctx: AuthContext, evaluation_id: UUID, scores: dict[str, int]) -> dict[str, Any]:
    db = ctx.db
    ev = db.get(TeacherEvaluation, evaluation_id)
    if ev is None:
        raise not_found("Evaluation")
    if ev.status == "finalized":
        raise AppError(409, "already_finalized", "Finalised evaluations cannot be changed.")
    rubric = db.get(EvaluationRubric, ev.rubric_id)
    if rubric:
        _validate_scores(rubric, scores)
    ev.scores = {**ev.scores, **scores}
    audit.record(
        db,
        ctx.school_id,
        "evaluation.scored",
        actor_user_id=ctx.user_id,
        entity_type="teacher_evaluation",
        entity_id=ev.id,
        ip=ctx.ip,
        details={"criteria": sorted(scores)},
    )
    db.commit()
    return {"ok": True, "scores": ev.scores}
