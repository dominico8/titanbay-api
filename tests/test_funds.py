from __future__ import annotations

from uuid import UUID

from httpx import AsyncClient

VALID_FUND = {
    "name": "Titanbay Growth Fund I",
    "vintage_year": 2024,
    "target_size_usd": 250000000.00,
    "status": "Fundraising",
}


async def test_create_fund_returns_201_with_generated_fields(client: AsyncClient) -> None:
    response = await client.post("/funds", json=VALID_FUND)
    assert response.status_code == 201
    body = response.json()
    UUID(body["id"])  # raises if not a UUID
    assert body["created_at"]
    assert body["name"] == VALID_FUND["name"]
    assert body["vintage_year"] == VALID_FUND["vintage_year"]
    assert body["target_size_usd"] == VALID_FUND["target_size_usd"]
    assert body["status"] == VALID_FUND["status"]


async def test_create_fund_negative_target_size_returns_422(client: AsyncClient) -> None:
    response = await client.post("/funds", json={**VALID_FUND, "target_size_usd": -1.00})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


async def test_create_fund_invalid_status_returns_422(client: AsyncClient) -> None:
    response = await client.post("/funds", json={**VALID_FUND, "status": "Bogus"})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


async def test_create_fund_vintage_year_too_old_returns_422(client: AsyncClient) -> None:
    response = await client.post("/funds", json={**VALID_FUND, "vintage_year": 1800})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


async def test_create_fund_vintage_year_too_new_returns_422(client: AsyncClient) -> None:
    response = await client.post("/funds", json={**VALID_FUND, "vintage_year": 2200})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


async def test_create_fund_empty_name_returns_422(client: AsyncClient) -> None:
    response = await client.post("/funds", json={**VALID_FUND, "name": ""})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


async def test_create_fund_whitespace_only_name_returns_422(client: AsyncClient) -> None:
    response = await client.post("/funds", json={**VALID_FUND, "name": "   "})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


async def test_create_fund_strips_name_whitespace(client: AsyncClient) -> None:
    response = await client.post("/funds", json={**VALID_FUND, "name": "  Trimmed Fund  "})
    assert response.status_code == 201
    assert response.json()["name"] == "Trimmed Fund"


async def test_create_fund_string_money_rejected(client: AsyncClient) -> None:
    response = await client.post(
        "/funds",
        json={**VALID_FUND, "target_size_usd": "100.00"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


async def test_create_fund_rejects_extra_fields(client: AsyncClient) -> None:
    response = await client.post(
        "/funds",
        json={**VALID_FUND, "unexpected_field": "boom"},
    )
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
    msgs = [e["msg"] for e in body["error"]["details"]["errors"]]
    assert any("extra" in m.lower() or "unexpected" in m.lower() for m in msgs)


async def test_create_fund_missing_field_returns_422(client: AsyncClient) -> None:
    payload = {k: v for k, v in VALID_FUND.items() if k != "status"}
    response = await client.post("/funds", json=payload)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


async def test_list_funds_returns_created_funds(client: AsyncClient) -> None:
    a = (await client.post("/funds", json={**VALID_FUND, "name": "Fund A"})).json()
    b = (await client.post("/funds", json={**VALID_FUND, "name": "Fund B"})).json()
    response = await client.get("/funds")
    assert response.status_code == 200
    names = {f["name"] for f in response.json()}
    ids = {f["id"] for f in response.json()}
    assert {"Fund A", "Fund B"} <= names
    assert {a["id"], b["id"]} <= ids


async def test_list_funds_empty(client: AsyncClient) -> None:
    response = await client.get("/funds")
    assert response.status_code == 200
    assert response.json() == []


async def test_get_fund_by_id_returns_200(client: AsyncClient) -> None:
    created = (await client.post("/funds", json=VALID_FUND)).json()
    response = await client.get(f"/funds/{created['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


async def test_get_fund_by_unknown_id_returns_404_with_envelope(client: AsyncClient) -> None:
    response = await client.get("/funds/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "NOT_FOUND"
    assert "not found" in body["error"]["message"].lower()


async def test_get_fund_by_malformed_uuid_returns_422(client: AsyncClient) -> None:
    response = await client.get("/funds/not-a-uuid")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


async def test_put_fund_updates_fields_and_returns_200(client: AsyncClient) -> None:
    created = (await client.post("/funds", json=VALID_FUND)).json()
    update_body = {
        "id": created["id"],
        "name": "Renamed Fund",
        "vintage_year": 2025,
        "target_size_usd": 300000000.00,
        "status": "Investing",
    }
    response = await client.put("/funds", json=update_body)
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == created["id"]
    assert body["name"] == "Renamed Fund"
    assert body["vintage_year"] == 2025
    assert body["target_size_usd"] == 300000000.00
    assert body["status"] == "Investing"

    # Persisted
    fetched = (await client.get(f"/funds/{created['id']}")).json()
    assert fetched["name"] == "Renamed Fund"
    assert fetched["status"] == "Investing"


async def test_put_fund_with_unknown_id_returns_404(client: AsyncClient) -> None:
    response = await client.put(
        "/funds",
        json={
            "id": "00000000-0000-0000-0000-000000000000",
            "name": "Phantom",
            "vintage_year": 2024,
            "target_size_usd": 1000000.00,
            "status": "Fundraising",
        },
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"
