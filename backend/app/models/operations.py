"""Staff operations, approvals, documents, enquiries, teacher evaluation and audit."""

import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import BigInteger, CheckConstraint, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TenantMixin, check_in, tenant_key, tfk

LEAVE_STATUSES = ("pending", "approved", "rejected", "cancelled")
LEAVE_TYPES = ("casual", "sick", "earned", "unpaid")
EVALUATION_STATUSES = ("draft", "finalized")


class LeaveRequest(TenantMixin, Base):
    __tablename__ = "leave_requests"
    __table_args__ = (
        tenant_key("leave_requests"),
        tfk("staff_id", "staff_profiles"),
        tfk("decided_by_user_id", "users"),
        Index("ix_leave_requests_status", "school_id", "status"),
        CheckConstraint(check_in("status", LEAVE_STATUSES), name="status"),
        CheckConstraint(check_in("leave_type", LEAVE_TYPES), name="leave_type"),
        CheckConstraint("ends_on >= starts_on", name="date_order"),
    )

    staff_id: Mapped[uuid.UUID]
    leave_type: Mapped[str] = mapped_column(String(16))
    starts_on: Mapped[date]
    ends_on: Mapped[date]
    reason: Mapped[str] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(16), default="pending")
    decided_by_user_id: Mapped[uuid.UUID | None]
    decided_at: Mapped[datetime | None]
    decision_comment: Mapped[str | None] = mapped_column(String(500))


class ApprovalRecord(TenantMixin, Base):
    """Immutable decision log for anything that needs approval (leave, mark publication, ...)."""

    __tablename__ = "approval_records"
    __table_args__ = (
        tenant_key("approval_records"),
        tfk("decided_by_user_id", "users"),
        Index("ix_approval_records_entity", "school_id", "entity_type", "entity_id"),
    )

    entity_type: Mapped[str] = mapped_column(String(32))
    entity_id: Mapped[uuid.UUID]
    decision: Mapped[str] = mapped_column(String(16))
    comment: Mapped[str | None] = mapped_column(String(500))
    decided_by_user_id: Mapped[uuid.UUID]


class StaffDuty(TenantMixin, Base):
    __tablename__ = "staff_duties"
    __table_args__ = (
        tenant_key("staff_duties"),
        tfk("staff_id", "staff_profiles"),
        Index("ix_staff_duties_staff", "school_id", "staff_id"),
        CheckConstraint(check_in("status", ("assigned", "done")), name="status"),
    )

    staff_id: Mapped[uuid.UUID]
    title: Mapped[str] = mapped_column(String(160))
    details: Mapped[str | None] = mapped_column(Text)
    duty_date: Mapped[date]
    status: Mapped[str] = mapped_column(String(16), default="assigned")


class Document(TenantMixin, Base):
    """Document metadata. File storage is not connected in the prototype (storage_key stays NULL)."""

    __tablename__ = "documents"
    __table_args__ = (
        tenant_key("documents"),
        tfk("uploaded_by_user_id", "users"),
        Index("ix_documents_owner", "school_id", "owner_type", "owner_id"),
        CheckConstraint(check_in("owner_type", ("student", "staff", "school")), name="owner_type"),
    )

    owner_type: Mapped[str] = mapped_column(String(16))
    owner_id: Mapped[uuid.UUID | None]
    title: Mapped[str] = mapped_column(String(160))
    category: Mapped[str] = mapped_column(String(32))
    storage_key: Mapped[str | None] = mapped_column(String(255))
    mime_type: Mapped[str | None] = mapped_column(String(80))
    size_bytes: Mapped[int | None] = mapped_column(BigInteger)
    uploaded_by_user_id: Mapped[uuid.UUID | None]


class AdmissionEnquiry(TenantMixin, Base):
    __tablename__ = "admission_enquiries"
    __table_args__ = (
        tenant_key("admission_enquiries"),
        Index("ix_admission_enquiries_created", "school_id", "created_at"),
        CheckConstraint(check_in("status", ("new", "contacted", "closed")), name="status"),
    )

    parent_name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(160))
    phone: Mapped[str] = mapped_column(String(20))
    grade_sought: Mapped[str] = mapped_column(String(32))
    message: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(16), default="new")


class EvaluationRubric(TenantMixin, Base):
    __tablename__ = "evaluation_rubrics"
    __table_args__ = (tenant_key("evaluation_rubrics"),)

    name: Mapped[str] = mapped_column(String(120))
    # [{"key", "label", "description", "max_score"}]
    criteria: Mapped[list[dict[str, Any]]] = mapped_column(JSONB)
    is_active: Mapped[bool] = mapped_column(default=True)


class TeacherEvaluation(TenantMixin, Base):
    """Human-reviewed evaluation. The system never computes a final rating on its own."""

    __tablename__ = "teacher_evaluations"
    __table_args__ = (
        tenant_key("teacher_evaluations"),
        tfk("staff_id", "staff_profiles"),
        tfk("rubric_id", "evaluation_rubrics"),
        tfk("created_by_user_id", "users"),
        tfk("finalized_by_user_id", "users"),
        CheckConstraint(check_in("status", EVALUATION_STATUSES), name="status"),
        CheckConstraint(
            "status <> 'finalized' OR (finalized_by_user_id IS NOT NULL AND reviewer_comment IS NOT NULL)",
            name="finalized_requires_reviewer",
        ),
    )

    staff_id: Mapped[uuid.UUID]
    rubric_id: Mapped[uuid.UUID]
    period_label: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(16), default="draft")
    scores: Mapped[dict[str, Any]]
    evidence_notes: Mapped[str] = mapped_column(Text)
    reviewer_comment: Mapped[str | None] = mapped_column(Text)
    created_by_user_id: Mapped[uuid.UUID]
    finalized_by_user_id: Mapped[uuid.UUID | None]
    finalized_at: Mapped[datetime | None]
    updated_at: Mapped[datetime | None]


class AuditEvent(TenantMixin, Base):
    """Append-only (UPDATE/DELETE blocked by a database trigger)."""

    __tablename__ = "audit_events"
    __table_args__ = (
        Index("ix_audit_events_created", "school_id", "created_at"),
        Index("ix_audit_events_entity", "school_id", "entity_type", "entity_id"),
    )

    actor_user_id: Mapped[uuid.UUID | None]
    action: Mapped[str] = mapped_column(String(64))
    entity_type: Mapped[str | None] = mapped_column(String(32))
    entity_id: Mapped[str | None] = mapped_column(String(64))
    details: Mapped[dict[str, Any]]
    ip: Mapped[str | None] = mapped_column(String(64))
