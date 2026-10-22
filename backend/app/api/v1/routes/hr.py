"""HR: staff directory, leave approvals and payroll (each gated by its own permission)."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.deps import page_params, require_permission
from app.api.responses import AUTHENTICATED_ERRORS
from app.schemas.common import PageParams
from app.schemas.staff import LeaveDecision
from app.services import hr
from app.services.auth_context import AuthContext

router = APIRouter(prefix="/hr", tags=["hr"], responses=AUTHENTICATED_ERRORS)


@router.get("/staff")
def list_staff(
    q: str | None = Query(None, max_length=60),
    params: PageParams = Depends(page_params),
    ctx: AuthContext = Depends(require_permission("hr.view")),
) -> Any:
    return hr.list_staff_directory(ctx, q, params)


@router.get("/leave-requests")
def list_leave_requests(
    status: str | None = Query(None, pattern="^(pending|approved|rejected|cancelled)$"),
    ctx: AuthContext = Depends(require_permission("hr.view", "approvals.decide_leave")),
) -> list[dict[str, Any]]:
    return hr.list_leave_requests(ctx, status)


@router.post("/leave-requests/{leave_id}/decision")
def decide_leave(
    leave_id: UUID, body: LeaveDecision, ctx: AuthContext = Depends(require_permission("approvals.decide_leave"))
) -> dict[str, Any]:
    return hr.decide_leave(ctx, leave_id, body)


@router.get("/payroll")
def list_payroll(ctx: AuthContext = Depends(require_permission("payroll.view"))) -> list[dict[str, Any]]:
    return hr.list_payroll(ctx)
