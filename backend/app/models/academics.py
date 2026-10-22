"""Academic structure, assignments, timetable, assessments and lesson progression."""

import uuid
from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, Index, Integer, Numeric, SmallInteger, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TenantMixin, check_in, tenant_key, tfk

ASSESSMENT_KINDS = ("unit_test", "half_yearly", "annual", "assignment", "practical")
TOPIC_STATUSES = ("planned", "in_progress", "pending", "completed")
TOPIC_ACTIONS = ("started", "continued", "kept_pending", "completed", "reopened")


class AcademicYear(TenantMixin, Base):
    __tablename__ = "academic_years"
    __table_args__ = (
        tenant_key("academic_years"),
        UniqueConstraint("school_id", "name"),
        CheckConstraint("ends_on > starts_on", name="date_order"),
        Index("uq_academic_years_one_current", "school_id", unique=True, postgresql_where="is_current"),
    )

    name: Mapped[str] = mapped_column(String(16))
    starts_on: Mapped[date]
    ends_on: Mapped[date]
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)


class Term(TenantMixin, Base):
    __tablename__ = "terms"
    __table_args__ = (
        tenant_key("terms"),
        tfk("academic_year_id", "academic_years"),
        UniqueConstraint("school_id", "academic_year_id", "name"),
        CheckConstraint("ends_on > starts_on", name="date_order"),
    )

    academic_year_id: Mapped[uuid.UUID]
    name: Mapped[str] = mapped_column(String(32))
    starts_on: Mapped[date]
    ends_on: Mapped[date]


class CalendarDay(TenantMixin, Base):
    """Holidays and non-instructional days. Weekly offs come from school settings."""

    __tablename__ = "calendar_days"
    __table_args__ = (
        tenant_key("calendar_days"),
        UniqueConstraint("school_id", "day"),
        CheckConstraint(check_in("kind", ("holiday", "non_instructional")), name="kind"),
    )

    day: Mapped[date]
    kind: Mapped[str] = mapped_column(String(24))
    name: Mapped[str] = mapped_column(String(120))


class SchoolClass(TenantMixin, Base):
    __tablename__ = "classes"
    __table_args__ = (tenant_key("classes"), UniqueConstraint("school_id", "grade_number"))

    name: Mapped[str] = mapped_column(String(32))
    grade_number: Mapped[int] = mapped_column(SmallInteger)


class Section(TenantMixin, Base):
    __tablename__ = "sections"
    __table_args__ = (
        tenant_key("sections"),
        tfk("class_id", "classes"),
        tfk("academic_year_id", "academic_years"),
        UniqueConstraint("school_id", "academic_year_id", "class_id", "name"),
    )

    class_id: Mapped[uuid.UUID]
    academic_year_id: Mapped[uuid.UUID]
    name: Mapped[str] = mapped_column(String(8))
    room: Mapped[str | None] = mapped_column(String(32))


class Subject(TenantMixin, Base):
    __tablename__ = "subjects"
    __table_args__ = (tenant_key("subjects"), UniqueConstraint("school_id", "code"))

    code: Mapped[str] = mapped_column(String(16))
    name: Mapped[str] = mapped_column(String(80))


class Enrollment(TenantMixin, Base):
    __tablename__ = "enrollments"
    __table_args__ = (
        tenant_key("enrollments"),
        tfk("student_id", "student_profiles"),
        tfk("section_id", "sections"),
        tfk("academic_year_id", "academic_years"),
        UniqueConstraint("school_id", "student_id", "academic_year_id"),
        UniqueConstraint("school_id", "section_id", "roll_no"),
        Index("ix_enrollments_section", "school_id", "section_id"),
        CheckConstraint(check_in("status", ("active", "transferred", "withdrawn")), name="status"),
    )

    student_id: Mapped[uuid.UUID]
    section_id: Mapped[uuid.UUID]
    academic_year_id: Mapped[uuid.UUID]
    roll_no: Mapped[int] = mapped_column(SmallInteger)
    status: Mapped[str] = mapped_column(String(16), default="active")


