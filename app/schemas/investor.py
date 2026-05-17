from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

InvestorType = Literal["Individual", "Institution", "Family Office"]


class InvestorCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    investor_type: InvestorType
    email: EmailStr

    @field_validator("name")
    @classmethod
    def _name_must_not_be_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("name must not be empty or whitespace-only")
        return stripped

    @field_validator("email")
    @classmethod
    def _email_lowercase(cls, v: str) -> str:
        return v.lower()


class InvestorRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    investor_type: InvestorType
    email: EmailStr
    created_at: datetime
