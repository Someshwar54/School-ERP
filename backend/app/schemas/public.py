"""Public (unauthenticated) request schemas."""

from pydantic import BaseModel, EmailStr, Field


class EnquiryCreate(BaseModel):
    parent_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    phone: str = Field(pattern=r"^[6-9]\d{9}$")
    grade_sought: str = Field(min_length=1, max_length=32)
    message: str | None = Field(default=None, max_length=2000)
    website: str | None = Field(default=None, max_length=200, description="Honeypot; must be empty")


class EnquiryResponse(BaseModel):
    ok: bool
    message: str
    notifications: str | None = None


class HealthResponse(BaseModel):
    status: str
    schema_version: str | None = None
