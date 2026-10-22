"""API version 1. Mounted at /api/v1 by app.main.

To add a domain: create routes/<domain>.py with an APIRouter, then list it below.
A future breaking change gets a sibling package (app/api/v2) mounted at /api/v2.
"""

from fastapi import APIRouter

from app.api.v1.routes import auth, finance, hr, management, public, shared, staff, student, teacher

api_router = APIRouter()
for module in (public, auth, shared, student, teacher, staff, hr, finance, management):
    api_router.include_router(module.router)
