"""Staff self-service: own profile, attendance, leave, duties and documents."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.deps import MonthParam, staff_ctx
from app.api.responses import AUTHENTICATED_ERRORS
from app.schemas.staff import LeaveCreate
from app.services import documents, staff_self_service
from app.services.auth_context import AuthContext

router = APIRouter(prefix="/staff", tags=["staff"], responses=AUTHENTICATED_ERRORS)
Staff = Depends(staff_ctx)


@router.get("/dashboard")
def dashboard(ctx: AuthContext = Staff) -> dict[str, Any]:
    return staff_self_service.get_dashboard(ctx)


@router.get("/profile")
def profile(ctx: AuthContext = Staff) -> dict[str, Any]:
    return staff_self_service.get_profile(ctx)


@router.get("/attendance")
def my_attendance(month: str | None = MonthParam, ctx: AuthContext = Staff) -> dict[str, Any]:
    return staff_self_service.get_my_attendance(ctx, month)


@router.get("/leave")
def list_my_leave(ctx: AuthContext = Staff) -> list[dict[str, Any]]:
    return staff_self_service.list_my_leave(ctx)


@router.post("/leave", status_code=201)
def request_leave(body: LeaveCreate, ctx: AuthContext = Staff) -> dict[str, Any]:
    return staff_self_service.request_leave(ctx, body)


@router.post("/leave/{leave_id}/cancel")
def cancel_leave(leave_id: UUID, ctx: AuthContext = Staff) -> dict[str, Any]:
    return staff_self_service.cancel_leave(ctx, leave_id)


@router.get("/duties")
def list_duties(ctx: AuthContext = Staff) -> list[dict[str, Any]]:
    return staff_self_service.list_duties(ctx)


@router.post("/duties/{duty_id}/done")
def complete_duty(duty_id: UUID, ctx: AuthContext = Staff) -> dict[str, Any]:
    return staff_self_service.complete_duty(ctx, duty_id)


@router.get("/documents")
def list_documents(ctx: AuthContext = Staff) -> list[dict[str, Any]]:
    return documents.list_documents(ctx, "staff", ctx.staff_id)
