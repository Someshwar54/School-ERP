"""Lesson / topic progression. Completion is always an explicit, confirmed action.

Marking a topic complete records content *delivery*; it is never treated as
evidence that students have mastered the topic.
"""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, select

from app.core.errors import AppError, bad_request, not_found
from app.models import LessonTopic, TimetableEntry, TopicFeedback, TopicProgressLog
from app.schemas.academics import TopicAction, TopicCreate
from app.services import audit
from app.services.auth_context import AuthContext
from app.services.lookups import roster, section_labels, subject_names
from app.services.school import current_year, school_today
from app.services.teaching import assert_teaches


def _topic_out(t: LessonTopic) -> dict[str, Any]:
    return {
        "id": t.id,
        "sequence": t.sequence,
        "title": t.title,
        "status": t.status,
        "planned_periods": t.planned_periods,
        "periods_used": t.periods_used,
        "started_on": t.started_on,
        "completed_on": t.completed_on,
    }


def list_topics(ctx: AuthContext, section_id: UUID, subject_id: UUID) -> dict[str, Any]:
    assert_teaches(ctx, section_id, subject_id)
    topics = list(
        ctx.db.scalars(
            select(LessonTopic)
            .where(LessonTopic.section_id == section_id, LessonTopic.subject_id == subject_id)
            .order_by(LessonTopic.sequence)
        )
    )
    done = sum(t.status == "completed" for t in topics)
    return {
        "topics": [_topic_out(t) for t in topics],
        "completed": done,
        "total": len(topics),
        "note": "Completion records content delivery, not student mastery.",
    }


def add_topic(ctx: AuthContext, body: TopicCreate) -> dict[str, Any]:
    assert_teaches(ctx, body.section_id, body.subject_id)
    db = ctx.db
    seq = (
        db.scalar(
            select(func.max(LessonTopic.sequence)).where(
                LessonTopic.section_id == body.section_id, LessonTopic.subject_id == body.subject_id
            )
        )
        or 0
    ) + 1
    t = LessonTopic(
        school_id=ctx.school_id,
        academic_year_id=current_year(db).id,
        section_id=body.section_id,
        subject_id=body.subject_id,
        sequence=seq,
        title=body.title,
        planned_periods=body.planned_periods,
    )
    db.add(t)
    db.flush()
    audit.record(
        db,
        ctx.school_id,
        "topic.created",
        actor_user_id=ctx.user_id,
        entity_type="lesson_topic",
        entity_id=t.id,
        ip=ctx.ip,
        details={"title": t.title},
    )
    db.commit()
    return _topic_out(t)


def apply_action(ctx: AuthContext, topic_id: UUID, body: TopicAction) -> dict[str, Any]:
    db = ctx.db
    t = db.scalar(select(LessonTopic).where(LessonTopic.id == topic_id).with_for_update())
    if t is None:
        raise not_found("Topic")
    assert_teaches(ctx, t.section_id, t.subject_id)
    if body.timetable_entry_id:
        entry = db.get(TimetableEntry, body.timetable_entry_id)
        if entry is None or entry.section_id != t.section_id or entry.subject_id != t.subject_id:
            raise bad_request("The timetable period does not match this topic.")
    today, now = school_today(ctx.school), datetime.now(UTC)
    others_in_progress = db.scalar(
        select(LessonTopic).where(
            LessonTopic.section_id == t.section_id,
            LessonTopic.subject_id == t.subject_id,
            LessonTopic.status == "in_progress",
            LessonTopic.id != t.id,
        )
    )

    def log(action: str) -> None:
        db.add(
            TopicProgressLog(
                school_id=ctx.school_id,
                topic_id=t.id,
                action=action,
                occurred_on=today,
                timetable_entry_id=body.timetable_entry_id,
                notes=body.notes,
                actor_user_id=ctx.user_id,
            )
        )

    started_next = None
    if body.action == "start":
        if t.status not in ("planned", "pending"):
            raise AppError(409, "invalid_transition", "Only planned or pending topics can be started.")
        if others_in_progress:
            raise AppError(
                409,
                "topic_in_progress",
                f"'{others_in_progress.title}' is still in progress. Complete it or keep it pending first.",
            )
        t.status, t.started_on = "in_progress", t.started_on or today
        t.periods_used += 1
        log("started")
    elif body.action == "continue":
        if t.status != "in_progress":
            raise AppError(409, "invalid_transition", "Only an in-progress topic can be continued.")
        t.periods_used += 1
        log("continued")
    elif body.action == "keep_pending":
        if t.status != "in_progress":
            raise AppError(409, "invalid_transition", "Only an in-progress topic can be kept pending.")
        t.status = "pending"
        log("kept_pending")
    elif body.action == "complete":
        if not body.confirm:
            # Dismissing the prompt must never complete a topic.
            raise bad_request("Completion must be explicitly confirmed.", "confirmation_required")
        if t.status != "in_progress":
            raise AppError(409, "invalid_transition", "Only an in-progress topic can be completed.")
        t.status, t.completed_on, t.completed_by_user_id = "completed", today, ctx.user_id
        log("completed")
        if body.start_next:
            nxt = db.scalar(
                select(LessonTopic)
                .where(
                    LessonTopic.section_id == t.section_id,
                    LessonTopic.subject_id == t.subject_id,
                    LessonTopic.status.in_(("planned", "pending")),
                    LessonTopic.sequence > t.sequence,
                )
                .order_by(LessonTopic.sequence)
            )
            if nxt:
                nxt.status, nxt.started_on, nxt.updated_at = "in_progress", today, now
                db.add(
                    TopicProgressLog(
                        school_id=ctx.school_id, topic_id=nxt.id, action="started", occurred_on=today, actor_user_id=ctx.user_id
                    )
                )
                started_next = _topic_out(nxt)
    elif body.action == "reopen":
        if t.status != "completed":
            raise AppError(409, "invalid_transition", "Only a completed topic can be reopened.")
        if not (body.notes and len(body.notes.strip()) >= 5):
            raise bad_request("Give a reason (at least 5 characters) to reopen a completed topic.", "reason_required")
        if others_in_progress:
            raise AppError(409, "topic_in_progress", "Another topic is in progress. Keep it pending first.")
        t.status, t.completed_on, t.completed_by_user_id = "in_progress", None, None
        log("reopened")
    t.updated_at = now
    audit.record(
        db,
        ctx.school_id,
        f"topic.{body.action}",
        actor_user_id=ctx.user_id,
        entity_type="lesson_topic",
        entity_id=t.id,
        ip=ctx.ip,
        details={"title": t.title, "notes": body.notes},
    )
    db.commit()
    return {"topic": _topic_out(t), "started_next": started_next}


