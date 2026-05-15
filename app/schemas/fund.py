from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

FundStatus = Literal["Fundraising", "Investing", "Closed"]


class FundCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    vintage_year: int = Field(ge=1900, le=2100)
    target_size_usd: Decimal = Field(gt=0, max_digits=20, decimal_places=2)
    status: FundStatus


class FundUpdate(BaseModel):
    id: UUID
    name: str = Field(min_length=1, max_length=255)
    vintage_year: int = Field(ge=1900, le=2100)
    target_size_usd: Decimal = Field(gt=0, max_digits=20, decimal_places=2)
    status: FundStatus


class FundRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    vintage_year: int
    target_size_usd: Decimal
    status: FundStatus
    created_at: datetime
