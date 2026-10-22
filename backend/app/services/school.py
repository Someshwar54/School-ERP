"""Per-school lookups shared by services: settings, current academic year, local dates."""

from datetime import date, datetime, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError
from app.models import AcademicYear, CalendarDay, School, SchoolSettings
from app.schemas.settings import SchoolSettingsModel


def school_settings(db: Session, school_id: UUID) -> SchoolSettingsModel:
    row = db.get(SchoolSettings, school_id)
    return SchoolSettingsModel.model_validate(row.settings if row else {})


def current_year(db: Session) -> AcademicYear:
    year = db.scalar(select(AcademicYear).where(AcademicYear.is_current.is_(True)))
    if year is None:
        raise AppError(409, "no_current_year", "No current academic year is configured.")
    return year


def school_today(school: School) -> date:
    return datetime.now(ZoneInfo(school.timezone)).date()


def instructional_days(db: Session, settings: SchoolSettingsModel, start: date, end: date) -> list[date]:
    """School days between start and end inclusive (weekly offs and calendar holidays excluded)."""
    if end < start:
        return []
    off = set(settings.attendance.weekly_off_days)
    closed = set(db.scalars(select(CalendarDay.day).where(CalendarDay.day >= start, CalendarDay.day <= end)))
    days, d = [], start
    while d <= end:
        if d.weekday() not in off and d not in closed:
            days.append(d)
        d += timedelta(days=1)
    return days


def is_instructional(db: Session, settings: SchoolSettingsModel, day: date) -> bool:
    return bool(instructional_days(db, settings, day, day))


def grade_for(settings: SchoolSettingsModel, percent: float) -> str:
    for band in settings.academic.grade_scale:
        if percent >= band.min_percent:
            return band.grade
    return settings.academic.grade_scale[-1].grade


def demo_data_label() -> str | None:
    """Label shown on analytics while the deployment runs on fictional demo data."""
    return "Fictional demonstration data" if get_settings().demo_auth_mode else None
