from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import NotFoundError
from app.models.fund import Fund
from app.schemas.fund import FundCreate, FundUpdate


class FundRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_all(self) -> list[Fund]:
        result = await self.session.scalars(select(Fund).order_by(Fund.created_at))
        return list(result.all())

    async def get_by_id(self, id: UUID) -> Fund:
        fund = await self.session.scalar(select(Fund).where(Fund.id == id))
        if fund is None:
            raise NotFoundError(f"Fund {id} not found")
        return fund

    async def create(self, data: FundCreate) -> Fund:
        fund = Fund(
            name=data.name,
            vintage_year=data.vintage_year,
            target_size_usd=data.target_size_usd,
            status=data.status,
        )
        self.session.add(fund)
        await self.session.commit()
        await self.session.refresh(fund)
        return fund

    async def update(self, data: FundUpdate) -> Fund:
        fund = await self.get_by_id(data.id)
        fund.name = data.name
        fund.vintage_year = data.vintage_year
        fund.target_size_usd = data.target_size_usd
        fund.status = data.status
        await self.session.commit()
        await self.session.refresh(fund)
        return fund
