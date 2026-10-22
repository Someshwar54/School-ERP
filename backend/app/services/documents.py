"""Document metadata listings. File storage is not connected in the prototype."""

from typing import Any
from uuid import UUID

from sqlalchemy import or_, select

from app.models import (
    Document,
)
from app.services.auth_context import AuthContext


def list_documents(ctx: AuthContext, owner_type: str, owner_id: UUID | None) -> list[dict[str, Any]]:
    rows = ctx.db.scalars(
        select(Document)
        .where(or_(Document.owner_type == "school", (Document.owner_type == owner_type) & (Document.owner_id == owner_id)))
        .order_by(Document.created_at.desc())
    )
    return [
        {
            "id": d.id,
            "title": d.title,
            "category": d.category,
            "scope": "School" if d.owner_type == "school" else "Personal",
            "available": d.storage_key is not None,
            "created_at": d.created_at,
        }
        for d in rows
    ]
