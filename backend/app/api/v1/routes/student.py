"""Student workspace. Every endpoint is keyed on the signed-in student; none accepts a student id."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.deps import MonthParam, student_ctx
from app.api.responses import AUTHENTICATED_ERRORS
from app.schemas.academics import TopicFeedbackCreate
from app.schemas.communication import ComplaintCreate, FeedbackCreate, MessageReply, MessageThreadCreate
from app.services import complaints, feedback, finance, messaging, student_portal
from app.services.auth_context import AuthContext
from app.services.school import school_today

router = APIRouter(prefix="/student", tags=["student"], responses=AUTHENTICATED_ERRORS)
Student = Depends(student_ctx)


@router.get("/dashboard")
def dashboard(ctx: AuthContext = Student) -> dict[str, Any]:
    return student_portal.get_dashboard(ctx)


@router.get("/profile")
def profile(ctx: AuthContext = Student) -> dict[str, Any]:
    return student_portal.get_profile(ctx)


@router.get("/attendance")
def attendance(month: str | None = MonthParam, ctx: AuthContext = Student) -> dict[str, Any]:
    return student_portal.get_attendance_month(ctx, month)


@router.get("/results")
def results(ctx: AuthContext = Student) -> dict[str, Any]:
    return student_portal.get_results(ctx)


@router.get("/performance")
def performance(ctx: AuthContext = Student) -> dict[str, Any]:
    return student_portal.get_performance(ctx)


@router.get("/timetable")
def timetable(ctx: AuthContext = Student) -> dict[str, Any]:
    return student_portal.get_timetable(ctx)


@router.get("/fees")
def fees(ctx: AuthContext = Student) -> dict[str, Any]:
    return finance.get_student_ledger(ctx.db, ctx.student_id, school_today(ctx.school))  # type: ignore[arg-type]


@router.get("/documents")
def documents(ctx: AuthContext = Student) -> dict[str, Any]:
    return student_portal.get_documents(ctx)


@router.get("/report-card/{term_id}")
def report_card(term_id: UUID, ctx: AuthContext = Student) -> dict[str, Any]:
    return student_portal.get_report_card(ctx, term_id)


@router.get("/teachers")
def teachers(ctx: AuthContext = Student) -> list[dict[str, Any]]:
    return messaging.list_student_teachers(ctx)


@router.get("/messages")
def list_threads(ctx: AuthContext = Student) -> list[dict[str, Any]]:
    return messaging.list_threads(ctx)


@router.post("/messages", status_code=201)
def create_thread(body: MessageThreadCreate, ctx: AuthContext = Student) -> dict[str, Any]:
    return messaging.create_thread(ctx, body)


@router.get("/messages/{thread_id}")
def get_thread(thread_id: UUID, ctx: AuthContext = Student) -> dict[str, Any]:
    return messaging.get_thread(ctx, thread_id)


@router.post("/messages/{thread_id}/reply")
def reply(thread_id: UUID, body: MessageReply, ctx: AuthContext = Student) -> dict[str, Any]:
    return messaging.reply_to_thread(ctx, thread_id, body)


@router.get("/complaints")
def list_complaints(ctx: AuthContext = Student) -> list[dict[str, Any]]:
    return complaints.list_student_complaints(ctx)


@router.post("/complaints", status_code=201)
def create_complaint(body: ComplaintCreate, ctx: AuthContext = Student) -> dict[str, Any]:
    return complaints.create_complaint(ctx, body)


@router.get("/topics")
def list_topics(ctx: AuthContext = Student) -> list[dict[str, Any]]:
    return student_portal.list_topics(ctx)


@router.post("/topics/{topic_id}/feedback")
def give_topic_feedback(topic_id: UUID, body: TopicFeedbackCreate, ctx: AuthContext = Student) -> dict[str, Any]:
    return student_portal.give_topic_feedback(ctx, topic_id, body)


@router.get("/feedback")
def list_my_feedback(ctx: AuthContext = Student) -> list[dict[str, Any]]:
    return feedback.list_my_feedback(ctx)


@router.post("/feedback", status_code=201)
def create_feedback(body: FeedbackCreate, ctx: AuthContext = Student) -> dict[str, Any]:
    return feedback.create_feedback(ctx, body)
