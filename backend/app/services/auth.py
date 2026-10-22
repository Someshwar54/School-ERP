"""Authentication: login with rate limiting, sessions, logout and password change."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError
from app.core.security import (
    hash_password,
    identifier_digest,
    needs_rehash,
    new_token,
    token_digest,
    verify_password,
)
from app.models import AuthSession, LoginAttempt, RolePermission, School, StudentProfile, User, UserRole
from app.services import audit
from app.services.rbac import PORTAL_ACCOUNT_TYPE

GENERIC_FAILURE = "The ID or password is incorrect."


@dataclass
class LoginResult:
    user: User
    session_token: str
    csrf_token: str


def load_permissions(db: Session, user_id: UUID) -> frozenset[str]:
    rows = db.scalars(
        select(RolePermission.permission_code)
        .join(UserRole, UserRole.role_id == RolePermission.role_id)
        .where(UserRole.user_id == user_id)
    )
    return frozenset(rows)


def normalize_login_id(login_id: str) -> str:
    return login_id.strip().upper()


def _recent_failures(db: Session, since: datetime, **where: str) -> int:
    column = LoginAttempt.identifier_hash if "identifier_hash" in where else LoginAttempt.ip
    value = where.get("identifier_hash") or where["ip"]
    last_success = db.scalar(select(func.max(LoginAttempt.created_at)).where(column == value, LoginAttempt.succeeded.is_(True)))
    floor = max(since, last_success) if last_success else since
    return (
        db.scalar(select(func.count()).where(column == value, LoginAttempt.succeeded.is_(False), LoginAttempt.created_at > floor))
        or 0
    )


def login(db: Session, school: School, portal: str, login_id: str, password: str, ip: str, user_agent: str) -> LoginResult:
    settings = get_settings()
    login_id = normalize_login_id(login_id)
    ident = identifier_digest(str(school.id), login_id)
    since = datetime.now(UTC) - timedelta(minutes=settings.login_window_minutes)

    if (
        _recent_failures(db, since, identifier_hash=ident) >= settings.login_max_failures_per_identifier
        or _recent_failures(db, since, ip=ip) >= settings.login_max_failures_per_ip
    ):
        audit.record(db, school.id, "auth.login_rate_limited", details={"portal": portal}, ip=ip)
        db.commit()
        raise AppError(429, "rate_limited", "Too many sign-in attempts. Please wait a few minutes and try again.")

    user = db.scalar(select(User).where(User.login_id == login_id))
    password_ok = verify_password(user.password_hash if user else None, password)
    allowed = user is not None and password_ok and user.is_active and user.account_type == PORTAL_ACCOUNT_TYPE[portal]
    if allowed and user is not None and portal == "director":
        allowed = "mgmt.portal" in load_permissions(db, user.id)
    if allowed and user is not None and user.account_type == "student":
        allowed = bool(db.scalar(select(StudentProfile.is_active).where(StudentProfile.user_id == user.id)))

    db.add(LoginAttempt(school_id=school.id, identifier_hash=ident, ip=ip, portal=portal, succeeded=allowed))
    if not allowed or user is None:
        # Same message whether the account exists, the password is wrong or the portal is wrong.
        audit.record(db, school.id, "auth.login_failed", details={"portal": portal}, ip=ip)
        db.commit()
        raise AppError(401, "invalid_credentials", GENERIC_FAILURE)

    if needs_rehash(user.password_hash):
        user.password_hash = hash_password(password)
    now = datetime.now(UTC)
    session_token, csrf_token = new_token(), new_token()
    db.add(
        AuthSession(
            school_id=school.id,
            user_id=user.id,
            token_hash=token_digest(session_token),
            csrf_hash=token_digest(csrf_token),
            portal=portal,
            expires_at=now + timedelta(hours=settings.session_ttl_hours),
            last_seen_at=now,
            ip=ip,
            user_agent=user_agent[:255],
        )
    )
    user.last_login_at = now
    audit.record(db, school.id, "auth.login", actor_user_id=user.id, details={"portal": portal}, ip=ip)
    db.commit()
    return LoginResult(user=user, session_token=session_token, csrf_token=csrf_token)


def logout(db: Session, session: AuthSession) -> None:
    session.revoked_at = datetime.now(UTC)
    audit.record(db, session.school_id, "auth.logout", actor_user_id=session.user_id)
    db.commit()


def revoke_other_sessions(db: Session, user: User, keep: AuthSession) -> int:
    result = db.execute(
        update(AuthSession)
        .where(AuthSession.user_id == user.id, AuthSession.id != keep.id, AuthSession.revoked_at.is_(None))
        .values(revoked_at=datetime.now(UTC))
    )
    return result.rowcount or 0  # type: ignore[attr-defined]


def validate_new_password(user: User, new_password: str, forbidden_values: list[str]) -> None:
    settings = get_settings()
    problems = []
    if len(new_password) < settings.min_password_length:
        problems.append(f"Use at least {settings.min_password_length} characters.")
    if not any(c.isalpha() for c in new_password) or not any(c.isdigit() for c in new_password):
        problems.append("Include both letters and numbers.")
    lowered = new_password.lower()
    if any(v and v.lower() in lowered for v in [user.login_id, *forbidden_values]):
        problems.append("Do not use your ID or phone number.")
    if problems:
        raise AppError(400, "weak_password", " ".join(problems))


def change_password(db: Session, user: User, session: AuthSession, current: str, new: str, ip: str) -> int:
    if not verify_password(user.password_hash, current):
        raise AppError(400, "invalid_current_password", "Your current password is incorrect.")
    phone = db.scalar(select(StudentProfile.phone).where(StudentProfile.user_id == user.id))
    validate_new_password(user, new, [phone or ""])
    if verify_password(user.password_hash, new):
        raise AppError(400, "weak_password", "Choose a password different from your current one.")
    user.password_hash = hash_password(new)
    user.must_change_password = False
    user.password_changed_at = datetime.now(UTC)
    revoked = revoke_other_sessions(db, user, session)
    audit.record(
        db, user.school_id, "auth.password_changed", actor_user_id=user.id, details={"other_sessions_revoked": revoked}, ip=ip
    )
    db.commit()
    return revoked
