from __future__ import annotations

from httpx import AsyncClient

VALID_FUND = {
    "name": "Titanbay Growth Fund I",
    "vintage_year": 2024,
    "target_size_usd": "250000000.00",
    "status": "Fundraising",
}
VALID_INVESTOR = {
    "name": "CalPERS",
    "investor_type": "Institution",
    "email": "pe@calpers.ca.gov",
}
UNKNOWN_UUID = "00000000-0000-0000-0000-000000000000"


async def _create_fund(client: AsyncClient, **overrides: object) -> dict:
    return (await client.post("/funds", json={**VALID_FUND, **overrides})).json()


async def _create_investor(client: AsyncClient, **overrides: object) -> dict:
    return (await client.post("/investors", json={**VALID_INVESTOR, **overrides})).json()


async def test_create_investment_happy_path(client: AsyncClient) -> None:
    fund = await _create_fund(client)
    investor = await _create_investor(client)
    response = await client.post(
        f"/funds/{fund['id']}/investments",
        json={
            "investor_id": investor["id"],
            "amount_usd": "50000000.00",
            "investment_date": "2024-03-15",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["fund_id"] == fund["id"]
    assert body["investor_id"] == investor["id"]
    assert body["amount_usd"] == "50000000.00"
    assert body["investment_date"] == "2024-03-15"
    assert body["id"]


async def test_create_investment_unknown_fund_returns_404(client: AsyncClient) -> None:
    investor = await _create_investor(client)
    response = await client.post(
        f"/funds/{UNKNOWN_UUID}/investments",
        json={
            "investor_id": investor["id"],
            "amount_usd": "1000.00",
            "investment_date": "2024-03-15",
        },
    )
    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "NOT_FOUND"
    assert "fund" in body["error"]["message"].lower()


async def test_create_investment_unknown_investor_returns_404(client: AsyncClient) -> None:
    fund = await _create_fund(client)
    response = await client.post(
        f"/funds/{fund['id']}/investments",
        json={
            "investor_id": UNKNOWN_UUID,
            "amount_usd": "1000.00",
            "investment_date": "2024-03-15",
        },
    )
    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "NOT_FOUND"
    assert "investor" in body["error"]["message"].lower()


async def test_create_investment_negative_amount_returns_422(client: AsyncClient) -> None:
    fund = await _create_fund(client)
    investor = await _create_investor(client)
    response = await client.post(
        f"/funds/{fund['id']}/investments",
        json={
            "investor_id": investor["id"],
            "amount_usd": "-100.00",
            "investment_date": "2024-03-15",
        },
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


async def test_create_investment_zero_amount_returns_422(client: AsyncClient) -> None:
    fund = await _create_fund(client)
    investor = await _create_investor(client)
    response = await client.post(
        f"/funds/{fund['id']}/investments",
        json={
            "investor_id": investor["id"],
            "amount_usd": "0.00",
            "investment_date": "2024-03-15",
        },
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


async def test_list_investments_filters_by_fund(client: AsyncClient) -> None:
    fund_a = await _create_fund(client, name="Fund A")
    fund_b = await _create_fund(client, name="Fund B")
    investor = await _create_investor(client)

    await client.post(
        f"/funds/{fund_a['id']}/investments",
        json={
            "investor_id": investor["id"],
            "amount_usd": "100.00",
            "investment_date": "2024-01-01",
        },
    )
    await client.post(
        f"/funds/{fund_b['id']}/investments",
        json={
            "investor_id": investor["id"],
            "amount_usd": "200.00",
            "investment_date": "2024-02-01",
        },
    )

    response = await client.get(f"/funds/{fund_a['id']}/investments")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["fund_id"] == fund_a["id"]
    assert body[0]["amount_usd"] == "100.00"


async def test_list_investments_unknown_fund_returns_404(client: AsyncClient) -> None:
    response = await client.get(f"/funds/{UNKNOWN_UUID}/investments")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


async def test_list_investments_empty_fund_returns_empty_list(client: AsyncClient) -> None:
    fund = await _create_fund(client)
    response = await client.get(f"/funds/{fund['id']}/investments")
    assert response.status_code == 200
    assert response.json() == []
