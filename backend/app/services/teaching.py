"""Assignment-based access checks for teachers. Every teacher query goes through these."""

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import forbidden
from app.models import ClassTeacherAssignment, TeachingAssignment
from app.services.auth_context import AuthContext
from app.services.lookups import section_labels, subject_names


def assignments(db: Session, staff_id: UUID) -> list[dict[str, Any]]:
    rows = list(db.scalars(select(TeachingAssignment).where(TeachingAssignment.staff_id == staff_id)))
    labels = section_labels(db, {r.section_id for r in rows})
    subjects = subject_names(db)
    out = [
        {
            "section_id": r.section_id,
            "section": labels[r.section_id],
            "subject_id": r.subject_id,
            "subject": subjects[r.subject_id],
        }
        for r in rows
    ]
    return sorted(out, key=lambda a: (a["section"], a["subject"]))


def class_teacher_sections(db: Session, staff_id: UUID) -> list[UUID]:
    return list(db.scalars(select(ClassTeacherAssignment.section_id).where(ClassTeacherAssignment.staff_id == staff_id)))


def assert_teaches(ctx: AuthContext, section_id: UUID, subject_id: UUID) -> None:
    ok = ctx.db.scalar(
        select(TeachingAssignment.id).where(
            TeachingAssignment.staff_id == ctx.staff_id,
            TeachingAssignment.section_id == section_id,
            TeachingAssignment.subject_id == subject_id,
        )
    )
    if not ok:
        raise forbidden("You are not assigned to teach this subject in this section.")


def assert_class_teacher(ctx: AuthContext, section_id: UUID) -> None:
    if ctx.staff_id is None or section_id not in class_teacher_sections(ctx.db, ctx.staff_id):
        raise forbidden("You are not the class teacher of this section.")


def assert_section_access(ctx: AuthContext, section_id: UUID) -> None:
    db = ctx.db
    teaches = db.scalar(
        select(TeachingAssignment.id)
        .where(TeachingAssignment.staff_id == ctx.staff_id, TeachingAssignment.section_id == section_id)
        .limit(1)
    )
    if not teaches and section_id not in class_teacher_sections(db, ctx.staff_id):  # type: ignore[arg-type]
        raise forbidden("You are not assigned to this section.")
