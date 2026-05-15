from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import ConflictError, NotFoundError
from app.models.investor import Investor
from app.schemas.investor import InvestorCreate


class InvestorRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_all(self) -> list[Investor]:
        result = await self.session.scalars(select(Investor).order_by(Investor.created_at))
        return list(result.all())

    async def get_by_id(self, id: UUID) -> Investor:
        investor = await self.session.scalar(select(Investor).where(Investor.id == id))
        if investor is None:
            raise NotFoundError(f"Investor {id} not found")
        return investor

    async def create(self, data: InvestorCreate) -> Investor:
        investor = Investor(
            name=data.name,
            investor_type=data.investor_type,
            email=str(data.email),
        )
        self.session.add(investor)
        try:
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise ConflictError("Investor with this email already exists") from exc
        await self.session.refresh(investor)
        return investor