def list_lesson_prompts(ctx: AuthContext) -> list[dict[str, Any]]:
    """Today's timetabled periods with the topic currently in progress for each."""
    db = ctx.db
    today = school_today(ctx.school)
    entries = list(
        db.scalars(
            select(TimetableEntry)
            .where(TimetableEntry.staff_id == ctx.staff_id, TimetableEntry.day_of_week == today.weekday())
            .order_by(TimetableEntry.period_no)
        )
    )
    if not entries:
        return []
    pairs = {(e.section_id, e.subject_id) for e in entries}
    topics = list(
        db.scalars(
            select(LessonTopic)
            .where(
                LessonTopic.section_id.in_({p[0] for p in pairs}), LessonTopic.status.in_(("in_progress", "planned", "pending"))
            )
            .order_by(LessonTopic.sequence)
        )
    )
    current: dict[tuple[UUID, UUID], LessonTopic] = {}
    upcoming: dict[tuple[UUID, UUID], LessonTopic] = {}
    for t in topics:
        key = (t.section_id, t.subject_id)
        if t.status == "in_progress":
            current[key] = t
        elif key not in upcoming:
            upcoming[key] = t
    labels, subjects = section_labels(db, {p[0] for p in pairs}), subject_names(db)
    out = []
    for e in entries:
        key = (e.section_id, e.subject_id)
        out.append(
            {
                "timetable_entry_id": e.id,
                "period_no": e.period_no,
                "section_id": e.section_id,
                "section": labels[e.section_id],
                "subject_id": e.subject_id,
                "subject": subjects[e.subject_id],
                "current_topic": _topic_out(current[key]) if key in current else None,
                "next_topic": _topic_out(upcoming[key]) if key in upcoming else None,
            }
        )
    return out


def get_topic_feedback_summary(ctx: AuthContext, section_id: UUID, subject_id: UUID) -> list[dict[str, Any]]:
    assert_teaches(ctx, section_id, subject_id)
    db = ctx.db
    topics = list(
        db.scalars(
            select(LessonTopic)
            .where(LessonTopic.section_id == section_id, LessonTopic.subject_id == subject_id)
            .order_by(LessonTopic.sequence)
        )
    )
    names = {s["student_id"]: s["name"] for s in roster(db, section_id)}
    fb: dict[UUID, list[TopicFeedback]] = {}
    for f in db.scalars(select(TopicFeedback).where(TopicFeedback.topic_id.in_([t.id for t in topics]))):
        fb.setdefault(f.topic_id, []).append(f)
    out = []
    for t in topics:
        items = fb.get(t.id, [])
        if not items:
            continue
        out.append(
            {
                "topic_id": t.id,
                "title": t.title,
                "status": t.status,
                "responses": len(items),
                "average_understanding": round(sum(i.understanding for i in items) / len(items), 2),
                "needs_support": [names.get(i.student_id, "Student") for i in items if i.understanding <= 2 and i.share_name],
                "comments": [
                    {
                        "comment": i.comment,
                        "understanding": i.understanding,
                        "student": names.get(i.student_id) if i.share_name else None,
                    }
                    for i in items
                    if i.comment
                ],
            }
        )
    return out
