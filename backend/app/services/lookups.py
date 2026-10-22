"""Small query helpers shared across services (batched lookups avoid N+1 queries)."""

from collections.abc import Iterable
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.models import Enrollment, SchoolClass, Section, StaffProfile, StudentProfile, Subject
from app.schemas.common import Page, PageParams


def section_labels(db: Session, ids: Iterable[UUID] | None = None) -> dict[UUID, str]:
    stmt = select(Section.id, SchoolClass.grade_number, Section.name).join(SchoolClass, SchoolClass.id == Section.class_id)
    if ids is not None:
        stmt = stmt.where(Section.id.in_(list(ids)))
    return {sid: f"{grade}-{name}" for sid, grade, name in db.execute(stmt)}


def subject_names(db: Session) -> dict[UUID, str]:
    return dict(db.execute(select(Subject.id, Subject.name)).all())  # type: ignore[arg-type]


def staff_names(db: Session, ids: Iterable[UUID] | None = None) -> dict[UUID, str]:
    stmt = select(StaffProfile.id, StaffProfile.first_name, StaffProfile.last_name)
    if ids is not None:
        stmt = stmt.where(StaffProfile.id.in_(list(ids)))
    return {i: f"{f} {l}" for i, f, l in db.execute(stmt)}


def student_names(db: Session, ids: Iterable[UUID]) -> dict[UUID, str]:
    wanted = {i for i in ids if i}
    if not wanted:
        return {}
    rows = db.execute(
        select(StudentProfile.id, StudentProfile.first_name, StudentProfile.last_name).where(StudentProfile.id.in_(wanted))
    )
    return {i: f"{f} {l}" for i, f, l in rows}


def month_bounds(month: str | None, today: date) -> tuple[date, date]:
    """First and last day of a 'YYYY-MM' month (defaults to the current month)."""
    y, m = (int(month[:4]), int(month[5:7])) if month else (today.year, today.month)
    return date(y, m, 1), date(y + (m == 12), m % 12 + 1, 1) - timedelta(days=1)


def roster(db: Session, section_id: UUID) -> list[dict[str, Any]]:
    rows = db.execute(
        select(
            StudentProfile.id,
            StudentProfile.student_code,
            StudentProfile.first_name,
            StudentProfile.last_name,
            Enrollment.roll_no,
        )
        .join(Enrollment, Enrollment.student_id == StudentProfile.id)
        .where(Enrollment.section_id == section_id, Enrollment.status == "active")
        .order_by(Enrollment.roll_no)
    )
    return [
        {"student_id": r.id, "student_code": r.student_code, "name": f"{r.first_name} {r.last_name}", "roll_no": r.roll_no}
        for r in rows
    ]


def enrollment_for(db: Session, student_id: UUID, academic_year_id: UUID) -> Enrollment | None:
    return db.scalar(
        select(Enrollment).where(
            Enrollment.student_id == student_id, Enrollment.academic_year_id == academic_year_id, Enrollment.status == "active"
        )
    )


def pct(numerator: float | Decimal, denominator: float | Decimal) -> float | None:
    if not denominator:
        return None
    return round(float(numerator) * 100 / float(denominator), 1)


def money(value: Decimal | None) -> str:
    """Serialise money as an exact string (never a float)."""
    return str((value or Decimal(0)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def paginate(db: Session, stmt: Select[Any] | Any, params: PageParams, mapper: Any) -> Page[Any]:
    total = db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0
    rows = db.execute(stmt.limit(params.page_size).offset(params.offset)).all()
    return Page(items=[mapper(r) for r in rows], total=total, page=params.page, page_size=params.page_size)