class TeachingAssignment(TenantMixin, Base):
    """Which staff member teaches which subject to which section."""

    __tablename__ = "teaching_assignments"
    __table_args__ = (
        tenant_key("teaching_assignments"),
        tfk("academic_year_id", "academic_years"),
        tfk("staff_id", "staff_profiles"),
        tfk("section_id", "sections"),
        tfk("subject_id", "subjects"),
        UniqueConstraint("school_id", "section_id", "subject_id"),
        Index("ix_teaching_assignments_staff", "school_id", "staff_id"),
    )

    academic_year_id: Mapped[uuid.UUID]
    staff_id: Mapped[uuid.UUID]
    section_id: Mapped[uuid.UUID]
    subject_id: Mapped[uuid.UUID]


class ClassTeacherAssignment(TenantMixin, Base):
    __tablename__ = "class_teacher_assignments"
    __table_args__ = (
        tenant_key("class_teacher_assignments"),
        tfk("academic_year_id", "academic_years"),
        tfk("staff_id", "staff_profiles"),
        tfk("section_id", "sections"),
        UniqueConstraint("school_id", "section_id"),
        Index("ix_class_teacher_assignments_staff", "school_id", "staff_id"),
    )

    academic_year_id: Mapped[uuid.UUID]
    section_id: Mapped[uuid.UUID]
    staff_id: Mapped[uuid.UUID]


class BellPeriod(TenantMixin, Base):
    __tablename__ = "bell_periods"
    __table_args__ = (
        tenant_key("bell_periods"),
        UniqueConstraint("school_id", "period_no"),
        CheckConstraint("ends_at > starts_at", name="time_order"),
    )

    period_no: Mapped[int] = mapped_column(SmallInteger)
    label: Mapped[str] = mapped_column(String(32))
    starts_at: Mapped[time]
    ends_at: Mapped[time]


class TimetableEntry(TenantMixin, Base):
    __tablename__ = "timetable_entries"
    __table_args__ = (
        tenant_key("timetable_entries"),
        tfk("academic_year_id", "academic_years"),
        tfk("section_id", "sections"),
        tfk("subject_id", "subjects"),
        tfk("staff_id", "staff_profiles"),
        UniqueConstraint("school_id", "academic_year_id", "section_id", "day_of_week", "period_no"),
        # A teacher cannot be in two rooms at once.
        UniqueConstraint("school_id", "academic_year_id", "staff_id", "day_of_week", "period_no"),
        CheckConstraint("day_of_week BETWEEN 0 AND 6", name="day_of_week"),
    )

    academic_year_id: Mapped[uuid.UUID]
    section_id: Mapped[uuid.UUID]
    subject_id: Mapped[uuid.UUID]
    staff_id: Mapped[uuid.UUID | None]
    day_of_week: Mapped[int] = mapped_column(SmallInteger)  # 0 = Monday
    period_no: Mapped[int] = mapped_column(SmallInteger)
    room: Mapped[str | None] = mapped_column(String(32))


class Assessment(TenantMixin, Base):
    __tablename__ = "assessments"
    __table_args__ = (
        tenant_key("assessments"),
        tfk("academic_year_id", "academic_years"),
        tfk("term_id", "terms"),
        tfk("section_id", "sections"),
        tfk("subject_id", "subjects"),
        tfk("created_by_user_id", "users"),
        tfk("published_by_user_id", "users"),
        UniqueConstraint("school_id", "section_id", "subject_id", "name"),
        Index("ix_assessments_section_subject", "school_id", "section_id", "subject_id"),
        CheckConstraint("max_marks > 0", name="max_marks_positive"),
        CheckConstraint(check_in("kind", ASSESSMENT_KINDS), name="kind"),
        CheckConstraint("NOT is_published OR published_at IS NOT NULL", name="published_at_required"),
    )

    academic_year_id: Mapped[uuid.UUID]
    term_id: Mapped[uuid.UUID]
    section_id: Mapped[uuid.UUID]
    subject_id: Mapped[uuid.UUID]
    name: Mapped[str] = mapped_column(String(80))
    kind: Mapped[str] = mapped_column(String(16))
    max_marks: Mapped[Decimal] = mapped_column(Numeric(6, 2))
    held_on: Mapped[date]
    created_by_user_id: Mapped[uuid.UUID | None]
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    published_at: Mapped[datetime | None]
    published_by_user_id: Mapped[uuid.UUID | None]


