"""Fees and finance. Balances are derived from the ledger; nothing here edits a balance directly."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.deps import page_params, require_permission
from app.api.responses import AUTHENTICATED_ERRORS
from app.schemas.common import PageParams
from app.schemas.finance import PaymentCreate
from app.services import finance
from app.services.auth_context import AuthContext
from app.services.school import school_today

router = APIRouter(prefix="/finance", tags=["finance"], responses=AUTHENTICATED_ERRORS)


@router.get("/summary")
def summary(ctx: AuthContext = Depends(require_permission("finance.view", "finance.view_summary"))) -> dict[str, Any]:
    return finance.get_school_summary(ctx.db, school_today(ctx.school))


@router.get("/invoices")
def list_invoices(
    q: str | None = Query(None, max_length=60),
    status: str | None = Query(None, pattern="^(paid|partially_paid|unpaid|overdue|cancelled)$"),
    params: PageParams = Depends(page_params),
    ctx: AuthContext = Depends(require_permission("finance.view")),
) -> dict[str, Any]:
    return finance.list_invoices(ctx.db, school_today(ctx.school), q, status, params.page, params.page_size)


@router.get("/students/{student_id}/ledger")
def student_ledger(student_id: UUID, ctx: AuthContext = Depends(require_permission("finance.view"))) -> dict[str, Any]:
    return finance.get_student_ledger(ctx.db, student_id, school_today(ctx.school))


@router.post("/payments", status_code=201)
def record_payment(
    body: PaymentCreate, ctx: AuthContext = Depends(require_permission("finance.record_payment"))
) -> dict[str, Any]:
    return finance.record_payment(ctx, body)
