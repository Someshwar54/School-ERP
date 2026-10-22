"""Authentication request and response schemas."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

Portal = Literal["student", "staff", "director"]
WorkspaceKind = Literal["student", "staff", "management"]


class LoginRequest(BaseModel):
    portal: Portal
    login_id: str = Field(min_length=3, max_length=32, pattern=r"^[A-Za-z0-9\-]+$")
    password: str = Field(min_length=1, max_length=128)


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=1, max_length=128)


class LoginResponse(BaseModel):
    ok: bool = True
    home: str
    must_change_password: bool


class UserSummary(BaseModel):
    login_id: str
    display_name: str
    account_type: str
    must_change_password: bool


class SchoolSummary(BaseModel):
    name: str
    slug: str


class ClassTeacherSection(BaseModel):
    section_id: UUID
    section: str


class Workspace(BaseModel):
    """What the signed-in user may use. Computed on the server; the UI only renders it."""

    kind: WorkspaceKind
    home: str
    modules: list[str]
    roles: list[str]
    permissions: list[str]
    is_teacher: bool | None = None
    teaching_assignments: int | None = None
    class_teacher_of: list[ClassTeacherSection] | None = None


class SessionInfo(BaseModel):
    expires_at: datetime
    idle_minutes: int


class MeResponse(BaseModel):
    user: UserSummary
    school: SchoolSummary
    workspace: Workspace
    session: SessionInfo
    demo_mode: bool


class PasswordChangedResponse(BaseModel):
    ok: bool = True
    other_sessions_signed_out: int


class SessionsRevokedResponse(BaseModel):
    ok: bool = True
    signed_out: int
