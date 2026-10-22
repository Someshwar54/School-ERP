"""FastAPI application factory. API docs: /api/docs (disabled in production)."""

from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response

from app.api.v1 import api_router
from app.core.config import get_settings
from app.core.errors import install_error_handlers
from app.core.logging import RequestContextMiddleware, configure_logging


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)
    docs = settings.app_env != "production"
    app = FastAPI(
        title="School ERP API",
        version="0.2.0",
        description="Prototype API for the school website and ERP. Errors use a single envelope; see ErrorEnvelope.",
        docs_url="/api/docs" if docs else None,
        redoc_url=None,
        openapi_url="/api/openapi.json" if docs else None,
    )
    app.add_middleware(RequestContextMiddleware)
    install_error_handlers(app)
    app.include_router(api_router, prefix="/api/v1")

    @app.middleware("http")
    async def security_headers(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "same-origin")
        response.headers.setdefault("Cache-Control", "no-store")
        return response

    return app


app = create_app()
