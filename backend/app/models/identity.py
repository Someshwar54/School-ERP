"""Users, credentials, roles, permissions, sessions and login attempts."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, ForeignKeyConstraint, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TenantMixin, check_in, tenant_key, tfk

ACCOUNT_TYPES = ("student", "staff", "management", "guardian")
ROLE_KINDS = ("staff", "management")


class User(TenantMixin, Base):
    """A login identity. `login_id` is the school-issued Student / Staff / Director ID."""

    __tablename__ = "users"
    __table_args__ = (
        tenant_key("users"),
        UniqueConstraint("school_id", "login_id"),
        CheckConstraint(check_in("account_type", ACCOUNT_TYPES), name="account_type"),
    )

    login_id: Mapped[str] = mapped_column(String(32))
    account_type: Mapped[str] = mapped_column(String(16))
    display_name: Mapped[str] = mapped_column(String(160))
    password_hash: Mapped[str] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    must_change_password: Mapped[bool] = mapped_column(Boolean, default=False)
    password_changed_at: Mapped[datetime | None]
    last_login_at: Mapped[datetime | None]


class Permission(Base):
    """Global permission catalogue (codes are referenced by school-defined roles)."""

    __tablename__ = "permissions"

    code: Mapped[str] = mapped_column(String(64), primary_key=True)
    category: Mapped[str] = mapped_column(String(32))
    description: Mapped[str] = mapped_column(String(255))


class Role(TenantMixin, Base):
    __tablename__ = "roles"
    __table_args__ = (
        tenant_key("roles"),
        UniqueConstraint("school_id", "code"),
        CheckConstraint(check_in("kind", ROLE_KINDS), name="kind"),
    )

    code: Mapped[str] = mapped_column(String(64))
    name: Mapped[str] = mapped_column(String(120))
    kind: Mapped[str] = mapped_column(String(16))
    description: Mapped[str] = mapped_column(String(255), default="")


class RolePermission(Base):
    __tablename__ = "role_permissions"
    __table_args__ = (
        tfk("role_id", "roles", "CASCADE"),
        ForeignKeyConstraint(["permission_code"], ["permissions.code"], ondelete="CASCADE"),
    )

    school_id: Mapped[uuid.UUID] = mapped_column(index=True)
    role_id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    permission_code: Mapped[str] = mapped_column(String(64), primary_key=True)


class UserRole(Base):
    __tablename__ = "user_roles"
    __table_args__ = (tfk("user_id", "users", "CASCADE"), tfk("role_id", "roles", "CASCADE"))

    school_id: Mapped[uuid.UUID] = mapped_column(index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    role_id: Mapped[uuid.UUID] = mapped_column(primary_key=True)


class AuthSession(TenantMixin, Base):
    """Server-side session. Only SHA-256 digests of the session and CSRF tokens are stored."""

    __tablename__ = "auth_sessions"
    __table_args__ = (
        tenant_key("auth_sessions"),
        tfk("user_id", "users", "CASCADE"),
        Index("ix_auth_sessions_user", "school_id", "user_id"),
    )

    user_id: Mapped[uuid.UUID]
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    csrf_hash: Mapped[str] = mapped_column(String(64))
    portal: Mapped[str] = mapped_column(String(16))
    expires_at: Mapped[datetime]
    last_seen_at: Mapped[datetime]
    revoked_at: Mapped[datetime | None]
    ip: Mapped[str | None] = mapped_column(String(64))
    user_agent: Mapped[str | None] = mapped_column(String(255))


class LoginAttempt(TenantMixin, Base):
    """Login audit + rate limiting. Identifiers are hashed; passwords are never stored."""

    __tablename__ = "login_attempts"
    __table_args__ = (
        Index("ix_login_attempts_identifier", "school_id", "identifier_hash", "created_at"),
        Index("ix_login_attempts_ip", "school_id", "ip", "created_at"),
    )

    identifier_hash: Mapped[str] = mapped_column(String(64))
    ip: Mapped[str] = mapped_column(String(64))
    portal: Mapped[str] = mapped_column(String(16))
    succeeded: Mapped[bool] = mapped_column(Boolean)
