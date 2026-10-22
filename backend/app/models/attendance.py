"""Student attendance sessions/records (with correction history) and staff attendance."""

import uuid
from datetime import date, datetime, time

from sqlalchemy import CheckConstraint, Index, SmallInteger, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TenantMixin, check_in, tenant_key, tfk

# "Not Recorded" is the absence of a record, never a stored status.
ATTENDANCE_STATUSES = ("present", "absent", "late", "approved_leave", "excused")
STAFF_ATTENDANCE_STATUSES = ("present", "absent", "late", "half_day", "on_leave")


class AttendanceSession(TenantMixin, Base):
    """One register: the daily register (period_no = 0) or a single timetable period."""

    __tablename__ = "attendance_sessions"
    __table_args__ = (
        tenant_key("attendance_sessions"),
        tfk("section_id", "sections"),
        tfk("taken_by_user_id", "users"),
        UniqueConstraint("school_id", "section_id", "day", "period_no"),
        Index("ix_attendance_sessions_day", "school_id", "day"),
        CheckConstraint(check_in("kind", ("daily", "period")), name="kind"),
        CheckConstraint("(kind = 'daily') = (period_no = 0)", name="daily_has_period_zero"),
    )

    section_id: Mapped[uuid.UUID]
    day: Mapped[date]
    kind: Mapped[str] = mapped_column(String(8))
    period_no: Mapped[int] = mapped_column(SmallInteger, default=0)
    taken_by_user_id: Mapped[uuid.UUID]
    submitted_at: Mapped[datetime]
    updated_at: Mapped[datetime | None]


class AttendanceRecord(TenantMixin, Base):
    __tablename__ = "attendance_records"
    __table_args__ = (
        tenant_key("attendance_records"),
        tfk("session_id", "attendance_sessions", "CASCADE"),
        tfk("student_id", "student_profiles"),
        tfk("updated_by_user_id", "users"),
        UniqueConstraint("school_id", "session_id", "student_id"),
        Index("ix_attendance_records_student", "school_id", "student_id"),
        CheckConstraint(check_in("status", ATTENDANCE_STATUSES), name="status"),
    )

    session_id: Mapped[uuid.UUID]
    student_id: Mapped[uuid.UUID]
    status: Mapped[str] = mapped_column(String(16))
    remark: Mapped[str | None] = mapped_column(String(255))
    updated_by_user_id: Mapped[uuid.UUID]
    updated_at: Mapped[datetime | None]


class AttendanceRecordHistory(TenantMixin, Base):
    __tablename__ = "attendance_record_history"
    __table_args__ = (
        tenant_key("attendance_record_history"),
        tfk("record_id", "attendance_records", "CASCADE"),
        tfk("changed_by_user_id", "users"),
    )

    record_id: Mapped[uuid.UUID]
    old_status: Mapped[str] = mapped_column(String(16))
    new_status: Mapped[str] = mapped_column(String(16))
    reason: Mapped[str | None] = mapped_column(String(255))
    changed_by_user_id: Mapped[uuid.UUID]


class StaffAttendance(TenantMixin, Base):
    __tablename__ = "staff_attendance"
    __table_args__ = (
        tenant_key("staff_attendance"),
        tfk("staff_id", "staff_profiles"),
        UniqueConstraint("school_id", "staff_id", "day"),
        Index("ix_staff_attendance_day", "school_id", "day"),
        CheckConstraint(check_in("status", STAFF_ATTENDANCE_STATUSES), name="status"),
    )

    staff_id: Mapped[uuid.UUID]
    day: Mapped[date]
    status: Mapped[str] = mapped_column(String(16))
    check_in: Mapped[time | None]
    check_out: Mapped[time | None]
