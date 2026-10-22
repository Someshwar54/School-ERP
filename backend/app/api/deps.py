"""Request dependencies: tenant resolution, authentication, CSRF and authorisation.

These checks are the security boundary. Frontend route guards only improve UX.
"""

from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from fastapi import Depends, Query, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import get_db, set_tenant
from app.core.errors import AppError, forbidden
from app.core.security import token_digest, tokens_match
from app.models import AuthSession, School, SchoolDomain, StaffProfile, StudentProfile, User
from app.schemas.common import PageParams
from app.services.auth import load_permissions
from app.services.auth_context import AuthContext

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
# Endpoints a user with a temporary password may still call when the change is enforced.
PASSWORD_CHANGE_ALLOWED = {"/api/v1/auth/me", "/api/v1/auth/logout", "/api/v1/auth/change-password"}


def client_ip(request: Request) -> str:
    if get_settings().trust_proxy_headers:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()[:64]
    return (request.client.host if request.client else "unknown")[:64]


def _request_host(request: Request) -> str:
    host = request.headers.get("host", "")
    if get_settings().trust_proxy_headers:
        host = request.headers.get("x-forwarded-host", host)
    return host.split(",")[0].strip().split(":")[0].lower()


def get_tenant(request: Request, db: Session = Depends(get_db)) -> School:
    """Resolve the school from the trusted hostname mapping (never from a client-supplied id)."""
    settings = get_settings()
    school = db.scalar(
        select(School)
        .join(SchoolDomain, SchoolDomain.school_id == School.id)
        .where(SchoolDomain.host == _request_host(request), School.is_active.is_(True))
    )
    if school is None and settings.tenant_fallback_to_default and settings.default_school_slug:
        school = db.scalar(select(School).where(School.slug == settings.default_school_slug, School.is_active.is_(True)))
    if school is None:
        raise AppError(404, "unknown_school", "This school is not configured.")
    set_tenant(db, school.id)
    return school


def _unauthenticated() -> AppError:
    return AppError(401, "unauthenticated", "Please sign in to continue.")


def get_auth(request: Request, school: School = Depends(get_tenant), db: Session = Depends(get_db)) -> AuthContext:
    settings = get_settings()
    raw = request.cookies.get(settings.session_cookie_name)
    if not raw:
        raise _unauthenticated()
    now = datetime.now(UTC)
    # RLS restricts this lookup to the resolved school: a session from another school is invisible.
    row = db.execute(
        select(AuthSession, User)
        .join(User, User.id == AuthSession.user_id)
        .where(AuthSession.token_hash == token_digest(raw), AuthSession.revoked_at.is_(None))
    ).first()
    if row is None:
        raise _unauthenticated()
    session, user = row
    idle_limit = session.last_seen_at + timedelta(minutes=settings.session_idle_minutes)
    if session.expires_at <= now or idle_limit <= now or not user.is_active:
        session.revoked_at = now
        db.commit()
        raise _unauthenticated()

    if request.method not in SAFE_METHODS:
        origin = request.headers.get("origin")
        if origin and origin not in settings.allowed_origins:
            raise forbidden("Request origin not allowed.")
        csrf = request.headers.get("x-csrf-token", "")
        if not csrf or not tokens_match(csrf, session.csrf_hash):
            raise AppError(403, "csrf_failed", "Security token missing or invalid. Please reload the page.")

    if (now - session.last_seen_at).total_seconds() > 60:
        session.last_seen_at = now
        db.commit()

    if settings.enforce_password_change and user.must_change_password and request.url.path not in PASSWORD_CHANGE_ALLOWED:
        raise AppError(403, "password_change_required", "You must change your temporary password first.")

    ctx = AuthContext(
        db=db, school=school, user=user, session=session, permissions=load_permissions(db, user.id), ip=client_ip(request)
    )
    if user.account_type == "student":
        ctx.student_id = db.scalar(select(StudentProfile.id).where(StudentProfile.user_id == user.id))
    elif user.account_type in ("staff", "management"):
        ctx.staff_id = db.scalar(select(StaffProfile.id).where(StaffProfile.user_id == user.id))
    return ctx


def require_account(*account_types: str) -> Callable[[AuthContext], AuthContext]:
    def _dep(ctx: AuthContext = Depends(get_auth)) -> AuthContext:
        if ctx.user.account_type not in account_types:
            raise forbidden("This area is not available for your account type.")
        return ctx

    return _dep


def require_permission(*permissions: str) -> Callable[[AuthContext], AuthContext]:
    def _dep(ctx: AuthContext = Depends(get_auth)) -> AuthContext:
        ctx.require(*permissions)
        return ctx

    return _dep


def student_ctx(ctx: AuthContext = Depends(require_account("student"))) -> AuthContext:
    if ctx.student_id is None:
        raise forbidden("No student profile is linked to this account.")
    return ctx


def staff_ctx(ctx: AuthContext = Depends(require_account("staff", "management"))) -> AuthContext:
    if ctx.staff_id is None:
        raise forbidden("No staff profile is linked to this account.")
    return ctx


def teacher_ctx(ctx: AuthContext = Depends(require_account("staff"))) -> AuthContext:
    if ctx.staff_id is None or not ctx.has("teaching.workspace"):
        raise forbidden("The teacher workspace is not enabled for this account.")
    return ctx


def management_ctx(ctx: AuthContext = Depends(require_account("management"))) -> AuthContext:
    ctx.require("mgmt.portal")
    return ctx


def management_permission(*permissions: str) -> Callable[[AuthContext], AuthContext]:
    """Management-portal account AND at least one of the given permissions."""

    def _dep(ctx: AuthContext = Depends(management_ctx)) -> AuthContext:
        ctx.require(*permissions)
        return ctx

    return _dep


def page_params(page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100)) -> PageParams:
    """Standard ?page=&page_size= pagination parameters."""
    return PageParams(page=page, page_size=page_size)


MonthParam = Query(default=None, pattern=r"^\d{4}-(0[1-9]|1[0-2])$", description="YYYY-MM")
