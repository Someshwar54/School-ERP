"""Teacher-student messaging. Students may only message teachers assigned to their class."""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select

from app.core.errors import forbidden, not_found
from app.models import (
    ClassTeacherAssignment,
    Message,
    MessageThread,
    StudentProfile,
    TeachingAssignment,
    User,
)
from app.schemas.communication import MessageReply, MessageThreadCreate
from app.services.auth_context import AuthContext
from app.services.lookups import enrollment_for, staff_names, student_names, subject_names
from app.services.school import current_year


# ---- messaging ---------------------------------------------------------------------------------------------------
def list_student_teachers(ctx: AuthContext) -> list[dict[str, Any]]:
    enr = enrollment_for(ctx.db, ctx.student_id, current_year(ctx.db).id)  # type: ignore[arg-type]
    if enr is None:
        return []
    rows = (
        ctx.db.execute(
            select(TeachingAssignment.staff_id, TeachingAssignment.subject_id).where(
                TeachingAssignment.section_id == enr.section_id
            )
        )
        .tuples()
        .all()
    )
    names, subjects = staff_names(ctx.db, {r[0] for r in rows}), subject_names(ctx.db)
    ct = ctx.db.scalar(select(ClassTeacherAssignment.staff_id).where(ClassTeacherAssignment.section_id == enr.section_id))
    return sorted(
        [{"staff_id": s, "name": names[s], "subject": subjects[sub], "is_class_teacher": s == ct} for s, sub in rows],
        key=lambda r: r["subject"],
    )


def _thread_out(t: MessageThread, names: dict[UUID, str], students: dict[UUID, str]) -> dict[str, Any]:
    return {
        "id": t.id,
        "subject": t.subject,
        "staff_id": t.staff_id,
        "staff_name": names.get(t.staff_id),
        "student_id": t.student_id,
        "student_name": students.get(t.student_id),
        "last_message_at": t.last_message_at,
    }


def list_threads(ctx: AuthContext) -> list[dict[str, Any]]:
    db = ctx.db
    stmt = select(MessageThread)
    stmt = (
        stmt.where(MessageThread.student_id == ctx.student_id)
        if ctx.student_id
        else stmt.where(MessageThread.staff_id == ctx.staff_id)
    )
    threads = list(db.scalars(stmt.order_by(MessageThread.last_message_at.desc()).limit(100)))
    names = staff_names(db, {t.staff_id for t in threads})
    students = student_names(db, {t.student_id for t in threads})
    return [_thread_out(t, names, students) for t in threads]


def _authorised_thread(ctx: AuthContext, thread_id: UUID) -> MessageThread:
    t = ctx.db.get(MessageThread, thread_id)
    if t is None or not (
        (ctx.student_id and t.student_id == ctx.student_id)
        or (ctx.staff_id and t.staff_id == ctx.staff_id and ctx.user.account_type == "staff")
    ):
        raise not_found("Conversation")
    return t


def get_thread(ctx: AuthContext, thread_id: UUID) -> dict[str, Any]:
    db = ctx.db
    t = _authorised_thread(ctx, thread_id)
    msgs = list(db.scalars(select(Message).where(Message.thread_id == t.id).order_by(Message.created_at)))
    senders = dict(
        db.execute(select(User.id, User.display_name).where(User.id.in_({m.sender_user_id for m in msgs}))).tuples().all()
    )
    names = staff_names(db, [t.staff_id])
    student = db.get(StudentProfile, t.student_id)
    return {
        **_thread_out(t, names, {t.student_id: f"{student.first_name} {student.last_name}"} if student else {}),
        "messages": [
            {
                "id": m.id,
                "body": m.body,
                "sender": senders.get(m.sender_user_id),
                "created_at": m.created_at,
                "mine": m.sender_user_id == ctx.user_id,
            }
            for m in msgs
        ],
    }


def create_thread(ctx: AuthContext, body: MessageThreadCreate) -> dict[str, Any]:
    if body.staff_id not in {t["staff_id"] for t in list_student_teachers(ctx)}:
        raise forbidden("You can only message teachers assigned to your class.")
    now = datetime.now(UTC)
    t = MessageThread(
        school_id=ctx.school_id,
        student_id=ctx.student_id,
        staff_id=body.staff_id,
        subject=body.subject,
        created_by_user_id=ctx.user_id,
        last_message_at=now,
    )
    ctx.db.add(t)
    ctx.db.flush()
    ctx.db.add(Message(school_id=ctx.school_id, thread_id=t.id, sender_user_id=ctx.user_id, body=body.body))
    ctx.db.commit()
    return {"id": t.id}


def reply_to_thread(ctx: AuthContext, thread_id: UUID, body: MessageReply) -> dict[str, Any]:
    t = _authorised_thread(ctx, thread_id)
    ctx.db.add(Message(school_id=ctx.school_id, thread_id=t.id, sender_user_id=ctx.user_id, body=body.body))
    t.last_message_at = datetime.now(UTC)
    ctx.db.commit()
    return {"ok": True}
