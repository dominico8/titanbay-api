from __future__ import annotations

from fastapi import APIRouter

from app.routers.dependencies import InvestorRepoDep
from app.schemas.error import ErrorResponse
from app.schemas.investor import InvestorCreate, InvestorRead

router = APIRouter(prefix="/investors", tags=["investors"])


@router.get("", response_model=list[InvestorRead])
async def list_investors(repo: InvestorRepoDep) -> list[InvestorRead]:
    investors = await repo.list_all()
    return [InvestorRead.model_validate(i) for i in investors]


@router.post(
    "",
    response_model=InvestorRead,
    status_code=201,
    responses={
        409: {"model": ErrorResponse, "description": "An investor with this email already exists"},
        422: {"model": ErrorResponse, "description": "Validation error"},
    },
)
async def create_investor(data: InvestorCreate, repo: InvestorRepoDep) -> InvestorRead:
    investor = await repo.create(data)
    return InvestorRead.model_validate(investor)
