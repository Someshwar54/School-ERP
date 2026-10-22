"""Attendance request schemas."""

from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field


class AttendanceEntry(BaseModel):
    student_id: UUID
    status: str = Field(pattern="^(present|absent|late|approved_leave|excused)$")
    remark: str | None = Field(default=None, max_length=255)


class AttendanceSubmission(BaseModel):
    section_id: UUID
    day: date
    period_no: int = Field(default=0, ge=0, le=12)
    records: list[AttendanceEntry] = Field(min_length=1, max_length=200)
    reason: str | None = Field(default=None, max_length=255)
