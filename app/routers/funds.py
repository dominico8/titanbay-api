from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter

from app.routers.dependencies import FundRepoDep
from app.schemas.fund import FundCreate, FundRead, FundUpdate

router = APIRouter(prefix="/funds", tags=["funds"])


@router.get("", response_model=list[FundRead])
async def list_funds(repo: FundRepoDep) -> list[FundRead]:
    funds = await repo.list_all()
    return [FundRead.model_validate(f) for f in funds]


@router.post("", response_model=FundRead, status_code=201)
async def create_fund(data: FundCreate, repo: FundRepoDep) -> FundRead:
    fund = await repo.create(data)
    return FundRead.model_validate(fund)


@router.put(
    "",
    response_model=FundRead,
    responses={404: {"description": "Fund not found"}},
)
async def update_fund(data: FundUpdate, repo: FundRepoDep) -> FundRead:
    fund = await repo.update(data)
    return FundRead.model_validate(fund)


@router.get(
    "/{id}",
    response_model=FundRead,
    responses={404: {"description": "Fund not found"}},
)
async def get_fund(id: UUID, repo: FundRepoDep) -> FundRead:
    fund = await repo.get_by_id(id)
    return FundRead.model_validate(fund)
