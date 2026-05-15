from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

InvestorType = Literal["Individual", "Institution", "Family Office"]


class InvestorCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    investor_type: InvestorType
    email: EmailStr


class InvestorRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    investor_type: InvestorType
    email: EmailStr
    created_at: datetime
