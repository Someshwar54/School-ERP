"""Finance request schemas. Money is always Decimal, never float."""

from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class PaymentCreate(BaseModel):
    invoice_id: UUID
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    method: str = Field(pattern="^(cash|upi|card|bank_transfer|cheque)$")
    reference: str | None = Field(default=None, max_length=64)
    paid_on: date
