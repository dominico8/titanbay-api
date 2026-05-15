from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, Numeric, String, text
from sqlalchemy.dialects.postgresql import ENUM, TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base

fund_status_enum = ENUM(
    "Fundraising",
    "Investing",
    "Closed",
    name="fund_status",
    create_type=True,
)


class Fund(Base):
    __tablename__ = "funds"
    __table_args__ = (
        CheckConstraint(
            "vintage_year BETWEEN 1900 AND 2100",
            name="ck_funds_vintage_year_range",
        ),
        CheckConstraint(
            "target_size_usd > 0",
            name="ck_funds_target_size_usd_positive",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    vintage_year: Mapped[int] = mapped_column(nullable=False)
    target_size_usd: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    status: Mapped[str] = mapped_column(fund_status_enum, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
