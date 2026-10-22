"""Admission enquiries submitted from the public website."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AdmissionEnquiry, School
from app.schemas.common import PageParams
from app.schemas.public import EnquiryCreate
from app.services.auth_context import AuthContext
from app.services.lookups import paginate


def list_enquiries(ctx: AuthContext, params: PageParams) -> Any:
    stmt = select(AdmissionEnquiry).order_by(AdmissionEnquiry.created_at.desc())
    return paginate(
        ctx.db,
        stmt,
        params,
        lambda r: {
            "id": r[0].id,
            "parent_name": r[0].parent_name,
            "email": r[0].email,
            "phone": r[0].phone,
            "grade_sought": r[0].grade_sought,
            "message": r[0].message,
            "status": r[0].status,
            "created_at": r[0].created_at,
        },
    )


def create_enquiry(db: Session, school: School, body: EnquiryCreate) -> dict[str, Any]:
    """Store an enquiry. Bots that fill the hidden honeypot field get the same reply but nothing is stored."""
    message = "Thank you. Your enquiry has been recorded and the admissions office will contact you."
    if body.website:
        return {"ok": True, "message": message}
    db.add(
        AdmissionEnquiry(
            school_id=school.id,
            parent_name=body.parent_name,
            email=str(body.email),
            phone=body.phone,
            grade_sought=body.grade_sought,
            message=body.message,
        )
    )
    db.commit()
    return {"ok": True, "message": message, "notifications": "Email/SMS confirmation is not connected in this prototype."}
