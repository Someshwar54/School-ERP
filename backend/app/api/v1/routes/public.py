"""Unauthenticated endpoints. Nothing here returns private student, staff or financial data."""

from typing import Any

from fastapi import APIRouter, Depends, Request
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import client_ip, get_tenant
from app.api.responses import PUBLIC_ERRORS
from app.core.db import get_db
from app.core.rate_limit import SlidingWindowLimiter
from app.models import School
from app.schemas.public import EnquiryCreate, EnquiryResponse, HealthResponse
from app.services import admissions

router = APIRouter(tags=["public"], responses=PUBLIC_ERRORS)
enquiry_limiter = SlidingWindowLimiter(max_hits=5, window_seconds=600)


@router.get("/health", response_model=HealthResponse, response_model_exclude_none=True, summary="Liveness check")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/ready", response_model=HealthResponse, summary="Readiness check (database + schema version)")
def ready(db: Session = Depends(get_db)) -> dict[str, Any]:
    db.execute(text("SELECT 1"))
    version = db.execute(text("SELECT version_num FROM alembic_version")).scalar()
    return {"status": "ready", "schema_version": str(version)}


@router.post("/public/enquiries", status_code=201, response_model=EnquiryResponse, summary="Submit an admission enquiry")
def create_enquiry(
    body: EnquiryCreate, request: Request, school: School = Depends(get_tenant), db: Session = Depends(get_db)
) -> dict[str, Any]:
    enquiry_limiter.hit(f"{school.id}:{client_ip(request)}")
    return admissions.create_enquiry(db, school, body)
