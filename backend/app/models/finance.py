"""Fee ledger. Balances are always derived from these records, never stored separately."""

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import CheckConstraint, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TenantMixin, check_in, tenant_key, tfk

LINE_TYPES = ("charge", "concession", "adjustment")
PAYMENT_METHODS = ("cash", "upi", "card", "bank_transfer", "cheque")


class FeeHead(TenantMixin, Base):
    __tablename__ = "fee_heads"
    __table_args__ = (tenant_key("fee_heads"), UniqueConstraint("school_id", "code"))

    code: Mapped[str] = mapped_column(String(32))
    name: Mapped[str] = mapped_column(String(120))


class FeeStructure(TenantMixin, Base):
    __tablename__ = "fee_structures"
    __table_args__ = (
        tenant_key("fee_structures"),
        tfk("academic_year_id", "academic_years"),
        tfk("class_id", "classes"),
        tfk("fee_head_id", "fee_heads"),
        tfk("term_id", "terms"),
        UniqueConstraint("school_id", "academic_year_id", "class_id", "fee_head_id", "term_id"),
        CheckConstraint("amount >= 0", name="non_negative"),
    )

    academic_year_id: Mapped[uuid.UUID]
    class_id: Mapped[uuid.UUID]
    fee_head_id: Mapped[uuid.UUID]
    term_id: Mapped[uuid.UUID]
    amount: Mapped[Decimal]


class Invoice(TenantMixin, Base):
    """Paid / partially paid is derived from allocations; only issue/cancel is stored."""

    __tablename__ = "invoices"
    __table_args__ = (
        tenant_key("invoices"),
        tfk("student_id", "student_profiles"),
        tfk("academic_year_id", "academic_years"),
        tfk("term_id", "terms"),
        UniqueConstraint("school_id", "invoice_no"),
        Index("ix_invoices_student", "school_id", "student_id"),
        CheckConstraint(check_in("status", ("issued", "cancelled")), name="status"),
        CheckConstraint("due_on >= issued_on", name="date_order"),
    )

    student_id: Mapped[uuid.UUID]
    academic_year_id: Mapped[uuid.UUID]
    term_id: Mapped[uuid.UUID | None]
    invoice_no: Mapped[str] = mapped_column(String(32))
    issued_on: Mapped[date]
    due_on: Mapped[date]
    status: Mapped[str] = mapped_column(String(16), default="issued")


class InvoiceLine(TenantMixin, Base):
    """Charges and concessions are positive amounts; adjustments are signed."""

    __tablename__ = "invoice_lines"
    __table_args__ = (
        tenant_key("invoice_lines"),
        tfk("invoice_id", "invoices", "CASCADE"),
        tfk("fee_head_id", "fee_heads"),
        Index("ix_invoice_lines_invoice", "school_id", "invoice_id"),
        CheckConstraint(check_in("line_type", LINE_TYPES), name="line_type"),
        CheckConstraint("line_type = 'adjustment' OR amount > 0", name="positive_unless_adjustment"),
    )

    invoice_id: Mapped[uuid.UUID]
    fee_head_id: Mapped[uuid.UUID | None]
    line_type: Mapped[str] = mapped_column(String(16))
    description: Mapped[str] = mapped_column(String(160))
    amount: Mapped[Decimal]


class Payment(TenantMixin, Base):
    __tablename__ = "payments"
    __table_args__ = (
        tenant_key("payments"),
        tfk("student_id", "student_profiles"),
        tfk("received_by_user_id", "users"),
        UniqueConstraint("school_id", "receipt_no"),
        Index("ix_payments_student", "school_id", "student_id"),
        Index("ix_payments_paid_on", "school_id", "paid_on"),
        CheckConstraint("amount > 0", name="positive"),
        CheckConstraint(check_in("method", PAYMENT_METHODS), name="method"),
    )

    student_id: Mapped[uuid.UUID]
    receipt_no: Mapped[str] = mapped_column(String(32))
    amount: Mapped[Decimal]
    paid_on: Mapped[date]
    method: Mapped[str] = mapped_column(String(16))
    reference: Mapped[str | None] = mapped_column(String(64))
    received_by_user_id: Mapped[uuid.UUID | None]


class PaymentAllocation(TenantMixin, Base):
    __tablename__ = "payment_allocations"
    __table_args__ = (
        tenant_key("payment_allocations"),
        tfk("payment_id", "payments", "CASCADE"),
        tfk("invoice_id", "invoices"),
        UniqueConstraint("school_id", "payment_id", "invoice_id"),
        Index("ix_payment_allocations_invoice", "school_id", "invoice_id"),
        CheckConstraint("amount > 0", name="positive"),
    )

    payment_id: Mapped[uuid.UUID]
    invoice_id: Mapped[uuid.UUID]
    amount: Mapped[Decimal]


class Refund(TenantMixin, Base):
    __tablename__ = "refunds"
    __table_args__ = (
        tenant_key("refunds"),
        tfk("payment_id", "payments"),
        tfk("approved_by_user_id", "users"),
        CheckConstraint("amount > 0", name="positive"),
    )

    payment_id: Mapped[uuid.UUID]
    amount: Mapped[Decimal]
    refunded_on: Mapped[date]
    reason: Mapped[str] = mapped_column(String(255))
    approved_by_user_id: Mapped[uuid.UUID]
