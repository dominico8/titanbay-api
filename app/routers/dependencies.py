from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.repositories import FundRepository, InvestmentRepository, InvestorRepository

DbSession = Annotated[AsyncSession, Depends(get_db)]


def get_fund_repo(db: DbSession) -> FundRepository:
    return FundRepository(db)


def get_investor_repo(db: DbSession) -> InvestorRepository:
    return InvestorRepository(db)


def get_investment_repo(db: DbSession) -> InvestmentRepository:
    return InvestmentRepository(db)


FundRepoDep = Annotated[FundRepository, Depends(get_fund_repo)]
InvestorRepoDep = Annotated[InvestorRepository, Depends(get_investor_repo)]
InvestmentRepoDep = Annotated[InvestmentRepository, Depends(get_investment_repo)]
