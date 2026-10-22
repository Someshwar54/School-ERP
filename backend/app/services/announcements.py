"""Announcements and events, filtered by the viewer's audience and class."""

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import or_, select

from app.models import (
    Announcement,
    SchoolEvent,
)
from app.schemas.common import PageParams
from app.services.auth_context import AuthContext
from app.services.lookups import enrollment_for, paginate
from app.services.school import current_year


# ---- announcements & events ------------------------------------------------------------------------------------
def _audiences(ctx: AuthContext) -> tuple[str, ...]:
    return {"student": ("all", "students"), "staff": ("all", "staff"), "management": ("all", "staff", "management")}.get(
        ctx.user.account_type, ("all",)
    )


def list_announcements(ctx: AuthContext, params: PageParams) -> Any:
    now = datetime.now(UTC)
    stmt = select(Announcement).where(
        Announcement.audience.in_(_audiences(ctx)),
        Announcement.published_at <= now,
        or_(Announcement.expires_at.is_(None), Announcement.expires_at > now),
    )
    if ctx.student_id:
        enr = enrollment_for(ctx.db, ctx.student_id, current_year(ctx.db).id)
        stmt = stmt.where(or_(Announcement.section_id.is_(None), Announcement.section_id == (enr.section_id if enr else None)))
    elif ctx.user.account_type == "management":
        stmt = stmt.where(Announcement.section_id.is_(None))
    stmt = stmt.order_by(Announcement.is_pinned.desc(), Announcement.published_at.desc())
    return paginate(
        ctx.db,
        stmt,
        params,
        lambda r: {
            "id": r[0].id,
            "title": r[0].title,
            "body": r[0].body,
            "audience": r[0].audience,
            "is_pinned": r[0].is_pinned,
            "published_at": r[0].published_at,
            "section_specific": r[0].section_id is not None,
        },
    )


def list_events(ctx: AuthContext, include_past_days: int = 30) -> list[dict[str, Any]]:
    since = datetime.now(UTC) - timedelta(days=include_past_days)
    rows = ctx.db.scalars(
        select(SchoolEvent)
        .where(SchoolEvent.audience.in_(_audiences(ctx)), SchoolEvent.ends_at >= since)
        .order_by(SchoolEvent.starts_at)
        .limit(50)
    )
    now = datetime.now(UTC)
    return [
        {
            "id": e.id,
            "title": e.title,
            "description": e.description,
            "starts_at": e.starts_at,
            "ends_at": e.ends_at,
            "location": e.location,
            "is_past": e.ends_at < now,
        }
        for e in rows
    ]
