"""Management portal. Every endpoint checks its own permission: entering via the Director portal
grants nothing by itself."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.deps import management_permission, page_params
from app.api.responses import AUTHENTICATED_ERRORS
from app.schemas.common import PageParams
from app.schemas.communication import ComplaintStatusUpdate
from app.schemas.management import EvaluationCreate, EvaluationFinalize, EvaluationScoresUpdate, SchoolConfigUpdate
from app.services import academics, admissions, analytics, audit, complaints, evaluations, feedback, school_config
from app.services.auth_context import AuthContext

router = APIRouter(prefix="/management", tags=["management"], responses=AUTHENTICATED_ERRORS)


def allow(*permissions: str) -> Any:
    return Depends(management_permission(*permissions))


@router.get("/overview")
def overview(ctx: AuthContext = allow("mgmt.dashboard.view")) -> dict[str, Any]:
    return analytics.get_overview(ctx)


@router.get("/academics")
def academic_performance(
    status: str | None = Query(None, pattern="^(published|unpublished)$"),
    params: PageParams = Depends(page_params),
    ctx: AuthContext = allow("mgmt.academics.view"),
) -> dict[str, Any]:
    return analytics.get_academics(ctx, status, params)


@router.post("/assessments/{assessment_id}/publish")
def publish_assessment(assessment_id: UUID, ctx: AuthContext = allow("marks.publish")) -> dict[str, Any]:
    return academics.publish_assessment(ctx, assessment_id)


@router.get("/attendance")
def attendance(ctx: AuthContext = allow("mgmt.attendance.view")) -> dict[str, Any]:
    return analytics.get_attendance(ctx)


@router.get("/teachers")
def teacher_evidence(ctx: AuthContext = allow("evaluation.view")) -> dict[str, Any]:
    return evaluations.get_teacher_evidence(ctx)


@router.get("/evaluations")
def list_evaluations(ctx: AuthContext = allow("evaluation.view")) -> dict[str, Any]:
    return evaluations.list_evaluations(ctx)


@router.post("/evaluations", status_code=201)
def create_evaluation(body: EvaluationCreate, ctx: AuthContext = allow("evaluation.manage")) -> dict[str, Any]:
    return evaluations.create_evaluation(ctx, body)


@router.patch("/evaluations/{evaluation_id}")
def score_evaluation(
    evaluation_id: UUID, body: EvaluationScoresUpdate, ctx: AuthContext = allow("evaluation.manage")
) -> dict[str, Any]:
    return evaluations.update_evaluation_scores(ctx, evaluation_id, body.scores)


@router.post("/evaluations/{evaluation_id}/finalize")
def finalize_evaluation(
    evaluation_id: UUID, body: EvaluationFinalize, ctx: AuthContext = allow("evaluation.manage")
) -> dict[str, Any]:
    return evaluations.finalize_evaluation(ctx, evaluation_id, body)


@router.get("/complaints")
def list_complaints(
    status: str | None = Query(None, pattern="^(open|in_review|resolved|closed)$"),
    ctx: AuthContext = allow("complaints.view_summary", "complaints.view_all", "complaints.view_confidential"),
) -> dict[str, Any]:
    return complaints.list_management_complaints(ctx, status)


@router.post("/complaints/{complaint_id}/update")
def update_complaint(
    complaint_id: UUID, body: ComplaintStatusUpdate, ctx: AuthContext = allow("complaints.manage")
) -> dict[str, Any]:
    return complaints.update_complaint(ctx, complaint_id, body, as_teacher=False)


@router.get("/feedback")
def feedback_summary(ctx: AuthContext = allow("feedback.view_aggregate")) -> dict[str, Any]:
    return feedback.feedback_summary(ctx)


@router.get("/audit")
def audit_log(
    action: str | None = Query(None, max_length=64),
    params: PageParams = Depends(page_params),
    ctx: AuthContext = allow("audit.view"),
) -> Any:
    return audit.list_events(ctx.db, action, params)


@router.get("/enquiries")
def list_enquiries(params: PageParams = Depends(page_params), ctx: AuthContext = allow("admissions.view")) -> Any:
    return admissions.list_enquiries(ctx, params)


@router.get("/config")
def get_config(ctx: AuthContext = allow("config.view", "config.manage")) -> dict[str, Any]:
    return school_config.get_config(ctx)


@router.put("/config")
def update_config(body: SchoolConfigUpdate, ctx: AuthContext = allow("config.manage")) -> dict[str, Any]:
    return school_config.update_config(ctx, body)
