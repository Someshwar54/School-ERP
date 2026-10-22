"""Staff self-service: own profile, attendance, leave requests and duties."""

from collections import Counter
from typing import Any
from uuid import UUID

from sqlalchemy import select

from app.core.errors import AppError, bad_request, not_found
from app.models import (
    LeaveRequest,
    StaffAttendance,
    StaffDuty,
    StaffProfile,
)
from app.schemas.common import PageParams
from app.schemas.staff import LeaveCreate
from app.services import announcements, audit
from app.services.auth_context import AuthContext
from app.services.lookups import month_bounds
from app.services.school import school_today


def get_profile(ctx: AuthContext) -> dict[str, Any]:
    p = ctx.db.get(StaffProfile, ctx.staff_id)
    if p is None:
        raise not_found("Staff profile")
    return {
        "staff_code": p.staff_code,
        "name": f"{p.first_name} {p.last_name}",
        "designation": p.designation,
        "department": p.department,
        "staff_type": p.staff_type,
        "joining_date": p.joining_date,
        "qualification": p.qualification,
        "email": p.email,
    }


def get_my_attendance(ctx: AuthContext, month: str | None) -> dict[str, Any]:
    today = school_today(ctx.school)
    start, end = month_bounds(month, today)
    rows = list(
        ctx.db.scalars(
            select(StaffAttendance)
            .where(StaffAttendance.staff_id == ctx.staff_id, StaffAttendance.day >= start, StaffAttendance.day <= end)
            .order_by(StaffAttendance.day)
        )
    )
    return {
        "month": start.strftime("%Y-%m"),
        "summary": dict(Counter(r.status for r in rows)),
        "days": [{"day": r.day, "status": r.status, "check_in": r.check_in, "check_out": r.check_out} for r in rows],
        "note": "Staff attendance is recorded by the school office; biometric integration is not connected.",
    }


def serialize_leave(r: LeaveRequest, names: dict[UUID, str]) -> dict[str, Any]:
    return {
        "id": r.id,
        "staff_name": names.get(r.staff_id),
        "leave_type": r.leave_type,
        "starts_on": r.starts_on,
        "ends_on": r.ends_on,
        "days": (r.ends_on - r.starts_on).days + 1,
        "reason": r.reason,
        "status": r.status,
        "decided_at": r.decided_at,
        "decision_comment": r.decision_comment,
        "created_at": r.created_at,
    }


def list_my_leave(ctx: AuthContext) -> list[dict[str, Any]]:
    rows = ctx.db.scalars(
        select(LeaveRequest).where(LeaveRequest.staff_id == ctx.staff_id).order_by(LeaveRequest.starts_on.desc())
    )
    return [serialize_leave(r, {}) for r in rows]


def request_leave(ctx: AuthContext, body: LeaveCreate) -> dict[str, Any]:
    db = ctx.db
    if body.starts_on < school_today(ctx.school):
        raise bad_request("Leave cannot start in the past. Contact HR for retrospective leave.")
    overlap = db.scalar(
        select(LeaveRequest.id).where(
            LeaveRequest.staff_id == ctx.staff_id,
            LeaveRequest.status.in_(("pending", "approved")),
            LeaveRequest.starts_on <= body.ends_on,
            LeaveRequest.ends_on >= body.starts_on,
        )
    )
    if overlap:
        raise AppError(409, "overlap", "You already have a pending or approved leave request for these dates.")
    r = LeaveRequest(
        school_id=ctx.school_id,
        staff_id=ctx.staff_id,
        leave_type=body.leave_type,
        starts_on=body.starts_on,
        ends_on=body.ends_on,
        reason=body.reason,
    )
    db.add(r)
    db.flush()
    audit.record(
        db, ctx.school_id, "leave.requested", actor_user_id=ctx.user_id, entity_type="leave_request", entity_id=r.id, ip=ctx.ip
    )
    db.commit()
    return serialize_leave(r, {})


def cancel_leave(ctx: AuthContext, leave_id: UUID) -> dict[str, Any]:
    r = ctx.db.get(LeaveRequest, leave_id)
    if r is None or r.staff_id != ctx.staff_id:
        raise not_found("Leave request")
    if r.status != "pending":
        raise AppError(409, "not_pending", "Only pending requests can be cancelled.")
    r.status = "cancelled"
    audit.record(
        ctx.db,
        ctx.school_id,
        "leave.cancelled",
        actor_user_id=ctx.user_id,
        entity_type="leave_request",
        entity_id=r.id,
        ip=ctx.ip,
    )
    ctx.db.commit()
    return {"ok": True}


def list_duties(ctx: AuthContext) -> list[dict[str, Any]]:
    rows = ctx.db.scalars(select(StaffDuty).where(StaffDuty.staff_id == ctx.staff_id).order_by(StaffDuty.duty_date))
    return [{"id": d.id, "title": d.title, "details": d.details, "duty_date": d.duty_date, "status": d.status} for d in rows]


def complete_duty(ctx: AuthContext, duty_id: UUID) -> dict[str, Any]:
    d = ctx.db.get(StaffDuty, duty_id)
    if d is None or d.staff_id != ctx.staff_id:
        raise not_found("Duty")
    d.status = "done"
    ctx.db.commit()
    return {"ok": True}


def get_dashboard(ctx: AuthContext) -> dict[str, Any]:
    return {
        "profile": get_profile(ctx),
        "attendance_this_month": get_my_attendance(ctx, None)["summary"],
        "pending_leave": sum(1 for r in list_my_leave(ctx) if r["status"] == "pending"),
        "duties": [d for d in list_duties(ctx) if d["status"] == "assigned"][:5],
        "announcements": announcements.list_announcements(ctx, PageParams(page=1, page_size=3)).items,
    }
