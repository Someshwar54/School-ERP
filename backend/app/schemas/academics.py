"""Assessment, marks and lesson-progression request schemas."""

from datetime import date
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class AssessmentCreate(BaseModel):
    section_id: UUID
    subject_id: UUID
    name: str = Field(min_length=3, max_length=80)
    kind: str = Field(pattern="^(unit_test|half_yearly|annual|assignment|practical)$")
    max_marks: Decimal = Field(gt=0, le=200, decimal_places=2)
    held_on: date


class MarkEntry(BaseModel):
    student_id: UUID
    marks_obtained: Decimal | None = Field(default=None, ge=0, decimal_places=2)
    is_absent: bool = False
    remarks: str | None = Field(default=None, max_length=255)

    @model_validator(mode="after")
    def _absent_xor_marks(self) -> "MarkEntry":
        if self.is_absent and self.marks_obtained is not None:
            raise ValueError("An absent student cannot have marks.")
        return self


class MarksSubmission(BaseModel):
    marks: list[MarkEntry] = Field(min_length=1, max_length=200)
    reason: str | None = Field(default=None, max_length=255)


class TopicCreate(BaseModel):
    section_id: UUID
    subject_id: UUID
    title: str = Field(min_length=3, max_length=160)
    planned_periods: int = Field(default=4, ge=1, le=60)


class TopicAction(BaseModel):
    action: Literal["start", "continue", "keep_pending", "complete", "reopen"]
    confirm: bool = False
    start_next: bool = False
    notes: str | None = Field(default=None, max_length=500)
    timetable_entry_id: UUID | None = None


class TopicFeedbackCreate(BaseModel):
    understanding: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=1000)
    share_name: bool = True
