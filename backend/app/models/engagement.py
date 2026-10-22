"""Announcements, events, complaints, feedback and teacher-student messaging."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, Index, SmallInteger, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TenantMixin, check_in, tenant_key, tfk

AUDIENCES = ("all", "students", "staff", "management")
COMPLAINT_STATUSES = ("open", "in_review", "resolved", "closed")
COMPLAINT_CATEGORIES = ("academic", "facilities", "transport", "conduct", "fees", "other")
FEEDBACK_CATEGORIES = ("teaching", "facilities", "transport", "communication", "general")


class Announcement(TenantMixin, Base):
    __tablename__ = "announcements"
    __table_args__ = (
        tenant_key("announcements"),
        tfk("section_id", "sections"),
        tfk("created_by_user_id", "users"),
        Index("ix_announcements_published", "school_id", "published_at"),
        CheckConstraint(check_in("audience", AUDIENCES), name="audience"),
    )

    title: Mapped[str] = mapped_column(String(160))
    body: Mapped[str] = mapped_column(Text)
    audience: Mapped[str] = mapped_column(String(16))
    section_id: Mapped[uuid.UUID | None]
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False)
    published_at: Mapped[datetime]
    expires_at: Mapped[datetime | None]
    created_by_user_id: Mapped[uuid.UUID | None]


class SchoolEvent(TenantMixin, Base):
    __tablename__ = "events"
    __table_args__ = (
        tenant_key("events"),
        Index("ix_events_starts", "school_id", "starts_at"),
        CheckConstraint(check_in("audience", AUDIENCES), name="audience"),
        CheckConstraint("ends_at >= starts_at", name="time_order"),
    )

    title: Mapped[str] = mapped_column(String(160))
    description: Mapped[str] = mapped_column(Text)
    starts_at: Mapped[datetime]
    ends_at: Mapped[datetime]
    location: Mapped[str] = mapped_column(String(120))
    audience: Mapped[str] = mapped_column(String(16))


class Complaint(TenantMixin, Base):
    __tablename__ = "complaints"
    __table_args__ = (
        tenant_key("complaints"),
        tfk("raised_by_user_id", "users"),
        tfk("student_id", "student_profiles"),
        tfk("section_id", "sections"),
        tfk("assigned_staff_id", "staff_profiles"),
        UniqueConstraint("school_id", "reference_no"),
        Index("ix_complaints_status", "school_id", "status"),
        Index("ix_complaints_assigned", "school_id", "assigned_staff_id"),
        CheckConstraint(check_in("status", COMPLAINT_STATUSES), name="status"),
        CheckConstraint(check_in("category", COMPLAINT_CATEGORIES), name="category"),
        # Confidential complaints are never routed to an individual teacher.
        CheckConstraint("NOT is_confidential OR assigned_staff_id IS NULL", name="confidential_not_assigned"),
    )

    reference_no: Mapped[str] = mapped_column(String(24))
    raised_by_user_id: Mapped[uuid.UUID]
    student_id: Mapped[uuid.UUID | None]
    section_id: Mapped[uuid.UUID | None]
    category: Mapped[str] = mapped_column(String(16))
    subject: Mapped[str] = mapped_column(String(160))
    description: Mapped[str] = mapped_column(Text)
    is_confidential: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(16), default="open")
    assigned_staff_id: Mapped[uuid.UUID | None]
    updated_at: Mapped[datetime | None]
    resolved_at: Mapped[datetime | None]


class ComplaintUpdate(TenantMixin, Base):
    __tablename__ = "complaint_updates"
    __table_args__ = (
        tenant_key("complaint_updates"),
        tfk("complaint_id", "complaints", "CASCADE"),
        tfk("author_user_id", "users"),
        Index("ix_complaint_updates_complaint", "school_id", "complaint_id"),
    )

    complaint_id: Mapped[uuid.UUID]
    author_user_id: Mapped[uuid.UUID]
    note: Mapped[str] = mapped_column(Text)
    new_status: Mapped[str | None] = mapped_column(String(16))


class Feedback(TenantMixin, Base):
    """General feedback. Anonymous submissions store no submitter id at all."""

    __tablename__ = "feedback"
    __table_args__ = (
        tenant_key("feedback"),
        tfk("submitted_by_user_id", "users"),
        CheckConstraint("rating BETWEEN 1 AND 5", name="rating_range"),
        CheckConstraint(check_in("category", FEEDBACK_CATEGORIES), name="category"),
        CheckConstraint("NOT is_anonymous OR submitted_by_user_id IS NULL", name="anonymous_has_no_submitter"),
    )

    submitted_by_user_id: Mapped[uuid.UUID | None]
    account_type: Mapped[str] = mapped_column(String(16))
    category: Mapped[str] = mapped_column(String(16))
    rating: Mapped[int] = mapped_column(SmallInteger)
    comment: Mapped[str | None] = mapped_column(Text)
    is_anonymous: Mapped[bool] = mapped_column(Boolean, default=False)


class MessageThread(TenantMixin, Base):
    __tablename__ = "message_threads"
    __table_args__ = (
        tenant_key("message_threads"),
        tfk("student_id", "student_profiles"),
        tfk("staff_id", "staff_profiles"),
        tfk("created_by_user_id", "users"),
        Index("ix_message_threads_student", "school_id", "student_id"),
        Index("ix_message_threads_staff", "school_id", "staff_id"),
    )

    student_id: Mapped[uuid.UUID]
    staff_id: Mapped[uuid.UUID]
    subject: Mapped[str] = mapped_column(String(160))
    created_by_user_id: Mapped[uuid.UUID]
    last_message_at: Mapped[datetime]


class Message(TenantMixin, Base):
    __tablename__ = "messages"
    __table_args__ = (
        tenant_key("messages"),
        tfk("thread_id", "message_threads", "CASCADE"),
        tfk("sender_user_id", "users"),
        Index("ix_messages_thread", "school_id", "thread_id"),
    )

    thread_id: Mapped[uuid.UUID]
    sender_user_id: Mapped[uuid.UUID]
    body: Mapped[str] = mapped_column(Text)
