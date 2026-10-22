"""Declarative base and tenant helpers.

Tenant isolation is enforced in three layers:
1. Every school-owned row carries `school_id`.
2. Every reference between school-owned rows is a *composite* foreign key
   `(school_id, x_id) -> parent(school_id, id)`, so the database itself rejects a
   record in school A that points at a record in school B.
3. PostgreSQL row-level security (see the initial migration) hides other schools' rows.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import DateTime, ForeignKey, ForeignKeyConstraint, MetaData, Numeric, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_N_label)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_N_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)
    # All timestamps are timezone-aware (stored as UTC); money is exact decimal.
    type_annotation_map = {datetime: DateTime(timezone=True), Decimal: Numeric(12, 2), dict[str, Any]: JSONB}


class TenantMixin:
    """Primary key, owning school and creation timestamp for school-owned tables."""

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


def tenant_key(table: str) -> UniqueConstraint:
    """(school_id, id) uniqueness, the target of composite tenant foreign keys."""
    return UniqueConstraint("school_id", "id", name=f"uq_{table}_tenant_key")


def tfk(column: str, parent: str, ondelete: str = "RESTRICT") -> ForeignKeyConstraint:
    """Composite same-school foreign key."""
    return ForeignKeyConstraint(["school_id", column], [f"{parent}.school_id", f"{parent}.id"], ondelete=ondelete)


def check_in(column: str, values: tuple[str, ...]) -> str:
    return f"{column} IN ({', '.join(repr(v) for v in values)})"
