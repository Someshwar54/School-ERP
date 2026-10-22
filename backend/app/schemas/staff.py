"""Staff self-service and HR request schemas."""

from datetime import date

from pydantic import BaseModel, Field, model_validator


class LeaveCreate(BaseModel):
    leave_type: str = Field(pattern="^(casual|sick|earned|unpaid)$")
    starts_on: date
    ends_on: date
    reason: str = Field(min_length=3, max_length=500)

    @model_validator(mode="after")
    def _order(self) -> "LeaveCreate":
        if self.ends_on < self.starts_on:
            raise ValueError("The end date cannot be before the start date.")
        if (self.ends_on - self.starts_on).days > 60:
            raise ValueError("Leave requests cannot exceed 60 days.")
        return self


class LeaveDecision(BaseModel):
    decision: str = Field(pattern="^(approved|rejected)$")
    comment: str | None = Field(default=None, max_length=500)
