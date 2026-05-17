from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator


class InvestmentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    investor_id: UUID
    amount_usd: Decimal = Field(gt=0, max_digits=20, decimal_places=2)
    investment_date: date

    @field_validator("amount_usd", mode="before")
    @classmethod
    def _reject_string_money(cls, v):
        if isinstance(v, str):
            raise ValueError("amount_usd must be a JSON number, not a string")
        return v


class InvestmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    investor_id: UUID
    fund_id: UUID
    amount_usd: Decimal
    investment_date: date

    @field_serializer("amount_usd")
    def _serialize_amount(self, v: Decimal) -> float:
        return float(v)
