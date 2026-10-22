"""OpenAPI documentation for the error envelope every endpoint can return.

All errors share one shape: {"error": {"code": str, "message": str, "details"?: [...]}}.
See app.core.errors for the handlers that produce it.
"""

from typing import Any

from pydantic import BaseModel


class ErrorDetail(BaseModel):
    field: str
    message: str


class ErrorBody(BaseModel):
    code: str
    message: str
    details: list[ErrorDetail] | None = None


class ErrorEnvelope(BaseModel):
    error: ErrorBody


def _err(description: str) -> dict[str, Any]:
    return {"model": ErrorEnvelope, "description": description}


PUBLIC_ERRORS: dict[int | str, dict[str, Any]] = {422: _err("Validation error"), 429: _err("Rate limited")}

AUTHENTICATED_ERRORS: dict[int | str, dict[str, Any]] = {
    401: _err("Not signed in or session expired"),
    403: _err("Forbidden: missing permission, wrong account type or CSRF failure"),
    404: _err("Not found (or not visible to this account)"),
    409: _err("Conflict with the current state"),
    422: _err("Validation error"),
}
