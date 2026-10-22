"""Sign-in, sign-out, current user and password management."""

from typing import Any

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from app.api.deps import client_ip, get_auth, get_tenant
from app.api.responses import AUTHENTICATED_ERRORS
from app.core.config import get_settings
from app.core.db import get_db
from app.core.errors import forbidden
from app.models import School
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    LoginResponse,
    MeResponse,
    PasswordChangedResponse,
    SessionsRevokedResponse,
)
from app.services import auth as auth_service
from app.services import workspace
from app.services.auth_context import AuthContext

router = APIRouter(prefix="/auth", tags=["auth"], responses=AUTHENTICATED_ERRORS)


def _set_cookies(response: Response, session_token: str, csrf_token: str) -> None:
    s = get_settings()
    max_age = s.session_ttl_hours * 3600
    response.set_cookie(
        s.session_cookie_name, session_token, max_age=max_age, httponly=True, secure=s.cookie_secure, samesite="lax", path="/"
    )
    # Readable by the frontend so it can echo it in the X-CSRF-Token header.
    response.set_cookie(
        s.csrf_cookie_name, csrf_token, max_age=max_age, httponly=False, secure=s.cookie_secure, samesite="lax", path="/"
    )


def _clear_cookies(response: Response) -> None:
    s = get_settings()
    response.delete_cookie(s.session_cookie_name, path="/")
    response.delete_cookie(s.csrf_cookie_name, path="/")


@router.post("/login", response_model=LoginResponse, summary="Sign in through a portal")
def login(
    body: LoginRequest, request: Request, response: Response, school: School = Depends(get_tenant), db: Session = Depends(get_db)
) -> dict[str, Any]:
    origin = request.headers.get("origin")
    if origin and origin not in get_settings().allowed_origins:
        raise forbidden("Request origin not allowed.")
    result = auth_service.login(
        db, school, body.portal, body.login_id, body.password, client_ip(request), request.headers.get("user-agent", "")
    )
    _set_cookies(response, result.session_token, result.csrf_token)
    return {"home": workspace.DEFAULT_HOME[result.user.account_type], "must_change_password": result.user.must_change_password}


@router.post("/logout", summary="Sign out and revoke this session")
def logout(response: Response, ctx: AuthContext = Depends(get_auth)) -> dict[str, bool]:
    auth_service.logout(ctx.db, ctx.session)
    _clear_cookies(response)
    return {"ok": True}


@router.get("/me", response_model=MeResponse, summary="Current user, school and permitted workspace")
def me(ctx: AuthContext = Depends(get_auth)) -> dict[str, Any]:
    return {
        "user": {
            "login_id": ctx.user.login_id,
            "display_name": ctx.user.display_name,
            "account_type": ctx.user.account_type,
            "must_change_password": ctx.user.must_change_password,
        },
        "school": {"name": ctx.school.name, "slug": ctx.school.slug},
        "workspace": workspace.build(ctx),
        "session": {"expires_at": ctx.session.expires_at, "idle_minutes": get_settings().session_idle_minutes},
        "demo_mode": get_settings().demo_auth_mode,
    }


@router.post("/change-password", response_model=PasswordChangedResponse, summary="Change password; signs out other sessions")
def change_password(body: ChangePasswordRequest, ctx: AuthContext = Depends(get_auth)) -> dict[str, Any]:
    revoked = auth_service.change_password(ctx.db, ctx.user, ctx.session, body.current_password, body.new_password, ctx.ip)
    return {"other_sessions_signed_out": revoked}


@router.post("/sessions/revoke-others", response_model=SessionsRevokedResponse, summary="Sign out all other sessions")
def revoke_others(ctx: AuthContext = Depends(get_auth)) -> dict[str, Any]:
    signed_out = auth_service.revoke_other_sessions(ctx.db, ctx.user, ctx.session)
    ctx.db.commit()
    return {"signed_out": signed_out}
