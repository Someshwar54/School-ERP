"""HR: staff directory, leave approvals (no self-approval) and audited payroll access."""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select

from app.core.errors import AppError, forbidden, not_found
from app.models import (
    ApprovalRecord,
    LeaveRequest,
    StaffCompensation,
    StaffProfile,
)
from app.schemas.common import PageParams
from app.schemas.staff import LeaveDecision
from app.services import audit
from app.services.auth_context import AuthContext
from app.services.lookups import money, paginate, staff_names
from app.services.staff_self_service import serialize_leave


# ---- HR ----------------------------------------------------------------------------------------------------------
def list_staff_directory(ctx: AuthContext, q: str | None, params: PageParams) -> Any:
    stmt = select(StaffProfile).where(StaffProfile.is_active.is_(True)).order_by(StaffProfile.staff_code)
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(
            StaffProfile.first_name.ilike(like)
            | StaffProfile.last_name.ilike(like)
            | StaffProfile.staff_code.ilike(like)
            | StaffProfile.department.ilike(like)
        )
    return paginate(
        ctx.db,
        stmt,
        params,
        lambda r: {
            "id": r[0].id,
            "staff_code": r[0].staff_code,
            "name": f"{r[0].first_name} {r[0].last_name}",
            "designation": r[0].designation,
            "department": r[0].department,
            "staff_type": r[0].staff_type,
            "joining_date": r[0].joining_date,
            "email": r[0].email,
        },
    )


def list_leave_requests(ctx: AuthContext, status: str | None) -> list[dict[str, Any]]:
    stmt = select(LeaveRequest).order_by(LeaveRequest.created_at.desc()).limit(200)
    if status:
        stmt = stmt.where(LeaveRequest.status == status)
    rows = list(ctx.db.scalars(stmt))
    names = staff_names(ctx.db, {r.staff_id for r in rows})
    return [{**serialize_leave(r, names), "is_own": r.staff_id == ctx.staff_id} for r in rows]


def decide_leave(ctx: AuthContext, leave_id: UUID, body: LeaveDecision) -> dict[str, Any]:
    db = ctx.db
    r = db.scalar(select(LeaveRequest).where(LeaveRequest.id == leave_id).with_for_update())
    if r is None:
        raise not_found("Leave request")
    if r.staff_id == ctx.staff_id:
        raise forbidden("You cannot decide your own leave request.")
    if r.status != "pending":
        raise AppError(409, "not_pending", "This request has already been decided.")
    r.status, r.decided_by_user_id, r.decided_at, r.decision_comment = body.decision, ctx.user_id, datetime.now(UTC), body.comment
    db.add(
        ApprovalRecord(
            school_id=ctx.school_id,
            entity_type="leave_request",
            entity_id=r.id,
            decision=body.decision,
            comment=body.comment,
            decided_by_user_id=ctx.user_id,
        )
    )
    audit.record(
        db,
        ctx.school_id,
        f"leave.{body.decision}",
        actor_user_id=ctx.user_id,
        entity_type="leave_request",
        entity_id=r.id,
        ip=ctx.ip,
    )
    db.commit()
    return {"ok": True, "status": r.status}


def list_payroll(ctx: AuthContext) -> list[dict[str, Any]]:
    db = ctx.db
    rows = (
        db.execute(
            select(StaffProfile, StaffCompensation)
            .join(StaffCompensation, StaffCompensation.staff_id == StaffProfile.id)
            .order_by(StaffProfile.staff_code, StaffCompensation.effective_from.desc())
        )
        .tuples()
        .all()
    )
    latest: dict[UUID, tuple[StaffProfile, StaffCompensation]] = {}
    for p, c in rows:
        latest.setdefault(p.id, (p, c))
    # Viewing salaries is sensitive and therefore audited.
    audit.record(db, ctx.school_id, "payroll.viewed", actor_user_id=ctx.user_id, ip=ctx.ip)
    db.commit()
    return [
        {
            "staff_code": p.staff_code,
            "name": f"{p.first_name} {p.last_name}",
            "designation": p.designation,
            "pay_grade": c.pay_grade,
            "monthly_gross": money(c.monthly_gross),
            "effective_from": c.effective_from,
            "bank_account": f"XXXX{c.bank_account_last4}" if c.bank_account_last4 else None,
        }
        for p, c in latest.values()
    ]
