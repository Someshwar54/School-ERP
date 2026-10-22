"""Complaints: routing, confidentiality and role-based visibility."""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, select

from app.core.errors import bad_request, forbidden, not_found
from app.models import (
    ClassTeacherAssignment,
    Complaint,
    ComplaintUpdate,
    StaffProfile,
    User,
)
from app.schemas.communication import ComplaintCreate, ComplaintStatusUpdate
from app.services import audit
from app.services.auth_context import AuthContext
from app.services.lookups import enrollment_for, section_labels, staff_names, student_names
from app.services.school import current_year


# ---- complaints --------------------------------------------------------------------------------------------------
def _complaint_out(
    c: Complaint, labels: dict[UUID, str], staff: dict[UUID, str], include_reporter: bool, students: dict[UUID, str] | None = None
) -> dict[str, Any]:
    return {
        "id": c.id,
        "reference_no": c.reference_no,
        "category": c.category,
        "subject": c.subject,
        "description": c.description,
        "is_confidential": c.is_confidential,
        "status": c.status,
        "section": labels.get(c.section_id) if c.section_id else None,
        "assigned_to": staff.get(c.assigned_staff_id) if c.assigned_staff_id else None,
        "student": (students or {}).get(c.student_id) if include_reporter and c.student_id else None,
        "created_at": c.created_at,
        "resolved_at": c.resolved_at,
    }


def _updates(ctx: AuthContext, complaint_ids: list[UUID]) -> dict[UUID, list[dict[str, Any]]]:
    out: dict[UUID, list[dict[str, Any]]] = {}
    rows = ctx.db.execute(
        select(ComplaintUpdate, User.display_name)
        .join(User, User.id == ComplaintUpdate.author_user_id)
        .where(ComplaintUpdate.complaint_id.in_(complaint_ids))
        .order_by(ComplaintUpdate.created_at)
    ).tuples()
    for u, author in rows:
        out.setdefault(u.complaint_id, []).append(
            {"note": u.note, "new_status": u.new_status, "author": author, "created_at": u.created_at}
        )
    return out


def list_student_complaints(ctx: AuthContext) -> list[dict[str, Any]]:
    rows = list(
        ctx.db.scalars(select(Complaint).where(Complaint.raised_by_user_id == ctx.user_id).order_by(Complaint.created_at.desc()))
    )
    labels, staff, ups = section_labels(ctx.db), staff_names(ctx.db), _updates(ctx, [c.id for c in rows])
    return [{**_complaint_out(c, labels, staff, False), "updates": ups.get(c.id, [])} for c in rows]


def create_complaint(ctx: AuthContext, body: ComplaintCreate) -> dict[str, Any]:
    db = ctx.db
    enr = enrollment_for(db, ctx.student_id, current_year(db).id)  # type: ignore[arg-type]
    assigned = None
    # Non-confidential academic complaints go to the class teacher; everything else to management.
    if body.category == "academic" and not body.is_confidential and enr:
        assigned = db.scalar(select(ClassTeacherAssignment.staff_id).where(ClassTeacherAssignment.section_id == enr.section_id))
    n = (db.scalar(select(func.count()).select_from(Complaint)) or 0) + 1
    c = Complaint(
        school_id=ctx.school_id,
        reference_no=f"CMP-{datetime.now(UTC).year}-{n:04d}",
        raised_by_user_id=ctx.user_id,
        student_id=ctx.student_id,
        section_id=enr.section_id if enr else None,
        category=body.category,
        subject=body.subject,
        description=body.description,
        is_confidential=body.is_confidential,
        assigned_staff_id=assigned,
    )
    db.add(c)
    db.flush()
    audit.record(
        db,
        ctx.school_id,
        "complaint.created",
        actor_user_id=ctx.user_id,
        entity_type="complaint",
        entity_id=c.id,
        ip=ctx.ip,
        details={"category": c.category, "confidential": c.is_confidential},
    )
    db.commit()
    return {"id": c.id, "reference_no": c.reference_no, "routed_to": "Class teacher" if assigned else "School management"}


