"""Audit trail: write events in the same transaction as the change, and query them for reviewers.

The audit_events table is append-only (a database trigger rejects UPDATE and DELETE).
"""

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AuditEvent, User
from app.schemas.common import Page, PageParams
from app.services.lookups import paginate


def record(
    db: Session,
    school_id: UUID,
    action: str,
    *,
    actor_user_id: UUID | None = None,
    entity_type: str | None = None,
    entity_id: UUID | str | None = None,
    details: dict[str, Any] | None = None,
    ip: str | None = None,
) -> None:
    db.add(
        AuditEvent(
            school_id=school_id,
            actor_user_id=actor_user_id,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id is not None else None,
            details=details or {},
            ip=ip,
        )
    )


def list_events(db: Session, action_prefix: str | None, params: PageParams) -> Page[dict[str, Any]]:
    stmt = (
        select(AuditEvent, User.display_name)
        .outerjoin(User, User.id == AuditEvent.actor_user_id)
        .order_by(AuditEvent.created_at.desc())
    )
    if action_prefix:
        stmt = stmt.where(AuditEvent.action.startswith(action_prefix))
    return paginate(
        db,
        stmt,
        params,
        lambda r: {
            "id": r[0].id,
            "action": r[0].action,
            "actor": r[1],
            "entity_type": r[0].entity_type,
            "entity_id": r[0].entity_id,
            "details": r[0].details,
            "ip": r[0].ip,
            "created_at": r[0].created_at,
        },
    )


def recent_activity(db: Session, limit: int = 8) -> list[dict[str, Any]]:
    rows = db.execute(
        select(AuditEvent, User.display_name)
        .outerjoin(User, User.id == AuditEvent.actor_user_id)
        .order_by(AuditEvent.created_at.desc())
        .limit(limit)
    ).tuples()
    return [{"action": e.action, "actor": n, "created_at": e.created_at} for e, n in rows]
