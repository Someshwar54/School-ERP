"""General feedback. Anonymous submissions store no submitter; summaries suppress small groups."""

from typing import Any

from sqlalchemy import func, select

from app.models import (
    Feedback,
)
from app.schemas.communication import FeedbackCreate
from app.services.auth_context import AuthContext


# ---- feedback ----------------------------------------------------------------------------------------------------
def create_feedback(ctx: AuthContext, body: FeedbackCreate) -> dict[str, Any]:
    fb = Feedback(
        school_id=ctx.school_id,
        submitted_by_user_id=None if body.is_anonymous else ctx.user_id,
        account_type=ctx.user.account_type,
        category=body.category,
        rating=body.rating,
        comment=body.comment,
        is_anonymous=body.is_anonymous,
    )
    ctx.db.add(fb)
    ctx.db.commit()
    return {"ok": True, "anonymous": body.is_anonymous}


def list_my_feedback(ctx: AuthContext) -> list[dict[str, Any]]:
    rows = ctx.db.scalars(
        select(Feedback).where(Feedback.submitted_by_user_id == ctx.user_id).order_by(Feedback.created_at.desc())
    )
    return [{"category": f.category, "rating": f.rating, "comment": f.comment, "created_at": f.created_at} for f in rows]


MIN_GROUP = 5


def feedback_summary(ctx: AuthContext) -> dict[str, Any]:
    rows = ctx.db.execute(select(Feedback.category, func.count(), func.avg(Feedback.rating)).group_by(Feedback.category)).all()
    cats = [
        {
            "category": c,
            "responses": n,
            "average_rating": round(float(a), 2) if n >= MIN_GROUP else None,
            "suppressed": n < MIN_GROUP,
        }
        for c, n, a in rows
    ]
    comments = ctx.db.scalars(
        select(Feedback.comment).where(Feedback.comment.is_not(None)).order_by(Feedback.created_at.desc()).limit(20)
    )
    return {
        "categories": sorted(cats, key=lambda c: c["category"]),
        "minimum_group_size": MIN_GROUP,
        "recent_comments": list(comments),
        "note": "Comments are shown without names. Groups under 5 responses are suppressed.",
    }
