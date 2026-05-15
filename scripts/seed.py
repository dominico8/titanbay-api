"""Idempotent seed data for the Titanbay API.

Run with: ``uv run python -m scripts.seed`` (or ``make seed``).

The script uses the same repository classes as the API, so it exercises the
same code paths. Existing rows (matched on natural keys) are left alone.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.exceptions import DomainError
from app.models.fund import Fund
from app.models.investment import Investment
from app.models.investor import Investor
from app.repositories import FundRepository, InvestmentRepository, InvestorRepository
from app.schemas.fund import FundCreate
from app.schemas.investment import InvestmentCreate
from app.schemas.investor import InvestorCreate

logger = logging.getLogger("seed")


FUNDS: list[FundCreate] = [
    FundCreate(
        name="Titanbay Growth Fund I",
        vintage_year=2024,
        target_size_usd=Decimal("250000000.00"),
        status="Investing",
    ),
    FundCreate(
        name="Titanbay Growth Fund II",
        vintage_year=2025,
        target_size_usd=Decimal("500000000.00"),
        status="Fundraising",
    ),
]

INVESTORS: list[InvestorCreate] = [
    InvestorCreate(
        name="Acme Family Office",
        investor_type="Family Office",
        email="ops@acmefo.example",
    ),
    InvestorCreate(
        name="Goldman Sachs Asset Management",
        investor_type="Institution",
        email="investments@gsam.example",
    ),
    InvestorCreate(
        name="Jane Carter",
        investor_type="Individual",
        email="jane@example.com",
    ),
]

# (fund_name, investor_email, amount, date)
INVESTMENTS: list[tuple[str, str, Decimal, date]] = [
    ("Titanbay Growth Fund I", "ops@acmefo.example", Decimal("25000000.00"), date(2024, 4, 12)),
    (
        "Titanbay Growth Fund I",
        "investments@gsam.example",
        Decimal("75000000.00"),
        date(2024, 5, 20),
    ),
    ("Titanbay Growth Fund I", "jane@example.com", Decimal("500000.00"), date(2024, 6, 1)),
    (
        "Titanbay Growth Fund II",
        "investments@gsam.example",
        Decimal("60000000.00"),
        date(2025, 2, 10),
    ),
]


async def _seed_funds(session: AsyncSession) -> dict[str, Fund]:
    repo = FundRepository(session)
    funds: dict[str, Fund] = {}
    for spec in FUNDS:
        existing = await session.scalar(
            select(Fund).where(Fund.name == spec.name, Fund.vintage_year == spec.vintage_year)
        )
        if existing is not None:
            logger.info("skipped fund %r (already exists)", spec.name)
            funds[spec.name] = existing
            continue
        try:
            created = await repo.create(spec)
        except DomainError as exc:
            logger.warning("skipped fund %r: %s", spec.name, exc.message)
            continue
        logger.info("inserted fund %r", spec.name)
        funds[spec.name] = created
    return funds


async def _seed_investors(session: AsyncSession) -> dict[str, Investor]:
    repo = InvestorRepository(session)
    investors: dict[str, Investor] = {}
    for spec in INVESTORS:
        email = str(spec.email)
        existing = await session.scalar(select(Investor).where(Investor.email == email))
        if existing is not None:
            logger.info("skipped investor %r (already exists)", email)
            investors[email] = existing
            continue
        try:
            created = await repo.create(spec)
        except DomainError as exc:
            logger.warning("skipped investor %r: %s", email, exc.message)
            continue
        logger.info("inserted investor %r", email)
        investors[email] = created
    return investors


async def _seed_investments(
    session: AsyncSession,
    funds: dict[str, Fund],
    investors: dict[str, Investor],
) -> None:
    repo = InvestmentRepository(session)
    for fund_name, investor_email, amount, inv_date in INVESTMENTS:
        fund = funds.get(fund_name)
        investor = investors.get(investor_email)
        if fund is None or investor is None:
            logger.warning(
                "skipped investment (fund=%r investor=%r): missing parent",
                fund_name,
                investor_email,
            )
            continue
        existing = await session.scalar(
            select(Investment).where(
                Investment.fund_id == fund.id,
                Investment.investor_id == investor.id,
                Investment.investment_date == inv_date,
            )
        )
        label = f"{fund_name} / {investor_email} / {inv_date.isoformat()}"
        if existing is not None:
            logger.info("skipped investment %s (already exists)", label)
            continue
        try:
            await repo.create(
                fund.id,
                InvestmentCreate(
                    investor_id=investor.id,
                    amount_usd=amount,
                    investment_date=inv_date,
                ),
            )
        except DomainError as exc:
            logger.warning("skipped investment %s: %s", label, exc.message)
            continue
        logger.info("inserted investment %s", label)


async def seed() -> None:
    async with AsyncSessionLocal() as session:
        funds = await _seed_funds(session)
        investors = await _seed_investors(session)
        await _seed_investments(session, funds, investors)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s - %(message)s")
    asyncio.run(seed())
