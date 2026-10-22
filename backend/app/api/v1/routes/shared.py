"""Endpoints available to every signed-in account; results are filtered by audience on the server."""

from typing import Any

from fastapi import APIRouter, Depends

from app.api.deps import get_auth, page_params
from app.api.responses import AUTHENTICATED_ERRORS
from app.schemas.common import PageParams
from app.services import announcements
from app.services.auth_context import AuthContext

router = APIRouter(tags=["shared"], responses=AUTHENTICATED_ERRORS)


@router.get("/announcements", summary="Announcements for the viewer's audience (paginated)")
def list_announcements(params: PageParams = Depends(page_params), ctx: AuthContext = Depends(get_auth)) -> Any:
    return announcements.list_announcements(ctx, params)


@router.get("/events", summary="Upcoming and recent events for the viewer's audience")
def list_events(ctx: AuthContext = Depends(get_auth)) -> list[dict[str, Any]]:
    return announcements.list_events(ctx)
