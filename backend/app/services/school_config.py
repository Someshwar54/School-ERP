"""School operational configuration: validated, versioned (optimistic locking) and audited."""

from typing import Any

from app.core.errors import AppError
from app.models import SchoolSettings
from app.schemas.management import SchoolConfigUpdate
from app.schemas.settings import SchoolSettingsModel
from app.services import audit
from app.services.auth_context import AuthContext
from app.services.school import school_settings


def get_config(ctx: AuthContext) -> dict[str, Any]:
    row = ctx.db.get(SchoolSettings, ctx.school_id)
    return {
        "settings": school_settings(ctx.db, ctx.school_id).model_dump(),
        "version": row.version if row else 0,
        "can_manage": ctx.has("config.manage"),
    }


def update_config(ctx: AuthContext, body: SchoolConfigUpdate) -> dict[str, Any]:
    db = ctx.db
    row = db.get(SchoolSettings, ctx.school_id, with_for_update=True)
    if row is None:
        row = SchoolSettings(school_id=ctx.school_id, settings={}, version=0)
        db.add(row)
    if row.version != body.version:
        raise AppError(409, "version_conflict", "Settings were changed by someone else. Reload and try again.")
    before = SchoolSettingsModel.model_validate(row.settings or {}).model_dump()
    after = body.settings.model_dump()
    row.settings, row.version, row.updated_by_user_id = after, row.version + 1, ctx.user_id
    audit.record(
        db,
        ctx.school_id,
        "config.updated",
        actor_user_id=ctx.user_id,
        entity_type="school_settings",
        ip=ctx.ip,
        details={"changed_sections": sorted(k for k in after if after[k] != before.get(k))},
    )
    db.commit()
    return {"ok": True, "version": row.version}
