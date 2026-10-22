"""Messaging, complaint and feedback request schemas."""

from uuid import UUID

from pydantic import BaseModel, Field


class MessageThreadCreate(BaseModel):
    staff_id: UUID
    subject: str = Field(min_length=3, max_length=160)
    body: str = Field(min_length=1, max_length=4000)


class MessageReply(BaseModel):
    body: str = Field(min_length=1, max_length=4000)


class ComplaintCreate(BaseModel):
    category: str = Field(pattern="^(academic|facilities|transport|conduct|fees|other)$")
    subject: str = Field(min_length=5, max_length=160)
    description: str = Field(min_length=10, max_length=4000)
    is_confidential: bool = False


class ComplaintStatusUpdate(BaseModel):
    note: str = Field(min_length=3, max_length=2000)
    status: str | None = Field(default=None, pattern="^(open|in_review|resolved|closed)$")
    assign_staff_id: UUID | None = None


class FeedbackCreate(BaseModel):
    category: str = Field(pattern="^(teaching|facilities|transport|communication|general)$")
    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=2000)
    is_anonymous: bool = False