class Mark(TenantMixin, Base):
    __tablename__ = "marks"
    __table_args__ = (
        tenant_key("marks"),
        tfk("assessment_id", "assessments", "CASCADE"),
        tfk("student_id", "student_profiles"),
        tfk("entered_by_user_id", "users"),
        UniqueConstraint("school_id", "assessment_id", "student_id"),
        Index("ix_marks_student", "school_id", "student_id"),
        CheckConstraint("marks_obtained IS NULL OR marks_obtained >= 0", name="non_negative"),
        CheckConstraint("NOT (is_absent AND marks_obtained IS NOT NULL)", name="absent_has_no_marks"),
    )

    assessment_id: Mapped[uuid.UUID]
    student_id: Mapped[uuid.UUID]
    marks_obtained: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    is_absent: Mapped[bool] = mapped_column(Boolean, default=False)
    remarks: Mapped[str | None] = mapped_column(String(255))
    entered_by_user_id: Mapped[uuid.UUID | None]
    updated_at: Mapped[datetime | None]


class MarkHistory(TenantMixin, Base):
    """Correction history for marks; never updated or deleted by the application."""

    __tablename__ = "mark_history"
    __table_args__ = (tenant_key("mark_history"), tfk("mark_id", "marks", "CASCADE"), tfk("changed_by_user_id", "users"))

    mark_id: Mapped[uuid.UUID]
    old_marks: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    new_marks: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    old_absent: Mapped[bool] = mapped_column(Boolean)
    new_absent: Mapped[bool] = mapped_column(Boolean)
    reason: Mapped[str | None] = mapped_column(String(255))
    changed_by_user_id: Mapped[uuid.UUID]


class LessonTopic(TenantMixin, Base):
    __tablename__ = "lesson_topics"
    __table_args__ = (
        tenant_key("lesson_topics"),
        tfk("academic_year_id", "academic_years"),
        tfk("section_id", "sections"),
        tfk("subject_id", "subjects"),
        tfk("completed_by_user_id", "users"),
        UniqueConstraint("school_id", "section_id", "subject_id", "sequence"),
        CheckConstraint(check_in("status", TOPIC_STATUSES), name="status"),
        CheckConstraint("status <> 'completed' OR completed_on IS NOT NULL", name="completed_on_required"),
        CheckConstraint("planned_periods > 0", name="planned_periods_positive"),
    )

    academic_year_id: Mapped[uuid.UUID]
    section_id: Mapped[uuid.UUID]
    subject_id: Mapped[uuid.UUID]
    sequence: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(160))
    description: Mapped[str | None] = mapped_column(Text)
    planned_periods: Mapped[int] = mapped_column(SmallInteger, default=1)
    periods_used: Mapped[int] = mapped_column(SmallInteger, default=0)
    status: Mapped[str] = mapped_column(String(16), default="planned")
    started_on: Mapped[date | None]
    completed_on: Mapped[date | None]
    completed_by_user_id: Mapped[uuid.UUID | None]
    updated_at: Mapped[datetime | None]


class TopicProgressLog(TenantMixin, Base):
    __tablename__ = "topic_progress_logs"
    __table_args__ = (
        tenant_key("topic_progress_logs"),
        tfk("topic_id", "lesson_topics", "CASCADE"),
        tfk("timetable_entry_id", "timetable_entries"),
        tfk("actor_user_id", "users"),
        Index("ix_topic_progress_logs_topic", "school_id", "topic_id"),
        CheckConstraint(check_in("action", TOPIC_ACTIONS), name="action"),
    )

    topic_id: Mapped[uuid.UUID]
    action: Mapped[str] = mapped_column(String(16))
    occurred_on: Mapped[date]
    timetable_entry_id: Mapped[uuid.UUID | None]
    notes: Mapped[str | None] = mapped_column(String(500))
    actor_user_id: Mapped[uuid.UUID]


class TopicFeedback(TenantMixin, Base):
    """A student's self-reported understanding of a topic (support signal, not an assessment)."""

    __tablename__ = "topic_feedback"
    __table_args__ = (
        tenant_key("topic_feedback"),
        tfk("topic_id", "lesson_topics", "CASCADE"),
        tfk("student_id", "student_profiles"),
        UniqueConstraint("school_id", "topic_id", "student_id"),
        CheckConstraint("understanding BETWEEN 1 AND 5", name="understanding_range"),
    )

    topic_id: Mapped[uuid.UUID]
    student_id: Mapped[uuid.UUID]
    understanding: Mapped[int] = mapped_column(SmallInteger)
    comment: Mapped[str | None] = mapped_column(Text)
    share_name: Mapped[bool] = mapped_column(Boolean, default=True)
