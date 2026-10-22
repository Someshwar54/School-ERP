"""Management request schemas: evaluations and school configuration."""

from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.settings import SchoolSettingsModel


class EvaluationCreate(BaseModel):
    staff_id: UUID
    period_label: str = Field(min_length=3, max_length=32)
    scores: dict[str, int] = Field(default_factory=dict)
    evidence_notes: str = Field(min_length=10, max_length=4000)


class EvaluationFinalize(BaseModel):
    reviewer_comment: str = Field(min_length=10, max_length=4000)


class EvaluationScoresUpdate(BaseModel):
    scores: dict[str, int]


class SchoolConfigUpdate(BaseModel):
    version: int
    settings: SchoolSettingsModel