def list_teacher_complaints(ctx: AuthContext) -> list[dict[str, Any]]:
    rows = list(
        ctx.db.scalars(
            select(Complaint)
            .where(Complaint.assigned_staff_id == ctx.staff_id, Complaint.is_confidential.is_(False))
            .order_by(Complaint.created_at.desc())
        )
    )
    labels, staff, ups = section_labels(ctx.db), staff_names(ctx.db), _updates(ctx, [c.id for c in rows])
    students = student_names(ctx.db, {c.student_id for c in rows if c.student_id})
    return [{**_complaint_out(c, labels, staff, True, students), "updates": ups.get(c.id, [])} for c in rows]


def list_management_complaints(ctx: AuthContext, status: str | None) -> dict[str, Any]:
    db = ctx.db
    summary_rows = db.execute(
        select(Complaint.status, Complaint.category, Complaint.is_confidential, func.count()).group_by(
            Complaint.status, Complaint.category, Complaint.is_confidential
        )
    ).all()
    summary = {"by_status": {}, "by_category": {}, "confidential_open": 0}  # type: dict[str, Any]
    for st, cat, conf, n in summary_rows:
        summary["by_status"][st] = summary["by_status"].get(st, 0) + n
        summary["by_category"][cat] = summary["by_category"].get(cat, 0) + n
        if conf and st in ("open", "in_review"):
            summary["confidential_open"] += n
    items: list[dict[str, Any]] | None = None
    if ctx.has("complaints.view_all") or ctx.has("complaints.view_confidential"):
        stmt = select(Complaint).order_by(Complaint.created_at.desc()).limit(200)
        if not ctx.has("complaints.view_confidential"):
            stmt = stmt.where(Complaint.is_confidential.is_(False))
        elif not ctx.has("complaints.view_all"):
            stmt = stmt.where(Complaint.is_confidential.is_(True))
        if status:
            stmt = stmt.where(Complaint.status == status)
        rows = list(db.scalars(stmt))
        students = student_names(db, {c.student_id for c in rows if c.student_id})
        labels, staff, ups = section_labels(db), staff_names(db), _updates(ctx, [c.id for c in rows])
        items = [{**_complaint_out(c, labels, staff, True, students), "updates": ups.get(c.id, [])} for c in rows]
    return {
        "summary": summary,
        "items": items,
        "can_manage": ctx.has("complaints.manage"),
        "can_view_confidential": ctx.has("complaints.view_confidential"),
    }


def update_complaint(ctx: AuthContext, complaint_id: UUID, body: ComplaintStatusUpdate, as_teacher: bool) -> dict[str, Any]:
    db = ctx.db
    c = db.scalar(select(Complaint).where(Complaint.id == complaint_id).with_for_update())
    if c is None:
        raise not_found("Complaint")
    if as_teacher:
        if c.assigned_staff_id != ctx.staff_id or c.is_confidential:
            raise not_found("Complaint")
        if body.assign_staff_id:
            raise forbidden("Teachers cannot reassign complaints.")
    else:
        ctx.require("complaints.manage")
        if c.is_confidential and not ctx.has("complaints.view_confidential"):
            raise not_found("Complaint")
        if body.assign_staff_id:
            if c.is_confidential:
                raise bad_request("Confidential complaints cannot be assigned to individual staff.")
            if not db.get(StaffProfile, body.assign_staff_id):
                raise bad_request("Unknown staff member.")
            c.assigned_staff_id = body.assign_staff_id
    now = datetime.now(UTC)
    if body.status:
        c.status = body.status
        c.resolved_at = now if body.status in ("resolved", "closed") else None
    c.updated_at = now
    db.add(
        ComplaintUpdate(
            school_id=ctx.school_id, complaint_id=c.id, author_user_id=ctx.user_id, note=body.note, new_status=body.status
        )
    )
    audit.record(
        db,
        ctx.school_id,
        "complaint.updated",
        actor_user_id=ctx.user_id,
        entity_type="complaint",
        entity_id=c.id,
        ip=ctx.ip,
        details={"status": body.status, "reassigned": bool(body.assign_staff_id)},
    )
    db.commit()
    return {"ok": True, "status": c.status}
