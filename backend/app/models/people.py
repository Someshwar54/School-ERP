"""Student, guardian and staff profiles."""

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TenantMixin, check_in, tenant_key, tfk

STAFF_TYPES = ("teaching", "non_teaching", "management")
GUARDIAN_VERIFICATION = ("pending", "verified", "revoked")


class StudentProfile(TenantMixin, Base):
    __tablename__ = "student_profiles"
    __table_args__ = (
        tenant_key("student_profiles"),
        tfk("user_id", "users"),
        UniqueConstraint("school_id", "student_code"),
        UniqueConstraint("school_id", "user_id"),
        UniqueConstraint("school_id", "admission_no"),
        Index("ix_student_profiles_name", "school_id", "last_name", "first_name"),
    )

    user_id: Mapped[uuid.UUID]
    student_code: Mapped[str] = mapped_column(String(32))
    admission_no: Mapped[str] = mapped_column(String(32))
    first_name: Mapped[str] = mapped_column(String(80))
    last_name: Mapped[str] = mapped_column(String(80))
    date_of_birth: Mapped[date]
    gender: Mapped[str] = mapped_column(String(16))
    admission_date: Mapped[date]
    # Private contact data: never returned by public endpoints and only to authorised roles.
    phone: Mapped[str] = mapped_column(String(20))
    email: Mapped[str | None] = mapped_column(String(160))
    address: Mapped[str | None] = mapped_column(Text)
    blood_group: Mapped[str | None] = mapped_column(String(4))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Guardian(TenantMixin, Base):
    """A parent/guardian. `user_id` is set once a guardian login is activated (future)."""

    __tablename__ = "guardians"
    __table_args__ = (tenant_key("guardians"), tfk("user_id", "users"), UniqueConstraint("school_id", "user_id"))

    user_id: Mapped[uuid.UUID | None]
    full_name: Mapped[str] = mapped_column(String(160))
    phone: Mapped[str] = mapped_column(String(20))
    email: Mapped[str | None] = mapped_column(String(160))
    occupation: Mapped[str | None] = mapped_column(String(120))


class StudentGuardian(TenantMixin, Base):
    """Verified relationship that will authorise guardian access to a child's records."""

    __tablename__ = "student_guardians"
    __table_args__ = (
        tenant_key("student_guardians"),
        tfk("student_id", "student_profiles", "CASCADE"),
        tfk("guardian_id", "guardians", "CASCADE"),
        tfk("verified_by_user_id", "users"),
        UniqueConstraint("school_id", "student_id", "guardian_id"),
        CheckConstraint(check_in("verification_status", GUARDIAN_VERIFICATION), name="verification_status"),
        CheckConstraint(
            "verification_status <> 'verified' OR (verified_at IS NOT NULL AND verified_by_user_id IS NOT NULL)",
            name="verified_requires_verifier",
        ),
    )

    student_id: Mapped[uuid.UUID]
    guardian_id: Mapped[uuid.UUID]
    relationship: Mapped[str] = mapped_column(String(32))
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    verification_status: Mapped[str] = mapped_column(String(16), default="pending")
    verified_at: Mapped[datetime | None]
    verified_by_user_id: Mapped[uuid.UUID | None]
    can_view_academics: Mapped[bool] = mapped_column(Boolean, default=True)
    can_view_fees: Mapped[bool] = mapped_column(Boolean, default=True)


class StaffProfile(TenantMixin, Base):
    __tablename__ = "staff_profiles"
    __table_args__ = (
        tenant_key("staff_profiles"),
        tfk("user_id", "users"),
        UniqueConstraint("school_id", "staff_code"),
        UniqueConstraint("school_id", "user_id"),
        CheckConstraint(check_in("staff_type", STAFF_TYPES), name="staff_type"),
    )

    user_id: Mapped[uuid.UUID]
    staff_code: Mapped[str] = mapped_column(String(32))
    first_name: Mapped[str] = mapped_column(String(80))
    last_name: Mapped[str] = mapped_column(String(80))
    staff_type: Mapped[str] = mapped_column(String(16))
    designation: Mapped[str] = mapped_column(String(120))
    department: Mapped[str] = mapped_column(String(80))
    joining_date: Mapped[date]
    qualification: Mapped[str | None] = mapped_column(String(160))
    phone: Mapped[str | None] = mapped_column(String(20))
    email: Mapped[str | None] = mapped_column(String(160))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    # Only explicitly approved fields may appear on the public website.
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    public_bio: Mapped[str | None] = mapped_column(Text)


class StaffCompensation(TenantMixin, Base):
    """Sensitive: readable only with the `payroll.view` permission."""

    __tablename__ = "staff_compensation"
    __table_args__ = (
        tenant_key("staff_compensation"),
        tfk("staff_id", "staff_profiles"),
        UniqueConstraint("school_id", "staff_id", "effective_from"),
        CheckConstraint("monthly_gross >= 0", name="non_negative"),
    )

    staff_id: Mapped[uuid.UUID]
    effective_from: Mapped[date]
    pay_grade: Mapped[str] = mapped_column(String(16))
    monthly_gross: Mapped[Decimal]
    bank_account_last4: Mapped[str | None] = mapped_column(String(4))
