from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter

from app.routers.dependencies import InvestmentRepoDep
from app.schemas.error import ErrorResponse
from app.schemas.investment import InvestmentCreate, InvestmentRead

router = APIRouter(prefix="/funds/{fund_id}/investments", tags=["investments"])


@router.get(
    "",
    response_model=list[InvestmentRead],
    responses={
        404: {"model": ErrorResponse, "description": "Fund not found"},
        422: {"model": ErrorResponse, "description": "Validation error"},
    },
)
async def list_investments_for_fund(
    fund_id: UUID,
    repo: InvestmentRepoDep,
) -> list[InvestmentRead]:
    investments = await repo.list_by_fund(fund_id)
    return [InvestmentRead.model_validate(inv) for inv in investments]


@router.post(
    "",
    response_model=InvestmentRead,
    status_code=201,
    responses={
        404: {"model": ErrorResponse, "description": "Fund or investor not found"},
        422: {"model": ErrorResponse, "description": "Validation error"},
    },
)
async def create_investment(
    fund_id: UUID,
    data: InvestmentCreate,
    repo: InvestmentRepoDep,
) -> InvestmentRead:
    investment = await repo.create(fund_id, data)
    return InvestmentRead.model_validate(investment)
