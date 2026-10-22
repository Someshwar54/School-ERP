"""Teacher workspace. Access to each class/subject is checked against assignments in the services."""

from datetime import date
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.deps import teacher_ctx
from app.api.responses import AUTHENTICATED_ERRORS
from app.schemas.academics import AssessmentCreate, MarksSubmission, TopicAction, TopicCreate
from app.schemas.attendance import AttendanceSubmission
from app.schemas.communication import ComplaintStatusUpdate, MessageReply
from app.services import academics, attendance, complaints, lessons, messaging, student_portal, teacher_portal
from app.services.auth_context import AuthContext
from app.services.lookups import roster
from app.services.teaching import assert_section_access, assignments

router = APIRouter(prefix="/teacher", tags=["teacher"], responses=AUTHENTICATED_ERRORS)
Teacher = Depends(teacher_ctx)


@router.get("/dashboard")
def dashboard(ctx: AuthContext = Teacher) -> dict[str, Any]:
    return teacher_portal.get_dashboard(ctx)


@router.get("/timetable")
def timetable(ctx: AuthContext = Teacher) -> dict[str, Any]:
    return student_portal.build_timetable(ctx, staff_id=ctx.staff_id)


@router.get("/assignments")
def list_assignments(ctx: AuthContext = Teacher) -> list[dict[str, Any]]:
    return assignments(ctx.db, ctx.staff_id)  # type: ignore[arg-type]


@router.get("/sections/{section_id}/students")
def section_students(section_id: UUID, ctx: AuthContext = Teacher) -> list[dict[str, Any]]:
    assert_section_access(ctx, section_id)
    return roster(ctx.db, section_id)


@router.get("/attendance")
def get_register(
    section_id: UUID, day: date, period_no: int = Query(0, ge=0, le=12), ctx: AuthContext = Teacher
) -> dict[str, Any]:
    return attendance.get_register(ctx, section_id, day, period_no)


@router.put("/attendance")
def save_register(body: AttendanceSubmission, ctx: AuthContext = Teacher) -> dict[str, Any]:
    return attendance.save_register(ctx, body)


@router.get("/assessments")
def list_assessments(section_id: UUID, subject_id: UUID, ctx: AuthContext = Teacher) -> list[dict[str, Any]]:
    return academics.list_teacher_assessments(ctx, section_id, subject_id)


@router.post("/assessments", status_code=201)
def create_assessment(body: AssessmentCreate, ctx: AuthContext = Teacher) -> dict[str, Any]:
    return academics.create_assessment(ctx, body)


@router.get("/assessments/{assessment_id}/marks")
def get_marks(assessment_id: UUID, ctx: AuthContext = Teacher) -> dict[str, Any]:
    return academics.get_marks_sheet(ctx, assessment_id)


@router.put("/assessments/{assessment_id}/marks")
def save_marks(assessment_id: UUID, body: MarksSubmission, ctx: AuthContext = Teacher) -> dict[str, Any]:
    return academics.save_marks(ctx, assessment_id, body)


@router.get("/topics")
def list_topics(section_id: UUID, subject_id: UUID, ctx: AuthContext = Teacher) -> dict[str, Any]:
    return lessons.list_topics(ctx, section_id, subject_id)


@router.post("/topics", status_code=201)
def add_topic(body: TopicCreate, ctx: AuthContext = Teacher) -> dict[str, Any]:
    return lessons.add_topic(ctx, body)


@router.post("/topics/{topic_id}/action")
def apply_topic_action(topic_id: UUID, body: TopicAction, ctx: AuthContext = Teacher) -> dict[str, Any]:
    return lessons.apply_action(ctx, topic_id, body)


@router.get("/lesson-prompts")
def list_lesson_prompts(ctx: AuthContext = Teacher) -> list[dict[str, Any]]:
    return lessons.list_lesson_prompts(ctx)


@router.get("/topic-feedback")
def topic_feedback(section_id: UUID, subject_id: UUID, ctx: AuthContext = Teacher) -> list[dict[str, Any]]:
    return lessons.get_topic_feedback_summary(ctx, section_id, subject_id)


@router.get("/messages")
def list_threads(ctx: AuthContext = Teacher) -> list[dict[str, Any]]:
    return messaging.list_threads(ctx)


@router.get("/messages/{thread_id}")
def get_thread(thread_id: UUID, ctx: AuthContext = Teacher) -> dict[str, Any]:
    return messaging.get_thread(ctx, thread_id)


@router.post("/messages/{thread_id}/reply")
def reply(thread_id: UUID, body: MessageReply, ctx: AuthContext = Teacher) -> dict[str, Any]:
    return messaging.reply_to_thread(ctx, thread_id, body)


@router.get("/complaints")
def list_complaints(ctx: AuthContext = Teacher) -> list[dict[str, Any]]:
    return complaints.list_teacher_complaints(ctx)


@router.post("/complaints/{complaint_id}/update")
def update_complaint(complaint_id: UUID, body: ComplaintStatusUpdate, ctx: AuthContext = Teacher) -> dict[str, Any]:
    return complaints.update_complaint(ctx, complaint_id, body, as_teacher=True)


@router.get("/class/{section_id}")
def class_overview(section_id: UUID, ctx: AuthContext = Teacher) -> dict[str, Any]:
    return teacher_portal.get_class_overview(ctx, section_id)
