from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import NotFoundError
from app.models.fund import Fund
from app.models.investment import Investment
from app.models.investor import Investor
from app.schemas.investment import InvestmentCreate


class InvestmentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_by_fund(self, fund_id: UUID) -> list[Investment]:
        fund_exists = await self.session.scalar(select(Fund.id).where(Fund.id == fund_id))
        if fund_exists is None:
            raise NotFoundError(f"Fund {fund_id} not found")
        result = await self.session.scalars(
            select(Investment)
            .where(Investment.fund_id == fund_id)
            .order_by(Investment.investment_date)
        )
        return list(result.all())

    async def create(self, fund_id: UUID, data: InvestmentCreate) -> Investment:
        fund_exists = await self.session.scalar(select(Fund.id).where(Fund.id == fund_id))
        if fund_exists is None:
            raise NotFoundError(f"Fund {fund_id} not found")

        investor_exists = await self.session.scalar(
            select(Investor.id).where(Investor.id == data.investor_id)
        )
        if investor_exists is None:
            raise NotFoundError(f"Investor {data.investor_id} not found")

        investment = Investment(
            fund_id=fund_id,
            investor_id=data.investor_id,
            amount_usd=data.amount_usd,
            investment_date=data.investment_date,
        )
        self.session.add(investment)
        try:
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise NotFoundError("Fund or investor not found") from exc
        await self.session.refresh(investment)
        return investment
